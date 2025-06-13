"""
Main interface: LinkedInScraper class for job search automation using Playwright.
"""

import os
import logging
import dotenv
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

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
    SKILLS_SECTION_SELECTORS
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

    def __init__(self, headless: bool = False, timeout: int = DEFAULT_TIMEOUT, browser: str = "chromium", 
                 proxy: Optional[str] = None, anonymize: bool = True):
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

        logger.info("✅ LinkedIn credentials loaded successfully")        # Initialize components
        self.browser_manager = None
        self.auth_manager = None
        self.filter_manager = None
        self.job_links_extractor = None
        self.job_details_extractor = None
        self._setup_complete = False

    async def _ensure_setup(self):
        """Ensure all components are set up."""
        if not self._setup_complete:
            self.browser_manager = BrowserManager(self.browser, self.headless, self.timeout, self.proxy, self.anonymize)
            await self.browser_manager.setup_driver()
            
            self.auth_manager = AuthManager(self.browser_manager.page, self.timeout)
            self.filter_manager = FilterManager(self.browser_manager.page, self.timeout)
            self.job_links_extractor = JobLinksExtractor(self.browser_manager.page)
            self.job_details_extractor = JobDetailsExtractor(self.browser_manager.page, self.timeout)
            
            self._setup_complete = True

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
            filter_success = await self.filter_manager.apply_search_filters(experience_levels, date_posted)
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
            await self.browser_manager.scroll_job_list_container(job_list_container, total_expected)

            # Get all job cards from the page
            job_cards = await self.browser_manager.get_job_cards(job_list_container)
            if not job_cards:
                logger.warning("No job cards found on this page.")
                break

            # Extract job links from all cards
            page_links = await self.job_links_extractor.extract_job_links_from_cards(job_cards, current_page)
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
            # Navigate to job page
            await self.browser_manager.navigate_to(job_url, 3.0, 5.0)

            # Wait for job details to load
            description_selectors = JOB_DESCRIPTION_SELECTORS

            # Wait for page to load properly
            found_selector = False
            for selector in description_selectors:
                try:
                    await self.browser_manager.page.wait_for_selector(selector, timeout=self.timeout)
                    found_selector = True
                    break
                except PlaywrightTimeoutError:
                    continue

            if not found_selector:
                logger.warning("No job description elements found on page")            # Initialize job details with all required fields and defaults
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
                "related_jobs": "NA"
            }            # Extract basic job information
            basic_info = await self.job_details_extractor.extract_job_basic_info(self.browser_manager.page)
            job_details.update(basic_info)
            
            # Map basic_info fields to expected field names
            if basic_info.get("posted_date") and job_details["date_posted"] == "NA":
                job_details["date_posted"] = basic_info["posted_date"]# Extract job description with "See more" handling
            job_details["description"] = await self.job_details_extractor.extract_complete_job_description()            # Extract date_posted if not already found in basic_info
            if job_details["date_posted"] == "NA":
                try:
                    date_selectors = ADDITIONAL_POSTED_DATE_SELECTORS
                    
                    for selector in date_selectors:
                        try:
                            date_element = await self.browser_manager.page.query_selector(selector)
                            if date_element and await date_element.is_visible():
                                date_text = await date_element.text_content()
                                if date_text and date_text.strip():
                                    job_details["date_posted"] = date_text.strip()
                                    break
                        except Exception:
                            continue
                except Exception as e:
                    logger.debug(f"Could not extract date_posted: {e}")            # Extract job_insights (applicant count, work preferences, hiring urgency, etc.)
            try:
                insights = []
                
                # First, try to get work type preferences (Remote, Full-time, etc.)
                try:
                    work_prefs_elements = await self.browser_manager.page.query_selector_all(".job-details-fit-level-preferences .tvm__text--low-emphasis strong")
                    for element in work_prefs_elements:
                        if await element.is_visible():
                            pref_text = await element.text_content()
                            if pref_text and pref_text.strip():
                                pref_text = pref_text.strip()
                                if pref_text not in insights and len(pref_text) < 50:
                                    insights.append(pref_text)
                except Exception:
                    pass
                  # Then try other insight selectors
                insight_selectors = ADDITIONAL_JOB_INSIGHTS_SELECTORS
                
                for selector in insight_selectors:
                    try:
                        insight_elements = await self.browser_manager.page.query_selector_all(selector)
                        for element in insight_elements:
                            if await element.is_visible():
                                insight_text = await element.text_content()
                                if insight_text and insight_text.strip():
                                    insight_text = insight_text.strip()
                                    # Filter out date information and common duplicates
                                    if (insight_text not in insights and 
                                        len(insight_text) < 200 and 
                                        not any(word in insight_text.lower() for word in ['posted', 'ago', 'view job']) and
                                        (any(word in insight_text.lower() for word in ['applicant', 'application', 'review', 'hiring', 'skill', 'match', 'remote', 'full-time', 'part-time', 'contract', 'hybrid']) or
                                         insight_text.lower() in ['remote', 'full-time', 'part-time', 'contract', 'hybrid', 'on-site'])):
                                        insights.append(insight_text)
                    except Exception:
                        continue
                
                if insights:
                    job_details["job_insights"] = " | ".join(insights)
            except Exception as e:
                logger.debug(f"Could not extract job_insights: {e}")            # Extract easy_apply and apply_info
            try:
                apply_button_selectors = ADDITIONAL_APPLY_BUTTON_SELECTORS
                
                for selector in apply_button_selectors:
                    try:
                        apply_button = await self.browser_manager.page.query_selector(selector)
                        if apply_button and await apply_button.is_visible():
                            button_text = await apply_button.text_content()
                            if button_text:
                                button_text = button_text.strip()
                                if "easy apply" in button_text.lower():
                                    job_details["easy_apply"] = True
                                    job_details["apply_info"] = "Easy Apply"
                                elif any(word in button_text.lower() for word in ['apply', 'bewerben']):
                                    # Check if it's an external apply
                                    href = await apply_button.get_attribute("href")
                                    if href and "linkedin.com" not in href:
                                        # Direct external link
                                        job_details["apply_info"] = href
                                    else:
                                        # Try to extract external URL by using the job_details_extractor
                                        external_url = await self.job_details_extractor.extract_external_apply_url(apply_button)
                                        if external_url:
                                            job_details["apply_info"] = external_url
                                        else:
                                            job_details["apply_info"] = button_text
                                break
                    except Exception:
                        continue
            except Exception as e:
                logger.debug(f"Could not extract apply info: {e}")# Extract metadata: location and other details
            metadata = await self.job_details_extractor.extract_job_metadata()
            job_details.update(metadata)
              # Try additional location extraction if still "NA"
            if job_details["location"] == "NA":
                try:
                    # Try to get location from subtitle grouping (usually first element)
                    subtitle_elements = await self.browser_manager.page.query_selector_all(".jobs-unified-top-card__subtitle-secondary-grouping span")
                    for element in subtitle_elements:
                        if await element.is_visible():
                            location_text = await element.text_content()
                            if location_text and location_text.strip():
                                location_text = location_text.strip()
                                # Filter out date/time information and check if it looks like a location
                                if (not any(word in location_text.lower() for word in ['ago', 'posted', 'hour', 'day', 'week', 'month', 'applicant']) and
                                    len(location_text) > 2 and 
                                    not location_text.isdigit()):
                                    job_details["location"] = location_text
                                    break
                      # If still not found, try other location selectors
                    if job_details["location"] == "NA":
                        location_selectors = ADDITIONAL_LOCATION_SELECTORS
                        
                        for selector in location_selectors:
                            try:
                                location_element = await self.browser_manager.page.query_selector(selector)
                                if location_element and await location_element.is_visible():
                                    location_text = await location_element.text_content()
                                    if location_text and location_text.strip():
                                        # Filter out date/time information
                                        location_text = location_text.strip()
                                        if not any(word in location_text.lower() for word in ['ago', 'posted', 'hour', 'day', 'week', 'month']):
                                            job_details["location"] = location_text
                                            break
                            except Exception:
                                continue
                except Exception as e:
                    logger.debug(f"Could not extract additional location: {e}")            # Extract skills and qualifications if available
            try:
                skills_section = await self.browser_manager.page.query_selector(SKILLS_SECTION_SELECTORS[0])
                if skills_section:
                    skill_elements = await skills_section.query_selector_all("li")
                    skills = []
                    for skill_element in skill_elements:
                        skill_text = await skill_element.text_content()
                        if skill_text and skill_text.strip():
                            skills.append(skill_text.strip())
                    if skills:
                        job_details["skills"] = skills
            except Exception as e:
                logger.debug(f"Could not extract skills: {e}")            # Extract applicant count if available
            applicant_selectors = APPLICANT_COUNT_SELECTORS

            for selector in applicant_selectors:
                try:
                    applicant_elements = await self.browser_manager.page.query_selector_all(selector)
                    for element in applicant_elements:
                        if await element.is_visible():
                            applicant_text = await element.text_content()
                            if applicant_text and applicant_text.strip():
                                applicant_text = applicant_text.strip()
                                if (
                                    "applicant" in applicant_text.lower()
                                    or "application" in applicant_text.lower()
                                ):
                                    job_details["applicant_count"] = applicant_text
                                    break
                    if job_details.get("applicant_count"):
                        break
                except Exception:
                    continue            # Extract contact info if available
            contact_selectors = CONTACT_INFO_SELECTORS

            for selector in contact_selectors:
                try:
                    contact_elements = await self.browser_manager.page.query_selector_all(selector)
                    for element in contact_elements:
                        if await element.is_visible():
                            contact_text = await element.text_content()
                            if contact_text and contact_text.strip():
                                contact_text = contact_text.strip()
                                if "recruiter" in contact_text.lower():
                                    job_details["contact_info"] = contact_text
                                    break
                    if job_details.get("contact_info"):
                        break
                except Exception:
                    continue            # Extract company information if available
            try:
                company_info = await self.job_details_extractor.extract_company_info()
                if company_info and company_info.strip():
                    job_details["company_info"] = company_info
            except Exception as e:
                logger.debug(f"Could not extract company info: {e}")            # Try to get company website
            company_website_selectors = ADDITIONAL_COMPANY_WEBSITE_SELECTORS

            for selector in company_website_selectors:
                try:
                    website_elements = await self.browser_manager.page.query_selector_all(selector)
                    for element in website_elements:
                        if await element.is_visible():
                            website_url = await element.get_attribute("href")
                            if website_url and not ("linkedin.com" in website_url):
                                job_details["company_website"] = website_url
                                break
                    if job_details.get("company_website"):
                        break
                except Exception:
                    continue

            # Extract hiring team information
            try:
                hiring_team = await self.job_details_extractor.extract_hiring_team()
                if hiring_team and len(hiring_team) > 0:
                    job_details["hiring_team"] = hiring_team
            except Exception as e:
                logger.debug(f"Could not extract hiring team: {e}")

            # Extract related jobs
            try:
                related_jobs = await self.job_details_extractor.extract_related_jobs()
                if related_jobs and len(related_jobs) > 0:
                    job_details["related_jobs"] = related_jobs
            except Exception as e:
                logger.debug(f"Could not extract related jobs: {e}")

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
                "related_jobs": "NA"
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
    
    def __init__(self, headless: bool = False, timeout: int = DEFAULT_TIMEOUT, browser: str = "chromium",
                 proxy: Optional[str] = None, anonymize: bool = True):
        self.scraper = LinkedInScraper(headless, timeout, browser, proxy, anonymize)
        self._loop = None

    def _run_async(self, coro):
        """Run an async coroutine in sync context."""
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
