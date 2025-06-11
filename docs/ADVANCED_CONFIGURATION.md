# Advanced Configuration Guide

This document provides detailed configuration options for power users and production environments.

## Environment Configuration

### Complete .env File Example

```env
# LinkedIn Authentication (Recommended)
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_secure_password

# AI Model API Keys
GOOGLE_API_KEY=your_google_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_claude_api_key

# API Configuration
API_HOST=localhost
API_PORT=8000
API_DEBUG=false

# Scraper Configuration
DEFAULT_BROWSER=chrome
HEADLESS_MODE=true
SCRAPER_TIMEOUT=30
DEFAULT_DELAY=2

# Output Configuration
OUTPUT_DIRECTORY=output
ENABLE_DEBUG_SCREENSHOTS=false
ENABLE_ERROR_LOGGING=true
```

## Advanced Scraper Configuration

### Browser Options

```yaml
# config/browser_config.yaml
chrome:
  options:
    - "--no-sandbox"
    - "--disable-dev-shm-usage"
    - "--disable-gpu"
    - "--window-size=1920,1080"
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  
firefox:
  options:
    - "--headless"
    - "--width=1920"
    - "--height=1080"
  profile_preferences:
    "general.useragent.override": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0)"
```

### Rate Limiting Configuration

```yaml
# config/rate_limiting.yaml
delays:
  between_jobs: [2, 5]        # Random delay between job extractions
  between_pages: [10, 20]     # Delay between page loads
  after_captcha: [60, 120]    # Wait time after CAPTCHA detection
  
retries:
  max_attempts: 3
  backoff_factor: 2
  max_backoff: 300
  
limits:
  max_jobs_per_session: 100
  max_pages_per_search: 10
  session_duration_minutes: 60
```

## Production Deployment

### Docker Configuration

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium-browser \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main_api.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jobsearch-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jobsearch-agent
  template:
    metadata:
      labels:
        app: jobsearch-agent
    spec:
      containers:
      - name: jobsearch-agent
        image: jobsearch-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: LINKEDIN_USERNAME
          valueFrom:
            secretKeyRef:
              name: linkedin-credentials
              key: username
        - name: LINKEDIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: linkedin-credentials
              key: password
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

## Monitoring and Logging

### Logging Configuration

```yaml
# config/logging.yaml
version: 1
formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default
    stream: ext://sys.stdout
    
  file:
    class: logging.FileHandler
    level: DEBUG
    formatter: detailed
    filename: logs/jobsearch.log
    
  error_file:
    class: logging.FileHandler
    level: ERROR
    formatter: detailed
    filename: logs/error.log

loggers:
  linkedin_scraper:
    level: DEBUG
    handlers: [console, file]
    propagate: false
    
  api:
    level: INFO
    handlers: [console, file]
    propagate: false

root:
  level: WARNING
  handlers: [console, error_file]
```

### Performance Monitoring

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Metrics for scraping performance
jobs_scraped_total = Counter('jobs_scraped_total', 'Total jobs scraped')
scraping_duration = Histogram('scraping_duration_seconds', 'Time spent scraping')
active_sessions = Gauge('active_sessions', 'Number of active scraping sessions')
captcha_encounters = Counter('captcha_encounters_total', 'Number of CAPTCHAs encountered')
```

## Security Configuration

### API Security

```yaml
# config/security.yaml
api:
  enable_cors: true
  allowed_origins:
    - "http://localhost:3000"
    - "https://your-frontend.com"
  
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    burst_size: 10
    
  authentication:
    type: "api_key"  # or "jwt"
    required_endpoints:
      - "/search"
      - "/process"
    
security:
  encrypt_credentials: true
  api_key_rotation_days: 30
  session_timeout_minutes: 30
```

### Data Privacy

```yaml
# config/privacy.yaml
data_handling:
  anonymize_personal_data: true
  retention_days: 90
  
  excluded_fields:
    - "hiring_team.email"
    - "hiring_team.phone"
    
scraping:
  respect_robots_txt: true
  user_agent_rotation: true
  ip_rotation: false  # Set to true if using proxy pool
```

## Performance Tuning

### Memory Optimization

```yaml
# config/performance.yaml
memory:
  max_heap_size: "2g"
  batch_size: 25
  enable_garbage_collection: true
  
browser:
  max_concurrent_tabs: 3
  tab_timeout_seconds: 300
  enable_image_loading: false
  enable_javascript: true
  
caching:
  enable_job_cache: true
  cache_duration_hours: 24
  max_cache_size_mb: 500
```

### Database Configuration

```yaml
# config/database.yaml
database:
  type: "sqlite"  # or "postgresql", "mysql"
  path: "data/jobsearch.db"
  
  # For PostgreSQL/MySQL
  host: "localhost"
  port: 5432
  username: "jobsearch"
  password: "secure_password"
  database: "jobsearch_db"
  
  connection_pool:
    min_connections: 5
    max_connections: 20
    
migration:
  auto_migrate: true
  backup_before_migration: true
```

## Custom Integrations

### Webhook Configuration

```yaml
# config/webhooks.yaml
webhooks:
  job_found:
    url: "https://your-server.com/webhook/job-found"
    method: "POST"
    headers:
      Authorization: "Bearer your-token"
    
  scraping_complete:
    url: "https://your-server.com/webhook/complete"
    method: "POST"
    
  error_occurred:
    url: "https://your-server.com/webhook/error"
    method: "POST"
```

### Custom AI Models

```yaml
# config/custom_models.yaml
models:
  custom_parser:
    type: "huggingface"
    model_name: "microsoft/DialoGPT-medium"
    api_endpoint: "https://api-inference.huggingface.co"
    
  local_model:
    type: "ollama"
    model_name: "llama2"
    endpoint: "http://localhost:11434"
    
model_routing:
  job_parsing: "custom_parser"
  cv_generation: "openai:gpt-4"
  cover_letter: "local_model"
```
