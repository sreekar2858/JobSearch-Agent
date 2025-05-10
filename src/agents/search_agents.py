"""
Search and scraping agents for Job Findr Agent.

This module includes:
- Google Search integration for finding job postings from LinkedIn, Indeed, and Glassdoor
- Targeted search query generation for better results
- Job posting extraction and normalization
"""
from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.langchain_tool import LangchainTool
from langchain_community.tools import TavilySearchResults
from google.adk.tools import google_search
import json
import re

from src.utils.file_utils import load_config

jobsearch_config = load_config("config/jobsearch_config.yaml")
file_config = load_config("config/file_config.yaml")

# --- Specialized Job Search Functions ---

def generate_targeted_query(job_title, location, site):
    """
    Generate a specialized search query targeting specific job sites.
    This helps get better results when using free search APIs.
    """
    site_queries = {
        "linkedin": f"site:linkedin.com/jobs {job_title} {location}",
        "indeed": f"site:indeed.com {job_title} {location} job",
        "glassdoor": f"site:glassdoor.com {job_title} {location} job"
    }
    return site_queries.get(site.lower(), f"{job_title} {location} jobs {site}")

# --- Google Search Agent with Progress Tracking ---
google_search_agent = LlmAgent(
    model=jobsearch_config['models']["gemini_2.5_flash"],
    name="google_search_agent",
    description="Finds job postings and extracts complete information from the job page.",
    instruction=(
        f"You are a job search assistant. Use Google search to find job postings for roles that match:\n"
        f"- Keywords: {jobsearch_config['keywords']}\n"
        f"- Locations: {', '.join(jobsearch_config['locations'])}\n"
        f"- Job type: {jobsearch_config['job_type']}\n"
        f"- Experience level: {jobsearch_config['experience_level']}\n"
        f"- Posted in the last {jobsearch_config['posting_within']}\n\n"

        "IMPORTANT: Use these specialized search techniques:\n"
        "1. First search LinkedIn with: site:linkedin.com/jobs [JOB TITLE] [LOCATION]\n"
        "2. Then search Indeed with: site:indeed.com [JOB TITLE] [LOCATION] job\n" 
        "3. Finally search Glassdoor with: site:glassdoor.com [JOB TITLE] [LOCATION] job\n\n"

        "For each result:\n"
        "- Follow the URL of the job post.\n"
        "- Extract detailed information from the actual job listing page.\n"
        "- Prioritize getting complete job descriptions and requirements.\n"

        "After each search, say 'Now searching [SITE_NAME]...' to show progress.\n\n"

        "Return up to 10 job entries as a JSON array with these fields:\n"
        "1. job_title\n"
        "2. company_name\n"
        "3. job_description\n"
        "4. job_location\n"
        "5. posting_date\n"
        "6. job_type\n"
        "7. experience_level\n"
        "8. skills_required\n"
        "9. contact_person\n"
        "10. contact_email_or_linkedin\n"
        "11. salary_info\n"
        "12. language_requirements\n"
        "13. keywords\n"
        "14. company_website\n"
        "15. job_url\n"
        "16. source_site\n\n"

        "Use structured JSON output. If any field is not available, leave it as an empty string."
    ),
    tools=[google_search],
    output_key="job_postings",
)

# --- Multi-Site Job Search Agent ---
multi_site_search_agent = LlmAgent(
    name="multi_site_job_search",
    model=jobsearch_config['models']["gemini_2.5_flash"],
    description="Advanced agent that searches multiple job sites in sequence",
    instruction=(
        "You are a multi-site job search specialist. Your goal is to find job listings from multiple sources.\n\n"
        
        f"Target job criteria:\n"
        f"- Job titles: {jobsearch_config['keywords']}\n"
        f"- Locations: {', '.join(jobsearch_config['locations'])}\n"
        f"- Job type: {jobsearch_config['job_type']}\n"
        f"- Experience: {jobsearch_config['experience_level']}\n"
        f"- Recent postings: {jobsearch_config['posting_within']}\n\n"
        
        "SEARCH PROCESS:\n"
        "1. First announce: '🔍 Searching LinkedIn jobs...'\n"
        "2. Search LinkedIn using this exact query format: site:linkedin.com/jobs [JOB TITLE] [LOCATION]\n"
        "3. Capture at least 3-4 job listings with their details\n"
        "4. Then announce: '🔍 Searching Indeed jobs...'\n"
        "5. Search Indeed using: site:indeed.com [JOB TITLE] [LOCATION] job\n"
        "6. Capture 3-4 more job listings\n"
        "7. Finally announce: '🔍 Searching Glassdoor jobs...'\n"
        "8. Search Glassdoor using: site:glassdoor.com [JOB TITLE] [LOCATION] job\n"
        "9. Announce: '✅ Job search complete! Processing results...'\n\n"
        
        "For each job found:\n"
        "- Extract the complete URL to the job posting\n"
        "- Follow the link to access the actual job description page\n"
        "- Parse and extract comprehensive details including responsibilities and requirements\n"
        "- Format the information according to the specified schema\n\n"
        
        "Return the results as a structured JSON array with these fields for each job:\n"
        "- job_title: The exact title of the job\n"
        "- company_name: Name of the company\n"
        "- job_description: Full description, responsibilities and requirements\n"
        "- job_location: City, state, country and remote status if applicable\n"
        "- posting_date: When the job was posted\n"
        "- job_type: Full-time, part-time, contract, etc.\n"
        "- experience_level: Years of experience or seniority level\n"
        "- skills_required: List of technical and soft skills\n"
        "- salary_info: Any available salary information\n"
        "- job_url: Direct link to the job posting\n"
        "- source_site: Which site the job was found on (LinkedIn, Indeed, or Glassdoor)\n\n"

        "Make sure each job entry is complete and properly formatted."
    ),
    tools=[google_search],
    output_key="multi_site_job_results",
)

# --- Tavily Search Agent ---
# Instantiate the LangChain tool
tavily_tool_instance = TavilySearchResults(
    max_results=10,
    search_depth="advanced",
    include_answer=True,
)

# Wrap it with LangchainTool for ADK
adk_tavily_tool = LangchainTool(tool=tavily_tool_instance)

# Define the ADK agent for job searching
tavily_search_agent = LlmAgent(
    name="job_search_agent",
    model=LiteLlm(model=f"{jobsearch_config['models']['gpt_4o']}"),
    description="Agent that searches for jobs online using keywords and a specified time frame.",
    instruction=(
        "You are an expert job search assistant. When given keywords and a time frame, "
        "you should find recent job listings matching those keywords.\n"
        "Use the search tool to look for job postings.\n"
        
        "IMPORTANT: Focus your searches on these job sites by using site-specific queries:\n"
        "- For LinkedIn: 'site:linkedin.com/jobs [JOB TITLE] [LOCATION]'\n"
        "- For Indeed: 'site:indeed.com [JOB TITLE] [LOCATION] job'\n"
        "- For Glassdoor: 'site:glassdoor.com [JOB TITLE] [LOCATION] job'\n\n"
        
        "Show your progress with these announcements:\n"
        "- '🔍 Searching LinkedIn jobs...'\n"
        "- '🔍 Searching Indeed jobs...'\n"
        "- '🔍 Searching Glassdoor jobs...'\n"
        "- '✅ Job search complete! Processing results...'\n\n"
        
        "Return the job entries with these fields:\n"
        "1. job_title\n"
        "2. company_name\n"
        "3. job_description\n"
        "4. job_location\n"
        "5. posting_date\n"
        "6. job_type\n"
        "7. experience_level\n"
        "8. skills_required\n"
        "9. contact_person\n"
        "10. contact_email_or_linkedin\n"
        "11. salary_info\n"
        "12. language_requirements\n"
        "13. keywords\n"
        "14. company_website\n"
        "15. job_url\n"
        "16. source_site\n\n"
    ),
    tools=[adk_tavily_tool]
)

def run_search_pipeline(keywords, locations=None, job_type=None, experience=None):
    """
    Run a comprehensive job search across multiple platforms.
    Prints progress to terminal as it goes through each step.
    
    Args:
        keywords: Job title or keywords to search for
        locations: List of locations to search in
        job_type: Type of job (full-time, contract, etc)
        experience: Experience level required
        
    Returns:
        List of job postings as dictionaries
    """
    print("🚀 Starting job search pipeline...")
    
    if locations is None:
        locations = jobsearch_config['locations']
    if job_type is None:
        job_type = jobsearch_config['job_type']
    if experience is None:
        experience = jobsearch_config['experience_level']
        
    print(f"🔎 Searching for: {keywords} in {', '.join(locations)}")
    
    results = []
    job_sites = ["linkedin", "indeed", "glassdoor"]
    
    for site in job_sites:
        print(f"🌐 Searching {site.capitalize()}...")
        for location in locations:
            print(f"  📍 Location: {location}")
            # Execute search for this site and location combination
            query = generate_targeted_query(keywords, location, site)
            print(f"  🔍 Query: {query}")
            
            # Here you would run the actual search using the appropriate agent
            # This is a placeholder for the implementation
            
            print(f"  ✓ Found jobs on {site.capitalize()} for {location}")
        
    print("✅ Search complete! Processing job details...")
    
    # This would be where you process the results
    
    print(f"📊 Found {len(results)} matching job postings")
    return results