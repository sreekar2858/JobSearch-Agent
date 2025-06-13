"""
Extract job URLs from LinkedIn search results pages using Playwright.
"""

import logging
from typing import Dict, Any, List

from playwright.async_api import Page, ElementHandle

from .selectors import JOB_LINK_SELECTORS, PAGINATION_STATE_SELECTORS, NEXT_BUTTON_SELECTORS, PAGE_BUTTON_SELECTORS
from ..utils import async_random_sleep

logger = logging.getLogger("linkedin_scraper")


class JobLinksExtractor:
    """Extracts job links from LinkedIn search results using Playwright."""
    
    def __init__(self, page: Page):
        """
        Initialize job links extractor.
        
        Args:
            page: Playwright Page instance
        """
        self.page = page

    async def extract_job_links_from_cards(self, job_cards: List[ElementHandle], current_page: int) -> set:
        """
        Extract job links from a list of job card elements.

        Args:
            job_cards: List of job card ElementHandles
            current_page: Current page number for logging

        Returns:
            Set of job URLs
        """
        job_links = set()
        logger.info(f"Processing {len(job_cards)} job cards on page {current_page}")

        processed = 0
        for card in job_cards:
            processed += 1
            if processed % 5 == 0:
                logger.info(f"Processed {processed}/{len(job_cards)} job cards")

            try:
                # Make sure the card is in view to load its details
                try:
                    await card.scroll_into_view_if_needed()
                    await async_random_sleep(0.5, 1.0)
                except Exception as e:
                    logger.debug(f"Error scrolling to job card {processed}: {e}")

                # Check if this card has data-occludable-job-id attribute
                job_id = None
                try:
                    job_id = await card.get_attribute("data-occludable-job-id")
                    if job_id:
                        logger.debug(f"Found card with job ID: {job_id}")
                    else:
                        logger.debug(f"Card {processed} has no data-occludable-job-id attribute")
                except Exception as e:
                    logger.debug(f"Error getting job ID from card {processed}: {e}")

                # Check if card has data-job-id attribute (alternative format)
                if not job_id:
                    try:
                        job_container = await card.query_selector("[data-job-id]")
                        if job_container:
                            job_id = await job_container.get_attribute("data-job-id")
                            if job_id:
                                logger.debug(f"Found card with job-id: {job_id}")
                    except:
                        pass

                # Try to find the job link inside this card
                link_elements = []
                try:
                    # Try each selector in the list
                    for selector in JOB_LINK_SELECTORS:
                        elements = await card.query_selector_all(selector)
                        link_elements.extend(elements)

                    # If we can't find with specific selectors, get all links
                    if not link_elements:
                        link_elements = await card.query_selector_all("a")
                except Exception as e:
                    logger.debug(f"Error finding links in card {processed}: {e}")

                # Process all found links to get a job URL
                url = None
                logger.debug(f"Card {processed}: Found {len(link_elements)} link elements")
                for i, link_element in enumerate(link_elements):
                    try:
                        href = await link_element.get_attribute("href")
                        logger.debug(f"  Link {i}: {href}")
                        if href and "/jobs/view/" in href:
                            url = href.split("?")[0]  # Remove query parameters
                            # Convert relative URLs to absolute URLs
                            if url.startswith("/"):
                                url = f"https://www.linkedin.com{url}"
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
                    try:
                        card_html = await card.inner_html()
                        if len(card_html.strip()) < 50:
                            logger.debug(f"Card {processed} appears to be a placeholder (short content)")
                        else:
                            logger.warning(
                                f"Could not extract job link from card {processed} (has content but no extractable URL)"
                            )
                            # Log some of the card's structure for debugging
                            try:
                                card_class = await card.get_attribute("class") or "no-class"
                                logger.debug(f"  Card class: {card_class}")
                                all_links = await card.query_selector_all("a")
                                logger.debug(f"  Total links in card: {len(all_links)}")
                                for j, link in enumerate(all_links[:3]):
                                    try:
                                        href = await link.get_attribute("href") or "no-href"
                                        logger.debug(f"    Link {j}: {href}")
                                    except:
                                        pass
                            except Exception as debug_e:
                                logger.debug(f"  Error debugging card {processed}: {debug_e}")
                    except Exception as e:
                        logger.debug(f"Error checking card HTML content: {e}")

            except Exception as e:
                logger.debug(f"Error processing job card {processed}/{len(job_cards)}: {e}")
                continue

        return job_links

    async def get_pagination_info(self) -> Dict[str, Any]:
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
            for selector in PAGINATION_STATE_SELECTORS:
                try:
                    page_state_element = await self.page.query_selector(selector)
                    if page_state_element and await page_state_element.is_visible():
                        page_state = await page_state_element.text_content()
                        if page_state:
                            page_state = page_state.strip()
                            pagination_info["page_state"] = page_state

                            # Parse "Page X of Y" format
                            if "Page" in page_state and "of" in page_state:
                                parts = page_state.split()
                                try:
                                    current_page = int(parts[1])
                                    total_pages = int(parts[3])
                                    pagination_info["current_page"] = current_page
                                    pagination_info["total_pages"] = total_pages
                                    logger.debug(f"Extracted pagination: Page {current_page} of {total_pages}")
                                except (IndexError, ValueError) as e:
                                    logger.debug(f"Could not parse pagination numbers: {e}")
                            break
                except Exception:
                    continue

            # Check if "Next" button is available and enabled
            for selector in NEXT_BUTTON_SELECTORS:
                try:
                    next_button = await self.page.query_selector(selector)
                    if next_button and await next_button.is_visible() and await next_button.is_enabled():
                        class_attr = await next_button.get_attribute("class") or ""
                        if "disabled" not in class_attr:
                            pagination_info["has_next"] = True
                            logger.debug("Next button is available and enabled")
                            break
                except Exception:
                    continue

            # Get list of available page numbers
            page_buttons = []
            for selector in PAGE_BUTTON_SELECTORS:
                try:
                    buttons = await self.page.query_selector_all(selector)
                    for button in buttons:
                        if await button.is_visible():
                            button_text = await button.text_content()
                            if button_text and button_text.strip().isdigit():
                                page_buttons.append(int(button_text.strip()))
                    if page_buttons:
                        break
                except Exception as e:
                    logger.debug(f"Could not extract page buttons: {e}")
                    continue

            if page_buttons:
                pagination_info["available_pages"] = sorted(page_buttons)
                logger.debug(f"Available page buttons: {pagination_info['available_pages']}")

        except Exception as e:
            logger.debug(f"Error extracting pagination info: {e}")

        return pagination_info

    async def go_to_next_page(self) -> bool:
        """
        Navigate to the next page of job results.

        Returns:
            bool: True if successfully navigated to next page, False otherwise
        """
        try:
            next_clicked = False
            for selector in NEXT_BUTTON_SELECTORS:
                try:
                    next_buttons = await self.page.query_selector_all(selector)
                    for next_button in next_buttons:
                        if await next_button.is_visible() and await next_button.is_enabled():
                            class_attr = await next_button.get_attribute("class") or ""
                            if "disabled" not in class_attr:
                                # Scroll to make the button visible
                                await next_button.scroll_into_view_if_needed()
                                await async_random_sleep(1.0, 2.0)

                                await next_button.click()
                                logger.info("Clicked next page button")
                                next_clicked = True
                                await async_random_sleep(3.0, 5.0)

                                # Verify we're on the next page
                                new_pagination_info = await self.get_pagination_info()
                                logger.info(f"After navigation: {new_pagination_info['page_state']}")
                                break

                    if next_clicked:
                        break
                except Exception as e:
                    logger.warning(f"Could not click next button with selector {selector}: {str(e)}")
                    continue

            if not next_clicked:
                logger.info("No more pages available or could not find next button")
                return False

        except Exception as e:
            logger.error(f"Error trying to navigate to next page: {str(e)}")
            return False

        return True
