# BugMeNot Scraper

Advanced Python scraper to extract login credentials with metadata from bugmenot.com

## Features
- 🔍 **Credential Extraction** - Username and password pairs
- 📊 **Metadata Collection** - Success rates, vote counts, and credential age
- 🖥️ **Command-Line Interface** - Easy to use with arguments
- 🎯 **Interactive Mode** - User-friendly prompts
- 💾 **JSON Export** - Structured data output
- 🌐 **Browser Support** - Headless or visible browser modes

## Files
- `bugmenot_scraper.py` - Main scraper class with enhanced HTML parsing
- `cli.py` - Command-line interface and interactive mode
- `requirements.txt` - Python dependencies

## Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install browser for Playwright
playwright install chromium
```

## Usage

### Command Line (Recommended)
```bash
# Basic usage
python cli.py --website glassdoor.com --output credentials.json

# Show browser window
python cli.py --website nytimes.com --visible

# Don't save to file
python cli.py --website wsj.com --no-save

# Get help
python cli.py --help
```

### Interactive Mode
```bash
python cli.py
```

### Programmatic Usage
```python
from bugmenot_scraper import BugMeNotScraper
import asyncio

async def main():
    scraper = BugMeNotScraper(headless=True)
    credentials = await scraper.scrape("glassdoor.com")
    
    for cred in credentials:
        print(f"Username: {cred['username']}")
        print(f"Password: {cred['password']}")
        print(f"Success Rate: {cred['success_rate']}%")
        print(f"Votes: {cred['votes']}")
        print(f"Age: {cred['age']}")
        print("-" * 40)

asyncio.run(main())
```

### Quick Functions
```python
from bugmenot_scraper import get_credentials
import asyncio

# Get credentials for one website
credentials = asyncio.run(get_credentials("nytimes.com"))

# Get credentials for multiple websites
websites = ["nytimes.com", "wsj.com", "economist.com"]
all_credentials = asyncio.run(get_multiple_credentials(websites))
```

## Output Format

The scraper outputs JSON files with the following structure:

```json
[
  {
    "website": "glassdoor.com",
    "username": "example@email.com",
    "password": "password123",
    "success_rate": 88,
    "votes": 84,
    "age": "9 months old",
    "scraped_at": "2025-06-13T10:45:02.294185"
  }
]
```

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--website` | `-w` | Website to scrape credentials for |
| `--output` | `-o` | Output JSON filename |
| `--visible` | `-v` | Show browser window |
| `--no-save` | | Don't save results to file |
| `--help` | `-h` | Show help message |

## Examples

```bash
# Save glassdoor credentials to a specific file
python cli.py --website glassdoor.com --output latest.json

# Scrape with visible browser (useful for debugging)
python cli.py --website nytimes.com --visible

# Quick scraping without saving
python cli.py --website wsj.com --no-save
```

## Notes

- The scraper uses Playwright to handle dynamic content
- Results are automatically deduplicated
- Credentials are validated before inclusion
- Rate limiting is implemented for multiple website scraping
- Browser can run in headless mode (default) or visible mode
