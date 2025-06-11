#!/usr/bin/env python
"""
JobSearch API - FastAPI application exposing the JobSearch-Agent functionality.

This API allows external applications (such as a React webapp) to communicate
with the JobSearch-Agent system through HTTP endpoints and WebSocket connections.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, BackgroundTasks, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Import agent functionality
from src.agents.job_details_parser import call_job_parsr_agent
from src.agents.cv_writer import call_cv_agent
from src.agents.coverLetter_writer import call_cover_letter_agent
from src.utils.job_search_pipeline import run_job_search
from src.utils.file_utils import slugify, ensure_dir_exists

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
        search_id = f"job_search_{timestamp}"

        # Run job search in background
        background_tasks.add_task(
            _run_job_search,
            search_id=search_id,
            keywords=request.keywords,
            locations=request.locations,
            job_type=request.job_type,
            experience_level=request.experience_level,
            max_jobs=request.max_jobs,
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
):
    """Background task to run job search"""
    try:
        # Run job search pipeline
        output_file = run_job_search(
            keywords=keywords,
            locations=locations,
            job_type=job_type,
            experience_level=experience_level,
            max_jobs=max_jobs,
        )

        # Create results file with search_id
        result_file = os.path.join(output_dir, f"{search_id}.json")

        # Copy the output to the result file
        with open(output_file, "r", encoding="utf-8") as src:
            with open(result_file, "w", encoding="utf-8") as dst:
                dst.write(src.read())

    except Exception as e:
        # Log the error
        error_file = os.path.join(output_dir, f"{search_id}_error.txt")
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(str(e))


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
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                # Parse the received message
                message_data = json.loads(data)
                action = message_data.get("action")

                if action == "search":
                    # Handle job search via WebSocket
                    await handle_ws_search(websocket, message_data)
                elif action == "parse":
                    # Handle job parsing via WebSocket
                    await handle_ws_parse(websocket, message_data)
                elif action == "process":
                    # Handle job processing via WebSocket
                    await handle_ws_process(websocket, message_data)
                else:
                    await manager.send_error(websocket, f"Unknown action: {action}")

            except json.JSONDecodeError:
                await manager.send_error(websocket, "Invalid JSON format")
            except Exception as e:
                await manager.send_error(websocket, str(e))

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


async def handle_ws_search(websocket: WebSocket, message_data: dict):
    """Handle job search request via WebSocket"""
    try:
        data = message_data.get("data", {})

        keywords = data.get("keywords", "")
        locations = data.get("locations", ["Remote"])
        job_type = data.get("job_type", "full-time")
        experience_level = data.get("experience_level", "mid-level")
        max_jobs = data.get("max_jobs", 3)

        await manager.send_progress(websocket, f"Starting job search for: {keywords}")
        await manager.send_progress(websocket, f"Locations: {', '.join(locations)}")

        # Run job search pipeline
        output_file = run_job_search(
            keywords=keywords,
            locations=locations,
            job_type=job_type,
            experience_level=experience_level,
            max_jobs=max_jobs,
        )

        # Read results
        with open(output_file, "r", encoding="utf-8") as f:
            job_results = json.load(f)

        await manager.send_progress(websocket, f"Found {len(job_results)} job postings")
        await manager.send_result(websocket, job_results)

    except Exception as e:
        await manager.send_error(websocket, str(e))


async def handle_ws_parse(websocket: WebSocket, message_data: dict):
    """Handle job parsing request via WebSocket"""
    try:
        data = message_data.get("data", {})
        text = data.get("text", "")
        file_content = data.get("file_content", "")
        url = data.get("url", "")
        extract_webpage = data.get("extract_webpage", False)

        # Check if we have at least one input source
        if not text and not file_content and not url:
            await manager.send_error(
                websocket, "No input provided for parsing (text, file content, or URL)"
            )
            return

        # Handle URL with web extraction
        if url and extract_webpage:
            await manager.send_progress(
                websocket, f"Extracting content from URL: {url}"
            )

            try:
                import requests
                from bs4 import BeautifulSoup
            except ImportError:
                await manager.send_error(
                    websocket,
                    "Web scraping libraries not installed. Install requests and beautifulsoup4.",
                )
                return

            try:
                # Fetch the webpage content
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                # Parse HTML content
                soup = BeautifulSoup(response.text, "html.parser")

                # Extract the main content
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
                job_content += f"\n\nSource URL: {url}"

                await manager.send_progress(
                    websocket, "Successfully extracted content from webpage"
                )
                text = job_content

            except requests.RequestException as e:
                await manager.send_error(
                    websocket, f"Failed to fetch the webpage: {str(e)}"
                )
                return

        # Use available content
        if not text:
            text = file_content

        await manager.send_progress(websocket, "Parsing job details...")

        # Call the job parser agent
        parsed_data = call_job_parsr_agent(text)

        await manager.send_progress(websocket, "Job details parsed successfully")
        await manager.send_result(websocket, json.loads(parsed_data))

    except Exception as e:
        await manager.send_error(websocket, str(e))


async def handle_ws_process(websocket: WebSocket, message_data: dict):
    """Handle job processing request via WebSocket"""
    try:
        data = message_data.get("data", {})
        job_posting = data.get("job_posting", {})
        generate_cv = data.get("generate_cv", True)
        generate_cover_letter = data.get("generate_cover_letter", False)

        if not job_posting:
            await manager.send_error(websocket, "No job posting provided")
            return

        company = job_posting.get("company_name", "Unknown")
        job_title = job_posting.get("job_title", "Unknown")

        await manager.send_progress(
            websocket, f"Processing job: {job_title} at {company}"
        )

        # Convert job posting to JSON string
        job_details_str = json.dumps(job_posting)

        results = {}

        # Generate CV if requested
        if generate_cv:
            await manager.send_progress(websocket, "Generating customized CV...")
            try:
                cv_text, state_json, cv_path = call_cv_agent(job_details_str)
                results["cv"] = cv_text
                await manager.send_progress(websocket, "CV generated successfully")
            except Exception as e:
                await manager.send_progress(websocket, f"Error generating CV: {str(e)}")
                results["cv_error"] = str(e)

        # Generate cover letter if requested
        if generate_cover_letter:
            await manager.send_progress(websocket, "Generating cover letter...")
            try:
                cover_letter_text, cl_state_json, cl_path = call_cover_letter_agent(
                    job_details_str
                )
                results["cover_letter"] = cover_letter_text
                await manager.send_progress(
                    websocket, "Cover letter generated successfully"
                )
            except Exception as e:
                await manager.send_progress(
                    websocket, f"Error generating cover letter: {str(e)}"
                )
                results["cover_letter_error"] = str(e)

        # Create folder for results to save files
        folder_name = os.path.join(output_dir, slugify(f"{company}_{job_title}"))
        os.makedirs(folder_name, exist_ok=True)

        # Save job metadata
        metadata_path = os.path.join(
            folder_name, f"{company}_{job_title}_metadata.json"
        )
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(job_posting, f, indent=2)

        # Save CV if generated
        if "cv" in results:
            cv_file_path = os.path.join(folder_name, f"{company}_{job_title}_cv.txt")
            with open(cv_file_path, "w", encoding="utf-8") as f:
                f.write(results["cv"])
            # Add file path to results
            results["cv_file"] = cv_file_path.replace(
                os.path.normpath(output_dir), "output"
            )

        # Save cover letter if generated
        if "cover_letter" in results:
            cl_file_path = os.path.join(folder_name, f"{company}_{job_title}.txt")
            with open(cl_file_path, "w", encoding="utf-8") as f:
                f.write(results["cover_letter"])
            # Add file path to results
            results["cover_letter_file"] = cl_file_path.replace(
                os.path.normpath(output_dir), "output"
            )

        await manager.send_progress(websocket, "Job processing completed")
        await manager.send_result(websocket, results)

    except Exception as e:
        await manager.send_error(websocket, str(e))


if __name__ == "__main__":
    # Run the FastAPI app with uvicorn
    uvicorn.run("main_api:app", host="0.0.0.0", port=8000, reload=True)
