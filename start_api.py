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
    required_packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('websockets', 'WebSockets (for real-time functionality)'),
        ('requests', 'Requests (for API testing)'),
    ]
    
    missing = []
    for package, description in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append((package, description))
    
    if missing:
        print("[ERROR] Missing required dependencies:")
        for package, description in missing:
            print(f"   * {package} - {description}")
        return False
    
    print("[OK] All required dependencies are installed")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("[INSTALL] Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "fastapi", "uvicorn[standard]", "websockets", "requests", "beautifulsoup4"
        ])
        print("[SUCCESS] Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("[ERROR] Failed to install dependencies")
        sys.exit(1)

def test_api_connection():
    """Test if the API is responding"""
    import time
    import requests    
    print("[TEST] Testing API connection...")
    
    # Wait a moment for server to start
    time.sleep(2)
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("[OK] API server is responding correctly")
            data = response.json()
            print(f"   Message: {data.get('message', 'N/A')}")
            return True
        else:
            print(f"[WARN] API responded with status {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"[ERROR] Failed to connect to API: {e}")
        return False

def test_websocket_connection():
    """Test WebSocket connectivity"""
    try:
        import asyncio
        import websockets
        import json
        
        async def test_ws():
            try:
                async with websockets.connect("ws://localhost:8000/ws") as websocket:
                    # Send a simple test message
                    test_message = {"action": "test", "data": {}}
                    await websocket.send(json.dumps(test_message))
                    
                    # Try to receive a response (with timeout)
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print("[OK] WebSocket connection successful")
                    return True
            except Exception as e:
                print(f"[ERROR] WebSocket test failed: {e}")
                return False
        
        return asyncio.run(test_ws())
        
    except ImportError:
        print("[WARN] WebSocket testing skipped (websockets package not available)")
        return False
    except Exception as e:
        print(f"[ERROR] WebSocket test error: {e}")
        return False

def run_comprehensive_tests():
    """Run the comprehensive test suite"""
    print("\n[TEST] Running comprehensive API tests...")
    
    if os.path.exists("test_api_websocket.py"):
        try:
            result = subprocess.run([
                sys.executable, "test_api_websocket.py"
            ], timeout=60, capture_output=True, text=True)
            
            print("[RESULTS] Test Results:")
            print(result.stdout)
            
            if result.stderr:
                print("[WARN] Test Warnings:")
                print(result.stderr)
            
            if result.returncode == 0:
                print("[SUCCESS] All tests passed!")
            else:
                print("[WARN] Some tests failed")
                
        except subprocess.TimeoutExpired:
            print("[TIMEOUT] Tests timed out (taking longer than 60 seconds)")
        except Exception as e:
            print(f"[ERROR] Failed to run tests: {e}")
    else:
        print("[WARN] test_api_websocket.py not found, skipping comprehensive tests")


def start_server(host="0.0.0.0", port=8000, reload=True, debug=False, test=False):
    """Start the FastAPI server"""
    print(f"[SERVER] Starting JobSearch API server on http://{host}:{port}")
    print("[DOCS] API Documentation will be available at: http://localhost:8000/docs")
    print("[WS] WebSocket endpoint: ws://localhost:8000/ws")

    # Set debug mode if requested
    if debug:
        os.environ["LOG_LEVEL"] = "DEBUG"

    # Start server with uvicorn in a separate process if testing
    if test:
        import subprocess
        import time
        
        print("[TEST] Starting server in background for testing...")
        server_process = subprocess.Popen([
            sys.executable, "-c",
            f"""
import uvicorn
uvicorn.run("main_api:app", host="{host}", port={port}, log_level="{'debug' if debug else 'info'}")
"""
        ])
        
        # Wait for server to start
        time.sleep(3)
        
        # Test connections
        api_ok = test_api_connection()
        ws_ok = test_websocket_connection()
        
        if api_ok and ws_ok:
            print("\n[SUCCESS] Server started successfully with all features working!")
            run_comprehensive_tests()
        else:
            print("\n[WARN] Server started but some features may not be working correctly")
        
        try:
            input("\n[PAUSE] Press Enter to stop the server...")
        except KeyboardInterrupt:
            pass
        finally:
            print("[STOP] Stopping server...")
            server_process.terminate()
            server_process.wait()
            print("[OK] Server stopped")
            
    else:
        # Start server normally
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
    parser.add_argument(
        "--test", action="store_true", help="Start in test mode with comprehensive testing"
    )

    args = parser.parse_args()

    print("[START] JobSearch Agent API Startup")
    print("=" * 40)

    # Install dependencies if requested
    if args.install:
        install_dependencies()

    # Check dependencies
    if not check_dependencies():
        print("[ERROR] Missing dependencies. Run with --install to install them.")
        return

    print("[OK] All dependencies are installed")

    # Start server
    start_server(
        host=args.host, 
        port=args.port, 
        reload=not args.no_reload, 
        debug=args.debug,
        test=args.test
    )


if __name__ == "__main__":
    main()
