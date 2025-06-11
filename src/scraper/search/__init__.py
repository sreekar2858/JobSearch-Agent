"""
Job search module for the JobSearch-Agent.

This module provides local scrapers for searching jobs on various platforms:
- LinkedIn job search using Firefox WebDriver
- Support for searching with keywords and location
- Job details extraction and storage
"""

from .search_manager import JobSearchManager
from .linkedin_scraper import LinkedInScraper

__all__ = ["JobSearchManager", "LinkedInScraper"]
