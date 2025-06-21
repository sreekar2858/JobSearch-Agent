#!/usr/bin/env python3
"""
Test script to verify scraper execution in the job search pipeline
"""

from src.utils.job_search_pipeline import JobSearchPipeline

def test_scraper_execution():
    """Test if scrapers are being executed correctly"""
    print("[TEST] Testing scraper execution in job search pipeline...")
    
    # Create a pipeline instance
    pipeline = JobSearchPipeline(
        keywords='python developer',
        locations=['Remote'],
        scrapers=['linkedin'],
        max_jobs_per_site=1  # Start with just 1 job for testing
    )
    
    print(f"[INFO] Pipeline scrapers: {pipeline.scrapers}")
    print(f"[INFO] LinkedIn scraper object: {type(pipeline.linkedin_scraper)}")
    print(f"[INFO] Max jobs per site: {pipeline.max_jobs_per_site}")
    
    try:
        print("[INFO] Testing search_jobs method...")
        results = pipeline.search_jobs()
        print(f"[RESULT] Found {len(results)} jobs")
        
        if results:
            print("[JOBS] Job details:")
            for i, job in enumerate(results[:3]):
                title = job.get('title', 'N/A')
                company = job.get('company', 'N/A')
                location = job.get('location', 'N/A')
                print(f"  {i+1}. {title} at {company} ({location})")
        else:
            print("[WARN] No jobs found")
            
    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraper_execution()
