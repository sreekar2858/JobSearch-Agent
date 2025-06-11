"""
Job search manager for local scraping implementations.

This module provides:
- A unified interface for searching jobs across different platforms
- Selenium-based scraping with Firefox (expandable to other browsers)
- Search result pagination and collection
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Import platform-specific scrapers
from .linkedin_scraper import LinkedInScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("job_search_manager")


class JobSearchManager:
    """
    Manager for searching jobs across different platforms using local scrapers.
    """
    
    def __init__(
        self, headless: bool = False, output_dir: str = "jobs", use_login: bool = False, timeout: int = 20
    ):
        """
        Initialize the job search manager.

        Args:
            headless: Whether to run the browsers in headless mode
            output_dir: Directory to save job data
            use_login: Whether to use login credentials from .env file
            timeout: Timeout in seconds for page loading
        """
        self.headless = headless
        self.output_dir = output_dir
        self.use_login = use_login
        self.timeout = timeout
        self.scrapers = {}
        self._initialize_scrapers()
        
    def _initialize_scrapers(self) -> None:
        """Initialize scrapers for different platforms."""
        # Initialize LinkedIn scraper
        self.scrapers["linkedin"] = LinkedInScraper(
            headless=self.headless, use_login=self.use_login, timeout=self.timeout
        )

        # Future: Add more platform scrapers here
        # self.scrapers["indeed"] = IndeedScraper(headless=self.headless)
        # self.scrapers["glassdoor"] = GlassdoorScraper(headless=self.headless)

        logger.info(
            f"Initialized scrapers for platforms: {', '.join(self.scrapers.keys())}"
        )

    def search_jobs(
        self,
        keywords: str,
        location: str,
        platforms: List[str] = ["linkedin"],
        max_pages: int = 10,
        save_results: bool = True,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for jobs across specified platforms.

        Args:
            keywords: Job search keywords
            location: Location for job search
            platforms: List of platforms to search (default: linkedin)
            max_pages: Maximum number of pages to scrape per platform
            save_results: Whether to save results to file

        Returns:
            Dictionary of jobs by platform
        """
        results = {}

        for platform in platforms:
            if platform.lower() not in self.scrapers:
                logger.warning(f"No scraper available for platform: {platform}")
                continue            
            logger.info(
                f"Searching for jobs on {platform.capitalize()} with keywords: '{keywords}' in location: '{location}'"
            )
            
            try:
                scraper = self.scrapers[platform.lower()]
                
                # Use the detailed version for LinkedIn that extracts all job details
                if platform.lower() == "linkedin":
                    platform_jobs = scraper.search_jobs_with_details(
                        keywords=keywords, location=location, max_pages=max_pages
                    )
                else:
                    # Use the standard search for other platforms
                    platform_jobs = scraper.search_jobs(
                        keywords=keywords, location=location, max_pages=max_pages
                    )
                
                results[platform] = platform_jobs

                logger.info(
                    f"Found {len(platform_jobs)} jobs on {platform.capitalize()}"
                )

                # Save platform-specific results if requested
                if save_results and platform_jobs:
                    self._save_results(platform_jobs, platform)

            except Exception as e:
                logger.error(f"Error searching {platform}: {str(e)}")
                results[platform] = []

        # Save combined results if requested
        if save_results and any(len(jobs) > 0 for jobs in results.values()):
            self._save_combined_results(results)

        return results

    def get_job_details(
        self, job_url: str, platform: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific job posting.

        Args:
            job_url: URL of the job posting
            platform: Platform the job is from (will be auto-detected if not specified)

        Returns:
            Dictionary containing detailed job information or None if failed
        """
        # Auto-detect platform from URL if not specified
        if not platform:
            if "linkedin.com" in job_url:
                platform = "linkedin"
            elif "indeed.com" in job_url:
                platform = "indeed"
            elif "glassdoor.com" in job_url:
                platform = "glassdoor"
            else:
                logger.error(f"Could not determine platform for URL: {job_url}")
                return None

        # Check if we have a scraper for the platform
        if platform.lower() not in self.scrapers:
            logger.error(f"No scraper available for platform: {platform}")
            return None

        # Get job details using the appropriate scraper
        try:
            scraper = self.scrapers[platform.lower()]
            job_details = scraper.get_job_details(job_url)
            return job_details
        except Exception as e:
            logger.error(
                f"Error getting job details from {platform} for URL {job_url}: {str(e)}"
            )
            return None

    def _save_results(self, jobs: List[Dict[str, Any]], platform: str) -> str:
        """
        Save platform-specific job data to a JSON file.

        Args:
            jobs: List of job dictionaries
            platform: Platform name

        Returns:
            Path to the saved file
        """
        # Create platform-specific directory
        platform_dir = os.path.join(self.output_dir, platform.lower())
        os.makedirs(platform_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{platform.lower()}_job_postings_{timestamp}.json"
        filepath = os.path.join(platform_dir, filename)

        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(jobs)} {platform} job postings to {filepath}")
        return filepath

    def _save_combined_results(self, results: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Save combined job data from all platforms to a JSON file.

        Args:
            results: Dictionary of jobs by platform

        Returns:
            Path to the saved file
        """
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"job_postings_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)

        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Count total jobs
        total_jobs = sum(len(jobs) for jobs in results.values())
        logger.info(
            f"Saved {total_jobs} job postings from {len(results)} platforms to {filepath}"
        )
        return filepath

    def close(self) -> None:
        """Close all WebDriver sessions."""
        for platform, scraper in self.scrapers.items():
            try:
                scraper.close()
                logger.info(f"Closed {platform} scraper")
            except Exception as e:
                logger.error(f"Error closing {platform} scraper: {str(e)}")

        logger.info("All scrapers closed")
