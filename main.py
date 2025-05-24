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
import os
import json
import sys
import argparse
from typing import List, Any

from src.utils.file_utils import slugify
from src.agents.cv_writer import call_cv_agent
from src.agents.coverLetter_writer import call_cover_letter_agent
from src.agents.job_details_parser import call_job_parsr_agent
from src.utils.job_search_pipeline import run_job_search

def process_jobs(json_path: str,
                 output_dir: str = "output",
                 generate_cv: bool = False,
                 generate_cover_letter: bool = False
                 ) -> None:
    """
    Load jobs from a JSON file and generate CVs and/or cover letters for each job.
    
    Args:
        json_path: Path to the JSON file containing job listings
        output_dir: Directory to save output files
        generate_cv: Whether to generate custom CVs
        generate_cover_letter: Whether to generate cover letters
    """
    print("📋 Loading job postings from JSON file...")
    with open(json_path, 'r', encoding='utf-8') as f:
        jobs = json.load(f)

    # Create a list if jobs is a single job
    if isinstance(jobs, dict):
        jobs = [jobs]
    
    print(f"📊 Found {len(jobs)} job postings to process")

    for i, job in enumerate(jobs):
        # Create a folder for this job
        company = job.get('company_name', '')
        job_title = job.get('job_title', '')
        print(f"\n🔹 Processing job {i+1}/{len(jobs)}: {job_title} at {company}")
        
        folder_name = os.path.join(output_dir, slugify(f"{company}_{job_title}"))
        os.makedirs(folder_name, exist_ok=True)
        print(f"📁 Created folder: {folder_name}")
        
        # Save job details
        print(f"💾 Saving job details to {folder_name}/{company}_{job_title}_metadata.json")
        with open(os.path.join(folder_name, f'{company}_{job_title}_metadata.json'), 'w', encoding='utf-8') as detail_file:
            json.dump(job, detail_file, indent=2)
        
        job_details_str = json.dumps(job)
        
        # Generate custom CV if requested
        if generate_cv:
            print(f"🤖 Starting CV generation for {job_title}...")
            try:
                cv_text, state_json, cv_path = call_cv_agent(job_details_str)
                # Save the CV text
                print(f"📄 Saving CV text to {folder_name}/{company}_{job_title}_cv.txt")
                with open(os.path.join(folder_name, f'{company}_{job_title}_cv.txt'), 'w', encoding='utf-8') as cv_file:
                    cv_file.write(cv_text)
            except Exception as e:
                print(f"❌ Error generating CV for {folder_name}: {e}")
        
        # Generate cover letter if requested
        if generate_cover_letter:
            print(f"📝 Starting cover letter generation for {job_title}...")
            try:
                cover_letter_text, cl_state_json, cl_path = call_cover_letter_agent(job_details_str)
                print(f"📄 Saving cover letter to {folder_name}/{company}_{job_title}.txt")
                with open(os.path.join(folder_name, f'{company}_{job_title}.txt'), 'w', encoding='utf-8') as cl_file:
                    cl_file.write(cover_letter_text)
            except Exception as e:
                print(f"❌ Error generating cover letter for {folder_name}: {e}")
                # Fallback to placeholder if generation fails
                cover_letter_text = f"Cover letter placeholder for {job_title} at {company}\n"
                with open(os.path.join(folder_name, f'{company}_{job_title}.txt'), 'w', encoding='utf-8') as cl_file:
                    cl_file.write(cover_letter_text)
        
    print("\n✅ All jobs processed successfully!")
    print(f"📂 Output files are available in the '{output_dir}' directory")

def parse_job_postings(text:str=None, **kwargs) -> None:
    # Parses the job postings from the given text file by passing to the 
    input_file = kwargs.get('input_file', None)
    if input_file:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
            
    if not text:
        print("❌ No text provided for parsing. Exiting.")
        return
    
    # Run the Job Parser agent
    print("🔍 Parsing job postings...")
    job_postings = call_job_parsr_agent(text)
    
    # Save the parsed job postings to a JSON file
    output_file = kwargs.get('output_file', None)
    # if the output file specified is not in the output directory, create the directory
    if output_file and not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        print(f"📂 Created output directory: {os.path.dirname(output_file)}")
    # if the output file is not specified, use the default name
    if not output_file:
        output_file = os.path.join("output", f"{input_file}_parsed.json")
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json.loads(job_postings), f, indent=2)
        print(f"💾 Parsed job postings saved to {output_file}")
    else:
        print("❌ No output file specified. Job postings not saved.")
        print("📋 Job postings:")
        print(json.dumps(job_postings, indent=2))

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Search for jobs on LinkedIn, Indeed, and Glassdoor without using APIs',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for jobs')
    search_parser.add_argument(
        'keywords', 
        help='Job title or keywords to search for (e.g., "Python Developer, Mechanical Engineer")'
    )
    search_parser.add_argument(
        '-l', '--locations',
        nargs='+',
        default=['Remote'],
        help='Locations to search in (e.g., "New York" "London" "Remote")'
    )
    search_parser.add_argument(
        '-t', '--job-type',
        default='full-time',
        choices=['full-time', 'part-time', 'contract', 'internship', 'any'],
        help='Type of job'
    )
    search_parser.add_argument(
        '-e', '--experience',
        default='mid-level',
        choices=['entry', 'mid-level', 'senior', 'any'],
        help='Experience level required'
    )
    search_parser.add_argument(
        '-m', '--max-jobs',
        type=int,
        default=3,
        help='Maximum number of jobs to fetch per site and location'
    )    
    search_parser.add_argument(
        '-o', '--output-dir',
        default='jobs',
        help='Directory to save results'
    )
    search_parser.add_argument(
        '-c', '--generate-cv',
        action='store_true',
        help='Generate custom CVs for all found jobs'
    )
    search_parser.add_argument(
        '-cl', '--generate-cover-letter',
        action='store_true',
        help='Generate cover letters for all found jobs'
    )
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process jobs from a JSON file')
    process_parser.add_argument(
        'json_file',
        help='JSON file containing job listings'
    )
    process_parser.add_argument(
        '-o', '--output-dir',
        default='output',
        help='Directory to save processed jobs'
    )
    process_parser.add_argument(
        '-c', '--generate-cv',
        action='store_true',
        default=True,
        help='Generate custom CVs (default: True)'
    )
    process_parser.add_argument(
        '-cl', '--generate-cover-letter',
        action='store_true',
        help='Generate cover letters for all jobs'
    )
    process_parser.add_argument(
        '--no-cv',
        action='store_true',
        help='Skip CV generation'
    )
    
    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse job details from text')
    parse_parser.add_argument(
        '-i', '--input-file',
        help='Text file with job details to parse'
    )
    parse_parser.add_argument(
        '-o', '--output-file',
        help='JSON file to save parsed job details'
    )    
    parse_parser.add_argument(
        '-t', '--text',
        help='Direct text to parse instead of input file'
    )
    
    return parser.parse_args()

def main():
    """Main function to run the job search CLI."""
    args = parse_arguments()
    
    if args.command == 'search':
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
            
            print("\n✅ Job search completed successfully!")
            print(f"💾 Results saved to: {output_file}")
            
            # Generate documents if requested
            if args.generate_cv or args.generate_cover_letter:
                print("\n🚀 Starting document generation for all found jobs...")
                process_jobs(
                    output_file, 
                    generate_cv=args.generate_cv, 
                    generate_cover_letter=args.generate_cover_letter
                )
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return 1
    
    elif args.command == 'process':
        try:
            print(f"\n📋 Processing jobs from: {args.json_file}")
            generate_cv = args.generate_cv and not args.no_cv
            process_jobs(
                args.json_file, 
                args.output_dir,
                generate_cv=generate_cv, 
                generate_cover_letter=args.generate_cover_letter
            )
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return 1
    
    elif args.command == 'parse':
        try:
            if args.text:
                parse_job_postings(text=args.text, output_file=args.output_file)
            elif args.input_file:
                parse_job_postings(input_file=args.input_file, output_file=args.output_file)
            else:
                print("❌ Error: Either text or input file must be provided for parsing")
                return 1
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return 1
    
    elif args.command == 'single':
        try:
            generate_cv = args.generate_cv and not args.no_cv
            
            # Create a job object from the single job parameters
            job_info = {
                "job_title": args.title,
                "company_name": args.company,
                "job_description": args.description
            }
            
            # Create a temporary JSON file for the single job
            temp_file = os.path.join("output", "temp_single_job.json")
            os.makedirs("output", exist_ok=True)
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(job_info, f, indent=2)
                
            # Process the job using the process_jobs function
            print(f"🔹 Processing single job: {args.title} at {args.company}")
            
            process_jobs(
                temp_file,
                output_dir="output",
                generate_cv=generate_cv,
                generate_cover_letter=args.generate_cover_letter
            )
              # Clean up the temporary file
            try:
                os.remove(temp_file)
            except Exception:
                pass
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return 1
    
    else:
        print("❌ No command specified. Use --help for usage information.")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
