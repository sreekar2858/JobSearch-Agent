"""
Extract job metadata from LinkedIn job detail pages using Playwright.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from playwright.async_api import Page, ElementHandle, TimeoutError as PlaywrightTimeoutError

from .selectors import (
    JOB_TITLE_SELECTORS, COMPANY_NAME_SELECTORS, LOCATION_SELECTORS, POSTED_DATE_SELECTORS,
    JOB_DESCRIPTION_SELECTORS, ARTICLE_SELECTORS, DESCRIPTION_CONTENT_SELECTORS,
    SEE_MORE_BUTTON_SELECTORS, COMPANY_LOGO_SELECTORS, APPLY_BUTTON_SELECTORS,
    SKILLS_SELECTORS, JOB_INSIGHTS_SELECTORS, APPLICANT_COUNT_SELECTORS,
    CONTACT_INFO_SELECTORS, COMPANY_INFO_SELECTORS, COMPANY_WEBSITE_SELECTORS,
    TERTIARY_DESCRIPTION_SELECTORS, TEXT_SPAN_SELECTORS,    HIRING_TEAM_SECTION_SELECTORS, HIRING_MEMBER_SELECTORS, HIRING_NAME_SELECTORS,
    HIRING_TITLE_SELECTORS, HIRING_CONNECTION_SELECTORS, HIRING_PROFILE_LINK_SELECTORS,RELATED_JOBS_SECTION_SELECTORS, RELATED_JOB_CARD_SELECTORS,
    RELATED_JOB_TITLE_SELECTORS, RELATED_JOB_COMPANY_SELECTORS,
    RELATED_JOB_LOCATION_SELECTORS, RELATED_JOB_DATE_SELECTORS, RELATED_JOB_INSIGHT_SELECTORS
)
from ..utils import async_random_sleep, extract_text_by_selectors

logger = logging.getLogger("linkedin_scraper")


class JobDetailsExtractor:
    """Extracts detailed job information from LinkedIn job pages using Playwright."""
    
    def __init__(self, page: Page, timeout: int = 20000):
        """
        Initialize job details extractor.
        
        Args:
            page: Playwright Page instance
            timeout: Timeout for element waiting in milliseconds
        """
        self.page = page
        self.timeout = timeout

    async def extract_job_basic_info(self, page_or_element) -> Dict[str, str]:
        """
        Extract basic job information (title, company, location, date) from a page or element.

        Args:
            page_or_element: Page or ElementHandle containing job information

        Returns:
            Dictionary with job basic information
        """
        job_info = {}

        # Extract job title
        title = await extract_text_by_selectors(page_or_element, JOB_TITLE_SELECTORS, "job title")
        if title:
            job_info["title"] = title

        # Extract company name
        company = await extract_text_by_selectors(page_or_element, COMPANY_NAME_SELECTORS, "company name")
        if company:
            job_info["company"] = company        # Extract location with priority for first span in subtitle grouping
        location = await self._extract_location_priority(page_or_element)
        if location:
            job_info["location"] = location

        # Extract posted date
        posted_date = await extract_text_by_selectors(page_or_element, POSTED_DATE_SELECTORS, "posted date")
        if posted_date:
            job_info["posted_date"] = posted_date

        return job_info

    async def extract_complete_job_description(self) -> str:
        """
        Extract the complete job description text content.
        Handles clicking "See more" button and captures the entire article text.

        Returns:
            Complete job description text
        """
        try:
            # Click "See more" button if present
            see_more_clicked = await self.click_see_more_button()

            if see_more_clicked:
                logger.info("Description expanded, waiting for content to load")
                await async_random_sleep(1.5, 2.5)

            description_text = "No description available"

            # First try to get the complete article element
            for selector in ARTICLE_SELECTORS:
                try:
                    article_element = await self.page.query_selector(selector)
                    if article_element and await article_element.is_visible():
                        text_content = await article_element.text_content()
                        if text_content and text_content.strip():
                            description_text = text_content.strip()
                            logger.info(f"Successfully extracted full job description ({len(text_content)} characters)")
                            break
                except Exception as e:
                    logger.debug(f"Could not extract article with selector {selector}: {e}")
                    continue

            # Try specific job details selector
            if description_text == "No description available" or len(description_text) < 100:
                try:
                    job_details_element = await self.page.query_selector("#job-details")
                    if job_details_element and await job_details_element.is_visible():
                        text_content = await job_details_element.text_content()
                        if text_content and text_content.strip() and len(text_content.strip()) > len(description_text):
                            description_text = text_content.strip()
                            logger.info(f"Successfully extracted #job-details text ({len(text_content)} characters)")
                except Exception as e:
                    logger.debug(f"Could not extract #job-details element: {e}")

            # If we couldn't get the article, try other selectors for just the content
            if description_text == "No description available":
                for selector in DESCRIPTION_CONTENT_SELECTORS:
                    try:
                        content_element = await self.page.query_selector(selector)
                        if content_element and await content_element.is_visible():
                            text_content = await content_element.text_content()
                            if text_content and text_content.strip():
                                description_text = text_content.strip()
                                logger.info(f"Extracted job description using selector {selector} ({len(text_content)} characters)")
                                break
                    except Exception as e:
                        logger.debug(f"Error extracting content with selector {selector}: {e}")
                        continue

            # Log the result
            if see_more_clicked:
                logger.info(f"Extracted expanded job description ({len(description_text)} characters)")
            else:
                logger.info(f"Extracted job description without expansion ({len(description_text)} characters)")

            return description_text

        except Exception as e:
            logger.error(f"Error extracting complete job description: {str(e)}")
            return "Error extracting description"

    async def click_see_more_button(self) -> bool:
        """
        Find and click the "See more" button if present.

        Returns:
            True if button was found and clicked, False otherwise
        """
        for selector in SEE_MORE_BUTTON_SELECTORS:
            try:
                see_more_buttons = await self.page.query_selector_all(selector)
                for see_more_button in see_more_buttons:
                    if (
                        see_more_button
                        and await see_more_button.is_visible()
                        and await see_more_button.is_enabled()
                    ):
                        # Check if the button text contains "See more" or similar
                        button_text = await see_more_button.text_content()
                        if button_text:
                            button_text = button_text.lower()
                            if "see more" in button_text or "show more" in button_text:
                                logger.info("Found 'See more' button, clicking to expand description")
                                # Scroll the button into view
                                await see_more_button.scroll_into_view_if_needed()
                                await async_random_sleep(1.0, 1.5)

                                # Click the button
                                try:
                                    await see_more_button.click()
                                    logger.info("Successfully clicked 'See more' button")
                                    await async_random_sleep(2.0, 3.0)
                                    return True
                                except Exception as e:
                                    # If direct click fails, try JavaScript click
                                    logger.debug(f"Direct click failed, trying JavaScript click: {e}")
                                    await see_more_button.evaluate("el => el.click()")
                                    logger.info("Successfully clicked 'See more' button using JavaScript")
                                    await async_random_sleep(2.0, 3.0)
                                    return True
            except Exception as e:
                logger.debug(f"Could not click 'See more' button with selector {selector}: {e}")
                continue

        logger.debug("No 'See more' button found or could not click it")
        return False

    async def extract_job_metadata(self) -> Dict[str, Any]:
        """
        Extract additional job metadata like experience level, employment type, etc.

        Returns:
            Dictionary containing job metadata
        """
        metadata = {}

        try:
            # Extract from tertiary description containers
            for selector in TERTIARY_DESCRIPTION_SELECTORS:
                try:
                    tertiary_container = await self.page.query_selector(selector)
                    if tertiary_container and await tertiary_container.is_visible():
                        text_spans = await tertiary_container.query_selector_all("span")
                        for span in text_spans:
                            span_text = await span.text_content()
                            if span_text and span_text.strip():
                                span_text = span_text.strip()
                                
                                # Detect different types of metadata
                                if any(keyword in span_text.lower() for keyword in ["full-time", "part-time", "contract", "temporary", "internship"]):
                                    metadata["employment_type"] = span_text
                                elif any(keyword in span_text.lower() for keyword in ["entry", "senior", "director", "executive", "associate", "mid"]):
                                    metadata["experience_level"] = span_text
                                elif any(keyword in span_text.lower() for keyword in ["remote", "hybrid", "on-site"]):
                                    metadata["work_type"] = span_text
                                elif re.search(r'\d+.*employees?', span_text.lower()):
                                    metadata["company_size"] = span_text
                                elif any(keyword in span_text.lower() for keyword in ["industry", "sector"]):
                                    metadata["industry"] = span_text

                        # Also look for specific class-based elements
                        text_elements = await tertiary_container.query_selector_all(".tvm__text")
                        for element in text_elements:
                            element_text = await element.text_content()
                            if element_text and element_text.strip():
                                element_text = element_text.strip()
                                if element_text not in metadata.values():
                                    if "employment_type" not in metadata and any(keyword in element_text.lower() for keyword in ["full-time", "part-time", "contract"]):
                                        metadata["employment_type"] = element_text
                                    elif "experience_level" not in metadata and any(keyword in element_text.lower() for keyword in ["entry", "senior", "director"]):
                                        metadata["experience_level"] = element_text

                        break
                except Exception as e:
                    logger.debug(f"Error extracting from tertiary container {selector}: {e}")
                    continue

            # Extract job insights if available
            job_insights = await self._extract_job_insights_enhanced()
            if job_insights:
                metadata["job_insights"] = job_insights

        except Exception as e:
            logger.error(f"Error extracting job metadata: {e}")

        return metadata

    async def extract_external_apply_url(self, apply_button: ElementHandle) -> str:
        """
        Extract external application URL from apply button.
        This method replicates the exact logic from the original Selenium scraper.

        Args:
            apply_button: Apply button ElementHandle

        Returns:
            External application URL or empty string
        """
        try:
            # Method 1: Check for direct href first
            href = await apply_button.get_attribute("href")
            if href and href.startswith("http") and "linkedin.com" not in href:
                logger.debug(f"Found direct href: {href}")
                return href

            # Method 2: Click-based extraction (main strategy from Selenium version)
            logger.debug("Attempting click-based extraction...")
            current_url = self.page.url
            
            # Get current pages/contexts
            current_pages = self.page.context.pages
            current_page_count = len(current_pages)
            
            try:
                logger.debug(f"Current URL before click: {current_url}")
                logger.debug(f"Current pages before click: {current_page_count}")

                # Click the apply button
                await apply_button.click(timeout=5000)
                await async_random_sleep(3.0, 4.0)  # Give time for redirect
                
                new_url = self.page.url
                new_pages = self.page.context.pages
                new_page_count = len(new_pages)
                
                logger.debug(f"URL after click: {new_url}")
                logger.debug(f"Pages after click: {new_page_count}")

                # Check for new pages/tabs
                if new_page_count > current_page_count:
                    logger.debug("New page/tab detected!")
                    # Get the new page (last one in the list)
                    new_page = new_pages[-1]
                    await async_random_sleep(1.0, 2.0)  # Wait for page to load
                    
                    tab_url = new_page.url
                    logger.debug(f"New tab URL: {tab_url}")

                    if not tab_url.startswith("https://www.linkedin.com") and tab_url.startswith("http"):
                        logger.debug(f"✅ SUCCESS (new tab): {tab_url}")
                        await new_page.close()
                        return tab_url
                    else:
                        logger.debug("New tab but still LinkedIn or invalid URL")
                        await new_page.close()

                # Check for same-page redirect
                elif new_url != current_url:
                    logger.debug(f"Same-page redirect detected: {new_url}")
                    if not new_url.startswith("https://www.linkedin.com") and new_url.startswith("http"):
                        logger.debug(f"✅ SUCCESS (redirect): {new_url}")
                        # Navigate back to original job page
                        await self.page.goto(current_url, wait_until='domcontentloaded')
                        await async_random_sleep(1.0, 2.0)
                        return new_url
                    else:
                        logger.debug("Redirected but still on LinkedIn")
                        await self.page.goto(current_url, wait_until='domcontentloaded')
                        await async_random_sleep(1.0, 2.0)
                else:
                    logger.debug("No redirect detected")

            except Exception as click_error:
                logger.debug(f"Click extraction failed: {click_error}")
                # Make sure we're back on the original page
                try:
                    if self.page.url != current_url:
                        await self.page.goto(current_url, wait_until='domcontentloaded')
                        await async_random_sleep(1.0, 2.0)
                except Exception:
                    pass

            # Method 3: Extract from page source as fallback
            try:
                page_content = await self.page.content()
                import re

                patterns = [
                    rf'"applyUrl":"([^"]*)"',
                    rf'"externalApplyUrl":"([^"]*)"',
                    rf'"companyApplyUrl":"([^"]*)"',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, page_content, re.IGNORECASE)
                    for match in matches:
                        if (
                            match
                            and match.startswith("http")
                            and "linkedin.com" not in match
                        ):
                            clean_url = match.replace("\\u0026", "&").replace("\\/", "/")
                            logger.debug(f"Found external URL from page source: {clean_url}")
                            return clean_url

            except Exception as page_extract_error:
                logger.debug(f"Page source extraction failed: {page_extract_error}")

            logger.debug("No external apply URL found using any method")
            return ""

        except Exception as e:
            logger.debug(f"Error extracting external apply URL: {e}")
            return ""

    async def extract_company_info(self) -> str:
        """
        Extract company information from the job page.

        Returns:
            Company information text
        """
        try:
            for selector in COMPANY_INFO_SELECTORS:
                try:
                    company_element = await self.page.query_selector(selector)
                    if company_element and await company_element.is_visible():
                        company_text = await company_element.text_content()
                        if company_text and company_text.strip():
                            return company_text.strip()
                except Exception as e:
                    logger.debug(f"Error extracting company info with selector {selector}: {e}")
                    continue

            return "No company information available"

        except Exception as e:
            logger.error(f"Error extracting company info: {e}")
            return "Error extracting company information"

    async def extract_hiring_team(self) -> List[Dict[str, str]]:
        """
        Extract hiring team information from the job page.

        Returns:
            List of dictionaries containing hiring team member information
        """
        hiring_team = []

        try:
            for section_selector in HIRING_TEAM_SECTION_SELECTORS:
                try:
                    hiring_section = await self.page.query_selector(section_selector)
                    if not hiring_section or not await hiring_section.is_visible():
                        continue

                    # Look for individual team members
                    for member_selector in HIRING_MEMBER_SELECTORS:
                        try:
                            members = await hiring_section.query_selector_all(member_selector)
                            for member in members:
                                if await member.is_visible():
                                    member_info = {}

                                    # Extract name
                                    name = await extract_text_by_selectors(member, HIRING_NAME_SELECTORS, "hiring member name")
                                    if name:
                                        member_info["name"] = name

                                    # Extract title
                                    title = await extract_text_by_selectors(member, HIRING_TITLE_SELECTORS, "hiring member title")
                                    if title:
                                        member_info["title"] = title                                    # Extract LinkedIn profile URL
                                    try:
                                        profile_link = await member.query_selector(HIRING_PROFILE_LINK_SELECTORS[0])
                                        if profile_link:
                                            href = await profile_link.get_attribute("href")
                                            if href:
                                                member_info["linkedin_url"] = href
                                    except Exception:
                                        pass

                                    # Extract connection degree
                                    try:
                                        connection_elem = await member.query_selector(HIRING_CONNECTION_SELECTORS[0])
                                        if connection_elem and await connection_elem.is_visible():
                                            connection_text = await connection_elem.text_content()
                                            if connection_text and connection_text.strip():
                                                member_info["connection_degree"] = connection_text.strip()
                                    except Exception:
                                        pass

                                    # Only add if we have at least a name
                                    if member_info.get("name"):
                                        hiring_team.append(member_info)

                        except Exception as e:
                            logger.debug(f"Error extracting hiring team member with selector {member_selector}: {e}")
                            continue

                    if hiring_team:
                        break

                except Exception as e:
                    logger.debug(f"Error extracting hiring team section with selector {section_selector}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting hiring team: {e}")

        # Remove duplicates based on name (same as original Selenium version)
        seen_names = set()
        unique_hiring_team = []
        for member in hiring_team:
            name = member.get("name", "")
            if name and name not in seen_names:
                seen_names.add(name)
                unique_hiring_team.append(member)

        return unique_hiring_team

    async def extract_related_jobs(self) -> List[Dict[str, str]]:
        """
        Extract related jobs information from the job page.

        Returns:
            List of dictionaries containing related job information
        """
        related_jobs = []

        try:
            for section_selector in RELATED_JOBS_SECTION_SELECTORS:
                try:
                    related_section = await self.page.query_selector(section_selector)
                    if not related_section or not await related_section.is_visible():
                        continue

                    # Look for individual job cards
                    for card_selector in RELATED_JOB_CARD_SELECTORS:
                        try:
                            job_cards = await related_section.query_selector_all(card_selector)
                            for card in job_cards:
                                if await card.is_visible():
                                    job_info = {}

                                    # Extract title
                                    title = await extract_text_by_selectors(card, RELATED_JOB_TITLE_SELECTORS, "related job title")
                                    if title:
                                        job_info["title"] = title

                                    # Extract company
                                    company = await extract_text_by_selectors(card, RELATED_JOB_COMPANY_SELECTORS, "related job company")
                                    if company:
                                        job_info["company"] = company

                                    # Extract location
                                    location = await extract_text_by_selectors(card, RELATED_JOB_LOCATION_SELECTORS, "related job location")
                                    if location:
                                        job_info["location"] = location

                                    # Extract date
                                    date = await extract_text_by_selectors(card, RELATED_JOB_DATE_SELECTORS, "related job date")
                                    if date:
                                        job_info["date"] = date

                                    # Extract insights
                                    insights = await extract_text_by_selectors(card, RELATED_JOB_INSIGHT_SELECTORS, "related job insights")
                                    if insights:
                                        job_info["insights"] = insights

                                    if job_info:
                                        related_jobs.append(job_info)

                        except Exception as e:
                            logger.debug(f"Error extracting related job card with selector {card_selector}: {e}")
                            continue

                    if related_jobs:
                        break

                except Exception as e:
                    logger.debug(f"Error extracting related jobs section with selector {section_selector}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting related jobs: {e}")

        return related_jobs

    async def _extract_location_priority(self, page_or_element) -> Optional[str]:
        """
        Extract location with priority for first span in tertiary description container.
        
        Args:
            page_or_element: Page or ElementHandle to search within
            
        Returns:
            Location text or None if not found
        """
        # First try to get the first span from tertiary description container
        try:
            tertiary_container = await page_or_element.query_selector(".job-details-jobs-unified-top-card__tertiary-description-container")
            if tertiary_container:
                # Look for the first tvm__text--low-emphasis span which should contain location
                first_span = await tertiary_container.query_selector(".tvm__text--low-emphasis:first-child")
                if first_span and await first_span.is_visible():
                    text = await first_span.text_content()
                    if text and text.strip():
                        location = text.strip()
                        logger.debug(f"Extracted location from tertiary container: {location}")
                        return location
                
                # Alternative: try the first span child
                spans = await tertiary_container.query_selector_all("span .tvm__text--low-emphasis")
                for span in spans[:1]:  # Only check the first one
                    if await span.is_visible():
                        text = await span.text_content()
                        if text and text.strip():
                            location = text.strip()
                            logger.debug(f"Extracted location from first span: {location}")
                            return location
        except Exception as e:
            logger.debug(f"Error extracting location from tertiary container: {e}")
        
        # Try subtitle grouping as backup
        try:
            subtitle_grouping = await page_or_element.query_selector(".jobs-unified-top-card__subtitle-secondary-grouping")
            if subtitle_grouping:
                spans = await subtitle_grouping.query_selector_all("span")
                for span in spans:
                    if await span.is_visible():
                        text = await span.text_content()
                        if text and text.strip():
                            location = text.strip()
                            logger.debug(f"Extracted location from subtitle grouping: {location}")
                            return location
        except Exception as e:
            logger.debug(f"Error extracting location from subtitle grouping: {e}")
        
        # Fallback to regular selectors
        return await extract_text_by_selectors(page_or_element, LOCATION_SELECTORS, "job location")

    async def _extract_job_insights_enhanced(self) -> List[str]:
        """
        Extract job insights with enhanced support for work type preferences.
        
        Returns:
            List of job insights including work type preferences
        """
        insight_texts = []
        
        # First, try to extract work type preferences from job-details-fit-level-preferences
        try:
            preferences_container = await self.page.query_selector(".job-details-fit-level-preferences")
            if preferences_container:
                # Look for strong tags within tvm__text--low-emphasis spans
                strong_elements = await preferences_container.query_selector_all(".tvm__text--low-emphasis strong")
                for strong in strong_elements:
                    if await strong.is_visible():
                        text = await strong.text_content()
                        if text and text.strip():
                            cleaned_text = text.strip()
                            if cleaned_text not in insight_texts:
                                insight_texts.append(cleaned_text)
                                logger.debug(f"Extracted work type preference: {cleaned_text}")
                
                # Also try buttons in preferences container as fallback
                if not insight_texts:
                    buttons = await preferences_container.query_selector_all("button")
                    for button in buttons:
                        if await button.is_visible():
                            text = await button.text_content()
                            if text and text.strip():
                                cleaned_text = text.strip()
                                if cleaned_text not in insight_texts:
                                    insight_texts.append(cleaned_text)
        except Exception as e:
            logger.debug(f"Error extracting work type preferences: {e}")
        
        # Then try other job insights selectors
        for selector in JOB_INSIGHTS_SELECTORS[2:]:  # Skip the first two as they're handled above
            try:
                insights = await self.page.query_selector_all(selector)
                for insight in insights:
                    if await insight.is_visible():
                        insight_text = await insight.text_content()
                        if insight_text and insight_text.strip():
                            cleaned_text = insight_text.strip()
                            if cleaned_text not in insight_texts:
                                insight_texts.append(cleaned_text)
            except Exception as e:
                logger.debug(f"Error extracting job insights with selector {selector}: {e}")
                continue
        
        if insight_texts:
            logger.debug(f"Extracted job insights: {insight_texts}")
        
        return insight_texts
