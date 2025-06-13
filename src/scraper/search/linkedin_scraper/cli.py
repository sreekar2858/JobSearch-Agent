"""
Command-line interface for LinkedIn scraper.
"""

import argparse
import json
import os
from datetime import datetime
from typing import List, Optional

from .scraper import LinkedInScraper


def parse_experience_levels(experience_str: str) -> List[str]:
    """Parse comma-separated experience levels."""
    if not experience_str:
        return []
    return [level.strip() for level in experience_str.split(',') if level.strip()]


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description='LinkedIn Job Scraper')
    
    # Required arguments
    parser.add_argument('keywords', help='Job search keywords')
    parser.add_argument('location', help='Job search location')
    # Optional arguments
    parser.add_argument('--max-pages', type=int, default=1, help='Maximum pages to scrape (default: 1)')
    parser.add_argument('--max-jobs', type=int, help='Maximum number of jobs to extract (overrides max-pages if specified)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--browser', choices=['chrome', 'firefox'], default='chrome', help='Browser to use (default: chrome)')
    parser.add_argument('--timeout', type=int, default=20, help='Timeout in seconds (default: 20)')
    parser.add_argument('--output', help='Output file path (default: auto-generated)')
    
    # Filter arguments
    parser.add_argument('--experience-levels', type=str, help='Comma-separated experience levels (internship,entry_level,associate,mid_senior,director,executive)')
    parser.add_argument('--date-posted', choices=['any_time', 'past_month', 'past_week', 'past_24_hours'], help='Date posted filter')
    parser.add_argument('--sort-by', choices=['relevance', 'recent'], help='Sort results by')
      # Action arguments
    parser.add_argument('--links-only', action='store_true', help='Only collect job links, not detailed information')
    parser.add_argument('--job-url', help='Get details for a specific job URL')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = LinkedInScraper(
        headless=args.headless,
        timeout=args.timeout,
        browser=args.browser
    )
    
    try:
        if args.job_url:
            # Get details for a specific job
            print(f"Getting details for job: {args.job_url}")
            job_details = scraper.get_job_details(args.job_url)
            
            # Output results
            if args.output:
                output_file = args.output
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"job_details_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(job_details, f, indent=2, ensure_ascii=False)
            
            print(f"Job details saved to: {output_file}")
        else:
            # Collect job links
            experience_levels = parse_experience_levels(args.experience_levels) if args.experience_levels else None
            
            print(f"Searching for jobs: '{args.keywords}' in '{args.location}'")
            if args.max_jobs:
                print(f"Max jobs: {args.max_jobs}")
            else:
                print(f"Max pages: {args.max_pages}")
            if experience_levels:
                print(f"Experience levels: {experience_levels}")
            if args.date_posted:
                print(f"Date posted: {args.date_posted}")
            if args.sort_by:
                print(f"Sort by: {args.sort_by}")
            
            job_links = scraper.collect_job_links(
                keywords=args.keywords,
                location=args.location,
                max_pages=args.max_pages,
                experience_levels=experience_levels,
                date_posted=args.date_posted,
                sort_by=args.sort_by
            )
            
            # Limit job links if max_jobs is specified
            if args.max_jobs and args.max_jobs > 0:
                job_links = job_links[:args.max_jobs]
                print(f"Limited to {len(job_links)} jobs (max_jobs: {args.max_jobs})")
            
            print(f"Found {len(job_links)} job links")
            
            if args.links_only:
                # Only output links
                results = {"job_links": job_links, "total_count": len(job_links)}
                
                if args.output:
                    output_file = args.output
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_keywords = "".join(c for c in args.keywords if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_location = "".join(c for c in args.location if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    output_file = f"linkedin_jobs_{safe_keywords.replace(' ', '_')}_{safe_location.replace(' ', '_')}_{timestamp}.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                print(f"Job links saved to: {output_file}")
                
            else:
                # Get detailed information for each job
                detailed_jobs = []
                
                for i, job_url in enumerate(job_links, 1):
                    print(f"Getting details for job {i}/{len(job_links)}: {job_url}")
                    try:
                        job_details = scraper.get_job_details(job_url)
                        detailed_jobs.append(job_details)
                    except Exception as e:
                        print(f"Error getting details for {job_url}: {e}")
                        continue
                  # Output results
                results = {
                    "search_params": {
                        "keywords": args.keywords,
                        "location": args.location,
                        "max_pages": args.max_pages,
                        "max_jobs": args.max_jobs,
                        "experience_levels": experience_levels,
                        "date_posted": args.date_posted,
                        "sort_by": args.sort_by
                    },
                    "total_jobs_found": len(detailed_jobs),
                    "jobs": detailed_jobs,
                    "scraped_at": datetime.now().isoformat()
                }
                
                if args.output:
                    output_file = args.output
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_keywords = "".join(c for c in args.keywords if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_location = "".join(c for c in args.location if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    if not os.path.exists("output/linkedin"):
                        os.makedirs("output/linkedin", exist_ok=True)
                    output_file = f"output/linkedin/linkedin_jobs_{safe_keywords.replace(' ', '_')}_{safe_location.replace(' ', '_')}_{timestamp}.json"
                
                # Create output directory if it doesn't exist
                os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                print(f"Job details saved to: {output_file}")
                print(f"Successfully scraped {len(detailed_jobs)} jobs")
    
    finally:
        scraper.close()


if __name__ == '__main__':
    main()
