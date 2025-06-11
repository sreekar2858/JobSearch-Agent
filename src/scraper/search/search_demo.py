"""
Sample script to demonstrate the usage of the local job scraper.

This script shows how to:
- Initialize the JobSearchManager
- Search for jobs on LinkedIn
- Save the results to a file
"""

import os
import sys
import logging
from argparse import ArgumentParser

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.scraper.search import JobSearchManager


def parse_args():
    """Parse command line arguments."""
    parser = ArgumentParser(description="Search for jobs using local scraper")
    parser.add_argument(
        "--keywords",
        type=str,
        required=True,
        help='Job search keywords (e.g., "Software Engineer")',
    )
    parser.add_argument(
        "--location",
        type=str,
        required=True,
        help='Location for job search (e.g., "Berlin, Germany")',
    )
    parser.add_argument(
        "--platforms",
        type=str,
        nargs="+",
        default=["linkedin"],
        help="Platforms to search (default: linkedin)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum number of pages to scrape per platform (default: 5)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="jobs",
        help="Directory to save job data (default: jobs)",
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run browsers in headless mode"
    )

    return parser.parse_args()


def main():
    """Main function to run the job search."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("job_search_demo")

    # Parse command line arguments
    args = parse_args()

    logger.info(f"Starting job search with the following parameters:")
    logger.info(f"  Keywords: {args.keywords}")
    logger.info(f"  Location: {args.location}")
    logger.info(f"  Platforms: {', '.join(args.platforms)}")
    logger.info(f"  Max Pages: {args.max_pages}")
    logger.info(f"  Output Directory: {args.output_dir}")
    logger.info(f"  Headless Mode: {args.headless}")

    try:
        # Initialize the job search manager
        search_manager = JobSearchManager(
            headless=args.headless, output_dir=args.output_dir
        )

        # Search for jobs
        results = search_manager.search_jobs(
            keywords=args.keywords,
            location=args.location,
            platforms=args.platforms,
            max_pages=args.max_pages,
            save_results=True,
        )

        # Print summary of results
        total_jobs = sum(len(jobs) for jobs in results.values())
        logger.info(
            f"Job search completed. Found {total_jobs} jobs across {len(results)} platforms."
        )

        for platform, jobs in results.items():
            logger.info(f"  {platform.capitalize()}: {len(jobs)} jobs")

    except Exception as e:
        logger.error(f"Error during job search: {str(e)}")
    finally:
        # Make sure to close the browser sessions
        if "search_manager" in locals():
            search_manager.close()

    logger.info("Job search demo completed")


if __name__ == "__main__":
    main()
