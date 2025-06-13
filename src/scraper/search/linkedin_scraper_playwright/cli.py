"""
Command-line interface for LinkedIn scraper using Playwright.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import List, Optional

# Handle both direct execution and module import
try:
    from .scraper import LinkedInScraper, LinkedInScraperSync
except ImportError:
    # Direct execution - add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    from scraper import LinkedInScraper, LinkedInScraperSync


def parse_experience_levels(experience_str: str) -> List[str]:
    """Parse comma-separated experience levels."""
    if not experience_str:
        return []
    return [level.strip() for level in experience_str.split(',') if level.strip()]


async def async_main():
    """Async main CLI function."""
    parser = argparse.ArgumentParser(description='LinkedIn Job Scraper (Playwright)')
    
    # Required arguments (made optional when using --job-url)
    parser.add_argument('keywords', nargs='?', help='Job search keywords')
    parser.add_argument('location', nargs='?', help='Job search location')
    
    # Optional arguments
    parser.add_argument('--max-pages', type=int, default=1, help='Maximum pages to scrape (default: 1)')
    parser.add_argument('--max-jobs', type=int, help='Maximum number of jobs to extract (overrides max-pages if specified)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium', help='Browser to use (default: chromium)')
    parser.add_argument('--timeout', type=int, default=20, help='Timeout in seconds (default: 20)')
    parser.add_argument('--output', help='Output file path (default: auto-generated)')
    
    # Filter arguments
    parser.add_argument('--experience-levels', type=str, help='Comma-separated experience levels (internship,entry_level,associate,mid_senior,director,executive)')
    parser.add_argument('--date-posted', choices=['any_time', 'past_month', 'past_week', 'past_24_hours'], help='Date posted filter')
    parser.add_argument('--sort-by', choices=['relevance', 'recent'], help='Sort results by')
    
    # Action arguments
    parser.add_argument('--links-only', action='store_true', help='Only collect job links, not detailed information')
    parser.add_argument('--job-url', help='Get details for a specific job URL')
    parser.add_argument('--sync', action='store_true', help='Use synchronous mode (backwards compatibility)')
    
    # Proxy and anonymization arguments
    parser.add_argument('--proxy', help='Proxy server (e.g., http://proxy:port or socks5://proxy:port)')
    parser.add_argument('--no-anonymize', action='store_true', help='Disable anonymization features (user agent randomization, WebGL blocking, etc.)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.job_url:
        # When using --job-url, keywords and location are not required
        if not args.keywords:
            args.keywords = "N/A"
        if not args.location:
            args.location = "N/A"
    else:
        # When not using --job-url, keywords and location are required
        if not args.keywords or not args.location:
            parser.error("keywords and location are required when not using --job-url")
    
    # Convert timeout to milliseconds for Playwright
    timeout_ms = args.timeout * 1000
    
    if args.sync:
        # Use synchronous wrapper
        await sync_scrape(args, timeout_ms)
    else:
        # Use async scraper
        await async_scrape(args, timeout_ms)


async def async_scrape(args, timeout_ms: int):
    """Async scraping function."""
    async with LinkedInScraper(
        headless=args.headless,
        timeout=timeout_ms,
        browser=args.browser,
        proxy=args.proxy,
        anonymize=not args.no_anonymize
    ) as scraper:
        
        if args.job_url:
            # Get details for a specific job
            print(f"🔍 Getting details for job: {args.job_url}")
            job_details = await scraper.get_job_details(args.job_url)
            
            # Output results
            if args.output:
                output_file = args.output
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"job_details_{timestamp}.json"
            
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(job_details, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Job details saved to: {output_file}")
            
        else:
            # Collect job links
            experience_levels = parse_experience_levels(args.experience_levels) if args.experience_levels else None
            
            print(f"🔎 Searching for jobs: '{args.keywords}' in '{args.location}'")
            if args.max_jobs:
                print(f"📊 Max jobs: {args.max_jobs}")
            else:
                print(f"📄 Max pages: {args.max_pages}")
            if experience_levels:
                print(f"🎯 Experience levels: {experience_levels}")
            if args.date_posted:
                print(f"📅 Date posted: {args.date_posted}")
            if args.sort_by:
                print(f"🔀 Sort by: {args.sort_by}")
            
            print(f"🌐 Using browser: {args.browser} ({'headless' if args.headless else 'GUI'})")
            
            job_links = await scraper.collect_job_links(
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
                print(f"🔢 Limited to {len(job_links)} jobs (max_jobs: {args.max_jobs})")
            
            print(f"✅ Found {len(job_links)} job links")
            
            if args.links_only:
                # Only output links
                results = {
                    "job_links": job_links, 
                    "total_count": len(job_links),
                    "scraped_at": datetime.now().isoformat(),
                    "scraper_version": "playwright"
                }
                
                output_file = get_output_filename(args, "links")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Job links saved to: {output_file}")
                
            else:
                # Get detailed information for each job
                detailed_jobs = []
                
                print(f"📋 Extracting detailed information...")
                for i, job_url in enumerate(job_links, 1):
                    print(f"⏳ Getting details for job {i}/{len(job_links)}: {job_url}")
                    try:
                        job_details = await scraper.get_job_details(job_url)
                        detailed_jobs.append(job_details)
                        print(f"   ✅ {job_details.get('title', 'Unknown')} at {job_details.get('company', 'Unknown')}")
                    except Exception as e:
                        print(f"   ❌ Error getting details for {job_url}: {e}")
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
                        "sort_by": args.sort_by,
                        "browser": args.browser,
                        "headless": args.headless,
                        "proxy": args.proxy,
                        "anonymize": not args.no_anonymize
                    },
                    "total_jobs_found": len(detailed_jobs),
                    "jobs": detailed_jobs,
                    "scraped_at": datetime.now().isoformat(),
                    "scraper_version": "playwright"
                }
                
                output_file = get_output_filename(args, "details")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Job details saved to: {output_file}")
                print(f"🎉 Successfully scraped {len(detailed_jobs)} jobs")


async def sync_scrape(args, timeout_ms: int):
    """Synchronous scraping function using the sync wrapper."""
    print("🔄 Using synchronous mode (backwards compatibility)")
    
    # Convert timeout back to seconds for the sync wrapper
    timeout_seconds = timeout_ms // 1000
    
    scraper = LinkedInScraperSync(
        headless=args.headless,
        timeout=timeout_ms,
        browser=args.browser,
        proxy=args.proxy,
        anonymize=not args.no_anonymize
    )
    
    try:
        if args.job_url:
            # Get details for a specific job
            print(f"🔍 Getting details for job: {args.job_url}")
            job_details = scraper.get_job_details(args.job_url)
            
            # Output results
            if args.output:
                output_file = args.output
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"job_details_{timestamp}.json"
            
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(job_details, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Job details saved to: {output_file}")
            
        else:
            # Collect job links
            experience_levels = parse_experience_levels(args.experience_levels) if args.experience_levels else None
            
            print(f"🔎 Searching for jobs: '{args.keywords}' in '{args.location}'")
            if args.max_jobs:
                print(f"📊 Max jobs: {args.max_jobs}")
            else:
                print(f"📄 Max pages: {args.max_pages}")
            if experience_levels:
                print(f"🎯 Experience levels: {experience_levels}")
            if args.date_posted:
                print(f"📅 Date posted: {args.date_posted}")
            if args.sort_by:
                print(f"🔀 Sort by: {args.sort_by}")
            
            print(f"🌐 Using browser: {args.browser} ({'headless' if args.headless else 'GUI'})")
            
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
                print(f"🔢 Limited to {len(job_links)} jobs (max_jobs: {args.max_jobs})")
            
            print(f"✅ Found {len(job_links)} job links")
            
            if args.links_only:
                # Only output links
                results = {
                    "job_links": job_links, 
                    "total_count": len(job_links),
                    "scraped_at": datetime.now().isoformat(),
                    "scraper_version": "playwright-sync"
                }
                
                output_file = get_output_filename(args, "links")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Job links saved to: {output_file}")
                
            else:
                # Get detailed information for each job
                detailed_jobs = []
                
                print(f"📋 Extracting detailed information...")
                for i, job_url in enumerate(job_links, 1):
                    print(f"⏳ Getting details for job {i}/{len(job_links)}: {job_url}")
                    try:
                        job_details = scraper.get_job_details(job_url)
                        detailed_jobs.append(job_details)
                        print(f"   ✅ {job_details.get('title', 'Unknown')} at {job_details.get('company', 'Unknown')}")
                    except Exception as e:
                        print(f"   ❌ Error getting details for {job_url}: {e}")
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
                        "sort_by": args.sort_by,
                        "browser": args.browser,
                        "headless": args.headless,
                        "proxy": args.proxy,
                        "anonymize": not args.no_anonymize
                    },
                    "total_jobs_found": len(detailed_jobs),
                    "jobs": detailed_jobs,
                    "scraped_at": datetime.now().isoformat(),
                    "scraper_version": "playwright-sync"
                }
                
                output_file = get_output_filename(args, "details")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Job details saved to: {output_file}")
                print(f"🎉 Successfully scraped {len(detailed_jobs)} jobs")
    
    finally:
        scraper.close()


def get_output_filename(args, file_type: str) -> str:
    """Generate output filename based on arguments."""
    if args.output:
        return args.output
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keywords = "".join(c for c in args.keywords if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_location = "".join(c for c in args.location if c.isalnum() or c in (' ', '-', '_')).rstrip()
    
    # Create output directory
    output_dir = "output/linkedin"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"linkedin_jobs_{file_type}_{safe_keywords.replace(' ', '_')}_{safe_location.replace(' ', '_')}_{timestamp}.json"
    return os.path.join(output_dir, filename)


def main():
    """Main CLI entry point."""
    try:
        # Check for required environment variables
        if not os.getenv("LINKEDIN_USERNAME") or not os.getenv("LINKEDIN_PASSWORD"):
            print("❌ Error: LinkedIn credentials not found!")
            print("Please set LINKEDIN_USERNAME and LINKEDIN_PASSWORD in your .env file")
            sys.exit(1)
        
        print("🚀 LinkedIn Job Scraper (Playwright Version)")
        print("=" * 60)
        
        # Run async main
        asyncio.run(async_main())
        
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def sync_main():
    """Synchronous CLI entry point for backwards compatibility."""
    parser = argparse.ArgumentParser(description='LinkedIn Job Scraper (Playwright - Sync Mode)')
    
    # Required arguments
    parser.add_argument('keywords', help='Job search keywords')
    parser.add_argument('location', help='Job search location')
    
    # Optional arguments
    parser.add_argument('--max-pages', type=int, default=1, help='Maximum pages to scrape (default: 1)')
    parser.add_argument('--max-jobs', type=int, help='Maximum number of jobs to extract (overrides max-pages if specified)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium', help='Browser to use (default: chromium)')
    parser.add_argument('--timeout', type=int, default=20, help='Timeout in seconds (default: 20)')
    parser.add_argument('--output', help='Output file path (default: auto-generated)')
    
    # Filter arguments
    parser.add_argument('--experience-levels', type=str, help='Comma-separated experience levels (internship,entry_level,associate,mid_senior,director,executive)')
    parser.add_argument('--date-posted', choices=['any_time', 'past_month', 'past_week', 'past_24_hours'], help='Date posted filter')
    parser.add_argument('--sort-by', choices=['relevance', 'recent'], help='Sort results by')
    
    # Action arguments
    parser.add_argument('--links-only', action='store_true', help='Only collect job links, not detailed information')
    parser.add_argument('--job-url', help='Get details for a specific job URL')
    
    # Proxy and anonymization arguments
    parser.add_argument('--proxy', help='Proxy server (e.g., http://proxy:port or socks5://proxy:port)')
    parser.add_argument('--no-anonymize', action='store_true', help='Disable anonymization features (user agent randomization, WebGL blocking, etc.)')
    
    args = parser.parse_args()
    args.sync = True  # Force sync mode
    
    try:
        # Check for required environment variables
        if not os.getenv("LINKEDIN_USERNAME") or not os.getenv("LINKEDIN_PASSWORD"):
            print("❌ Error: LinkedIn credentials not found!")
            print("Please set LINKEDIN_USERNAME and LINKEDIN_PASSWORD in your .env file")
            sys.exit(1)
        
        print("🚀 LinkedIn Job Scraper (Playwright Version - Sync Mode)")
        print("=" * 60)
        
        # Run sync version directly
        timeout_ms = args.timeout * 1000
        asyncio.run(sync_scrape(args, timeout_ms))
        
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
