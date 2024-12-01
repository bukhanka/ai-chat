from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import os
import logging
import sys
from pydantic import BaseModel
import chardet
from docx import Document

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.document_analysis import analyze_comprehensive_document
from src.tools import RussianContractAdvisorChat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store advisor instances
advisors: Dict[str, RussianContractAdvisorChat] = {}

# Pydantic models
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    ready_for_recommendation: bool = False

async def get_advisor(user_id: str = "default_user") -> RussianContractAdvisorChat:
    """Get or create advisor instance for user"""
    if user_id not in advisors:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        advisors[user_id] = RussianContractAdvisorChat(
            api_key=api_key,
            user_id=user_id,
            persist_directory="./chroma_db"
        )
        # Explicitly disable RAG mode
        advisors[user_id].toggle_rag_mode(False)
    
    return advisors[user_id]

@app.post("/api/chat")
async def chat(
    message: ChatMessage,
    user_id: str = "default_user",
    advisor: RussianContractAdvisorChat = Depends(get_advisor)
) -> ChatResponse:
    """
    Handle chat messages with contract advisor
    """
    try:
        result = advisor.process_conversation(message.message)
        
        if not result["success"]:
            return ChatResponse(
                success=False,
                error=result.get("error", "Unknown error occurred")
            )
        
        return ChatResponse(
            success=True,
            response=result["response"],
            ready_for_recommendation=result.get("ready_for_recommendation", False)
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(success=False, error=str(e))

@app.post("/api/documents/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    user_id: str = "default_user",
    advisor: RussianContractAdvisorChat = Depends(get_advisor)
):
    """
    Handle document uploads for RAG with robust encoding detection
    """
    temp_files = []
    try:
        files_info = []
        for file in files:
            # Save uploaded file temporarily
            temp_path = f"/tmp/{file.filename}"
            temp_files.append(temp_path)
            
            content = await file.read()
            
            # Detect file encoding
            try:
                if file.filename.endswith('.docx'):
                    # For .docx files, use python-docx library
                    with open(temp_path, "wb") as f:
                        f.write(content)
                    doc = Document(temp_path)
                    # Convert document to plain text
                    text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                    
                    # Re-save as text file
                    temp_text_path = temp_path + '.txt'
                    with open(temp_text_path, 'w', encoding='utf-8') as f:
                        f.write(text_content)
                    
                    files_info.append({
                        'path': temp_text_path,
                        'name': file.filename + '.txt'
                    })
                else:
                    # For other files, detect encoding
                    raw_content = content
                    detected_encoding = chardet.detect(raw_content)['encoding'] or 'utf-8'
                    
                    with open(temp_path, "wb") as f:
                        f.write(content)
                    
                    # Try reading with detected encoding
                    try:
                        with open(temp_path, 'r', encoding=detected_encoding) as f:
                            f.read()
                    except UnicodeDecodeError:
                        # Fallback to utf-8 with error handling
                        detected_encoding = 'utf-8'
                    
                    files_info.append({
                        'path': temp_path,
                        'name': file.filename
                    })
            
            except Exception as file_error:
                logger.error(f"Error processing file {file.filename}: {file_error}")
                files_info.append({
                    'path': None,
                    'name': file.filename,
                    'status': 'error',
                    'message': str(file_error)
                })
        
        # Process the documents
        result = advisor.load_documents(files_info)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )
    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
                # Also remove .txt version if it exists
                if temp_file.endswith('.docx'):
                    txt_file = temp_file + '.txt'
                    if os.path.exists(txt_file):
                        os.unlink(txt_file)
            except Exception as e:
                logger.error(f"Error cleaning up temporary file {temp_file}: {e}")

@app.get("/api/recommendations")
async def get_recommendations(
    user_id: str = "default_user",
    advisor: RussianContractAdvisorChat = Depends(get_advisor)
):
    """
    Get contract recommendations based on conversation history
    """
    try:
        result = advisor.get_contract_recommendation()
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.delete("/api/user/data")
async def clear_user_data(
    user_id: str = "default_user",
    advisor: RussianContractAdvisorChat = Depends(get_advisor)
):
    """
    Clear user's data including vector store and conversation history
    """
    try:
        result = advisor.clear_user_data()
        if user_id in advisors:
            del advisors[user_id]
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error clearing user data: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

# Keep existing document analysis endpoint
@app.post("/api/document/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    api_key: str = os.getenv("OPENAI_API_KEY")
):
    """
    Endpoint for comprehensive document analysis
    
    Args:
        file (UploadFile): Uploaded document file
        api_key (str): OpenAI API key from environment
    
    Returns:
        JSONResponse with comprehensive document analysis results
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Perform comprehensive analysis
        result = analyze_comprehensive_document(api_key, temp_path)
        
        # Ensure the result matches frontend expectations
        comprehensive_result = {
            "success": True,
            "file_path": temp_path,
            "risks": result.get("risks", []),
            "summary": result.get("summary", ""),
            "qa_results": result.get("qa_results", {}),
        }
        
        # Remove temporary file
        os.unlink(temp_path)
        
        return JSONResponse(content=comprehensive_result)
    
    except Exception as e:
        # Log the error and return an error response
        logger.error(f"Document analysis error: {e}")
        return JSONResponse(
            status_code=500, 
            content={
                "success": False, 
                "error": str(e)
            }
        )

# Optional: Add a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# This allows running the app directly with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)