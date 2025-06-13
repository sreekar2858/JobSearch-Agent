"""
Utility functions for LinkedIn scraper.
"""

import time
import random
import os
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger("linkedin_scraper")


def random_sleep(min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
    """
    Sleep for a random duration to mimic human behavior.

    Args:
        min_seconds: Minimum sleep time in seconds
        max_seconds: Maximum sleep time in seconds
    """
    time.sleep(random.uniform(min_seconds, max_seconds))


def save_screenshot(driver, label: str, subfolder: str = "linkedin") -> str:
    """
    Save a screenshot with timestamp and return the path.

    Args:
        driver: WebDriver instance
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
        driver.save_screenshot(screenshot_path)
        logger.info(f"Saved screenshot to {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logger.error(f"Failed to save screenshot: {e}")
        return ""


def extract_text_by_selectors(element, selectors: List[str], element_name: str = "element") -> Optional[str]:
    """
    Extract text from an element using multiple selectors as fallback.

    Args:
        element: WebElement to search within (can be driver for page-level searches)
        selectors: List of CSS selectors to try
        element_name: Name for logging purposes

    Returns:
        First non-empty text found, or None if nothing found
    """
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
    
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
