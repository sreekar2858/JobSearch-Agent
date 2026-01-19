"""
Main interface: LinkedInScraper class for job search automation using Playwright.
"""

import os
import logging
import dotenv
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from .browser import BrowserManager
from .auth import AuthManager
from .filters import FilterManager
from .extractors import JobLinksExtractor, JobDetailsExtractor
from .config import DEFAULT_TIMEOUT
from .utils import async_random_sleep
from .extractors.selectors import (
    JOB_DESCRIPTION_SELECTORS,
    ADDITIONAL_POSTED_DATE_SELECTORS,
    JOB_INSIGHTS_SELECTORS,
    ADDITIONAL_JOB_INSIGHTS_SELECTORS,
    ADDITIONAL_APPLY_BUTTON_SELECTORS,
    ADDITIONAL_LOCATION_SELECTORS,
    APPLICANT_COUNT_SELECTORS,
    CONTACT_INFO_SELECTORS,
    ADDITIONAL_COMPANY_WEBSITE_SELECTORS,
    SKILLS_SECTION_SELECTORS,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("linkedin_scraper")


class LinkedInScraper:
    """
    A class to scrape job listings from LinkedIn using Playwright.

    Features:
    - Search for jobs with keywords and location
    - Support for authenticated searches using LinkedIn credentials
    - Extraction of job titles, companies, locations, and URLs
    - Support for Chromium, Firefox, and WebKit browsers    - Handling of common scraping challenges (captchas, rate limits)
    """

    def __init__(
        self,
        headless: bool = False,
        timeout: int = DEFAULT_TIMEOUT,
        browser: str = "chromium",
        proxy: Optional[str] = None,
        anonymize: bool = True,
    ):
        """
        Initialize the LinkedIn scraper.

        ⚠️  LinkedIn login is REQUIRED for job scraping to work properly.
        Credentials must be configured in .env file or environment variables.

        Args:
            headless: Whether to run the browser in headless mode
            timeout: Wait timeout in milliseconds for page loading
            browser: Browser to use ('chromium', 'firefox', or 'webkit')
            proxy: Proxy string in format "http://host:port" or "socks5://host:port"
            anonymize: Whether to enable anonymization features
        """
        self.timeout = timeout
        self.headless = headless
        self.browser = browser.lower()
        self.proxy = proxy
        self.anonymize = anonymize
        self.use_login = True  # Always use login - required for LinkedIn scraping

        # Load environment variables for login (always required)
        dotenv.load_dotenv()
        self.username = os.getenv("LINKEDIN_USERNAME")
        self.password = os.getenv("LINKEDIN_PASSWORD")

        if not self.username or not self.password:
            raise ValueError(
                "❌ LinkedIn credentials are REQUIRED but not found!\n"
                "Please configure LINKEDIN_USERNAME and LINKEDIN_PASSWORD in your .env file or environment variables.\n"
                "LinkedIn scraping cannot work without proper authentication."
            )

        logger.info("✅ LinkedIn credentials loaded successfully")

        # Initialize components
        self.browser_manager = None
        self.auth_manager = None
        self.filter_manager = None
        self.job_links_extractor = None
        self.job_details_extractor = None
        self._setup_complete = False

    async def _ensure_setup(self):
        """Ensure all components are set up."""
        if not self._setup_complete:
            try:
                self.browser_manager = BrowserManager(
                    self.browser,
                    self.headless,
                    self.timeout,
                    self.proxy,
                    self.anonymize,
                )
                await self.browser_manager.setup_driver()

                self.auth_manager = AuthManager(self.browser_manager.page, self.timeout)
                self.filter_manager = FilterManager(
                    self.browser_manager.page, self.timeout
                )
                self.job_links_extractor = JobLinksExtractor(self.browser_manager.page)
                self.job_details_extractor = JobDetailsExtractor(
                    self.browser_manager.page, self.timeout
                )

                self._setup_complete = True
            except RuntimeError as e:
                if "Windows async incompatibility" in str(e):
                    # Re-raise with more context for the job search pipeline to catch
                    raise RuntimeError(
                        "Windows async incompatibility detected during browser setup. "
                        "Use synchronous scraper fallback."
                    ) from e
                else:
                    raise

    @property
    async def page(self):
        """Get the Page instance."""
        await self._ensure_setup()
        return self.browser_manager.page

    async def collect_job_links(
        self,
        keywords: str,
        location: str,
        max_pages: int = 1,
        experience_levels: Optional[List[str]] = None,
        date_posted: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> list:
        """
        Collect all job posting URLs from LinkedIn search results pages.

        Args:
            keywords: Job search keywords
            location: Location for job search
            max_pages: Maximum number of pages to scrape
            experience_levels: List of experience levels to filter by
                             Valid values: ['internship', 'entry_level', 'associate', 'mid_senior', 'director', 'executive']
            date_posted: Date posted filter option
                        Valid values: ['any_time', 'past_month', 'past_week', 'past_24_hours']
            sort_by: Sort results by relevance or date
                    Valid values: ['relevance', 'recent'] or None for default

        Returns:
            List of job URLs (strings).
        """
        await self._ensure_setup()

        await self.auth_manager.ensure_login(self.username, self.password)

        search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location.replace(' ', '%20')}"

        # Add sort parameter if specified
        if sort_by:
            if sort_by.lower() == "relevance":
                search_url += "&sortBy=R"
            elif sort_by.lower() == "recent":
                search_url += "&sortBy=DD"
            else:
                logger.warning(
                    f"Invalid sort_by value: {sort_by}. Valid values are 'relevance' or 'recent'"
                )

        await self.browser_manager.navigate_to(search_url, 3.0, 5.0)

        # Apply search filters if specified
        if experience_levels or date_posted:
            logger.info("Applying search filters...")
            filter_success = await self.filter_manager.apply_search_filters(
                experience_levels, date_posted
            )
            if not filter_success:
                logger.warning("Some filters may not have been applied correctly")

        job_links = set()
        current_page = 1
        while current_page <= max_pages:
            logger.info(f"Collecting links from page {current_page} of {max_pages}")

            # Debug: analyze page structure
            logger.info("Analyzing page structure...")
            await self.browser_manager.debug_page_structure()

            # Get total job count for this search
            total_expected = await self.browser_manager.get_total_job_count()

            # Find the job list container
            job_list_container = await self.browser_manager.find_job_list_container()

            # Scroll through the job list to load all cards
            await self.browser_manager.scroll_job_list_container(
                job_list_container, total_expected
            )

            # Get all job cards from the page
            job_cards = await self.browser_manager.get_job_cards(job_list_container)
            if not job_cards:
                logger.warning("No job cards found on this page.")
                break

            # Extract job links from all cards
            page_links = await self.job_links_extractor.extract_job_links_from_cards(
                job_cards, current_page
            )
            job_links.update(page_links)

            logger.info(f"Collected {len(job_links)} unique job links so far.")

            # Check if we can go to next page
            pagination_info = await self.job_links_extractor.get_pagination_info()
            logger.info(f"Pagination status: {pagination_info['page_state']}")

            if not pagination_info["has_next"]:
                logger.info("No next page available - reached end of results")
                break

            # Navigate to next page
            if not await self.job_links_extractor.go_to_next_page():
                break

            current_page += 1
        return list(job_links)

    async def _extract_job_details_python(self, page, job_url: str) -> Dict[str, Any]:
        """
        Extract job details using Playwright Python API instead of JS evaluate.
        Keeps same logic as previous JS implementation.
        """
        import re
        from urllib.parse import urlparse, parse_qs

        def clean_text(text: Optional[str]) -> Optional[str]:
            """Helper to clean text"""
            if not text:
                return None
            return re.sub(r"\s+", " ", text.strip())

        result = {}

        # Get title - prioritize specific job title selectors
        title = None
        title_selectors = [
            ".job-details-jobs-unified-top-card__job-title h1",
            ".jobs-unified-top-card__job-title h1",
            "h1.t-24",
            "main h1",
        ]
        for selector in title_selectors:
            h1 = await page.query_selector(selector)
            if h1:
                title = clean_text(await h1.text_content())
                if (
                    title
                    and len(title) > 3
                    and title not in ["Home", "Jobs", "LinkedIn"]
                ):
                    break

        if not title or title in ["Home", "Jobs", "LinkedIn"]:
            page_title = await page.title()
            if "|" in page_title:
                title = page_title.split("|")[0].strip()
        result["title"] = title

        # Get company - avoid navigation links
        company = None
        company_selectors = [
            ".job-details-jobs-unified-top-card__company-name a",
            ".jobs-unified-top-card__company-name a",
            'a.ember-view[href*="/company/"]',
        ]

        for selector in company_selectors:
            company_link = await page.query_selector(selector)
            if company_link:
                # Check if it's in the main job content area, not navigation
                in_nav = await company_link.evaluate(
                    'el => !!el.closest("header, nav, aside")'
                )
                if not in_nav:
                    text = clean_text(await company_link.text_content())
                    if (
                        text
                        and 2 < len(text) < 100
                        and text
                        not in ["Home", "Jobs", "Network", "Messaging", "Notifications"]
                    ):
                        company = text
                        break

        if not company:
            page_title = await page.title()
            if "|" in page_title:
                parts = page_title.split("|")
                if len(parts) > 1:
                    company = parts[1].strip().replace(" | LinkedIn", "")
        result["company"] = company

        # Get description - use specific job description selectors
        description = None
        description_selectors = [
            ".jobs-description__content",
            ".jobs-box__html-content",
            "article.jobs-description",
            ".job-details-jobs-unified-top-card__job-description",
            'div[class*="description"] article',
        ]

        for selector in description_selectors:
            desc_element = await page.query_selector(selector)
            if desc_element:
                desc_text = clean_text(await desc_element.text_content())
                if desc_text and 100 < len(desc_text) < 50000:
                    description = desc_text
                    break

        if not description or len(description) < 100:
            # Fallback: Look for div with job description keywords
            keywords = [
                "responsibilities",
                "requirements",
                "experience",
                "qualifications",
                "about the role",
                "about the job",
                "we are looking",
                "you will",
                "your role",
                "what you",
                "who you are",
                "skills",
                "duties",
            ]
            divs = await page.query_selector_all("div, section")
            candidates = []

            for div in divs:
                # Skip nav/header/footer
                parent_tag = await div.evaluate(
                    'el => el.closest("nav, header, aside, footer") ? true : false'
                )
                if parent_tag:
                    continue

                full_text = await div.text_content()
                if not full_text:
                    continue

                has_keywords = any(k in full_text.lower() for k in keywords)
                if has_keywords and 200 < len(full_text) < 15000:
                    candidates.append(
                        {"text": clean_text(full_text), "length": len(full_text)}
                    )
        #  - use specific selectors first
        location = None
        location_selectors = [
            ".job-details-jobs-unified-top-card__bullet",
            ".jobs-unified-top-card__bullet",
            "span.jobs-unified-top-card__workplace-type",
        ]

        for selector in location_selectors:
            loc_element = await page.query_selector(selector)
            if loc_element:
                text = clean_text(await loc_element.text_content())
                if text and 3 < len(text) < 100:
                    # Exclude date/time patterns
                    if not re.search(
                        r"\d{4}|ago|applicant|visible", text, re.IGNORECASE
                    ):
                        if (
                            any(
                                keyword in text
                                for keyword in ["Remote", "Hybrid", "On-site"]
                            )
                            or "," in text
                        ):
                            location = text
                            break

        if not location:
            # Fallback to span scanning
            all_spans = await page.query_selector_all("span.t-black--light, span")
            for span in all_spans[:100]:  # Limit to first 100 spans
                in_nav = await span.evaluate('el => !!el.closest("header, nav, aside")')
                if in_nav:
                    continue
                text = clean_text(await span.text_content())
                if text and 3 < len(text) < 100:
                    if re.match(r"[A-Z][a-z]+,\s*[A-Z]", text) or any(
                        loc in text
                        for loc in [
                            "Germany",
                            "Berlin",
                            "Remote",
                            "Hybrid",
                            "United States",
                            "London",
                        ]
                    ):
                        if not re.search(
                            r"\d{4}|ago|applicant|visible|reviewing|alum",
                            text,
                            re.IGNORECASE,
                        ):
                            location = text
                            break
        result["location"] = location

        # Get date posted - be more specific
        date_posted = None
        date_selectors = [
            "span.jobs-unified-top-card__posted-date",
            'span[class*="posted"]',
        ]

        for selector in date_selectors:
            date_element = await page.query_selector(selector)
            if date_element:
                text = clean_text(await date_element.text_content())
                if text and re.search(
                    r"\d+\s+(hour|day|week|month)s?\s+ago", text, re.IGNORECASE
                ):
                    # Extract just the "X days ago" part
                    match = re.search(
                        r"\d+\s+(hour|day|week|month)s?\s+ago", text, re.IGNORECASE
                    )
                    if match:
                        date_posted = match.group(0)
                        break

        if not date_posted:
            # Fallback span search
            all_spans = await page.query_selector_all("span")
            # for span in all_s - be more careful with name extraction
        hiring_team = []
        seen_urls = set()

        # Look specifically in hiring team section
        hiring_section = await page.query_selector(
            'section:has-text("Meet the hiring team")'
        )
        if hiring_section:
            profile_links = await hiring_section.query_selector_all('a[href*="/in/"]')
        else:
            profile_links = await page.query_selector_all('a[href*="/in/"]')

        for link in profile_links[:20]:  # Limit to first 20 profile links
            if len(hiring_team) >= 5:
                break
            href = await link.get_attribute("href")
            if not href or href in seen_urls:
                continue
            # Skip header/nav/footer
            in_nav = await link.evaluate(
                'el => !!el.closest("header, nav, footer, aside")'
            )
            if in_nav:
                continue

            name = None
            title_text = None

            # Try to find name in strong tag within the link
            strong_el = await link.query_selector("strong, span.t-bold")
            if strong_el:
                name = clean_text(await strong_el.text_content())
                # Clean up - remove trailing metadata like "1 company alum"
                if name:
                    name = re.sub(
                        r"\s*\d+\s+(company\s+alum|mutual connection).*$",
                        "",
                        name,
                        flags=re.IGNORECASE,
                    ).strip()

            if not name:
                link_text = clean_text(await link.text_content())
                if link_text and 2 < len(link_text) < 80:
                    # Split by bullet point or newline
                    name = link_text.split("•")[0].split("\n")[0].strip()
                    # Clean up
                    name = re.sub(
                        r"\s*\d+\s+(company\s+alum|mutual connection).*$",
                        "",
                        name,
                        flags=re.IGNORECASE,
                    ).strip()

            # Look for title in parent container
            if name and len(name) > 2:
                try:
                    parent_data = await link.evaluate("""el => {
                        const container = el.closest('li, div[class*="card"]') || el.parentElement;
                        if (!container) return null;
                        
                        // Look for title in spans/divs
                        const textElements = Array.from(container.querySelectorAll('span, div, p'));
                        for (const elem of textElements) {
                            const text = elem.textContent.trim();
                            // Skip if it's the name or metadata
                            if (text && text.length > 5 && text.length < 100 &&
                                !text.includes('company alum') && 
                                !text.includes('mutual connection') &&
                                !text.match(/^\d+(st|nd|rd|th)/) &&
                                !text.includes('Message') &&
                                !text.includes('Follow')) {
                                return text;
                            }
                        }
                        return null;
                    }""")
                    if parent_data and parent_data != name:
                        title_text = clean_text(parent_data)
                except:
                    pass

            if (
                name
                and len(name) > 2
                and "LinkedIn" not in name
                and name not in ["Home", "Jobs", "Network"]
            ):
                seen_urls.add(href)
                member = {"name": name, "linkedin_url": href}
                if title_text and title_text != name:
                    name = clean_text(await strong_el.text_content())
            elif link_text and 2 < len(link_text) < 80:
                name = link_text.split("•")[0].strip()

            # Look for title in sibling elements
            if name:
                parent = await link.evaluate("el => el.parentElement")
                if parent:
                    siblings = await link.evaluate("""el => {
                        const parent = el.parentElement;
                        if (!parent) return [];
                        return Array.from(parent.querySelectorAll('span, div, p')).map(e => e.textContent.trim());
                    }""")
                    for text in siblings:
                        text = clean_text(text)
                        if (
                            text
                            and text != name
                            and 3 < len(text) < 100
                            and "•" not in text
                            and "connection" not in text
                            and not re.match(r"^(1st|2nd|3rd)", text)
                            and "Message" not in text
                        ):
                            title_text = text
                            break

            if name and len(name) > 2 and "LinkedIn" not in name:
                seen_urls.add(href)
                member = {"name": name, "linkedin_url": href}
                if title_text:
                    member["title"] = title_text
                hiring_team.append(member)

        result["hiring_team"] = hiring_team

        # Extract related jobs
        related_jobs = []
        seen_job_urls = set()
        current_job_id = job_url.rstrip("/").split("/")[-1]

        # Strategy 1: Look for ul.js-similar-jobs-list
        similar_list = await page.query_selector("ul.js-similar-jobs-list")
        if not similar_list:
            similar_list = await page.query_selector(
                "ul.card-list.js-similar-jobs-list"
            )
        if not similar_list:
            all_uls = await page.query_selector_all("ul")
            for ul in all_uls:
                classes = await ul.get_attribute("class")
                if classes and (
                    "js-similar-jobs-list" in classes
                    or (
                        "card-list" in classes
                        and await ul.query_selector(
                            ".job-card-job-posting-card-wrapper"
                        )
                    )
                ):
                    similar_list = ul
                    break

        if similar_list:
            items = await similar_list.query_selector_all("li")
            logger.info(f"Found similar jobs list with {len(items)} items")

            for li in items:
                if len(related_jobs) >= 8:
                    break

                link = await li.query_selector(
                    "a.job-card-job-posting-card-wrapper__card-link"
                )
                if not link:
                    link = await li.query_selector('a[href*="jobs"]')
                if not link:
                    continue

                href = await link.get_attribute("href")
                if not href:
                    continue

                # Extract job ID from URL params
                link_job_id = None
                try:
                    parsed = urlparse(href)
                    params = parse_qs(parsed.query)
                    link_job_id = (
                        params.get("originToLandingJobPostings", [None])[0]
                        or params.get("currentJobId", [None])[0]
                        or params.get("referenceJobId", [None])[0]
                    )
                except:
                    pass

                if not link_job_id:
                    match = re.search(r"/jobs/view/(\d+)", href)
                    if match:
                        link_job_id = match.group(1)

                if (
                    not link_job_id
                    or link_job_id == current_job_id
                    or link_job_id in seen_job_urls
                ):
                    continue
                seen_job_urls.add(link_job_id)

                # Get title
                job_title = None
                title_selectors = [
                    ".artdeco-entity-lockup__title strong",
                    ".job-card-job-posting-card-wrapper__title strong",
                    ".artdeco-entity-lockup__title",
                    ".job-card-job-posting-card-wrapper__title",
                ]
                for sel in title_selectors:
                    title_el = await li.query_selector(sel)
                    if title_el:
                        job_title = clean_text(await title_el.text_content())
                        if job_title:
                            break

                if not job_title:
                    link_text = clean_text(await link.text_content())
                    if link_text and 3 < len(link_text) < 200:
                        job_title = link_text.split("\n")[0].strip()

                if not job_title or len(job_title) < 3:
                    continue

                job = {"title": job_title, "job_url": href}

                # Get company
                company_selectors = [
                    ".artdeco-entity-lockup__subtitle",
                    ".job-card-job-posting-card-wrapper__subtitle",
                ]
                for sel in company_selectors:
                    company_el = await li.query_selector(sel)
                    if company_el:
                        company_text = clean_text(await company_el.text_content())
                        if company_text:
                            job["company"] = company_text
                            break

                # Get location
                loc_selectors = [
                    ".artdeco-entity-lockup__caption",
                    ".job-card-job-posting-card-wrapper__caption",
                ]
                for sel in loc_selectors:
                    loc_el = await li.query_selector(sel)
                    if loc_el:
                        loc_text = clean_text(await loc_el.text_content())
                        if loc_text:
                            job["location"] = loc_text
                            break

                related_jobs.append(job)

            logger.info(
                f"Extracted {len(related_jobs)} related jobs from similar jobs list"
            )
        else:
            logger.info(
                "Similar jobs list (ul) not found, trying link-based extraction"
            )

        # Strategy 2: Find links to /jobs/collections/similar-jobs/
        if len(related_jobs) == 0:
            similar_job_links = await page.query_selector_all(
                'a[href*="/jobs/collections/similar-jobs/"]'
            )
            logger.info(f"Found {len(similar_job_links)} similar job collection links")

            for link in similar_job_links:
                if len(related_jobs) >= 8:
                    break

                try:
                    href = await link.get_attribute("href")
                    if not href:
                        continue

                    parsed = urlparse(href)
                    params = parse_qs(parsed.query)
                    link_job_id = (
                        params.get("currentJobId", [None])[0]
                        or params.get("originToLandingJobPostings", [None])[0]
                    )

                    if (
                        not link_job_id
                        or link_job_id == current_job_id
                        or link_job_id in seen_job_urls
                    ):
                        continue
                    seen_job_urls.add(link_job_id)

                    # Find container
                    container = await link.evaluate("""el => {
                        let c = el.closest('div[componentkey]') || el.parentElement;
                        for (let i = 0; i < 5 && c; i++) {
                            if (c.querySelector('p, h3, h4')) break;
                            c = c.parentElement;
                        }
                        return c;
                    }""")

                    if not container:
                        continue

                    # Find title
                    job_title = None
                    container_text = await link.evaluate(
                        'el => el.closest("div[componentkey]")?.textContent || el.parentElement?.textContent || ""'
                    )
                    possible_titles = await link.evaluate("""el => {
                        const c = el.closest('div[componentkey]') || el.parentElement;
                        if (!c) return [];
                        return Array.from(c.querySelectorAll('p, h3, h4, span')).map(e => e.textContent.trim());
                    }""")

                    for text in possible_titles:
                        text = clean_text(text)
                        if (
                            text
                            and 10 < len(text) < 150
                            and "ago" not in text
                            and "Easy Apply" not in text
                            and "€" not in text
                            and "$" not in text
                            and "linkedin" not in text.lower()
                        ):
                            job_title = text
                            break

                    if not job_title:
                        continue

                    job = {
                        "title": job_title,
                        "job_url": f"https://www.linkedin.com/jobs/view/{link_job_id}/",
                    }

                    # Find company and location from container text
                    if container_text:
                        lines = [
                            l.strip() for l in container_text.split("\n") if l.strip()
                        ]
                        for line in lines:
                            if line == job_title:
                                continue
                            # Location
                            if (
                                "Germany" in line
                                or "Remote" in line
                                or "Berlin" in line
                                or re.match(r"[A-Z][a-z]+, [A-Z]", line)
                            ):
                                if "ago" not in line and len(line) < 100:
                                    job["location"] = line
                            # Company
                            elif (
                                "company" not in job
                                and 2 < len(line) < 80
                                and "€" not in line
                                and "$" not in line
                                and "ago" not in line
                                and "Apply" not in line
                            ):
                                job["company"] = line

                    related_jobs.append(job)
                except Exception as e:
                    logger.debug(f"Error processing similar job link: {e}")

            logger.info(
                f"Extracted {len(related_jobs)} related jobs from collection links"
            )

        # Strategy 3: Fallback - scan all /jobs/view/ links
        if len(related_jobs) == 0:
            job_view_links = await page.query_selector_all('a[href*="/jobs/view/"]')
            for link in job_view_links:
                if len(related_jobs) >= 8:
                    break

                href = await link.get_attribute("href")
                if not href:
                    continue

                match = re.search(r"/jobs/view/(\d+)", href)
                if not match:
                    continue
                link_job_id = match.group(1)

                if link_job_id == current_job_id or link_job_id in seen_job_urls:
                    continue
                seen_job_urls.add(link_job_id)

                # Get title
                job_title = None
                strong_in_link = await link.query_selector("strong")
                if strong_in_link:
                    job_title = clean_text(await strong_in_link.text_content())

                if not job_title:
                    link_text = clean_text(await link.text_content())
                    if (
                        link_text
                        and 3 < len(link_text) < 150
                        and "apply" not in link_text.lower()
                        and "see all" not in link_text.lower()
                        and "show more" not in link_text.lower()
                    ):
                        job_title = link_text

                if not job_title or len(job_title) < 3:
                    continue

                job = {"title": job_title, "job_url": href}

                # Try to find company and location in parent container
                try:
                    parent_info = await link.evaluate("""el => {
                        let container = el.parentElement;
                        for (let i = 0; i < 5 && container; i++) {
                            if (container.tagName === 'LI' || container.tagName === 'ARTICLE') break;
                            container = container.parentElement;
                        }
                        if (!container) container = el.parentElement;
                        
                        const companyLink = container?.querySelector('a[href*="/company/"]');
                        const company = companyLink ? companyLink.textContent.trim() : null;
                        
                        const spans = container ? Array.from(container.querySelectorAll('span')) : [];
                        let location = null;
                        for (const span of spans) {
                            const text = span.textContent.trim();
                            if (text && (text.includes(',') || text.toLowerCase().includes('remote')) &&
                                !text.includes('ago') && text.length < 100) {
                                location = text;
                                break;
                            }
                        }
                        
                        return {company, location};
                    }""")

                    if parent_info.get("company"):
                        job["company"] = parent_info["company"]
                    if parent_info.get("location"):
                        job["location"] = parent_info["location"]
                except:
                    pass

                related_jobs.append(job)

        result["related_jobs"] = related_jobs

        return result

    async def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific job posting.

        Args:
            job_url: URL of the job posting

        Returns:            Dictionary containing detailed job information
        """
        await self._ensure_setup()

        # Ensure we're logged in (same as collect_job_links method)
        await self.auth_manager.ensure_login(self.username, self.password)

        try:
            # Navigate to job page and wait for DOM to be ready
            await self.browser_manager.page.goto(
                job_url, wait_until="domcontentloaded", timeout=self.timeout
            )
            logger.info(f"Navigated to {job_url}")

            # Small wait for JS to hydrate the page
            await asyncio.sleep(3)

            # Scroll multiple times to load all lazy content (hiring team, related jobs)
            try:
                # Scroll down in stages to trigger lazy loading
                for _ in range(5):
                    await self.browser_manager.page.evaluate(
                        "window.scrollTo(0, document.body.scrollHeight)"
                    )
                    await asyncio.sleep(1.5)

                # Scroll back up to ensure all sections are visible
                await self.browser_manager.page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(1)

                # Try to click any "show more" or "see more jobs" buttons - be very specific to avoid navigation
                # Only click buttons, not links, and check we stay on the same page
                show_more_selectors = [
                    'button:has-text("Show more")',
                    'button:has-text("See more")',
                    'button[aria-label*="Show more"]',
                    "button.jobs-description__footer-button",
                ]
                for selector in show_more_selectors:
                    try:
                        # Store current URL to verify we don't navigate away
                        current_url = self.browser_manager.page.url

                        btn = await self.browser_manager.page.query_selector(selector)
                        if btn and await btn.is_visible():
                            # Only click if it's actually a button element, not a link
                            tag_name = await btn.evaluate(
                                "el => el.tagName.toLowerCase()"
                            )
                            if tag_name == "button":
                                await btn.click()
                                await asyncio.sleep(2)

                                # Check if we got redirected
                                if (
                                    self.browser_manager.page.url != current_url
                                    and "/company/" in self.browser_manager.page.url
                                ):
                                    logger.warning(
                                        "Accidentally navigated to company page, going back"
                                    )
                                    await self.browser_manager.page.goto(
                                        current_url,
                                        wait_until="domcontentloaded",
                                        timeout=self.timeout,
                                    )
                                    await asyncio.sleep(2)
                    except Exception as e:
                        logger.debug(f"Show more button interaction: {e}")
                        pass

                # Wait specifically for similar jobs section to appear (if it exists)
                try:
                    await self.browser_manager.page.wait_for_selector(
                        'ul.js-similar-jobs-list, section:has-text("Similar jobs")',
                        state="attached",
                        timeout=3000,
                    )
                    logger.info("Similar jobs section found")
                except Exception:
                    logger.info("Similar jobs section not found (may not be present)")
            except Exception as e:
                logger.debug(f"Scrolling/waiting error: {e}")

            # Check if we're on the right page
            if (
                "login" in self.browser_manager.page.url.lower()
                or "checkpoint" in self.browser_manager.page.url.lower()
            ):
                logger.warning("Redirected to login/checkpoint page!")
                # Try logging in again
                await self.auth_manager.ensure_login(self.username, self.password)
                await self.browser_manager.page.goto(
                    job_url, wait_until="domcontentloaded", timeout=self.timeout
                )
                await asyncio.sleep(3)

            # Wait for structural elements to be attached to DOM
            try:
                # Wait for standard structural elements instead of specific classes which may be evaluated
                await self.browser_manager.page.wait_for_selector(
                    "h1, article, main", state="attached", timeout=5000
                )
            except PlaywrightTimeoutError:
                logger.warning(
                    "Structural elements not found, attempting extraction anyway"
                )

            # Initialize job details with all required fields and defaults
            job_details = {
                "url": job_url,
                "source": "linkedin",
                "scraped_at": datetime.now().isoformat(),
                "title": "NA",
                "company": "NA",
                "description": "NA",
                "location": "NA",
                "date_posted": "NA",
                "job_insights": "NA",
                "easy_apply": False,
                "apply_info": "NA",
                "company_info": "NA",
                "hiring_team": "NA",
                "related_jobs": "NA",
            }

            # Try direct extraction using Playwright Python API
            try:
                js_data = await self._extract_job_details_python(
                    self.browser_manager.page, job_url
                )

                if js_data:
                    logger.info(
                        f"JS extraction result: title={js_data.get('title')}, company={js_data.get('company')}, hiring_team={len(js_data.get('hiring_team', []))}, related_jobs={len(js_data.get('related_jobs', []))}"
                    )
                    if js_data.get("title"):
                        job_details["title"] = js_data["title"]
                    if js_data.get("company"):
                        job_details["company"] = js_data["company"]
                    if js_data.get("location"):
                        job_details["location"] = js_data["location"]
                    if js_data.get("description"):
                        job_details["description"] = js_data["description"]
                    if js_data.get("date_posted"):
                        job_details["date_posted"] = js_data["date_posted"]
                    job_details["easy_apply"] = js_data.get("easy_apply", False)
                    if js_data.get("hiring_team") and len(js_data["hiring_team"]) > 0:
                        job_details["hiring_team"] = js_data["hiring_team"]
                    if js_data.get("related_jobs") and len(js_data["related_jobs"]) > 0:
                        job_details["related_jobs"] = js_data["related_jobs"]
            except Exception as e:
                logger.warning(f"JS extraction failed: {e}")

            # --- Condensed Fallback Section ---

            # 1. Basic Info (Title/Company/Location)
            if any(
                job_details.get(k) == "NA" for k in ["title", "company", "location"]
            ):
                try:
                    basic_info = (
                        await self.job_details_extractor.extract_job_basic_info(
                            self.browser_manager.page
                        )
                    )
                    for key in ["title", "company", "location"]:
                        if job_details.get(key) == "NA" and basic_info.get(key):
                            job_details[key] = basic_info[key]
                    if (
                        basic_info.get("posted_date")
                        and job_details["date_posted"] == "NA"
                    ):
                        job_details["date_posted"] = basic_info["posted_date"]
                except Exception:
                    pass

            # 2. Description Fallback
            if job_details["description"] == "NA":
                job_details[
                    "description"
                ] = await self.job_details_extractor.extract_complete_job_description()

            # 3. Date Posted Fallback
            if job_details["date_posted"] == "NA":
                try:
                    for selector in ADDITIONAL_POSTED_DATE_SELECTORS:
                        element = await self.browser_manager.page.query_selector(
                            selector
                        )
                        if element and await element.is_visible():
                            text = await element.text_content()
                            if text and any(
                                w in text.lower()
                                for w in ["ago", "hour", "day", "week", "month"]
                            ):
                                job_details["date_posted"] = text.strip()
                                break
                except Exception:
                    pass

            # 4. Job Insights (Work fit, skills, etc.)
            try:
                insights = []
                # Work prefs
                elements = await self.browser_manager.page.query_selector_all(
                    ".job-details-fit-level-preferences .tvm__text--low-emphasis strong"
                )
                for el in elements:
                    if await el.is_visible():
                        t = await el.text_content()
                        if t and t.strip() and len(t) < 50:
                            insights.append(t.strip())

                # Metadata / Additional insights
                metadata = await self.job_details_extractor.extract_job_metadata()
                job_details.update({k: v for k, v in metadata.items() if v != "NA"})

                if insights:
                    current = job_details.get("job_insights", "NA")
                    job_details["job_insights"] = (
                        " | ".join(insights)
                        if current == "NA"
                        else f"{current} | {' | '.join(insights)}"
                    )
            except Exception as e:
                logger.debug(f"Insight extraction error: {e}")

            # 5. Apply info
            if job_details["apply_info"] == "NA":
                if job_details["easy_apply"]:
                    job_details["apply_info"] = "Easy Apply"
                else:
                    # Try to find external link
                    try:
                        for selector in ADDITIONAL_APPLY_BUTTON_SELECTORS:
                            btn = await self.browser_manager.page.query_selector(
                                selector
                            )
                            if btn and await btn.is_visible():
                                href = await btn.get_attribute("href")
                                if href and "linkedin.com" not in href:
                                    job_details["apply_info"] = href
                                    break
                    except Exception:
                        pass

            # 6. Skills
            try:
                skills_section = await self.browser_manager.page.query_selector(
                    SKILLS_SECTION_SELECTORS[0]
                )
                if skills_section:
                    skill_elements = await skills_section.query_selector_all("li")
                    skills = [await el.text_content() for el in skill_elements]
                    job_details["skills"] = [
                        s.strip() for s in skills if s and s.strip()
                    ]
            except Exception:
                pass

            # 7. Hiring Team Fallback (if JS extraction missed it)
            if job_details["hiring_team"] == "NA" or job_details["hiring_team"] == []:
                try:
                    hiring_team = await self.job_details_extractor.extract_hiring_team()
                    if hiring_team and len(hiring_team) > 0:
                        job_details["hiring_team"] = hiring_team
                except Exception as e:
                    logger.debug(f"Hiring team extraction error: {e}")

            # 8. Related Jobs Fallback (if JS extraction missed it)
            if job_details["related_jobs"] == "NA" or job_details["related_jobs"] == []:
                try:
                    related_jobs = (
                        await self.job_details_extractor.extract_related_jobs()
                    )
                    if related_jobs and len(related_jobs) > 0:
                        job_details["related_jobs"] = related_jobs
                except Exception as e:
                    logger.debug(f"Related jobs extraction error: {e}")

            return job_details

        except Exception as e:
            logger.error(f"Error extracting job details: {str(e)}")
            # Return a minimal job details object if extraction fails
            return {
                "url": job_url,
                "source": "linkedin",
                "scraped_at": datetime.now().isoformat(),
                "error": str(e),
                "title": "Error extracting job",
                "company": "Unknown",
                "location": "Unknown",
                "description": "Error extracting job details",
                "date_posted": "NA",
                "job_insights": "NA",
                "easy_apply": False,
                "apply_info": "NA",
                "company_info": "NA",
                "hiring_team": "NA",
                "related_jobs": "NA",
            }

    async def close(self) -> None:
        """Close the browser session."""
        if self.browser_manager:
            await self.browser_manager.close()

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Synchronous wrapper for backwards compatibility
class LinkedInScraperSync:
    """Synchronous wrapper for the async LinkedInScraper."""

    def __init__(
        self,
        headless: bool = False,
        timeout: int = DEFAULT_TIMEOUT,
        browser: str = "chromium",
        proxy: Optional[str] = None,
        anonymize: bool = True,
    ):
        self.scraper = LinkedInScraper(headless, timeout, browser, proxy, anonymize)
        self._loop = None

    def _run_async(self, coro):
        """Run an async coroutine in sync context."""
        try:
            # Check if there's already a running event loop
            loop = asyncio.get_running_loop()
            # If we're in an active event loop, we can't use run_until_complete
            # This happens when called from FastAPI/async context
            import threading
            import concurrent.futures

            # Run the coroutine in a separate thread with its own event loop
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()

        except RuntimeError:
            # No running event loop, safe to create our own
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
            return self._loop.run_until_complete(coro)

    def collect_job_links(
        self,
        keywords: str,
        location: str,
        max_pages: int = 1,
        experience_levels: Optional[List[str]] = None,
        date_posted: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> list:
        """Synchronous version of collect_job_links."""
        return self._run_async(
            self.scraper.collect_job_links(
                keywords, location, max_pages, experience_levels, date_posted, sort_by
            )
        )

    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """Synchronous version of get_job_details."""
        return self._run_async(self.scraper.get_job_details(job_url))

    def close(self) -> None:
        """Close the scraper session."""
        if self._loop:
            self._run_async(self.scraper.close())
            self._loop.close()
            self._loop = None
