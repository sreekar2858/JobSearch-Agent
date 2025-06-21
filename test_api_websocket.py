#!/usr/bin/env python3
"""
Simple test script to verify the JobSearch API WebSocket functionality
"""

import asyncio
import json
import websockets
import requests
from datetime import datetime

API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

async def test_websocket_search():
    """Test WebSocket search functionality"""
    print("[TEST] Testing WebSocket Search...")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            # Send search request
            search_message = {
                "action": "search",
                "data": {
                    "keywords": "python developer",
                    "locations": ["Remote"],
                    "job_type": "full-time",
                    "experience_level": "mid-level",
                    "max_jobs": 3,
                    "scrapers": ["linkedin"]
                }
            }
            
            print(f"[SEND] Sending search request: {search_message['data']['keywords']}")
            await websocket.send(json.dumps(search_message))
            
            # Listen for responses
            progress_count = 0
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60.0)  # Increased timeout
                    response = json.loads(message)
                    
                    print(f"[RECV] Received: {response['type']}")
                    
                    if response['type'] == 'progress':
                        progress_count += 1
                        print(f"   Progress {progress_count}: {response['message']}")
                    elif response['type'] == 'similar_found':
                        print(f"   Similar searches found: {len(response['data']['exact_matches'])} exact, {len(response['data']['similar_searches'])} similar")
                        
                        # Show details of similar searches
                        if response['data']['exact_matches']:
                            print(f"   [EXACT] Recent exact matches:")
                            for match in response['data']['exact_matches']:
                                print(f"     * {match.get('keywords', 'N/A')} ({match.get('job_count', 0)} jobs)")
                        
                        if response['data']['similar_searches']:
                            print(f"   [SIMILAR] Similar searches:")
                            for similar in response['data']['similar_searches']:
                                print(f"     * {similar.get('keywords', 'N/A')} ({similar.get('job_count', 0)} jobs)")
                        break
                    elif response['type'] == 'result':
                        jobs = response['data'].get('jobs', [])
                        print(f"   Search completed! Found {len(jobs)} jobs")
                        print(f"   Search ID: {response['data']['search_id']}")
                        
                        # Show first few jobs if available
                        if jobs:
                            print(f"   [JOBS] Sample jobs:")
                            for i, job in enumerate(jobs[:2]):
                                print(f"     {i+1}. {job.get('job_title', 'N/A')} at {job.get('company_name', 'N/A')}")
                                print(f"        Location: {job.get('job_location', 'N/A')}")
                                if job.get('salary_info'):
                                    print(f"        Salary: {job.get('salary_info')}")
                        else:
                            print(f"   [WARN] No jobs returned in results")
                        break
                    elif response['type'] == 'error':
                        print(f"   [ERROR] Error: {response['message']}")
                        break
                        
                except asyncio.TimeoutError:
                    print("   [TIMEOUT] Request timed out after 60 seconds")
                    break
                    
            print(f"   [STATS] Total progress messages received: {progress_count}")
                    
    except Exception as e:
        print(f"[ERROR] WebSocket test failed: {e}")
        print(f"   Make sure the backend is running on {API_BASE_URL}")

async def test_similar_search_scenario():
    """Test similar search detection by running same search twice"""
    print("\n[TEST] Testing Similar Search Detection...")
    
    search_params = {
        "keywords": "javascript developer",
        "locations": ["New York"],
        "job_type": "full-time",
        "experience_level": "senior-level",
        "max_jobs": 2,
        "scrapers": ["linkedin"]
    }
    
    try:
        # First, run a regular REST search to create history
        print("[INIT] Creating initial search via REST API...")
        response = requests.post(f"{API_BASE_URL}/search", json=search_params)
        if response.status_code == 200:
            search_data = response.json()
            print(f"[SUCCESS] Initial search started: {search_data.get('search_id', 'N/A')}")
            
            # Wait a bit for the search to process
            await asyncio.sleep(2)
            
            # Now test WebSocket with same parameters (should detect similarity)
            print("[TEST] Testing WebSocket with same parameters...")
            async with websockets.connect(WS_URL) as websocket:
                search_message = {"action": "search", "data": search_params}
                await websocket.send(json.dumps(search_message))
                
                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response = json.loads(message)
                
                if response['type'] == 'similar_found':
                    print("[SUCCESS] Similar search detection working correctly!")
                elif response['type'] == 'progress':
                    print("[WARN] Similar search detection might not be working - got progress instead")
                else:
                    print(f"[INFO] Unexpected response: {response['type']}")
        else:
            print(f"[ERROR] Failed to create initial search: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Similar search test failed: {e}")

def test_rest_api():
    """Test REST API endpoints"""
    print("\n[TEST] Testing REST API...")
    
    try:
        # Test health check
        print("[HEALTH] Testing health check...")
        response = requests.get(f"{API_BASE_URL}/")
        print(f"[RESPONSE] Health check: {response.status_code} - {response.json()}")
        
        # Test search history
        print("[HISTORY] Testing search history...")
        response = requests.get(f"{API_BASE_URL}/search/history")
        if response.status_code == 200:
            history = response.json()
            print(f"[SUCCESS] Found {len(history['searches'])} searches in history")
        else:
            print(f"[ERROR] History request failed: {response.status_code}")
            
        # Test similar search check
        print("[SIMILAR] Testing similar search check...")
        search_params = {
            "keywords": "python developer",
            "locations": ["Remote"],
            "job_type": "full-time",
            "experience_level": "mid-level",
            "max_jobs": 3,
            "scrapers": ["linkedin"]
        }
        
        response = requests.post(f"{API_BASE_URL}/search/check", json=search_params)
        if response.status_code == 200:
            similar = response.json()
            print(f"[SUCCESS] Similar searches: {len(similar['exact_matches'])} exact, {len(similar['similar_searches'])} similar")
        else:
            print(f"[ERROR] Similar search check failed: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] REST API test failed: {e}")

async def main():
    """Run all tests"""
    print("[START] Starting JobSearch API Tests")
    print("=" * 50)
    
    # Test REST API first
    test_rest_api()
    
    # Test WebSocket
    await test_websocket_search()
    
    # Test similar search detection
    await test_similar_search_scenario()
    
    print("\n[COMPLETE] All tests completed!")
    print("\n[SUMMARY] Summary:")
    print("   1. REST API health check and endpoints")
    print("   2. WebSocket real-time search functionality")
    print("   3. Similar search detection workflow")
    print("\n[NEXT] Next steps:")
    print("   * Open the webapp and test the UI")
    print("   * Try the API test HTML file for interactive testing")
    print("   * Run multiple searches to test similar search detection")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Tests interrupted by user")
    except Exception as e:
        print(f"[ERROR] Test suite failed: {e}")
