# LinkedIn Scraper Guide

Complete guide for using the LinkedIn job scraper to extract comprehensive job information.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Basic job search
python extract_linkedin_jobs.py "Software Engineer" "Berlin" --jobs 10

# Advanced search with authentication
python extract_linkedin_jobs.py "Data Scientist" "Remote" --login --pages 3 --headless
```

## Requirements

- Python 3.10+
- Chrome or Firefox browser
- LinkedIn credentials (recommended)
- Stable internet connection

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure LinkedIn credentials (optional but recommended):
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## Usage

### Command Line Interface

```bash
python extract_linkedin_jobs.py [keywords] [location] [options]
```

#### Arguments

**Positional Arguments:**
- `keywords`: Job search terms (required)
- `location`: Job location (required)

**Optional Arguments:**
- `--jobs N`: Maximum number of jobs to extract
- `--pages N`: Maximum pages to scrape (default: 1)
- `--headless`: Run browser in background
- `--browser {chrome,firefox}`: Choose browser (default: chrome)
- `--login`: Use LinkedIn authentication

#### Examples

```bash
# Basic search
python extract_linkedin_jobs.py "Python Developer" "New York"

# Limit to 20 jobs
python extract_linkedin_jobs.py "DevOps Engineer" "Berlin" --jobs 20

# Multiple pages with headless browser
python extract_linkedin_jobs.py "Machine Learning" "Remote" --pages 5 --headless

# With authentication for better results
python extract_linkedin_jobs.py "Backend Engineer" "London" --login --jobs 25

# Using Firefox browser
python extract_linkedin_jobs.py "Frontend Developer" "Amsterdam" --browser firefox
```

## Authentication

### Setting Up LinkedIn Credentials

Create a `.env` file with your LinkedIn credentials:

```env
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

### Benefits of Authentication

- **Complete Job Descriptions**: Access full job details
- **Hiring Team Information**: See recruiter and hiring manager profiles
- **Related Jobs**: Get job recommendations
- **Reduced Rate Limiting**: Better success rates
- **Company Details**: Access detailed company information

## How It Works

### Scraping Process

1. **Login** (if credentials provided): Authenticates with LinkedIn
2. **Search Navigation**: Goes to job search with your keywords/location
3. **Intelligent Scrolling**: Loads all jobs from the sidebar (25+ per page)
4. **URL Collection**: Extracts individual job page URLs
5. **Detail Extraction**: Visits each job page for complete information
6. **Rich Data Parsing**: Extracts company info, hiring team, related jobs
7. **JSON Export**: Saves structured data for processing

### Anti-Detection Features

- **Human-like Behavior**: Random delays and realistic mouse movements
- **Browser Fingerprinting**: Uses real browser instances, not headless-only
- **Rate Limiting**: Intelligent backoff when rate limits are hit
- **CAPTCHA Handling**: Pauses for manual intervention when needed
- **Session Management**: Maintains login state across requests

## Output Format

Jobs are saved as JSON files in `output/linkedin/` with comprehensive metadata:

```json
{
  "url": "https://www.linkedin.com/jobs/view/4196291618/",
  "source": "linkedin",
  "scraped_at": "2025-06-11T23:15:37.916308",
  "title": "Senior Software Engineer",
  "company": "TechCorp Inc",
  "location": "Berlin, Germany",
  "description": "Full job description with requirements and responsibilities...",
  "date_posted": "1 week ago",
  "job_insights": [
    "On-site Full-time Mid-Senior level",
    "See how you compare to 82 others who clicked apply"
  ],
  "easy_apply": false,
  "apply_info": "https://techcorp.com/careers/apply/...",
  "company_info": "About the company\nTechCorp Inc\n500+ employees...",
  "hiring_team": [
    {
      "name": "John Smith",
      "title": "Engineering Manager",
      "linkedin_url": "https://linkedin.com/in/johnsmith",
      "connection_degree": "3rd+"
    }
  ],
  "related_jobs": [
    {
      "title": "Frontend Developer",
      "company": "StartupCorp",
      "location": "Berlin, Germany",
      "url": "https://www.linkedin.com/jobs/view/...",
      "posted_date": "2 days ago",
      "insights": ["Remote", "Full-time", "Easy Apply"]
    }
  ]
}
```

### Data Fields Explained

#### Basic Information
- `url`: Direct link to the job posting
- `source`: Always "linkedin" for this scraper
- `scraped_at`: ISO timestamp of when the job was scraped
- `title`: Job title as posted
- `company`: Company name
- `location`: Job location (city, state/country)

#### Job Details
- `description`: Complete job description with requirements
- `date_posted`: When the job was posted (e.g., "1 week ago")
- `job_insights`: Array of job characteristics (remote, full-time, etc.)

#### Application Information
- `easy_apply`: Boolean indicating if LinkedIn Easy Apply is available
- `apply_info`: Either "Easy Apply" or external application URL

#### Company Information
- `company_info`: Detailed company description and statistics
- `hiring_team`: Array of recruiter/hiring manager information

#### Related Content
- `related_jobs`: Array of similar job postings with details

## Rate Limits & Best Practices

### LinkedIn Limits

- **Free Accounts**: ~1000 jobs per search query
- **Pages**: Maximum ~40 pages per search (25 jobs each)
- **Commercial Use**: ~300 monthly searches before hitting commercial limits
- **Profile Views**: Limited profile views for non-connections

### Recommended Practices

1. **Use Authentication**: Significantly improves success rates
2. **Reasonable Limits**: Don't exceed 50-100 jobs per session
3. **Delay Between Searches**: Wait 5-10 minutes between different searches
4. **Monitor for CAPTCHAs**: Be ready to solve verification challenges
5. **Respect Terms of Service**: Use responsibly and ethically

### Avoiding Rate Limits

```bash
# Good: Reasonable job limit
python extract_linkedin_jobs.py "Engineer" "Berlin" --jobs 25

# Better: Use authentication
python extract_linkedin_jobs.py "Engineer" "Berlin" --jobs 25 --login

# Best: Add delays between different searches manually
python extract_linkedin_jobs.py "Software Engineer" "Berlin" --jobs 20 --login
# Wait 5-10 minutes before next search
python extract_linkedin_jobs.py "Data Scientist" "Munich" --jobs 20 --login
```

## Troubleshooting

### Common Issues

#### Login Failed
```bash
# Check your .env file
LINKEDIN_USERNAME=your_actual_email@example.com
LINKEDIN_PASSWORD=your_actual_password

# Make sure the file is in the root directory
ls -la .env
```

#### Browser Issues
```bash
# Try Firefox if Chrome fails
python extract_linkedin_jobs.py "Engineer" "Berlin" --browser firefox

# Update browser drivers
pip install --upgrade webdriver-manager selenium
```

#### Rate Limiting / CAPTCHAs
```bash
# Use smaller job limits
python extract_linkedin_jobs.py "Engineer" "Berlin" --jobs 10

# Enable authentication
python extract_linkedin_jobs.py "Engineer" "Berlin" --jobs 10 --login

# Wait between searches (manually)
```

#### No Jobs Found
```bash
# Try broader keywords
python extract_linkedin_jobs.py "Engineer" "Berlin" --jobs 10

# Try different location format
python extract_linkedin_jobs.py "Software Engineer" "Germany" --jobs 10
```

#### Browser Won't Start
```bash
# Check if browser is installed
google-chrome --version
firefox --version

# Try headless mode
python extract_linkedin_jobs.py "Engineer" "Berlin" --headless --jobs 5
```

### Debug Mode

For troubleshooting, you can run without headless mode to see what's happening:

```bash
# Run with visible browser for debugging
python extract_linkedin_jobs.py "Software Engineer" "Berlin" --jobs 5
```

This allows you to:
- See login process
- Manually solve CAPTCHAs
- Observe the scraping process
- Identify where issues occur

### Error Messages

**"LinkedIn credentials are REQUIRED but not found!"**
- Solution: Create `.env` file with your LinkedIn credentials

**"Could not initialize any browser"**
- Solution: Install Chrome or Firefox, or update webdriver-manager

**"CAPTCHA detected. Waiting for manual resolution..."**
- Solution: Solve the CAPTCHA in the browser window, then press Enter

**"No job cards found in sidebar"**
- Solution: Try different keywords or location, or check if LinkedIn layout changed

## Programmatic Usage

You can also use the scraper programmatically in Python:

```python
from src.scraper.search.linkedin_scraper import LinkedInScraper

# Initialize scraper
scraper = LinkedInScraper(headless=True)

try:
    # Collect job links
    job_links = scraper.collect_job_links(
        keywords="Python Developer",
        location="Berlin",
        max_pages=2
    )
    
    # Extract details for each job
    jobs = []
    for url in job_links[:10]:  # Limit to first 10
        job_details = scraper.get_job_details(url)
        jobs.append(job_details)
    
    print(f"Extracted {len(jobs)} jobs")

finally:
    scraper.close()
```

## Advanced Configuration

### Custom Browser Options

```python
from src.scraper.search.linkedin_scraper import LinkedInScraper

# Custom configuration
scraper = LinkedInScraper(
    headless=False,
    timeout=30
)

# Use different browser profiles, proxy settings, etc.
```

### Filtering Options

The scraper supports basic filtering through LinkedIn's interface:

```python
job_links = scraper.collect_job_links(
    keywords="Software Engineer",
    location="Berlin",
    max_pages=3,
    experience_levels=['mid_senior', 'director'],  # Future feature
    date_posted='past_week'                        # Future feature
)
```

## Legal and Ethical Considerations

### Terms of Service

- **Respect LinkedIn's ToS**: Use the scraper responsibly
- **Rate Limiting**: Don't overwhelm LinkedIn's servers
- **Personal Use**: Intended for individual job search, not commercial scraping
- **Data Usage**: Only use scraped data for personal job applications

### Best Practices

1. **Don't abuse the system**: Reasonable request rates only
2. **Respect robots.txt**: LinkedIn's technical guidelines
3. **Personal use only**: Don't resell or redistribute scraped data
4. **Keep credentials secure**: Never share your LinkedIn login details

## Updates and Maintenance

The LinkedIn scraper is regularly updated to handle:

- **Layout Changes**: LinkedIn UI updates
- **New Features**: Additional data extraction capabilities
- **Bug Fixes**: Improvements to reliability and performance
- **Anti-Detection**: Enhanced techniques to avoid blocking

### Version History

- **v2.1 (June 2025)**: Restored rich output format, enhanced extraction
- **v2.0 (May 2025)**: Complete rewrite with new selectors
- **v1.5**: Added authentication support
- **v1.0**: Initial release

For the latest updates, check the GitHub repository and release notes.
