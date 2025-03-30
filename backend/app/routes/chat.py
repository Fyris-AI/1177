from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import json
from typing import Dict, List, Any

from app.services.ai import ai_service

router = APIRouter()

@router.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        messages = data.get("messages", [])
        
        async def stream_response():
            try:
                async for chunk in ai_service.generate_response(messages):
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
            except Exception as e:
                error_message = f"data: {json.dumps({'error': str(e)})}\n\n"
                yield error_message
            finally:
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
