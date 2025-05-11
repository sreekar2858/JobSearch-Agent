"""
Job Search Pipeline - Complete workflow for finding and processing job listings.

This module implements the complete job search pipeline:
1. Generate optimized search queries for job sites
2. Use Google Search to find job listings
3. Extract job details with the scraper
4. Save results to JSON
"""
import json
import os
import time
from typing import Dict, List, Any
from google.adk.tools import google_search

from src.utils.file_utils import load_config
from src.scraper.crawl.scraper import JobScraper, extract_job_links_from_google_results

# Load configuration
jobsearch_config = load_config("config/jobsearch_config.yaml")
file_config = load_config("config/file_config.yaml")

class JobSearchPipeline:
    """
    Complete job search pipeline that combines Google Search with targeted scraping.
    Uses site-specific queries to find job listings on LinkedIn, Indeed, and Glassdoor.
    """
    
    def __init__(self, 
                 keywords: str, 
                 locations: List[str] = None, 
                 job_type: str = None, 
                 experience_level: str = None,
                 max_jobs_per_site: int = 3,
                 output_dir: str = "jobs"):
        """
        Initialize the job search pipeline.
        
        Args:
            keywords: Job title or keywords to search for
            locations: List of locations to search in
            job_type: Type of job (full-time, contract, etc)
            experience_level: Experience level required
            max_jobs_per_site: Maximum number of jobs to collect per site
            output_dir: Directory to save results
        """
        self.keywords = keywords
        self.locations = locations or jobsearch_config.get('locations', ["remote"])
        self.job_type = job_type or jobsearch_config.get('job_type', "full-time")
        self.experience_level = experience_level or jobsearch_config.get('experience_level', "mid-level")
        self.max_jobs_per_site = max_jobs_per_site
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize the scraper
        self.scraper = JobScraper(delay_range=(1.5, 4))
        
    def generate_search_query(self, site: str, location: str) -> str:
        """
        Generate a site-specific search query.
        
        Args:
            site: The job site to search (linkedin, indeed, glassdoor)
            location: Location to search in
            
        Returns:
            Optimized search query string
        """
        base_query = f"{self.keywords} {location}"
        if self.job_type and self.job_type.lower() != "any":
            base_query += f" {self.job_type}"
            
        site_queries = {
            "linkedin": f"site:linkedin.com/jobs {base_query}",
            "indeed": f"site:indeed.com/job {base_query}",
            "glassdoor": f"site:glassdoor.com/job {base_query}"
        }
        
        return site_queries.get(site.lower(), base_query)
    
    def search_jobs(self) -> List[Dict[str, Any]]:
        """
        Execute the complete job search pipeline.
        
        Returns:
            List of job postings with complete details
        """
        print("🚀 Starting job search pipeline...")
        all_results = []
        job_sites = ["linkedin", "indeed", "glassdoor"]
        
        for site in job_sites:
            print(f"\n🌐 Searching {site.capitalize()} jobs...")
            site_results = []
            
            for location in self.locations:
                print(f"  📍 Location: {location}")
                search_query = self.generate_search_query(site, location)
                print(f"  🔍 Query: {search_query}")
                
                try:
                    # Use Google Search to find job listings
                    print("  🔎 Executing Google search...")
                    search_results = google_search.run(search_query)["results"]
                    
                    # Extract job links
                    job_links = extract_job_links_from_google_results(search_results)
                    
                    # Limit the number of jobs per site/location
                    site_limit = min(len(job_links), self.max_jobs_per_site)
                    job_links = job_links[:site_limit]
                    
                    # Scrape job details
                    if job_links:
                        print(f"  🔍 Scraping {len(job_links)} job postings from {site.capitalize()}...")
                        jobs_data = self.scraper.batch_process_urls(job_links)
                        site_results.extend(jobs_data)
                    else:
                        print(f"  ⚠️ No job links found for {site.capitalize()} in {location}")
                    
                except Exception as e:
                    print(f"  ❌ Error searching {site} jobs in {location}: {str(e)}")
                
                # Small delay between location searches
                time.sleep(1)
            
            # Add the site results to the complete list
            all_results.extend(site_results)
            print(f"  ✓ Found {len(site_results)} jobs on {site.capitalize()}")
            
        # Save all results to JSON
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"job_postings_{timestamp}.json")
        
        print(f"\n💾 Saving {len(all_results)} job postings to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Job search completed. Found {len(all_results)} job postings!")
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
                  max_jobs: int = 10) -> str:
    """
    Convenience function to run the job search pipeline.
    
    Args:
        keywords: Job title or keywords to search for
        locations: List of locations to search in
        job_type: Type of job (full-time, contract, etc)
        experience_level: Experience level required
        max_jobs: Maximum number of jobs to collect per site
        
    Returns:
        Path to the output JSON file
    """
    pipeline = JobSearchPipeline(
        keywords=keywords,
        locations=locations,
        job_type=job_type,
        experience_level=experience_level,
        max_jobs_per_site=max_jobs,
    )
    
    return pipeline.search_and_process()


if __name__ == "__main__":
    # Example usage
    keywords = "Python Developer"
    locations = ["Remote", "London", "New York"]
    
    output_file = run_job_search(
        keywords=keywords, 
        locations=locations,
        job_type="full-time",
        max_jobs=3
    )
    
    print(f"\n🎉 Job search completed! Results saved to: {output_file}")