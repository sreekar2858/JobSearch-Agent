"""
Extractors package for LinkedIn job data extraction.
"""

from .job_links import JobLinksExtractor
from .job_details import JobDetailsExtractor

__all__ = ['JobLinksExtractor', 'JobDetailsExtractor']
