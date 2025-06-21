"""
Job Search Pipeline - Complete workflow for finding and processing job listings.

This module implements the complete job search pipeline using direct scrapers:
1. Use LinkedIn scraper to search for jobs directly
2. Extract job details with the scraper
3. Save results to JSON
"""
import json
import os
import time
from typing import Dict, List, Any

from src.utils.file_utils import load_config
from src.scraper.search.linkedin_scraper.scraper import LinkedInScraperSync

# Load configuration
jobsearch_config = load_config("config/jobsearch_config.yaml")
file_config = load_config("config/file_config.yaml")

class JobSearchPipeline:
    """
    Complete job search pipeline using direct scrapers.
    Directly searches job sites without needing Google search.
    """
    
    def __init__(self, 
                 keywords: str, 
                 locations: List[str] = None, 
                 job_type: str = None, 
                 experience_level: str = None,
                 max_jobs_per_site: int = 3,
                 output_dir: str = "jobs",
                 scrapers: List[str] = None):
        """
        Initialize the job search pipeline.
        
        Args:
            keywords: Job title or keywords to search for
            locations: List of locations to search in
            job_type: Type of job (full-time, contract, etc)
            experience_level: Experience level required
            max_jobs_per_site: Maximum number of jobs to collect per site
            output_dir: Directory to save results
            scrapers: List of scrapers to use (linkedin, indeed, glassdoor)
        """
        self.keywords = keywords
        self.locations = locations or jobsearch_config.get('locations', ["remote"])
        self.job_type = job_type or jobsearch_config.get('job_type', "full-time")
        self.experience_level = experience_level or jobsearch_config.get('experience_level', "mid-level")
        self.max_jobs_per_site = max_jobs_per_site
        self.output_dir = output_dir
        self.scrapers = scrapers or ["linkedin"]  # Default to LinkedIn
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize scrapers
        self.linkedin_scraper = None
        if "linkedin" in self.scrapers:
            print("[INIT] Initializing LinkedIn scraper...")
            try:
                self.linkedin_scraper = LinkedInScraperSync(headless=True)
                print("[SUCCESS] LinkedIn scraper initialized")
            except Exception as e:
                print(f"[ERROR] Failed to initialize LinkedIn scraper: {e}")
                self.linkedin_scraper = None
    
    def search_jobs(self) -> List[Dict[str, Any]]:
        """
        Execute the complete job search pipeline using direct scrapers.
        
        Returns:
            List of job postings with complete details
        """
        print("[START] Starting job search pipeline...")
        all_results = []
        
        # LinkedIn scraping
        if "linkedin" in self.scrapers and self.linkedin_scraper:
            print(f"\n[SITE] Searching LinkedIn jobs...")
            
            for location in self.locations:
                print(f"  [LOCATION] Location: {location}")
                
                try:
                    # Collect job links using LinkedIn scraper
                    print(f"  [SEARCH] Searching LinkedIn for: {self.keywords}")
                    job_links = self.linkedin_scraper.collect_job_links(
                        keywords=self.keywords,
                        location=location,
                        max_pages=1  # Start with 1 page
                    )
                    
                    print(f"  [LINKS] Found {len(job_links)} job links")
                    
                    # Limit the number of jobs
                    if len(job_links) > self.max_jobs_per_site:
                        job_links = job_links[:self.max_jobs_per_site]
                        print(f"  [LIMIT] Limited to {self.max_jobs_per_site} jobs")
                    
                    # Get job details for each link
                    location_results = []
                    for i, job_url in enumerate(job_links):
                        print(f"  [SCRAPE] Processing job {i+1}/{len(job_links)}")
                        
                        try:
                            job_details = self.linkedin_scraper.get_job_details(job_url)
                            if job_details:
                                location_results.append(job_details)
                                print(f"    ✅ {job_details.get('title', 'N/A')} at {job_details.get('company', 'N/A')}")
                            else:
                                print(f"    ❌ Failed to get details")
                        except Exception as e:
                            print(f"    ❌ Error getting job details: {str(e)}")
                        
                        # Small delay between requests
                        time.sleep(2)
                    
                    all_results.extend(location_results)
                    print(f"  [SUCCESS] Found {len(location_results)} jobs in {location}")
                    
                except Exception as e:
                    print(f"  [ERROR] Error searching LinkedIn in {location}: {str(e)}")
                
                # Delay between locations
                time.sleep(3)
            
            print(f"  [TOTAL] LinkedIn total: {len([r for r in all_results if r.get('source') == 'linkedin'])} jobs")
        
        # TODO: Add other scrapers here (Indeed, Glassdoor, etc.)
        
        # Save all results to JSON
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"job_postings_{timestamp}.json")
        
        print(f"\n💾 Saving {len(all_results)} job postings to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Job search completed. Found {len(all_results)} job postings!")
        
        # Close scrapers
        if self.linkedin_scraper:
            try:
                self.linkedin_scraper.close()
            except:
                pass
        
        return all_results
    
    def search_and_process(self) -> str:
        """
        Run the search pipeline and return the path to the output file.
        
        Returns:
            Path to the JSON file with the job results
        """
        results = self.search_jobs()
        
        # Save the latest results to the standard job_postings.json file
        standard_output = os.path.join(self.output_dir, "job_postings.json")
        with open(standard_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return standard_output

def run_job_search(keywords: str, 
                  locations: List[str] = None,
                  job_type: str = None,
                  experience_level: str = None,
                  max_jobs: int = 10,
                  scrapers: List[str] = None) -> str:    
    """
    Convenience function to run the job search pipeline.
    
    Args:
        keywords: Job title or keywords to search for
        locations: List of locations to search in
        job_type: Type of job (full-time, contract, etc)
        experience_level: Experience level required
        max_jobs: Maximum number of jobs to collect total
        scrapers: List of scrapers to use
        
    Returns:
        Path to the output JSON file
    """
    # Calculate max jobs per site based on total and number of scrapers
    scrapers = scrapers or ["linkedin"]
    max_jobs_per_site = max(1, max_jobs // len(scrapers))
    
    pipeline = JobSearchPipeline(
        keywords=keywords,
        locations=locations,
        job_type=job_type,
        experience_level=experience_level,
        max_jobs_per_site=max_jobs_per_site,
        scrapers=scrapers
    )
    
    return pipeline.search_and_process()
