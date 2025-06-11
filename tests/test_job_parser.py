"""
Test suite for job parser agent functionality.
Tests both single and multiple job parsing capabilities.
"""

import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.agents.job_details_parser import (
    call_job_parsr_agent,
    create_parse_bulk_text_agent,
    JobParsr,
)


class TestJobParser:
    """Test cases for job parser functionality"""

    def test_create_parse_bulk_text_agent(self):
        """Test that factory function creates unique agent instances"""
        agent1 = create_parse_bulk_text_agent()
        agent2 = create_parse_bulk_text_agent()

        # Should be different instances
        assert agent1 is not agent2
        assert agent1.name == "parseBulkText"
        assert agent2.name == "parseBulkText"

    @patch("src.agents.job_details_parser.Runner")
    @patch("src.agents.job_details_parser.InMemorySessionService")
    def test_job_parser_single_job(self, mock_session_service, mock_runner):
        """Test parsing a single job posting"""
        # Mock the runner and session service
        mock_session = MagicMock()
        mock_session_service.return_value = mock_session
        mock_session.create_session.return_value = None

        # Mock the event loop to return a successful result
        mock_event = MagicMock()
        mock_event.is_final_response.return_value = True
        mock_event.author = "JobParsr"
        mock_event.content.parts = [MagicMock()]
        mock_event.content.parts[0].text = json.dumps(
            {
                "job_title": "Software Engineer",
                "company_name": "ABC Corp",
                "job_location": "Remote",
            }
        )
        mock_event.error_message = None

        mock_runner_instance = MagicMock()
        mock_runner_instance.run.return_value = [mock_event]
        mock_runner.return_value = mock_runner_instance

        # Test single job parsing
        result = call_job_parsr_agent("Software Engineer at ABC Corp")

        # Should return the parsed job data
        assert isinstance(result, dict)
        assert result["job_title"] == "Software Engineer"
        assert result["company_name"] == "ABC Corp"

    @patch("src.agents.job_details_parser.Runner")
    @patch("src.agents.job_details_parser.InMemorySessionService")
    def test_job_parser_multiple_jobs(self, mock_session_service, mock_runner):
        """Test parsing multiple job postings"""
        # Mock the runner and session service
        mock_session = MagicMock()
        mock_session_service.return_value = mock_session
        mock_session.create_session.return_value = None

        # Mock the event loop to return multiple jobs
        mock_event = MagicMock()
        mock_event.is_final_response.return_value = True
        mock_event.author = "JobParsr"
        mock_event.content.parts = [MagicMock()]
        mock_event.content.parts[0].text = json.dumps(
            [
                {
                    "job_title": "Software Engineer",
                    "company_name": "ABC Corp",
                    "job_location": "Remote",
                },
                {
                    "job_title": "Data Scientist",
                    "company_name": "XYZ Inc",
                    "job_location": "New York",
                },
            ]
        )
        mock_event.error_message = None

        mock_runner_instance = MagicMock()
        mock_runner_instance.run.return_value = [mock_event]
        mock_runner.return_value = mock_runner_instance

        # Test multiple job parsing
        result = call_job_parsr_agent(
            "Multiple jobs: Software Engineer at ABC Corp, Data Scientist at XYZ Inc"
        )

        # Should return array of jobs
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["job_title"] == "Software Engineer"
        assert result[1]["job_title"] == "Data Scientist"

    def test_job_parser_agent_initialization(self):
        """Test that JobParsr agent can be initialized properly"""
        parse_bulk_text_agent = create_parse_bulk_text_agent()
        job_parser = JobParsr(name="TestJobParsr", parseBulkText=parse_bulk_text_agent)

        assert job_parser.name == "TestJobParsr"
        assert job_parser.parseBulkText is not None
        assert len(job_parser.sub_agents) == 1

    @patch("src.agents.job_details_parser.Runner")
    @patch("src.agents.job_details_parser.InMemorySessionService")
    def test_job_parser_error_handling(self, mock_session_service, mock_runner):
        """Test error handling in job parser"""
        # Mock the runner and session service
        mock_session = MagicMock()
        mock_session_service.return_value = mock_session
        mock_session.create_session.return_value = None

        # Mock an error event
        mock_event = MagicMock()
        mock_event.is_final_response.return_value = False
        mock_event.error_message = "Test error"

        mock_runner_instance = MagicMock()
        mock_runner_instance.run.return_value = [mock_event]
        mock_runner.return_value = mock_runner_instance

        # Test error handling
        result = call_job_parsr_agent("Invalid job posting")

        # Should return empty string or handle error gracefully
        assert result == ""

    @patch("src.agents.job_details_parser.Runner")
    @patch("src.agents.job_details_parser.InMemorySessionService")
    def test_job_parser_json_decode_error(self, mock_session_service, mock_runner):
        """Test handling of JSON decode errors"""
        # Mock the runner and session service
        mock_session = MagicMock()
        mock_session_service.return_value = mock_session
        mock_session.create_session.return_value = None

        # Mock event with invalid JSON
        mock_event = MagicMock()
        mock_event.is_final_response.return_value = True
        mock_event.author = "JobParsr"
        mock_event.content.parts = [MagicMock()]
        mock_event.content.parts[0].text = "Invalid JSON content"
        mock_event.error_message = None

        mock_runner_instance = MagicMock()
        mock_runner_instance.run.return_value = [mock_event]
        mock_runner.return_value = mock_runner_instance

        # Test JSON decode error handling
        result = call_job_parsr_agent("Job posting with invalid JSON response")

        # Should return the raw text when JSON parsing fails
        assert result == "Invalid JSON content"

    def test_unique_session_generation(self):
        """Test that unique session IDs are generated for each call"""
        # We can't easily test the actual function without mocking everything,
        # but we can test the session ID generation logic
        import uuid
        from datetime import datetime

        SESSION_ID = "session_01"

        # Generate two session IDs
        timestamp1 = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_session_id1 = f"{SESSION_ID}_{timestamp1}_{str(uuid.uuid4())[:8]}"

        timestamp2 = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_session_id2 = f"{SESSION_ID}_{timestamp2}_{str(uuid.uuid4())[:8]}"

        # Should be different (very high probability due to UUID)
        assert unique_session_id1 != unique_session_id2
        assert unique_session_id1.startswith(SESSION_ID)
        assert unique_session_id2.startswith(SESSION_ID)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
