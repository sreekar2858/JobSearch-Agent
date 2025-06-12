#!/usr/bin/env python
"""
LinkedIn Job Extractor - A simple and efficient tool to extract complete job details from LinkedIn

This script:
1. Searches LinkedIn for jobs matching keywords and location
2. Extracts ALL jobs from the search results by scrolling the left sidebar (not just the initial 7 loaded jobs)
3. Gets COMPLETE job details for each listing including:
   - Job title, company name, location
   - Full job description, qualifications, requirements
   - Posted date, job type, seniority level
   - Contact info when available, company details
   - Enhanced metadata: location, date_posted, skills, apply information
4. Saves the results to a JSON file with timestamp

USAGE:
    python extract_linkedin_jobs.py "Python Developer" "Berlin" --pages 2 --headless
    python extract_linkedin_jobs.py "Data Scientist" "New York" --jobs 10 --headless
    python extract_linkedin_jobs.py "Backend Engineer" "Remote" --experience-levels entry_level mid_senior --date-posted past_week

Options:
    --pages N    : Maximum number of search result pages to process
    --jobs N     : Maximum number of jobs to extract (takes priority over --pages)
    --headless   : Run browser in headless mode
    --browser    : Choose browser (chrome/firefox)
    --experience-levels : Filter by experience levels (internship, entry_level, associate, mid_senior, director, executive)
    --date-posted : Filter by date posted (any_time, past_month, past_week, past_24_hours)

Note: LinkedIn login is REQUIRED and automatically handled. Configure LINKEDIN_USERNAME 
and LINKEDIN_PASSWORD in your .env file.

Author: Sreekar Reddy
"""

import argparse
import json
import os
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("linkedin_extractor")

def extract_jobs(keywords: str, location: str, max_pages: int = 1, max_jobs: int = None, headless: bool = False, browser: str = "chrome", experience_levels: List[str] = None, date_posted: str = None) -> List[Dict[str, Any]]:
    """Extract complete job details from LinkedIn search results
    
    Note: LinkedIn login is automatically required and handled by the scraper.
    Ensure LINKEDIN_USERNAME and LINKEDIN_PASSWORD are configured in your .env file.
    """
    try:
        # Import the scraper classes
        from src.scraper.search.linkedin_scraper import LinkedInScraper
        
        # Initialize the LinkedIn scraper
        logger.info(f"Initializing LinkedIn scraper (headless: {headless}, browser: {browser})")
        
        try:
            scraper = LinkedInScraper(headless=headless)
        except Exception as e:
            logger.warning(f"Error initializing Chrome: {str(e)}")
            logger.info("Falling back to Firefox...")
            
            # Try to use Firefox instead
            try:
                # We need to monkey patch the scraper to use Firefox
                from selenium import webdriver
                from selenium.webdriver.firefox.service import Service
                from selenium.webdriver.firefox.options import Options
                from webdriver_manager.firefox import GeckoDriverManager
                
                # Create a custom scraper instance
                scraper = LinkedInScraper(headless=headless)
                
                # Replace the setup_driver method
                def setup_firefox_driver():
                    options = Options()
                    if headless:
                        options.add_argument("-headless")
                    
                    options.add_argument("--disable-notifications")
                    options.add_argument("--disable-popup-blocking")
                    options.add_argument("--start-maximized")
                    
                    # Initialize the Firefox driver
                    service = Service(GeckoDriverManager().install())
                    driver = webdriver.Firefox(service=service, options=options)
                    driver.set_window_size(1920, 1080)
                    return driver
                
                # Replace the driver
                scraper.driver = setup_firefox_driver()
                logger.info("Successfully initialized Firefox driver")
                
            except Exception as firefox_error:
                logger.error(f"Failed to initialize Firefox as well: {str(firefox_error)}")
                raise Exception("Could not initialize any browser. Make sure either Chrome or Firefox is installed.")
          # Create output directory for detailed results
        output_dir = os.path.join("output", "linkedin")
        os.makedirs(output_dir, exist_ok=True)
          # Step 1: Collect all job links from the search results pages
        logger.info(f"Collecting job links for '{keywords}' in '{location}' (max pages: {max_pages})")
        job_links = scraper.collect_job_links(
            keywords=keywords,
            location=location,
            max_pages=max_pages,
            experience_levels=experience_levels,
            date_posted=date_posted
        )
        
        # Limit job links if max_jobs is specified
        if max_jobs and max_jobs > 0:
            job_links = job_links[:max_jobs]
            logger.info(f"Limited to {len(job_links)} jobs (max_jobs: {max_jobs})")
        else:
            logger.info(f"Found {len(job_links)} job links. Now extracting details...")

        # Step 2: Visit each job link and extract complete details
        jobs = []
        total_to_process = len(job_links)
        
        for idx, url in enumerate(job_links, 1):
            logger.info(f"[{idx}/{total_to_process}] Extracting details for: {url}")
            try:
                details = scraper.get_job_details(url)
                details["url"] = url
                jobs.append(details)
                
                # Early exit if we've reached max_jobs (in case of processing errors)
                if max_jobs and len(jobs) >= max_jobs:
                    logger.info(f"Reached maximum jobs limit ({max_jobs}), stopping extraction")
                    break
                    
            except Exception as e:
                logger.warning(f"Failed to extract details for {url}: {e}")
                continue

        # Close the scraper
        scraper.close()

        # Generate a descriptive filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin_jobs_{keywords.replace(' ', '_')}_{location.replace(' ', '_')}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save results to JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Extracted {len(jobs)} jobs. Results saved to {filepath}")
        return jobs
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

def main():
    """Parse command line arguments and run the job extractor"""
    parser = argparse.ArgumentParser(description="Extract complete job details from LinkedIn search results")
    parser.add_argument("keywords", help="Job search keywords")
    parser.add_argument("location", help="Job search location")
    parser.add_argument("--pages", type=int, default=1, help="Maximum number of pages to scrape (default: 1)")
    parser.add_argument("--jobs", type=int, help="Maximum number of jobs to extract (overrides pages if specified)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--browser", choices=["chrome", "firefox"], default="chrome", help="Browser to use (default: chrome)")
    
    # Filter options
    parser.add_argument("--experience-levels", nargs="+", 
                       choices=["internship", "entry_level", "associate", "mid_senior", "director", "executive"],
                       help="Filter by experience levels (can specify multiple)")
    parser.add_argument("--date-posted", choices=["any_time", "past_month", "past_week", "past_24_hours"],
                       help="Filter by date posted")
    
    args = parser.parse_args()
    
    try:
        # Determine what to display for job limits
        job_limit_display = f"Max jobs: {args.jobs}" if args.jobs else f"Max pages: {args.pages}"
        
        print(f"\n🔍 Searching LinkedIn for: {args.keywords} in {args.location}")
        print(f"📄 {job_limit_display} | Headless mode: {'✅' if args.headless else '❌'} | Browser: {args.browser}")
        
        # Show a helpful message about the priority of jobs vs pages
        if args.jobs:
            print(f"🎯 Limiting to maximum {args.jobs} jobs (will stop when limit is reached regardless of pages)")
        
        print()  # Empty line for spacing
        
        jobs = extract_jobs(
            keywords=args.keywords,
            location=args.location,
            max_pages=args.pages,
            max_jobs=args.jobs,
            headless=args.headless,
            browser=args.browser,
            experience_levels=args.experience_levels,
            date_posted=args.date_posted
        )
        
        print(f"\n✅ Successfully extracted {len(jobs)} LinkedIn jobs!")
        print(f"💾 Results saved to: output/linkedin_jobs_{args.keywords.replace(' ', '_')}_{args.location.replace(' ', '_')}*.json\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
