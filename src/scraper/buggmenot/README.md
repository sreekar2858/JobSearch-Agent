# BugMeNot Scraper

Advanced Python scraper to extract login credentials with metadata from bugmenot.com using Playwright browser automation.

## 🚀 Key Features

- **🔍 Credential Extraction**: Username and password pairs with comprehensive metadata
- **📊 Metadata Collection**: Success rates, vote counts, and credential age tracking
- **💻 Modern CLI Interface**: Non-interactive, argument-driven command-line tool
- **🛡️ Anonymization & Stealth**: Random user agents, browser fingerprinting protection
- **🔗 Proxy Support**: HTTP and SOCKS5 proxy configuration
- **🌐 Multi-Browser Support**: Chromium, Firefox, and WebKit compatibility
- **💾 JSON Export**: Structured data output with timestamps
- **📦 Module Execution**: Support for `python -m` execution
- **🎯 Robust Extraction**: Enhanced parsing with error handling

## 📁 Project Structure

```
buggmenot/
├── __init__.py                 # Package exports
├── __main__.py                 # Module execution entry point
├── bugmenot_scraper.py         # Main scraper class with enhanced parsing
├── cli.py                      # Command-line interface (non-interactive)
└── README.md                   # This documentation
```

## 🔧 Installation

1. **Install dependencies** (from project root):
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   # Optional: install other browsers
   playwright install firefox webkit
   ```

## 💻 Usage

### Command Line Interface

**Basic usage (from project root):**
```bash
# Modern module execution
python -m src.scraper.buggmenot glassdoor.com

# With output file
python -m src.scraper.buggmenot nytimes.com --output credentials.json

# With browser and anonymization options
python -m src.scraper.buggmenot wsj.com \
  --browser firefox \
  --proxy "http://proxy:8080" \
  --no-anonymize \
  --visible

# Legacy CLI execution
python src/scraper/buggmenot/cli.py glassdoor.com --output results.json
```

### CLI Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `website` | Website to scrape (required) | `glassdoor.com` |
| `--output` | Output JSON filename | `--output credentials.json` |
| `--browser` | Browser to use | `--browser firefox` |
| `--proxy` | Proxy server (HTTP/SOCKS5) | `--proxy http://proxy:8080` |
| `--no-anonymize` | Disable anonymization | `--no-anonymize` |
| `--visible` | Show browser window | `--visible` |
| `--timeout` | Timeout in seconds | `--timeout 30` |

### Python API Usage

**Async Usage (Recommended):**
```python
from src.scraper.buggmenot import BugMeNotScraper
import asyncio

async def main():
    # With anonymization and proxy support
    scraper = BugMeNotScraper(
        headless=True,
        browser="chromium",
        proxy="http://proxy:8080",  # Optional
        anonymize=True              # Default
    )
    
    try:
        credentials = await scraper.scrape("glassdoor.com")
        
        for cred in credentials:
            print(f"Username: {cred['username']}")
            print(f"Password: {cred['password']}")
            print(f"Success Rate: {cred['success_rate']}%")
            print(f"Votes: {cred['votes']}")
            print(f"Age: {cred['age']}")
            print("-" * 40)
    finally:
        await scraper.close()

asyncio.run(main())
```

**Quick Helper Functions:**
```python
from src.scraper.buggmenot import get_credentials, get_multiple_credentials
import asyncio

# Get credentials for one website
credentials = asyncio.run(get_credentials("nytimes.com"))

# Get credentials for multiple websites
websites = ["nytimes.com", "wsj.com", "economist.com"]
all_credentials = asyncio.run(get_multiple_credentials(websites))
```

## 🛡️ Anonymization & Stealth Features

The scraper includes comprehensive anonymization features (enabled by default):

### 🎭 **Anonymization Features**
- **Random User Agents**: Rotates between realistic browser signatures
- **Geographic Randomization**: Random timezone and language settings
- **Fingerprinting Protection**: 
  - WebGL blocking to prevent graphics fingerprinting
  - Canvas fingerprinting protection
  - WebRTC blocking to prevent IP leaks
- **Automation Detection Removal**: Removes webdriver properties
- **Browser Object Spoofing**: Adds realistic browser objects

### 🔗 **Proxy Support**
- **HTTP Proxies**: `http://proxy:port` format
- **SOCKS5 Proxies**: `socks5://proxy:port` format
- **Automatic Configuration**: Proxy settings applied to browser context

### 🔧 **Usage Examples**
```bash
# With proxy
python -m src.scraper.buggmenot glassdoor.com --proxy http://proxy:8080

# Disable anonymization
python -m src.scraper.buggmenot nytimes.com --no-anonymize

# Firefox with SOCKS5 proxy
python -m src.scraper.buggmenot wsj.com --browser firefox --proxy socks5://proxy:1080
```

### Browser Support
- `chromium` (default, recommended)
- `firefox`
- `webkit`

## 📊 Output Format

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

**Field Descriptions:**
- `website`: Target website domain
- `username`: Login username/email
- `password`: Login password
- `success_rate`: Success percentage (0-100)
- `votes`: Number of user votes
- `age`: How old the credential is
- `scraped_at`: ISO timestamp of when credential was scraped

## ⚡ Performance Tips

1. **Use headless mode** for faster execution (default)
2. **Use Chromium browser** for best performance
3. **Set appropriate timeout** for slow networks: `--timeout 30`
4. **Use proxy rotation** for multiple requests

## 🔧 Configuration

The scraper uses the following default settings:

- **Default timeout**: 30 seconds
- **Default browser**: Chromium
- **Default headless**: True
- **Anonymization**: Enabled by default

## 🐛 Troubleshooting

**Common Issues:**

1. **No credentials found**: Website may not be in BugMeNot database
2. **Browser not found**: Run `playwright install chromium`
3. **Timeout errors**: Increase timeout with `--timeout 60`
4. **Proxy errors**: Verify proxy server is accessible

**Debug Mode:**
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 📈 Usage Examples

```bash
# Basic credential extraction
python -m src.scraper.buggmenot glassdoor.com

# Multiple options with proxy
python -m src.scraper.buggmenot nytimes.com \
  --output nyt_creds.json \
  --proxy http://proxy:8080 \
  --browser firefox \
  --visible

# Quick extraction without saving
python -m src.scraper.buggmenot wsj.com --output /dev/null

# With custom timeout
python -m src.scraper.buggmenot economist.com --timeout 60
```

## 🤝 Contributing

1. Follow the existing async/await code structure
2. Add proper error handling and logging
3. Test with multiple browsers when possible
4. Update this README for any significant changes

## 📄 License

This project follows the same license as the main repository.

---

*For questions or support, please refer to the main project documentation or create an issue in the project repository.*
