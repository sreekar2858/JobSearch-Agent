"""
Job Findr Agent - A toolkit for job search, CV generation, and application tracking

This package provides tools to:
- Search for job postings online
- Process and store job listing information
- Generate customized CVs based on job requirements
- Create targeted cover letters
- Organize application materials by job

Main entry points:
- main.py: Batch process multiple job postings
- src.agents.cv_writer: Generate custom CVs
- src.agents.search_agents: Find job postings online
"""

from src.agents import call_agent, CVWriter, google_search_agent, tavily_search_agent
from src.utils import load_config, load_docx_template

__version__ = "0.1.0"
__author__ = "Your Name"