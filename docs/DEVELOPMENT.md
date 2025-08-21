# Development Guide

This guide helps contributors understand the codebase and contribute effectively to the JobSearch Agent project.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Chrome or Firefox browser
- Code editor (VS Code recommended)

### Local Development

1. **Clone and setup**:
```bash
git clone https://github.com/sreekar2858/JobSearch-Agent.git
cd JobSearch-Agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r dev-requirements.txt  # Development dependencies
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials and API keys
```

3. **Run tests**:
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_job_parser.py

# Run with coverage
python -m pytest --cov=src
```

## Project Architecture

### Core Pipeline Architecture

The project uses a **unified pipeline architecture** centered around `src/utils/job_search_pipeline.py`:

```python
# Single unified class supporting both execution modes
class JobSearchPipeline:
    def __init__(self, async_mode=False, ...):
        # Initialize with sync or async scrapers based on mode
        
    def search_jobs(self):              # Synchronous execution
    async def search_jobs_async(self):  # Asynchronous execution

# Convenience functions for both modes
def run_job_search(...):              # For CLI/scripts  
async def run_job_search_async(...):  # For FastAPI/web services
```

**Key Benefits:**
- Single source of truth eliminates code duplication
- Consistent behavior between CLI and API modes  
- Easier maintenance and testing
- Backward compatibility maintained

### Directory Structure

```
JobSearch-Agent/
├── src/                          # Source code
│   ├── agents/                   # AI agents
│   │   ├── job_details_parser.py
│   │   ├── cv_writer.py
│   │   └── coverLetter_writer.py
│   ├── scraper/                  # Web scraping
│   │   └── search/
│   │       └── linkedin_scraper.py
│   ├── prompts/                  # AI prompts
│   ├── utils/                    # Utilities
│   └── api/                      # API endpoints
├── tests/                        # Test files
├── config/                       # Configuration
├── data/                         # Templates and data
├── output/                       # Generated outputs
└── docs/                         # Documentation
```

### Core Components

#### LinkedIn Scraper (`src/scraper/search/linkedin_scraper.py`)

```python
class LinkedInScraper:
    """Main scraper class for LinkedIn job extraction."""
    
    def __init__(self, browser_name="chrome", headless=True):
        """Initialize scraper with browser configuration."""
        
    def search_jobs(self, keywords: str, location: str) -> List[str]:
        """Search for jobs and return job URLs."""
        
    def collect_job_links(self, max_jobs: int = None) -> List[str]:
        """Scroll through sidebar and collect all job links."""
        
    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """Extract complete job details from job page."""
```

**Key Methods:**
- `_setup_browser()`: Configure browser with anti-detection
- `_login()`: Handle LinkedIn authentication
- `_scroll_jobs_sidebar()`: Intelligent sidebar scrolling
- `_extract_job_data()`: Parse job page content
- `_extract_hiring_team()`: Get recruiter information
- `_extract_company_info()`: Company details extraction

#### AI Agents (`src/agents/`)

**Job Parser Agent**:
```python
class JobParsr(BaseAgent):
    """Parses unstructured job text into structured data."""
    
    def __init__(self):
        # Initialize with multiple specialized agents
        self.parsing_agent = create_parse_bulk_text_agent()
        
    async def parse_job(self, job_text: str) -> Dict[str, Any]:
        """Parse job description into structured format."""
```

**CV Writer Agent**:
```python
class CVWriter(BaseAgent):
    """Multi-agent system for CV generation."""
    
    def __init__(self):
        # Agent pipeline: Draft -> Critique -> Revise -> Grammar -> Final
        self.initial_draft = create_initial_draft_agent()
        self.critic = create_critic_agent()
        self.reviser = create_reviser_agent()
        self.grammar_check = create_grammar_check_agent()
        self.final_draft = create_final_draft_agent()
```

### Design Patterns

#### Agent Factory Pattern

```python
def create_initial_draft_agent():
    """Factory function to create draft agent with fresh state."""
    return LlmAgent(
        name="InitialDrafter",
        model=get_configured_model("initial_draft_model"),
        instruction=initial_draft_prompt,
        input_schema=None,
        output_key="initial_draft",
    )
```

#### Multi-Agent Pipeline

```python
class CVWriter(BaseAgent):
    def __init__(self):
        # Sequential processing with loop for iteration
        loop_agent = LoopAgent(
            sub_agents=[critic, reviser, ExitConditionAgent()],
            max_iterations=MAX_LOOP_ITERATIONS,
        )
        
        # Final processing pipeline
        sequential_agent = SequentialAgent(
            sub_agents=[grammar_check, final_draft],
        )
```

## Contributing Guidelines

### Code Style

We follow PEP 8 with these specific guidelines:

```python
# Good: Clear function names with type hints
def extract_job_details(self, job_url: str) -> Dict[str, Any]:
    """Extract comprehensive job details from LinkedIn job page."""
    pass

# Good: Descriptive variable names
hiring_team_members = []
company_info = {}

# Good: Constants in uppercase
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 20
```

### Testing

#### Test Structure

```python
# tests/test_linkedin_scraper.py
import pytest
from unittest.mock import Mock, patch
from src.scraper.search.linkedin_scraper import LinkedInScraper

class TestLinkedInScraper:
    def setup_method(self):
        """Setup for each test method."""
        self.scraper = LinkedInScraper(headless=True)
    
    @patch('selenium.webdriver.Chrome')
    def test_job_search(self, mock_chrome):
        """Test job search functionality."""
        # Test implementation
        pass
    
    def test_job_detail_extraction(self):
        """Test job detail parsing."""
        # Test implementation
        pass
```

#### Running Tests

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test class
python -m pytest tests/test_linkedin_scraper.py::TestLinkedInScraper

# Run with coverage report
python -m pytest --cov=src --cov-report=html
```

### Adding New Features

#### Adding a New Job Board

1. **Create scraper class**:
```python
# src/scraper/search/indeed_scraper.py
class IndeedScraper(BaseScraper):
    def search_jobs(self, keywords: str, location: str) -> List[str]:
        """Implementation for Indeed job search."""
        pass
```

2. **Add configuration**:
```yaml
# config/jobsearch_config.yaml
scrapers:
  indeed:
    base_url: "https://indeed.com"
    search_endpoint: "/jobs"
    selectors:
      job_card: ".jobsearch-SerpJobCard"
      job_title: ".jobTitle a"
```

3. **Write tests**:
```python
# tests/test_indeed_scraper.py
class TestIndeedScraper:
    def test_job_search(self):
        pass
```

#### Adding New AI Agent

1. **Create agent class**:
```python
# src/agents/salary_analyzer.py
class SalaryAnalyzer(BaseAgent):
    def __init__(self):
        super().__init__(name="SalaryAnalyzer")
    
    async def analyze_salary(self, job_data: Dict) -> Dict[str, Any]:
        """Analyze salary information from job data."""
        pass
```

2. **Add prompts**:
```python
# src/prompts/salary_prompts.py
salary_analysis_prompt = """
Analyze the salary information from the job posting...
"""
```

3. **Update configuration**:
```yaml
# config/cv_app_agent_config.yaml
agents:
  salary_analyzer:
    model: "gemini_2.5_flash"
    enabled: true
```

### Error Handling

#### Standard Error Patterns

```python
class LinkedInScrapingError(Exception):
    """Custom exception for LinkedIn scraping errors."""
    pass

def extract_job_details(self, job_url: str) -> Dict[str, Any]:
    try:
        # Extraction logic
        return job_data
    except TimeoutException:
        logger.error(f"Timeout while loading job page: {job_url}")
        raise LinkedInScrapingError(f"Failed to load job: {job_url}")
    except Exception as e:
        logger.error(f"Unexpected error extracting job {job_url}: {e}")
        raise
```

#### Retry Logic

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return wrapper
    return decorator
```

## Debugging

### Debug Mode

Enable debug mode for detailed logging:

```python
# Set environment variable
import os
os.environ['DEBUG'] = '1'

# Or in .env file
DEBUG=1
```

### Common Debug Scenarios

#### Scraper Issues

```python
# Enable debug screenshots
scraper = LinkedInScraper(debug=True)

# Manual debugging
scraper.driver.save_screenshot("debug.png")
with open("debug.html", "w") as f:
    f.write(scraper.driver.page_source)
```

#### AI Agent Issues

```python
# Debug agent responses
import logging
logging.getLogger('agents').setLevel(logging.DEBUG)

# Print intermediate results
for event in agent.run_async(context):
    print(f"Agent: {event.author}, Content: {event.content}")
```

## Release Process

### Version Management

We use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Steps

1. **Update version**:
```python
# __init__.py
__version__ = "2.1.0"
```

2. **Update CHANGELOG.md**:
```markdown
## [2.1.0] - 2025-06-15
### Added
- New Indeed scraper support
- Enhanced error handling
### Fixed
- Memory leak in browser management
```

3. **Create release**:
```bash
git tag v2.1.0
git push origin v2.1.0
```

## Performance Guidelines

### Memory Management

```python
# Good: Clean up browser resources
def __exit__(self, exc_type, exc_val, exc_tb):
    if self.driver:
        self.driver.quit()

# Good: Use generators for large datasets
def process_jobs(self, job_urls: List[str]):
    for url in job_urls:
        yield self.extract_job_details(url)
```

### Optimization Tips

- Use headless browsers for production
- Implement connection pooling for databases
- Cache frequently accessed data
- Use async/await for I/O operations
- Profile code with cProfile for bottlenecks

## Security Considerations

### Credential Management

```python
# Good: Environment variables
username = os.getenv('LINKEDIN_USERNAME')

# Bad: Hardcoded credentials
username = 'myemail@example.com'  # Never do this
```

### Input Validation

```python
def validate_job_url(url: str) -> bool:
    """Validate LinkedIn job URL format."""
    pattern = r'https://www\.linkedin\.com/jobs/view/\d+'
    return bool(re.match(pattern, url))
```

### Rate Limiting

```python
import time
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def wait_if_needed(self):
        now = datetime.now()
        # Remove old requests outside time window
        self.requests = [req for req in self.requests 
                        if now - req < timedelta(seconds=self.time_window)]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]).seconds
            time.sleep(sleep_time)
        
        self.requests.append(now)
```
