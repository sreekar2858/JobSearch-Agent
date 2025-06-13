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
Extract jobs from LinkedIn search results or individual job URLs with flexible browser support and output options.

### AI-Powered Processing
Generate tailored CVs and cover letters using multi-agent AI systems for professional applications.

### API & CLI Access
Use via command line interface or REST API with WebSocket support for web integrations.

---

## 🎯 Key Features

### 🔍 **Advanced LinkedIn Scraper**
- **Dual Extraction Modes**: Search by keywords/location OR extract from specific job URLs
- **Multi-Browser Support**: Chrome (default) or Firefox with automatic fallback
- **Smart Sorting**: Sort results by relevance or recency
- **Flexible Output**: Full job details or fast link-only collection
- **Rich Data**: Titles, companies, descriptions, requirements, salaries, application URLs
- **Company Intelligence**: Detailed profiles, employee counts, hiring team information
- **Anti-Detection**: Stealth browsing with CAPTCHA handling and rate limiting

### 🤖 **AI-Powered Job Processing**
- **Intelligent Parsing**: Extract structured data from unformatted job descriptions
- **Custom CV Generation**: Tailored CVs for specific job applications
- **Personalized Cover Letters**: Compelling letters matched to job requirements
- **Multi-Agent Architecture**: Specialized agents for critique, fact-checking, and refinement
- **Bulk Processing**: Handle multiple applications efficiently
- **Template Integration**: Works with Word and text templates

### 🌐 **API & Integration**
- **REST API**: HTTP endpoints for job search, parsing, and document generation
- **WebSocket Support**: Real-time progress updates and interactive communication
- **React Integration**: Ready-to-use examples for web applications
- **Background Processing**: Asynchronous task handling
- **File Downloads**: Direct access to generated documents

---

## 📋 Requirements

- **Python 3.10+**
- **Browser**: Chrome or Firefox (Chrome recommended)
- **LinkedIn Account**: For enhanced scraping capabilities
- **AI API Keys**: For CV/cover letter generation (Google Gemini or OpenAI)

---

## 🛠️ Installation

1. **Clone repository and install dependencies**
   ```bash
   git clone https://github.com/sreekar2858/JobSearch-Agent.git
   cd JobSearch-Agent
   pip install -r requirements.txt
   ```

2. **Configure environment** (create `.env` file)
   ```env
   LINKEDIN_USERNAME=your_email@example.com
   LINKEDIN_PASSWORD=your_password
   GOOGLE_API_KEY=your_gemini_api_key
   ```

---

## 🔧 Usage Overview

### LinkedIn Scraper

**Search Mode Examples:**
```bash
# Basic search
python extract_linkedin_jobs.py "Software Engineer" "Berlin" --jobs 15

# Advanced options
python extract_linkedin_jobs.py "Data Scientist" "Remote" --browser firefox --sort recency --links-only

# Multiple locations
python main.py search "Python Developer" --locations "Berlin" "Munich" --max-jobs 25
```

**Single Job Mode:**
```bash
# Extract from specific job URL
python extract_linkedin_jobs.py --job-url "https://linkedin.com/jobs/view/123456789"
```

**Key Options:**
- `--browser chrome|firefox` - Browser choice with fallback
- `--sort relevance|recency` - Sort results
- `--links-only` - Fast link collection without full details
- `--headless` - Run without GUI

### AI Job Processing

**Complete Workflow:**
```bash
# Search + generate documents
python main.py search "Frontend Developer" --locations "Berlin" --generate-cv --generate-cover-letter

# Process existing job data
python main.py process linkedin_jobs.json --generate-cv
```

### API Server

**Start server and access documentation:**
```bash
python main_api.py
# Visit http://localhost:8000/docs for interactive API documentation
```

**Key endpoints:**
- `POST /search` - Start job search
- `GET /search/{id}` - Get results
- `POST /process` - Generate CV/cover letters
- `POST /parse` - Parse job descriptions

---

## 📁 Project Structure

The project is organized for easy navigation and contribution:

```
JobSearch-Agent/
├── extract_linkedin_jobs.py          # Main LinkedIn scraper
├── main_api.py                       # FastAPI server
├── main.py                           # CLI interface
├── src/
│   ├── agents/                       # AI agents (CV writer, cover letter, parser)
│   ├── scraper/                      # Web scraping modules
│   ├── prompts/                      # AI agent prompts
│   └── utils/                        # Utilities and helpers
├── config/                           # Configuration files
├── data/                             # Templates and samples
├── output/                           # Generated outputs
├── docs/                             # Advanced documentation
├── examples/                         # Usage examples
└── tests/                            # Test files
```

**📚 Detailed Documentation:**
- [Scraper Technical Guide](src/scraper/search/README.md) - LinkedIn scraper deep dive
- [Advanced Configuration](docs/ADVANCED_CONFIGURATION.md) - Production setup
- [Development Guide](docs/DEVELOPMENT.md) - Contributing guidelines

---

## ⚙️ Configuration

### Basic Setup

Create `.env` file with your credentials:
```env
# LinkedIn (recommended for better results)
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password

# AI APIs (for CV/cover letter generation)
GOOGLE_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key  # Optional alternative
```

### Advanced Configuration

The system uses YAML configuration files in the `config/` directory:

- **`jobsearch_config.yaml`** - Main scraper and API settings
- **`cv_app_agent_config.yaml`** - AI agent configuration
- **`file_config.yaml`** - File paths and templates

Key settings include browser preferences, retry logic, output directories, and AI model assignments.

---

## 📊 Output & Results

### File Organization

All outputs are organized in the `output/` directory:

- **`linkedin/`** - Scraped job data in JSON format with timestamps
- **`cvs/`** - Generated CVs in both text and Word formats
- **`cover_letters/`** - Personalized cover letters
- **`parsed_jobs/`** - Structured job data from parsing

### Data Quality

The scraper extracts comprehensive job information including:
- Complete job descriptions and requirements
- Company profiles and employee counts
- Hiring team information and contact details
- Related job suggestions and career insights
- Application URLs and salary information (when available)

---

## 🚦 Best Practices & Guidelines

### Scraping Guidelines

**Recommended Limits:**
- **Jobs per session**: 25-50 for stability
- **Pages per search**: 5-10 pages maximum
- **Break between searches**: 10-15 minutes
- **Authentication**: Always use LinkedIn login for better results

**Performance Tips:**
- Use `--headless` mode for faster scraping
- Choose `--links-only` for quick job URL collection
- Process large datasets in smaller batches
- Monitor for CAPTCHAs and be ready to solve them manually

### Ethical Usage

- **Personal Use**: Ideal for individual job searching
- **Respect Limits**: Don't overwhelm LinkedIn's servers
- **Privacy**: Only collect publicly available job information
- **Compliance**: Follow LinkedIn's Terms of Service
- **Responsible**: Use data ethically and don't republish without permission

---

## 🔧 Troubleshooting

### Common Issues & Solutions

**🔍 Browser Problems**
- Try switching browsers: `--browser firefox` or `--browser chrome`
- Update browser drivers: `pip install --upgrade webdriver-manager`
- Check browser installation and version compatibility

**🔑 Authentication Issues**
- Verify credentials in `.env` file
- Check for two-factor authentication requirements
- Ensure LinkedIn account is active and in good standing

**⚠️ Rate Limiting**
- Reduce job limits: `--jobs 10` instead of larger numbers
- Increase delays between requests
- Take breaks between different searches
- Use authentication to reduce rate limiting

**📊 Empty Results**
- Broaden search terms ("Software" instead of "Senior React Developer")
- Try different location formats ("Berlin, Germany" vs "Berlin")
- Enable authentication for better access
- Check if search terms are too specific

**🐛 Technical Errors**
- Enable debug mode: `export DEBUG=1`
- Check log files in `logs/` directory
- Verify all dependencies are installed
- Review screenshots in `output/linkedin/` for visual debugging

---

## 📚 Documentation & Support

### Quick Reference
- **Main Commands**: `python extract_linkedin_jobs.py --help`
- **API Documentation**: Visit `http://localhost:8000/docs` when server is running
- **Configuration**: See `config/` directory for all settings

### Additional Resources
- **CHANGELOG.md** - Version history and updates
- **TODO.md** - Planned features and roadmap
- **examples/** - Sample usage and integration code

### Getting Help
1. Check the troubleshooting section above
2. Review the detailed documentation in `docs/`
3. Search existing issues on GitHub
4. Create a new issue with detailed information

---

## 🤝 Contributing

Contributions are welcome! Please see our [Development Guide](docs/DEVELOPMENT.md) for:
- Development environment setup
- Code style guidelines
- Testing procedures
- Pull request process

### Quick Start for Contributors
```bash
git clone https://github.com/your-username/JobSearch-Agent.git
cd JobSearch-Agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

---

## 📄 License & Disclaimer

**License:** MIT License - see [LICENSE](LICENSE) for details.

**Disclaimer:** This tool is for educational and personal use. Users are responsible for complying with LinkedIn's Terms of Service and applicable laws. The authors are not responsible for any misuse.

---

## 📞 Contact & Links

- **GitHub**: [@sreekar2858](https://github.com/sreekar2858)
- **Repository**: [JobSearch-Agent](https://github.com/sreekar2858/JobSearch-Agent)
- **Issues**: [Report bugs or request features](https://github.com/sreekar2858/JobSearch-Agent/issues)

---

## 🙏 Acknowledgments

Special thanks to:
- [Selenium](https://selenium.dev/) for browser automation
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [LinkedIn](https://linkedin.com/) for providing job data
- All contributors and users who help improve this project
