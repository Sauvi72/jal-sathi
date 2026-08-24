"""
whatsapp_service.py
Twilio WhatsApp Webhook Gateway for Jal (Groundwater & Agricultural AI Assistant).
Handles incoming WhatsApp text and voice notes, queries the CGWB database and Open-Meteo satellite APIs,
and delivers instant, ultra-targeted direct text responses (< 1s).
"""

import os
import re
import logging
from typing import Optional, Any
import httpx
from fastapi import APIRouter, Form, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from google import genai
from google.genai import types

from app.agent import ingres_agent as groundwater_agent

logger = logging.getLogger("ingres_whatsapp")

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

def _markdown_to_whatsapp(text: str) -> str:
    """Converts standard Markdown formatting into clean WhatsApp chat styling."""
    if not text:
        return ""
    lines = []
    for line in text.splitlines():
        l = line.strip()
        if l.startswith("###"):
            title = l.lstrip("#").strip().replace("**", "")
            lines.append(f"*{title}*")
        elif l.startswith("- **") or l.startswith("* **"):
            lines.append(line.replace("**", "*"))
        else:
            lines.append(line.replace("**", "*"))
    
    cleaned = "\n".join(lines)
    cleaned = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'\1: \2', cleaned)
    return cleaned.strip()

async def _transcribe_whatsapp_audio(media_url: str, mime_type: str) -> str:
    """Downloads WhatsApp voice note via Twilio Basic Auth and transcribes via Gemini."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    api_key_id = os.getenv("TWILIO_API_KEY", "").strip()
    auth_secret = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not gemini_key:
        logger.error("Missing GEMINI_API_KEY for audio transcription.")
        return "कृषि जल सलाह"

    username = api_key_id if api_key_id.startswith("SK") else account_sid
    auth = httpx.BasicAuth(username, auth_secret) if username and auth_secret else None
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(media_url, auth=auth, follow_redirects=True)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch WhatsApp audio: HTTP {resp.status_code}")
                return "कृषि जल सलाह"
            audio_bytes = resp.content

        ai_client = genai.Client(api_key=gemini_key)
        prompt = (
            "You are a helpful rural Indian agricultural assistant. "
            "Listen carefully to this voice note from a farmer. "
            "Transcribe the query verbatim in Hindi or English. "
            "Return ONLY the plain transcription without any conversational commentary."
        )
        clean_mime = mime_type.split(";")[0].strip() if mime_type else "audio/ogg"
        if clean_mime in ["audio/ogg", "audio/opus"]:
            clean_mime = "audio/ogg"
            
        transcribe_resp = ai_client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=clean_mime),
                prompt
            ]
        )
        transcribed_text = transcribe_resp.text.strip() if transcribe_resp.text else ""
        logger.info(f"Transcribed WhatsApp audio: '{transcribed_text}'")
        return transcribed_text or "कृषि जल सलाह"
    except Exception as e:
        logger.error(f"Gemini voice note transcription error: {e}")
        return "कृषि जल सलाह"

# ============================================================================
# Core Webhook Endpoint
# ============================================================================
@router.post("/webhook")
@router.post("/webh")
@router.post("/v")
@router.post("")
@router.post("/")
async def handle_whatsapp(request: Request):
    """
    Twilio WhatsApp Webhook Endpoint.
    Receives incoming text and voice messages from WhatsApp users,
    processes queries through the Jal Sathi AI Agent, and returns clean TwiML XML.
    """
    try:
        form_data = await request.form()
        incoming_msg = form_data.get("Body", "").strip()
        sender = form_data.get("From", "")
        media_url = form_data.get("MediaUrl0", "")
        media_type = form_data.get("MediaContentType0", "")

        logging.info(f"📩 [Twilio Incoming] From: {sender} | Msg: {incoming_msg}")

        if not incoming_msg and not media_url:
            return Response(content="<Response/>", media_type="application/xml")

        # Handle voice note if audio media is attached
        if media_url and media_type and "audio" in media_type.lower():
            logging.info(f"Processing incoming WhatsApp voice note from {sender}")
            user_query = await _transcribe_whatsapp_audio(media_url, media_type)
        else:
            user_query = incoming_msg

        # Generate Jal Sathi response
        agent_result = await groundwater_agent.process_query(user_query, requested_language=None)
        response_md = agent_result.get("response", "")
        reply_text = _markdown_to_whatsapp(response_md) or "भूजल स्तर और मौसम की जानकारी प्राप्त हो गई है।"

        logging.info(f"📤 [Twilio Replying]: {reply_text[:60]}")

        # Build clean TwiML XML response
        twiml_resp = MessagingResponse()
        twiml_resp.message(reply_text)
        return Response(content=str(twiml_resp), media_type="application/xml")

    except Exception as e:
        logging.error(f"❌ [WhatsApp Error]: {e}", exc_info=True)
        fallback_resp = MessagingResponse()
        fallback_resp.message("📍 **Jal Sathi:** सूचना प्राप्त करने में समस्या आई। कृपया पुनः प्रयास करें।")
        return Response(content=str(fallback_resp), media_type="application/xml")



@router.get("/status")
async def get_whatsapp_status():
    """Returns WhatsApp gateway operational health and configuration."""
    return {
        "status": "online",
        "service": "Jal WhatsApp AI Gateway",
        "mode": "Ultra-Fast Direct Text",
        "twilio_configured": bool(os.getenv("TWILIO_ACCOUNT_SID")),
        "whatsapp_number": os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
    }
