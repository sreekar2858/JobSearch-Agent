# LinkedIn Scraper - Modular Structure

This directory contains the modularized LinkedIn job scraper, organized into focused, maintainable components.

## 📁 File Structure

```
linkedin_scraper/
├── __init__.py              # Package initialization and main export
├── scraper.py              # Main LinkedInScraper class interface
├── browser.py              # Browser setup, navigation, retries, scrolling
├── auth.py                 # Login + CAPTCHA logic
├── filters.py              # Search filters and query helpers
├── utils.py                # Helpers: sleep, save HTML, logging, etc.
├── config.py               # Constants like timeout, retries
├── cli.py                  # Command-line interface
└── extractors/
    ├── __init__.py
    ├── job_links.py        # Extract job URLs from listings
    ├── job_details.py      # Extract job metadata from detail page
    └── selectors.py        # Shared CSS/XPath selectors as constants
```

## 🔧 Components

### Core Components

- **`scraper.py`**: Main interface providing the `LinkedInScraper` class with the same API as before
- **`browser.py`**: Handles Chrome/Firefox WebDriver setup, navigation, scrolling, and page structure analysis
- **`auth.py`**: Manages LinkedIn authentication and CAPTCHA detection
- **`filters.py`**: Applies search filters (experience level, date posted, etc.)

### Data Extraction

- **`extractors/job_links.py`**: Extracts job URLs from search result pages with pagination handling
- **`extractors/job_details.py`**: Extracts detailed job information from individual job pages
- **`extractors/selectors.py`**: Centralized CSS/XPath selectors used across extractors

### Utilities

- **`utils.py`**: Common utility functions (sleep, screenshots, text extraction)
- **`config.py`**: Configuration constants and mappings
- **`cli.py`**: Optional command-line interface for standalone usage

## 🚀 Usage

The API remains exactly the same as the original monolithic version:

```python
from src.scraper.search.linkedin_scraper import LinkedInScraper

# Initialize scraper
scraper = LinkedInScraper(headless=True, browser="chrome")

# Collect job links
job_links = scraper.collect_job_links(
    keywords="Software Engineer",
    location="San Francisco",
    max_pages=3,
    experience_levels=["entry_level", "mid_senior"],
    date_posted="past_week"
)

# Get detailed job information
for job_url in job_links:
    job_details = scraper.get_job_details(job_url)
    print(job_details)

# Clean up
scraper.close()
```

## 📋 Command Line Interface

You can also use the CLI for quick searches:

```bash
# Basic search
python -m src.scraper.search.linkedin_scraper.cli "Software Engineer" "San Francisco"

# With filters and job limits
python -m src.scraper.search.linkedin_scraper.cli \
    "Data Scientist" "Remote" \
    --max-pages 5 \
    --max-jobs 20 \
    --experience-levels "mid_senior,director" \
    --date-posted "past_week" \
    --headless

# Only collect job links (faster)
python -m src.scraper.search.linkedin_scraper.cli \
    "Python Developer" "Berlin" \
    --max-jobs 50 \
    --links-only \
    --headless

# Get details for specific job
python -m src.scraper.search.linkedin_scraper.cli \
    --job-url "https://www.linkedin.com/jobs/view/12345678/"
```

## ✅ Benefits of Modular Structure

1. **Maintainability**: Each component has a single responsibility
2. **Testability**: Individual components can be tested in isolation
3. **Reusability**: Components can be reused across different scrapers
4. **Debugging**: Easier to locate and fix issues in specific areas
5. **Extensibility**: Easy to add new extractors or features
6. **Code Organization**: Related functionality is grouped together

## 🔄 Migration Notes

- **No API Changes**: The public interface (`LinkedInScraper` class) remains identical
- **No Algorithm Changes**: All scraping logic has been preserved exactly as-is
- **Backward Compatibility**: Existing code using the scraper will work without modification
- **Import Path**: Still imported from `src.scraper.search.linkedin_scraper`

## 🧪 Testing

The modular structure has been verified to:
- ✅ Import correctly
- ✅ Initialize without errors
- ✅ Maintain all original functionality
- ✅ Preserve the exact same scraping algorithms

## 📝 Development Guidelines

When modifying the scraper:

1. **Selectors**: Add new CSS selectors to `extractors/selectors.py`
2. **Configuration**: Add constants to `config.py`
3. **Utilities**: Add helper functions to `utils.py`
4. **New Extractors**: Create new files in the `extractors/` directory
5. **Browser Logic**: Modify `browser.py` for navigation/scrolling changes
6. **Authentication**: Modify `auth.py` for login-related changes

This structure makes the codebase much more professional and maintainable while preserving all existing functionality.
