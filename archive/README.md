# LinkedIn Search Scraper

Comprehensive LinkedIn job scraper with advanced features for extracting rich job data, company information, and hiring team details.

## 🎯 Overview

The LinkedIn scraper is a production-ready tool that extracts complete job information from LinkedIn job postings. It uses Selenium WebDriver to navigate LinkedIn's interface, handle dynamic content loading, and extract comprehensive job data including hidden information not available through public APIs.

### Key Capabilities

- **Complete Job Extraction**: Full job descriptions, requirements, and company details
- **Hiring Team Information**: Recruiter and hiring manager contact details (with login)
- **Company Intelligence**: Company size, industry, about section, and employee insights
- **Related Job Discovery**: Similar positions and career progression opportunities
- **Anti-Detection Technology**: Human-like browsing patterns to avoid blocking
- **Robust Error Handling**: Graceful failure recovery and retry mechanisms

## 📁 Module Files

| File | Purpose | Status |
|------|---------|--------|
| `linkedin_scraper.py` | Main scraper implementation | ✅ Production Ready |
| `search_manager.py` | Multi-platform abstraction layer | ⚠️ Legacy (can be removed) |
| `search_demo.py` | Usage examples and demos | ⚠️ Legacy (can be removed) |

**Recommendation**: Use `linkedin_scraper.py` directly or through the main `extract_linkedin_jobs.py` script.

## 🚀 Quick Start

### Basic Usage

```python
from src.scraper.search.linkedin_scraper import LinkedInScraper

# Initialize scraper
scraper = LinkedInScraper(headless=True)

# Method 1: Get job links first, then extract details
job_links = scraper.collect_job_links(
    keywords="Software Engineer",
    location="Berlin, Germany", 
    max_pages=2
)

# Extract detailed information for each job
for url in job_links[:5]:  # Process first 5 jobs
    job_details = scraper.get_job_details(url)
    print(f"Job: {job_details['title']} at {job_details['company']}")

# Always clean up
scraper.close()
```

### Context Manager (Recommended)

```python
# Automatic cleanup with context manager
with LinkedInScraper(headless=True) as scraper:
    job_links = scraper.collect_job_links("Python Developer", "Remote", max_pages=3)
    
    jobs = []
    for url in job_links:
        try:
            job_data = scraper.get_job_details(url)
            jobs.append(job_data)
        except Exception as e:
            print(f"Failed to extract {url}: {e}")
            continue
    
    print(f"Successfully extracted {len(jobs)} jobs")
```

### Command Line Usage

```bash
# Use the main extraction script (recommended)
python extract_linkedin_jobs.py "Data Scientist" "Berlin" --jobs 20 --headless
```

## 🔧 Configuration

### Constructor Parameters

```python
class LinkedInScraper:
    def __init__(
        self,
        browser_name: str = "chrome",          # Browser choice: chrome/firefox
        headless: bool = True,                 # Run without GUI
        timeout: int = 20,                     # Page load timeout (seconds)
        delay_range: tuple = (1, 3),           # Random delay range (seconds)
        max_retries: int = 3,                  # Retry attempts for failed requests
        debug: bool = False,                   # Enable debug mode
        user_data_dir: str = None,             # Custom browser profile directory
        proxy: str = None                      # Proxy configuration (format: host:port)
    ):
```

### Environment Configuration

Create a `.env` file in the project root:

```env
# LinkedIn Authentication (highly recommended)
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_secure_password

# Scraper Settings
DEFAULT_BROWSER=chrome
HEADLESS_MODE=true
SCRAPER_TIMEOUT=30
DEFAULT_DELAY=2

# Debug Options
ENABLE_DEBUG_SCREENSHOTS=false
ENABLE_ERROR_LOGGING=true
DEBUG_OUTPUT_DIR=output/debug
```

### Browser Configuration

**Chrome (Default)**:
```python
scraper = LinkedInScraper(
    browser_name="chrome",
    headless=True,
    timeout=20
)
```

**Firefox (Fallback)**:
```python
scraper = LinkedInScraper(
    browser_name="firefox", 
    headless=True,
    timeout=20
)
```

**Custom Browser Options**:
```python
# For advanced users - modify browser setup
def custom_chrome_options():
    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return options
```

## 🔍 Core Methods

### 1. Job Link Collection

```python
def collect_job_links(
    self, 
    keywords: str, 
    location: str, 
    max_pages: int = 1,
    date_filter: str = "past-week"
) -> List[str]:
    """
    Collect job URLs from LinkedIn search results.
    
    Args:
        keywords: Job search terms (e.g., "Software Engineer Python")
        location: Location string (e.g., "Berlin, Germany", "Remote")
        max_pages: Maximum search result pages to process
        date_filter: Time filter ("past-week", "past-month", "any-time")
    
    Returns:
        List of LinkedIn job URLs
        
    Example:
        job_urls = scraper.collect_job_links(
            keywords="Machine Learning Engineer",
            location="San Francisco, CA",
            max_pages=5,
            date_filter="past-week"
        )
    """
```

**How it works:**
1. Navigates to LinkedIn jobs search page
2. Applies search filters (keywords, location, date)
3. Intelligently scrolls through the job sidebar to load all jobs
4. Extracts job URLs from each loaded job card
5. Handles pagination to process multiple pages
6. Returns complete list of unique job URLs

### 2. Job Detail Extraction

```python
def get_job_details(self, job_url: str) -> Dict[str, Any]:
    """
    Extract comprehensive job details from a LinkedIn job page.
    
    Args:
        job_url: Direct LinkedIn job posting URL
        
    Returns:
        Dictionary containing complete job information
        
    Example:
        job_data = scraper.get_job_details(
            "https://www.linkedin.com/jobs/view/3785692847"
        )
    """
```

**Extracted Information:**
- **Basic Details**: Title, company, location, job ID
- **Job Content**: Full description, requirements, qualifications
- **Metadata**: Posted date, employment type, seniority level
- **Application Info**: Apply method, external URLs, easy apply status
- **Company Details**: About section, size, industry, website
- **Hiring Team**: Recruiters and hiring managers (with login)
- **Related Opportunities**: Similar jobs at the company
- **Enhanced Data**: Skills, benefits, salary info when available

### 3. Authentication

```python
def login(self, username: str = None, password: str = None) -> bool:
    """
    Login to LinkedIn using provided or environment credentials.
    
    Args:
        username: LinkedIn email (optional, uses .env if not provided)
        password: LinkedIn password (optional, uses .env if not provided)
        
    Returns:
        True if login successful, False otherwise
        
    Example:
        # Using environment variables
        success = scraper.login()
        
        # Using explicit credentials
        success = scraper.login("user@email.com", "password")
    """
```

**Benefits of Authentication:**
- Access to hiring team contact information
- Reduced rate limiting and CAPTCHA frequency
- Complete job descriptions (some truncated without login)
- Company employee insights and connections
- Better success rate for large-scale scraping

## 📊 Data Extraction Details

### Complete Job Object Structure

```json
{
  "url": "https://www.linkedin.com/jobs/view/3785692847",
  "job_id": "3785692847",
  "title": "Senior Software Engineer - Backend",
  "company": "TechCorp Inc",
  "location": "Berlin, Germany",
  "description": "We are looking for a Senior Software Engineer...",
  "requirements": "• 5+ years of Python experience\n• Experience with microservices...",
  "date_posted": "2 weeks ago",
  "employment_type": "Full-time",
  "experience_level": "Mid-Senior level",
  "job_function": "Engineering",
  "industries": ["Technology", "Software Development"],
  
  "job_insights": [
    "Remote work available",
    "Skills match your profile", 
    "Health insurance provided",
    "Professional development budget"
  ],
  
  "easy_apply": false,
  "apply_info": {
    "apply_url": "https://techcorp.com/careers/apply/backend-engineer",
    "application_type": "external",
    "application_deadline": "2025-07-15"
  },
  
  "company_info": {
    "name": "TechCorp Inc",
    "about": "TechCorp is a leading software development company specializing in cloud solutions...",
    "employees": "501-1,000 employees",
    "industry": "Software Development", 
    "headquarters": "Berlin, Germany",
    "website": "https://techcorp.com",
    "logo_url": "https://media.licdn.com/dms/image/C4E0BAQGhp...",
    "specialties": ["Cloud Computing", "Microservices", "DevOps"]
  },
  
  "hiring_team": [
    {
      "name": "John Smith",
      "title": "Engineering Manager",
      "linkedin_url": "https://www.linkedin.com/in/johnsmith",
      "profile_image": "https://media.licdn.com/dms/image/C4E03AQH...",
      "company_tenure": "3 years at TechCorp"
    },
    {
      "name": "Sarah Johnson",
      "title": "Senior Technical Recruiter", 
      "linkedin_url": "https://www.linkedin.com/in/sarahjohnson",
      "profile_image": "https://media.licdn.com/dms/image/C4E03AQG..."
    }
  ],
  
  "related_jobs": [
    {
      "title": "Frontend Engineer",
      "company": "TechCorp Inc",
      "url": "https://www.linkedin.com/jobs/view/3785692848",
      "location": "Berlin, Germany",
      "posted_date": "1 week ago"
    },
    {
      "title": "DevOps Engineer", 
      "company": "TechCorp Inc",
      "url": "https://www.linkedin.com/jobs/view/3785692849",
      "location": "Berlin, Germany",
      "posted_date": "3 days ago"
    }
  ],
  
  "salary_info": {
    "range": "$90,000 - $120,000",
    "currency": "USD",
    "period": "yearly"
  },
  
  "benefits": [
    "Health insurance",
    "Dental insurance", 
    "Remote work options",
    "Stock options",
    "Professional development budget",
    "Flexible working hours"
  ],
  
  "skills_required": [
    "Python",
    "Django",
    "PostgreSQL",
    "AWS",
    "Docker", 
    "Kubernetes",
    "RESTful APIs",
    "Microservices"
  ],
  
  "qualifications": [
    "Bachelor's degree in Computer Science or related field",
    "5+ years of backend development experience",
    "Experience with cloud platforms (AWS, GCP, or Azure)",
    "Strong knowledge of database design and optimization"
  ]
}
```

### Field Availability Matrix

| Field Category | Always Available | Login Required | Sometimes Available |
|----------------|------------------|----------------|-------------------|
| **Basic Info** | ✅ Title, Company, Location | | |
| **Job Content** | ✅ Description, Requirements | | ⚠️ Complete text |
| **Metadata** | ✅ Date, Type, Level | | ⚠️ Function, Industries |
| **Application** | ✅ Easy Apply, URLs | | ⚠️ Deadlines |
| **Company Info** | ✅ About, Size, Industry | | ⚠️ Specialties |
| **Hiring Team** | | ✅ Names, Titles, Profiles | |
| **Related Jobs** | ✅ Similar positions | | |
| **Compensation** | | | ⚠️ Salary ranges |
| **Benefits** | | | ⚠️ Extracted from text |

## 🛡️ Anti-Detection Features

### Human-Like Behavior Simulation

```python
class AntiDetectionMixin:
    def simulate_human_scrolling(self):
        """Scroll page naturally with variable speed and pauses"""
        
    def add_random_mouse_movements(self):
        """Move mouse cursor randomly between actions"""
        
    def variable_typing_speed(self, text: str):
        """Type text with human-like variable speed"""
        
    def random_page_interactions(self):
        """Occasionally interact with page elements naturally"""
```

### Advanced Stealth Techniques

1. **Browser Fingerprinting Avoidance**:
   ```python
   # Remove automation indicators
   options.add_argument("--disable-blink-features=AutomationControlled")
   options.add_experimental_option("excludeSwitches", ["enable-automation"])
   options.add_experimental_option('useAutomationExtension', False)
   
   # Override navigator.webdriver property
   driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
   ```

2. **Request Pattern Randomization**:
   ```python
   def intelligent_delay(self):
       """Smart delay based on page complexity and previous actions"""
       base_delay = random.uniform(*self.delay_range)
       
       # Longer delays for heavy pages
       if self.page_load_time > 5:
           base_delay *= 1.5
           
       # Shorter delays for simple interactions  
       if self.last_action == "scroll":
           base_delay *= 0.7
           
       time.sleep(base_delay)
   ```

3. **Session Management**:
   ```python
   def maintain_session_state(self):
       """Preserve login state and cookies across requests"""
       # Save cookies periodically
       cookies = self.driver.get_cookies()
       
       # Restore session if needed
       if self.session_expired():
           self.restore_cookies(cookies)
   ```

### CAPTCHA Detection & Handling

```python
def detect_captcha(self) -> bool:
    """Detect if CAPTCHA challenge is present"""
    captcha_indicators = [
        "challenge",
        "captcha", 
        "verify",
        "unusual activity",
        "security check"
    ]
    
    page_text = self.driver.page_source.lower()
    return any(indicator in page_text for indicator in captcha_indicators)

def handle_captcha_workflow(self):
    """Interactive CAPTCHA resolution workflow"""
    if self.detect_captcha():
        print("🚨 CAPTCHA detected!")
        print("📝 Please solve the CAPTCHA manually in the browser window")
        print("⏳ Press Enter when completed...")
        
        # Take screenshot for reference
        self.driver.save_screenshot("captcha_screenshot.png")
        print("📸 Screenshot saved as 'captcha_screenshot.png'")
        
        input()  # Wait for user input
        
        # Verify CAPTCHA was solved
        if not self.detect_captcha():
            print("✅ CAPTCHA solved successfully!")
            return True
        else:
            print("❌ CAPTCHA still present. Please try again.")
            return self.handle_captcha_workflow()
```

## 📈 Performance Optimization

### Memory Management

```python
class MemoryOptimizedScraper(LinkedInScraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_urls = set()  # Track processed URLs
        self.batch_size = 25         # Process jobs in batches
        
    def process_jobs_efficiently(self, job_urls: List[str]):
        """Process jobs in memory-efficient batches"""
        for i in range(0, len(job_urls), self.batch_size):
            batch = job_urls[i:i + self.batch_size]
            yield self.process_batch(batch)
            
            # Clear cache between batches
            self.clear_temporary_data()
            
    def clear_temporary_data(self):
        """Clear temporary data to free memory"""
        # Clear browser cache
        self.driver.execute_script("window.localStorage.clear();")
        self.driver.execute_script("window.sessionStorage.clear();")
        
        # Force garbage collection
        import gc
        gc.collect()
```

### Concurrent Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ConcurrentScraper:
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    async def scrape_jobs_concurrently(self, job_urls: List[str]):
        """Process multiple jobs concurrently"""
        loop = asyncio.get_event_loop()
        
        # Create scraper instances for each worker
        scrapers = [LinkedInScraper(headless=True) for _ in range(self.max_workers)]
        
        try:
            # Split URLs among workers
            chunks = [job_urls[i::self.max_workers] for i in range(self.max_workers)]
            
            # Process chunks concurrently
            tasks = [
                loop.run_in_executor(
                    self.executor,
                    self.process_chunk,
                    scraper,
                    chunk
                )
                for scraper, chunk in zip(scrapers, chunks)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Flatten results
            all_jobs = []
            for chunk_results in results:
                all_jobs.extend(chunk_results)
                
            return all_jobs
            
        finally:
            # Clean up all scrapers
            for scraper in scrapers:
                scraper.close()
```

### Caching Strategy

```python
import hashlib
import pickle
from pathlib import Path

class CachedScraper(LinkedInScraper):
    def __init__(self, cache_dir: str = "cache", cache_ttl: int = 3600, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_ttl = cache_ttl
        
    def get_cache_key(self, url: str) -> str:
        """Generate cache key for URL"""
        return hashlib.md5(url.encode()).hexdigest()
        
    def is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file is still valid"""
        if not cache_file.exists():
            return False
            
        age = time.time() - cache_file.stat().st_mtime
        return age < self.cache_ttl
        
    def get_job_details_cached(self, job_url: str) -> Dict[str, Any]:
        """Get job details with caching"""
        cache_key = self.get_cache_key(job_url)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        # Try to load from cache
        if self.is_cache_valid(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                pass  # Cache corrupted, fall through to scraping
        
        # Scrape fresh data
        job_data = self.get_job_details(job_url)
        
        # Save to cache
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(job_data, f)
        except Exception as e:
            logger.warning(f"Failed to cache job data: {e}")
            
        return job_data
```

## 🚨 Error Handling & Recovery

### Retry Mechanisms

```python
import time
from functools import wraps
from typing import Callable, Any

def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator for retrying failed operations with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        break
                        
                    wait_time = delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {wait_time:.1f} seconds..."
                    )
                    time.sleep(wait_time)
            
            raise last_exception
        return wrapper
    return decorator

# Usage example
class RobustLinkedInScraper(LinkedInScraper):
    @retry_on_failure(max_attempts=3, delay=2.0, exceptions=(TimeoutException, WebDriverException))
    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        return super().get_job_details(job_url)
```

### Exception Hierarchy

```python
class LinkedInScrapingError(Exception):
    """Base exception for LinkedIn scraping errors"""
    pass

class LinkedInAuthenticationError(LinkedInScrapingError):
    """Raised when LinkedIn authentication fails"""
    pass

class LinkedInRateLimitError(LinkedInScrapingError):
    """Raised when rate limiting is detected"""
    pass

class LinkedInPageLoadError(LinkedInScrapingError):
    """Raised when page fails to load properly"""
    pass

class LinkedInDataExtractionError(LinkedInScrapingError):
    """Raised when data extraction fails"""
    pass

class LinkedInCaptchaError(LinkedInScrapingError):
    """Raised when CAPTCHA blocks scraping"""
    pass
```

### Recovery Strategies

```python
def handle_common_errors(self, exception: Exception, context: str) -> bool:
    """Handle common scraping errors with appropriate recovery strategies"""
    
    if isinstance(exception, TimeoutException):
        logger.warning(f"Timeout in {context}. Refreshing page...")
        self.driver.refresh()
        time.sleep(5)
        return True
        
    elif isinstance(exception, NoSuchElementException):
        logger.warning(f"Element not found in {context}. Page may have changed layout.")
        self.take_debug_screenshot(f"missing_element_{context}")
        return False
        
    elif isinstance(exception, StaleElementReferenceException):
        logger.warning(f"Stale element in {context}. Re-finding elements...")
        time.sleep(2)
        return True
        
    elif "rate limit" in str(exception).lower():
        wait_time = self.calculate_rate_limit_backoff()
        logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
        time.sleep(wait_time)
        return True
        
    else:
        logger.error(f"Unhandled error in {context}: {exception}")
        return False
```

## 🔍 Debugging & Monitoring

### Debug Mode Features

```python
class DebugLinkedInScraper(LinkedInScraper):
    def __init__(self, debug_dir: str = "debug", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug_mode = True
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(exist_ok=True)
        self.step_counter = 0
        
    def debug_step(self, action: str, details: str = ""):
        """Log and capture debug information for each step"""
        self.step_counter += 1
        timestamp = datetime.now().strftime("%H%M%S")
        
        logger.debug(f"Step {self.step_counter}: {action} - {details}")
        
        # Capture screenshot
        screenshot_path = self.debug_dir / f"step_{self.step_counter:03d}_{timestamp}_{action.replace(' ', '_')}.png"
        self.driver.save_screenshot(str(screenshot_path))
        
        # Save page source if it's an important step
        if action in ["search_results", "job_page", "error"]:
            source_path = self.debug_dir / f"step_{self.step_counter:03d}_{timestamp}_source.html"
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
        
        # Log current URL and page title
        logger.debug(f"Current URL: {self.driver.current_url}")
        logger.debug(f"Page title: {self.driver.title}")
```

### Performance Monitoring

```python
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PerformanceMetrics:
    operation: str
    duration: float
    success: bool
    error_message: str = ""

class PerformanceMonitor:
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        
    @contextmanager
    def measure(self, operation: str):
        """Context manager to measure operation performance"""
        start_time = time.time()
        success = True
        error_msg = ""
        
        try:
            yield
        except Exception as e:
            success = False
            error_msg = str(e)
            raise
        finally:
            duration = time.time() - start_time
            self.metrics.append(PerformanceMetrics(
                operation=operation,
                duration=duration, 
                success=success,
                error_message=error_msg
            ))
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        total_operations = len(self.metrics)
        successful_operations = sum(1 for m in self.metrics if m.success)
        
        avg_duration = sum(m.duration for m in self.metrics) / total_operations if total_operations > 0 else 0
        
        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "average_duration": avg_duration,
            "slowest_operation": max(self.metrics, key=lambda m: m.duration, default=None),
            "failed_operations": [m for m in self.metrics if not m.success]
        }

# Usage example
monitor = PerformanceMonitor()

with monitor.measure("collect_job_links"):
    job_links = scraper.collect_job_links("Engineer", "Berlin", max_pages=3)

with monitor.measure("extract_job_details"):
    for url in job_links:
        scraper.get_job_details(url)

report = monitor.get_performance_report()
print(f"Success rate: {report['success_rate']:.2%}")
print(f"Average operation time: {report['average_duration']:.2f}s")
```

## 🚀 Advanced Usage Patterns

### Batch Processing with Progress Tracking

```python
from tqdm import tqdm
import json

def batch_process_jobs(
    scraper: LinkedInScraper,
    job_urls: List[str],
    batch_size: int = 25,
    output_file: str = "jobs_output.json"
) -> List[Dict[str, Any]]:
    """Process jobs in batches with progress tracking"""
    
    all_jobs = []
    total_batches = (len(job_urls) + batch_size - 1) // batch_size
    
    # Process in batches
    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min((batch_idx + 1) * batch_size, len(job_urls))
        batch_urls = job_urls[start_idx:end_idx]
        
        print(f"\n📦 Processing batch {batch_idx + 1}/{total_batches} ({len(batch_urls)} jobs)")
        
        batch_jobs = []
        for url in tqdm(batch_urls, desc="Extracting jobs"):
            try:
                job_data = scraper.get_job_details(url)
                batch_jobs.append(job_data)
                
                # Save progress after each job
                all_jobs.append(job_data)
                
                # Periodic save to prevent data loss
                if len(all_jobs) % 10 == 0:
                    save_progress(all_jobs, output_file)
                    
            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")
                continue
        
        print(f"✅ Batch {batch_idx + 1} completed: {len(batch_jobs)}/{len(batch_urls)} jobs extracted")
        
        # Break between batches to avoid rate limiting
        if batch_idx < total_batches - 1:
            print("⏳ Waiting 30 seconds before next batch...")
            time.sleep(30)
    
    # Final save
    save_progress(all_jobs, output_file)
    return all_jobs

def save_progress(jobs: List[Dict], filename: str):
    """Save current progress to file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
```

### Job Filtering and Deduplication

```python
def filter_and_deduplicate_jobs(
    jobs: List[Dict[str, Any]],
    filters: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Filter and deduplicate job listings"""
    
    if filters is None:
        filters = {}
    
    # Remove duplicates based on job_id
    seen_ids = set()
    unique_jobs = []
    
    for job in jobs:
        job_id = job.get('job_id')
        if job_id and job_id not in seen_ids:
            seen_ids.add(job_id)
            unique_jobs.append(job)
    
    # Apply filters
    filtered_jobs = []
    for job in unique_jobs:
        # Filter by keywords in title/description
        if 'keywords' in filters:
            keywords = [kw.lower() for kw in filters['keywords']]
            text_to_search = f"{job.get('title', '')} {job.get('description', '')}".lower()
            if not any(keyword in text_to_search for keyword in keywords):
                continue
        
        # Filter by experience level
        if 'experience_levels' in filters:
            job_level = job.get('experience_level', '').lower()
            if not any(level.lower() in job_level for level in filters['experience_levels']):
                continue
        
        # Filter by company size
        if 'company_size' in filters:
            employees = job.get('company_info', {}).get('employees', '')
            # Add logic to parse and filter by company size
        
        # Filter by remote work availability
        if filters.get('remote_only'):
            job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('location', '')}".lower()
            if 'remote' not in job_text:
                continue
        
        filtered_jobs.append(job)
    
    return filtered_jobs

# Usage example
filters = {
    'keywords': ['python', 'machine learning'],
    'experience_levels': ['Senior', 'Mid-Senior'],
    'remote_only': True
}

filtered_jobs = filter_and_deduplicate_jobs(extracted_jobs, filters)
```

### Integration with Data Analysis

```python
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

def analyze_job_market(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Perform market analysis on scraped job data"""
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(jobs)
    
    analysis = {}
    
    # 1. Top companies by job count
    company_counts = df['company'].value_counts().head(10)
    analysis['top_companies'] = company_counts.to_dict()
    
    # 2. Location distribution
    location_counts = df['location'].value_counts().head(10)
    analysis['top_locations'] = location_counts.to_dict()
    
    # 3. Experience level distribution
    experience_counts = df['experience_level'].value_counts()
    analysis['experience_levels'] = experience_counts.to_dict()
    
    # 4. Skills analysis
    all_skills = []
    for job in jobs:
        skills = job.get('skills_required', [])
        all_skills.extend(skills)
    
    skill_counts = Counter(all_skills)
    analysis['top_skills'] = dict(skill_counts.most_common(20))
    
    # 5. Salary analysis (if available)
    salaries = []
    for job in jobs:
        salary_info = job.get('salary_info', {})
        if 'range' in salary_info:
            # Parse salary range and extract numbers
            # Implementation depends on salary format
            pass
    
    # 6. Remote work statistics
    remote_jobs = sum(1 for job in jobs if 'remote' in job.get('location', '').lower())
    analysis['remote_percentage'] = (remote_jobs / len(jobs)) * 100 if jobs else 0
    
    return analysis

def generate_market_report(analysis: Dict[str, Any], output_path: str = "market_report.html"):
    """Generate HTML market analysis report"""
    html_content = f"""
    <html>
    <head><title>Job Market Analysis Report</title></head>
    <body>
        <h1>Job Market Analysis Report</h1>
        
        <h2>Top Companies</h2>
        <ul>
        {''.join(f'<li>{company}: {count} jobs</li>' for company, count in analysis['top_companies'].items())}
        </ul>
        
        <h2>Top Locations</h2>
        <ul>
        {''.join(f'<li>{location}: {count} jobs</li>' for location, count in analysis['top_locations'].items())}
        </ul>
        
        <h2>Most Demanded Skills</h2>
        <ul>
        {''.join(f'<li>{skill}: {count} mentions</li>' for skill, count in analysis['top_skills'].items())}
        </ul>
        
        <h2>Remote Work</h2>
        <p>{analysis['remote_percentage']:.1f}% of jobs offer remote work</p>
    </body>
    </html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Market report saved to {output_path}")
```

## 🔧 Maintenance & Updates

### Selector Resilience

LinkedIn frequently updates their HTML structure. The scraper uses resilient selector strategies:

```python
class ResilientSelectors:
    """Selector patterns that adapt to LinkedIn layout changes"""
    
    JOB_CARD_SELECTORS = [
        ".jobs-search-results__list-item",
        ".job-search-card",
        "[data-job-id]",
        ".jobs-search-two-pane__job-card-container"
    ]
    
    JOB_TITLE_SELECTORS = [
        ".job-details-jobs-unified-top-card__job-title h1",
        ".jobs-unified-top-card__job-title h1", 
        ".job-details-jobs-unified-top-card__job-title",
        ".top-card-layout__title"
    ]
    
    COMPANY_NAME_SELECTORS = [
        ".job-details-jobs-unified-top-card__primary-description-container a",
        ".jobs-unified-top-card__company-name a",
        ".job-details-jobs-unified-top-card__company-name a"
    ]

def find_element_resilient(driver, selectors: List[str], timeout: int = 10):
    """Try multiple selectors until one works"""
    for selector in selectors:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except TimeoutException:
            continue
    
    raise NoSuchElementException(f"None of the selectors worked: {selectors}")
```

### Update Detection

```python
def detect_layout_changes(scraper: LinkedInScraper) -> bool:
    """Detect if LinkedIn has changed their layout"""
    test_elements = [
        (".jobs-search-results__list", "job list"),
        (".job-details-jobs-unified-top-card", "job header"),
        (".jobs-unified-top-card__company-name", "company name")
    ]
    
    missing_elements = []
    for selector, name in test_elements:
        try:
            scraper.driver.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            missing_elements.append(name)
    
    if missing_elements:
        logger.warning(f"Potential layout changes detected. Missing: {', '.join(missing_elements)}")
        return True
    
    return False
```

---

## 📚 Related Documentation

- **[Main Project README](../../../README.md)** - Complete project overview and setup
- **[Scraper Module README](../README.md)** - General scraper architecture and features
- **[API Documentation](../../../docs/ADVANCED_CONFIGURATION.md)** - Advanced configuration options
- **[Development Guide](../../../docs/DEVELOPMENT.md)** - Contributing and development setup

## 🤝 Contributing

Found a bug or want to add a feature? Check our [Development Guide](../../../docs/DEVELOPMENT.md) for:
- Setting up the development environment
- Code style guidelines
- Testing procedures
- Submitting pull requests

## ⚠️ Legal & Ethical Use

This scraper is intended for:
- ✅ Personal job searching and career development
- ✅ Academic research and market analysis
- ✅ Small-scale data collection for legitimate purposes

Please ensure you:
- ❌ Don't violate LinkedIn's Terms of Service
- ❌ Don't overload their servers with excessive requests
- ❌ Don't republish or sell scraped data
- ❌ Don't harvest personal information beyond public job postings

Use responsibly and ethically! 🙏
