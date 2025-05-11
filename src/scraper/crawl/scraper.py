"""
Job posting scraper utility for extracting job details from various job platforms.

This module includes:
- HTML parsing functions for LinkedIn, Indeed, and Glassdoor
- Header rotation and proxy support to avoid IP blocks
- Job data normalization across different platforms
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import random
import time
from typing import Dict, List, Optional, Any, Union
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("job_scraper")

# --- Request Headers & User Agents ---
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 Safari/537.36',
]

def get_random_headers():
    """Generate random headers to avoid detection."""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

# --- Main Scraper Class ---
class JobScraper:
    """
    Scraper class for extracting job details from different platforms.
    Implements site-specific parsing logic and anti-detection measures.
    """
    
    def __init__(self, use_proxy: bool = False, delay_range: tuple = (1, 3)):
        self.use_proxy = use_proxy
        self.delay_range = delay_range
        self.session = requests.Session()
        logger.info("JobScraper initialized")
        
    def _get_random_delay(self) -> float:
        """Get a random delay within the specified range."""
        return random.uniform(*self.delay_range)
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make an HTTP request with anti-detection measures."""
        headers = get_random_headers()
        
        # Add a small delay to appear more human-like
        time.sleep(self._get_random_delay())
        
        try:
            logger.info(f"Requesting: {url}")
            print(f"  🌐 Fetching {url}")
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response
            else:
                logger.warning(f"Failed to fetch {url}. Status code: {response.status_code}")
                print(f"  ⚠️ Failed to access page. Status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            print(f"  ❌ Error: {str(e)}")
            return None
    
    def _detect_platform(self, url: str) -> str:
        """Detect which job platform the URL belongs to."""
        url_lower = url.lower()
        
        if "linkedin.com" in url_lower:
            return "linkedin"
        elif "indeed.com" in url_lower:
            return "indeed"
        elif "glassdoor.com" in url_lower:
            return "glassdoor"
        else:
            return "unknown"
    
    def scrape_job_posting(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Main entry point for scraping a job posting URL.
        Delegates to platform-specific parsers.
        """
        platform = self._detect_platform(url)
        print(f"  📊 Detected platform: {platform}")
        
        if platform == "unknown":
            logger.warning(f"Unknown job platform for URL: {url}")
            print("  ⚠️ Unknown job platform, attempting generic extraction")
            return self._parse_generic_job_page(url)
            
        response = self._make_request(url)
        if not response:
            return None
            
        if platform == "linkedin":
            return self._parse_linkedin_job(response)
        elif platform == "indeed":
            return self._parse_indeed_job(response)
        elif platform == "glassdoor":
            return self._parse_glassdoor_job(response)
        else:
            return self._parse_generic_job_page(response)
    
    def _parse_linkedin_job(self, response: requests.Response) -> Dict[str, Any]:
        """Parse LinkedIn job posting page."""
        print("  🔍 Parsing LinkedIn job posting...")
        soup = BeautifulSoup(response.text, 'html.parser')
        job_data = {}
        
        # Basic job information
        try:
            job_data["job_title"] = (
                soup.find("h1", class_="top-card-layout__title") or
                soup.find("h2", class_="t-24") or 
                soup.find("h1", class_="job-title")
            )
            if job_data["job_title"]:
                job_data["job_title"] = job_data["job_title"].get_text().strip()
            
            company_name = (
                soup.find("a", class_="topcard__org-name-link") or
                soup.find("span", class_="topcard__flavor") or
                soup.find("a", class_="company-name")
            )
            if company_name:
                job_data["company_name"] = company_name.get_text().strip()
            
            # Job description
            job_description = (
                soup.find("div", class_="show-more-less-html__markup") or
                soup.find("div", class_="description__text") or
                soup.find("div", id="job-details")
            )
            if job_description:
                job_data["job_description"] = job_description.get_text().strip()
            
            # Location
            location = (
                soup.find("span", class_="topcard__flavor--bullet") or
                soup.find("span", class_="job-location")
            )
            if location:
                job_data["job_location"] = location.get_text().strip()
                
            # Additional details
            job_data["source_site"] = "LinkedIn"
            job_data["job_url"] = response.url
            
        except Exception as e:
            logger.error(f"Error parsing LinkedIn job: {str(e)}")
            print(f"  ❌ Error parsing job details: {str(e)}")
        
        return self._normalize_job_data(job_data)
        
    def _parse_indeed_job(self, response: requests.Response) -> Dict[str, Any]:
        """Parse Indeed job posting page."""
        print("  🔍 Parsing Indeed job posting...")
        soup = BeautifulSoup(response.text, 'html.parser')
        job_data = {}
        
        try:
            # Basic job information
            job_title = (
                soup.find("h1", class_="jobsearch-JobInfoHeader-title") or
                soup.find("h1", attrs={"data-testid": "jobTitle"})
            )
            if job_title:
                job_data["job_title"] = job_title.get_text().strip()
                
            company_name = (
                soup.find("div", class_="jobsearch-InlineCompanyRating") or
                soup.find("div", attrs={"data-testid": "inlineHeader-companyName"})
            )
            if company_name:
                job_data["company_name"] = company_name.get_text().strip().split('\n')[0]
                
            # Job description
            job_description = (
                soup.find("div", id="jobDescriptionText") or
                soup.find("div", attrs={"data-testid": "jobDescriptionText"})
            )
            if job_description:
                job_data["job_description"] = job_description.get_text().strip()
                
            # Location
            location = (
                soup.find("div", class_="jobsearch-JobInfoHeader-subtitle") or
                soup.find("div", attrs={"data-testid": "job-location"})
            )
            if location:
                location_text = location.get_text().strip()
                job_data["job_location"] = location_text
                
            # Additional details
            job_data["source_site"] = "Indeed"
            job_data["job_url"] = response.url
            
        except Exception as e:
            logger.error(f"Error parsing Indeed job: {str(e)}")
            print(f"  ❌ Error parsing job details: {str(e)}")
            
        return self._normalize_job_data(job_data)
        
    def _parse_glassdoor_job(self, response: requests.Response) -> Dict[str, Any]:
        """Parse Glassdoor job posting page."""
        print("  🔍 Parsing Glassdoor job posting...")
        soup = BeautifulSoup(response.text, 'html.parser')
        job_data = {}
        
        try:
            # Basic job information
            job_title = soup.find("div", class_="job-title")
            if job_title:
                job_data["job_title"] = job_title.get_text().strip()
                
            company_name = soup.find("div", class_="employer-name")
            if company_name:
                job_data["company_name"] = company_name.get_text().strip()
                
            # Job description
            job_description = soup.find("div", class_="jobDescriptionContent")
            if job_description:
                job_data["job_description"] = job_description.get_text().strip()
                
            # Location
            location = soup.find("div", class_="location")
            if location:
                job_data["job_location"] = location.get_text().strip()
                
            # Additional details
            salary = soup.find("div", class_="salary")
            if salary:
                job_data["salary_info"] = salary.get_text().strip()
                
            job_data["source_site"] = "Glassdoor"
            job_data["job_url"] = response.url
            
        except Exception as e:
            logger.error(f"Error parsing Glassdoor job: {str(e)}")
            print(f"  ❌ Error parsing job details: {str(e)}")
            
        return self._normalize_job_data(job_data)
    
    def _parse_generic_job_page(self, response_or_url) -> Dict[str, Any]:
        """Parse a generic job posting page when site is unknown."""
        print("  🔍 Using generic job posting parser...")
        
        if isinstance(response_or_url, str):
            response = self._make_request(response_or_url)
            if not response:
                return {}
        else:
            response = response_or_url
            
        soup = BeautifulSoup(response.text, 'html.parser')
        job_data = {}
        
        # Try to extract job title from common HTML patterns
        job_title_candidates = [
            soup.find("h1"),  # Most common for job titles
            soup.find("title"),  # Page title often contains job title
        ]
        for candidate in job_title_candidates:
            if candidate and candidate.get_text().strip():
                job_data["job_title"] = candidate.get_text().strip()
                break
                
        # Try to find company name
        # Company names often appear near the job title or in meta tags
        meta_company = soup.find("meta", property="og:site_name")
        if meta_company:
            job_data["company_name"] = meta_company["content"]
            
        # Try to extract job description from common containers
        description_candidates = [
            soup.find("div", class_=lambda c: c and "description" in c.lower()),
            soup.find("div", class_=lambda c: c and "job-details" in c.lower()),
            soup.find("div", id=lambda i: i and "job-description" in i.lower()),
            soup.find("section", class_=lambda c: c and "description" in c.lower()),
        ]
        for candidate in description_candidates:
            if candidate and candidate.get_text().strip():
                job_data["job_description"] = candidate.get_text().strip()
                break
                
        # Extract from structured data if available (JobPosting schema)
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and "@type" in data and data["@type"] == "JobPosting":
                    if "title" in data and not job_data.get("job_title"):
                        job_data["job_title"] = data["title"]
                    if "hiringOrganization" in data and not job_data.get("company_name"):
                        if isinstance(data["hiringOrganization"], dict) and "name" in data["hiringOrganization"]:
                            job_data["company_name"] = data["hiringOrganization"]["name"]
                    if "description" in data and not job_data.get("job_description"):
                        job_data["job_description"] = data["description"]
                    if "jobLocation" in data:
                        if isinstance(data["jobLocation"], dict) and "address" in data["jobLocation"]:
                            addr = data["jobLocation"]["address"]
                            if isinstance(addr, dict):
                                location_parts = []
                                for field in ["addressLocality", "addressRegion", "addressCountry"]:
                                    if field in addr:
                                        location_parts.append(addr[field])
                                if location_parts:
                                    job_data["job_location"] = ", ".join(location_parts)
                    break
            except:
                continue
                
        job_data["source_site"] = "Unknown"
        job_data["job_url"] = response.url
        
        return self._normalize_job_data(job_data)
    
    def _normalize_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize job data to have consistent fields across different sources."""
        normalized = {
            "job_title": job_data.get("job_title", ""),
            "company_name": job_data.get("company_name", ""),
            "job_description": job_data.get("job_description", ""),
            "job_location": job_data.get("job_location", ""),
            "posting_date": job_data.get("posting_date", ""),
            "job_type": job_data.get("job_type", ""),
            "experience_level": job_data.get("experience_level", ""),
            "skills_required": job_data.get("skills_required", ""),
            "contact_person": job_data.get("contact_person", ""),
            "contact_email_or_linkedin": job_data.get("contact_email_or_linkedin", ""),
            "salary_info": job_data.get("salary_info", ""),
            "language_requirements": job_data.get("language_requirements", ""),
            "keywords": job_data.get("keywords", ""),
            "company_website": job_data.get("company_website", ""),
            "job_url": job_data.get("job_url", ""),
            "source_site": job_data.get("source_site", "Unknown")
        }
        
        # Extract additional information from job description if possible
        desc = normalized["job_description"]
        if desc:
            # Try to extract job type
            if not normalized["job_type"]:
                job_types = ["full-time", "part-time", "contract", "permanent", "temporary", "internship"]
                for jt in job_types:
                    if jt in desc.lower():
                        normalized["job_type"] = jt.title()
                        break
            
            # Try to extract experience level
            if not normalized["experience_level"]:
                exp_patterns = [
                    r'(\d+)[\+]?\s+years?\s+(?:of\s+)?experience',
                    r'experience\s*:\s*(\d+)[\+]?\s+years?',
                    r'minimum\s+(?:of\s+)?(\d+)[\+]?\s+years?\s+(?:of\s+)?experience'
                ]
                for pattern in exp_patterns:
                    match = re.search(pattern, desc.lower())
                    if match:
                        normalized["experience_level"] = f"{match.group(1)}+ years"
                        break
            
            # Try to extract skills required
            if not normalized["skills_required"]:
                # Look for skills sections
                skills_sections = [
                    r'skills\s*(?:and\s+qualifications)?:(.*?)(?:\n\n|\n[A-Z])',
                    r'requirements:(.*?)(?:\n\n|\n[A-Z])',
                    r'qualifications:(.*?)(?:\n\n|\n[A-Z])'
                ]
                for pattern in skills_sections:
                    match = re.search(pattern, desc.lower(), re.DOTALL)
                    if match:
                        skills_text = match.group(1).strip()
                        # Extract bullet points or comma-separated lists
                        skills = re.findall(r'[\•\-\*]\s*([^\n\•\-\*]+)', skills_text)
                        if not skills:
                            skills = [s.strip() for s in skills_text.split(',') if s.strip()]
                        if skills:
                            normalized["skills_required"] = ", ".join(skills)
                            break
        
        return normalized
    
    def batch_process_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of URLs and extract job data."""
        results = []
        
        for i, url in enumerate(urls):
            print(f"Processing URL {i+1}/{len(urls)}: {url}")
            job_data = self.scrape_job_posting(url)
            if job_data:
                results.append(job_data)
                print(f"  ✅ Successfully extracted job: {job_data.get('job_title', 'Unknown')} at {job_data.get('company_name', 'Unknown')}")
            else:
                print(f"  ❌ Failed to extract job data from {url}")
            
            # Add a delay between requests to avoid rate limiting
            if i < len(urls) - 1:  # Don't delay after the last URL
                delay = self._get_random_delay() * 2  # Slightly longer delay between different jobs
                print(f"  ⏱️ Waiting {delay:.1f}s before next request...")
                time.sleep(delay)
                
        print(f"📊 Processed {len(results)}/{len(urls)} jobs successfully")
        return results


# --- Helper Functions ---

def extract_job_links_from_google_results(search_results: List[Dict[str, Any]]) -> List[str]:
    """
    Extract job posting URLs from Google Search results.
    Filters for LinkedIn, Indeed, and Glassdoor job links.
    """
    print("🔗 Extracting job links from search results...")
    job_urls = []
    
    for result in search_results:
        url = result.get("link", "")
        # Filter for job posting URLs
        if any(site in url for site in ["linkedin.com/jobs", "indeed.com/job", "glassdoor.com/job"]):
            if url not in job_urls:  # Avoid duplicates
                job_urls.append(url)
                print(f"  ✓ Found job URL: {url}")
    
    print(f"  📊 Total job links found: {len(job_urls)}")
    return job_urls