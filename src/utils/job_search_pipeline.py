"""
Job Search Pipeline - Complete workflow for finding and processing job listings.

This module implements both sync and async job search pipelines using direct scrapers:
1. Use LinkedIn scraper to search for jobs directly
2. Extract job details with the scraper
3. Save results to JSON and Database
4. Avoid duplicate jobs using database checks

Supports both synchronous and asynchronous execution modes for different use cases:
- Sync: For CLI scripts and standalone execution
- Async: For FastAPI background tasks and existing event loops
"""
import json
import sys
import os
import time
import asyncio
from typing import Dict, List, Any

from src.utils.file_utils import load_config
from src.utils.job_database import JobDatabase
# Don't import scrapers at module level to avoid potential initialization issues
# They will be imported dynamically when needed

# Load configuration
jobsearch_config = load_config("config/jobsearch_config.yaml")
file_config = load_config("config/file_config.yaml")

class JobSearchPipeline:
    """
    Complete job search pipeline using direct scrapers.
    Supports both synchronous and asynchronous execution modes.
    """
    
    def __init__(self,
                 keywords: str, 
                 locations: List[str] = None, 
                 job_type: str = None, 
                 experience_level: str = None,
                 max_jobs_per_site: int = 3,
                 output_dir: str = "jobs",
                 scrapers: List[str] = None,
                 use_database: bool = True,
                 async_mode: bool = False):
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
            use_database: Whether to save jobs to database and check for duplicates
            async_mode: Whether to use async scrapers (for FastAPI/event loop integration)
        """
        self.keywords = keywords
        self.locations = locations or jobsearch_config.get('locations', ["remote"])
        self.job_type = job_type or jobsearch_config.get('job_type', "full-time")
        self.experience_level = experience_level or jobsearch_config.get('experience_level', "mid-level")
        self.max_jobs_per_site = max_jobs_per_site
        self.output_dir = output_dir
        self.scrapers = scrapers or ["linkedin"]  # Default to LinkedIn
        self.use_database = use_database
        self.async_mode = async_mode
        
        # Initialize database connection
        self.db = JobDatabase() if use_database else None
        if self.db:
            print("[INIT] Database connection established")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize scrapers (sync mode only in __init__)
        self.linkedin_scraper = None
        if not async_mode and "linkedin" in self.scrapers:
            print("[INIT] Initializing LinkedIn scraper (sync mode)...")
            try:
                from src.scraper.search.linkedin_scraper.scraper import LinkedInScraperSync
                self.linkedin_scraper = LinkedInScraperSync(headless=True)
                print("[SUCCESS] LinkedIn scraper initialized")
            except Exception as e:
                print(f"[ERROR] Failed to initialize LinkedIn scraper: {e}")
                self.linkedin_scraper = None
    
    async def _initialize_scrapers_async(self):
        """Initialize scrapers asynchronously with proper error handling"""
        # Apply Windows async fix before initializing scrapers
        if sys.platform == "win32":
            try:
                # Ensure ProactorEventLoop policy is set for subprocess compatibility
                current_policy = asyncio.get_event_loop_policy()
                if not isinstance(current_policy, asyncio.WindowsProactorEventLoopPolicy):
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    print("[WINDOWS] Applied Windows async compatibility fix")
            except Exception as e:
                print(f"[WARN] Could not apply Windows async fix: {e}")
        
        if "linkedin" in self.scrapers:
            print("[INIT] Initializing LinkedIn scraper (async mode)...")
            try:
                # Import the async scraper dynamically to avoid module-level issues
                from src.scraper.search.linkedin_scraper.scraper import LinkedInScraper
                self.linkedin_scraper = LinkedInScraper(headless=True)
                print("[SUCCESS] LinkedIn scraper initialized (async)")
            except Exception as e:
                print(f"[ERROR] Failed to initialize LinkedIn scraper: {e}")
                self.linkedin_scraper = None
    
    def _initialize_scrapers_sync(self):
        """Initialize scrapers synchronously with proper error handling"""
        if "linkedin" in self.scrapers:
            print("[INIT] Initializing LinkedIn scraper (sync mode)...")
            try:
                # Use the sync version of the Playwright-based scraper
                from src.scraper.search.linkedin_scraper.scraper import LinkedInScraperSync
                self.linkedin_scraper = LinkedInScraperSync(headless=True)
                print("[SUCCESS] LinkedIn scraper initialized (Playwright sync)")
            except Exception as e:
                print(f"[ERROR] Failed to initialize LinkedIn scraper: {e}")
                self.linkedin_scraper = None
    
    def search_jobs(self) -> List[Dict[str, Any]]:
        """
        Execute the complete job search pipeline using direct scrapers.
        
        Returns:
            List of job postings with complete details
        """
        start_time = time.time()
        print("[START] Starting job search pipeline...")
        all_results = []
        
        # Initialize scrapers if not already done
        if not hasattr(self, 'linkedin_scraper') or self.linkedin_scraper is None:
            self._initialize_scrapers_sync()
        
        # LinkedIn scraping
        if "linkedin" in self.scrapers and self.linkedin_scraper:
            print(f"\n[SITE] Searching LinkedIn jobs...")
            
            for location in self.locations:
                print(f"  [LOCATION] Location: {location}")
                
                try:
                    # Collect job links using LinkedIn scraper
                    print(f"  [SEARCH] Searching LinkedIn for: {self.keywords}")
                    
                    # Calculate number of pages based on max_jobs_per_site
                    # Assuming ~25 jobs per page, calculate pages needed
                    max_pages = max(1, (self.max_jobs_per_site + 24) // 25)
                    print(f"  [PAGES] Will scrape {max_pages} page(s) to get up to {self.max_jobs_per_site} jobs")
                    
                    job_links = self.linkedin_scraper.collect_job_links(
                        keywords=self.keywords,
                        location=location,
                        max_pages=max_pages
                    )
                    
                    print(f"  [LINKS] Found {len(job_links)} job links")
                    
                    # Limit the number of jobs
                    if len(job_links) > self.max_jobs_per_site:
                        job_links = job_links[:self.max_jobs_per_site]
                        print(f"  [LIMIT] Limited to {self.max_jobs_per_site} jobs")                    # Get job details for each link with immediate database updates
                    location_results = []
                    successful_saves = 0
                    skipped_existing = 0
                    failed_scrapes = 0
                    
                    for i, job_url in enumerate(job_links):
                        print(f"  [SCRAPE] Processing job {i+1}/{len(job_links)}: {job_url}")
                        
                        # Check if job already exists in database
                        if self.db and self.db.job_exists(source_url=job_url):
                            print(f"    ⏭️  Job already exists in database, skipping...")
                            skipped_existing += 1
                            continue
                        
                        try:
                            job_details = self.linkedin_scraper.get_job_details(job_url)
                            if job_details:
                                # Add metadata
                                job_details['source'] = 'linkedin'
                                job_details['source_url'] = job_url
                                job_details['scraped_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
                                  # Save to database immediately with detailed feedback
                                if self.db:
                                    feedback = self.db.add_job_with_immediate_feedback(job_details)
                                    if feedback["success"]:
                                        successful_saves += 1
                                        print(f"    💾 {feedback['message']} ({feedback['duration_ms']}ms)")
                                    else:
                                        print(f"    ⚠️  {feedback['message']} ({feedback['duration_ms']}ms)")
                                        failed_scrapes += 1
                                else:
                                    # If no database, add to results for JSON output
                                    location_results.append(job_details)
                                
                                job_title = job_details.get('job_title', job_details.get('title', 'N/A'))
                                company_name = job_details.get('company_name', job_details.get('company', 'N/A'))
                                print(f"    ✅ {job_title} at {company_name}")
                            else:
                                print(f"    ❌ Failed to get job details")
                                failed_scrapes += 1
                        except Exception as e:
                            print(f"    ❌ Error getting job details: {str(e)}")
                            failed_scrapes += 1
                        
                        # Small delay between requests to avoid rate limiting
                        time.sleep(2)
                    
                    # Print summary for this location
                    print(f"  [SUMMARY] Location {location}: {successful_saves} saved, {skipped_existing} skipped, {failed_scrapes} failed")
                    
                    # For reporting purposes, create fake result entries for saved jobs
                    if self.db and successful_saves > 0:
                        # Add placeholder results to represent saved jobs
                        location_results = [{"saved": True}] * successful_saves
                    
                    all_results.extend(location_results)
                    print(f"  [SUCCESS] Found {len(location_results)} jobs in {location}")
                    
                except Exception as e:
                    print(f"  [ERROR] Error searching LinkedIn in {location}: {str(e)}")
                
                # Delay between locations
                time.sleep(3)
            
            print(f"  [TOTAL] LinkedIn total: {len([r for r in all_results if r.get('source') == 'linkedin'])} jobs")
          # TODO: Add other scrapers here (Indeed, Glassdoor, etc.)
        
        # Only save JSON if database is not used or explicitly requested
        if not self.use_database and all_results:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.output_dir, f"job_postings_{timestamp}.json")
            
            print(f"\n💾 Saving {len(all_results)} job postings to {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
        elif self.use_database:
            print(f"\n💾 Jobs saved to database only (no JSON output)")
        
        print(f"✅ Job search completed. Found {len(all_results)} job postings!")
          # Display final statistics with database breakdown
        if self.db:
            stats = self.db.get_stats()
            print(f"\n📊 Final Database Statistics:")
            print(f"  Total jobs in database: {stats['total_jobs']}")
            print(f"  Jobs by source:")
            for source in stats['by_source']:
                print(f"    - {source['source']}: {source['count']} jobs")
            print(f"  Top companies:")
            for company in stats['top_companies'][:3]:
                print(f"    - {company['company']}: {company['count']} jobs")
        
        # Display session summary
        print(f"\n📈 Session Summary:")
        print(f"  Jobs scraped this session: {len(all_results)}")
        print(f"  Total processing time: {time.time() - start_time:.1f} seconds")
        if all_results:
            print(f"  Average time per job: {(time.time() - start_time) / len(all_results):.1f} seconds")
        
        # Close scrapers and database
        if self.linkedin_scraper:
            try:
                self.linkedin_scraper.close()
            except:
                pass
        
        if self.db:
            try:
                self.db.close()
            except:
                pass
        
        return all_results
    
    async def search_jobs_async(self) -> List[Dict[str, Any]]:
        """
        Execute the complete job search pipeline using direct scrapers (async version).
        
        Returns:
            List of job postings with complete details
        """
        start_time = time.time()
        print("[START] Starting job search pipeline (async mode)...")
        all_results = []
        
        # Initialize scrapers
        await self._initialize_scrapers_async()
        
        # LinkedIn scraping
        if "linkedin" in self.scrapers and self.linkedin_scraper:
            print(f"\n[SITE] Searching LinkedIn jobs...")
            
            for location in self.locations:
                print(f"  [LOCATION] Location: {location}")
                
                try:
                    # Collect job links using LinkedIn scraper
                    print(f"  [SEARCH] Searching LinkedIn for: {self.keywords}")
                    
                    # Calculate number of pages based on max_jobs_per_site
                    # Assuming ~25 jobs per page, calculate pages needed
                    max_pages = max(1, (self.max_jobs_per_site + 24) // 25)
                    print(f"  [PAGES] Will scrape {max_pages} page(s) to get up to {self.max_jobs_per_site} jobs")
                    
                    # Use appropriate method based on scraper type
                    if self.async_mode and hasattr(self.linkedin_scraper, 'collect_job_links'):
                        # Async scraper
                        job_links = await self.linkedin_scraper.collect_job_links(
                            keywords=self.keywords,
                            location=location,
                            max_pages=max_pages
                        )
                    else:
                        # Sync scraper fallback
                        job_links = self.linkedin_scraper.collect_job_links(
                            keywords=self.keywords,
                            location=location,
                            max_pages=max_pages
                        )
                    
                    print(f"  [LINKS] Found {len(job_links)} job links")
                    
                    # Limit the number of jobs
                    if len(job_links) > self.max_jobs_per_site:
                        job_links = job_links[:self.max_jobs_per_site]
                        print(f"  [LIMIT] Limited to {self.max_jobs_per_site} jobs")
                    
                    # Get job details for each link with immediate database updates
                    location_results = []
                    successful_saves = 0
                    skipped_existing = 0
                    failed_scrapes = 0
                    
                    for i, job_url in enumerate(job_links):
                        print(f"  [SCRAPE] Processing job {i+1}/{len(job_links)}: {job_url}")
                        
                        # Check if job already exists in database
                        if self.db and self.db.job_exists(source_url=job_url):
                            print(f"    ⏭️  Job already exists in database, skipping...")
                            skipped_existing += 1
                            continue
                        
                        try:
                            # Use appropriate method based on scraper type
                            if self.async_mode and hasattr(self.linkedin_scraper, 'collect_job_links'):
                                # Async scraper
                                job_details = await self.linkedin_scraper.get_job_details(job_url)
                            else:
                                # Sync scraper fallback
                                job_details = self.linkedin_scraper.get_job_details(job_url)
                                
                            if job_details:
                                # Add metadata
                                job_details['source'] = 'linkedin'
                                job_details['source_url'] = job_url
                                job_details['scraped_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
                                
                                # Save to database immediately with detailed feedback
                                if self.db:
                                    feedback = self.db.add_job_with_immediate_feedback(job_details)
                                    if feedback["success"]:
                                        successful_saves += 1
                                        print(f"    💾 {feedback['message']} ({feedback['duration_ms']}ms)")
                                    else:
                                        print(f"    ⚠️  {feedback['message']} ({feedback['duration_ms']}ms)")
                                        failed_scrapes += 1
                                else:
                                    # If no database, add to results for JSON output
                                    location_results.append(job_details)
                                
                                job_title = job_details.get('job_title', job_details.get('title', 'N/A'))
                                company_name = job_details.get('company_name', job_details.get('company', 'N/A'))
                                print(f"    ✅ {job_title} at {company_name}")
                            else:
                                print(f"    ❌ Failed to get job details")
                                failed_scrapes += 1
                        except Exception as e:
                            print(f"    ❌ Error getting job details: {str(e)}")
                            failed_scrapes += 1
                        
                        # Small delay between requests to avoid rate limiting
                        if self.async_mode:
                            await asyncio.sleep(2)
                        else:
                            time.sleep(2)
                    
                    # Print summary for this location
                    print(f"  [SUMMARY] Location {location}: {successful_saves} saved, {skipped_existing} skipped, {failed_scrapes} failed")
                    
                    # For reporting purposes, create fake result entries for saved jobs
                    if self.db and successful_saves > 0:
                        # Add placeholder results to represent saved jobs
                        location_results = [{"saved": True}] * successful_saves
                    
                    all_results.extend(location_results)
                    print(f"  [SUCCESS] Found {len(location_results)} jobs in {location}")
                    
                except Exception as e:
                    print(f"  [ERROR] Error searching LinkedIn in {location}: {str(e)}")
                
                # Delay between locations
                if self.async_mode:
                    await asyncio.sleep(3)
                else:
                    time.sleep(3)
            
            print(f"  [TOTAL] LinkedIn total: {len([r for r in all_results if r.get('source') == 'linkedin'])} jobs")
        
        # TODO: Add other scrapers here (Indeed, Glassdoor, etc.)
        
        # Only save JSON if database is not used or explicitly requested
        if not self.use_database and all_results:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.output_dir, f"job_postings_{timestamp}.json")
            
            print(f"\n💾 Saving {len(all_results)} job postings to {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
        elif self.use_database:
            print(f"\n💾 Jobs saved to database only (no JSON output)")
        
        print(f"✅ Job search completed. Found {len(all_results)} job postings!")
        
        # Display final statistics with database breakdown
        if self.db:
            stats = self.db.get_stats()
            print(f"\n📊 Final Database Statistics:")
            print(f"  Total jobs in database: {stats['total_jobs']}")
            print(f"  Jobs by source:")
            for source in stats['by_source']:
                print(f"    - {source['source']}: {source['count']} jobs")
            print(f"  Top companies:")
            for company in stats['top_companies'][:3]:
                print(f"    - {company['company']}: {company['count']} jobs")
        
        # Display session summary
        print(f"\n📈 Session Summary:")
        print(f"  Jobs scraped this session: {len(all_results)}")
        print(f"  Total processing time: {time.time() - start_time:.1f} seconds")
        if all_results:
            print(f"  Average time per job: {(time.time() - start_time) / len(all_results):.1f} seconds")
        
        # Close scrapers and database
        if self.linkedin_scraper:
            try:
                if self.async_mode and hasattr(self.linkedin_scraper, 'close'):
                    await self.linkedin_scraper.close()
                elif hasattr(self.linkedin_scraper, 'close'):
                    self.linkedin_scraper.close()
            except:
                pass
        
        if self.db:
            try:
                self.db.close()
            except:
                pass
        
        return all_results
    
    def export_database_to_json(self, output_file: str = None, limit: int = None) -> str:
        """
        Export database contents to JSON file.
        
        Args:
            output_file: Path to output JSON file. If None, uses timestamped filename
            limit: Maximum number of jobs to export. If None, exports all jobs
            
        Returns:
            Path to the created JSON file
        """
        if not self.db:
            raise ValueError("Database is not initialized. Cannot export to JSON.")
        
        # Get jobs from database
        jobs = self.db.get_jobs(limit=limit or 10000)  # Default to large limit
        
        if not jobs:
            print("⚠️  No jobs found in database to export")
            return None
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.output_dir, f"db_export_{timestamp}.json")
        
        # Convert database rows to JSON-serializable format
        json_jobs = []
        for job in jobs:
            job_dict = dict(job)  # Convert sqlite3.Row to dict
            
            # Parse JSON fields back to objects
            for field in ['job_insights', 'apply_info', 'company_info', 'hiring_team', 'related_jobs']:
                if job_dict.get(field):
                    try:
                        job_dict[field] = json.loads(job_dict[field])
                    except (json.JSONDecodeError, TypeError):
                        pass  # Keep as string if not valid JSON
            
            json_jobs.append(job_dict)
        
        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_jobs, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(json_jobs)} jobs from database to {output_file}")
        return output_file
    def search_and_process(self, export_to_json: bool = False) -> str:
        """
        Run the search pipeline and optionally export to JSON (sync version).
        
        Args:
            export_to_json: Whether to export database contents to JSON after scraping
            
        Returns:
            Path to the JSON file if exported, otherwise None
        """
        results = self.search_jobs()
        
        # Only create JSON if requested or if database is not used
        if export_to_json and self.db:
            return self.export_database_to_json()
        elif not self.use_database and results:
            # Save the results to the standard job_postings.json file
            standard_output = os.path.join(self.output_dir, "job_postings.json")
            with open(standard_output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            return standard_output
        
        return None

    async def search_and_process_async(self, export_to_json: bool = False) -> str:
        """
        Run the search pipeline and optionally export to JSON (async version).
        
        Args:
            export_to_json: Whether to export database contents to JSON after scraping
            
        Returns:
            Path to the JSON file if exported, otherwise None
        """
        results = await self.search_jobs_async()
        
        # Only create JSON if requested or if database is not used
        if export_to_json and self.db:
            return self.export_database_to_json()
        elif not self.use_database and results:
            # Save the results to the standard job_postings.json file
            standard_output = os.path.join(self.output_dir, "job_postings.json")
            with open(standard_output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            return standard_output
        
        return None

def run_job_search(keywords: str, 
                  locations: List[str] = None,
                  job_type: str = None,
                  experience_level: str = None,
                  max_jobs: int = 10,
                  scrapers: List[str] = None,
                  use_database: bool = True,
                  export_to_json: bool = False) -> str:    
    """
    Convenience function to run the job search pipeline.
    
    Args:
        keywords: Job title or keywords to search for
        locations: List of locations to search in
        job_type: Type of job (full-time, contract, etc)
        experience_level: Experience level required
        max_jobs: Maximum number of jobs to collect total
        scrapers: List of scrapers to use
        use_database: Whether to save jobs to database and check for duplicates
        export_to_json: Whether to export database to JSON after scraping
        
    Returns:
        Path to the output JSON file if exported, otherwise None
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
        scrapers=scrapers,
        use_database=use_database
    )
    
    return pipeline.search_and_process(export_to_json=export_to_json)

async def run_job_search_async(keywords: str, 
                              locations: List[str] = None,
                              job_type: str = None,
                              experience_level: str = None,
                              max_jobs: int = 10,
                              scrapers: List[str] = None,
                              use_database: bool = True,
                              export_to_json: bool = False) -> str:    
    """
    Async convenience function to run the job search pipeline.
    
    Args:
        keywords: Job title or keywords to search for
        locations: List of locations to search in
        job_type: Type of job (full-time, contract, etc)
        experience_level: Experience level required
        max_jobs: Maximum number of jobs to collect total
        scrapers: List of scrapers to use
        use_database: Whether to save jobs to database and check for duplicates
        export_to_json: Whether to export database to JSON after scraping
        
    Returns:
        Path to the output JSON file if exported, otherwise None
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
        scrapers=scrapers,
        use_database=use_database,
        async_mode=True  # Enable async mode
    )
    
    return await pipeline.search_and_process_async(export_to_json=export_to_json)

def export_jobs_to_json(output_file: str = None, limit: int = None) -> str:
    """
    Standalone function to export database jobs to JSON.
    
    Args:
        output_file: Path to output JSON file. If None, uses timestamped filename
        limit: Maximum number of jobs to export. If None, exports all jobs
        
    Returns:
        Path to the created JSON file
    """
    db = JobDatabase()
    try:
        # Create temporary pipeline just for export functionality
        pipeline = JobSearchPipeline("", use_database=True)
        pipeline.db = db
        return pipeline.export_database_to_json(output_file, limit)
    finally:
        db.close()
