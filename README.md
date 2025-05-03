# Job Findr Agent

An agentic job search and CV preparation application using Google ADK.

## Features

- **Multi-site Job Search**: Search for jobs on LinkedIn, Indeed, and Glassdoor without requiring API access
- **Targeted Search**: Use optimized search queries for better job matching
- **Automatic CV Generation**: Create customized CVs for each job application
- **Real-time Progress Tracking**: View detailed progress in the terminal

## How it Works

The Job Findr Agent utilizes a clever approach to search for jobs without needing paid APIs:

1. **Smart Google Search**: Uses site-specific Google search queries (e.g., `site:linkedin.com/jobs Python Developer Remote`) to find job listings
2. **Scraping Pipeline**: Extracts complete job details from the search results
3. **CV Customization**: Generates tailored CVs for each job using the Google ADK agent system

<p align="center">
<img src="assets/Job-Findr_Agent.png" alt="drawing" width="600"/>
</p>

## Project Structure

```
Job_Findr_Agent/
├── main.py                # Main entry point for batch processing jobs
├── config/                # Configuration files
│   └── config.yaml        # Main configuration settings
├── data/                  # Document templates
│   ├── SajjalaSreekarReddy_CV.docx      # CV template
│   └── CoverLetter_Template.docx        # Cover letter template
├── jobs/                  # Job posting data storage
│   └── job_postings.json  # Sample job postings
├── output/                # Generated files for each job
│   └── [company]_[role]/  # Folder for each processed job
├── src/                   # Source code modules
│   ├── agents/            # AI agent implementations
│   │   ├── cv_writer.py   # CV generation pipeline
│   │   ├── cv_prompts.py  # LLM prompts for CV pipeline
│   │   └── search_agents.py # Job search agents
│   └── utils/             # Utility functions
│       ├── file_utils.py  # File and config handling
│       ├── scraper.py     # Web scraping utilities
│       └── exit_conditions.py # Loop exit conditions
└── README.md
```

## Prerequisites

- Python 3.10+
- Dependencies: Google ADK, python-docx, scrapy, pyyaml, python-dotenv

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/job-findr-agent.git
cd job-findr-agent

# Install dependencies
pip install -r requirements.txt

# Add your API keys in .env file
```

## Usage

### Job Search CLI

Use the command-line interface to search for jobs:

```bash
python job_search_cli.py "Python Developer" -l "Remote" "London" -t full-time -m 5
```

Options:
- `keywords`: Job title or keywords to search for
- `-l, --locations`: Locations to search in (default: Remote)
- `-t, --job-type`: Type of job (default: full-time)
- `-e, --experience`: Experience level (default: mid-level)
- `-m, --max-jobs`: Maximum jobs per site/location (default: 3)
- `-c, --generate-cv`: Generate custom CVs for all found jobs

### Process Existing Jobs

Process jobs from a JSON file to generate custom CVs:

```bash
python main.py
```

### Configuration

Edit `config/config.yaml` to set default search parameters:

```yaml
keywords: "Software Developer"
locations: ["Remote", "London"]
job_type: "full-time"
experience_level: "mid-level"
posting_within: "7 days"
```

## Terminal Progress Tracking

The application shows detailed progress in the terminal with emojis indicating each step:

- 🚀 Starting job search pipeline...
- 🌐 Searching LinkedIn jobs...
- 📍 Location: Remote
- 🔍 Query: site:linkedin.com/jobs Software Engineer Remote
- 📝 Generating initial CV draft...
- ✅ Job search completed. Found 12 job postings!

## Requirements

- Python 3.9+
- Google ADK
- Access to Google Search
- BeautifulSoup4 and Requests for web scraping

## Extending

### Add New Agent Types

1. Create a new file in `src/agents/`
2. Import and use in the main pipeline

### Add New Job Sites for Scraping

Edit `src/utils/scraper.py` to add new domain selectors:

```python
DOMAIN_SELECTORS = {
    "newjobsite.com": {
        "job_title": "h1.job-title",
        "company_name": "span.company",
        ...
    },
    ...
}
```

## License

MIT
