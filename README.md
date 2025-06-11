# JobSearch Agent

<p align="center">
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+">
  </a>
  <a href="https://github.com/sreekar2858/JobSearch-Agent/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT">
  </a>
  <a href="https://github.com/sreekar2858/JobSearch-Agent/issues">
    <img src="https://img.shields.io/github/issues/sreekar2858/JobSearch-Agent" alt="GitHub issues">
  </a>
</p>

An intelligent job search automation system with advanced LinkedIn scraping capabilities, CV generation, and cover letter creation powered by AI agents. This comprehensive toolkit extracts rich job data, including company information, hiring team details, related positions, and complete job descriptions, making it perfect for job seekers who want detailed insights and automated application materials.

---

## 🚀 Quick Start

### LinkedIn Job Scraping

```bash
# Install dependencies
pip install -r requirements.txt

# Basic job search - extracts rich job data
python extract_linkedin_jobs.py "Software Engineer" "Berlin" --jobs 10

# Advanced search with multiple pages and headless mode
python extract_linkedin_jobs.py "Data Scientist" "Remote" --pages 3 --headless

# Search with authentication for complete access to hiring team info
python extract_linkedin_jobs.py "Product Manager" "San Francisco" --jobs 20 --login

# Extract comprehensive data including company info and related jobs
python extract_linkedin_jobs.py "Backend Engineer" "London" --login --jobs 15
```

### CLI Job Processing

```bash
# Search and process jobs with AI agents
python main.py search "Machine Learning Engineer" --locations "Berlin" "Remote" --max-jobs 10 --generate-cv

# Process existing job data to generate CVs and cover letters
python main.py process jobs.json --generate-cv --generate-cover-letter

# Parse job descriptions from text files
python main.py parse --input-file job_description.txt --output-file parsed_job.json
```

### API Server

```bash
# Start the API server
python main_api.py

# Access documentation at http://localhost:8000/docs
```

---

## 🎯 Features

### 🔍 **Advanced LinkedIn Scraper**
- **Complete Job Extraction**: Titles, companies, descriptions, requirements, salaries, and application URLs
- **Rich Metadata**: Job insights, application deadlines, hiring team information, and company details
- **Intelligent Scrolling**: Automatically loads all jobs from search results (25+ per page)
- **Company Information**: Detailed company profiles, employee counts, and industry data
- **Hiring Team Data**: Extract recruiter and hiring manager contact information
- **Related Jobs**: Discover similar positions and career progression opportunities
- **External Apply URLs**: Direct application links when available (bypasses LinkedIn application)
- **Anti-Detection**: Handles CAPTCHAs, rate limiting, and layout changes with human-like behavior

### 🤖 **AI-Powered Job Processing**
- **Intelligent Job Parsing**: Extract structured data from unformatted job descriptions
- **Custom CV Generation**: Create tailored CVs for specific job applications using AI agents
- **Personalized Cover Letters**: Generate compelling cover letters matched to job requirements
- **Bulk Processing**: Handle multiple job applications efficiently with batch operations
- **Multi-Agent Architecture**: Separate agents for critique, fact-checking, and refinement
- **Template Integration**: Works with existing CV and cover letter templates (Word/Text)

### 🌐 **API & Integration**
- **REST API**: HTTP endpoints for job search, parsing, and document generation
- **WebSocket Support**: Real-time progress updates and interactive communication
- **React Integration**: Ready-to-use examples for web application frontends
- **Background Processing**: Asynchronous task handling for long-running operations
- **File Download**: Direct access to generated CVs and cover letters via HTTP endpoints

---

## 📋 Requirements

- Python 3.10 or higher
- Chrome or Firefox browser
- LinkedIn credentials (for enhanced scraping)

---

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/JobSearch-Agent.git
   cd JobSearch-Agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (optional but recommended)
   ```bash
   cp .env.example .env
   # Edit .env with your LinkedIn credentials
   ```

---

## 🔧 Usage

### LinkedIn Job Scraper

The LinkedIn scraper is the core feature, extracting comprehensive job data:

```bash
# Basic usage
python extract_linkedin_jobs.py "Python Developer" "New York"

# Limit number of jobs
python extract_linkedin_jobs.py "DevOps Engineer" "Berlin" --jobs 15

# Multiple pages with headless browser
python extract_linkedin_jobs.py "Machine Learning" "Remote" --pages 5 --headless

# With authentication for better access
python extract_linkedin_jobs.py "Backend Engineer" "London" --login --jobs 25
```

#### Arguments:
**Core Arguments:**
- `keywords`: Job search terms (required)
- `location`: Job location (required)
- `--jobs N`: Maximum jobs to extract (takes priority over pages)
- `--pages N`: Maximum pages to scrape (default: 1)

**Browser Options:**
- `--headless`: Run browser without GUI (faster, less resource-intensive)
- `--browser`: Choose browser (chrome/firefox, default: chrome)
- `--login`: Use LinkedIn authentication for enhanced access

**Advanced Options:**
- `--output`: Custom output directory (default: output/linkedin/)
- `--delay`: Custom delay between requests (default: 1-3 seconds)
- `--timeout`: Page load timeout in seconds (default: 20)

#### Output:
Jobs are saved as JSON files in `output/linkedin/` with comprehensive metadata:

```json
{
  "url": "https://www.linkedin.com/jobs/view/...",
  "job_id": "3785692847",
  "title": "Senior Software Engineer",
  "company": "TechCorp Inc",
  "location": "Berlin, Germany",
  "description": "Full job description with complete requirements and responsibilities...",
  "date_posted": "1 week ago",
  "job_insights": ["Remote work available", "Full-time", "Mid-Senior level"],
  "easy_apply": false,
  "apply_info": {
    "apply_url": "https://techcorp.com/careers/apply/...",
    "application_type": "external"
  },
  "company_info": {
    "about": "About the company description...",
    "employees": "501-1,000 employees",
    "industry": "Software Development",
    "website": "https://techcorp.com"
  },
  "hiring_team": [
    {
      "name": "John Smith",
      "title": "Engineering Manager",
      "linkedin_url": "https://linkedin.com/in/johnsmith",
      "profile_image": "https://media.licdn.com/dms/image/..."
    }
  ],
  "related_jobs": [
    {
      "title": "Frontend Engineer",
      "company": "TechCorp Inc",
      "url": "https://www.linkedin.com/jobs/view/..."
    }
  ],
  "salary_info": "$120,000 - $150,000",
  "benefits": ["Health insurance", "Remote work", "Stock options"],
  "skills_required": ["Python", "React", "AWS", "Docker"],
  "experience_level": "Mid-Senior level",
  "employment_type": "Full-time"
}
```

### API Server

Start the FastAPI server for programmatic access:

```bash
python main_api.py
```

The server starts at `http://localhost:8000` with interactive documentation at `/docs`.

#### REST API Endpoints

**1. Job Search**
```bash
POST /search
```
Start a background job search task:
```json
{
  "keywords": "Software Engineer",
  "locations": ["Remote", "Berlin"],
  "job_type": "full-time",
  "experience_level": "mid-level",
  "max_jobs": 10
}
```

**2. Get Search Results**
```bash
GET /search/{search_id}
```
Retrieve completed search results with full job data.

**3. Parse Job Posting**
```bash
POST /parse
```
Extract structured data from job descriptions:
```json
{
  "text": "Job description text...",
  "extract_webpage": false
}
```

**4. Process Job**
```bash
POST /process
```
Generate CV and cover letters for specific jobs:
```json
{
  "job_posting": {
    "job_title": "Senior Software Engineer",
    "company_name": "TechCorp",
    "job_description": "..."
  },
  "generate_cv": true,
  "generate_cover_letter": true
}
```

**5. File Downloads**
Access generated files at:
```
GET /output/{filepath}
```

#### WebSocket API

Connect to `ws://localhost:8000/ws` for real-time updates:

```javascript
const socket = new WebSocket('ws://localhost:8000/ws');
socket.send(JSON.stringify({
  "action": "search",
  "data": {
    "keywords": "Python Developer",
    "locations": ["Berlin"]
  }
}));
```

**Documentation:** Visit `http://localhost:8000/docs` for interactive API documentation.

### Command Line Interface

The `main.py` script provides a comprehensive CLI for job searching and processing:

#### Job Search Command
```bash
python main.py search "Python Developer" --locations "Berlin" "Remote" --max-jobs 15 --generate-cv
```

**Search Options:**
- `--locations`: Multiple locations (e.g., "Berlin" "Remote" "London")
- `--job-type`: Employment type (full-time, part-time, contract)
- `--experience`: Experience level (entry, mid, senior)
- `--max-jobs`: Maximum jobs per location
- `--generate-cv`: Auto-generate CVs for found jobs
- `--generate-cover-letter`: Auto-generate cover letters

#### Job Processing Command
```bash
python main.py process jobs.json --output-dir custom_output --generate-cv --generate-cover-letter
```

**Processing Options:**
- `--output-dir`: Custom output directory
- `--generate-cv`: Generate tailored CVs
- `--generate-cover-letter`: Generate personalized cover letters
- `--no-cv`: Skip CV generation (when enabled by default)

#### Job Parsing Command
```bash
python main.py parse --input-file job_description.txt --output-file parsed_job.json
```

**Parsing Options:**
- `--input-file`: Text file with job descriptions
- `--output-file`: JSON output file
- `--text`: Direct text input (alternative to file)

#### Single Job Processing
```bash
python main.py single --title "Senior Engineer" --company "TechCorp" --description "Job requirements..." --generate-cv
```

**Single Job Options:**
- `--title`: Job title
- `--company`: Company name
- `--description`: Job description text
- `--generate-cv`: Generate CV for this specific job

---

## 📁 Project Structure

```
JobSearch-Agent/
├── 📄 extract_linkedin_jobs.py          # Main LinkedIn scraper script
├── 📄 main_api.py                       # FastAPI server
├── 📁 src/
│   ├── 📁 agents/                       # AI agents for job processing
│   │   ├── 📄 job_details_parser.py     # Job description parser
│   │   ├── 📄 cv_writer.py              # CV generation agent
│   │   └── 📄 cover_letter_writer.py    # Cover letter agent
│   ├── 📁 scraper/
│   │   └── 📁 search/
│   │       └── 📄 linkedin_scraper.py   # Core LinkedIn scraper
│   └── 📁 prompts/                      # AI agent prompts
├── 📁 config/                           # Configuration files
├── 📁 data/                             # CV templates and samples
├── 📁 output/                           # Generated outputs
│   └── 📁 linkedin/                     # LinkedIn scraping results
├── 📁 docs/                             # Documentation
└── 📁 examples/                         # Usage examples
```

---

## ⚙️ Configuration

### Environment Setup

1. **Create environment file:**
```bash
cp .env.example .env
```

2. **Configure LinkedIn credentials (recommended):**
```env
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

3. **Configure AI API keys (for CV/cover letter generation):**
```env
GOOGLE_API_KEY=your_google_gemini_api_key
OPENAI_API_KEY=your_openai_api_key  # Optional alternative
```

**Benefits of LinkedIn authentication:**
- Access to complete job descriptions
- Hiring team information and contact details
- Company insights and employee counts
- Related job suggestions
- Reduced rate limiting and better success rates

### Configuration Files

**Main Configuration (`config/jobsearch_config.yaml`):**
```yaml
api:
  host: "localhost"
  port: 8000
  debug: false

scraper:
  default_browser: "chrome"
  headless: true
  timeout: 20
  delay_range: [1, 3]  # Random delay between requests
  max_retries: 3

search:
  default_max_jobs: 25
  default_pages: 1
  enable_login: true
```

**Agent Configuration (`config/cv_app_agent_config.yaml`):**
```yaml
app_name: "CVWriter"
logging_level: "INFO"
max_loop_iterations: 5

models:
  gemini_2.5_flash: "gemini-2.0-flash-exp"
  gpt_4o: "gpt-4o"
  
# Agent-specific model assignments
initial_draft_model: "gemini_2.5_flash"
critic_model: "gemini_2.5_flash"
grammar_check_model: "gpt_4o"
```

**File Configuration (`config/file_config.yaml`):**
```yaml
templates:
  cv: "data/SajjalaSreekarReddy_CV.docx"
  cover_letter: "data/CoverLetter_Template.docx"
  
output:
  linkedin: "output/linkedin"
  cvs: "output/cvs"
  cover_letters: "output/cover_letters"
```

---

## 🔍 How It Works

### LinkedIn Scraper Architecture

1. **Authentication**: Logs into LinkedIn for enhanced access
2. **Search Navigation**: Navigates to job search with keywords/location
3. **Intelligent Scrolling**: Loads all jobs from sidebar (25+ per page)
4. **Job URL Collection**: Extracts URLs for individual job pages
5. **Detail Extraction**: Visits each job page for complete information
6. **Rich Data Parsing**: Extracts company info, hiring team, related jobs
7. **JSON Export**: Saves structured data for further processing

### Anti-Detection Features

- **Human-like Behavior**: Random delays and mouse movements
- **Browser Fingerprinting**: Uses real browser instances
- **Rate Limiting**: Intelligent backoff strategies
- **CAPTCHA Handling**: Manual intervention prompts
- **Session Management**: Maintains login state across requests

---

## 📊 Usage Examples

### Basic Job Scraping

```bash
# Quick search for software engineering jobs
python extract_linkedin_jobs.py "Software Engineer" "Berlin" --jobs 15

# Remote work opportunities
python extract_linkedin_jobs.py "Python Developer" "Remote" --pages 2 --headless

# Multiple location search
python main.py search "Data Scientist" --locations "Berlin" "Munich" "Hamburg" --max-jobs 10
```

### Advanced Scraping

```bash
# Comprehensive search with authentication
python extract_linkedin_jobs.py "Machine Learning Engineer" "San Francisco" --login --jobs 25 --browser chrome

# Headless scraping for production environments
python extract_linkedin_jobs.py "DevOps Engineer" "Amsterdam" --headless --pages 3 --output custom_output/

# Search with specific experience level filtering
python main.py search "Senior Backend Developer" --locations "London" --experience "senior" --job-type "full-time"
```

### Job Processing Workflows

```bash
# Complete workflow: search + generate documents
python main.py search "Frontend Developer" --locations "Berlin" --max-jobs 10 --generate-cv --generate-cover-letter

# Process existing job data
python main.py process linkedin_jobs_20250611.json --generate-cv --output-dir applications/

# Parse and structure job descriptions
python main.py parse --input-file job_descriptions.txt --output-file structured_jobs.json
```

### API Integration

**Python Client Example:**
```python
import requests

# Start job search
response = requests.post('http://localhost:8000/search', json={
    "keywords": "Python Developer",
    "locations": ["Berlin", "Remote"],
    "max_jobs": 15
})
search_id = response.json()['search_id']

# Get results
results = requests.get(f'http://localhost:8000/search/{search_id}')
jobs = results.json()

# Process jobs
for job in jobs:
    process_response = requests.post('http://localhost:8000/process', json={
        "job_posting": job,
        "generate_cv": True
    })
```

**React Integration:**
```javascript
// WebSocket connection
const socket = new WebSocket('ws://localhost:8000/ws');

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'result') {
        console.log('Search completed:', data.data);
    }
};

// Start search
socket.send(JSON.stringify({
    action: 'search',
    data: {
        keywords: 'React Developer',
        locations: ['Berlin']
    }
}));
```

---

## 🧠 AI Agent Architecture

### Multi-Agent System

The JobSearch Agent uses a sophisticated multi-agent architecture for processing jobs and generating documents:

**Job Parser Agent:**
- Extracts structured data from unformatted job descriptions
- Validates and cleans job information
- Standardizes company names, locations, and requirements

**CV Writer Agent System:**
- **Initial Draft Agent**: Creates first version based on job requirements
- **Critic Agent**: Reviews and suggests improvements
- **Fact Checker**: Verifies information accuracy
- **Reviser Agent**: Implements improvements and corrections
- **Grammar Checker**: Ensures proper language and formatting
- **Final Draft Agent**: Produces polished final version

**Cover Letter Writer Agent System:**
- Similar multi-agent workflow as CV generation
- Personalizes content for specific companies and roles
- Maintains professional tone and structure
- Incorporates job-specific keywords and requirements

### Agent Configuration

Each agent can be configured with different AI models:

```yaml
models:
  gemini_2.5_flash: "gemini-2.0-flash-exp"
  gpt_4o: "gpt-4o"
  claude_3: "claude-3-sonnet"

# Assign models to specific agents
initial_draft_model: "gemini_2.5_flash"  # Fast generation
critic_model: "gpt_4o"                   # Detailed analysis
grammar_check_model: "claude_3"          # Language precision
```

## � Output Structure

### Directory Organization

```
output/
├── linkedin/                           # LinkedIn scraping results
│   ├── linkedin_jobs_Engineer_Berlin_20250611_143052.json
│   ├── linkedin_jobs_DataScientist_Remote_20250611_151023.json
│   └── debug_screenshot_20250611_143105.png
├── cvs/                               # Generated CVs
│   ├── TechCorp_Senior_Engineer/
│   │   ├── TechCorp_Senior_Engineer_cv.txt
│   │   ├── TechCorp_Senior_Engineer_cv.docx
│   │   └── TechCorp_Senior_Engineer_metadata.json
│   └── DataTech_ML_Engineer/
├── cover_letters/                     # Generated cover letters
│   ├── TechCorp_Senior_Engineer.txt
│   ├── TechCorp_Senior_Engineer.docx
│   └── DataTech_ML_Engineer.txt
└── parsed_jobs/                       # Structured job data
    ├── parsed_jobs_20250611.json
    └── job_analysis_report.json
```

### File Formats

**LinkedIn Scraping Output:**
- JSON files with comprehensive job data
- Screenshots for debugging (when enabled)
- Error logs and debug information

**Generated Documents:**
- Plain text versions (.txt) for quick review
- Word documents (.docx) for professional use
- Metadata files (.json) with generation details

**Job Processing:**
- Structured JSON with standardized fields
- Analysis reports with insights and statistics
- Batch processing summaries

## 🚦 Rate Limits & Best Practices

### LinkedIn Scraping Guidelines

**Account Limits:**
- **Free LinkedIn accounts**: ~1000 job views per month
- **Premium accounts**: Higher limits, better access to hiring team info
- **Commercial use**: Consider LinkedIn's commercial terms

**Technical Limits:**
- **Jobs per page**: 25 jobs maximum (LinkedIn's page limit)
- **Pages per search**: Recommend 5-10 pages for stability
- **Concurrent requests**: Single-threaded for safety
- **Session duration**: 30-60 minutes maximum

**Recommended Practices:**

1. **Use Authentication**: LinkedIn login significantly improves success rates
2. **Reasonable Limits**: Don't exceed 50-100 jobs per session
3. **Delay Between Searches**: Wait 10-15 minutes between different keyword searches
4. **Monitor for CAPTCHAs**: Be ready to solve manual verification challenges
5. **Respect Terms of Service**: Use responsibly and ethically

### Performance Optimization

**For Large-Scale Scraping:**
```bash
# Use headless mode for better performance
python extract_linkedin_jobs.py "Engineer" "Berlin" --headless --jobs 25

# Process in batches to avoid memory issues
python extract_linkedin_jobs.py "Software Engineer" "Berlin" --pages 2
sleep 900  # 15-minute break
python extract_linkedin_jobs.py "Backend Engineer" "Berlin" --pages 2
```

**For Production Use:**
```bash
# Configure custom delays and timeouts
python extract_linkedin_jobs.py "Developer" "Remote" --delay 2 --timeout 30 --headless

# Use error handling and retry logic
python extract_linkedin_jobs.py "Engineer" "Berlin" --retries 3 --continue-on-error
```

### Ethical Guidelines

- **Personal Use**: Ideal for individual job searching and career development
- **Respect Privacy**: Don't harvest personal information beyond public job postings
- **Rate Limiting**: Don't overwhelm LinkedIn's servers with excessive requests
- **Terms Compliance**: Follow LinkedIn's Terms of Service and robots.txt
- **Data Usage**: Use scraped data responsibly and don't republish without permission

---

## 🔧 Troubleshooting

### Common Issues

**❌ Login Failed**
```bash
# Check credentials in .env file
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password

# Test login manually
python extract_linkedin_jobs.py "test" "test" --login --jobs 1
```

**❌ Browser Issues**
```bash
# Try different browser
python extract_linkedin_jobs.py "Software Engineer" "Berlin" --browser firefox

# Update browser drivers
pip install --upgrade webdriver-manager selenium

# Check browser installation
google-chrome --version  # Chrome
firefox --version        # Firefox
```

**❌ Rate Limiting / IP Blocked**
```bash
# Use smaller job limits and increase delays
python extract_linkedin_jobs.py "Engineer" "Berlin" --jobs 5 --delay 3

# Wait 15-30 minutes between different searches
# Use VPN or different network if necessary
```

**❌ CAPTCHA Challenges**
- The scraper will automatically pause when CAPTCHA is detected
- Solve the CAPTCHA manually in the browser window
- Press Enter in terminal to continue scraping
- Consider using authentication to reduce CAPTCHA frequency

**❌ Empty Results**
```bash
# Check if search terms are too specific
python extract_linkedin_jobs.py "Software" "Remote" --jobs 5

# Verify location format (try "Berlin, Germany" instead of "Berlin")
# Enable login for better access
python extract_linkedin_jobs.py "Developer" "Berlin, Germany" --login
```

**❌ Memory Issues (Large Searches)**
```bash
# Use headless mode to save memory
python extract_linkedin_jobs.py "Engineer" "Berlin" --headless --jobs 10

# Process in smaller batches
python extract_linkedin_jobs.py "Engineer" "Berlin" --pages 1
```

**❌ API Errors**
```bash
# Check if API server is running
curl http://localhost:8000/

# Verify AI API keys are set
python -c "import os; print('GOOGLE_API_KEY:', bool(os.getenv('GOOGLE_API_KEY')))"

# Check logs for detailed error messages
tail -f logs/jobsearch.log
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Set environment variable
export DEBUG=1

# Or modify config
# config/jobsearch_config.yaml
logging:
  level: "DEBUG"
  file: "logs/debug.log"
```

**Debug files location:**
- Screenshots: `output/linkedin/debug_screenshot_*.png`
- Error logs: `logs/error.log`
- Page source: `output/linkedin/debug_page_source.html`

---

## 📚 Documentation

### Main Documentation
- **README.md** (this file) - Complete user guide and reference
- **CHANGELOG.md** - Version history and release notes
- **TODO.md** - Development roadmap and planned features

### Advanced Documentation
- **docs/ADVANCED_CONFIGURATION.md** - Production deployment and advanced settings
- **docs/DEVELOPMENT.md** - Contributor guide and development setup

### Quick Links
- [🚀 Quick Start](#-quick-start)
- [🔧 Installation](#️-installation)
- [⚙️ Configuration](#️-configuration)
- [📊 Usage Examples](#-usage-examples)
- [🔧 Troubleshooting](#-troubleshooting)
- [🧠 AI Agent Architecture](#-ai-agent-architecture)

---

## 🤝 Contributing

We welcome contributions! Please see our [Development Guide](docs/DEVELOPMENT.md) for detailed information on:

- Setting up the development environment
- Code style guidelines and best practices
- Testing procedures and requirements
- Adding new features and job board integrations
- Submitting pull requests

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`python -m pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/your-username/JobSearch-Agent.git
cd JobSearch-Agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This tool is for educational and personal use only. Users are responsible for complying with LinkedIn's Terms of Service and applicable laws. The authors are not responsible for any misuse or violations.

---

## 📧 Contact

- GitHub: [@sreekar2858](https://github.com/sreekar2858)
- Project Link: [https://github.com/sreekar2858/JobSearch-Agent](https://github.com/sreekar2858/JobSearch-Agent)

---

## 🙏 Acknowledgments

- [Selenium](https://selenium.dev/) for browser automation
- [FastAPI](https://fastapi.tiangolo.com/) for API framework
- [LinkedIn](https://linkedin.com/) for job data (used responsibly)
- Contributors and testers who helped improve the scraper
