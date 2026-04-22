import os
import uuid
import aiofiles
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from backend.ingestion import process_pdf
from backend.agent import create_agent
from dotenv import load_dotenv
import json
import asyncio

load_dotenv()

app = FastAPI(title="DocIntel API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
agent = create_agent()

@app.post("/api/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    """Upload and process a PDF contract."""
    
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Read file content
    content = await file.read()
    
    # Check file size (20MB limit)
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size exceeds 20MB limit")
    
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
    """Stream chat responses using SSE."""
    
    # Validate thread_id is a valid UUID
    try:
        uuid.UUID(thread_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread_id format")
    
    async def event_generator():
        try:
            # Create config with thread_id
            config = {
                "configurable": {"thread_id": thread_id}
            }
            
            # Create input
            input_message = {"messages": [HumanMessage(content=query)]}
            
            # Stream events
            async for event in agent.astream_events(input_message, config, version="v1"):
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
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
