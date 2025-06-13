"""
Search filters and query helpers for LinkedIn job search.
"""

import logging
from typing import List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .config import EXPERIENCE_LEVEL_MAPPING, DATE_POSTED_MAPPING, EXPERIENCE_DISPLAY_TEXT, DATE_DISPLAY_TEXT
from .utils import random_sleep

logger = logging.getLogger("linkedin_scraper")


class FilterManager:
    """Manages LinkedIn search filters."""
    
    def __init__(self, driver, timeout: int = 20):
        """
        Initialize filter manager.
        
        Args:
            driver: WebDriver instance
            timeout: Timeout for filter operations
        """
        self.driver = driver
        self.timeout = timeout

    def apply_search_filters(
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
            if not self.apply_experience_level_filter(experience_levels):
                success = False

        # Apply date posted filter
        if date_posted:
            if not self.apply_date_posted_filter(date_posted):
                success = False

        return success

    def apply_experience_level_filter(self, experience_levels: List[str]) -> bool:
        """
        Apply experience level filter with robust error handling and fallback strategies.

        Args:
            experience_levels: List of experience levels to filter by.

        Returns:
            bool: True if filter was applied successfully, False otherwise
        """
        if not experience_levels:
            return True

        try:
            logger.info(f"Applying experience level filter: {experience_levels}")

            # Find and click the experience level filter button
            experience_button_selectors = [
                'button[id="searchFilter_experience"]',
                'button[aria-label*="Experience level filter"]',
                '.search-reusables__filter-trigger-and-dropdown[data-basic-filter-parameter-name="experience"] button',
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
            random_sleep(1.0, 2.0)

            # Wait for dropdown and get container
            dropdown_container = self._get_dropdown_container()
            if not dropdown_container:
                logger.warning("Experience level dropdown did not appear")
                return False

            random_sleep(1.0, 1.5)

            # Select experience levels with robust fallback
            selections_made = 0
            for level in experience_levels:
                if level.lower() in EXPERIENCE_LEVEL_MAPPING:
                    value = EXPERIENCE_LEVEL_MAPPING[level.lower()]
                    checkbox_id = f"experience-{value}"

                    if self._select_checkbox(dropdown_container, checkbox_id, level, value):
                        selections_made += 1
                        logger.debug(f"Selected experience level: {level}")
                        random_sleep(0.5, 1.0)
                    else:
                        logger.warning(f"Could not select experience level: {level}")
                else:
                    logger.warning(f"Invalid experience level: {level}")

            if selections_made == 0:
                logger.warning("No experience level selections were made")
                self._close_dropdown(dropdown_container)
                return False

            # Apply the filter
            logger.info(f"Successfully selected {selections_made} experience levels")
            return self._apply_filter(dropdown_container, selections_made)

        except Exception as e:
            logger.error(f"Failed to apply experience level filter: {e}")
            return False

    def apply_date_posted_filter(self, date_posted: str) -> bool:
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

        try:
            logger.info(f"Applying date posted filter: {date_posted}")

            # Find and click the date posted filter button
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
            random_sleep(1.0, 2.0)

            # Wait for the dropdown to appear
            dropdown_container = self._get_dropdown_container()
            if not dropdown_container:
                logger.warning("Date posted dropdown container did not appear")
                return False

            random_sleep(1.0, 1.5)

            # Select the specified date option
            if date_posted.lower() in DATE_POSTED_MAPPING:
                value = DATE_POSTED_MAPPING[date_posted.lower()]
                radio_id = f"timePostedRange-{value}"

                if self._select_radio_button(dropdown_container, radio_id, date_posted, value):
                    logger.info(f"Selected date posted option: {date_posted}")
                    random_sleep(0.5, 1.0)
                else:
                    logger.warning(f"Could not find or select radio button for date: {date_posted}")
                    return False
            else:
                logger.warning(f"Invalid date posted option: {date_posted}")
                return False

            # Apply the filter
            return self._apply_filter(dropdown_container, 1)

        except Exception as e:
            logger.error(f"Failed to apply date posted filter: {e}")
            return False

    def _get_dropdown_container(self):
        """Get the dropdown container element."""
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
                        (By.CSS_SELECTOR, f"{selector} input[type='checkbox'], {selector} input[type='radio']")
                    )
                )
                logger.debug(f"Dropdown container found with selector: {selector}")
                return dropdown_container
            except TimeoutException:
                continue

        return None

    def _select_checkbox(self, dropdown_container, checkbox_id: str, level: str, value: str) -> bool:
        """Select a checkbox in the dropdown with multiple fallback strategies."""
        try:
            # Strategy 1: Find by exact ID
            try:
                checkbox = dropdown_container.find_element(By.ID, checkbox_id)
                if checkbox.is_displayed():
                    if not checkbox.is_selected():
                        # Try clicking the associated label first
                        try:
                            label = dropdown_container.find_element(By.CSS_SELECTOR, f'label[for="{checkbox_id}"]')
                            self.driver.execute_script("arguments[0].click();", label)
                        except:
                            # Fallback to clicking checkbox directly
                            self.driver.execute_script("arguments[0].click();", checkbox)
                    return True
            except NoSuchElementException:
                pass

            # Strategy 2: Find by value attribute with various name patterns
            name_patterns = [
                'experience-level-filter-value',
                'experience',
                'experienceLevel'
            ]
            
            for name_pattern in name_patterns:
                try:
                    xpath = f"//input[@name='{name_pattern}'][@value='{value}']"
                    checkbox = dropdown_container.find_element(By.XPATH, xpath)
                    if checkbox.is_displayed() and not checkbox.is_selected():
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        return True
                except NoSuchElementException:
                    continue

            # Strategy 3: Find by visible text content (case-insensitive)
            display_texts = [
                EXPERIENCE_DISPLAY_TEXT.get(level.lower()),
                level.title(),
                level.lower(),
                level.upper()
            ]
            
            for display_text in display_texts:
                if display_text:
                    try:
                        # Try exact text match
                        xpath = f"//span[text()='{display_text}']/ancestor::label"
                        label = dropdown_container.find_element(By.XPATH, xpath)
                        if label.is_displayed():
                            self.driver.execute_script("arguments[0].click();", label)
                            return True
                    except NoSuchElementException:
                        try:
                            # Try contains text match
                            xpath = f"//span[contains(text(), '{display_text}')]/ancestor::label"
                            label = dropdown_container.find_element(By.XPATH, xpath)
                            if label.is_displayed():
                                self.driver.execute_script("arguments[0].click();", label)
                                return True
                        except NoSuchElementException:
                            continue

            # Strategy 4: Find any checkbox with similar data attributes
            try:
                xpath = f"//input[@type='checkbox'][contains(@value, '{value}') or contains(@id, '{value}')]"
                checkbox = dropdown_container.find_element(By.XPATH, xpath)
                if checkbox.is_displayed() and not checkbox.is_selected():
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    return True
            except NoSuchElementException:
                pass

            logger.warning(f"Could not find any suitable checkbox for experience level: {level}")
            return False

        except Exception as e:
            logger.warning(f"Error selecting experience level {level}: {e}")
            return False

    def _select_radio_button(self, dropdown_container, radio_id: str, date_posted: str, value: str) -> bool:
        """Select a radio button in the dropdown with multiple fallback strategies."""
        try:
            # Strategy 1: Find by exact ID
            try:
                radio_button = dropdown_container.find_element(By.ID, radio_id)
                if radio_button.is_displayed():
                    if not radio_button.is_selected():
                        # Try clicking the associated label first
                        try:
                            label = dropdown_container.find_element(By.CSS_SELECTOR, f'label[for="{radio_id}"]')
                            self.driver.execute_script("arguments[0].click();", label)
                        except:
                            # Fallback to clicking radio button directly
                            self.driver.execute_script("arguments[0].click();", radio_button)
                    return True
            except NoSuchElementException:
                pass

            # Strategy 2: Find by value attribute with various name patterns
            name_patterns = [
                'timePostedRange',
                'date-posted-filter-value',
                'datePosted',
                'timePosted'
            ]
            
            for name_pattern in name_patterns:
                try:
                    xpath = f"//input[@name='{name_pattern}'][@value='{value}']"
                    radio_button = dropdown_container.find_element(By.XPATH, xpath)
                    if radio_button.is_displayed() and not radio_button.is_selected():
                        self.driver.execute_script("arguments[0].click();", radio_button)
                        return True
                except NoSuchElementException:
                    continue

            # Strategy 3: Find by visible text content (case-insensitive)
            display_texts = [
                DATE_DISPLAY_TEXT.get(date_posted.lower()),
                date_posted.replace('_', ' ').title(),
                date_posted.lower(),
                date_posted.upper()
            ]
            
            for display_text in display_texts:
                if display_text:
                    try:
                        # Try exact text match
                        xpath = f"//span[text()='{display_text}']/ancestor::label"
                        label = dropdown_container.find_element(By.XPATH, xpath)
                        if label.is_displayed():
                            self.driver.execute_script("arguments[0].click();", label)
                            return True
                    except NoSuchElementException:
                        try:
                            # Try contains text match
                            xpath = f"//span[contains(text(), '{display_text}')]/ancestor::label"
                            label = dropdown_container.find_element(By.XPATH, xpath)
                            if label.is_displayed():
                                self.driver.execute_script("arguments[0].click();", label)
                                return True
                        except NoSuchElementException:
                            continue

            # Strategy 4: Find any radio button with similar data attributes
            try:
                xpath = f"//input[@type='radio'][contains(@value, '{value}') or contains(@id, '{value}')]"
                radio_button = dropdown_container.find_element(By.XPATH, xpath)
                if radio_button.is_displayed() and not radio_button.is_selected():
                    self.driver.execute_script("arguments[0].click();", radio_button)
                    return True
            except NoSuchElementException:
                pass

            logger.warning(f"Could not find any suitable radio button for date: {date_posted}")
            return False

        except Exception as e:
            logger.warning(f"Error selecting date posted option: {e}")
            return False

    def _close_dropdown(self, dropdown_container) -> None:
        """Close the dropdown if no selections were made with multiple strategies."""
        try:
            # Strategy 1: Look for specific cancel buttons
            cancel_selectors = [
                'button[aria-label*="Cancel Experience level filter"]',
                'button[aria-label*="Cancel Date posted filter"]',
                'button[aria-label*="Cancel"]',
                ".reusable-search-filters-buttons button.artdeco-button--tertiary",
                'button[class*="artdeco-button--tertiary"]',
            ]
            
            for selector in cancel_selectors:
                try:
                    cancel_button = dropdown_container.find_element(By.CSS_SELECTOR, selector)
                    if cancel_button.is_displayed() and cancel_button.is_enabled():
                        self.driver.execute_script("arguments[0].click();", cancel_button)
                        logger.debug("Successfully closed dropdown with cancel button")
                        return
                except:
                    continue

            # Strategy 2: Click outside the dropdown to close it
            try:
                # Click on the body element to close dropdown
                body = self.driver.find_element(By.TAG_NAME, "body")
                self.driver.execute_script("arguments[0].click();", body)
                logger.debug("Closed dropdown by clicking outside")
                return
            except:
                pass

            # Strategy 3: Press ESC key
            try:
                from selenium.webdriver.common.keys import Keys
                dropdown_container.send_keys(Keys.ESCAPE)
                logger.debug("Closed dropdown with ESC key")
            except:
                pass

        except Exception as e:
            logger.debug(f"Could not close dropdown: {e}")
            pass

    def _apply_filter(self, dropdown_container, selections_made: int) -> bool:
        """Apply the selected filter options with robust button detection."""
        try:
            # Strategy 1: Look for specific apply buttons
            apply_button_selectors = [
                'button.artdeco-button--primary[aria-label*="Apply current filter"]',
                'button.artdeco-button--primary[aria-label*="Show"]',
                ".reusable-search-filters-buttons button.artdeco-button--primary",
                'button[class*="artdeco-button--primary"][aria-label*="Show"]',
                'button[class*="artdeco-button--primary"]',
                'button[type="submit"]',
            ]

            apply_button = None
            for selector in apply_button_selectors:
                try:
                    buttons = dropdown_container.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            # Check if button text suggests it's an apply button
                            button_text = button.text.lower()
                            if any(keyword in button_text for keyword in ['show', 'apply', 'done', 'submit']):
                                apply_button = button
                                break
                    if apply_button:
                        break
                except NoSuchElementException:
                    continue

            if apply_button:
                self.driver.execute_script("arguments[0].click();", apply_button)
                random_sleep(2.0, 4.0)  # Wait for page reload
                logger.info(f"Applied filter with {selections_made} selections")
                return True
            else:
                logger.warning("Could not find apply button for filter")
                
                # Strategy 2: Try pressing Enter key as fallback
                try:
                    from selenium.webdriver.common.keys import Keys
                    dropdown_container.send_keys(Keys.ENTER)
                    random_sleep(2.0, 4.0)
                    logger.info(f"Applied filter using Enter key with {selections_made} selections")
                    return True
                except:
                    pass
                
                return False

        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            return False
