"""
LinkedIn job search scraper using Chrome or Firefox and Selenium.

This module provides functionality to:
- Search for jobs on LinkedIn based on keywords and location
- Collect job details from search results up to a specified page number
- Extract job titles, companies, locations, and URLs
- Support both Chrome and Firefox browsers
"""

import time
import logging
import random
import os
import dotenv
from datetime import datetime
from typing import Dict, List, Optional, Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

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
            self._setup_driver()  # Ensure login if required
        self._ensure_login()

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

        self._navigate_to(search_url, 3.0, 5.0)

        # Apply search filters if specified
        if experience_levels or date_posted:
            logger.info("Applying search filters...")
            filter_success = self._apply_search_filters(experience_levels, date_posted)
            if not filter_success:
                logger.warning("Some filters may not have been applied correctly")

        job_links = set()
        current_page = 1
        while current_page <= max_pages:
            logger.info(f"Collecting links from page {current_page} of {max_pages}")

            # Debug: analyze page structure
            logger.info("Analyzing page structure...")
            self._debug_page_structure()

            # Get total job count for this search
            total_expected = self._get_total_job_count()

            # Find the job list container
            job_list_container = self._find_job_list_container()

            # Scroll through the job list to load all cards
            self._scroll_job_list_container(job_list_container, total_expected)

            # Get all job cards from the page
            job_cards = self._get_job_cards(job_list_container)
            if not job_cards:
                logger.warning("No job cards found on this page.")
                break

            # Extract job links from all cards
            page_links = self._extract_job_links_from_cards(job_cards, current_page)
            job_links.update(page_links)

            logger.info(f"Collected {len(job_links)} unique job links so far.")

            # Check if we can go to next page
            pagination_info = self._get_pagination_info()
            logger.info(f"Pagination status: {pagination_info['page_state']}")

            if not pagination_info["has_next"]:
                logger.info("No next page available - reached end of results")
                break

            # Navigate to next page
            if not self._go_to_next_page():
                break

            current_page += 1
        return list(job_links)

    def __init__(
        self, headless: bool = False, timeout: int = 20, browser: str = "chrome"
    ):
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
        self.driver = None
        self.headless = headless
        self.browser = browser.lower()
        self.use_login = True  # Always use login - required for LinkedIn scraping
        self.retry_count = 0
        self.max_retries = 5

        # Validate browser choice
        if self.browser not in ["chrome", "firefox"]:
            raise ValueError(
                f"Unsupported browser: {browser}. Supported browsers: 'chrome', 'firefox'"
            )

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
        self._setup_driver()

    def _setup_driver(self) -> None:
        """Set up the WebDriver based on the selected browser."""
        if self.browser == "chrome":
            self._setup_chrome_driver()
        elif self.browser == "firefox":
            self._setup_firefox_driver()
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")

        # Common setup for all browsers
        self.driver.set_window_size(1920, 1080)

    def _setup_chrome_driver(self) -> None:
        """Set up the Chrome WebDriver."""
        options = Options()
        if self.headless:
            options.add_argument(
                "--headless=new"
            )  # Updated headless argument for Chrome

        # Add additional options to make the browser more stealthy
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Set user agent to mimic a regular browser
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )

        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def _setup_firefox_driver(self) -> None:
        """Set up the Firefox WebDriver."""
        options = FirefoxOptions()
        if self.headless:
            options.add_argument("--headless")

        # Add additional options to make the browser more stealthy
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")

        # Set preferences for Firefox
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference(
            "general.useragent.override",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
        )

        # Initialize the driver
        service = FirefoxService(GeckoDriverManager().install())
        self.driver = webdriver.Firefox(service=service, options=options)

    def _random_sleep(self, min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
        """
        Sleep for a random duration to mimic human behavior.

        Args:
            min_seconds: Minimum sleep time in seconds
            max_seconds: Maximum sleep time in seconds
        """
        time.sleep(random.uniform(min_seconds, max_seconds))

    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific job posting.

        Args:
            job_url: URL of the job posting

        Returns:
            Dictionary containing detailed job information
        """
        if not self.driver:
            self._setup_driver()

        try:
            # Navigate to job page
            self._navigate_to(job_url, 3.0, 5.0)

            # Wait for job details to load
            description_selectors = [
                ".jobs-description",
                ".jobs-description-content",
                "#job-details",
                ".jobs-box__html-content",
                "[data-test-job-description]",
            ]

            # Wait for page to load properly
            job_description = None
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
            }  # Extract basic job information using helper method
            basic_info = self._extract_job_basic_info(self.driver)
            job_details.update(basic_info)

            # Extract job description with "See more" handling
            job_details["description"] = self._extract_complete_job_description()

            # Extract metadata: location, date_posted, skills, apply information
            metadata = self._extract_job_metadata()
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
                    applicant_elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector
                    )
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
                    contact_elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector
                    )
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
            company_info_selectors = [
                ".jobs-company__box",
                ".jobs-company__content",
                ".jobs-company-information",
            ]

            for selector in company_info_selectors:
                try:
                    company_elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector
                    )
                    for element in company_elements:
                        if element.is_displayed():
                            company_info_text = element.text.strip()
                            if company_info_text:
                                job_details["company_info"] = company_info_text
                                break
                    if job_details.get("company_info"):
                        break
                except NoSuchElementException:
                    continue

            # Try to get company website
            company_website_selectors = [
                ".jobs-company__box a[href*='http']",
                ".jobs-company__content a[href*='http']",
                ".jobs-company-information a[href*='http']",
            ]

            for selector in company_website_selectors:
                try:
                    website_elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector
                    )
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
            hiring_team = self._extract_hiring_team()
            if hiring_team:
                job_details["hiring_team"] = hiring_team
            else:
                job_details["hiring_team"] = "NA"  # Extract related jobs
            related_jobs = self._extract_related_jobs()
            job_details["related_jobs"] = related_jobs if related_jobs else "NA"

            return job_details

        except Exception as e:
            logger.error(f"Error extracting job details from right pane: {str(e)}")
            # # Take a screenshot for debugging
            # screenshot_path = os.path.join("output", "linkedin", f"detail_extraction_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            # self.driver.save_screenshot(screenshot_path)
            # logger.info(f"Saved error screenshot to {screenshot_path}")
            return job_details

    def _extract_complete_job_description(self) -> str:
        """
        Extract the complete job description text content.
        Handles clicking "See more" button and captures the entire article text.

        Returns:
            Complete job description text
        """
        try:
            # Click "See more" button if present
            see_more_clicked = self._click_see_more_button()

            if see_more_clicked:
                logger.info("Description expanded, waiting for content to load")
                self._random_sleep(1.5, 2.5)

            description_text = "No description available"

            # First try to get the complete article element
            article_selectors = [
                "article.jobs-description__container",
                "article.jobs-description__container--condensed",
                ".jobs-description__container",
                "article[class*='jobs-description__container']",
            ]

            for selector in article_selectors:
                try:
                    article_element = self.driver.find_element(
                        By.CSS_SELECTOR, selector
                    )
                    if article_element and article_element.is_displayed():
                        text_content = article_element.text.strip()
                        if text_content:
                            description_text = text_content
                            logger.info(
                                f"Successfully extracted full job description ({len(text_content)} characters)"
                            )
                            break
                except (NoSuchElementException, Exception) as e:
                    logger.debug(
                        f"Could not extract article with selector {selector}: {e}"
                    )
                    continue

            # Try specific job details selector - this targets the main content area
            if (
                description_text == "No description available"
                or len(description_text) < 100
            ):
                try:
                    job_details_element = self.driver.find_element(
                        By.CSS_SELECTOR, "#job-details"
                    )
                    if job_details_element and job_details_element.is_displayed():
                        text_content = job_details_element.text.strip()
                        if text_content and len(text_content) > len(description_text):
                            description_text = text_content
                            logger.info(
                                f"Successfully extracted #job-details text ({len(text_content)} characters)"
                            )
                except (NoSuchElementException, Exception) as e:
                    logger.debug(f"Could not extract #job-details element: {e}")

            # If we couldn't get the article, try other selectors for just the content
            if description_text == "No description available":
                content_selectors = [
                    ".jobs-description__content.jobs-description-content",
                    ".jobs-description__content",
                    ".jobs-description-content",
                    ".jobs-box__html-content",
                    "div.jobs-box__html-content.jobs-description-content__text--stretch",
                    "[data-test-job-description]",
                    "div.jobs-box__html-content",
                ]

                for selector in content_selectors:
                    try:
                        content_element = self.driver.find_element(
                            By.CSS_SELECTOR, selector
                        )
                        if content_element and content_element.is_displayed():
                            text_content = content_element.text.strip()
                            if text_content:
                                description_text = text_content
                                logger.info(
                                    f"Extracted job description using selector {selector} ({len(text_content)} characters)"
                                )
                                break
                    except (NoSuchElementException, Exception) as e:
                        logger.debug(
                            f"Error extracting content with selector {selector}: {e}"
                        )
                        continue
            # Log the result
            if see_more_clicked:
                logger.info(
                    f"Extracted expanded job description ({len(description_text)} characters)"
                )
            else:
                logger.info(
                    f"Extracted job description without expansion ({len(description_text)} characters)"
                )

            return description_text

        except Exception as e:
            logger.error(f"Error extracting complete job description: {str(e)}")
            return "Error extracting description"

    def _login(self) -> bool:
        """
        Log in to LinkedIn using credentials (always required).

        Returns:
            True if login successful, False otherwise
        """
        if not self.username or not self.password:
            logger.error(
                "LinkedIn credentials are missing! Cannot proceed without authentication."
            )
            raise ValueError(
                "LinkedIn username and password are required for scraping."
            )

        try:
            logger.info(f"🔐 Attempting to login with username: {self.username}")

            # Navigate to LinkedIn login page
            self.driver.get("https://www.linkedin.com/login")
            self._random_sleep(2.0, 3.0)

            # Wait for the login form
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "username"))
            )

            # Fill in username and password
            username_field = self.driver.find_element(By.ID, "username")
            password_field = self.driver.find_element(By.ID, "password")

            username_field.clear()
            # Type like a human - character by character
            for char in self.username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))

            password_field.clear()
            for char in self.password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))

            # Click the login button
            login_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[type='submit']"
            )
            login_button.click()

            # Wait for the login to complete
            self._random_sleep(3.0, 5.0)

            # Check if login was successful by looking for elements that exist after login
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.ID, "global-nav"))
                )
                logger.info("Successfully logged in to LinkedIn")
                return True
            except TimeoutException:
                # Try an alternative selector
                try:
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".nav-main"))
                    )
                    logger.info(
                        "Successfully logged in to LinkedIn (alternative check)"
                    )
                    return True
                except TimeoutException:
                    logger.error("Failed to login - could not find post-login elements")

                    # Check for security verification
                    if self._check_for_captcha():
                        logger.warning(
                            "Security verification required after login. Please check the browser."
                        )

                    return False

        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False

    def _check_for_captcha(self) -> bool:
        """
        Check if the page is showing a CAPTCHA or security verification.
        More conservative approach to avoid false positives.

        Returns:
            True if a CAPTCHA is detected, False otherwise
        """
        try:
            # # Take a screenshot to help with debugging
            # os.makedirs(os.path.join("output", "linkedin"), exist_ok=True)
            # screenshot_path = os.path.join("output", "linkedin", f"page_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            # self.driver.save_screenshot(screenshot_path)

            # First check: Look for job listing elements to verify we're on the results page
            job_listing_selectors = [
                ".jobs-search__results-list",
                ".scaffold-layout__list",
                ".job-search-results",
                "ul.jobs-search-results__list",
                ".jobs-search-results-list",
            ]

            for selector in job_listing_selectors:
                if self.driver.find_elements(By.CSS_SELECTOR, selector):
                    logger.info("Job listings found, definitely not a CAPTCHA page")
                    return False

            # If no job listings, check more cautiously for CAPTCHA elements
            # Only consider elements that are currently visible
            captcha_indicators = [
                "//h1[contains(text(), 'Security Verification') and not(ancestor::*[contains(@style,'display: none')])]",
                "//div[contains(text(), 'CAPTCHA') and not(ancestor::*[contains(@style,'display: none')])]",
                "//div[contains(text(), 'security check') and not(ancestor::*[contains(@style,'display: none')])]",
                "//form[contains(@action, 'checkpoint') and not(ancestor::*[contains(@style,'display: none')])]",
                "//input[@name='captcha' and not(ancestor::*[contains(@style,'display: none')])]",
                "//img[contains(@src, 'captcha') and not(ancestor::*[contains(@style,'display: none')])]",
                "//iframe[contains(@src, 'captcha') or contains(@src, 'recaptcha')]",
            ]

            # Check for visible CAPTCHA indicators
            for indicator in captcha_indicators:
                elements = self.driver.find_elements(By.XPATH, indicator)
                for element in elements:
                    if element.is_displayed():
                        logger.warning(
                            "CAPTCHA or security verification detected and is visible"
                        )
                        captcha_path = os.path.join(
                            "output",
                            "linkedin",
                            f"captcha_confirmed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        )
                        self.driver.save_screenshot(captcha_path)

                        # Try to get the text of the verification page for better debugging
                        try:
                            body_text = self.driver.find_element(
                                By.TAG_NAME, "body"
                            ).text
                            logger.info(f"CAPTCHA page text: {body_text[:500]}...")
                        except:
                            pass

                        return True

            # No visible CAPTCHA indicators and no job listings - might be loading or another page
            # Check for LinkedIn main structure to confirm we're not on a CAPTCHA page
            linkedin_main_elements = [
                "#global-nav",
                ".nav-main",
                ".search-global-typeahead",
                ".feed-identity-module",
            ]

            for selector in linkedin_main_elements:
                if self.driver.find_elements(By.CSS_SELECTOR, selector):
                    logger.info(
                        "LinkedIn main elements found, likely not a CAPTCHA page"
                    )
                    return False

            # Final check: Explicitly look for "No results found" message
            no_results_selectors = [
                "//h1[contains(text(), 'No matching')]",
                "//div[contains(text(), 'No matching')]",
                "//p[contains(text(), 'No matching')]",
            ]

            for selector in no_results_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        logger.info("'No results' message found, not a CAPTCHA page")
                        return False

            # If we've reached here, we don't have job listings or LinkedIn main elements
            # But we also don't have visible CAPTCHA elements
            # Take a closer look at the page content
            page_title = self.driver.title
            logger.info(f"Current page title: {page_title}")

            if "Security Verification" in page_title or "CAPTCHA" in page_title:
                logger.warning("CAPTCHA detected from page title")
                captcha_path = os.path.join(
                    "output",
                    "linkedin",
                    f"captcha_from_title_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                )
                self.driver.save_screenshot(captcha_path)
                return True

            # If we got this far, it's probably not a CAPTCHA
            return False

        except Exception as e:
            logger.error(f"Error checking for CAPTCHA: {str(e)}")
            return False

    def _handle_rate_limiting(self) -> bool:
        """
        Handle rate limiting by pausing and retrying.

        Returns:
            True if the rate limiting was handled, False if max retries exceeded
        """
        if self.retry_count >= self.max_retries:
            logger.error(
                "Maximum retry attempts reached. LinkedIn may be rate-limiting requests."
            )
            return False

        # Increase wait time with each retry
        wait_time = 15 + (self.retry_count * 10)
        logger.info(
            f"Rate limiting detected. Waiting {wait_time} seconds before retrying..."
        )
        time.sleep(wait_time)

        self.retry_count += 1
        return True

    def close(self) -> None:
        """Close the WebDriver session."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("WebDriver session closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver session: {str(e)}")
                self.driver = None

    def _extract_job_details_from_right_pane(self) -> Dict[str, Any]:
        """
        Extract detailed job information from the right-hand pane in LinkedIn jobs view.

        Returns:
            Dictionary containing all available job details including company info, hiring team, and related jobs
        """
        job_details = {
            "source": "linkedin",
            "scraped_at": datetime.now().isoformat(),
        }

        try:
            # Wait for job details to load
            detail_container_selectors = [
                ".jobs-details",
                ".job-details-jobs-unified-top-card__container",
                ".jobs-search__job-details--container",
                ".jobs-search-two-pane__details",
                ".jobs-unified-top-card",
                ".jobs-search-results-list__list-item--active",
                ".jobs-details__main-content",
                ".scaffold-layout__detail",
            ]

            container_found = False
            for selector in detail_container_selectors:
                try:
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    container_found = True
                    logger.info(
                        f"Found job details container with selector: {selector}"
                    )
                    break
                except TimeoutException:
                    continue

            if not container_found:
                logger.warning("Could not find job details container")
                return job_details

            # Scroll to ensure job details pane is fully loaded
            self.driver.execute_script(
                "document.querySelector('.jobs-details, .scaffold-layout__detail').scrollTo(0, 0);"
            )
            self._random_sleep(1.0, 2.0)

            # Extract job URL and ID from current URL
            try:
                current_url = self.driver.current_url
                if "/jobs/view/" in current_url:
                    job_id = (
                        current_url.split("/jobs/view/")[1].split("/")[0].split("?")[0]
                    )
                    if job_id:
                        job_details["job_id"] = job_id
                        job_details["url"] = (
                            f"https://www.linkedin.com/jobs/view/{job_id}/"
                        )
                        logger.debug(f"Extracted job ID: {job_id}")
            except Exception as e:
                logger.debug(f"Could not extract job ID from URL: {e}")

            # Extract job title
            title_selectors = [
                ".jobs-unified-top-card__job-title",
                ".job-details-jobs-unified-top-card__job-title",
                "h1.jobs-unified-top-card__job-title",
                "h1[data-test-job-title]",
                "h1[data-test-job-card-title]",
                "h1.t-24",
                "h1",
                ".job-card-container__title",
                ".job-title",
            ]

            for selector in title_selectors:
                try:
                    title_elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector
                    )
                    for title_element in title_elements:
                        if title_element.is_displayed() and title_element.text.strip():
                            job_details["title"] = title_element.text.strip()
                            logger.debug(f"Extracted job title: {job_details['title']}")
                            break
                    if job_details.get("title"):
                        break
                except NoSuchElementException:
                    continue

            # Extract company name
            company_selectors = [
                ".jobs-unified-top-card__company-name",
                ".job-details-jobs-unified-top-card__company-name",
                "a.jobs-unified-top-card__company-name",
                "[data-test-job-company-name]",
                ".jobs-details__top-card-company-url",
                ".jobs-details__top-card-company-name",
                ".job-card-container__company-name",
                ".artdeco-entity-lockup__subtitle",
                ".company-name",
            ]

            for selector in company_selectors:
                try:
                    company_elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector
                    )
                    for company_element in company_elements:
                        if (
                            company_element.is_displayed()
                            and company_element.text.strip()
                        ):
                            job_details["company"] = company_element.text.strip()
                            logger.debug(
                                f"Extracted company name: {job_details['company']}"
                            )
                            break
                    if job_details.get("company"):
                        break
                except NoSuchElementException:
                    continue

            # Extract location
            location_selectors = [
                ".jobs-unified-top-card__bullet",
                ".job-details-jobs-unified-top-card__bullet",
                ".jobs-unified-top-card__workplace-type",
                "[data-test-job-location]",
            ]

            for selector in location_selectors:
                try:
                    location_elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector
                    )
                    for element in location_elements:
                        if element.is_displayed() and element.text.strip():
                            location_text = element.text.strip()
                            # Make sure it's not a posting date
                            if not any(
                                time_word in location_text.lower()
                                for time_word in [
                                    "ago",
                                    "hour",
                                    "day",
                                    "week",
                                    "month",
                                    "minute",
                                ]
                            ):
                                job_details["location"] = location_text
                                logger.debug(
                                    f"Extracted location: {job_details['location']}"
                                )
                                break
                    if job_details.get("location"):
                        break
                except NoSuchElementException:
                    continue

            # Extract company logo if available
            logo_selectors = [
                ".jobs-details-top-card__company-logo",
                ".jobs-unified-top-card__company-logo",
                ".jobs-details__top-card-company-logo",
                ".artdeco-entity-image",
                ".artdeco-entity-lockup__image img",
                ".ivm-view-attr__img--centered",
            ]

            for selector in logo_selectors:
                try:
                    logo_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for logo in logo_elements:
                        if logo.is_displayed():
                            logo_url = logo.get_attribute("src")
                            if logo_url:
                                job_details["company_logo"] = logo_url
                                logger.debug(
                                    f"Extracted company logo: {job_details['company_logo']}"
                                )
                                break
                    if job_details.get("company_logo"):
                        break
                except NoSuchElementException:
                    continue

            # Click "See more" button to expand full job description
            self._click_see_more_button()

            # Extract full job description
            description_selectors = [
                ".jobs-description-content",
                ".jobs-description__content",
                "#job-details",
                ".jobs-box__html-content",
                "[data-test-job-description]",
                ".jobs-description-content__text",
                ".jobs-description .jobs-description-content__text",
            ]

            job_details["description"] = "No description available"
            for selector in description_selectors:
                try:
                    description_element = self.driver.find_element(
                        By.CSS_SELECTOR, selector
                    )
                    if description_element.is_displayed():
                        job_details["description"] = description_element.text.strip()
                        break
                except NoSuchElementException:
                    continue

            # Extract metadata: location, date_posted, skills, apply information
            metadata = self._extract_job_metadata()
            job_details.update(metadata)

            # Extract company information
            company_info = self._extract_company_info()
            if company_info:
                job_details["company_info"] = company_info  # Extract hiring team
            hiring_team = self._extract_hiring_team()
            job_details["hiring_team"] = hiring_team if hiring_team else "NA"

            # Extract related jobs
            related_jobs = self._extract_related_jobs()
            job_details["related_jobs"] = related_jobs if related_jobs else "NA"

            # Log the extracted job details
            logger.info(
                f"Extracted job details: {job_details.get('title', 'Unknown')} at {job_details.get('company', 'Unknown')}"
            )

            return job_details

        except Exception as e:
            logger.error(f"Error extracting job details from right pane: {str(e)}")
            return job_details

    def _extract_job_metadata(self) -> Dict[str, Any]:
        """
        Extract specific job metadata from LinkedIn job page:
        - Location and date_posted from tertiary description container (first two spans)
        - Skills from job insight button
        - Easy Apply status and apply information

        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {}

        try:
            # Extract location and date_posted from tertiary description container
            # Structure: .job-details-jobs-unified-top-card__primary-description-container
            #           -> .job-details-jobs-unified-top-card__tertiary-description-container
            #           -> spans with .tvm__text.tvm__text--low-emphasis
            logger.debug(
                "Extracting location and date_posted from tertiary description container"
            )

            tertiary_selectors = [
                ".job-details-jobs-unified-top-card__primary-description-container .job-details-jobs-unified-top-card__tertiary-description-container",
                ".job-details-jobs-unified-top-card__tertiary-description-container",
                ".jobs-unified-top-card__tertiary-description-container",
            ]

            tertiary_container = None
            for selector in tertiary_selectors:
                try:
                    tertiary_container = self.driver.find_element(
                        By.CSS_SELECTOR, selector
                    )
                    if tertiary_container:
                        logger.debug(
                            f"Found tertiary container with selector: {selector}"
                        )
                        break
                except NoSuchElementException:
                    continue

            if tertiary_container:
                # Get all span elements with the low-emphasis text class
                span_selectors = [
                    ".tvm__text.tvm__text--low-emphasis",
                    ".tvm__text",
                    "span.tvm__text--low-emphasis",
                    "span",
                ]

                spans = []
                for span_selector in span_selectors:
                    try:
                        spans = tertiary_container.find_elements(
                            By.CSS_SELECTOR, span_selector
                        )
                        if spans:
                            logger.debug(
                                f"Found {len(spans)} spans with selector: {span_selector}"
                            )
                            break
                    except:
                        continue

                # Extract text from valid spans (skip separators like "·")
                valid_spans = []
                for span in spans:
                    text = span.text.strip()
                    if text and text != "·" and len(text) > 1:
                        valid_spans.append(text)
                        logger.debug(f"Valid span text: '{text}'")

                # First valid span should be location
                if len(valid_spans) >= 1:
                    metadata["location"] = valid_spans[0]
                    logger.debug(f"Extracted location: {valid_spans[0]}")

                # Second valid span should be date_posted
                if len(valid_spans) >= 2:
                    # Look for date-like content in subsequent spans
                    for span_text in valid_spans[1:]:
                        if any(
                            indicator in span_text.lower()
                            for indicator in [
                                "ago",
                                "week",
                                "day",
                                "month",
                                "hour",
                                "minute",
                                "posted",
                            ]
                        ):
                            metadata["date_posted"] = span_text
                            logger.debug(f"Extracted date_posted: {span_text}")
                            break
            else:
                logger.debug("Could not find tertiary description container")

            # Extract skills from job insight button
            logger.debug("Extracting skills from job insight button")

            skills_selectors = [
                ".job-details-jobs-unified-top-card__job-insight-text-button",
                ".job-details-jobs-unified-top-card__job-insight button",
                ".jobs-unified-top-card__job-insight-text-button",
                "button[aria-label*='Skills']",
                "button[data-tracking-control-name*='skills']",
            ]

            for selector in skills_selectors:
                try:
                    skills_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if skills_button and skills_button.is_displayed():
                        skills_text = skills_button.text.strip()
                        logger.debug(f"Skills button text: '{skills_text}'")

                        if skills_text and (
                            "Skills:" in skills_text or "skill" in skills_text.lower()
                        ):
                            # Remove "Skills:" prefix and parse
                            skills_content = skills_text.replace("Skills:", "").strip()

                            # Split by commas and clean up
                            if "," in skills_content:
                                skills_list = [
                                    skill.strip()
                                    for skill in skills_content.split(",")
                                    if skill.strip()
                                ]
                            else:
                                # Single skill or space-separated
                                skills_list = (
                                    skills_content.split() if skills_content else []
                                )

                            # Handle "+X more" pattern and extract actual skills
                            processed_skills = []
                            import re

                            for skill in skills_list:
                                if re.search(
                                    r"\+\d+\s*(more|additional)", skill.lower()
                                ):
                                    # Extract number if present
                                    match = re.search(r"\+(\d+)", skill)
                                    if match:
                                        metadata["additional_skills_count"] = int(
                                            match.group(1)
                                        )
                                else:
                                    # Clean skill name
                                    clean_skill = re.sub(
                                        r"[^\w\s\+#\.-]", "", skill
                                    ).strip()
                                    if clean_skill and len(clean_skill) > 1:
                                        processed_skills.append(clean_skill)

                            if processed_skills:
                                metadata["skills"] = processed_skills
                                logger.debug(f"Extracted skills: {processed_skills}")
                            break
                except (NoSuchElementException, Exception) as e:
                    logger.debug(f"Skills selector '{selector}' failed: {e}")
                    continue
            # Extract job insights (workplace type, job type, etc.)
            logger.debug("Extracting job insights")

            try:
                job_insights = []
                insight_selectors = [
                    ".job-details-jobs-unified-top-card__job-insight",
                    ".jobs-unified-top-card__job-insight",
                    ".job-details-jobs-unified-top-card__insights li",
                ]

                for selector in insight_selectors:
                    try:
                        insight_elements = self.driver.find_elements(
                            By.CSS_SELECTOR, selector
                        )
                        if insight_elements:
                            logger.debug(
                                f"Found {len(insight_elements)} insight elements with selector: {selector}"
                            )

                            for insight_element in insight_elements:
                                try:
                                    # Extract all text content from this insight element
                                    insight_text = insight_element.text.strip()

                                    if insight_text:
                                        # Clean up the text by removing extra whitespace and newlines
                                        clean_text = " ".join(insight_text.split())
                                        if (
                                            clean_text
                                            and clean_text not in job_insights
                                        ):
                                            job_insights.append(clean_text)
                                            logger.debug(
                                                f"Extracted insight text: {clean_text}"
                                            )

                                except Exception as insight_error:
                                    logger.debug(
                                        f"Error processing individual insight: {insight_error}"
                                    )
                                    continue

                            break  # Found insights with this selector
                    except:
                        continue  # Store all insights as a simple list of strings
                if job_insights:
                    metadata["job_insights"] = job_insights
                    logger.debug(f"Extracted job insights: {job_insights}")
                else:
                    metadata["job_insights"] = "NA"
                    logger.debug("No job insights found")

            except Exception as e:
                metadata["job_insights"] = "NA"
                logger.debug(f"Could not extract job insights: {e}")

            # Extract Easy Apply status and apply information
            logger.debug("Extracting apply information")

            apply_selectors = [
                "button",
                "a[role='button']",
                "[role='link']",
                ".jobs-apply-button",
                "#jobs-apply-button-id",
                ".jobs-s-apply button",
                ".jobs-s-apply .jobs-apply-button",
                "button[aria-label*='Apply']",
            ]

            found_apply_button = False

            for selector in apply_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.debug(
                        f"Found {len(buttons)} elements with selector: {selector}"
                    )

                    for i, button in enumerate(buttons):
                        if button.is_displayed():
                            try:
                                button_text = button.text.strip()
                                aria_label = button.get_attribute("aria-label") or ""
                                button_role = button.get_attribute("role") or ""
                                href = button.get_attribute("href") or ""
                                class_name = button.get_attribute("class") or ""

                                # Check if it's an apply button
                                if (
                                    "Apply" in button_text or "Apply" in aria_label
                                ) and button_text:
                                    found_apply_button = True
                                    logger.debug(
                                        f"Apply button found - text: '{button_text}', aria-label: '{aria_label}', href: '{href}'"
                                    )

                                    # Check if it's Easy Apply
                                    if (
                                        "Easy Apply" in button_text
                                        or "Easy Apply" in aria_label
                                    ):
                                        metadata["easy_apply"] = True
                                        metadata["apply_info"] = "Easy Apply"
                                        logger.debug("This is an Easy Apply button")
                                    else:
                                        # This is an external apply button
                                        metadata["easy_apply"] = False
                                        logger.debug(
                                            "This appears to be an EXTERNAL apply button"
                                        )
                                        # Try to extract the external apply URL
                                        apply_url = self._extract_external_apply_url(
                                            button
                                        )

                                        if apply_url:
                                            metadata["apply_info"] = apply_url
                                            logger.debug(
                                                f"✅ SUCCESS: Extracted URL: {apply_url}"
                                            )
                                        else:
                                            # Even if we can't extract the URL, don't return "NA"
                                            metadata["apply_info"] = (
                                                f"External application - {button_text}"
                                            )
                                            logger.debug(
                                                f"❌ Could not extract URL, but found external apply button: {button_text}"
                                            )

                                    break  # Found our apply button, stop looking

                            except Exception as button_error:
                                logger.debug(
                                    f"Error examining button {i + 1}: {button_error}"
                                )

                    if found_apply_button:
                        break  # Found apply button, stop searching selectors

                except Exception as selector_error:
                    logger.debug(f"Selector {selector} failed: {selector_error}")
                    continue

            # Set defaults if no apply button found
            if "easy_apply" not in metadata:
                metadata["easy_apply"] = False
                metadata["apply_info"] = "NA"
                logger.debug("No apply button found, set defaults")

            logger.debug(f"Final metadata extracted: {metadata}")
            return metadata
        except Exception as e:
            logger.error(f"Error extracting job metadata: {str(e)}")
            return metadata

    def _extract_apply_url_from_page_source(self) -> str:
        """
        Extract apply URL from page source as a fallback method.

        Returns:
            The external apply URL if found, None otherwise
        """
        try:
            # Get the job ID to look for apply URL patterns
            current_url = self.driver.current_url
            if "/jobs/view/" in current_url:
                job_id = current_url.split("/jobs/view/")[1].split("/")[0].split("?")[0]

                # Look for apply URL patterns in page source
                page_source = self.driver.page_source
                import re

                # Common patterns for external apply URLs
                patterns = [
                    rf'"applyUrl":"([^"]*)"',
                    rf'"externalApplyUrl":"([^"]*)"',
                    rf'"companyApplyUrl":"([^"]*)"',
                    rf'data-apply-url="([^"]*)"',
                    rf'applyUrl["\']?\s*:\s*["\']([^"\']*)["\']',
                    rf'apply.*?url["\']?\s*:\s*["\']([^"\']*)["\']',
                    rf'href\s*=\s*["\']([^"\']*apply[^"\']*)["\']',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    for match in matches:
                        if match and match.startswith("http"):
                            apply_url = match.replace("\\u0026", "&").replace(
                                "\\/", "/"
                            )
                            logger.debug(
                                f"Found apply URL from page source pattern '{pattern}': {apply_url}"
                            )
                            return apply_url

        except Exception as url_extract_error:
            logger.debug(
                f"Could not extract apply URL from page source: {url_extract_error}"
            )

        return None

    def _get_pagination_info(self) -> Dict[str, Any]:
        """
        Extract pagination information from the LinkedIn jobs search page.

        Returns:
            Dictionary containing current page, total pages, and next page availability
        """
        pagination_info = {
            "current_page": 1,
            "total_pages": 1,
            "has_next": False,
            "page_state": "",
        }

        try:
            # Extract pagination state text (e.g., "Page 1 of 30")
            page_state_selectors = [
                ".jobs-search-pagination__page-state",
                ".jobs-search-results-list__pagination .jobs-search-pagination__page-state",
                "p.jobs-search-pagination__page-state",
            ]

            for selector in page_state_selectors:
                try:
                    page_state_element = self.driver.find_element(
                        By.CSS_SELECTOR, selector
                    )
                    if page_state_element and page_state_element.is_displayed():
                        page_state = page_state_element.text.strip()
                        pagination_info["page_state"] = page_state

                        # Parse "Page X of Y" format
                        if "Page" in page_state and "of" in page_state:
                            parts = page_state.split()
                            try:
                                current_page = int(parts[1])
                                total_pages = int(parts[3])
                                pagination_info["current_page"] = current_page
                                pagination_info["total_pages"] = total_pages
                                logger.debug(
                                    f"Extracted pagination: Page {current_page} of {total_pages}"
                                )
                            except (IndexError, ValueError) as e:
                                logger.debug(f"Could not parse pagination numbers: {e}")
                        break
                except NoSuchElementException:
                    continue

            # Check if "Next" button is available and enabled
            next_button_selectors = [
                "button.jobs-search-pagination__button--next",
                ".jobs-search-pagination__button--next",
                "button[aria-label='View next page']",
            ]

            for selector in next_button_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if (
                        next_button
                        and next_button.is_displayed()
                        and next_button.is_enabled()
                        and "disabled" not in next_button.get_attribute("class")
                    ):
                        pagination_info["has_next"] = True
                        logger.debug("Next button is available and enabled")
                        break
                except NoSuchElementException:
                    continue

            # Get list of available page numbers
            page_buttons = []
            page_button_selectors = [
                ".jobs-search-pagination__indicator-button",
                ".jobs-search-pagination__pages .jobs-search-pagination__indicator button",
            ]

            for selector in page_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed():
                            button_text = button.text.strip()
                            if button_text.isdigit():
                                page_buttons.append(int(button_text))
                    if page_buttons:
                        break
                except Exception as e:
                    logger.debug(f"Could not extract page buttons: {e}")
                    continue

            if page_buttons:
                pagination_info["available_pages"] = sorted(page_buttons)
                logger.debug(
                    f"Available page buttons: {pagination_info['available_pages']}"
                )

        except Exception as e:
            logger.debug(f"Error extracting pagination info: {e}")

        return pagination_info

    # Helper methods for reducing code duplication

    def _extract_text_by_selectors(
        self, element, selectors: List[str], element_name: str = "element"
    ) -> Optional[str]:
        """
        Extract text from an element using multiple selectors as fallback.

        Args:
            element: WebElement to search within (can be driver for page-level searches)
            selectors: List of CSS selectors to try
            element_name: Name for logging purposes

        Returns:
            First non-empty text found, or None if nothing found
        """
        for selector in selectors:
            try:
                candidates = element.find_elements(By.CSS_SELECTOR, selector)
                for candidate in candidates:
                    if candidate.is_displayed():
                        text = candidate.text.strip()
                        if text:
                            logger.debug(
                                f"Extracted {element_name} using selector '{selector}': {text}"
                            )
                            return text
            except (NoSuchElementException, StaleElementReferenceException):
                continue
            except Exception as e:
                logger.debug(
                    f"Error with selector '{selector}' for {element_name}: {e}"
                )
                continue

        logger.debug(
            f"Could not extract {element_name} with any of the provided selectors"
        )
        return None

    def _navigate_to(
        self, url: str, min_wait: float = 3.0, max_wait: float = 5.0
    ) -> None:
        """
        Navigate to a URL and wait for page load.

        Args:
            url: URL to navigate to
            min_wait: Minimum wait time in seconds

            max_wait: Maximum wait time in seconds
        """
        logger.info(f"Navigating to: {url}")
        self.driver.get(url)
        self._random_sleep(min_wait, max_wait)

    def _save_screenshot(self, label: str, subfolder: str = "linkedin") -> str:
        """
        Save a screenshot with timestamp and return the path.

        Args:
            label: Descriptive label for the screenshot
            subfolder: Subfolder within output directory

        Returns:
            Path to saved screenshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_dir = os.path.join("output", subfolder)
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, f"{label}_{timestamp}.png")

        try:
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Saved screenshot to {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return ""

    def _ensure_login(self) -> bool:
        """
        Ensure user is logged in (always required for LinkedIn scraping).
        Centralized login check to avoid repetition.

        Returns:
            True if logged in successfully, False if login failed
        """
        if not hasattr(self, "_login_attempted"):
            self._login_attempted = False
            self._login_successful = False

        if not self._login_attempted:
            logger.info("🔐 Attempting LinkedIn login (required for job scraping)...")
            self._login_successful = self._login()
            self._login_attempted = True

            if self._login_successful:
                logger.info("✅ Successfully logged in to LinkedIn")
            else:
                logger.error(
                    "❌ Login failed! Cannot proceed without LinkedIn authentication."
                )
                raise RuntimeError(
                    "LinkedIn login is required for job scraping but failed. "
                    "Please check your credentials in the .env file."
                )

        return self._login_successful

    def _extract_job_basic_info(self, element) -> Dict[str, str]:
        """
        Extract basic job information (title, company, location, date) from an element.
        Centralized to avoid duplication across methods.

        Args:
            element: WebElement containing job information

        Returns:
            Dictionary with job basic information
        """
        job_info = {}

        # Job title selectors
        title_selectors = [
            ".jobs-unified-top-card__job-title",
            ".job-details-jobs-unified-top-card__job-title",
            "h1.jobs-unified-top-card__job-title",
            "h1[data-test-job-title]",
            "h1[data-test-job-card-title]",
            "h1.t-24",
            "h1",
            ".job-card-container__title",
            ".job-title",
        ]

        title = self._extract_text_by_selectors(element, title_selectors, "job title")
        if title:
            job_info["title"] = title

        # Company name selectors
        company_selectors = [
            ".jobs-unified-top-card__company-name",
            ".job-details-jobs-unified-top-card__company-name",
            "a.jobs-unified-top-card__company-name",
            "[data-test-job-company-name]",
            ".jobs-details__top-card-company-url",
            ".jobs-details__top-card-company-name",
            ".job-card-container__company-name",
            ".artdeco-entity-lockup__subtitle",
            ".company-name",
        ]

        company = self._extract_text_by_selectors(
            element, company_selectors, "company name"
        )
        if company:
            job_info["company"] = company

        # Location selectors
        location_selectors = [
            ".jobs-unified-top-card__bullet",
            ".job-details-jobs-unified-top-card__bullet",
            ".jobs-unified-top-card__workplace-type",
            "[data-test-job-location]",
            ".job-card-container__location",
            ".location",
        ]

        location = self._extract_text_by_selectors(
            element, location_selectors, "job location"
        )
        if location:
            job_info["location"] = location

        # Posted date selectors
        date_selectors = [
            ".jobs-unified-top-card__posted-date",
            ".jobs-details-job-summary__text--ellipsis",
            "[data-test-job-posted-date]",
            ".job-card-container__posted-date",
            ".posted-date",
        ]

        posted_date = self._extract_text_by_selectors(
            element, date_selectors, "posted date"
        )
        if posted_date:
            job_info["posted_date"] = posted_date

        return job_info

    def _click_see_more_button(self) -> bool:
        """
        Find and click the "See more" button if present.
        Centralized to avoid duplication.

        Returns:
            True if button was found and clicked, False otherwise
        """
        see_more_selectors = [
            "button.jobs-description__footer-button",
            "button[aria-label*='see more']",
            "button[aria-label*='Click to see more description']",
            ".jobs-description__footer-button",
            "button.artdeco-button--tertiary:contains('See more')",
            "button[class*='jobs-description__footer-button']",
            "button.artdeco-button.artdeco-button--tertiary.artdeco-button--fluid",
        ]

        for selector in see_more_selectors:
            try:
                see_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for see_more_button in see_more_buttons:
                    if (
                        see_more_button
                        and see_more_button.is_displayed()
                        and see_more_button.is_enabled()
                    ):
                        # Check if the button text contains "See more" or similar
                        button_text = see_more_button.text.lower()
                        if "see more" in button_text or "show more" in button_text:
                            logger.info(
                                "Found 'See more' button, clicking to expand description"
                            )
                            # Scroll the button into view
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                see_more_button,
                            )
                            self._random_sleep(1.0, 1.5)

                            # Click the button
                            try:
                                see_more_button.click()
                                logger.info("Successfully clicked 'See more' button")
                                self._random_sleep(2.0, 3.0)  # Wait for expansion
                                return True
                            except Exception as e:
                                # If direct click fails, try JavaScript click
                                logger.debug(
                                    f"Direct click failed, trying JavaScript click: {e}"
                                )
                                self.driver.execute_script(
                                    "arguments[0].click();", see_more_button
                                )
                                logger.info(
                                    "Successfully clicked 'See more' button using JavaScript"
                                )
                                self._random_sleep(2.0, 3.0)  # Wait for expansion
                                return True
            except (NoSuchElementException, Exception) as e:
                logger.debug(
                    f"Could not click 'See more' button with selector {selector}: {e}"
                )
                continue

        logger.debug("No 'See more' button found or could not click it")
        return False

    def _navigate_to_next_page(self) -> bool:
        """
        Centralized method to navigate to the next page of search results.
        Uses the updated LinkedIn pagination selectors and handles various edge cases.

        Returns:
            True if successfully navigated to next page, False otherwise
        """
        try:
            # Get pagination information before trying to navigate
            pagination_info = self._get_pagination_info()
            logger.info(f"Current pagination status: {pagination_info['page_state']}")

            if not pagination_info["has_next"]:
                logger.info("No next page available - reached end of results")
                return False

            # Updated LinkedIn pagination selectors
            next_button_selectors = [
                "button.jobs-search-pagination__button--next",
                ".jobs-search-pagination__button--next",
                "button[aria-label='View next page']",
                "button.artdeco-button.jobs-search-pagination__button--next",
                ".jobs-search-pagination button[aria-label*='next']",
                "button[aria-label='Next']",  # fallback to old selector
                ".artdeco-pagination__button--next",  # fallback to old selector
                "button.artdeco-pagination__button--next",
                "[data-test-pagination-page-btn='next']",
            ]

            next_clicked = False
            for selector in next_button_selectors:
                try:
                    next_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for next_button in next_buttons:
                        if (
                            next_button
                            and next_button.is_displayed()
                            and next_button.is_enabled()
                            and "disabled" not in next_button.get_attribute("class")
                        ):
                            # Scroll to make the button visible
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});",
                                next_button,
                            )
                            self._random_sleep(1.0, 2.0)

                            # Click the button
                            next_button.click()
                            logger.info("Successfully clicked next page button")
                            next_clicked = True
                            self._random_sleep(3.0, 5.0)

                            # Verify we're on the next page
                            new_pagination_info = self._get_pagination_info()
                            logger.info(
                                f"After navigation: {new_pagination_info['page_state']}"
                            )

                            return True
                except Exception as e:
                    logger.debug(
                        f"Could not click next button with selector {selector}: {e}"
                    )
                    continue

            if not next_clicked:
                logger.info("No more pages available or could not find next button")

            return False

        except Exception as e:
            logger.error(f"Error navigating to next page: {str(e)}")
            # Take a screenshot for debugging
            # self._save_screenshot("next_page_error")
            return False

    def _get_total_job_count(self) -> int:
        """
        Extract the total number of jobs from the search results page.

        Returns:
            int: Total expected job count, or 0 if not found
        """
        try:
            total_jobs_element = self.driver.find_element(
                By.CSS_SELECTOR,
                ".jobs-search-results-list__title-heading .t-12, .jobs-search-results-list__subtitle",
            )
            if total_jobs_element:
                results_text = total_jobs_element.text.strip()
                if "results" in results_text:
                    total_expected = int(
                        "".join(filter(str.isdigit, results_text.split("results")[0]))
                    )
                    logger.info(
                        f"Found {total_expected} total jobs according to LinkedIn"
                    )
                    return total_expected
        except Exception as e:
            logger.warning(f"Could not determine total job count: {e}")
        return 0

    def _find_job_list_container(self):
        """
        Find the job list container element on the page.

        Returns:
            WebElement: The job list container, or body element as fallback
        """
        job_list_selectors = [
            "ul.scaffold-layout__list-container",  # Standard LinkedIn class for job list UL
            "ul.jobs-search-results__list",  # Alternative class name
            ".scaffold-layout__list",  # The left panel container
            ".jobs-search-results-list",
            ".jobs-search-results__list-container",
            "ul li[data-occludable-job-id]",  # New structure - find parent UL of job cards
            "ul:has(li[data-occludable-job-id])",  # CSS4 selector for UL containing job cards
        ]

        for selector in job_list_selectors:
            try:
                job_list_container = self.driver.find_element(By.CSS_SELECTOR, selector)
                if job_list_container:
                    logger.info(f"Found job list container with selector: {selector}")
                    return job_list_container
            except:
                continue

        # If no specific container found, try to find the UL that contains job cards
        try:
            # Find all ULs and check if they contain job cards
            uls = self.driver.find_elements(By.TAG_NAME, "ul")
            for ul in uls:
                job_cards_in_ul = ul.find_elements(
                    By.CSS_SELECTOR, "li[data-occludable-job-id]"
                )
                if len(job_cards_in_ul) > 0:
                    logger.info(
                        f"Found job list container (UL with {len(job_cards_in_ul)} job cards)"
                    )
                    return ul
        except Exception as e:
            logger.warning(f"Error finding UL with job cards: {e}")

        logger.warning("Could not find job list container, using body instead")
        return self.driver.find_element(By.TAG_NAME, "body")

    def _scroll_job_list_container(
        self, job_list_container, total_expected: int
    ) -> None:
        """
        Scroll through the job list container to load all job cards.

        Args:
            job_list_container: The container element to scroll
            total_expected: Expected total number of jobs
        """
        scroll_attempts = 0
        max_scroll_attempts = 20  # Increase this to ensure we load all jobs
        last_job_count = 0
        stagnant_count = 0

        while scroll_attempts < max_scroll_attempts:
            logger.info(
                f"Scrolling job list container (attempt {scroll_attempts + 1}/{max_scroll_attempts})"
            )
            # Find all currently loaded job cards (both loaded and placeholder li elements)
            job_card_selector = "li[data-occludable-job-id], li.jobs-search-results__list-item, li.scaffold-layout__list-item"
            job_cards = job_list_container.find_elements(
                By.CSS_SELECTOR, job_card_selector
            )
            loaded_count = len(job_cards)

            logger.info(
                f"Currently have {loaded_count} job card elements (loaded + placeholders)"
            )

            # If no cards found yet, try direct page scroll
            if loaded_count == 0:
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight / 2);"
                )
                self._random_sleep(1.0, 2.0)
                job_cards = job_list_container.find_elements(
                    By.CSS_SELECTOR, job_card_selector
                )
                loaded_count = len(job_cards)
                logger.info(
                    f"After page scroll, found {loaded_count} job card elements"
                )

            # If we've found cards, scroll to the last one to load more
            if loaded_count > 0:
                # Scroll to the last job card to trigger loading more
                last_card = job_cards[-1]
                try:
                    # First try scrolling the job card into view (this will scroll the left panel)
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'end', behavior: 'smooth'});",
                        last_card,
                    )
                    logger.info(f"Scrolled to job card {loaded_count}")
                except Exception as e:
                    logger.warning(f"Error scrolling to last job card: {e}")
                    # Try a different scroll approach - scroll the list container itself
                    try:
                        # Scroll the list container directly
                        scroll_script = """
                            arguments[0].scrollTop = arguments[0].scrollHeight;
                        """
                        self.driver.execute_script(scroll_script, job_list_container)
                        logger.info("Scrolled job list container directly")
                    except Exception as container_scroll_error:
                        logger.warning(
                            f"Error scrolling container: {container_scroll_error}"
                        )
                        # Last resort: scroll the page
                        self.driver.execute_script(
                            "window.scrollTo(0, document.body.scrollHeight);"
                        )

            # Wait for new content to load
            self._random_sleep(2.0, 3.0)
            # Count job cards again
            job_cards = job_list_container.find_elements(
                By.CSS_SELECTOR, job_card_selector
            )
            new_count = len(job_cards)
            logger.info(f"After scrolling, now have {new_count} job card elements")

            # If we're at the expected total or haven't loaded more in several attempts, stop scrolling
            if (total_expected > 0 and new_count >= total_expected) or new_count >= 100:
                logger.info(f"Found all expected jobs: {new_count}/{total_expected}")
                break

            if new_count == last_job_count:
                stagnant_count += 1
                if stagnant_count >= 3:
                    logger.info(
                        f"Job count hasn't increased for 3 attempts, stopping at {new_count} jobs"
                    )
                    break
            else:
                stagnant_count = 0  # Reset if we found more jobs

            last_job_count = new_count
            scroll_attempts += 1

    def _get_job_cards(self, job_list_container):
        """
        Get all job cards from the page using various selectors.

        Args:
            job_list_container: The container element to search in

        Returns:
            List of WebElements representing job cards
        """
        job_cards_selectors = [
            "li[data-occludable-job-id]",  # New primary selector
            "li.jobs-search-results__list-item",
            "li.scaffold-layout__list-item",
            ".job-card-container",
            "[data-job-id]",
        ]
        job_cards = []

        # Try each selector to find job cards
        for selector in job_cards_selectors:
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(cards) > len(job_cards):
                    job_cards = cards
                    logger.info(
                        f"Found {len(job_cards)} job cards with selector: {selector}"
                    )
            except Exception as e:
                logger.debug(f"Failed to find job cards with selector {selector}: {e}")
                continue

        return job_cards

    def _extract_job_links_from_cards(self, job_cards, current_page: int) -> set:
        """
        Extract job links from a list of job card elements.

        Args:
            job_cards: List of job card WebElements
            current_page: Current page number for logging

        Returns:
            Set of job URLs
        """
        job_links = set()
        logger.info(f"Processing {len(job_cards)} job cards on page {current_page}")

        # Extract job links from all cards
        processed = 0
        for card in job_cards:
            processed += 1
            if processed % 5 == 0:
                logger.info(f"Processed {processed}/{len(job_cards)} job cards")

            try:
                # *** KEY STEP: Make sure the card is in view to load its details ***
                try:
                    # Scroll to the card to ensure its content is loaded
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
                        card,
                    )
                    # Give it a moment to load the content
                    self._random_sleep(0.5, 1.0)
                except Exception as e:
                    logger.debug(f"Error scrolling to job card {processed}: {e}")

                # Check if this card has data-occludable-job-id attribute
                job_id = None
                try:
                    job_id = card.get_attribute("data-occludable-job-id")
                    if job_id:
                        logger.debug(f"Found card with job ID: {job_id}")
                    else:
                        logger.debug(
                            f"Card {processed} has no data-occludable-job-id attribute"
                        )
                except Exception as e:
                    logger.debug(f"Error getting job ID from card {processed}: {e}")

                # Check if card has data-job-id attribute (alternative format)
                if not job_id:
                    try:
                        job_container = card.find_element(
                            By.CSS_SELECTOR, "[data-job-id]"
                        )
                        job_id = job_container.get_attribute("data-job-id")
                        if job_id:
                            logger.debug(f"Found card with job-id: {job_id}")
                    except:
                        pass

                # Try to find the job link inside this card
                link_elements = []
                try:
                    # Look for the title link with various selectors - prioritize new structure
                    link_elements = card.find_elements(
                        By.CSS_SELECTOR,
                        "a.job-card-container__link, a[href*='/jobs/view/'], a[data-control-id], a.job-card-list__title-link, a.job-card-list__title--link",
                    )

                    # If we can't find with specific selectors, get all links
                    if not link_elements:
                        link_elements = card.find_elements(By.TAG_NAME, "a")
                except Exception as e:
                    logger.debug(f"Error finding links in card {processed}: {e}")

                # Process all found links to get a job URL
                url = None
                logger.debug(
                    f"Card {processed}: Found {len(link_elements)} link elements"
                )
                for i, link_element in enumerate(link_elements):
                    try:
                        href = link_element.get_attribute("href")
                        logger.debug(f"  Link {i}: {href}")
                        if href and "/jobs/view/" in href:
                            url = href.split("?")[0]  # Remove query parameters
                            logger.debug(f"Found job URL: {url}")
                            break
                    except Exception as e:
                        logger.debug(f"  Error processing link {i}: {e}")
                        continue

                # If we found a URL, add it to our collection
                if url:
                    job_links.add(url)
                    logger.debug(f"Added job URL to collection: {url}")
                # If we have a job ID but no URL, construct one
                elif job_id:
                    constructed_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
                    logger.debug(f"Constructed job URL from ID: {constructed_url}")
                    job_links.add(constructed_url)
                else:
                    # Check if this is an empty placeholder card
                    card_html = card.get_attribute("innerHTML") or ""
                    if (
                        len(card_html.strip()) < 50
                    ):  # Very short content suggests placeholder
                        logger.debug(
                            f"Card {processed} appears to be a placeholder (short content)"
                        )
                    else:
                        logger.warning(
                            f"Could not extract job link from card {processed} (has content but no extractable URL)"
                        )
                        # Log some of the card's structure for debugging
                        try:
                            card_class = card.get_attribute("class") or "no-class"
                            logger.debug(f"  Card class: {card_class}")
                            all_links = card.find_elements(By.TAG_NAME, "a")
                            logger.debug(f"  Total links in card: {len(all_links)}")
                            for j, link in enumerate(
                                all_links[:3]
                            ):  # Only show first 3
                                try:
                                    href = link.get_attribute("href") or "no-href"
                                    logger.debug(f"    Link {j}: {href}")
                                except:
                                    pass
                        except Exception as debug_e:
                            logger.debug(
                                f"  Error debugging card {processed}: {debug_e}"
                            )

            except StaleElementReferenceException:
                logger.warning(
                    f"Stale element reference when processing card {processed}/{len(job_cards)}. Skipping."
                )
                continue
            except Exception as e:
                logger.debug(
                    f"Error processing job card {processed}/{len(job_cards)}: {e}"
                )
                continue

        return job_links

    def _go_to_next_page(self) -> bool:
        """
        Navigate to the next page of job results.

        Returns:
            bool: True if successfully navigated to next page, False otherwise
        """
        try:
            next_button_selectors = [
                "button.jobs-search-pagination__button--next",
                ".jobs-search-pagination__button--next",
                "button[aria-label='View next page']",
                "button.artdeco-button.jobs-search-pagination__button--next",
                ".jobs-search-pagination button[aria-label*='next']",
                "button.artdeco-pagination__button--next",  # fallback to old selector
                ".artdeco-pagination__button--next",  # fallback to old selector
            ]

            next_clicked = False
            for selector in next_button_selectors:
                try:
                    next_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for next_button in next_buttons:
                        if (
                            next_button.is_displayed()
                            and next_button.is_enabled()
                            and "disabled" not in next_button.get_attribute("class")
                        ):  # Scroll to make the button visible
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});",
                                next_button,
                            )
                            self._random_sleep(1.0, 2.0)

                            next_button.click()
                            logger.info("Clicked next page button")
                            next_clicked = True
                            self._random_sleep(3.0, 5.0)

                            # Verify we're on the next page
                            new_pagination_info = self._get_pagination_info()
                            logger.info(
                                f"After navigation: {new_pagination_info['page_state']}"
                            )
                            break

                    if next_clicked:
                        break
                except Exception as e:
                    logger.warning(
                        f"Could not click next button with selector {selector}: {str(e)}"
                    )
                    continue

            if not next_clicked:
                logger.info("No more pages available or could not find next button")
                return False

        except Exception as e:
            logger.error(f"Error trying to navigate to next page: {str(e)}")
            return False

        return True

    def _extract_company_info(self) -> str:
        """
        Extract company information excluding footer links and "Show more" buttons.

        Returns:
            Clean company information text
        """
        try:
            company_info_selectors = [
                ".jobs-company__box",
                ".jobs-company__content",
                ".jobs-company-information",
            ]

            for selector in company_info_selectors:
                try:
                    company_elements = self.driver.find_elements(
                        By.CSS_SELECTOR, selector
                    )
                    for element in company_elements:
                        if element.is_displayed():
                            # Get the full text first
                            full_text = element.text.strip()

                            if full_text:
                                # Remove footer content that contains "Show more" links
                                # Look for common patterns that indicate footer content
                                lines = full_text.split("\n")
                                clean_lines = []

                                for line in lines:
                                    line = line.strip()
                                    # Skip lines that are footer links or "Show more" buttons
                                    if (
                                        line.lower() in ["show more", "see more"]
                                        or "Show more" in line
                                        or "See more" in line
                                        or line.startswith("http")
                                        or "/company/" in line
                                    ):
                                        # Stop processing when we hit footer content
                                        break
                                    if line:  # Only add non-empty lines
                                        clean_lines.append(line)

                                # Join the clean lines back together
                                clean_text = "\n".join(clean_lines).strip()

                                if clean_text:
                                    logger.debug(
                                        f"Extracted company info ({len(clean_text)} characters)"
                                    )
                                    return clean_text
                except (NoSuchElementException, Exception) as e:
                    logger.debug(
                        f"Could not extract company info with selector {selector}: {e}"
                    )
                    continue

            logger.debug("Could not extract company information")
            return ""

        except Exception as e:
            logger.error(f"Error extracting company info: {str(e)}")
            return ""

    def _extract_external_apply_url(self, apply_button) -> str:
        """
        Extract the external apply URL from a LinkedIn job apply button.
        Uses the proven simple click method from the debug script.

        Args:
            apply_button: The selenium WebElement of the apply button

        Returns:
            The external apply URL if found, None otherwise
        """
        try:
            # Method 1: Check for direct href first
            href = apply_button.get_attribute("href")
            if href and href.startswith("http") and "linkedin.com" not in href:
                logger.debug(f"Found direct href: {href}")
                return href

            # Method 2: Simple click test with detailed logging (like debug script)
            logger.debug("Attempting click-based extraction...")
            current_url = self.driver.current_url
            current_windows = set(self.driver.window_handles)

            try:
                logger.debug(f"Current URL before click: {current_url}")
                logger.debug(f"Current windows before click: {len(current_windows)}")

                # Try clicking the button
                apply_button.click()
                time.sleep(3)  # Give time for redirect

                new_url = self.driver.current_url
                new_windows = set(self.driver.window_handles)

                logger.debug(f"URL after click: {new_url}")
                logger.debug(f"Windows after click: {len(new_windows)}")

                # Check for new windows
                if len(new_windows) > len(current_windows):
                    logger.debug("New window/tab detected!")
                    new_window = list(new_windows - current_windows)[0]
                    self.driver.switch_to.window(new_window)
                    tab_url = self.driver.current_url
                    logger.debug(f"New tab URL: {tab_url}")

                    if not tab_url.startswith(
                        "https://www.linkedin.com"
                    ) and tab_url.startswith("http"):
                        logger.debug(f"✅ SUCCESS (new tab): {tab_url}")
                        self.driver.close()
                        self.driver.switch_to.window(list(current_windows)[0])
                        return tab_url
                    else:
                        logger.debug("New tab but still LinkedIn or invalid URL")
                        self.driver.close()
                        self.driver.switch_to.window(list(current_windows)[0])

                # Check for same-window redirect
                elif new_url != current_url:
                    logger.debug(f"Same-window redirect detected: {new_url}")
                    if not new_url.startswith(
                        "https://www.linkedin.com"
                    ) and new_url.startswith("http"):
                        logger.debug(f"✅ SUCCESS (redirect): {new_url}")
                        # Navigate back
                        self.driver.get(current_url)
                        time.sleep(2)
                        return new_url
                    else:
                        logger.debug("Redirected but still on LinkedIn")
                        self.driver.get(current_url)
                        time.sleep(2)
                else:
                    logger.debug("No redirect detected")

            except Exception as click_error:
                logger.debug(f"Click extraction failed: {click_error}")
                # Make sure we're back on the original page
                try:
                    if self.driver.current_url != current_url:
                        self.driver.get(current_url)
                        time.sleep(2)
                except:
                    pass

            # Method 3: Extract from page source as fallback
            try:
                page_source = self.driver.page_source
                import re

                patterns = [
                    rf'"applyUrl":"([^"]*)"',
                    rf'"externalApplyUrl":"([^"]*)"',
                    rf'"companyApplyUrl":"([^"]*)"',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    for match in matches:
                        if (
                            match
                            and match.startswith("http")
                            and "linkedin.com" not in match
                        ):
                            clean_url = match.replace("\\u0026", "&").replace(
                                "\\/", "/"
                            )
                            logger.debug(
                                f"Found external URL from page source: {clean_url}"
                            )
                            return clean_url

            except Exception as page_extract_error:
                logger.debug(f"Page source extraction failed: {page_extract_error}")

            logger.debug("No external apply URL found using any method")
            return None

        except Exception as e:
            logger.debug(f"Error extracting external apply URL: {e}")
            return None

    def _extract_hiring_team(self) -> List[Dict[str, str]]:
        """
        Extract hiring team/contact person details from the job page.

        Returns:
            List of hiring team members with their details
        """
        try:
            hiring_team = []

            # Look for the hiring team section
            hiring_section_selectors = [
                ".job-details-people-who-can-help__section",
                ".jobs-poster",
                ".jobs-poster__details",
                ".hirer-card",
            ]

            for selector in hiring_section_selectors:
                try:
                    hiring_sections = self.driver.find_elements(
                        By.CSS_SELECTOR, selector
                    )

                    for section in hiring_sections:
                        if not section.is_displayed():
                            continue

                        # Look for individual hiring team members
                        member_selectors = [
                            ".hirer-card__hirer-information",
                            ".jobs-poster__name",
                            ".display-flex.align-items-center",
                        ]

                        for member_selector in member_selectors:
                            try:
                                members = section.find_elements(
                                    By.CSS_SELECTOR, member_selector
                                )

                                for member in members:
                                    if not member.is_displayed():
                                        continue

                                    member_info = {}

                                    # Extract name
                                    name_selectors = [
                                        ".jobs-poster__name",
                                        ".t-black.jobs-poster__name",
                                        "strong",
                                        ".text-body-medium-bold strong",
                                    ]

                                    for name_sel in name_selectors:
                                        try:
                                            name_elem = member.find_element(
                                                By.CSS_SELECTOR, name_sel
                                            )
                                            if name_elem and name_elem.text.strip():
                                                member_info["name"] = (
                                                    name_elem.text.strip()
                                                )
                                                break
                                        except NoSuchElementException:
                                            continue

                                    # Extract title/role
                                    title_selectors = [
                                        ".text-body-small.t-black",
                                        ".hirer-card__job-poster",
                                        ".jobs-poster__title",
                                    ]

                                    for title_sel in title_selectors:
                                        try:
                                            title_elem = member.find_element(
                                                By.CSS_SELECTOR, title_sel
                                            )
                                            if title_elem and title_elem.text.strip():
                                                member_info["title"] = (
                                                    title_elem.text.strip()
                                                )
                                                break
                                        except NoSuchElementException:
                                            continue

                                    # Extract LinkedIn profile URL
                                    try:
                                        profile_link = member.find_element(
                                            By.CSS_SELECTOR, "a[href*='/in/']"
                                        )
                                        if profile_link:
                                            member_info["linkedin_url"] = (
                                                profile_link.get_attribute("href")
                                            )
                                    except NoSuchElementException:
                                        pass

                                    # Extract connection degree
                                    try:
                                        connection_elem = member.find_element(
                                            By.CSS_SELECTOR,
                                            ".hirer-card__connection-degree",
                                        )
                                        if (
                                            connection_elem
                                            and connection_elem.text.strip()
                                        ):
                                            member_info["connection_degree"] = (
                                                connection_elem.text.strip()
                                            )
                                    except NoSuchElementException:
                                        pass

                                    # Only add if we have at least a name
                                    if member_info.get("name"):
                                        hiring_team.append(member_info)

                            except Exception as member_error:
                                logger.debug(
                                    f"Error extracting hiring team member: {member_error}"
                                )
                                continue

                except Exception as section_error:
                    logger.debug(
                        f"Error processing hiring section {selector}: {section_error}"
                    )
                    continue

            # Remove duplicates based on name
            seen_names = set()
            unique_hiring_team = []
            for member in hiring_team:
                name = member.get("name", "")
                if name and name not in seen_names:
                    seen_names.add(name)
                    unique_hiring_team.append(member)

            logger.debug(f"Extracted {len(unique_hiring_team)} hiring team members")
            return unique_hiring_team

        except Exception as e:
            logger.debug(f"Error extracting hiring team: {e}")
            return []

    def _extract_related_jobs(self) -> List[Dict[str, str]]:
        """
        Extract related/similar jobs from the job page.

        Returns:
            List of related jobs with their details
        """
        try:
            related_jobs = []

            # Look for the related jobs section
            related_jobs_selectors = [
                "ul.card-list.card-list--tile.js-similar-jobs-list",
                ".js-similar-jobs-list",
                ".similar-jobs",
                ".jobs-similar-jobs",
            ]

            for selector in related_jobs_selectors:
                try:
                    related_sections = self.driver.find_elements(
                        By.CSS_SELECTOR, selector
                    )

                    for section in related_sections:
                        if not section.is_displayed():
                            continue

                        # Look for individual job cards
                        job_card_selectors = [
                            "li.list-style-none",
                            ".job-card-job-posting-card-wrapper",
                            ".job-card",
                        ]

                        for card_selector in job_card_selectors:
                            try:
                                job_cards = section.find_elements(
                                    By.CSS_SELECTOR, card_selector
                                )

                                for card in job_cards:
                                    if not card.is_displayed():
                                        continue

                                    job_info = {}

                                    # Extract job title
                                    title_selectors = [
                                        ".artdeco-entity-lockup__title strong",
                                        ".job-card-job-posting-card-wrapper__title strong",
                                        ".job-card__title",
                                    ]

                                    for title_sel in title_selectors:
                                        try:
                                            title_elem = card.find_element(
                                                By.CSS_SELECTOR, title_sel
                                            )
                                            if title_elem and title_elem.text.strip():
                                                job_info["title"] = (
                                                    title_elem.text.strip()
                                                )
                                                break
                                        except NoSuchElementException:
                                            continue

                                    # Extract company name
                                    company_selectors = [
                                        ".artdeco-entity-lockup__subtitle",
                                        ".job-card__company-name",
                                        ".job-card-job-posting-card-wrapper__company",
                                    ]

                                    for company_sel in company_selectors:
                                        try:
                                            company_elem = card.find_element(
                                                By.CSS_SELECTOR, company_sel
                                            )
                                            if (
                                                company_elem
                                                and company_elem.text.strip()
                                            ):
                                                job_info["company"] = (
                                                    company_elem.text.strip()
                                                )
                                                break
                                        except NoSuchElementException:
                                            continue

                                    # Extract location
                                    location_selectors = [
                                        ".artdeco-entity-lockup__caption",
                                        ".job-card__location",
                                        ".job-card-job-posting-card-wrapper__location",
                                    ]

                                    for location_sel in location_selectors:
                                        try:
                                            location_elem = card.find_element(
                                                By.CSS_SELECTOR, location_sel
                                            )
                                            if (
                                                location_elem
                                                and location_elem.text.strip()
                                            ):
                                                job_info["location"] = (
                                                    location_elem.text.strip()
                                                )
                                                break
                                        except NoSuchElementException:
                                            continue

                                    # Extract job URL
                                    try:
                                        link_elem = card.find_element(
                                            By.CSS_SELECTOR, "a[href*='/jobs/']"
                                        )
                                        if link_elem:
                                            href = link_elem.get_attribute("href")
                                            # Extract job ID from the URL
                                            import re

                                            job_id_match = re.search(
                                                r"/jobs/.*?(\d+)", href
                                            )
                                            if job_id_match:
                                                job_id = job_id_match.group(1)
                                                job_info["url"] = (
                                                    f"https://www.linkedin.com/jobs/view/{job_id}"
                                                )
                                            else:
                                                job_info["url"] = href
                                    except NoSuchElementException:
                                        pass

                                    # Extract posting date
                                    date_selectors = [
                                        "time",
                                        ".job-card__date",
                                        ".job-card-job-posting-card-wrapper__footer-item time",
                                    ]

                                    for date_sel in date_selectors:
                                        try:
                                            date_elem = card.find_element(
                                                By.CSS_SELECTOR, date_sel
                                            )
                                            if date_elem and date_elem.text.strip():
                                                job_info["posted_date"] = (
                                                    date_elem.text.strip()
                                                )
                                                break
                                        except NoSuchElementException:
                                            continue

                                    # Extract job insights (like "Easy Apply", alumni info, etc.)
                                    insights = []
                                    insight_selectors = [
                                        ".job-card-job-posting-card-wrapper__job-insight-text",
                                        ".job-card__insight",
                                        ".job-card-job-posting-card-wrapper__footer-item",
                                    ]

                                    for insight_sel in insight_selectors:
                                        try:
                                            insight_elems = card.find_elements(
                                                By.CSS_SELECTOR, insight_sel
                                            )
                                            for elem in insight_elems:
                                                if (
                                                    elem.is_displayed()
                                                    and elem.text.strip()
                                                ):
                                                    insights.append(elem.text.strip())
                                        except NoSuchElementException:
                                            continue

                                    if insights:
                                        job_info["insights"] = insights

                                    # Only add if we have at least a title
                                    if job_info.get("title"):
                                        related_jobs.append(job_info)

                            except Exception as card_error:
                                logger.debug(
                                    f"Error extracting related job card: {card_error}"
                                )
                                continue

                except Exception as section_error:
                    logger.debug(
                        f"Error processing related jobs section {selector}: {section_error}"
                    )
                    continue

            # Remove duplicates based on title and company
            seen_jobs = set()
            unique_related_jobs = []
            for job in related_jobs:
                job_key = f"{job.get('title', '')}-{job.get('company', '')}"
                if job_key and job_key not in seen_jobs:
                    seen_jobs.add(job_key)
                    unique_related_jobs.append(job)

            logger.debug(f"Extracted {len(unique_related_jobs)} related jobs")
            return unique_related_jobs

        except Exception as e:
            logger.debug(f"Error extracting related jobs: {e}")
            return []

    def _apply_experience_level_filter(self, experience_levels: List[str]) -> bool:
        """
        Apply experience level filter by clicking on the dropdown and selecting options.

        Args:
            experience_levels: List of experience levels to filter by.
                              Valid values: ['internship', 'entry_level', 'associate', 'mid_senior', 'director', 'executive']

        Returns:
            bool: True if filter was applied successfully, False otherwise
        """
        if not experience_levels:
            return True

        # Map experience level names to their values
        level_mapping = {
            "internship": "1",
            "entry_level": "2",
            "associate": "3",
            "mid_senior": "4",
            "director": "5",
            "executive": "6",
        }

        try:
            logger.info(f"Applying experience level filter: {experience_levels}")

            # Find and click the experience level filter button with multiple selectors
            experience_button_selectors = [
                'button[id="searchFilter_experience"]',
                'button[aria-label*="Experience level filter"]',
                '.search-reusables__filter-trigger-and-dropdown[data-basic-filter-parameter-name="experience"] button',
                'button.reusable-search-filter-trigger-and-dropdown__trigger[id*="experience"]',
            ]

            experience_button = None
            for selector in experience_button_selectors:
                try:
                    experience_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.debug(f"Found experience button with selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if not experience_button:
                logger.warning("Could not find experience level filter button")
                return False

            # Click to open the dropdown
            experience_button.click()
            self._random_sleep(1.0, 2.0)
            # Wait for the dropdown to appear and be fully loaded
            dropdown_container = None
            dropdown_selectors = [
                ".artdeco-hoverable-content--visible .reusable-search-filters-trigger-dropdown__container",
                "fieldset.reusable-search-filters-trigger-dropdown__container",
                ".artdeco-hoverable-content--visible fieldset",
            ]

            for selector in dropdown_selectors:
                try:
                    dropdown_container = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    # Additional wait for the content to be fully rendered
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, f"{selector} input[type='checkbox']")
                        )
                    )
                    logger.debug(f"Dropdown container found with selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if not dropdown_container:
                logger.warning("Experience level dropdown container did not appear")
                return False

            # Wait a bit more for any animations to complete
            self._random_sleep(1.0, 1.5)

            # Select the specified experience levels
            selections_made = 0
            for level in experience_levels:
                if level.lower() in level_mapping:
                    value = level_mapping[level.lower()]
                    checkbox_id = f"experience-{value}"

                    try:
                        # Try multiple approaches to find and click the checkbox
                        checkbox_found = False

                        # Method 1: Find by ID within the dropdown container
                        try:
                            checkbox = dropdown_container.find_element(
                                By.ID, checkbox_id
                            )
                            if checkbox.is_displayed() and not checkbox.is_selected():
                                # Try clicking the label first
                                try:
                                    label = dropdown_container.find_element(
                                        By.CSS_SELECTOR, f'label[for="{checkbox_id}"]'
                                    )
                                    self.driver.execute_script(
                                        "arguments[0].click();", label
                                    )
                                    checkbox_found = True
                                except:
                                    # Fallback to checkbox click
                                    self.driver.execute_script(
                                        "arguments[0].click();", checkbox
                                    )
                                    checkbox_found = True
                        except NoSuchElementException:
                            pass

                        # Method 2: Find by value attribute if ID approach failed
                        if not checkbox_found:
                            try:
                                xpath = f"//input[@name='experience-level-filter-value'][@value='{value}']"
                                checkbox = dropdown_container.find_element(
                                    By.XPATH, xpath
                                )
                                if (
                                    checkbox.is_displayed()
                                    and not checkbox.is_selected()
                                ):
                                    self.driver.execute_script(
                                        "arguments[0].click();", checkbox
                                    )
                                    checkbox_found = True
                            except NoSuchElementException:
                                pass

                        # Method 3: Find by visible text content
                        if not checkbox_found:
                            try:
                                # Map level names to display text
                                display_text_map = {
                                    "internship": "Internship",
                                    "entry_level": "Entry level",
                                    "associate": "Associate",
                                    "mid_senior": "Mid-Senior level",
                                    "director": "Director",
                                    "executive": "Executive",
                                }
                                display_text = display_text_map.get(level.lower())
                                if display_text:
                                    xpath = f"//span[text()='{display_text}']/ancestor::label"
                                    label = dropdown_container.find_element(
                                        By.XPATH, xpath
                                    )
                                    if label.is_displayed():
                                        self.driver.execute_script(
                                            "arguments[0].click();", label
                                        )
                                        checkbox_found = True
                            except NoSuchElementException:
                                pass

                        if checkbox_found:
                            selections_made += 1
                            logger.info(f"Selected experience level: {level}")
                            self._random_sleep(0.3, 0.7)
                        else:
                            logger.warning(
                                f"Could not find or select checkbox for experience level: {level}"
                            )

                    except Exception as e:
                        logger.warning(f"Error selecting experience level {level}: {e}")
                        continue
                else:
                    logger.warning(f"Invalid experience level: {level}")

            if selections_made == 0:
                logger.warning("No experience level selections were made")
                # Try to close the dropdown
                try:
                    cancel_selectors = [
                        'button[aria-label*="Cancel Experience level filter"]',
                        'button[aria-label*="Cancel"]',
                        ".reusable-search-filters-buttons button.artdeco-button--tertiary",
                    ]
                    for selector in cancel_selectors:
                        try:
                            cancel_button = dropdown_container.find_element(
                                By.CSS_SELECTOR, selector
                            )
                            if cancel_button.is_displayed():
                                cancel_button.click()
                                break
                        except:
                            continue
                except:
                    pass
                return False

            # Click "Show results" button with improved detection
            apply_button_selectors = [
                'button.artdeco-button--primary[aria-label*="Apply current filter"]',
                'button.artdeco-button--primary[aria-label*="Show"]',
                ".reusable-search-filters-buttons button.artdeco-button--primary",
                'button[class*="artdeco-button--primary"][aria-label*="Show"]',
            ]

            apply_button = None
            for selector in apply_button_selectors:
                try:
                    apply_button = dropdown_container.find_element(
                        By.CSS_SELECTOR, selector
                    )
                    if apply_button.is_displayed() and apply_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue

            if apply_button:
                # Use JavaScript click for reliability
                self.driver.execute_script("arguments[0].click();", apply_button)
                self._random_sleep(2.0, 4.0)  # Wait longer for page reload
                logger.info(
                    f"Applied experience level filter with {selections_made} selections"
                )
                return True
            else:
                logger.warning(
                    "Could not find apply button for experience level filter"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to apply experience level filter: {e}")
            return False

    def _apply_date_posted_filter(self, date_posted: str) -> bool:
        """
        Apply date posted filter by clicking on the dropdown and selecting an option.

        Args:
            date_posted: Date posted filter option.
                        Valid values: ['any_time', 'past_month', 'past_week', 'past_24_hours']

        Returns:
            bool: True if filter was applied successfully, False otherwise
        """
        if not date_posted or date_posted == "any_time":
            return True

        # Map date posted options to their values
        date_mapping = {
            "any_time": "",
            "past_month": "r2592000",
            "past_week": "r604800",
            "past_24_hours": "r86400",
        }

        try:
            logger.info(f"Applying date posted filter: {date_posted}")

            # Find and click the date posted filter button with multiple selectors
            date_button_selectors = [
                'button[id="searchFilter_timePostedRange"]',
                'button[aria-label*="Date posted filter"]',
                '.search-reusables__filter-trigger-and-dropdown[data-basic-filter-parameter-name="timePostedRange"] button',
            ]

            date_button = None
            for selector in date_button_selectors:
                try:
                    date_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.debug(f"Found date button with selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if not date_button:
                logger.warning("Could not find date posted filter button")
                return False

            # Click to open the dropdown
            date_button.click()
            self._random_sleep(1.0, 2.0)
            # Wait for the dropdown to appear and be fully loaded
            dropdown_container = None
            dropdown_selectors = [
                ".artdeco-hoverable-content--visible .reusable-search-filters-trigger-dropdown__container",
                "fieldset.reusable-search-filters-trigger-dropdown__container",
                ".artdeco-hoverable-content--visible fieldset",
            ]

            for selector in dropdown_selectors:
                try:
                    dropdown_container = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    # Additional wait for radio buttons to be rendered
                    WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, f"{selector} input[type='radio']")
                        )
                    )
                    logger.debug(f"Dropdown container found with selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if not dropdown_container:
                logger.warning("Date posted dropdown container did not appear")
                return False

            # Wait a bit more for any animations to complete
            self._random_sleep(1.0, 1.5)

            # Select the specified date option
            if date_posted.lower() in date_mapping:
                value = date_mapping[date_posted.lower()]
                radio_id = f"timePostedRange-{value}"

                try:
                    radio_found = False

                    # Method 1: Find by ID within the dropdown container
                    try:
                        radio_button = dropdown_container.find_element(By.ID, radio_id)
                        if (
                            radio_button.is_displayed()
                            and not radio_button.is_selected()
                        ):
                            # Try clicking the label first
                            try:
                                label = dropdown_container.find_element(
                                    By.CSS_SELECTOR, f'label[for="{radio_id}"]'
                                )
                                self.driver.execute_script(
                                    "arguments[0].click();", label
                                )
                                radio_found = True
                            except:
                                # Fallback to radio button click
                                self.driver.execute_script(
                                    "arguments[0].click();", radio_button
                                )
                                radio_found = True
                    except NoSuchElementException:
                        pass

                    # Method 2: Find by value attribute if ID approach failed
                    if not radio_found:
                        try:
                            xpath = f"//input[@name='date-posted-filter-value'][@value='{value}']"
                            radio_button = dropdown_container.find_element(
                                By.XPATH, xpath
                            )
                            if (
                                radio_button.is_displayed()
                                and not radio_button.is_selected()
                            ):
                                self.driver.execute_script(
                                    "arguments[0].click();", radio_button
                                )
                                radio_found = True
                        except NoSuchElementException:
                            pass

                    # Method 3: Find by visible text content
                    if not radio_found:
                        try:
                            # Map date options to display text
                            display_text_map = {
                                "any_time": "Any time",
                                "past_month": "Past month",
                                "past_week": "Past week",
                                "past_24_hours": "Past 24 hours",
                            }
                            display_text = display_text_map.get(date_posted.lower())
                            if display_text:
                                xpath = (
                                    f"//span[text()='{display_text}']/ancestor::label"
                                )
                                label = dropdown_container.find_element(By.XPATH, xpath)
                                if label.is_displayed():
                                    self.driver.execute_script(
                                        "arguments[0].click();", label
                                    )
                                    radio_found = True
                        except NoSuchElementException:
                            pass

                    if radio_found:
                        logger.info(f"Selected date posted option: {date_posted}")
                        self._random_sleep(0.5, 1.0)
                    else:
                        logger.warning(
                            f"Could not find or select radio button for date: {date_posted}"
                        )
                        return False

                except Exception as e:
                    logger.warning(f"Error selecting date posted option: {e}")
                    return False
            else:
                logger.warning(f"Invalid date posted option: {date_posted}")
                return False

            # Click "Show results" button with improved detection
            apply_button_selectors = [
                'button.artdeco-button--primary[aria-label*="Apply current filter"]',
                'button.artdeco-button--primary[aria-label*="Show"]',
                ".reusable-search-filters-buttons button.artdeco-button--primary",
                'button[class*="artdeco-button--primary"][aria-label*="Show"]',
            ]

            apply_button = None
            for selector in apply_button_selectors:
                try:
                    apply_button = dropdown_container.find_element(
                        By.CSS_SELECTOR, selector
                    )
                    if apply_button.is_displayed() and apply_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue

            if apply_button:
                # Use JavaScript click for reliability
                self.driver.execute_script("arguments[0].click();", apply_button)
                self._random_sleep(2.0, 4.0)  # Wait longer for page reload
                logger.info("Date posted filter applied successfully")
                return True
            else:
                logger.warning("Could not find apply button for date posted filter")
                return False

        except Exception as e:
            logger.error(f"Failed to apply date posted filter: {e}")
            return False

    def _apply_search_filters(
        self,
        experience_levels: Optional[List[str]] = None,
        date_posted: Optional[str] = None,
    ) -> bool:
        """
        Apply multiple search filters in sequence.

        Args:
            experience_levels: List of experience levels to filter by
            date_posted: Date posted filter option

        Returns:
            bool: True if all filters were applied successfully, False otherwise
        """
        success = True

        # Apply experience level filter
        if experience_levels:
            if not self._apply_experience_level_filter(experience_levels):
                success = False

        # Apply date posted filter
        if date_posted:
            if not self._apply_date_posted_filter(date_posted):
                success = False

        return success

    def _debug_page_structure(self) -> None:
        """Debug method to analyze the current page structure"""
        try:
            # Check for various UL elements
            uls = self.driver.find_elements(By.TAG_NAME, "ul")
            logger.info(f"Found {len(uls)} UL elements on page")

            for i, ul in enumerate(uls[:5]):  # Only check first 5 ULs
                try:
                    ul_class = ul.get_attribute("class") or "no-class"
                    job_cards = ul.find_elements(
                        By.CSS_SELECTOR, "li[data-occludable-job-id]"
                    )
                    if len(job_cards) > 0:
                        logger.info(
                            f"UL {i}: class='{ul_class}' has {len(job_cards)} job cards"
                        )
                        # Sample the first job card
                        if job_cards:
                            first_card = job_cards[0]
                            job_id = first_card.get_attribute("data-occludable-job-id")
                            logger.info(f"  First job card ID: {job_id}")

                            # Look for job title link
                            links = first_card.find_elements(
                                By.CSS_SELECTOR, "a[href*='/jobs/view/']"
                            )
                            if links:
                                href = links[0].get_attribute("href")
                                logger.info(f"  First job link: {href}")
                    else:
                        logger.debug(f"UL {i}: class='{ul_class}' has no job cards")
                except Exception as e:
                    logger.debug(f"Error analyzing UL {i}: {e}")

            # Check for job cards anywhere on page
            all_job_cards = self.driver.find_elements(
                By.CSS_SELECTOR, "li[data-occludable-job-id]"
            )
            logger.info(f"Total job cards found on page: {len(all_job_cards)}")

        except Exception as e:
            logger.warning(f"Error in debug analysis: {e}")
