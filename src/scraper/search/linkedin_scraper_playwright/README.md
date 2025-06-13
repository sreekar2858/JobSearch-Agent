# LinkedIn Job Scraper - Playwright Implementation

A modern, async-first LinkedIn job scraper built with Playwright. This is a feature-complete migration from the original Selenium implementation, offering better performance, stability, and modern browser automation capabilities.

## 🚀 Features

- **Async/Await Support**: Native async implementation for better performance
- **Multi-Browser Support**: Chromium, Firefox, and WebKit
- **Complete Job Data Extraction**: All fields from the original implementation
- **Search Filters**: Experience levels, date posted, location, etc.
- **CLI Interface**: Command-line tool for easy usage
- **Backwards Compatibility**: Sync wrapper for existing code

## 📁 Project Structure

```
linkedin_scraper_playwright/
├── __init__.py                 # Package exports
├── scraper.py                  # Main scraper classes (async & sync)
├── cli.py                      # Command-line interface
├── browser.py                  # Browser management
├── auth.py                     # LinkedIn authentication
├── filters.py                  # Search filters
├── config.py                   # Configuration constants
├── utils.py                    # Utility functions
├── extractors/                 # Data extraction modules
│   ├── job_links.py           # Job URL extraction
│   ├── job_details.py         # Job details extraction
│   └── selectors.py           # CSS selectors
├── requirements.txt            # Dependencies
├── linkedin_scraper_cli.bat    # Windows CLI runner
└── README.md                   # This documentation
```

## 🔧 Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

3. **Set up environment variables:**
   Create a `.env` file with your LinkedIn credentials:
   ```env
   LINKEDIN_USERNAME=your_email@example.com
   LINKEDIN_PASSWORD=your_password
   ```

## 💻 Usage

### Command Line Interface

**Basic usage:**
```bash
python -m src.scraper.search.linkedin_scraper_playwright.cli "Python Developer" "Berlin"
```

**With filters:**
```bash
python -m src.scraper.search.linkedin_scraper_playwright.cli "Data Scientist" "New York" \
  --experience-levels "entry_level,mid_senior" \
  --date-posted "past_week" \
  --sort-by "recent" \
  --max-jobs 20 \
  --headless
```

**Windows batch script:**
```cmd
linkedin_scraper_cli.bat "Software Engineer" "San Francisco" --max-jobs 10 --headless
```

### CLI Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `keywords` | Job search keywords (required) | `"Python Developer"` |
| `location` | Job location (required) | `"Berlin"` |
| `--max-pages` | Maximum pages to scrape | `--max-pages 3` |
| `--max-jobs` | Maximum jobs to extract | `--max-jobs 50` |
| `--headless` | Run browser in headless mode | `--headless` |
| `--browser` | Browser to use | `--browser firefox` |
| `--timeout` | Timeout in seconds | `--timeout 30` |
| `--output` | Output file path | `--output results.json` |
| `--experience-levels` | Experience levels filter | `--experience-levels "entry_level,mid_senior"` |
| `--date-posted` | Date posted filter | `--date-posted "past_month"` |
| `--sort-by` | Sort results by | `--sort-by "recent"` |
| `--links-only` | Only collect job links | `--links-only` |
| `--job-url` | Get details for specific job | `--job-url "https://linkedin.com/jobs/view/123"` |
| `--sync` | Use synchronous mode | `--sync` |

### Python API

**Async Usage (Recommended):**
```python
import asyncio
from linkedin_scraper_playwright import LinkedInScraper

async def main():
    async with LinkedInScraper(headless=True, browser="chromium") as scraper:
        # Collect job links
        job_links = await scraper.collect_job_links(
            keywords="Python Developer",
            location="Berlin",
            max_pages=2,
            experience_levels=["entry_level", "mid_senior"]
        )
        
        # Get detailed job information
        job_details = await scraper.get_job_details(job_links[0])
        print(job_details)

asyncio.run(main())
```

**Synchronous Usage:**
```python
from linkedin_scraper_playwright import LinkedInScraperSync

scraper = LinkedInScraperSync(headless=True)
try:
    job_links = scraper.collect_job_links(
        keywords="Data Scientist",
        location="New York",
        max_pages=1
    )
    
    for job_url in job_links[:5]:
        job_details = scraper.get_job_details(job_url)
        print(f"{job_details['title']} at {job_details['company']}")
finally:
    scraper.close()
```

## 📊 Output Format

All jobs are extracted with the following fields:

```json
{
  "url": "https://www.linkedin.com/jobs/view/1234567890/",
  "source": "linkedin",
  "scraped_at": "2025-06-13T10:30:45.123456",
  "title": "Senior Python Developer",
  "company": "Tech Company Inc.",
  "description": "Job description...",
  "location": "Berlin, Germany",
  "date_posted": "2 days ago",
  "job_insights": "50+ applicants | Actively reviewing",
  "easy_apply": true,
  "apply_info": "Easy Apply",
  "company_info": "Company description...",
  "hiring_team": "NA",
  "related_jobs": [...]
}
```

**Field Descriptions:**
- `url`: Direct link to the job posting
- `source`: Always "linkedin"
- `scraped_at`: ISO timestamp of when job was scraped
- `title`: Job title
- `company`: Company name
- `description`: Complete job description
- `location`: Job location (or "NA" if not found)
- `date_posted`: When the job was posted (or "NA" if not found)
- `job_insights`: Application insights like applicant count (or "NA" if not found)
- `easy_apply`: Boolean indicating if Easy Apply is available
- `apply_info`: Apply button text or external URL (or "NA" if not found)
- `company_info`: Company description and details (or "NA" if not found)
- `hiring_team`: Hiring team information (or "NA" if not found)
- `related_jobs`: Array of related job suggestions (or "NA" if not found)

## 🎯 Experience Levels

Available experience level filters:
- `internship`
- `entry_level`
- `associate`
- `mid_senior`
- `director`
- `executive`

## 📅 Date Posted Options

- `any_time`
- `past_month`
- `past_week`
- `past_24_hours`

## 🔍 Sort Options

- `relevance` (default)
- `recent`

## 🌐 Browser Support

- `chromium` (default, recommended)
- `firefox`
- `webkit`

## ⚡ Performance Tips

1. **Use headless mode** for faster execution: `--headless`
2. **Limit job count** for quick testing: `--max-jobs 10`
3. **Use Chromium browser** for best performance: `--browser chromium`
4. **Set appropriate timeout** for slow networks: `--timeout 30`

## 🔧 Configuration

The scraper uses the following default settings (configurable via config.py):

- **Default timeout**: 20 seconds
- **Default browser**: Chromium
- **Default headless**: False
- **Scroll attempts**: 20 for job list loading
- **Sleep intervals**: Random delays between 1-3 seconds

## 🐛 Troubleshooting

**Common Issues:**

1. **Login fails**: Verify LinkedIn credentials in `.env` file
2. **Browser not found**: Run `playwright install chromium`
3. **Timeout errors**: Increase timeout with `--timeout 30`
4. **Module import errors**: Ensure you're running from the correct directory

**Debug Mode:**
Add logging to see detailed execution:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 🔄 Migration from Selenium

The Playwright version maintains 100% API compatibility with the Selenium version:

- Same function names and parameters
- Identical output format
- Same CLI arguments
- Drop-in replacement for existing code

**Migration steps:**
1. Replace import: `from linkedin_scraper_playwright import LinkedInScraper`
2. Use async/await or sync wrapper as needed
3. Update browser parameter from `"chrome"` to `"chromium"`

## 📈 Performance Comparison

| Metric | Selenium | Playwright |
|--------|----------|------------|
| Job extraction speed | ~3-5 sec/job | ~2-3 sec/job |
| Memory usage | Higher | Lower |
| Browser startup | ~5-8 seconds | ~2-4 seconds |
| Stability | Good | Excellent |
| Modern browser features | Limited | Full support |

## 🤝 Contributing

1. Follow the existing code structure
2. Add proper async/await support
3. Include error handling
4. Update selectors if LinkedIn changes
5. Test with both async and sync APIs

## 📄 License

This project follows the same license as the main repository.
        # Collect job links
        job_links = await scraper.collect_job_links(
            keywords="Python Developer",
            location="San Francisco, CA",
            max_pages=2
        )
        
        # Get detailed job information
        for url in job_links[:5]:
            job_details = await scraper.get_job_details(url)
            print(f"Title: {job_details.get('title')}")
            print(f"Company: {job_details.get('company')}")

asyncio.run(main())
```

### Synchronous Usage (Backwards Compatibility)
```python
from linkedin_scraper_playwright import LinkedInScraperSync

scraper = LinkedInScraperSync(headless=True, browser="chromium")
try:
    job_links = scraper.collect_job_links(
        keywords="Data Scientist",
        location="New York, NY",
        max_pages=1
    )
    
    for url in job_links[:3]:
        job_details = scraper.get_job_details(url)
        print(f"Title: {job_details.get('title')}")
finally:
    scraper.close()
```

### Command Line Interface (CLI)

The Playwright version includes a powerful CLI that matches the Selenium version's functionality:

#### Quick Start
```bash
# Windows
linkedin_scraper_cli.bat "Python Developer" "San Francisco, CA" --max-pages 2 --headless

# Linux/macOS
./linkedin_scraper_cli.sh "Python Developer" "San Francisco, CA" --max-pages 2 --headless

# Direct Python
python run_cli.py "Data Scientist" "Remote" --experience-levels "entry_level,associate" --date-posted "past_week"
```

#### CLI Features
- **Same arguments** as Selenium version with additional browser options
- **Async and sync modes** for different use cases
- **Enhanced output** with emojis and better progress indication
- **Multiple browser support** (chromium, firefox, webkit)
- **Flexible output options** with auto-generated filenames

#### Common CLI Usage
```bash
# Basic search
python run_cli.py "Software Engineer" "Seattle, WA"

# Advanced filtering
python run_cli.py "ML Engineer" "Remote" \
  --experience-levels "associate,mid_senior" \
  --date-posted "past_month" \
  --sort-by "recent" \
  --max-jobs 20 \
  --headless

# Links only (faster)
python run_cli.py "DevOps" "Austin, TX" --links-only --max-pages 5

# Specific job details
python run_cli.py --job-url "https://www.linkedin.com/jobs/view/1234567890/"
```

For complete CLI documentation, see [CLI_USAGE.md](CLI_USAGE.md).

## Configuration

### Browser Options
- `browser`: Choose from "chromium", "firefox", or "webkit"
- `headless`: Run in headless mode (default: False)
- `timeout`: Timeout for operations in milliseconds (default: 20000)

### Environment Variables
The same environment variables are required as the Selenium version:
```
LINKEDIN_USERNAME=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
```

## Dependencies

### Required Packages
```bash
pip install playwright python-dotenv
playwright install  # Install browser binaries
```

### Optional for specific browsers
```bash
playwright install chromium  # For Chromium support
playwright install firefox   # For Firefox support
playwright install webkit    # For WebKit/Safari support
```

## Migration from Selenium Version

The Playwright version maintains API compatibility with the Selenium version:

1. **Same method signatures**: All public methods have identical signatures
2. **Same configuration**: Environment variables and initialization parameters are unchanged
3. **Same output format**: Job data structures and return types are identical
4. **Same filtering options**: Experience levels, date filters, and sorting work the same way

### Key Changes for Migration
- Import from `linkedin_scraper_playwright` instead of `linkedin_scraper`
- Use async/await for the main API or use the `LinkedInScraperSync` wrapper
- Handle async context managers if using the async API

## Performance Considerations

### Async Benefits
- **Concurrent operations**: Can handle multiple browser operations simultaneously
- **Better resource utilization**: Non-blocking I/O operations
- **Improved reliability**: Better handling of network timeouts and retries

### Memory Usage
- Playwright generally uses less memory than Selenium
- Better garbage collection due to native async support
- More efficient browser process management

## Error Handling

The error handling strategy remains the same:
- Graceful degradation when elements are not found
- Retry mechanisms for network-related failures
- Comprehensive logging for debugging
- CAPTCHA detection and handling

## Browser-Specific Notes

### Chromium (Recommended)
- Best compatibility with LinkedIn's dynamic content
- Fastest execution time
- Most stable for automation

### Firefox
- Good alternative to Chromium
- Slightly slower but more privacy-focused
- Good for environments where Chromium is not available

### WebKit
- macOS Safari engine
- Useful for testing Safari compatibility
- May have some limitations with complex JavaScript

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Screenshot Capture
Screenshots are automatically saved to `output/linkedin/` when errors occur or CAPTCHAs are detected.

### Browser Developer Tools
When running in non-headless mode, you can inspect the browser and use developer tools for debugging.

## Known Limitations

1. **LinkedIn Rate Limiting**: Same limitations as Selenium version
2. **CAPTCHA Handling**: Manual intervention may be required
3. **Dynamic Content**: Some elements may require additional wait times
4. **Browser Dependencies**: Requires Playwright browser binaries

## Contributing

When contributing to the Playwright version:
1. Maintain API compatibility with the Selenium version
2. Use async/await patterns consistently
3. Include proper error handling and logging
4. Test with multiple browsers when possible
5. Update this README for any significant changes
