"""
Browser setup, navigation, retries, and scrolling functionality using Playwright.
"""

import asyncio
import logging
import random
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
    BROWSER_ARGS,
    ANONYMIZATION_CONFIG,
    USER_AGENTS_POOL,
    TIMEZONE_OPTIONS,
    LANGUAGE_OPTIONS
)
from .utils import async_random_sleep
from .extractors.selectors import JOB_LIST_CONTAINER_SELECTORS, JOB_CARD_SELECTORS

logger = logging.getLogger("linkedin_scraper")


class BrowserManager:
    """Manages browser setup, navigation, and scrolling operations using Playwright."""
    
    def __init__(self, browser: str = "chromium", headless: bool = False, timeout: int = DEFAULT_TIMEOUT, 
                 proxy: str = None, anonymize: bool = True):
        """
        Initialize browser manager.
        
        Args:
            browser: Browser type ('chromium', 'firefox', or 'webkit')
            headless: Whether to run in headless mode
            timeout: Default timeout for operations in milliseconds
            proxy: Proxy string in format "http://host:port" or "socks5://host:port"
            anonymize: Whether to enable anonymization features
        """
        self.browser = browser.lower()
        self.headless = headless
        self.timeout = timeout
        self.proxy = proxy
        self.anonymize = anonymize
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
            raise ValueError(f"Unsupported browser: {self.browser}")        # Common setup for all browsers
        await self.page.set_viewport_size({"width": 1920, "height": 1080})

    async def _setup_chromium_browser(self) -> None:
        """Set up the Chromium browser with anonymization and proxy support."""
        # Prepare launch args
        launch_args = BROWSER_ARGS.copy()
        
        # Add proxy support if specified
        launch_options = {
            "headless": self.headless,
            "args": launch_args
        }
        
        if self.proxy:
            # Parse proxy format
            if self.proxy.startswith(("http://", "https://", "socks5://")):
                proxy_config = {"server": self.proxy}
                logger.info(f"Using proxy: {self.proxy}")
            else:
                # Assume http if no protocol specified
                proxy_config = {"server": f"http://{self.proxy}"}
                logger.info(f"Using proxy: http://{self.proxy}")
        else:
            proxy_config = None
        
        self.browser_instance = await self.playwright.chromium.launch(**launch_options)
        
        # Prepare context options with anonymization
        context_options = {
            "viewport": {"width": 1920, "height": 1080}
        }
        
        # Add proxy to context if specified
        if proxy_config:
            context_options["proxy"] = proxy_config
        
        # Anonymization features
        if self.anonymize:
            # Randomize user agent
            if ANONYMIZATION_CONFIG.get("randomize_user_agent"):
                context_options["user_agent"] = random.choice(USER_AGENTS_POOL)
            else:
                context_options["user_agent"] = CHROME_USER_AGENT
                
            # Randomize timezone
            if ANONYMIZATION_CONFIG.get("randomize_timezone"):
                context_options["timezone_id"] = random.choice(TIMEZONE_OPTIONS)
                
            # Randomize language
            if ANONYMIZATION_CONFIG.get("randomize_language"):
                context_options["locale"] = random.choice(LANGUAGE_OPTIONS).split(',')[0]
        else:
            context_options["user_agent"] = CHROME_USER_AGENT
        
        self.context = await self.browser_instance.new_context(**context_options)
        
        # Enhanced anonymization scripts
        if self.anonymize:
            await self._add_anonymization_scripts()
        else:
            # Basic webdriver removal
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });            """)
        
        self.page = await self.context.new_page()

    async def _setup_firefox_browser(self) -> None:
        """Set up the Firefox browser with anonymization and proxy support."""
        # Prepare launch args
        launch_args = ["--disable-blink-features=AutomationControlled"]
        
        # Add proxy support if specified
        launch_options = {
            "headless": self.headless,
            "args": launch_args
        }
        
        if self.proxy:
            # Parse proxy format
            if self.proxy.startswith(("http://", "https://", "socks5://")):
                proxy_config = {"server": self.proxy}
                logger.info(f"Using proxy: {self.proxy}")
            else:
                # Assume http if no protocol specified
                proxy_config = {"server": f"http://{self.proxy}"}
                logger.info(f"Using proxy: http://{self.proxy}")
        else:
            proxy_config = None
        
        self.browser_instance = await self.playwright.firefox.launch(**launch_options)
        
        # Prepare context options with anonymization
        context_options = {
            "viewport": {"width": 1920, "height": 1080}
        }
        
        # Add proxy to context if specified
        if proxy_config:
            context_options["proxy"] = proxy_config
        
        # Anonymization features
        if self.anonymize:
            # Randomize user agent
            if ANONYMIZATION_CONFIG.get("randomize_user_agent"):
                context_options["user_agent"] = random.choice(USER_AGENTS_POOL)
            else:
                context_options["user_agent"] = FIREFOX_USER_AGENT
                
            # Randomize timezone
            if ANONYMIZATION_CONFIG.get("randomize_timezone"):
                context_options["timezone_id"] = random.choice(TIMEZONE_OPTIONS)
                
            # Randomize language
            if ANONYMIZATION_CONFIG.get("randomize_language"):
                context_options["locale"] = random.choice(LANGUAGE_OPTIONS).split(',')[0]
        else:
            context_options["user_agent"] = FIREFOX_USER_AGENT
        
        self.context = await self.browser_instance.new_context(**context_options)
        
        # Enhanced anonymization scripts
        if self.anonymize:
            await self._add_anonymization_scripts()
        else:
            # Basic webdriver removal
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });            """)
        
        self.page = await self.context.new_page()

    async def _setup_webkit_browser(self) -> None:
        """Set up the WebKit browser with anonymization and proxy support."""
        # Prepare launch options
        launch_options = {
            "headless": self.headless
        }
        
        if self.proxy:
            # Parse proxy format
            if self.proxy.startswith(("http://", "https://", "socks5://")):
                proxy_config = {"server": self.proxy}
                logger.info(f"Using proxy: {self.proxy}")
            else:
                # Assume http if no protocol specified
                proxy_config = {"server": f"http://{self.proxy}"}
                logger.info(f"Using proxy: http://{self.proxy}")
        else:
            proxy_config = None
        
        self.browser_instance = await self.playwright.webkit.launch(**launch_options)
        
        # Prepare context options with anonymization
        context_options = {
            "viewport": {"width": 1920, "height": 1080}
        }
        
        # Add proxy to context if specified
        if proxy_config:
            context_options["proxy"] = proxy_config
        
        # Anonymization features
        if self.anonymize:
            # Randomize user agent
            if ANONYMIZATION_CONFIG.get("randomize_user_agent"):
                context_options["user_agent"] = random.choice(USER_AGENTS_POOL)
            else:
                context_options["user_agent"] = WEBKIT_USER_AGENT
                
            # Randomize timezone
            if ANONYMIZATION_CONFIG.get("randomize_timezone"):
                context_options["timezone_id"] = random.choice(TIMEZONE_OPTIONS)
                
            # Randomize language
            if ANONYMIZATION_CONFIG.get("randomize_language"):
                context_options["locale"] = random.choice(LANGUAGE_OPTIONS).split(',')[0]
        else:
            context_options["user_agent"] = WEBKIT_USER_AGENT
        
        self.context = await self.browser_instance.new_context(**context_options)
        
        # Enhanced anonymization scripts
        if self.anonymize:
            await self._add_anonymization_scripts()
        else:
            # Basic webdriver removal
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
        
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
            ElementHandle: The job list container, or body element as fallback        """
        job_list_selectors = JOB_LIST_CONTAINER_SELECTORS

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
            List of ElementHandles representing job cards        """
        job_cards_selectors = JOB_CARD_SELECTORS
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

    async def _add_anonymization_scripts(self) -> None:
        """Add comprehensive anonymization scripts to the browser context."""
        anonymization_script = """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Override navigator properties
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Override chrome property
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Remove automation signals
        const originalQuery = window.document.querySelector;
        window.document.querySelector = function(selector) {
            if (selector === 'script[src*="automation"]') {
                return null;
            }
            return originalQuery.call(document, selector);
        };
        
        // Disable WebGL fingerprinting if configured
        if (""" + str(ANONYMIZATION_CONFIG.get("disable_webgl", False)).lower() + """) {
            const getContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type) {
                if (type === 'webgl' || type === 'webgl2') {
                    return null;
                }
                return getContext.call(this, type);
            };
        }
        
        // Disable canvas fingerprinting if configured  
        if (""" + str(ANONYMIZATION_CONFIG.get("disable_canvas_fingerprinting", False)).lower() + """) {
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==';
            };
        }
        
        // Block WebRTC if configured
        if (""" + str(ANONYMIZATION_CONFIG.get("block_webrtc", False)).lower() + """) {
            window.RTCPeerConnection = undefined;
            window.RTCDataChannel = undefined;
            window.RTCSessionDescription = undefined;
        }
        """
        
        await self.context.add_init_script(anonymization_script)
