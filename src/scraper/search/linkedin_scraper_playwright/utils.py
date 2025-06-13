"""
Utility functions for LinkedIn scraper using Playwright.
"""

import asyncio
import random
import os
import logging
from datetime import datetime
from typing import List, Optional, Union
from playwright.async_api import Page, ElementHandle

logger = logging.getLogger("linkedin_scraper")


def random_sleep(min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
    """
    Sleep for a random duration to mimic human behavior.

    Args:
        min_seconds: Minimum sleep time in seconds
        max_seconds: Maximum sleep time in seconds
    """
    import time
    time.sleep(random.uniform(min_seconds, max_seconds))


async def async_random_sleep(min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
    """
    Async sleep for a random duration to mimic human behavior.

    Args:
        min_seconds: Minimum sleep time in seconds
        max_seconds: Maximum sleep time in seconds
    """
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))


async def save_screenshot(page: Page, label: str, subfolder: str = "linkedin") -> str:
    """
    Save a screenshot with timestamp and return the path.

    Args:
        page: Playwright Page instance
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
        await page.screenshot(path=screenshot_path)
        logger.info(f"Saved screenshot to {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logger.error(f"Failed to save screenshot: {e}")
        return ""


async def extract_text_by_selectors(
    page_or_element: Union[Page, ElementHandle], 
    selectors: List[str], 
    element_name: str = "element"
) -> Optional[str]:
    """
    Extract text from a page or element using multiple selectors as fallback.

    Args:
        page_or_element: Page or ElementHandle to search within
        selectors: List of CSS selectors to try
        element_name: Name for logging purposes

    Returns:
        First non-empty text found, or None if nothing found
    """
    for selector in selectors:
        try:
            elements = await page_or_element.query_selector_all(selector)
            for element in elements:
                if await element.is_visible():
                    text = await element.text_content()
                    if text and text.strip():
                        text = text.strip()
                        logger.debug(
                            f"Extracted {element_name} using selector '{selector}': {text}"
                        )
                        return text
        except Exception as e:
            logger.debug(
                f"Error with selector '{selector}' for {element_name}: {e}"
            )
            continue

    logger.debug(
        f"Could not extract {element_name} with any of the provided selectors"
    )
    return None


async def wait_for_any_selector(page: Page, selectors: List[str], timeout: int = 20000) -> Optional[str]:
    """
    Wait for any of the provided selectors to appear on the page.

    Args:
        page: Playwright Page instance
        selectors: List of CSS selectors to wait for
        timeout: Timeout in milliseconds

    Returns:
        The first selector that appeared, or None if timeout
    """
    try:
        # Create a list of promises for each selector
        promises = []
        for selector in selectors:
            promises.append(page.wait_for_selector(selector, timeout=timeout))
        
        # Wait for the first one to resolve
        done, pending = await asyncio.wait(promises, return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel pending promises
        for p in pending:
            p.cancel()
        
        # Return the selector that resolved first
        for i, promise in enumerate(promises):
            if promise in done:
                return selectors[i]
        
        return None
    except Exception as e:
        logger.debug(f"Error waiting for selectors: {e}")
        return None
