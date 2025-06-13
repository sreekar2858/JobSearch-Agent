"""
Main interface: LinkedInScraper class for job search automation.
"""

import os
import logging
import dotenv
from datetime import datetime
from typing import Dict, List, Optional, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .browser import BrowserManager
from .auth import AuthManager
from .filters import FilterManager
from .extractors import JobLinksExtractor, JobDetailsExtractor
from .config import DEFAULT_TIMEOUT
from .utils import random_sleep

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("linkedin_scraper")


class LinkedInScraper:
    """
    A class to scrape job listings from LinkedIn using Chrome or Firefox and Selenium.

    Features:
    - Search for jobs with keywords and location
    - Support for authenticated searches using LinkedIn credentials
    - Extraction of job titles, companies, locations, and URLs
    - Support for both Chrome and Firefox browsers
    - Handling of common scraping challenges (captchas, rate limits)
    """

    def __init__(self, headless: bool = False, timeout: int = DEFAULT_TIMEOUT, browser: str = "chrome"):
        """
        Initialize the LinkedIn scraper.

        ⚠️  LinkedIn login is REQUIRED for job scraping to work properly.
        Credentials must be configured in .env file or environment variables.

        Args:
            headless: Whether to run the browser in headless mode
            timeout: Wait timeout in seconds for page loading
            browser: Browser to use ('chrome' or 'firefox')
        """
        self.timeout = timeout
        self.headless = headless
        self.browser = browser.lower()
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
        self.browser_manager = BrowserManager(browser, headless, timeout)
        self.browser_manager.setup_driver()
        
        self.auth_manager = AuthManager(self.browser_manager.driver, timeout)
        self.filter_manager = FilterManager(self.browser_manager.driver, timeout)
        self.job_links_extractor = JobLinksExtractor(self.browser_manager.driver)
        self.job_details_extractor = JobDetailsExtractor(self.browser_manager.driver, timeout)

    @property
    def driver(self):
        """Get the WebDriver instance."""
        return self.browser_manager.driver

    def collect_job_links(
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
        if not self.driver:
            self.browser_manager.setup_driver()
        
        self.auth_manager.ensure_login(self.username, self.password)

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

        self.browser_manager.navigate_to(search_url, 3.0, 5.0)

        # Apply search filters if specified
        if experience_levels or date_posted:
            logger.info("Applying search filters...")
            filter_success = self.filter_manager.apply_search_filters(experience_levels, date_posted)
            if not filter_success:
                logger.warning("Some filters may not have been applied correctly")

        job_links = set()
        current_page = 1
        while current_page <= max_pages:
            logger.info(f"Collecting links from page {current_page} of {max_pages}")

            # Debug: analyze page structure
            logger.info("Analyzing page structure...")
            self.browser_manager.debug_page_structure()

            # Get total job count for this search
            total_expected = self.browser_manager.get_total_job_count()

            # Find the job list container
            job_list_container = self.browser_manager.find_job_list_container()

            # Scroll through the job list to load all cards
            self.browser_manager.scroll_job_list_container(job_list_container, total_expected)

            # Get all job cards from the page
            job_cards = self.browser_manager.get_job_cards(job_list_container)
            if not job_cards:
                logger.warning("No job cards found on this page.")
                break

            # Extract job links from all cards
            page_links = self.job_links_extractor.extract_job_links_from_cards(job_cards, current_page)
            job_links.update(page_links)

            logger.info(f"Collected {len(job_links)} unique job links so far.")

            # Check if we can go to next page
            pagination_info = self.job_links_extractor.get_pagination_info()
            logger.info(f"Pagination status: {pagination_info['page_state']}")

            if not pagination_info["has_next"]:
                logger.info("No next page available - reached end of results")
                break

            # Navigate to next page
            if not self.job_links_extractor.go_to_next_page():
                break

            current_page += 1
        return list(job_links)

    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific job posting.

        Args:
            job_url: URL of the job posting

        Returns:
            Dictionary containing detailed job information
        """
        if not self.driver:
            self.browser_manager.setup_driver()

        try:
            # Navigate to job page
            self.browser_manager.navigate_to(job_url, 3.0, 5.0)

            # Wait for job details to load
            description_selectors = [
                ".jobs-description",
                ".jobs-description-content",
                "#job-details",
                ".jobs-box__html-content",
                "[data-test-job-description]",
            ]

            # Wait for page to load properly
            for selector in description_selectors:
                try:
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except (TimeoutException, NoSuchElementException):
                    continue

            # Initialize job details with basic info
            job_details = {
                "url": job_url,
                "source": "linkedin",
                "scraped_at": datetime.now().isoformat(),
            }

            # Extract basic job information
            basic_info = self.job_details_extractor.extract_job_basic_info(self.driver)
            job_details.update(basic_info)

            # Extract job description with "See more" handling
            job_details["description"] = self.job_details_extractor.extract_complete_job_description()

            # Extract metadata: location, date_posted, skills, apply information
            metadata = self.job_details_extractor.extract_job_metadata()
            job_details.update(metadata)

            # Extract skills and qualifications if available
            try:
                skills_section = self.driver.find_element(
                    By.CSS_SELECTOR, ".jobs-description-details__list"
                )
                if skills_section:
                    job_details["skills"] = [
                        skill.text.strip()
                        for skill in skills_section.find_elements(By.TAG_NAME, "li")
                    ]
            except Exception as e:
                logger.debug(f"Could not extract skills: {e}")

            # Extract applicant count if available
            applicant_selectors = [
                ".jobs-unified-top-card__applicant-count",
                ".jobs-details-top-card__applicant-count",
                "[data-test-applicant-count]",
                ".jobs-details__top-card-applicant-count",
                ".jobs-unified-top-card__subtitle-secondary-grouping span[class*='applicant']",
            ]

            for selector in applicant_selectors:
                try:
                    applicant_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in applicant_elements:
                        if element.is_displayed():
                            applicant_text = element.text.strip()
                            if applicant_text and (
                                "applicant" in applicant_text.lower()
                                or "application" in applicant_text.lower()
                            ):
                                job_details["applicant_count"] = applicant_text
                                break
                    if job_details.get("applicant_count"):
                        break
                except NoSuchElementException:
                    continue

            # Extract contact info if available
            contact_selectors = [
                ".jobs-unified-top-card__job-insight--recruiter",
                ".jobs-details-top-card__job-posting-recruiter",
                ".jobs-poster__details",
            ]

            for selector in contact_selectors:
                try:
                    contact_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in contact_elements:
                        if element.is_displayed():
                            contact_text = element.text.strip()
                            if contact_text and "recruiter" in contact_text.lower():
                                job_details["contact_info"] = contact_text
                                break
                    if job_details.get("contact_info"):
                        break
                except NoSuchElementException:
                    continue

            # Extract company information if available
            company_info = self.job_details_extractor.extract_company_info()
            if company_info:
                job_details["company_info"] = company_info

            # Try to get company website
            company_website_selectors = [
                ".jobs-company__box a[href*='http']",
                ".jobs-company__content a[href*='http']",
                ".jobs-company-information a[href*='http']",
            ]

            for selector in company_website_selectors:
                try:
                    website_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in website_elements:
                        if element.is_displayed():
                            website_url = element.get_attribute("href")
                            if website_url and not ("linkedin.com" in website_url):
                                job_details["company_website"] = website_url
                                break
                    if job_details.get("company_website"):
                        break
                except NoSuchElementException:
                    continue

            # Extract hiring team information
            hiring_team = self.job_details_extractor.extract_hiring_team()
            job_details["hiring_team"] = hiring_team if hiring_team else "NA"

            # Extract related jobs
            related_jobs = self.job_details_extractor.extract_related_jobs()
            job_details["related_jobs"] = related_jobs if related_jobs else "NA"

            return job_details

        except Exception as e:
            logger.error(f"Error extracting job details: {str(e)}")
            return job_details

    def close(self) -> None:
        """Close the WebDriver session."""
        self.browser_manager.close()
