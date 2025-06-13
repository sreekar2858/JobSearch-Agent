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

An intelligent job search automation system with **LinkedIn scraping**, **AI-powered CV generation**, and **cover letter creation**. Extract detailed job data, company information, and hiring team details with advanced anonymization and proxy support.

---

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/sreekar2858/JobSearch-Agent.git
cd JobSearch-Agent
pip install -r requirements.txt
```

### 2. Setup (Optional but Recommended)
Create a `.env` file for enhanced features:
```env
# LinkedIn credentials (for better scraping results)
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password

# AI API key (for CV/cover letter generation)  
GOOGLE_API_KEY=your_gemini_api_key
```

### 3. Start Scraping
```bash
# LinkedIn job search
python -m src.scraper.search.linkedin_scraper "Software Engineer" "San Francisco" --max-jobs 10

# Get credentials for job sites
python -m src.scraper.buggmenot --website glassdoor.com

# Extract from specific job URL
python -m src.scraper.search.linkedin_scraper --job-url "https://linkedin.com/jobs/view/123456789"
```

---

## 🔧 Main Tools

### 🔍 **LinkedIn Scraper (Playwright)**
Advanced LinkedIn job scraper with anonymization and proxy support:

```bash
# Basic search
python -m src.scraper.search.linkedin_scraper "Python Developer" "Remote" --max-jobs 5

# With browser options
python -m src.scraper.search.linkedin_scraper "Data Scientist" "NYC" --browser firefox --headless

# With anonymization disabled
python -m src.scraper.search.linkedin_scraper "DevOps Engineer" "Berlin" --no-anonymize

# With proxy
python -m src.scraper.search.linkedin_scraper "ML Engineer" "London" --proxy http://proxy:8080
```

**Key Features:**
- ✅ **Multi-browser support** (Chromium, Firefox, WebKit)
- ✅ **Anonymization** (random user agents, timezone, WebGL blocking)
- ✅ **Proxy support** (HTTP/SOCKS5)
- ✅ **Robust data extraction** (job details, company info, hiring team)
- ✅ **Rate limiting protection**

### 🔐 **BugMeNot Scraper**
Get login credentials for job sites:

```bash
# Basic usage
python -m src.scraper.buggmenot --website economist.com

# With browser visible
python -m src.scraper.buggmenot --website nytimes.com --visible

# With proxy
python -m src.scraper.buggmenot --website wsj.com --proxy socks5://proxy:1080
```

### 🤖 **AI Job Processing**
Generate CVs and cover letters (requires AI API key):

```bash
# Process job data and generate documents
python main.py search "Frontend Developer" --locations "Berlin" --generate-cv --generate-cover-letter

# Start API server
python main_api.py
# Visit http://localhost:8000/docs for API documentation
```

---

## 📁 Project Structure

```
JobSearch-Agent/
├── src/scraper/
│   ├── search/linkedin_scraper/    # LinkedIn scraper
│   └── buggmenot/                             # BugMeNot scraper
├── src/agents/                                # AI agents
├── output/                                    # Scraped data & generated files
├── config/                                    # Configuration files
└── docs/                                      # Detailed documentation
```

---

## 📖 Documentation

For detailed instructions and advanced features, see:

- **[LinkedIn Scraper Guide](src/scraper/search/linkedin_scraper/README.md)** - Complete scraper documentation with API usage, CLI options, and performance tips
- **[BugMeNot Scraper Guide](src/scraper/buggmenot/README.md)** - Credential scraper details  
- **[API Documentation](docs/API.md)** - REST API reference
- **[Advanced Configuration](docs/ADVANCED_CONFIGURATION.md)** - Production setup
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing guidelines

---

## ⚡ Common Commands

```bash
# LinkedIn job search with 20 results
python -m src.scraper.search.linkedin_scraper "Software Engineer" "Remote" --max-jobs 20

# LinkedIn search with filters
python -m src.scraper.search.linkedin_scraper "Data Scientist" "SF" --experience-levels "mid_senior" --date-posted "past_week"

# Get job details from specific URL
python -m src.scraper.search.linkedin_scraper --job-url "https://linkedin.com/jobs/view/4243594281/"

# BugMeNot credentials
python -m src.scraper.buggmenot --website glassdoor.com --output credentials.json

# Links only (fast collection)
python -m src.scraper.search.linkedin_scraper "Python" "NYC" --links-only --max-pages 3

# Help for any tool
python -m src.scraper.search.linkedin_scraper --help
python -m src.scraper.buggmenot --help
```

---

## 🛡️ Features

- **🔒 Anonymization**: Random user agents, timezone/language randomization, WebGL/Canvas/WebRTC blocking
- **🌐 Proxy Support**: HTTP and SOCKS5 proxy configuration for both scrapers  
- **📊 Rich Data**: Complete job descriptions, company info, hiring team details, related jobs
- **🚀 Fast & Robust**: Optimized selectors, retry logic, rate limiting protection
- **🔧 Flexible**: CLI arguments, module execution, programmatic usage

---

## ⚠️ Important Notes

- **LinkedIn Login**: Recommended for better scraping results and fewer rate limits
- **Responsible Usage**: Respect rate limits, use delays between requests
- **Browser Support**: Chromium recommended for LinkedIn (best compatibility)
- **Proxy Usage**: For additional anonymization and geographic flexibility

---

## 🤝 Contributing

Contributions welcome! See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Need Help?** 
- Check the [troubleshooting section](docs/ADVANCED_CONFIGURATION.md#troubleshooting) 
- Review [examples](examples/) for usage patterns
- Open an [issue](https://github.com/sreekar2858/JobSearch-Agent/issues) for support
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
