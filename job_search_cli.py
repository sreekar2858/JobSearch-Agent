#!/usr/bin/env python
"""
Job Search CLI - Command line interface for searching jobs from multiple platforms.

This script provides a command-line interface to search for jobs on:
- LinkedIn
- Indeed
- Glassdoor

It uses Google Search with specialized site-specific queries to find job listings
without requiring paid API access to these platforms.
"""
import argparse
import sys
import json
from typing import List

from src.utils.job_search_pipeline import run_job_search
from main import process_jobs

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Search for jobs on LinkedIn, Indeed, and Glassdoor without using APIs',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        'keywords', 
        help='Job title or keywords to search for (e.g., "Python Developer")'
    )
    
    parser.add_argument(
        '-l', '--locations',
        nargs='+',
        default=['Remote'],
        help='Locations to search in (e.g., "New York" "London" "Remote")'
    )
    
    parser.add_argument(
        '-t', '--job-type',
        default='full-time',
        choices=['full-time', 'part-time', 'contract', 'internship', 'any'],
        help='Type of job'
    )
    
    parser.add_argument(
        '-e', '--experience',
        default='mid-level',
        choices=['entry', 'mid-level', 'senior', 'any'],
        help='Experience level required'
    )
    
    parser.add_argument(
        '-m', '--max-jobs',
        type=int,
        default=3,
        help='Maximum number of jobs to fetch per site and location'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='jobs',
        help='Directory to save results'
    )
    
    parser.add_argument(
        '-c', '--generate-cv',
        action='store_true',
        help='Generate custom CVs for all found jobs'
    )
    
    return parser.parse_args()

def main():
    """Main function to run the job search CLI."""
    args = parse_arguments()
    
    print(f"\n🔎 Searching for: {args.keywords}")
    print(f"📍 Locations: {', '.join(args.locations)}")
    print(f"💼 Job type: {args.job_type}")
    print(f"📊 Experience level: {args.experience}")
    print(f"🔢 Max jobs per site/location: {args.max_jobs}")
    
    try:
        # Run the job search pipeline
        output_file = run_job_search(
            keywords=args.keywords,
            locations=args.locations,
            job_type=args.job_type,
            experience_level=args.experience,
            max_jobs=args.max_jobs
        )
        
        print(f"\n✅ Job search completed successfully!")
        print(f"💾 Results saved to: {output_file}")
        
        # Generate CVs if requested
        if args.generate_cv:
            print("\n🚀 Starting CV generation for all found jobs...")
            process_jobs(output_file)
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())