"""
Search filters and query helpers for LinkedIn job search using Playwright.
"""

import logging
from typing import List, Optional

from playwright.async_api import Page, ElementHandle, TimeoutError as PlaywrightTimeoutError

from .config import EXPERIENCE_LEVEL_MAPPING, DATE_POSTED_MAPPING, EXPERIENCE_DISPLAY_TEXT, DATE_DISPLAY_TEXT
from .utils import async_random_sleep
from .extractors.selectors import EXPERIENCE_FILTER_SELECTOR, TIME_POSTED_FILTER_SELECTOR

logger = logging.getLogger("linkedin_scraper")


class FilterManager:
    """Manages LinkedIn search filters using Playwright."""
    
    def __init__(self, page: Page, timeout: int = 20000):
        """
        Initialize filter manager.
        
        Args:
            page: Playwright Page instance
            timeout: Timeout for filter operations in milliseconds
        """
        self.page = page
        self.timeout = timeout

    async def apply_search_filters(
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
            if not await self.apply_experience_level_filter(experience_levels):
                success = False

        # Apply date posted filter
        if date_posted:
            if not await self.apply_date_posted_filter(date_posted):
                success = False

        return success

    async def apply_experience_level_filter(self, experience_levels: List[str]) -> bool:
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
            logger.info(f"Applying experience level filter: {experience_levels}")            # Find and click the experience level filter button
            experience_button_selectors = [
                'button[id="searchFilter_experience"]',
                'button[aria-label*="Experience level filter"]',
                EXPERIENCE_FILTER_SELECTOR,
            ]

            experience_button = None
            for selector in experience_button_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    experience_button = await self.page.query_selector(selector)
                    if experience_button:
                        logger.debug(f"Found experience button with selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue

            if not experience_button:
                logger.warning("Could not find experience level filter button")
                return False

            # Click to open the dropdown
            await experience_button.click()
            await async_random_sleep(1.0, 2.0)

            # Wait for dropdown and get container
            dropdown_container = await self._get_dropdown_container()
            if not dropdown_container:
                logger.warning("Experience level dropdown did not appear")
                return False

            await async_random_sleep(1.0, 1.5)

            # Select experience levels with robust fallback
            selections_made = 0
            for level in experience_levels:
                if level.lower() in EXPERIENCE_LEVEL_MAPPING:
                    value = EXPERIENCE_LEVEL_MAPPING[level.lower()]
                    checkbox_id = f"experience-{value}"

                    if await self._select_checkbox(dropdown_container, checkbox_id, level, value):
                        selections_made += 1
                        logger.debug(f"Selected experience level: {level}")
                        await async_random_sleep(0.5, 1.0)
                    else:
                        logger.warning(f"Could not select experience level: {level}")
                else:
                    logger.warning(f"Invalid experience level: {level}")

            if selections_made == 0:
                logger.warning("No experience level selections were made")
                await self._close_dropdown(dropdown_container)
                return False

            # Apply the filter
            logger.info(f"Successfully selected {selections_made} experience levels")
            return await self._apply_filter(dropdown_container, selections_made)

        except Exception as e:
            logger.error(f"Failed to apply experience level filter: {e}")
            return False

    async def apply_date_posted_filter(self, date_posted: str) -> bool:
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
            logger.info(f"Applying date posted filter: {date_posted}")            # Find and click the date posted filter button
            date_button_selectors = [
                'button[id="searchFilter_timePostedRange"]',
                'button[aria-label*="Date posted filter"]',
                TIME_POSTED_FILTER_SELECTOR,
            ]

            date_button = None
            for selector in date_button_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    date_button = await self.page.query_selector(selector)
                    if date_button:
                        logger.debug(f"Found date button with selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue

            if not date_button:
                logger.warning("Could not find date posted filter button")
                return False

            # Click to open the dropdown
            await date_button.click()
            await async_random_sleep(1.0, 2.0)

            # Wait for the dropdown to appear
            dropdown_container = await self._get_dropdown_container()
            if not dropdown_container:
                logger.warning("Date posted dropdown container did not appear")
                return False

            await async_random_sleep(1.0, 1.5)

            # Select the specified date option
            if date_posted.lower() in DATE_POSTED_MAPPING:
                value = DATE_POSTED_MAPPING[date_posted.lower()]
                radio_id = f"timePostedRange-{value}"

                if await self._select_radio_button(dropdown_container, radio_id, date_posted, value):
                    logger.info(f"Selected date posted option: {date_posted}")
                    await async_random_sleep(0.5, 1.0)
                else:
                    logger.warning(f"Could not find or select radio button for date: {date_posted}")
                    return False
            else:
                logger.warning(f"Invalid date posted option: {date_posted}")
                return False

            # Apply the filter
            return await self._apply_filter(dropdown_container, 1)

        except Exception as e:
            logger.error(f"Failed to apply date posted filter: {e}")
            return False

    async def _get_dropdown_container(self) -> Optional[ElementHandle]:
        """Get the dropdown container element."""
        dropdown_selectors = [
            ".artdeco-hoverable-content--visible .reusable-search-filters-trigger-dropdown__container",
            "fieldset.reusable-search-filters-trigger-dropdown__container",
            ".artdeco-hoverable-content--visible fieldset",
        ]

        for selector in dropdown_selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=5000)
                
                # Additional wait for the content to be fully rendered
                await self.page.wait_for_selector(
                    f"{selector} input[type='checkbox'], {selector} input[type='radio']",
                    timeout=3000
                )
                
                dropdown_container = await self.page.query_selector(selector)
                if dropdown_container:
                    logger.debug(f"Dropdown container found with selector: {selector}")
                    return dropdown_container
            except PlaywrightTimeoutError:
                continue

        return None

    async def _select_checkbox(self, dropdown_container: ElementHandle, checkbox_id: str, level: str, value: str) -> bool:
        """Select a checkbox in the dropdown with multiple fallback strategies."""
        try:
            # Strategy 1: Find by exact ID
            try:
                checkbox = await dropdown_container.query_selector(f"#{checkbox_id}")
                if checkbox and await checkbox.is_visible():
                    if not await checkbox.is_checked():
                        # Try clicking the associated label first
                        try:
                            label = await dropdown_container.query_selector(f'label[for="{checkbox_id}"]')
                            if label:
                                await label.click()
                            else:
                                await checkbox.click()
                        except:
                            # Fallback to clicking checkbox directly
                            await checkbox.click()
                    return True
            except:
                pass

            # Strategy 2: Find by value attribute with various name patterns
            name_patterns = [
                'experience-level-filter-value',
                'experience',
                'experienceLevel'
            ]
            
            for name_pattern in name_patterns:
                try:
                    checkbox = await dropdown_container.query_selector(f"input[name='{name_pattern}'][value='{value}']")
                    if checkbox and await checkbox.is_visible() and not await checkbox.is_checked():
                        await checkbox.click()
                        return True
                except:
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
                        label = await dropdown_container.query_selector(f"text={display_text}")
                        if label and await label.is_visible():
                            # Find the parent label element
                            parent_label = await label.evaluate_handle("el => el.closest('label')")
                            if parent_label:
                                await parent_label.click()
                            else:
                                await label.click()
                            return True
                    except:
                        try:
                            # Try contains text match
                            label = await dropdown_container.query_selector(f"text*={display_text}")
                            if label and await label.is_visible():
                                parent_label = await label.evaluate_handle("el => el.closest('label')")
                                if parent_label:
                                    await parent_label.click()
                                else:
                                    await label.click()
                                return True
                        except:
                            continue

            # Strategy 4: Find any checkbox with similar data attributes
            try:
                checkbox = await dropdown_container.query_selector(f"input[type='checkbox'][value*='{value}']")
                if not checkbox:
                    checkbox = await dropdown_container.query_selector(f"input[type='checkbox'][id*='{value}']")
                
                if checkbox and await checkbox.is_visible() and not await checkbox.is_checked():
                    await checkbox.click()
                    return True
            except:
                pass

            logger.warning(f"Could not find any suitable checkbox for experience level: {level}")
            return False

        except Exception as e:
            logger.warning(f"Error selecting experience level {level}: {e}")
            return False

    async def _select_radio_button(self, dropdown_container: ElementHandle, radio_id: str, date_posted: str, value: str) -> bool:
        """Select a radio button in the dropdown with multiple fallback strategies."""
        try:
            # Strategy 1: Find by exact ID
            try:
                radio_button = await dropdown_container.query_selector(f"#{radio_id}")
                if radio_button and await radio_button.is_visible():
                    if not await radio_button.is_checked():
                        # Try clicking the associated label first
                        try:
                            label = await dropdown_container.query_selector(f'label[for="{radio_id}"]')
                            if label:
                                await label.click()
                            else:
                                await radio_button.click()
                        except:
                            # Fallback to clicking radio button directly
                            await radio_button.click()
                    return True
            except:
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
                    radio_button = await dropdown_container.query_selector(f"input[name='{name_pattern}'][value='{value}']")
                    if radio_button and await radio_button.is_visible() and not await radio_button.is_checked():
                        await radio_button.click()
                        return True
                except:
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
                        label = await dropdown_container.query_selector(f"text={display_text}")
                        if label and await label.is_visible():
                            parent_label = await label.evaluate_handle("el => el.closest('label')")
                            if parent_label:
                                await parent_label.click()
                            else:
                                await label.click()
                            return True
                    except:
                        try:
                            # Try contains text match
                            label = await dropdown_container.query_selector(f"text*={display_text}")
                            if label and await label.is_visible():
                                parent_label = await label.evaluate_handle("el => el.closest('label')")
                                if parent_label:
                                    await parent_label.click()
                                else:
                                    await label.click()
                                return True
                        except:
                            continue

            # Strategy 4: Find any radio button with similar data attributes
            try:
                radio_button = await dropdown_container.query_selector(f"input[type='radio'][value*='{value}']")
                if not radio_button:
                    radio_button = await dropdown_container.query_selector(f"input[type='radio'][id*='{value}']")
                
                if radio_button and await radio_button.is_visible() and not await radio_button.is_checked():
                    await radio_button.click()
                    return True
            except:
                pass

            logger.warning(f"Could not find any suitable radio button for date: {date_posted}")
            return False

        except Exception as e:
            logger.warning(f"Error selecting date posted option: {e}")
            return False

    async def _close_dropdown(self, dropdown_container: ElementHandle) -> None:
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
                    cancel_button = await dropdown_container.query_selector(selector)
                    if cancel_button and await cancel_button.is_visible() and await cancel_button.is_enabled():
                        await cancel_button.click()
                        logger.debug("Successfully closed dropdown with cancel button")
                        return
                except:
                    continue

            # Strategy 2: Click outside the dropdown to close it
            try:
                # Click on the body element to close dropdown
                await self.page.click("body", position={"x": 10, "y": 10})
                logger.debug("Closed dropdown by clicking outside")
                return
            except:
                pass

            # Strategy 3: Press ESC key
            try:
                await self.page.keyboard.press("Escape")
                logger.debug("Closed dropdown with ESC key")
            except:
                pass

        except Exception as e:
            logger.debug(f"Could not close dropdown: {e}")
            pass

    async def _apply_filter(self, dropdown_container: ElementHandle, selections_made: int) -> bool:
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
                    buttons = await dropdown_container.query_selector_all(selector)
                    for button in buttons:
                        if await button.is_visible() and await button.is_enabled():
                            # Check if button text suggests it's an apply button
                            button_text = await button.text_content()
                            if button_text and any(keyword in button_text.lower() for keyword in ['show', 'apply', 'done', 'submit']):
                                apply_button = button
                                break
                    if apply_button:
                        break
                except:
                    continue

            if apply_button:
                await apply_button.click()
                await async_random_sleep(2.0, 4.0)  # Wait for page reload
                logger.info(f"Applied filter with {selections_made} selections")
                return True
            else:
                logger.warning("Could not find apply button for filter")
                
                # Strategy 2: Try pressing Enter key as fallback
                try:
                    await self.page.keyboard.press("Enter")
                    await async_random_sleep(2.0, 4.0)
                    logger.info(f"Applied filter using Enter key with {selections_made} selections")
                    return True
                except:
                    pass
                
                return False

        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            return False
