"""
ingres_agent.py
Exposes the multi-tier Model Cascade Fallback pipeline with Google Search Grounding.
"""

from app.agent import (
    FALLBACK_MODELS,
    get_genai_client,
    generate_grounded_response,
    INGRESSQLAgent,
    ingres_agent
)

__all__ = [
    "FALLBACK_MODELS",
    "get_genai_client",
    "generate_grounded_response",
    "INGRESSQLAgent",
    "ingres_agent"
]
