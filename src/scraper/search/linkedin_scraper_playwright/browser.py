"""
Browser setup, navigation, retries, and scrolling functionality using Playwright.
"""

import asyncio
import logging
from typing import Optional, List

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .config import (
    CHROME_USER_AGENT, 
    FIREFOX_USER_AGENT, 
    WEBKIT_USER_AGENT,
    SUPPORTED_BROWSERS,
    MAX_RETRIES,
    MAX_SCROLL_ATTEMPTS,
    NAVIGATION_MIN_SLEEP,
    NAVIGATION_MAX_SLEEP,
    DEFAULT_TIMEOUT,
    BROWSER_ARGS
)
from .utils import async_random_sleep

logger = logging.getLogger("linkedin_scraper")


class BrowserManager:
    """Manages browser setup, navigation, and scrolling operations using Playwright."""
    
    def __init__(self, browser: str = "chromium", headless: bool = False, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize browser manager.
        
        Args:
            browser: Browser type ('chromium', 'firefox', or 'webkit')
            headless: Whether to run in headless mode
            timeout: Default timeout for operations in milliseconds
        """
        self.browser = browser.lower()
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser_instance = None
        self.context = None
        self.page = None
        self.retry_count = 0
        
        if self.browser not in SUPPORTED_BROWSERS:
            raise ValueError(
                f"Unsupported browser: {browser}. Supported browsers: {SUPPORTED_BROWSERS}"
            )
    
    async def setup_driver(self) -> None:
        """Set up the browser based on the selected browser type."""
        self.playwright = await async_playwright().start()
        
        if self.browser == "chromium":
            await self._setup_chromium_browser()
        elif self.browser == "firefox":
            await self._setup_firefox_browser()
        elif self.browser == "webkit":
            await self._setup_webkit_browser()
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")

        # Common setup for all browsers
        await self.page.set_viewport_size({"width": 1920, "height": 1080})

    async def _setup_chromium_browser(self) -> None:
        """Set up the Chromium browser."""
        self.browser_instance = await self.playwright.chromium.launch(
            headless=self.headless,
            args=BROWSER_ARGS
        )
        
        self.context = await self.browser_instance.new_context(
            user_agent=CHROME_USER_AGENT,
            viewport={"width": 1920, "height": 1080}
        )
        
        # Add script to remove webdriver property
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        self.page = await self.context.new_page()

    async def _setup_firefox_browser(self) -> None:
        """Set up the Firefox browser."""
        self.browser_instance = await self.playwright.firefox.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        self.context = await self.browser_instance.new_context(
            user_agent=FIREFOX_USER_AGENT,
            viewport={"width": 1920, "height": 1080}
        )
        
        # Add script to remove webdriver property
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        self.page = await self.context.new_page()

    async def _setup_webkit_browser(self) -> None:
        """Set up the WebKit browser."""
        self.browser_instance = await self.playwright.webkit.launch(
            headless=self.headless
        )
        
        self.context = await self.browser_instance.new_context(
            user_agent=WEBKIT_USER_AGENT,
            viewport={"width": 1920, "height": 1080}
        )
        
        self.page = await self.context.new_page()

    async def navigate_to(self, url: str, min_wait: float = NAVIGATION_MIN_SLEEP, max_wait: float = NAVIGATION_MAX_SLEEP) -> None:
        """
        Navigate to a URL and wait for page load.

        Args:
            url: URL to navigate to
            min_wait: Minimum wait time in seconds
            max_wait: Maximum wait time in seconds
        """
        logger.info(f"Navigating to: {url}")
        await self.page.goto(url, timeout=self.timeout)
        await async_random_sleep(min_wait, max_wait)

    async def handle_rate_limiting(self) -> bool:
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
        await asyncio.sleep(wait_time)

        self.retry_count += 1
        return True

    async def close(self) -> None:
        """Close the browser session."""
        if self.page:
            try:
                await self.page.close()
                self.page = None
                logger.info("Page closed")
            except Exception as e:
                logger.error(f"Error closing page: {str(e)}")
                self.page = None

        if self.context:
            try:
                await self.context.close()
                self.context = None
                logger.info("Browser context closed")
            except Exception as e:
                logger.error(f"Error closing context: {str(e)}")
                self.context = None

        if self.browser_instance:
            try:
                await self.browser_instance.close()
                self.browser_instance = None
                logger.info("Browser instance closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
                self.browser_instance = None

        if self.playwright:
            try:
                await self.playwright.stop()
                self.playwright = None
                logger.info("Playwright stopped")
            except Exception as e:
                logger.error(f"Error stopping playwright: {str(e)}")
                self.playwright = None

    async def get_total_job_count(self) -> int:
        """
        Extract the total number of jobs from the search results page.

        Returns:
            int: Total expected job count, or 0 if not found
        """
        try:
            total_jobs_element = await self.page.query_selector(
                ".jobs-search-results-list__title-heading .t-12, .jobs-search-results-list__subtitle"
            )
            if total_jobs_element:
                results_text = await total_jobs_element.text_content()
                if results_text and "results" in results_text:
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

    async def find_job_list_container(self):
        """
        Find the job list container element on the page.

        Returns:
            ElementHandle: The job list container, or body element as fallback
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
                job_list_container = await self.page.query_selector(selector)
                if job_list_container:
                    logger.info(f"Found job list container with selector: {selector}")
                    return job_list_container
            except:
                continue

        # If no specific container found, try to find the UL that contains job cards
        try:
            uls = await self.page.query_selector_all("ul")
            for ul in uls:
                job_cards_in_ul = await ul.query_selector_all("li[data-occludable-job-id]")
                if len(job_cards_in_ul) > 0:
                    logger.info(
                        f"Found job list container (UL with {len(job_cards_in_ul)} job cards)"
                    )
                    return ul
        except Exception as e:
            logger.warning(f"Error finding UL with job cards: {e}")

        logger.warning("Could not find job list container, using body instead")
        return await self.page.query_selector("body")

    async def scroll_job_list_container(self, job_list_container, total_expected: int) -> None:
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
            job_cards = await job_list_container.query_selector_all(job_card_selector)
            loaded_count = len(job_cards)

            logger.info(f"Currently have {loaded_count} job card elements (loaded + placeholders)")

            # If no cards found yet, try direct page scroll
            if loaded_count == 0:
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
                await async_random_sleep(1.0, 2.0)
                job_cards = await job_list_container.query_selector_all(job_card_selector)
                loaded_count = len(job_cards)
                logger.info(f"After page scroll, found {loaded_count} job card elements")

            # If we've found cards, scroll to the last one to load more
            if loaded_count > 0:
                last_card = job_cards[-1]
                try:
                    await last_card.scroll_into_view_if_needed()
                    logger.info(f"Scrolled to job card {loaded_count}")
                except Exception as e:
                    logger.warning(f"Error scrolling to last job card: {e}")
                    try:
                        await job_list_container.evaluate("el => el.scrollTop = el.scrollHeight")
                        logger.info("Scrolled job list container directly")
                    except Exception as container_scroll_error:
                        logger.warning(f"Error scrolling container: {container_scroll_error}")
                        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for new content to load
            await async_random_sleep(2.0, 3.0)
            
            # Count job cards again
            job_cards = await job_list_container.query_selector_all(job_card_selector)
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

    async def get_job_cards(self, job_list_container):
        """
        Get all job cards from the page using various selectors.

        Args:
            job_list_container: The container element to search in

        Returns:
            List of ElementHandles representing job cards
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
                cards = await self.page.query_selector_all(selector)
                if len(cards) > len(job_cards):
                    job_cards = cards
                    logger.info(f"Found {len(job_cards)} job cards with selector: {selector}")
            except Exception as e:
                logger.debug(f"Failed to find job cards with selector {selector}: {e}")
                continue

        return job_cards

    async def debug_page_structure(self) -> None:
        """Debug method to analyze the current page structure"""
        try:
            uls = await self.page.query_selector_all("ul")
            logger.info(f"Found {len(uls)} UL elements on page")

            for i, ul in enumerate(uls[:5]):
                try:
                    ul_class = await ul.get_attribute("class") or "no-class"
                    job_cards = await ul.query_selector_all("li[data-occludable-job-id]")
                    if len(job_cards) > 0:
                        logger.info(f"UL {i}: class='{ul_class}' has {len(job_cards)} job cards")
                        if job_cards:
                            first_card = job_cards[0]
                            job_id = await first_card.get_attribute("data-occludable-job-id")
                            logger.info(f"  First job card ID: {job_id}")

                            links = await first_card.query_selector_all("a[href*='/jobs/view/']")
                            if links:
                                href = await links[0].get_attribute("href")
                                logger.info(f"  First job link: {href}")
                    else:
                        logger.debug(f"UL {i}: class='{ul_class}' has no job cards")
                except Exception as e:
                    logger.debug(f"Error analyzing UL {i}: {e}")

            all_job_cards = await self.page.query_selector_all("li[data-occludable-job-id]")
            logger.info(f"Total job cards found on page: {len(all_job_cards)}")

        except Exception as e:
            logger.warning(f"Error in debug analysis: {e}")
