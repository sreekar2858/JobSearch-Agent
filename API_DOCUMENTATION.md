# JobSearch API Documentation

This API allows external applications (like React webapps) to interact with the JobSearch-Agent system through HTTP endpoints and WebSocket connections.

## Setup and Running

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Run the API server:
```bash
python main_api.py
```

The server will start at `http://localhost:8000` by default.

## API Endpoints

### REST API

#### 1. Job Search

**Endpoint**: `POST /search`

Starts a background job search task and returns a search ID.

**Request body**:
```json
{
  "keywords": "Software Engineer",
  "locations": ["Remote", "New York"],
  "job_type": "full-time",
  "experience_level": "mid-level",
  "max_jobs": 3
}
```

**Response**:
```json
{
  "search_id": "job_search_20250515_123456",
  "status": "Job search started"
}
```

#### 2. Get Search Results

**Endpoint**: `GET /search/{search_id}`

Returns the results of a previously started job search.

**Response**:
```json
[
  {
    "job_title": "Senior Software Engineer",
    "company_name": "Example Corp",
    "job_description": "...",
    "job_location": "Remote",
    "posting_date": "2025-05-10",
    "job_type": "Full-time",
    "experience_level": "Senior",
    "skills_required": ["Python", "React"],
    "salary_info": "$120,000 - $150,000",
    "job_url": "https://example.com/jobs/123",
    "source_site": "LinkedIn"
  },
  ...
]
```

#### 3. Parse Job Posting

**Endpoint**: `POST /parse`

Parses job details from text or file content.

**Request body**:
```json
{
  "text": "Job posting text content...",
  "file_content": null
}
```

**Response**: Parsed job data in JSON format

#### 4. Process Job

**Endpoint**: `POST /process`

Processes a job posting to generate a CV and/or cover letter.

**Request body**:
```json
{
  "job_posting": {
    "job_title": "Senior Software Engineer",
    "company_name": "Example Corp",
    "job_description": "..."
  },
  "generate_cv": true,
  "generate_cover_letter": true
}
```

**Response**:
```json
{
  "process_id": "job_process_20250515_123456",
  "status": "Job processing started"
}
```

#### 5. Get Process Results

**Endpoint**: `GET /process/{process_id}`

Returns the results of a previously started job processing task.

### WebSocket API

Connect to `ws://localhost:8000/ws` to establish a WebSocket connection for real-time interaction.

#### Message Format

All WebSocket messages should follow this JSON format:

```json
{
  "action": "search|parse|process",
  "data": {
    // Action-specific data
  }
}
```

#### Response Format

WebSocket responses will be in this JSON format:

```json
{
  "type": "progress|result|error",
  "message": "Progress update or error message",
  "data": {} // For type "result" only
}
```

#### Actions

1. **search**: Start a job search
2. **parse**: Parse job details from text
3. **process**: Process a job to generate documents

## Example Usage with React

See the `examples/react-client-example.jsx` file for a complete example of how to interact with the API from a React application.

## File Downloads

Generated files (CVs, cover letters) can be downloaded from:

```
http://localhost:8000/output/{filepath}
```

Where `{filepath}` is the path returned in the API response.
