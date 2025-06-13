"""
Extract job metadata from LinkedIn job detail pages.
"""

import re
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .selectors import (
    JOB_TITLE_SELECTORS, COMPANY_NAME_SELECTORS, LOCATION_SELECTORS, POSTED_DATE_SELECTORS,
    JOB_DESCRIPTION_SELECTORS, ARTICLE_SELECTORS, DESCRIPTION_CONTENT_SELECTORS,
    SEE_MORE_BUTTON_SELECTORS, COMPANY_LOGO_SELECTORS, APPLY_BUTTON_SELECTORS,
    SKILLS_SELECTORS, JOB_INSIGHTS_SELECTORS, APPLICANT_COUNT_SELECTORS,
    CONTACT_INFO_SELECTORS, COMPANY_INFO_SELECTORS, COMPANY_WEBSITE_SELECTORS,
    TERTIARY_DESCRIPTION_SELECTORS, TEXT_SPAN_SELECTORS,
    HIRING_TEAM_SECTION_SELECTORS, HIRING_MEMBER_SELECTORS, HIRING_NAME_SELECTORS,
    HIRING_TITLE_SELECTORS, RELATED_JOBS_SECTION_SELECTORS, RELATED_JOB_CARD_SELECTORS,
    RELATED_JOB_TITLE_SELECTORS, RELATED_JOB_COMPANY_SELECTORS,
    RELATED_JOB_LOCATION_SELECTORS, RELATED_JOB_DATE_SELECTORS, RELATED_JOB_INSIGHT_SELECTORS
)
from ..utils import random_sleep, extract_text_by_selectors

logger = logging.getLogger("linkedin_scraper")


class JobDetailsExtractor:
    """Extracts detailed job information from LinkedIn job pages."""
    
    def __init__(self, driver, timeout: int = 20):
        """
        Initialize job details extractor.
        
        Args:
            driver: WebDriver instance
            timeout: Timeout for element waiting
        """
        self.driver = driver
        self.timeout = timeout

    def extract_job_basic_info(self, element) -> Dict[str, str]:
        """
        Extract basic job information (title, company, location, date) from an element.

        Args:
            element: WebElement containing job information

        Returns:
            Dictionary with job basic information
        """
        job_info = {}

        # Extract job title
        title = extract_text_by_selectors(element, JOB_TITLE_SELECTORS, "job title")
        if title:
            job_info["title"] = title

        # Extract company name
        company = extract_text_by_selectors(element, COMPANY_NAME_SELECTORS, "company name")
        if company:
            job_info["company"] = company

        # Extract location
        location = extract_text_by_selectors(element, LOCATION_SELECTORS, "job location")
        if location:
            job_info["location"] = location

        # Extract posted date
        posted_date = extract_text_by_selectors(element, POSTED_DATE_SELECTORS, "posted date")
        if posted_date:
            job_info["posted_date"] = posted_date

        return job_info

    def extract_complete_job_description(self) -> str:
        """
        Extract the complete job description text content.
        Handles clicking "See more" button and captures the entire article text.

        Returns:
            Complete job description text
        """
        try:
            # Click "See more" button if present
            see_more_clicked = self.click_see_more_button()

            if see_more_clicked:
                logger.info("Description expanded, waiting for content to load")
                random_sleep(1.5, 2.5)

            description_text = "No description available"

            # First try to get the complete article element
            for selector in ARTICLE_SELECTORS:
                try:
                    article_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if article_element and article_element.is_displayed():
                        text_content = article_element.text.strip()
                        if text_content:
                            description_text = text_content
                            logger.info(f"Successfully extracted full job description ({len(text_content)} characters)")
                            break
                except (NoSuchElementException, Exception) as e:
                    logger.debug(f"Could not extract article with selector {selector}: {e}")
                    continue

            # Try specific job details selector
            if description_text == "No description available" or len(description_text) < 100:
                try:
                    job_details_element = self.driver.find_element(By.CSS_SELECTOR, "#job-details")
                    if job_details_element and job_details_element.is_displayed():
                        text_content = job_details_element.text.strip()
                        if text_content and len(text_content) > len(description_text):
                            description_text = text_content
                            logger.info(f"Successfully extracted #job-details text ({len(text_content)} characters)")
                except (NoSuchElementException, Exception) as e:
                    logger.debug(f"Could not extract #job-details element: {e}")

            # If we couldn't get the article, try other selectors for just the content
            if description_text == "No description available":
                for selector in DESCRIPTION_CONTENT_SELECTORS:
                    try:
                        content_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if content_element and content_element.is_displayed():
                            text_content = content_element.text.strip()
                            if text_content:
                                description_text = text_content
                                logger.info(f"Extracted job description using selector {selector} ({len(text_content)} characters)")
                                break
                    except (NoSuchElementException, Exception) as e:
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

    def click_see_more_button(self) -> bool:
        """
        Find and click the "See more" button if present.

        Returns:
            True if button was found and clicked, False otherwise
        """
        for selector in SEE_MORE_BUTTON_SELECTORS:
            try:
                see_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for see_more_button in see_more_buttons:
                    if (
                        see_more_button
                        and see_more_button.is_displayed()
                        and see_more_button.is_enabled()
                    ):
                        # Check if the button text contains "See more" or similar
                        button_text = see_more_button.text.lower()
                        if "see more" in button_text or "show more" in button_text:
                            logger.info("Found 'See more' button, clicking to expand description")
                            # Scroll the button into view
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                see_more_button,
                            )
                            random_sleep(1.0, 1.5)

                            # Click the button
                            try:
                                see_more_button.click()
                                logger.info("Successfully clicked 'See more' button")
                                random_sleep(2.0, 3.0)
                                return True
                            except Exception as e:
                                # If direct click fails, try JavaScript click
                                logger.debug(f"Direct click failed, trying JavaScript click: {e}")
                                self.driver.execute_script("arguments[0].click();", see_more_button)
                                logger.info("Successfully clicked 'See more' button using JavaScript")
                                random_sleep(2.0, 3.0)
                                return True
            except (NoSuchElementException, Exception) as e:
                logger.debug(f"Could not click 'See more' button with selector {selector}: {e}")
                continue

        logger.debug("No 'See more' button found or could not click it")
        return False

    def extract_job_metadata(self) -> Dict[str, Any]:
        """
        Extract specific job metadata from LinkedIn job page.

        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {}

        try:
            # Extract location and date_posted from tertiary description container
            logger.debug("Extracting location and date_posted from tertiary description container")

            tertiary_container = None
            for selector in TERTIARY_DESCRIPTION_SELECTORS:
                try:
                    tertiary_container = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if tertiary_container:
                        logger.debug(f"Found tertiary container with selector: {selector}")
                        break
                except NoSuchElementException:
                    continue

            if tertiary_container:
                spans = []
                for span_selector in TEXT_SPAN_SELECTORS:
                    try:
                        spans = tertiary_container.find_elements(By.CSS_SELECTOR, span_selector)
                        if spans:
                            logger.debug(f"Found {len(spans)} spans with selector: {span_selector}")
                            break
                    except:
                        continue

                # Extract text from valid spans (skip separators like "·")
                valid_spans = []
                for span in spans:
                    text = span.text.strip()
                    if text and text != "·" and len(text) > 1:
                        valid_spans.append(text)
                        logger.debug(f"Valid span text: '{text}'")

                # First valid span should be location
                if len(valid_spans) >= 1:
                    metadata["location"] = valid_spans[0]
                    logger.debug(f"Extracted location: {valid_spans[0]}")

                # Second valid span should be date_posted
                if len(valid_spans) >= 2:
                    for span_text in valid_spans[1:]:
                        if any(
                            indicator in span_text.lower()
                            for indicator in ["ago", "week", "day", "month", "hour", "minute", "posted"]
                        ):
                            metadata["date_posted"] = span_text
                            logger.debug(f"Extracted date_posted: {span_text}")
                            break
            else:
                logger.debug("Could not find tertiary description container")

            # Extract skills from job insight button
            logger.debug("Extracting skills from job insight button")
            for selector in SKILLS_SELECTORS:
                try:
                    skills_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if skills_button and skills_button.is_displayed():
                        skills_text = skills_button.text.strip()
                        logger.debug(f"Skills button text: '{skills_text}'")

                        if skills_text and ("Skills:" in skills_text or "skill" in skills_text.lower()):
                            # Remove "Skills:" prefix and parse
                            skills_content = skills_text.replace("Skills:", "").strip()

                            # Split by commas and clean up
                            if "," in skills_content:
                                skills_list = [skill.strip() for skill in skills_content.split(",") if skill.strip()]
                            else:
                                skills_list = skills_content.split() if skills_content else []

                            # Handle "+X more" pattern and extract actual skills
                            processed_skills = []
                            for skill in skills_list:
                                if re.search(r"\+\d+\s*(more|additional)", skill.lower()):
                                    match = re.search(r"\+(\d+)", skill)
                                    if match:
                                        metadata["additional_skills_count"] = int(match.group(1))
                                else:
                                    clean_skill = re.sub(r"[^\w\s\+#\.-]", "", skill).strip()
                                    if clean_skill and len(clean_skill) > 1:
                                        processed_skills.append(clean_skill)

                            if processed_skills:
                                metadata["skills"] = processed_skills
                                logger.debug(f"Extracted skills: {processed_skills}")
                            break
                except (NoSuchElementException, Exception) as e:
                    logger.debug(f"Skills selector '{selector}' failed: {e}")
                    continue            # Extract job insights
            logger.debug("Extracting job insights")
            try:
                job_insights = []
                for selector in JOB_INSIGHTS_SELECTORS:
                    try:
                        insight_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if insight_elements:
                            logger.debug(f"Found {len(insight_elements)} insight elements with selector: {selector}")

                            for insight_element in insight_elements:
                                try:
                                    # Get the full HTML content as a string
                                    insight_html = insight_element.get_attribute('outerHTML')
                                    # Also get the text content for fallback
                                    insight_text = insight_element.text.strip()
                                    
                                    # Create a comprehensive insight object
                                    insight_data = {
                                        "html_content": insight_html,
                                        "text_content": insight_text,
                                        "element_class": insight_element.get_attribute('class'),
                                        "element_tag": insight_element.tag_name
                                    }
                                    
                                    # Check if this insight is not already captured
                                    if insight_data not in job_insights and (insight_html or insight_text):
                                        job_insights.append(insight_data)
                                        logger.debug(f"Extracted insight data: {insight_data}")
                                        
                                except Exception as insight_error:
                                    logger.debug(f"Error processing individual insight: {insight_error}")
                                    continue
                            break
                    except:
                        continue

                if job_insights:
                    metadata["job_insights"] = job_insights
                    logger.debug(f"Extracted job insights: {len(job_insights)} insights found")
                else:
                    metadata["job_insights"] = "NA"
                    logger.debug("No job insights found")

            except Exception as e:
                metadata["job_insights"] = "NA"
                logger.debug(f"Could not extract job insights: {e}")

            # Extract Easy Apply status and apply information
            logger.debug("Extracting apply information")
            found_apply_button = False

            for selector in APPLY_BUTTON_SELECTORS:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.debug(f"Found {len(buttons)} elements with selector: {selector}")

                    for i, button in enumerate(buttons):
                        if button.is_displayed():
                            try:
                                button_text = button.text.strip()
                                aria_label = button.get_attribute("aria-label") or ""
                                button_role = button.get_attribute("role") or ""
                                href = button.get_attribute("href") or ""
                                class_name = button.get_attribute("class") or ""

                                # Check if it's an apply button
                                if ("Apply" in button_text or "Apply" in aria_label) and button_text:
                                    found_apply_button = True
                                    logger.debug(f"Apply button found - text: '{button_text}', aria-label: '{aria_label}', href: '{href}'")

                                    # Check if it's Easy Apply
                                    if "Easy Apply" in button_text or "Easy Apply" in aria_label:
                                        metadata["easy_apply"] = True
                                        metadata["apply_info"] = "Easy Apply"
                                        logger.debug("This is an Easy Apply button")
                                    else:
                                        # This is an external apply button
                                        metadata["easy_apply"] = False
                                        logger.debug("This appears to be an EXTERNAL apply button")
                                        # Try to extract the external apply URL
                                        apply_url = self.extract_external_apply_url(button)

                                        if apply_url:
                                            metadata["apply_info"] = apply_url
                                            logger.debug(f"✅ SUCCESS: Extracted URL: {apply_url}")
                                        else:
                                            metadata["apply_info"] = f"External application - {button_text}"
                                            logger.debug(f"❌ Could not extract URL, but found external apply button: {button_text}")

                                    break

                            except Exception as button_error:
                                logger.debug(f"Error examining button {i + 1}: {button_error}")

                    if found_apply_button:
                        break

                except Exception as selector_error:
                    logger.debug(f"Selector {selector} failed: {selector_error}")
                    continue

            # Set defaults if no apply button found
            if "easy_apply" not in metadata:
                metadata["easy_apply"] = False
                metadata["apply_info"] = "NA"
                logger.debug("No apply button found, set defaults")

            logger.debug(f"Final metadata extracted: {metadata}")
            return metadata
        except Exception as e:
            logger.error(f"Error extracting job metadata: {str(e)}")
            return metadata

    def extract_external_apply_url(self, apply_button) -> str:
        """
        Extract the external apply URL from a LinkedIn job apply button.

        Args:
            apply_button: The selenium WebElement of the apply button

        Returns:
            The external apply URL if found, None otherwise
        """
        try:
            # Method 1: Check for direct href first
            href = apply_button.get_attribute("href")
            if href and href.startswith("http") and "linkedin.com" not in href:
                logger.debug(f"Found direct href: {href}")
                return href

            # Method 2: Simple click test with detailed logging
            logger.debug("Attempting click-based extraction...")
            current_url = self.driver.current_url
            current_windows = set(self.driver.window_handles)

            try:
                logger.debug(f"Current URL before click: {current_url}")
                logger.debug(f"Current windows before click: {len(current_windows)}")

                # Try clicking the button
                apply_button.click()
                time.sleep(3)  # Give time for redirect

                new_url = self.driver.current_url
                new_windows = set(self.driver.window_handles)

                logger.debug(f"URL after click: {new_url}")
                logger.debug(f"Windows after click: {len(new_windows)}")

                # Check for new windows
                if len(new_windows) > len(current_windows):
                    logger.debug("New window/tab detected!")
                    new_window = list(new_windows - current_windows)[0]
                    self.driver.switch_to.window(new_window)
                    tab_url = self.driver.current_url
                    logger.debug(f"New tab URL: {tab_url}")

                    if not tab_url.startswith("https://www.linkedin.com") and tab_url.startswith("http"):
                        logger.debug(f"✅ SUCCESS (new tab): {tab_url}")
                        self.driver.close()
                        self.driver.switch_to.window(list(current_windows)[0])
                        return tab_url
                    else:
                        logger.debug("New tab but still LinkedIn or invalid URL")
                        self.driver.close()
                        self.driver.switch_to.window(list(current_windows)[0])

                # Check for same-window redirect
                elif new_url != current_url:
                    logger.debug(f"Same-window redirect detected: {new_url}")
                    if not new_url.startswith("https://www.linkedin.com") and new_url.startswith("http"):
                        logger.debug(f"✅ SUCCESS (redirect): {new_url}")
                        # Navigate back
                        self.driver.get(current_url)
                        time.sleep(2)
                        return new_url
                    else:
                        logger.debug("Redirected but still on LinkedIn")
                        self.driver.get(current_url)
                        time.sleep(2)
                else:
                    logger.debug("No redirect detected")

            except Exception as click_error:
                logger.debug(f"Click extraction failed: {click_error}")
                # Make sure we're back on the original page
                try:
                    if self.driver.current_url != current_url:
                        self.driver.get(current_url)
                        time.sleep(2)
                except:
                    pass

            # Method 3: Extract from page source as fallback
            try:
                page_source = self.driver.page_source
                patterns = [
                    rf'"applyUrl":"([^"]*)"',
                    rf'"externalApplyUrl":"([^"]*)"',
                    rf'"companyApplyUrl":"([^"]*)"',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    for match in matches:
                        if match and match.startswith("http") and "linkedin.com" not in match:
                            clean_url = match.replace("\\u0026", "&").replace("\\/", "/")
                            logger.debug(f"Found external URL from page source: {clean_url}")
                            return clean_url

            except Exception as page_extract_error:
                logger.debug(f"Page source extraction failed: {page_extract_error}")

            logger.debug("No external apply URL found using any method")
            return None

        except Exception as e:
            logger.debug(f"Error extracting external apply URL: {e}")
            return None

    def extract_company_info(self) -> str:
        """
        Extract company information excluding footer links and "Show more" buttons.

        Returns:
            Clean company information text
        """
        try:
            for selector in COMPANY_INFO_SELECTORS:
                try:
                    company_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in company_elements:
                        if element.is_displayed():
                            full_text = element.text.strip()

                            if full_text:
                                # Remove footer content that contains "Show more" links
                                lines = full_text.split("\n")
                                clean_lines = []

                                for line in lines:
                                    line = line.strip()
                                    # Skip lines that are footer links or "Show more" buttons
                                    if (
                                        line.lower() in ["show more", "see more"]
                                        or "Show more" in line
                                        or "See more" in line
                                        or line.startswith("http")
                                        or "/company/" in line
                                    ):
                                        break
                                    if line:
                                        clean_lines.append(line)

                                clean_text = "\n".join(clean_lines).strip()

                                if clean_text:
                                    logger.debug(f"Extracted company info ({len(clean_text)} characters)")
                                    return clean_text
                except (NoSuchElementException, Exception) as e:
                    logger.debug(f"Could not extract company info with selector {selector}: {e}")
                    continue

            logger.debug("Could not extract company information")
            return ""

        except Exception as e:
            logger.error(f"Error extracting company info: {str(e)}")
            return ""

    def extract_hiring_team(self) -> List[Dict[str, str]]:
        """
        Extract hiring team/contact person details from the job page.

        Returns:
            List of hiring team members with their details
        """
        try:
            hiring_team = []

            # Look for the hiring team section
            for selector in HIRING_TEAM_SECTION_SELECTORS:
                try:
                    hiring_sections = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for section in hiring_sections:
                        if not section.is_displayed():
                            continue

                        # Look for individual hiring team members
                        for member_selector in HIRING_MEMBER_SELECTORS:
                            try:
                                members = section.find_elements(By.CSS_SELECTOR, member_selector)

                                for member in members:
                                    if not member.is_displayed():
                                        continue

                                    member_info = {}

                                    # Extract name
                                    name = extract_text_by_selectors(member, HIRING_NAME_SELECTORS, "hiring member name")
                                    if name:
                                        member_info["name"] = name

                                    # Extract title/role
                                    title = extract_text_by_selectors(member, HIRING_TITLE_SELECTORS, "hiring member title")
                                    if title:
                                        member_info["title"] = title

                                    # Extract LinkedIn profile URL
                                    try:
                                        profile_link = member.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
                                        if profile_link:
                                            member_info["linkedin_url"] = profile_link.get_attribute("href")
                                    except NoSuchElementException:
                                        pass

                                    # Extract connection degree
                                    try:
                                        connection_elem = member.find_element(By.CSS_SELECTOR, ".hirer-card__connection-degree")
                                        if connection_elem and connection_elem.text.strip():
                                            member_info["connection_degree"] = connection_elem.text.strip()
                                    except NoSuchElementException:
                                        pass

                                    # Only add if we have at least a name
                                    if member_info.get("name"):
                                        hiring_team.append(member_info)

                            except Exception as member_error:
                                logger.debug(f"Error extracting hiring team member: {member_error}")
                                continue

                except Exception as section_error:
                    logger.debug(f"Error processing hiring section {selector}: {section_error}")
                    continue

            # Remove duplicates based on name
            seen_names = set()
            unique_hiring_team = []
            for member in hiring_team:
                name = member.get("name", "")
                if name and name not in seen_names:
                    seen_names.add(name)
                    unique_hiring_team.append(member)

            logger.debug(f"Extracted {len(unique_hiring_team)} hiring team members")
            return unique_hiring_team

        except Exception as e:
            logger.debug(f"Error extracting hiring team: {e}")
            return []

    def extract_related_jobs(self) -> List[Dict[str, str]]:
        """
        Extract related/similar jobs from the job page.

        Returns:
            List of related jobs with their details
        """
        try:
            related_jobs = []

            # Look for the related jobs section
            for selector in RELATED_JOBS_SECTION_SELECTORS:
                try:
                    related_sections = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for section in related_sections:
                        if not section.is_displayed():
                            continue

                        # Look for individual job cards
                        for card_selector in RELATED_JOB_CARD_SELECTORS:
                            try:
                                job_cards = section.find_elements(By.CSS_SELECTOR, card_selector)

                                for card in job_cards:
                                    if not card.is_displayed():
                                        continue

                                    job_info = {}

                                    # Extract job title
                                    title = extract_text_by_selectors(card, RELATED_JOB_TITLE_SELECTORS, "related job title")
                                    if title:
                                        job_info["title"] = title

                                    # Extract company name
                                    company = extract_text_by_selectors(card, RELATED_JOB_COMPANY_SELECTORS, "related job company")
                                    if company:
                                        job_info["company"] = company

                                    # Extract location
                                    location = extract_text_by_selectors(card, RELATED_JOB_LOCATION_SELECTORS, "related job location")
                                    if location:
                                        job_info["location"] = location

                                    # Extract job URL
                                    try:
                                        link_elem = card.find_element(By.CSS_SELECTOR, "a[href*='/jobs/']")
                                        if link_elem:
                                            href = link_elem.get_attribute("href")
                                            job_id_match = re.search(r"/jobs/.*?(\d+)", href)
                                            if job_id_match:
                                                job_id = job_id_match.group(1)
                                                job_info["url"] = f"https://www.linkedin.com/jobs/view/{job_id}"
                                            else:
                                                job_info["url"] = href
                                    except NoSuchElementException:
                                        pass

                                    # Extract posting date
                                    posted_date = extract_text_by_selectors(card, RELATED_JOB_DATE_SELECTORS, "related job date")
                                    if posted_date:
                                        job_info["posted_date"] = posted_date

                                    # Extract job insights
                                    insights = []
                                    for insight_sel in RELATED_JOB_INSIGHT_SELECTORS:
                                        try:
                                            insight_elems = card.find_elements(By.CSS_SELECTOR, insight_sel)
                                            for elem in insight_elems:
                                                if elem.is_displayed() and elem.text.strip():
                                                    insights.append(elem.text.strip())
                                        except NoSuchElementException:
                                            continue

                                    if insights:
                                        job_info["insights"] = insights

                                    # Only add if we have at least a title
                                    if job_info.get("title"):
                                        related_jobs.append(job_info)

                            except Exception as card_error:
                                logger.debug(f"Error extracting related job card: {card_error}")
                                continue

                except Exception as section_error:
                    logger.debug(f"Error processing related jobs section {selector}: {section_error}")
                    continue

            # Remove duplicates based on title and company
            seen_jobs = set()
            unique_related_jobs = []
            for job in related_jobs:
                job_key = f"{job.get('title', '')}-{job.get('company', '')}"
                if job_key and job_key not in seen_jobs:
                    seen_jobs.add(job_key)
                    unique_related_jobs.append(job)

            logger.debug(f"Extracted {len(unique_related_jobs)} related jobs")
            return unique_related_jobs

        except Exception as e:
            logger.debug(f"Error extracting related jobs: {e}")
            return []
