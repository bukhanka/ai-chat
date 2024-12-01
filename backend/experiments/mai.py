import os
from typing import List, Optional, Dict

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate
from langchain.chains.openai_functions import OpenAIFunctionsChain, OpenAIFunctionsModel
from langchain.schema.runnable import RunnablePassthrough, StrOutputParser

from src.document_analysis import EnhancedDocumentAnalyzer

import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(
    title="Legal Document Analysis API",
    description="AI-powered legal document analysis and processing",
    version="0.1.0"
)

# CORS middleware for frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class DocumentQuestionRequest(BaseModel):
    questions: List[str]

    class Config:
        extra = 'ignore'  # Allow extra fields in the request

class DocumentAnalysisResponse(BaseModel):
    success: bool
    risks: Optional[List[dict]] = None
    summary: Optional[str] = None
    qa_results: Optional[dict] = None
    error: Optional[str] = None

@app.post("/analyze/risks", response_model=DocumentAnalysisResponse)
async def analyze_document_risks(file: UploadFile = File(...)):
    """
    Endpoint to analyze risks in a document
    
    Args:
        file (UploadFile): Uploaded document file
    
    Returns:
        DocumentAnalysisResponse with identified risks
    """
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Initialize analyzer
        analyzer = EnhancedDocumentAnalyzer(OPENAI_API_KEY)
        
        # Extract text and analyze risks
        document_text = analyzer._extract_text_from_file(temp_path)
        risks = analyzer._analyze_document_risks(document_text)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return DocumentAnalysisResponse(
            success=True,
            risks=risks
        )
    
    except Exception as e:
        return DocumentAnalysisResponse(
            success=False,
            error=str(e)
        )

@app.post("/analyze/summary", response_model=DocumentAnalysisResponse)
async def generate_document_summary(file: UploadFile = File(...)):
    """
    Endpoint to generate document summary
    
    Args:
        file (UploadFile): Uploaded document file
    
    Returns:
        DocumentAnalysisResponse with document summary
    """
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Initialize analyzer
        analyzer = EnhancedDocumentAnalyzer(OPENAI_API_KEY)
        
        # Extract text and generate summary
        document_text = analyzer._extract_text_from_file(temp_path)
        text_splitter = analyzer.text_splitter
        texts = text_splitter.split_text(document_text)
        docs = [Document(page_content=text) for text in texts]
        
        summary = analyzer._generate_document_summary(docs)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return DocumentAnalysisResponse(
            success=True,
            summary=summary
        )
    
    except Exception as e:
        return DocumentAnalysisResponse(
            success=False,
            error=str(e)
        )

@app.post("/analyze/qa", response_model=DocumentAnalysisResponse)
async def document_question_answering(
    file: UploadFile = File(...), 
    questions: Optional[DocumentQuestionRequest] = None
):
    """
    Endpoint for document Q&A
    """
    try:
        # Log incoming request details
        logger.info(f"Received Q&A request for file: {file.filename}")
        
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Initialize analyzer
        analyzer = EnhancedDocumentAnalyzer(OPENAI_API_KEY)
        
        # Extract text and process Q&A
        document_text = analyzer._extract_text_from_file(temp_path)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000, 
            chunk_overlap=200
        )
        texts = text_splitter.split_text(document_text)
        docs = [Document(page_content=text) for text in texts]
        
        # Handle case when no questions are provided
        question_list = questions.questions if questions and questions.questions else []
        
        qa_results = analyzer._answer_document_questions(
            docs, 
            question_list
        )
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return DocumentAnalysisResponse(
            success=True,
            qa_results=qa_results
        )
    
    except Exception as e:
        logger.error(f"Error in document Q&A: {e}")
        logger.error(traceback.format_exc())
        return DocumentAnalysisResponse(
            success=False,
            error=str(e)
        )

@app.post("/analyze/revise", response_model=DocumentAnalysisResponse)
async def revise_document(file: UploadFile = File(...)):
    """
    Endpoint to revise a document
    
    Args:
        file (UploadFile): Uploaded document file
    
    Returns:
        DocumentAnalysisResponse with revised document
    """
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Initialize analyzer
        analyzer = EnhancedDocumentAnalyzer(OPENAI_API_KEY)
        
        # Extract text and revise document
        document_text = analyzer._extract_text_from_file(temp_path)
        revised_document = analyzer._revise_document(document_text)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return DocumentAnalysisResponse(
            success=True,
            summary=revised_document  # Using summary field for revised document
        )
    
    except Exception as e:
        return DocumentAnalysisResponse(
            success=False,
            error=str(e)
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )
