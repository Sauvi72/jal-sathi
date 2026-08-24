"""
main.py
FastAPI Web Application for INGRES Dynamic Search & Auto-Caching Groundwater Assistant.
Powers chat endpoint with integrated Edge-TTS Neural Audio generation and single-page web UI.
"""

import io
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from config import HOST, PORT, DEBUG, BASE_DIR, is_gemini_configured, is_huggingface_configured
from app.agent import ingres_agent
from app.db_service import get_db_stats
from app.tts_service import generate_speech, generate_speech_base64
from app.whatsapp_service import router as whatsapp_router

app = FastAPI(
    title="INGRES Jal API",
    description="Voice AI Virtual Assistant for India Groundwater Resource Estimation System (Ministry of Jal Shakti / CGWB)",
    version="2.0.0"
)

# Mount WhatsApp Webhook & Media Gateway
app.include_router(whatsapp_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Request & Response Models
class ChatRequest(BaseModel):
    query: str = Field(..., description="User voice transcript or text query", min_length=1)
    language: Optional[str] = Field("auto", description="Preferred response language: 'auto', 'en', 'hi'")

class ChatResponse(BaseModel):
    query: str
    response: str
    spoken_text: Optional[str] = None
    audio_base64: Optional[str] = None
    sql_query_used: str
    district: Optional[str] = None
    category_status: Optional[str] = None
    extraction_percentage: Optional[float] = None
    depth_mbgl: Optional[float] = None
    depth_feet: Optional[float] = None
    soil_moisture: Optional[Dict[str, Any]] = None
    cached_from_db: bool = False
    auto_cached: bool = False
    language: str
    status: str

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "auto"
    voice: Optional[str] = None

# API Endpoints
@app.get("/api/health")
async def health_check():
    """Health check and system status."""
    stats = get_db_stats()
    return {
        "status": "healthy",
        "service": "INGRES Jal",
        "database": "connected",
        "cached_districts": stats.get("total_districts", 0),
        "states_covered": stats.get("states_count", 0),
        "gemini_active": is_gemini_configured(),
        "huggingface_active": is_huggingface_configured(),
        "tts_engine": "Microsoft Edge Neural HD (Zero-Cost)",
        "architecture": "Hugging Face Indic NLP + Gemini Text-to-SQL + SQLite"
    }

@app.get("/api/stats")
async def get_overview_stats():
    """Overview statistics for dashboard metrics."""
    try:
        return get_db_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Processes user query via local DB search or dynamic web search with auto-caching and neural audio."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        result = await ingres_agent.process_query(
            user_query=request.query.strip(),
            requested_language=None if request.language == "auto" else request.language
        )

        # Generate HD neural audio in-memory for instant playback
        text_to_speak: str = result.get("spoken_text") or result.get("response") or ""
        audio_b64 = await generate_speech_base64(
            text=text_to_speak,
            lang=result.get("language", "en")
        )
        result["audio_base64"] = audio_b64

        return ChatResponse(**result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "query": request.query,
                "response": f"An error occurred while retrieving groundwater assessment: {str(e)}",
                "spoken_text": "An error occurred while processing your request.",
                "audio_base64": None,
                "sql_query_used": "ERROR",
                "district": None,
                "category_status": None,
                "extraction_percentage": None,
                "cached_from_db": False,
                "auto_cached": False,
                "language": "en",
                "status": "error"
            }
        )

@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Server-Sent Events (SSE) streaming chat endpoint for sub-200ms token rendering."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    gen = ingres_agent.process_query_stream(
        user_query=request.query.strip(),
        requested_language=None if request.language == "auto" else request.language
    )
    return StreamingResponse(gen, media_type="text/event-stream")


@app.post("/api/tts")
async def text_to_speech_endpoint(request: TTSRequest):
    """Generates streaming ultra-realistic neural speech audio via edge-tts."""
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        audio_bytes = await generate_speech(
            text=request.text.strip(),
            lang=request.language or "en",
            voice=request.voice
        )
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

# Mount static folder
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def serve_index():
    """Serve single-page frontend application."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "INGRES AI Assistant API is running. Frontend index.html not found."}

@app.on_event("startup")

async def startup_banner():
    """Prints active webhook endpoint banner on server boot for Twilio configuration."""
    import os
    base_url = os.getenv("BASE_URL", "https://jalsathi-groundwater-ai.loca.lt").rstrip("/")
    webhook_url = f"{base_url}/whatsapp/webhook"
    print("\n" + "=" * 70)
    print("🚀 INGRES JAL SATHI AI ASSISTANT SERVER STARTED")
    print(f"📡 Web Interface:   http://{HOST}:{PORT}")
    print(f"📲 WhatsApp Webhook: {webhook_url}")
    print("💡 Copy the WhatsApp Webhook URL above to Twilio Console Sandbox Settings!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)

