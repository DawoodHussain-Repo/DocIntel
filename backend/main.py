"""FastAPI application with PDF upload and SSE streaming endpoints."""
import os
import sys
import uuid
import aiofiles
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from ingestion import process_pdf
from agent import create_agent
from config import config
import json

# Validate configuration on startup
config.validate()

app = FastAPI(title="DocIntel API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent on startup
agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize agent on application startup."""
    global agent
    agent = await create_agent()

@app.post("/api/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    """Upload and process a PDF contract.
    
    Args:
        file: PDF file to process
        
    Returns:
        JSON with status, filename, chunks indexed, and collection name
        
    Raises:
        HTTPException: 400 if not PDF, 413 if too large, 500 on processing error
    """
    
    # Validate file type
    if file.content_type not in config.ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > config.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413, 
            detail=f"File size exceeds {config.MAX_FILE_SIZE_MB}MB limit"
        )
    
    # Save to temp file with UUID
    temp_filename = f"{uuid.uuid4()}.pdf"
    temp_path = f"/tmp/{temp_filename}"
    
    try:
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(content)
        
        # Process PDF
        result = process_pdf(temp_path, file.filename)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/chat/stream")
async def chat_stream(
    query: str = Query(...),
    thread_id: str = Query(...)
):
    """Stream chat responses using SSE.
    
    Args:
        query: User query string
        thread_id: UUID for conversation thread
        
    Returns:
        StreamingResponse with SSE events
        
    Raises:
        HTTPException: 400 if thread_id is invalid UUID
    """
    
    # Validate thread_id is a valid UUID
    try:
        uuid.UUID(thread_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread_id format")
    
    async def event_generator():
        """Generate SSE events from agent stream."""
        try:
            # Create config with thread_id
            config_dict = {
                "configurable": {"thread_id": thread_id}
            }
            
            # Create input
            input_message = {"messages": [HumanMessage(content=query)]}
            
            # Stream events
            async for event in agent.astream_events(input_message, config_dict, version="v1"):
                event_type = event.get("event")
                
                # Tool call event
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "tool_calls") and chunk.tool_calls:
                        for tool_call in chunk.tool_calls:
                            yield f"event: tool_call\n"
                            yield f"data: {json.dumps({'tool': tool_call['name'], 'query': tool_call['args']})}\n\n"
                
                # Token streaming
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield f"event: token\n"
                        yield f"data: {json.dumps({'text': chunk.content})}\n\n"
            
            # Done event
            yield f"event: done\n"
            yield f"data: {json.dumps({'finish_reason': 'stop'})}\n\n"
        
        except Exception as e:
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=config.BACKEND_PORT, reload=True)
