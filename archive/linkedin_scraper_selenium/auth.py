"""
Authentication and CAPTCHA handling for LinkedIn.
"""

import time
import random
import os
import logging
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .utils import random_sleep

logger = logging.getLogger("linkedin_scraper")


class AuthManager:
    """Handles LinkedIn authentication and CAPTCHA detection."""
    
    def __init__(self, driver, timeout: int = 20):
        """
        Initialize authentication manager.
        
        Args:
            driver: WebDriver instance
            timeout: Timeout for authentication operations
        """
        self.driver = driver
        self.timeout = timeout
        self._login_attempted = False
        self._login_successful = False

    def ensure_login(self, username: str, password: str) -> bool:
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
            self._login_successful = self.login(username, password)
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

    def login(self, username: str, password: str) -> bool:
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
            self.driver.get("https://www.linkedin.com/login")
            random_sleep(2.0, 3.0)

            # Wait for the login form
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "username"))
            )

            # Fill in username and password
            username_field = self.driver.find_element(By.ID, "username")
            password_field = self.driver.find_element(By.ID, "password")

            username_field.clear()
            # Type like a human - character by character
            for char in username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))

            password_field.clear()
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))

            # Click the login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            # Wait for the login to complete
            random_sleep(3.0, 5.0)

            # Check if login was successful
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
                    logger.info("Successfully logged in to LinkedIn (alternative check)")
                    return True
                except TimeoutException:
                    logger.error("Failed to login - could not find post-login elements")

                    # Check for security verification
                    if self.check_for_captcha():
                        logger.warning(
                            "Security verification required after login. Please check the browser."
                        )

                    return False

        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False

    def check_for_captcha(self) -> bool:
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
                if self.driver.find_elements(By.CSS_SELECTOR, selector):
                    logger.info("Job listings found, definitely not a CAPTCHA page")
                    return False

            # Check for visible CAPTCHA indicators
            captcha_indicators = [
                "//h1[contains(text(), 'Security Verification') and not(ancestor::*[contains(@style,'display: none')])]",
                "//div[contains(text(), 'CAPTCHA') and not(ancestor::*[contains(@style,'display: none')])]",
                "//div[contains(text(), 'security check') and not(ancestor::*[contains(@style,'display: none')])]",
                "//form[contains(@action, 'checkpoint') and not(ancestor::*[contains(@style,'display: none')])]",
                "//input[@name='captcha' and not(ancestor::*[contains(@style,'display: none')])]",
                "//img[contains(@src, 'captcha') and not(ancestor::*[contains(@style,'display: none')])]",
                "//iframe[contains(@src, 'captcha') or contains(@src, 'recaptcha')]",
            ]

            for indicator in captcha_indicators:
                elements = self.driver.find_elements(By.XPATH, indicator)
                for element in elements:
                    if element.is_displayed():
                        logger.warning("CAPTCHA or security verification detected and is visible")
                        captcha_path = os.path.join(
                            "output",
                            "linkedin",
                            f"captcha_confirmed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        )
                        os.makedirs(os.path.dirname(captcha_path), exist_ok=True)
                        self.driver.save_screenshot(captcha_path)

                        # Try to get the text of the verification page
                        try:
                            body_text = self.driver.find_element(By.TAG_NAME, "body").text
                            logger.info(f"CAPTCHA page text: {body_text[:500]}...")
                        except:
                            pass

                        return True

            # Check for LinkedIn main structure
            linkedin_main_elements = [
                "#global-nav",
                ".nav-main",
                ".search-global-typeahead",
                ".feed-identity-module",
            ]

            for selector in linkedin_main_elements:
                if self.driver.find_elements(By.CSS_SELECTOR, selector):
                    logger.info("LinkedIn main elements found, likely not a CAPTCHA page")
                    return False

            # Check for "No results found" message
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

            # Check page title
            page_title = self.driver.title
            logger.info(f"Current page title: {page_title}")

            if "Security Verification" in page_title or "CAPTCHA" in page_title:
                logger.warning("CAPTCHA detected from page title")
                captcha_path = os.path.join(
                    "output",
                    "linkedin",
                    f"captcha_from_title_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                )
                os.makedirs(os.path.dirname(captcha_path), exist_ok=True)
                self.driver.save_screenshot(captcha_path)
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking for CAPTCHA: {str(e)}")
            return False
