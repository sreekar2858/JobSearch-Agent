"""
LinkedIn scraper package for job search automation using Playwright.

This package provides a modern, async-first implementation of LinkedIn job scraping
using Playwright instead of Selenium, while maintaining the same API and algorithm
as the original implementation.
"""

from .scraper import LinkedInScraper, LinkedInScraperSync
from .cli import main as cli_main, sync_main as cli_sync_main

__all__ = ['LinkedInScraper', 'LinkedInScraperSync', 'cli_main', 'cli_sync_main']
__version__ = '2.0.0'
