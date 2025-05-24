// Example React component for connecting to JobSearch API
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

// API base URL - update with your actual server URL when deploying
const API_BASE_URL = 'http://localhost:8000';

// WebSocket connection
const useWebSocket = (onMessage) => {
  const socket = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    // Create WebSocket connection
    socket.current = new WebSocket(`ws://localhost:8000/ws`);
    
    socket.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };
    
    socket.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };
    
    socket.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };
    
    socket.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    // Clean up on unmount
    return () => {
      if (socket.current) {
        socket.current.close();
      }
    };
  }, [onMessage]);
  
  // Function to send messages through the WebSocket
  const sendMessage = (action, data) => {
    if (socket.current && isConnected) {
      socket.current.send(JSON.stringify({ action, data }));
    } else {
      console.error('WebSocket not connected');
    }
  };
  
  return { isConnected, sendMessage };
};

// Job Search Component
export const JobSearch = () => {
  const [keywords, setKeywords] = useState('');
  const [location, setLocation] = useState('Remote');
  const [jobType, setJobType] = useState('full-time');
  const [experience, setExperience] = useState('mid-level');
  const [maxJobs, setMaxJobs] = useState(3);
  
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState([]);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  
  // Handle WebSocket messages
  const handleWebSocketMessage = (data) => {
    if (data.type === 'progress') {
      setProgress(prev => [...prev, data.message]);
    } else if (data.type === 'result') {
      setResults(data.data);
      setIsLoading(false);
    } else if (data.type === 'error') {
      setError(data.message);
      setIsLoading(false);
    }
  };
  
  // WebSocket connection
  const { isConnected, sendMessage } = useWebSocket(handleWebSocketMessage);
  
  // Search via WebSocket for real-time updates
  const handleSearch = () => {
    if (!keywords) {
      setError('Please enter search keywords');
      return;
    }
    
    setIsLoading(true);
    setProgress([]);
    setResults([]);
    setError('');
    
    sendMessage('search', {
      keywords,
      locations: [location],
      job_type: jobType,
      experience_level: experience,
      max_jobs: maxJobs
    });
  };
  
  // Get job details via REST API (alternative to WebSocket)
  const handleSearchRest = async () => {
    if (!keywords) {
      setError('Please enter search keywords');
      return;
    }
    
    setIsLoading(true);
    setProgress(['Starting job search...']);
    setResults([]);
    setError('');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/search`, {
        keywords,
        locations: [location],
        job_type: jobType,
        experience_level: experience,
        max_jobs: maxJobs
      });
      
      const searchId = response.data.search_id;
      setProgress(prev => [...prev, `Search started with ID: ${searchId}`]);
      
      // Poll for results
      let resultsFetched = false;
      let attempts = 0;
      
      while (!resultsFetched && attempts < 30) {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
        attempts++;
        
        const resultsResponse = await axios.get(`${API_BASE_URL}/search/${searchId}`);
        
        if (resultsResponse.data.status !== 'in_progress') {
          setResults(resultsResponse.data);
          resultsFetched = true;
          setProgress(prev => [...prev, 'Search completed']);
        } else {
          setProgress(prev => [...prev, 'Still searching...']);
        }
      }
      
      if (!resultsFetched) {
        setError('Search timed out. Please try again.');
      }
      
    } catch (error) {
      setError(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle job selection for processing
  const processJob = (job) => {
    // Navigate to job processing page or open modal
    console.log('Processing job:', job);
    
    // Example: Send to process via WebSocket
    sendMessage('process', {
      job_posting: job,
      generate_cv: true,
      generate_cover_letter: true
    });
  };
  
  return (
    <div className="job-search">
      <h1>Job Search</h1>
      
      <div className="connection-status">
        WebSocket: {isConnected ? '✅ Connected' : '❌ Disconnected'}
      </div>
      
      <div className="search-form">
        <div className="form-group">
          <label>Keywords (Job Title, Skills)</label>
          <input 
            type="text"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="e.g., Software Engineer, Data Scientist"
          />
        </div>
        
        <div className="form-group">
          <label>Location</label>
          <input 
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g., Remote, New York, London"
          />
        </div>
        
        <div className="form-group">
          <label>Job Type</label>
          <select value={jobType} onChange={(e) => setJobType(e.target.value)}>
            <option value="full-time">Full Time</option>
            <option value="part-time">Part Time</option>
            <option value="contract">Contract</option>
            <option value="internship">Internship</option>
          </select>
        </div>
        
        <div className="form-group">
          <label>Experience Level</label>
          <select value={experience} onChange={(e) => setExperience(e.target.value)}>
            <option value="entry">Entry Level</option>
            <option value="mid-level">Mid Level</option>
            <option value="senior">Senior Level</option>
          </select>
        </div>
        
        <div className="form-group">
          <label>Max Jobs Per Site</label>
          <input 
            type="number"
            value={maxJobs}
            onChange={(e) => setMaxJobs(parseInt(e.target.value))}
            min="1"
            max="10"
          />
        </div>
        
        <div className="form-actions">
          <button 
            onClick={handleSearch} 
            disabled={isLoading || !isConnected}
          >
            Search via WebSocket
          </button>
          <button 
            onClick={handleSearchRest} 
            disabled={isLoading}
          >
            Search via REST API
          </button>
        </div>
      </div>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      {isLoading && (
        <div className="progress">
          <h3>Progress</h3>
          <ul>
            {progress.map((message, index) => (
              <li key={index}>{message}</li>
            ))}
          </ul>
        </div>
      )}
      
      {results.length > 0 && (
        <div className="search-results">
          <h3>Found {results.length} Jobs</h3>
          <div className="job-list">
            {results.map((job, index) => (
              <div className="job-card" key={index}>
                <h4>{job.job_title}</h4>
                <p><strong>Company:</strong> {job.company_name}</p>
                <p><strong>Location:</strong> {job.job_location}</p>
                <p><strong>Type:</strong> {job.job_type}</p>
                <button onClick={() => processJob(job)}>Generate Documents</button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Job Processing Component
export const JobProcessor = () => {
  // Implementation for processing a specific job
  // Similar pattern to JobSearch component
  return <div>Job Processor Component</div>;
};

// Job Parser Component
export const JobParser = () => {
  // Implementation for parsing job text
  // Similar pattern to JobSearch component
  return <div>Job Parser Component</div>;
};

// Export a default component that includes all features
const JobSearchApp = () => {
  return (
    <div className="job-search-app">
      <JobSearch />
    </div>
  );
};

export default JobSearchApp;
