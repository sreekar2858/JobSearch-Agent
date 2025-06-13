"""
Authentication and CAPTCHA handling for LinkedIn using Playwright.
"""

import asyncio
import random
import os
import logging
from datetime import datetime

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .utils import async_random_sleep, save_screenshot

logger = logging.getLogger("linkedin_scraper")


class AuthManager:
    """Handles LinkedIn authentication and CAPTCHA detection using Playwright."""
    
    def __init__(self, page: Page, timeout: int = 20000):
        """
        Initialize authentication manager.
        
        Args:
            page: Playwright Page instance
            timeout: Timeout for authentication operations in milliseconds
        """
        self.page = page
        self.timeout = timeout
        self._login_attempted = False
        self._login_successful = False

    async def ensure_login(self, username: str, password: str) -> bool:
        """
        Ensure user is logged in (always required for LinkedIn scraping).
        
        Args:
            username: LinkedIn username
            password: LinkedIn password
            
        Returns:
            True if logged in successfully, False if login failed
        """
        if not self._login_attempted:
            logger.info("🔐 Attempting LinkedIn login (required for job scraping)...")
            self._login_successful = await self.login(username, password)
            self._login_attempted = True

            if self._login_successful:
                logger.info("✅ Successfully logged in to LinkedIn")
            else:
                logger.error("❌ Login failed! Cannot proceed without LinkedIn authentication.")
                raise RuntimeError(
                    "LinkedIn login is required for job scraping but failed. "
                    "Please check your credentials in the .env file."
                )

        return self._login_successful

    async def login(self, username: str, password: str) -> bool:
        """
        Log in to LinkedIn using credentials.

        Args:
            username: LinkedIn username
            password: LinkedIn password
            
        Returns:
            True if login successful, False otherwise
        """
        if not username or not password:
            logger.error("LinkedIn credentials are missing! Cannot proceed without authentication.")
            raise ValueError("LinkedIn username and password are required for scraping.")

        try:
            logger.info(f"🔐 Attempting to login with username: {username}")

            # Navigate to LinkedIn login page
            await self.page.goto("https://www.linkedin.com/login")
            await async_random_sleep(2.0, 3.0)

            # Wait for the login form
            await self.page.wait_for_selector("#username", timeout=self.timeout)            # Fill in username and password
            username_field = await self.page.query_selector("#username")
            password_field = await self.page.query_selector("#password")

            # Clear and type username
            await username_field.fill("")  # Clear the field
            # Type like a human - character by character
            for char in username:
                await username_field.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.2))

            # Clear and type password
            await password_field.fill("")  # Clear the field
            for char in password:
                await password_field.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.2))

            # Click the login button
            login_button = await self.page.query_selector("button[type='submit']")
            await login_button.click()

            # Wait for the login to complete
            await async_random_sleep(3.0, 5.0)

            # Check if login was successful
            try:
                await self.page.wait_for_selector("#global-nav", timeout=self.timeout)
                logger.info("Successfully logged in to LinkedIn")
                return True
            except PlaywrightTimeoutError:
                # Try an alternative selector
                try:
                    await self.page.wait_for_selector(".nav-main", timeout=self.timeout)
                    logger.info("Successfully logged in to LinkedIn (alternative check)")
                    return True
                except PlaywrightTimeoutError:
                    logger.error("Failed to login - could not find post-login elements")

                    # Check for security verification
                    if await self.check_for_captcha():
                        logger.warning(
                            "Security verification required after login. Please check the browser."
                        )

                    return False

        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False

    async def check_for_captcha(self) -> bool:
        """
        Check if the page is showing a CAPTCHA or security verification.
        
        Returns:
            True if a CAPTCHA is detected, False otherwise
        """
        try:
            # First check: Look for job listing elements to verify we're on the results page
            job_listing_selectors = [
                ".jobs-search__results-list",
                ".scaffold-layout__list",
                ".job-search-results",
                "ul.jobs-search-results__list",
                ".jobs-search-results-list",
            ]

            for selector in job_listing_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    logger.info("Job listings found, definitely not a CAPTCHA page")
                    return False

            # Check for visible CAPTCHA indicators
            captcha_selectors = [
                "h1:has-text('Security Verification')",
                "div:has-text('CAPTCHA')",
                "div:has-text('security check')",
                "form[action*='checkpoint']",
                "input[name='captcha']",
                "img[src*='captcha']",
                "iframe[src*='captcha'], iframe[src*='recaptcha']",
            ]

            for selector in captcha_selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        logger.warning("CAPTCHA or security verification detected and is visible")
                        await save_screenshot(
                            self.page,
                            f"captcha_confirmed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        )

                        # Try to get the text of the verification page
                        try:
                            body = await self.page.query_selector("body")
                            body_text = await body.text_content()
                            logger.info(f"CAPTCHA page text: {body_text[:500]}...")
                        except:
                            pass

                        return True

            # Check for LinkedIn main structure
            linkedin_main_selectors = [
                "#global-nav",
                ".nav-main",
                ".search-global-typeahead",
                ".feed-identity-module",
            ]

            for selector in linkedin_main_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    logger.info("LinkedIn main elements found, likely not a CAPTCHA page")
                    return False

            # Check for "No results found" message
            no_results_selectors = [
                "h1:has-text('No matching')",
                "div:has-text('No matching')",
                "p:has-text('No matching')",
            ]

            for selector in no_results_selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        logger.info("'No results' message found, not a CAPTCHA page")
                        return False

            # Check page title
            page_title = await self.page.title()
            logger.info(f"Current page title: {page_title}")

            if "Security Verification" in page_title or "CAPTCHA" in page_title:
                logger.warning("CAPTCHA detected from page title")
                await save_screenshot(
                    self.page,
                    f"captcha_from_title_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking for CAPTCHA: {str(e)}")
            return False
