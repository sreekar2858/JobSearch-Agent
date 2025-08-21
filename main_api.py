#!/usr/bin/env python
"""
JobSearch API - FastAPI application exposing the JobSearch-Agent functionality.

This API allows external applications (such as a React webapp) to communicate
with the JobSearch-Agent system through HTTP endpoints and WebSocket connections.
"""

import os
import sys
import json
import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Fix for Windows Playwright subprocess issue in async context
if sys.platform == "win32":
    # Set Windows ProactorEventLoop policy to fix subprocess NotImplementedError
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Additional Windows subprocess environment setup
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
    
    # Ensure proper subprocess handling on Windows
    import signal
    if hasattr(signal, 'SIGBREAK'):
        signal.signal(signal.SIGBREAK, signal.SIG_DFL)
    if hasattr(signal, 'SIGINT'):
        signal.signal(signal.SIGINT, signal.SIG_DFL)

# Import agent functionality
from src.agents.job_details_parser import call_job_parsr_agent
from src.agents.cv_writer import call_cv_agent
from src.agents.coverLetter_writer import call_cover_letter_agent
from src.utils.job_search_pipeline import run_job_search, run_job_search_async
from src.utils.file_utils import slugify, ensure_dir_exists
from src.utils.job_database import JobDatabase

# Create FastAPI app
app = FastAPI(
    title="JobSearch API",
    description="API for interacting with JobSearch-Agent system",
    version="1.0.0",
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Make output directory available for downloading generated files
output_dir = os.path.join(os.getcwd(), "output")
ensure_dir_exists(output_dir)
app.mount("/output", StaticFiles(directory=output_dir), name="output")


# Define data models
class JobSearchRequest(BaseModel):
    keywords: str
    locations: List[str] = Field(default=["Remote"])
    job_type: str = Field(default="full-time")
    experience_level: str = Field(default="mid-level")
    max_jobs: int = Field(default=3)
    scrapers: List[str] = Field(default=["linkedin"])  # Scraper selection (only LinkedIn working currently)


class JobParseRequest(BaseModel):
    text: Optional[str] = None
    file_content: Optional[str] = None
    url: Optional[str] = None
    extract_webpage: bool = Field(default=False)


class JobProcessRequest(BaseModel):
    job_posting: Dict[str, Any]
    generate_cv: bool = Field(default=True)
    generate_cover_letter: bool = Field(default=False)


class WebSocketMessage(BaseModel):
    action: str
    data: Dict[str, Any]


# Store active websocket connections
active_connections: List[WebSocket] = []


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_progress(self, websocket: WebSocket, message: str):
        if websocket in self.active_connections:
            await websocket.send_json({"type": "progress", "message": message})

    async def send_result(self, websocket: WebSocket, data: Any):
        if websocket in self.active_connections:
            await websocket.send_json({"type": "result", "data": data})

    async def send_error(self, websocket: WebSocket, error: str):
        if websocket in self.active_connections:
            await websocket.send_json({"type": "error", "message": error})


manager = ConnectionManager()


# Search history tracking
search_history_file = os.path.join(output_dir, "search_history.json")

def load_search_history() -> List[Dict[str, Any]]:
    """Load search history from file"""
    if os.path.exists(search_history_file):
        try:
            with open(search_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading search history: {e}")
            return []
    return []

def save_search_history(history: List[Dict[str, Any]]):
    """Save search history to file"""
    try:
        with open(search_history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving search history: {e}")

def generate_search_hash(keywords: str, locations: List[str], job_type: str, 
                        experience_level: str, scrapers: List[str]) -> str:
    """Generate a hash for search parameters to identify duplicates"""
    # Normalize parameters for consistent hashing
    normalized_locations = sorted([loc.lower().strip() for loc in locations])
    normalized_scrapers = sorted([s.lower().strip() for s in scrapers])
    
    search_string = f"{keywords.lower().strip()}|{','.join(normalized_locations)}|{job_type.lower().strip()}|{experience_level.lower().strip()}|{','.join(normalized_scrapers)}"
    return hashlib.md5(search_string.encode()).hexdigest()

def find_similar_searches(keywords: str, locations: List[str], job_type: str, 
                         experience_level: str, scrapers: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Find similar searches in history"""
    search_hash = generate_search_hash(keywords, locations, job_type, experience_level, scrapers)
    history = load_search_history()
    
    # Find exact matches
    exact_matches = [search for search in history if search.get('search_hash') == search_hash]
    
    # Find partial matches (same keywords and job type)
    partial_matches = [search for search in history 
                      if search.get('keywords', '').lower().strip() == keywords.lower().strip() 
                      and search.get('job_type', '').lower().strip() == job_type.lower().strip()
                      and search.get('search_hash') != search_hash]
    
    return {'exact': exact_matches, 'similar': partial_matches}

def add_search_to_history(search_id: str, keywords: str, locations: List[str], 
                         job_type: str, experience_level: str, scrapers: List[str], 
                         max_jobs: int, status: str = "started"):
    """Add a search to history"""
    history = load_search_history()
    search_hash = generate_search_hash(keywords, locations, job_type, experience_level, scrapers)
    
    search_entry = {
        'search_id': search_id,
        'search_hash': search_hash,
        'keywords': keywords,
        'locations': locations,
        'job_type': job_type,
        'experience_level': experience_level,
        'scrapers': scrapers,
        'max_jobs': max_jobs,
        'timestamp': datetime.now().isoformat(),
        'status': status
    }
    
    # Add to beginning of history (most recent first)
    history.insert(0, search_entry)
    
    # Keep only last 50 searches
    history = history[:50]
    
    save_search_history(history)

def update_search_status(search_id: str, status: str, job_count: int = None):
    """Update search status in history"""
    history = load_search_history()
    for search in history:
        if search.get('search_id') == search_id:
            search['status'] = status
            if job_count is not None:
                search['job_count'] = job_count
            break
    save_search_history(history)


# Define API endpoints
@app.get("/")
async def root():
    return {"message": "JobSearch API is running. Access /docs for API documentation."}


@app.post("/search")
async def search_jobs(request: JobSearchRequest, background_tasks: BackgroundTasks):
    """
    Search for jobs based on provided criteria.
    Returns a job ID that can be used to fetch results.
    """
    try:
        # Generate unique ID for this search
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        search_id = f"job_search_{timestamp}"        # Run job search in background
        background_tasks.add_task(
            _run_job_search,
            search_id=search_id,
            keywords=request.keywords,
            locations=request.locations,
            job_type=request.job_type,
            experience_level=request.experience_level,
            max_jobs=request.max_jobs,
            scrapers=request.scrapers,
        )

        # Add search to history
        add_search_to_history(
            search_id=search_id,
            keywords=request.keywords,
            locations=request.locations,
            job_type=request.job_type,
            experience_level=request.experience_level,
            scrapers=request.scrapers,
            max_jobs=request.max_jobs,
            status="started",
        )

        return {"search_id": search_id, "status": "Job search started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _run_job_search(
    search_id: str,
    keywords: str,
    locations: List[str],
    job_type: str,
    experience_level: str,
    max_jobs: int,
    scrapers: List[str],
):
    """Background task to run job search"""
    try:
        # Use synchronous version that works reliably on Windows
        # Run in thread pool to avoid blocking the event loop
        import asyncio
        loop = asyncio.get_event_loop()
        
        output_file = await loop.run_in_executor(
            None,
            run_job_search,  # Use sync version
            keywords,
            locations,
            job_type,
            experience_level,
            max_jobs,
            scrapers,
        )

        # Create results file with search_id
        result_file = os.path.join(output_dir, f"{search_id}.json")

        # If output_file is None (database-only mode), create an empty results file
        if output_file is None:
            # Get results from database
            db = JobDatabase()
            try:
                jobs = db.get_jobs(limit=max_jobs)
                results = []
                for job in jobs:
                    job_dict = dict(job)
                    # Parse JSON fields back to objects
                    for field in ['job_insights', 'apply_info', 'company_info', 'hiring_team', 'related_jobs']:
                        if job_dict.get(field):
                            try:
                                job_dict[field] = json.loads(job_dict[field])
                            except (json.JSONDecodeError, TypeError):
                                pass
                    results.append(job_dict)
                
                with open(result_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                job_count = len(results)
            finally:
                db.close()
        else:
            # Copy the output to the result file
            with open(output_file, "r", encoding="utf-8") as src:
                content = src.read()
                with open(result_file, "w", encoding="utf-8") as dst:
                    dst.write(content)
            
            # Get actual job count from results
            try:
                results = json.loads(content)
                job_count = len(results) if isinstance(results, list) else 0
            except:
                job_count = 0

        # Update search status in history
        update_search_status(search_id, status="completed", job_count=job_count)

    except Exception as e:
        # Log the error
        error_file = os.path.join(output_dir, f"{search_id}_error.txt")
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(str(e))

        # Create empty results file to prevent returning old database jobs
        result_file = os.path.join(output_dir, f"{search_id}.json")
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump([], f)

        # Update search status to error
        update_search_status(search_id, status="error")


@app.get("/search/{search_id}")
async def get_search_results(search_id: str):
    """Get the results of a job search by ID"""
    result_file = os.path.join(output_dir, f"{search_id}.json")
    error_file = os.path.join(output_dir, f"{search_id}_error.txt")

    if os.path.exists(result_file):
        with open(result_file, "r", encoding="utf-8") as f:
            return json.load(f)
    elif os.path.exists(error_file):
        with open(error_file, "r", encoding="utf-8") as f:
            error = f.read()
        raise HTTPException(status_code=500, detail=error)
    else:
        return {"status": "in_progress", "message": "Job search is still running"}


@app.post("/parse")
async def parse_job_posting(request: JobParseRequest):
    """Parse job details from text, file content, or URL"""
    try:
        # Check if we have required input data
        if not request.text and not request.file_content and not request.url:
            raise HTTPException(
                status_code=400,
                detail="Either text, file_content, or url must be provided",
            )

        # If URL is provided and extract_webpage is True, set the input type to URL
        if request.url and request.extract_webpage:
            # Import web scraping libraries (install if needed)
            try:
                import requests
                from bs4 import BeautifulSoup
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="Web scraping libraries not installed. Install requests and beautifulsoup4.",
                )

            try:
                # Fetch the webpage content
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(request.url, headers=headers, timeout=10)
                response.raise_for_status()

                # Parse HTML content
                soup = BeautifulSoup(response.text, "html.parser")

                # Extract the main content (this is a simple extraction, can be improved)
                job_content = ""

                # Try to find job description container
                job_description = soup.find(
                    "div", class_=["job-description", "description", "jobDescription"]
                )
                if job_description:
                    job_content = job_description.get_text(separator="\n")
                else:
                    # If no specific job container found, extract main content
                    main_content = (
                        soup.find("main") or soup.find("article") or soup.find("body")
                    )
                    job_content = main_content.get_text(separator="\n")

                # Add the URL as a source
                job_content += f"\n\nSource URL: {request.url}"

                # Call the job parser agent with the extracted content
                parsed_data = call_job_parsr_agent(job_content)

                # Return parsed data as JSON
                return json.loads(parsed_data)

            except requests.RequestException as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to fetch the webpage: {str(e)}"
                )
        else:
            # Use text if provided, otherwise use file_content
            text_to_parse = request.text if request.text else request.file_content

            # Call the job parser agent
            parsed_data = call_job_parsr_agent(text_to_parse)

            # Return parsed data as JSON
            return json.loads(parsed_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process")
async def process_job(request: JobProcessRequest, background_tasks: BackgroundTasks):
    """
    Process a job posting to generate CV and/or cover letter
    Returns a process_id that can be used to fetch results
    """
    try:
        # Generate unique ID for this process
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        process_id = f"job_process_{timestamp}"

        # Run process in background
        background_tasks.add_task(
            _run_job_process,
            process_id=process_id,
            job_posting=request.job_posting,
            generate_cv=request.generate_cv,
            generate_cover_letter=request.generate_cover_letter,
        )

        return {"process_id": process_id, "status": "Job processing started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _run_job_process(
    process_id: str,
    job_posting: Dict[str, Any],
    generate_cv: bool,
    generate_cover_letter: bool,
):
    """Background task to process job posting"""
    try:
        # Convert job posting to json string
        job_details_str = json.dumps(job_posting)

        # Create folder for results
        company = job_posting.get("company_name", "Unknown")
        job_title = job_posting.get("job_title", "Job")
        folder_name = os.path.join(output_dir, slugify(f"{company}_{job_title}"))
        os.makedirs(folder_name, exist_ok=True)

        results = {"status": "completed", "files": {}}

        # Save job metadata
        metadata_path = os.path.join(
            folder_name, f"{company}_{job_title}_metadata.json"
        )
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(job_posting, f, indent=2)
        results["files"]["metadata"] = metadata_path.replace(
            os.path.normpath(output_dir), "output"
        )

        # Generate CV if requested
        if generate_cv:
            try:
                cv_text, state_json, cv_path = call_cv_agent(job_details_str)
                # Save the CV text
                cv_file_path = os.path.join(
                    folder_name, f"{company}_{job_title}_cv.txt"
                )
                with open(cv_file_path, "w", encoding="utf-8") as cv_file:
                    cv_file.write(cv_text)
                results["files"]["cv"] = cv_file_path.replace(
                    os.path.normpath(output_dir), "output"
                )
            except Exception as e:
                results["cv_error"] = str(e)

        # Generate cover letter if requested
        if generate_cover_letter:
            try:
                cover_letter_text, cl_state_json, cl_path = call_cover_letter_agent(
                    job_details_str
                )
                cl_file_path = os.path.join(folder_name, f"{company}_{job_title}.txt")
                with open(cl_file_path, "w", encoding="utf-8") as cl_file:
                    cl_file.write(cover_letter_text)
                results["files"]["cover_letter"] = cl_file_path.replace(
                    os.path.normpath(output_dir), "output"
                )
            except Exception as e:
                results["cover_letter_error"] = str(e)

        # Write results file
        with open(
            os.path.join(output_dir, f"{process_id}.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(results, f, indent=2)

    except Exception as e:
        # Log the error
        with open(
            os.path.join(output_dir, f"{process_id}_error.txt"), "w", encoding="utf-8"
        ) as f:
            f.write(str(e))


@app.get("/process/{process_id}")
async def get_process_results(process_id: str):
    """Get the results of a job processing task by ID"""
    result_file = os.path.join(output_dir, f"{process_id}.json")
    error_file = os.path.join(output_dir, f"{process_id}_error.txt")

    if os.path.exists(result_file):
        with open(result_file, "r", encoding="utf-8") as f:
            return json.load(f)
    elif os.path.exists(error_file):
        with open(error_file, "r", encoding="utf-8") as f:
            error = f.read()
        raise HTTPException(status_code=500, detail=error)
    else:
        return {"status": "in_progress", "message": "Job processing is still running"}


# WebSocket endpoint for real-time interaction with agents
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    try:
        while True:            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            
            if action == "search":
                await handle_ws_search(websocket, message)
            else:
                await manager.send_error(websocket, f"Unknown action: {action}")
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

async def handle_ws_search(websocket: WebSocket, message_data: dict):
    """Handle job search request via WebSocket with real-time progress"""
    try:
        data = message_data.get("data", {})
        
        # Extract search parameters
        keywords = data.get("keywords", "")
        locations = data.get("locations", ["Remote"])
        job_type = data.get("job_type", "full-time")
        experience_level = data.get("experience_level", "mid-level")
        max_jobs = data.get("max_jobs", 3)
        scrapers = data.get("scrapers", ["linkedin"])
        
        if not keywords:
            await manager.send_error(websocket, "Keywords are required")
            return
            
        # Generate unique ID for this search
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        search_id = f"job_search_{timestamp}"
        
        await manager.send_progress(websocket, f"Starting job search: {keywords}")
        
        # Check for similar searches first
        await manager.send_progress(websocket, "Checking for similar recent searches...")
        similar_searches = find_similar_searches(
            keywords=keywords,
            locations=locations, 
            job_type=job_type,
            experience_level=experience_level,
            scrapers=scrapers
        )
        
        # Check if we have recent exact matches
        now = datetime.now()
        recent_exact = []
        for search in similar_searches['exact']:
            search_time = datetime.fromisoformat(search['timestamp'])
            if (now - search_time).total_seconds() < 86400:  # 24 hours
                result_file = os.path.join(output_dir, f"{search['search_id']}.json")
                if os.path.exists(result_file):
                    recent_exact.append(search)
        
        if recent_exact:
            await manager.send_progress(websocket, "Found recent similar search results")
            # Send the similar searches for user decision
            await websocket.send_json({
                "type": "similar_found",
                "data": {
                    "exact_matches": recent_exact,
                    "similar_searches": similar_searches['similar'][:3],
                    "search_id": search_id
                }
            })
            return
        
        # No recent matches, proceed with new search
        await manager.send_progress(websocket, "No recent similar searches found, starting new search...")
        
        # Add search to history
        add_search_to_history(
            search_id=search_id,
            keywords=keywords,
            locations=locations,
            job_type=job_type,
            experience_level=experience_level,
            scrapers=scrapers,
            max_jobs=max_jobs,
            status="started",
        )
        
        # Run job search with progress updates
        await _run_job_search_with_websocket(
            websocket,
            search_id=search_id,
            keywords=keywords,
            locations=locations,
            job_type=job_type,
            experience_level=experience_level,
            max_jobs=max_jobs,
            scrapers=scrapers,
        )
        
    except Exception as e:
        await manager.send_error(websocket, str(e))

async def _run_job_search_with_websocket(
    websocket: WebSocket,
    search_id: str,
    keywords: str,
    locations: List[str],
    job_type: str,
    experience_level: str,
    max_jobs: int,
    scrapers: List[str],
):
    """Background task to run job search with WebSocket progress updates"""
    try:
        await manager.send_progress(websocket, f"Initializing scrapers: {', '.join(scrapers)}")
        
        # Initialize progress tracking
        progress_steps = [
            "Setting up search parameters",
            "Starting web scrapers",
            "Scraping job listings",
            "Processing job data",
            "Filtering and cleaning results",
            "Finalizing search results"
        ]
        
        for i, step in enumerate(progress_steps):
            await manager.send_progress(websocket, f"Step {i+1}/{len(progress_steps)}: {step}")
            await asyncio.sleep(0.5)  # Small delay for realistic progress
        
        # Run job search pipeline using sync version in thread pool
        await manager.send_progress(websocket, "Running job search pipeline...")
        
        loop = asyncio.get_event_loop()
        output_file = await loop.run_in_executor(
            None,
            run_job_search,  # Use sync version
            keywords,
            locations,
            job_type,
            experience_level,
            max_jobs,
            scrapers,
        )

        # Create results file with search_id
        result_file = os.path.join(output_dir, f"{search_id}.json")
        
        # Handle both database-only and file output modes
        if output_file is None:
            # Get results from database
            db = JobDatabase()
            try:
                jobs = db.get_jobs(limit=max_jobs)
                results = []
                for job in jobs:
                    job_dict = dict(job)
                    # Parse JSON fields back to objects
                    for field in ['job_insights', 'apply_info', 'company_info', 'hiring_team', 'related_jobs']:
                        if job_dict.get(field):
                            try:
                                job_dict[field] = json.loads(job_dict[field])
                            except (json.JSONDecodeError, TypeError):
                                pass
                    results.append(job_dict)
                
                with open(result_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                job_count = len(results)
            finally:
                db.close()
        else:
            # Copy the output to the result file
            with open(output_file, "r", encoding="utf-8") as src:
                content = src.read()
                with open(result_file, "w", encoding="utf-8") as dst:
                    dst.write(content)
            
            # Get actual job count from results
            try:
                results = json.loads(content)
                job_count = len(results) if isinstance(results, list) else 0
            except:
                job_count = 0
                results = []

        await manager.send_progress(websocket, f"Search completed! Found {job_count} jobs")

        # Update search status in history
        update_search_status(search_id, status="completed", job_count=job_count)
        
        # Send final results
        await manager.send_result(websocket, {
            "search_id": search_id,
            "jobs": results,
            "job_count": job_count,
            "status": "completed"
        })

    except Exception as e:
        # Log the error
        error_file = os.path.join(output_dir, f"{search_id}_error.txt")
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(str(e))

        # Create empty results file to prevent returning old database jobs
        result_file = os.path.join(output_dir, f"{search_id}.json")
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump([], f)

        # Update search status to error
        update_search_status(search_id, status="error")
        await manager.send_error(websocket, f"Search failed: {str(e)}")

@app.post("/search/check")
async def check_similar_searches(request: JobSearchRequest):
    """Check for existing/similar searches before starting a new one"""
    try:
        similar_searches = find_similar_searches(
            keywords=request.keywords,
            locations=request.locations,
            job_type=request.job_type,
            experience_level=request.experience_level,
            scrapers=request.scrapers
        )
        
        # Filter out old searches (older than 24 hours) for exact matches
        now = datetime.now()
        recent_exact = []
        for search in similar_searches['exact']:
            search_time = datetime.fromisoformat(search['timestamp'])
            if (now - search_time).total_seconds() < 86400:  # 24 hours
                # Check if results file exists
                result_file = os.path.join(output_dir, f"{search['search_id']}.json")
                if os.path.exists(result_file):
                    # Add job count if available
                    try:
                        with open(result_file, 'r', encoding='utf-8') as f:
                            results = json.load(f)
                            search['job_count'] = len(results) if isinstance(results, list) else 0
                    except:
                        search['job_count'] = 0
                    recent_exact.append(search)
        
        # Get recent similar searches (last 7 days)
        recent_similar = []
        for search in similar_searches['similar'][:5]:  # Limit to 5 most recent
            search_time = datetime.fromisoformat(search['timestamp'])
            if (now - search_time).total_seconds() < 604800:  # 7 days
                result_file = os.path.join(output_dir, f"{search['search_id']}.json")
                if os.path.exists(result_file):
                    try:
                        with open(result_file, 'r', encoding='utf-8') as f:
                            results = json.load(f)
                            search['job_count'] = len(results) if isinstance(results, list) else 0
                    except:
                        search['job_count'] = 0
                    recent_similar.append(search)
        
        return {
            "exact_matches": recent_exact,
            "similar_searches": recent_similar,
            "has_recent_exact": len(recent_exact) > 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/history")
async def get_search_history(limit: int = 20):
    """Get recent search history"""
    try:
        history = load_search_history()
        
        # Add job counts and filter valid searches
        valid_history = []
        for search in history[:limit]:
            result_file = os.path.join(output_dir, f"{search['search_id']}.json")
            if os.path.exists(result_file):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                        search['job_count'] = len(results) if isinstance(results, list) else 0
                        search['has_results'] = True
                except:
                    search['job_count'] = 0
                    search['has_results'] = False
                valid_history.append(search)
        
        return {"searches": valid_history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DATABASE ENDPOINTS
# ============================================================================

@app.get("/jobs/stats")
async def get_job_stats():
    """Get database statistics"""
    try:
        db = JobDatabase()
        stats = db.get_stats()
        db.close()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs")
async def get_jobs(limit: int = 100, offset: int = 0):
    """Get jobs from database with pagination"""
    try:
        db = JobDatabase()
        jobs = db.get_jobs(limit=limit, offset=offset)
        db.close()
        return {"success": True, "data": jobs, "count": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/search")
async def search_jobs(keyword: str = None, company: str = None, location: str = None):
    """Search jobs in database"""
    try:
        db = JobDatabase()
        jobs = db.search_jobs(keyword=keyword, company=company, location=location)
        db.close()
        return {"success": True, "data": jobs, "count": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}")
async def get_job(job_id: int):
    """Get a specific job by ID"""
    try:
        db = JobDatabase()
        job = db.get_job(job_id)        
        db.close()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"success": True, "data": job}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jobs/migrate")
async def migrate_jobs():
    """Migrate existing JSON files to database"""
    try:
        import glob
        
        # Find all JSON files in jobs directory
        json_files = glob.glob("jobs/*.json")
        if not json_files:
            return {"success": True, "message": "No JSON files found to migrate", "migrated": 0}
        
        db = JobDatabase()
        migrated_count = db.migrate_from_json(json_files)
        stats = db.get_stats()
        db.close()
        
        return {
            "success": True, 
            "message": f"Migration completed. {migrated_count} jobs migrated.",
            "migrated": migrated_count,
            "total_in_db": stats["total_jobs"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Don't force Windows compatibility here - let the browser manager handle it
    # Run the FastAPI app with uvicorn
    uvicorn.run("main_api:app", host="0.0.0.0", port=8000, reload=True)
