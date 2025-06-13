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
    # Search for jobs by keywords and location
    python extract_linkedin_jobs.py "Python Developer" "Berlin" --pages 2 --headless
    python extract_linkedin_jobs.py "Data Scientist" "New York" --jobs 10 --headless --sort-by recent
    python extract_linkedin_jobs.py "Backend Engineer" "Remote" --experience-levels entry_level mid_senior --date-posted past_week --sort-by relevance
    python extract_linkedin_jobs.py "Software Engineer" "San Francisco" --no-extract-details  # Just collect job links (faster)

    # Extract details from a single job URL
    python extract_linkedin_jobs.py --job-url "https://www.linkedin.com/jobs/view/4248346302"
    python extract_linkedin_jobs.py --job-url "https://www.linkedin.com/jobs/view/4248346302" --headless

Search Mode Options:
    --pages N    : Maximum number of search result pages to process
    --jobs N     : Maximum number of jobs to extract (takes priority over --pages)
    --headless   : Run browser in headless mode
    --browser    : Choose browser (chrome/firefox)
    --sort-by    : Sort results by 'relevance' or 'recent' (default: LinkedIn default sorting)
    --experience-levels : Filter by experience levels (internship, entry_level, associate, mid_senior, director, executive)
    --date-posted : Filter by date posted (any_time, past_month, past_week, past_24_hours)
    --extract-details / --no-extract-details : Extract full job details vs just collect job links (default: extract details)

Note: LinkedIn login is REQUIRED and automatically handled. Configure LINKEDIN_USERNAME
and LINKEDIN_PASSWORD in your .env file.

Author: Sreekar Reddy
"""

import argparse
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("linkedin_extractor")


def extract_jobs(
    keywords: str,
    location: str,
    max_pages: int = 1,
    max_jobs: int = None,
    headless: bool = False,
    browser: str = "chrome",
    experience_levels: List[str] = None,
    date_posted: str = None,
    sort_by: str = None,
    extract_details: bool = True,
) -> List[Dict[str, Any]]:
    """Extract complete job details from LinkedIn search results

    Args:
        keywords: Job search keywords
        location: Job search location
        max_pages: Maximum number of pages to scrape
        max_jobs: Maximum number of jobs to extract (overrides pages if specified)
        headless: Run browser in headless mode
        browser: Browser to use (chrome/firefox)
        experience_levels: List of experience levels to filter by
        date_posted: Date posted filter option
        sort_by: Sort results by relevance or recent
        extract_details: Whether to extract full job details or just collect job links

    Note: LinkedIn login is automatically required and handled by the scraper.
    Ensure LINKEDIN_USERNAME and LINKEDIN_PASSWORD are configured in your .env file.
    """
    try:
        # Import the scraper classes
        from src.scraper.search.linkedin_scraper import LinkedInScraper

        # Initialize the LinkedIn scraper
        logger.info(
            f"Initializing LinkedIn scraper (headless: {headless}, browser: {browser})"
        )
        try:
            scraper = LinkedInScraper(headless=headless, browser=browser)
        except Exception as e:
            logger.warning(f"Error initializing {browser}: {str(e)}")
            if browser.lower() == "chrome":
                logger.info("Falling back to Firefox...")
                try:
                    scraper = LinkedInScraper(headless=headless, browser="firefox")
                except Exception as firefox_e:
                    logger.error(f"Firefox also failed: {firefox_e}")
                    raise e
            else:
                raise e

        # Create output directory for detailed results
        output_dir = os.path.join("output", "linkedin")
        os.makedirs(output_dir, exist_ok=True)
        # Step 1: Collect all job links from the search results pages
        logger.info(
            f"Collecting job links for '{keywords}' in '{location}' (max pages: {max_pages})"
        )
        job_links = scraper.collect_job_links(
            keywords=keywords,
            location=location,
            max_pages=max_pages,
            experience_levels=experience_levels,
            date_posted=date_posted,
            sort_by=sort_by,
        )

        # Limit job links if max_jobs is specified
        if max_jobs and max_jobs > 0:
            job_links = job_links[:max_jobs]
            logger.info(
                f"Limited to {len(job_links)} jobs (max_jobs: {max_jobs})"
            )  # Step 2: Extract details or return basic job info based on extract_details flag
        jobs = []

        if extract_details:
            logger.info(f"Found {len(job_links)} job links. Now extracting details...")
            total_to_process = len(job_links)

            for idx, url in enumerate(job_links, 1):
                logger.info(f"[{idx}/{total_to_process}] Extracting details for: {url}")
                try:
                    details = scraper.get_job_details(url)
                    details["url"] = url
                    jobs.append(details)

                    # Early exit if we've reached max_jobs (in case of processing errors)
                    if max_jobs and len(jobs) >= max_jobs:
                        logger.info(
                            f"Reached maximum jobs limit ({max_jobs}), stopping extraction"
                        )
                        break

                except Exception as e:
                    logger.warning(f"Failed to extract details for {url}: {e}")
                    continue
        else:
            logger.info(
                f"Found {len(job_links)} job links. Returning basic job info only..."
            )
            for url in job_links:
                jobs.append({"url": url})

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


def extract_single_job(
    job_url: str, headless: bool = False, browser: str = "chrome"
) -> Dict[str, Any]:
    """Extract complete details from a single LinkedIn job URL

    Args:
        job_url: LinkedIn job URL (e.g., https://www.linkedin.com/jobs/view/4248346302)
        headless: Run browser in headless mode
        browser: Browser to use (chrome/firefox)

    Returns:
        Dictionary containing job details

    Note: LinkedIn login is automatically required and handled by the scraper.
    Ensure LINKEDIN_USERNAME and LINKEDIN_PASSWORD are configured in your .env file.
    """
    try:
        # Validate URL format
        if not job_url.startswith("https://www.linkedin.com/jobs/view/"):
            raise ValueError(
                "Invalid LinkedIn job URL. Expected format: https://www.linkedin.com/jobs/view/[job_id]"
            )

        # Import the scraper classes
        from src.scraper.search.linkedin_scraper import LinkedInScraper

        # Initialize the LinkedIn scraper
        logger.info(
            f"Initializing LinkedIn scraper (headless: {headless}, browser: {browser})"
        )

        try:
            scraper = LinkedInScraper(headless=headless, browser=browser)
        except Exception as e:
            logger.warning(f"Error initializing {browser}: {str(e)}")
            if browser.lower() == "chrome":
                logger.info("Falling back to Firefox...")
                try:
                    scraper = LinkedInScraper(headless=headless, browser="firefox")
                except Exception as firefox_e:
                    logger.error(f"Firefox also failed: {firefox_e}")
                    raise e
            else:
                raise e

        # Create output directory for detailed results
        output_dir = os.path.join("output", "linkedin")
        os.makedirs(output_dir, exist_ok=True)

        # Extract job details
        logger.info(f"Extracting details for: {job_url}")
        job_details = scraper.get_job_details(job_url)
        job_details["url"] = job_url

        # Close the scraper
        scraper.close()

        # Generate a descriptive filename with job ID
        job_id = job_url.split("/jobs/view/")[1].split("/")[0].split("?")[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin_job_{job_id}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        # Save results to JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(job_details, f, indent=2, ensure_ascii=False)

        logger.info(f"Job details extracted successfully. Results saved to {filepath}")
        return job_details

    except Exception as e:
        logger.error(f"Error extracting job details: {str(e)}")
        raise


def main():
    """Parse command line arguments and run the job extractor"""
    parser = argparse.ArgumentParser(
        description="Extract complete job details from LinkedIn search results or a single job URL"
    )

    # Job URL mode (mutually exclusive with search mode)
    parser.add_argument(
        "--job-url",
        type=str,
        help="Extract details from a single LinkedIn job URL (e.g., https://www.linkedin.com/jobs/view/4248346302)",
    )

    # Search mode arguments (required if --job-url is not provided)
    parser.add_argument(
        "keywords", nargs="?", help="Job search keywords (required for search mode)"
    )
    parser.add_argument(
        "location", nargs="?", help="Job search location (required for search mode)"
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Maximum number of pages to scrape (default: 1)",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        help="Maximum number of jobs to extract (overrides pages if specified)",
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run browser in headless mode"
    )
    parser.add_argument(
        "--browser",
        choices=["chrome", "firefox"],
        default="chrome",
        help="Browser to use (default: chrome)",
    )
    # Filter options
    parser.add_argument(
        "--experience-levels",
        nargs="+",
        choices=[
            "internship",
            "entry_level",
            "associate",
            "mid_senior",
            "director",
            "executive",
        ],
        help="Filter by experience levels (can specify multiple)",
    )
    parser.add_argument(
        "--date-posted",
        choices=["any_time", "past_month", "past_week", "past_24_hours"],
        help="Filter by date posted",
    )
    parser.add_argument(
        "--sort-by",
        choices=["relevance", "recent"],
        help="Sort results by relevance or recent (default: LinkedIn default sorting)",
    )
    parser.add_argument(
        "--extract-details",
        action="store_true",
        default=True,
        help="Extract full job details from each posting (default: True). Use --no-extract-details for just links.",
    )
    parser.add_argument(
        "--no-extract-details",
        dest="extract_details",
        action="store_false",
        help="Only collect job links without extracting full details (faster)",
    )

    args = parser.parse_args()

    try:
        # Handle single job URL mode
        if args.job_url:
            print(f"\n🔍 Extracting details from LinkedIn job: {args.job_url}")
            print(
                f"🛠️ Headless mode: {'✅' if args.headless else '❌'} | Browser: {args.browser}"
            )
            print()  # Empty line for spacing

            job_details = extract_single_job(
                job_url=args.job_url, headless=args.headless, browser=args.browser
            )

            print(f"\n✅ Successfully extracted job details!")
            print(f"💾 Results saved to: output/linkedin/linkedin_job_*.json\n")
            return

        # Handle search mode
        if not args.keywords or not args.location:
            parser.error("keywords and location are required for search mode")

        # Determine what to display for job limits
        job_limit_display = (
            f"Max jobs: {args.jobs}" if args.jobs else f"Max pages: {args.pages}"
        )

        print(f"\n🔍 Searching LinkedIn for: {args.keywords} in {args.location}")
        print(
            f"📄 {job_limit_display} | Headless mode: {'✅' if args.headless else '❌'} | Browser: {args.browser}"
        )
        # Show a helpful message about the priority of jobs vs pages
        if args.jobs:
            print(
                f"🎯 Limiting to maximum {args.jobs} jobs (will stop when limit is reached regardless of pages)"
            )

        print()  # Empty line for spacing

        jobs = extract_jobs(
            keywords=args.keywords,
            location=args.location,
            max_pages=args.pages,
            max_jobs=args.jobs,
            headless=args.headless,
            browser=args.browser,
            experience_levels=args.experience_levels,
            date_posted=args.date_posted,
            sort_by=args.sort_by,
            extract_details=args.extract_details,
        )

        print(f"\n✅ Successfully extracted {len(jobs)} LinkedIn jobs!")
        print(
            f"💾 Results saved to: output/linkedin_jobs_{args.keywords.replace(' ', '_')}_{args.location.replace(' ', '_')}*.json\n"
        )

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
