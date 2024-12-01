import requests
import os
import pytest

# Configuration for testing
BASE_URL = "http://localhost:8000"  # Adjust if your FastAPI runs on a different port
TEST_DOCUMENT_PATH = "/path/to/your/test/document.docx"  # Replace with an actual test document

def test_document_risks_endpoint():
    """
    Test the document risks analysis endpoint
    """
    with open(TEST_DOCUMENT_PATH, 'rb') as file:
        files = {'file': file}
        
        # Send request to risks endpoint
        response = requests.post(f"{BASE_URL}/analyze/risks", files=files)
        
        # Assertions
        assert response.status_code == 200, "Endpoint should return 200 OK"
        
        result = response.json()
        assert result['success'] is True, "Analysis should be successful"
        assert 'risks' in result, "Result should contain risks"
        
        # Optional: Print risks for manual inspection
        print("Risks Analysis Result:")
        print(result)

def test_document_summary_endpoint():
    """
    Test the document summary generation endpoint
    """
    with open(TEST_DOCUMENT_PATH, 'rb') as file:
        files = {'file': file}
        
        # Send request to summary endpoint
        response = requests.post(f"{BASE_URL}/analyze/summary", files=files)
        
        # Assertions
        assert response.status_code == 200, "Endpoint should return 200 OK"
        
        result = response.json()
        assert result['success'] is True, "Summary generation should be successful"
        assert 'summary' in result, "Result should contain summary"
        
        # Optional: Print summary for manual inspection
        print("Document Summary:")
        print(result['summary'])

def test_document_qa_endpoint():
    """
    Test the document Q&A endpoint
    """
    with open(TEST_DOCUMENT_PATH, 'rb') as file:
        files = {'file': file}
        
        # Prepare questions
        questions = {
            'questions': [
                "What is the main purpose of this document?", 
                "Are there any key dates mentioned?",
                "Who are the primary parties involved?"
            ]
        }
        
        # Send request to Q&A endpoint
        response = requests.post(
            f"{BASE_URL}/analyze/qa", 
            files=files, 
            json=questions
        )
        
        # Assertions
        assert response.status_code == 200, "Endpoint should return 200 OK"
        
        result = response.json()
        assert result['success'] is True, "Q&A should be successful"
        assert 'qa_results' in result, "Result should contain Q&A answers"
        
        # Optional: Print Q&A results for manual inspection
        print("Document Q&A Results:")
        print(result['qa_results'])

def test_document_revision_endpoint():
    """
    Test the document revision endpoint
    """
    with open(TEST_DOCUMENT_PATH, 'rb') as file:
        files = {'file': file}
        
        # Send request to revision endpoint
        response = requests.post(f"{BASE_URL}/analyze/revise", files=files)
        
        # Assertions
        assert response.status_code == 200, "Endpoint should return 200 OK"
        
        result = response.json()
        assert result['success'] is True, "Document revision should be successful"
        assert 'summary' in result, "Result should contain revised document"
        
        # Optional: Print revised document for manual inspection
        print("Revised Document:")
        print(result['summary'])

# Run all tests
if __name__ == "__main__":
    pytest.main([__file__]) 