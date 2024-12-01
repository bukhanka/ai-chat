import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from io import BytesIO

# Import the main FastAPI app
from main import app

# Create a test client
client = TestClient(app)

# Utility function to create a test file
def create_test_file(filename="test_document.txt", content="Sample document content"):
    """Create a test file for upload"""
    return {
        "file": (BytesIO(content.encode()), filename)
    }

def test_document_analysis_successful_upload():
    """
    Test successful document upload and analysis
    """
    # Mock the analyze_comprehensive_document function
    with patch('backend.main.analyze_comprehensive_document') as mock_analyze:
        # Setup mock return value
        mock_analyze.return_value = {
            "summary": "Test document summary",
            "key_points": ["Point 1", "Point 2"],
            "analysis_complete": True
        }

        # Prepare test file
        test_file = create_test_file()
        
        # Send request with file and mock API key
        response = client.post(
            "/api/document/analyze", 
            files=test_file,
            data={"api_key": "test_api_key"}
        )

        # Assert response
        assert response.status_code == 200
        result = response.json()
        assert "summary" in result
        assert "key_points" in result
        assert result["analysis_complete"] is True

def test_document_analysis_no_file():
    """
    Test endpoint behavior when no file is uploaded
    """
    response = client.post("/api/document/analyze")
    
    # Expect a 400 Bad Request
    assert response.status_code == 400
    assert "No file uploaded" in response.json()["detail"]

def test_health_check():
    """
    Test the health check endpoint
    """
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.parametrize("file_content", [
    "",  # Empty file
    "Very short content"  # Minimal content
])
def test_document_analysis_edge_cases(file_content):
    """
    Test document analysis with edge case file contents
    """
    with patch('backend.main.analyze_comprehensive_document') as mock_analyze:
        # Setup mock return value
        mock_analyze.return_value = {
            "summary": "Edge case document summary",
            "key_points": [],
            "analysis_complete": True
        }

        # Prepare test file
        test_file = create_test_file(content=file_content)
        
        # Send request with file and mock API key
        response = client.post(
            "/api/document/analyze", 
            files=test_file,
            data={"api_key": "test_api_key"}
        )

        # Assert response
        assert response.status_code == 200
        result = response.json()
        assert "summary" in result