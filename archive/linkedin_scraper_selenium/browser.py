"""
Browser setup, navigation, retries, and scrolling functionality.
"""

import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from .config import (
    CHROME_USER_AGENT, 
    FIREFOX_USER_AGENT, 
    SUPPORTED_BROWSERS,
    MAX_RETRIES,
    MAX_SCROLL_ATTEMPTS,
    NAVIGATION_MIN_SLEEP,
    NAVIGATION_MAX_SLEEP
)
from .utils import random_sleep

logger = logging.getLogger("linkedin_scraper")


class BrowserManager:
    """Manages browser setup, navigation, and scrolling operations."""
    
    def __init__(self, browser: str = "chrome", headless: bool = False, timeout: int = 20):
        """
        Initialize browser manager.
        
        Args:
            browser: Browser type ('chrome' or 'firefox')
            headless: Whether to run in headless mode
            timeout: Default timeout for operations
        """
        self.browser = browser.lower()
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.retry_count = 0
        
        if self.browser not in SUPPORTED_BROWSERS:
            raise ValueError(
                f"Unsupported browser: {browser}. Supported browsers: {SUPPORTED_BROWSERS}"
            )
    
    def setup_driver(self) -> None:
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
            options.add_argument("--headless=new")

        # Add options to make the browser more stealthy
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(f"user-agent={CHROME_USER_AGENT}")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def _setup_firefox_driver(self) -> None:
        """Set up the Firefox WebDriver."""
        options = FirefoxOptions()
        if self.headless:
            options.add_argument("--headless")

        # Add options to make the browser more stealthy
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")

        # Set preferences for Firefox
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference("general.useragent.override", FIREFOX_USER_AGENT)

        service = FirefoxService(GeckoDriverManager().install())
        self.driver = webdriver.Firefox(service=service, options=options)

    def navigate_to(self, url: str, min_wait: float = NAVIGATION_MIN_SLEEP, max_wait: float = NAVIGATION_MAX_SLEEP) -> None:
        """
        Navigate to a URL and wait for page load.

        Args:
            url: URL to navigate to
            min_wait: Minimum wait time in seconds
            max_wait: Maximum wait time in seconds
        """
        logger.info(f"Navigating to: {url}")
        self.driver.get(url)
        random_sleep(min_wait, max_wait)

    def handle_rate_limiting(self) -> bool:
        """
        Handle rate limiting by pausing and retrying.

        Returns:
            True if the rate limiting was handled, False if max retries exceeded
        """
        if self.retry_count >= MAX_RETRIES:
            logger.error(
                "Maximum retry attempts reached. LinkedIn may be rate-limiting requests."
            )
            return False

        # Increase wait time with each retry
        wait_time = 15 + (self.retry_count * 10)
        logger.info(
            f"Rate limiting detected. Waiting {wait_time} seconds before retrying..."
        )
        import time
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

    def get_total_job_count(self) -> int:
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

    def find_job_list_container(self):
        """
        Find the job list container element on the page.

        Returns:
            WebElement: The job list container, or body element as fallback
        """
        job_list_selectors = [
            "ul.scaffold-layout__list-container",
            "ul.jobs-search-results__list",
            ".scaffold-layout__list",
            ".jobs-search-results-list",
            ".jobs-search-results__list-container",
            "ul li[data-occludable-job-id]",
            "ul:has(li[data-occludable-job-id])",
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

    def scroll_job_list_container(self, job_list_container, total_expected: int) -> None:
        """
        Scroll through the job list container to load all job cards.

        Args:
            job_list_container: The container element to scroll
            total_expected: Expected total number of jobs
        """
        scroll_attempts = 0
        last_job_count = 0
        stagnant_count = 0

        while scroll_attempts < MAX_SCROLL_ATTEMPTS:
            logger.info(
                f"Scrolling job list container (attempt {scroll_attempts + 1}/{MAX_SCROLL_ATTEMPTS})"
            )
            
            # Find all currently loaded job cards
            job_card_selector = "li[data-occludable-job-id], li.jobs-search-results__list-item, li.scaffold-layout__list-item"
            job_cards = job_list_container.find_elements(By.CSS_SELECTOR, job_card_selector)
            loaded_count = len(job_cards)

            logger.info(f"Currently have {loaded_count} job card elements (loaded + placeholders)")

            # If no cards found yet, try direct page scroll
            if loaded_count == 0:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                random_sleep(1.0, 2.0)
                job_cards = job_list_container.find_elements(By.CSS_SELECTOR, job_card_selector)
                loaded_count = len(job_cards)
                logger.info(f"After page scroll, found {loaded_count} job card elements")

            # If we've found cards, scroll to the last one to load more
            if loaded_count > 0:
                last_card = job_cards[-1]
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'end', behavior: 'smooth'});",
                        last_card,
                    )
                    logger.info(f"Scrolled to job card {loaded_count}")
                except Exception as e:
                    logger.warning(f"Error scrolling to last job card: {e}")
                    try:
                        scroll_script = "arguments[0].scrollTop = arguments[0].scrollHeight;"
                        self.driver.execute_script(scroll_script, job_list_container)
                        logger.info("Scrolled job list container directly")
                    except Exception as container_scroll_error:
                        logger.warning(f"Error scrolling container: {container_scroll_error}")
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for new content to load
            random_sleep(2.0, 3.0)
            
            # Count job cards again
            job_cards = job_list_container.find_elements(By.CSS_SELECTOR, job_card_selector)
            new_count = len(job_cards)
            logger.info(f"After scrolling, now have {new_count} job card elements")

            # Check if we should stop scrolling
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
                stagnant_count = 0

            last_job_count = new_count
            scroll_attempts += 1

    def get_job_cards(self, job_list_container):
        """
        Get all job cards from the page using various selectors.

        Args:
            job_list_container: The container element to search in

        Returns:
            List of WebElements representing job cards
        """
        job_cards_selectors = [
            "li[data-occludable-job-id]",
            "li.jobs-search-results__list-item",
            "li.scaffold-layout__list-item",
            ".job-card-container",
            "[data-job-id]",
        ]
        job_cards = []

        for selector in job_cards_selectors:
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(cards) > len(job_cards):
                    job_cards = cards
                    logger.info(f"Found {len(job_cards)} job cards with selector: {selector}")
            except Exception as e:
                logger.debug(f"Failed to find job cards with selector {selector}: {e}")
                continue

        return job_cards

    def debug_page_structure(self) -> None:
        """Debug method to analyze the current page structure"""
        try:
            uls = self.driver.find_elements(By.TAG_NAME, "ul")
            logger.info(f"Found {len(uls)} UL elements on page")

            for i, ul in enumerate(uls[:5]):
                try:
                    ul_class = ul.get_attribute("class") or "no-class"
                    job_cards = ul.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")
                    if len(job_cards) > 0:
                        logger.info(f"UL {i}: class='{ul_class}' has {len(job_cards)} job cards")
                        if job_cards:
                            first_card = job_cards[0]
                            job_id = first_card.get_attribute("data-occludable-job-id")
                            logger.info(f"  First job card ID: {job_id}")

                            links = first_card.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
                            if links:
                                href = links[0].get_attribute("href")
                                logger.info(f"  First job link: {href}")
                    else:
                        logger.debug(f"UL {i}: class='{ul_class}' has no job cards")
                except Exception as e:
                    logger.debug(f"Error analyzing UL {i}: {e}")

            all_job_cards = self.driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")
            logger.info(f"Total job cards found on page: {len(all_job_cards)}")

        except Exception as e:
            logger.warning(f"Error in debug analysis: {e}")
