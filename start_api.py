#!/usr/bin/env python
"""
Start script for JobSearch API Server
This script sets up and runs the FastAPI server for the JobSearch Agent
"""

import os
import sys
import subprocess
import argparse


def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import google.adk

        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )


def start_server(host="0.0.0.0", port=8000, reload=True, debug=False):
    """Start the FastAPI server"""
    print(f"Starting JobSearch API server on http://{host}:{port}")

    # Set debug mode if requested
    if debug:
        os.environ["LOG_LEVEL"] = "DEBUG"

    # Start server with uvicorn
    import uvicorn

    uvicorn.run(
        "main_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="debug" if debug else "info",
    )


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start JobSearch API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind the server to"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable automatic reloading on code changes",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--install", action="store_true", help="Install dependencies before starting"
    )

    args = parser.parse_args()

    # Install dependencies if requested
    if args.install:
        install_dependencies()

    # Check dependencies
    if not check_dependencies():
        print("Missing dependencies. Run with --install to install them.")
        return

    # Start server
    start_server(
        host=args.host, port=args.port, reload=not args.no_reload, debug=args.debug
    )


if __name__ == "__main__":
    main()
