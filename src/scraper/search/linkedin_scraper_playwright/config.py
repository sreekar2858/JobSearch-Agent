"""
Configuration constants for LinkedIn scraper using Playwright.
"""

# Timeout and retry constants
DEFAULT_TIMEOUT = 20000  # Playwright uses milliseconds
MAX_RETRIES = 5
MAX_SCROLL_ATTEMPTS = 20

# Sleep ranges for human-like behavior
DEFAULT_MIN_SLEEP = 2.0
DEFAULT_MAX_SLEEP = 5.0
NAVIGATION_MIN_SLEEP = 3.0
NAVIGATION_MAX_SLEEP = 5.0

# Browser configuration
SUPPORTED_BROWSERS = ["chromium", "firefox", "webkit"]

# Chrome options
CHROME_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

# Firefox user agent
FIREFOX_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"

# WebKit user agent
WEBKIT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"

# Experience level mapping
EXPERIENCE_LEVEL_MAPPING = {
    "internship": "1",
    "entry_level": "2",
    "associate": "3",
    "mid_senior": "4",
    "mid_senior_level": "4",  # Alternative naming for mid-senior level
    "director": "5",
    "executive": "6",
}

# Date posted mapping
DATE_POSTED_MAPPING = {
    "any_time": "",
    "past_month": "r2592000",
    "past_week": "r604800",
    "past_24_hours": "r86400",
}

# Experience level display text mapping
EXPERIENCE_DISPLAY_TEXT = {
    "internship": "Internship",
    "entry_level": "Entry level",
    "associate": "Associate",
    "mid_senior": "Mid-Senior level",
    "mid_senior_level": "Mid-Senior level",  # Alternative naming
    "director": "Director",
    "executive": "Executive",
}

# Date posted display text mapping
DATE_DISPLAY_TEXT = {
    "any_time": "Any time",
    "past_month": "Past month",
    "past_week": "Past week",
    "past_24_hours": "Past 24 hours",
}

# Browser launch arguments for better stealth
BROWSER_ARGS = [
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-blink-features=AutomationControlled",
    "--disable-web-security",
    "--disable-features=VizDisplayCompositor",
    "--disable-extensions-file-access-check",
    "--disable-extensions-except",
    "--disable-plugins-discovery",
    "--allow-running-insecure-content",
]
