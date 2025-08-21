# API Documentation

The JobSearch Agent provides a REST API for integrating with external applications like React web apps. The API is built on a unified pipeline architecture that supports both synchronous and asynchronous job search operations.

## Pipeline Architecture

The API uses a **unified job search pipeline** (`src/utils/job_search_pipeline.py`) that provides:

- **Sync Mode**: For CLI tools and standalone scripts
- **Async Mode**: For FastAPI server and real-time web services  
- **Database Integration**: SQLite storage with automatic deduplication
- **Export Flexibility**: JSON output and database export options

## Getting Started

### Start the Server

```bash
python main_api.py
```

The server runs on `http://localhost:8000` by default.

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Architecture Benefits

The unified pipeline architecture provides:
- **Consistent behavior** between CLI and API modes
- **No code duplication** - single source of truth
- **Automatic deduplication** - prevents duplicate job entries
- **Database-first approach** - persistent storage with optional JSON export
- **Real-time updates** - WebSocket support for live progress tracking

## Authentication

Currently, the API uses basic authentication for LinkedIn credentials through environment variables. Future versions will include API key authentication.

## Endpoints

### Job Search

#### Start Job Search

```http
POST /search
```

**Request Body:**
```json
{
  "keywords": "Software Engineer",
  "location": "Berlin",
  "max_jobs": 10,
  "max_pages": 2,
  "use_login": true
}
```

**Response:**
```json
{
  "search_id": "job_search_20250611_143052",
  "status": "Job search started",
  "estimated_completion": "2024-01-15T10:30:00Z"
}
```

#### Get Search Results

```http
GET /search/{search_id}
```

**Response:**
```json
{
  "search_id": "job_search_20250611_143052",
  "status": "completed",
  "total_jobs": 15,
  "jobs": [
    {
      "url": "https://www.linkedin.com/jobs/view/...",
      "title": "Senior Software Engineer",
      "company": "TechCorp Inc",
      "location": "Berlin, Germany",
      "description": "Full job description...",
      "date_posted": "1 week ago",
      "job_insights": ["Remote", "Full-time", "Mid-Senior level"],
      "easy_apply": false,
      "apply_info": "https://techcorp.com/careers/apply/...",
      "company_info": "About the company...",
      "hiring_team": [...],
      "related_jobs": [...]
    }
  ]
}
```

### Job Processing

#### Parse Job Description

```http
POST /parse
```

**Request Body:**
```json
{
  "text": "Job description text content...",
  "file_content": null
}
```

**Response:**
```json
{
  "title": "Software Engineer",
  "company": "TechCorp",
  "location": "Berlin",
  "requirements": ["Python", "Django", "PostgreSQL"],
  "experience_level": "Mid-Senior",
  "salary_range": "€60,000 - €80,000",
  "job_type": "Full-time",
  "remote_option": true
}
```

#### Generate CV/Cover Letter

```http
POST /process
```

**Request Body:**
```json
{
  "job_data": {
    "title": "Software Engineer",
    "company": "TechCorp",
    "requirements": ["Python", "Django"],
    "description": "Full job description..."
  },
  "generate_cv": true,
  "generate_cover_letter": false,
  "base_cv_path": "data/base_cv.docx"
}
```

**Response:**
```json
{
  "process_id": "process_20250611_143052",
  "status": "Job processing started"
}
```

#### Get Processing Results

```http
GET /process/{process_id}
```

**Response:**
```json
{
  "process_id": "process_20250611_143052",
  "status": "completed",
  "cv_path": "output/cvs/cv_tailored_techcorp_20250611.pdf",
  "cover_letter_path": null,
  "processing_time": "45.2 seconds"
}
```

## WebSocket API

For real-time updates during long-running operations:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Progress update:', data);
};

// Send search request
ws.send(JSON.stringify({
    type: 'search',
    keywords: 'Software Engineer',
    location: 'Berlin'
}));
```

## Error Handling

All endpoints return standardized error responses:

```json
{
  "error": "invalid_request",
  "message": "Missing required field: keywords",
  "details": {
    "field": "keywords",
    "code": "FIELD_REQUIRED"
  }
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limits

- **Job Search**: 10 requests per minute
- **Job Processing**: 5 requests per minute
- **Parse Requests**: 20 requests per minute

## React Integration Example

```jsx
import React, { useState, useEffect } from 'react';

function JobSearch() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);

  const searchJobs = async (keywords, location) => {
    setLoading(true);
    
    // Start search
    const searchResponse = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keywords, location, max_jobs: 20 })
    });
    
    const { search_id } = await searchResponse.json();
    
    // Poll for results
    const pollResults = async () => {
      const resultResponse = await fetch(`/api/search/${search_id}`);
      const data = await resultResponse.json();
      
      if (data.status === 'completed') {
        setJobs(data.jobs);
        setLoading(false);
      } else {
        setTimeout(pollResults, 2000);
      }
    };
    
    pollResults();
  };

  return (
    <div>
      {loading ? (
        <div>Searching for jobs...</div>
      ) : (
        <div>
          {jobs.map(job => (
            <div key={job.url}>
              <h3>{job.title}</h3>
              <p>{job.company} - {job.location}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

## Configuration

### Environment Variables

```env
# API Configuration
API_HOST=localhost
API_PORT=8000
API_DEBUG=false

# LinkedIn Credentials
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password

# Rate Limiting
SEARCH_RATE_LIMIT=10
PROCESS_RATE_LIMIT=5
PARSE_RATE_LIMIT=20
```

### API Settings

Configure in `config/api_config.yaml`:

```yaml
api:
  host: "0.0.0.0"
  port: 8000
  debug: false
  cors_origins: ["http://localhost:3000"]
  
rate_limits:
  search: 10  # per minute
  process: 5  # per minute
  parse: 20   # per minute

scraper:
  default_timeout: 30
  max_retries: 3
  headless: true
```
