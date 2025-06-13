"""
BugMeNot Scraper Package
A scraper for obtaining login credentials from bugmenot.com

Main components:
- BugMeNotScraper: Core scraper class
- CLI: Command-line interface

Usage:
    python -m src.scraper.buggmenot --website glassdoor.com
    python -m src.scraper.buggmenot --help
"""

from .bugmenot_scraper import BugMeNotScraper
from .cli import main

__version__ = "1.0.0"
__all__ = ["BugMeNotScraper", "main"]
