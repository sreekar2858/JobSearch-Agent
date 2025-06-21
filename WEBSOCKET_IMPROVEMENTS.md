# JobSearch Agent - API & WebSocket Improvements

## Overview

This update enhances the JobSearch Agent with improved API input/output handling, real-time WebSocket search functionality, better loading animations, and similar search detection.

## New Features

### 🔍 Smart Search with Similar Detection
- Automatically checks for recent similar searches before starting new ones
- Suggests using existing results to save time
- Tracks search history with metadata

### ⚡ Real-time WebSocket Search
- Live progress updates during job scraping
- Real-time job count as results are found
- Better error handling and timeout management

### 🎨 Enhanced Loading UI
- Beautiful animated loading indicators
- Stage-based progress visualization
- Responsive design for all screen sizes

### 📊 Improved Result Display
- Better job result formatting
- Enhanced loading states
- Consistent error handling

## Backend Improvements

### WebSocket Endpoint (`/ws`)
- Real-time communication for search operations
- Progress tracking with detailed messages
- Similar search detection with user prompts

### Enhanced API Endpoints
- `/search/check` - Check for similar recent searches
- `/search/history` - Get search history with metadata
- Improved error handling and validation

### Search History Management
- Automatic search deduplication
- Metadata tracking (job counts, timestamps)
- Configurable retention periods

## Frontend Improvements

### Search Component
- Real-time progress display during searches
- Similar search modal with options to reuse or continue
- Enhanced loading states with progress indicators

### JobResults Component
- Improved loading animations
- Better error states
- Consistent result formatting

### New Components
- `LoadingIndicator` - Reusable loading animation component
- `SearchLoadingIndicator` - Specialized search progress component

## Usage Instructions

### 1. Start the Backend API
```bash
cd JobSearch-Agent
python main_api.py
```

### 2. Start the Frontend WebApp
```bash
cd JobSearch-Agent-WebApp
npm install  # if first time
npm run dev
```

### 3. Test the New Features

#### Test WebSocket Connectivity
```bash
cd JobSearch-Agent
python test_api_websocket.py
```

#### Manual Testing Steps
1. **Similar Search Detection:**
   - Perform a search (e.g., "python developer" in "Remote")
   - Wait for completion
   - Perform the same search again
   - Should see a modal asking if you want to reuse results

2. **Real-time Progress:**
   - Start a new search
   - Watch the loading indicator show progress stages
   - See job count update in real-time

3. **Search History:**
   - Click the "History" button in search options
   - View recent searches with job counts
   - Click to rerun previous searches

## Technical Details

### WebSocket Message Format
```json
{
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
```

### Response Types
- `progress` - Search progress updates
- `similar_found` - Similar searches detected
- `result` - Final search results
- `error` - Error messages

### Search History Schema
```json
{
  "search_id": "job_search_20231219_143022",
  "search_hash": "md5_hash_of_parameters",
  "keywords": "python developer",
  "locations": ["Remote"],
  "job_type": "full-time",
  "experience_level": "mid-level",
  "scrapers": ["linkedin"],
  "max_jobs": 3,
  "timestamp": "2023-12-19T14:30:22",
  "status": "completed",
  "job_count": 5
}
```

## Configuration

### Environment Variables
- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

### Search History Settings
- Exact match retention: 24 hours
- Similar search retention: 7 days
- Maximum history entries: 50

## Troubleshooting

### WebSocket Connection Issues
1. Ensure backend is running on port 8000
2. Check firewall settings
3. Verify WebSocket URL in browser console

### Similar Search Not Working
1. Check search history file exists in `output/search_history.json`
2. Verify search parameters are identical
3. Check timestamp filters (24h for exact matches)

### Frontend Loading Issues
1. Verify all imports are correct
2. Check React component state management
3. Ensure WebSocket service is properly initialized

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/search` | POST | Start job search |
| `/search/{id}` | GET | Get search results |
| `/search/check` | POST | Check for similar searches |
| `/search/history` | GET | Get search history |
| `/ws` | WebSocket | Real-time communication |

## Development Notes

### Code Organization
- Backend WebSocket logic in `main_api.py`
- Frontend WebSocket service in `src/services/jobSearchService.ts`
- Loading components in `src/components/common/`
- Search logic in `src/features/tools/Search.tsx`

### Future Enhancements
- [ ] Search result caching
- [ ] Advanced search filters
- [ ] Export search results
- [ ] Search analytics dashboard
- [ ] Multi-language support

## Support

For issues or questions:
1. Check the console logs for WebSocket errors
2. Run the test script to verify connectivity
3. Review the API response status codes
4. Check the search history file for data persistence
