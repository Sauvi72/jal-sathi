#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_project_pdf.py
Generates: Jal Sathi – Technical Architecture & Ecosystem Overview
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import os

NAVY       = HexColor("#1E293B")
CYAN       = HexColor("#0EA5E9")
CYAN_LIGHT = HexColor("#E0F2FE")
DARK_GRAY  = HexColor("#334155")
MID_GRAY   = HexColor("#64748B")
LIGHT_GRAY = HexColor("#F1F5F9")
WHITE      = HexColor("#FFFFFF")
GREEN      = HexColor("#059669")
AMBER      = HexColor("#D97706")
PURPLE     = HexColor("#7C3AED")
TABLE_HDR  = HexColor("#0F172A")
OUTPUT_FILE = "Jal_Sathi_Project_Overview.pdf"

def S(name, **kw):
    return ParagraphStyle(name, **kw)

STYLES = {
    "cover_title": S("cover_title", fontName="Helvetica-Bold", fontSize=28, textColor=WHITE, alignment=TA_CENTER, leading=34),
    "cover_sub":   S("cover_sub",   fontName="Helvetica",      fontSize=13, textColor=CYAN_LIGHT, alignment=TA_CENTER, leading=18),
    "tagline":     S("tagline",     fontName="Helvetica-BoldOblique", fontSize=10, textColor=NAVY, alignment=TA_CENTER, leading=16),
    "sec_hdr":     S("sec_hdr",     fontName="Helvetica-Bold", fontSize=14, textColor=WHITE, alignment=TA_LEFT, leading=18),
    "body":        S("body",        fontName="Helvetica",      fontSize=9.5, textColor=DARK_GRAY, alignment=TA_LEFT, leading=15, spaceAfter=4),
    "bullet":      S("bullet",      fontName="Helvetica",      fontSize=9.5, textColor=DARK_GRAY, alignment=TA_LEFT, leading=15, leftIndent=14, bulletIndent=4, spaceAfter=2, bulletText="*"),
    "tbl_hdr":     S("tbl_hdr",     fontName="Helvetica-Bold", fontSize=9,   textColor=WHITE, alignment=TA_CENTER),
    "tbl_bold":    S("tbl_bold",    fontName="Helvetica-Bold", fontSize=8.5, textColor=NAVY,  alignment=TA_LEFT),
    "tbl_cell":    S("tbl_cell",    fontName="Helvetica",      fontSize=8.5, textColor=DARK_GRAY, alignment=TA_LEFT, leading=13),
    "footer":      S("footer",      fontName="Helvetica",      fontSize=8,   textColor=MID_GRAY, alignment=TA_CENTER),
    "meta":        S("meta",        fontName="Helvetica",      fontSize=9,   textColor=MID_GRAY, alignment=TA_CENTER),
    "num":         S("num",         fontName="Helvetica-Bold", fontSize=16,  textColor=CYAN, leading=22),
    "arch_title":  S("arch_title",  fontName="Helvetica-Bold", fontSize=10.5, textColor=WHITE, leading=16, leftIndent=6),
    "arch_body":   S("arch_body",   fontName="Helvetica",      fontSize=9.5, textColor=DARK_GRAY, leading=15, leftIndent=4, rightIndent=4),
    "api_name":    S("api_name",    fontName="Helvetica-Bold", fontSize=10.5, textColor=WHITE, leading=16, leftIndent=4),
    "api_tier":    S("api_tier",    fontName="Helvetica-Bold", fontSize=8,   textColor=WHITE, alignment=TA_RIGHT, leading=16),
    "api_model":   S("api_model",   fontName="Helvetica-Oblique", fontSize=8.5, textColor=NAVY, leading=14, leftIndent=4),
    "api_bullet":  S("api_bullet",  fontName="Helvetica",      fontSize=9,   textColor=DARK_GRAY, leading=14, leftIndent=20, bulletIndent=10, spaceAfter=1, bulletText=">"),
}

def box(data, cols, bg, tp=7, bp=7, lp=10):
    t = Table(data, colWidths=cols)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("TOPPADDING",    (0,0), (-1,-1), tp),
        ("BOTTOMPADDING", (0,0), (-1,-1), bp),
        ("LEFTPADDING",   (0,0), (-1,-1), lp),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t

def sec(title):
    t = Table([[Paragraph("  " + title, STYLES["sec_hdr"])]], colWidths=[17*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), NAVY),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
    ]))
    return t

def cover():
    e = []
    e.append(Spacer(1, 1.5*cm))
    e.append(box([[Paragraph("Jal Sathi", STYLES["cover_title"])]], [17*cm], NAVY, 32, 10, 0))
    e.append(HRFlowable(width="100%", thickness=5, color=CYAN, spaceAfter=0, spaceBefore=0))
    e.append(box([[Paragraph("Technical Architecture &amp; Ecosystem Overview", STYLES["cover_sub"])]], [17*cm], NAVY, 10, 32, 0))
    e.append(Spacer(1, 0.6*cm))
    tag = Table([[Paragraph("India's AI-Powered Groundwater &amp; Agro-Intelligence Platform for Farmers", STYLES["tagline"])]], colWidths=[17*cm])
    tag.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), CYAN_LIGHT),
        ("TOPPADDING",    (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("LEFTPADDING",   (0,0), (-1,-1), 16),
        ("RIGHTPADDING",  (0,0), (-1,-1), 16),
        ("BOX", (0,0), (-1,-1), 1.5, CYAN),
    ]))
    e.append(tag)
    e.append(Spacer(1, 0.4*cm))
    meta = Table([[Paragraph("Version 2.0", STYLES["meta"]),
                   Paragraph("August 2026", STYLES["meta"]),
                   Paragraph("Render Cloud · India", STYLES["meta"])]], colWidths=[5.66*cm]*3)
    meta.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_GRAY),
        ("ALIGN",   (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("BOX", (0,0), (-1,-1), 0.5, MID_GRAY),
    ]))
    e.append(meta)
    e.append(Spacer(1, 0.5*cm))
    e.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=12))
    return e

def section1():
    e = []
    e.append(sec("01  Project Summary &amp; Core Objective"))
    e.append(Spacer(1, 0.25*cm))
    e.append(Paragraph(
        "<b>Jal Sathi</b> (जल साथी — Water Companion) is India's first conversational AI platform "
        "delivering real-time groundwater intelligence, personalized crop advisory, and borewell "
        "regulatory guidance to farmers and local authorities — in their native language, instantly and at zero cost.",
        STYLES["body"]
    ))
    e.append(Spacer(1, 0.15*cm))
    bullets = [
        "<b>Multilingual Voice AI:</b> Accepts voice and text in Hindi, Hinglish, and English. "
        "Responds with Microsoft Azure Neural TTS (SwaraNeural / NeerjaNeural).",
        "<b>Groundwater Intelligence:</b> Queries 21,000+ entry CGWB January 2026 SQLite database "
        "for water table depth, extraction status (Safe / Semi-Critical / Critical / Over-Exploited).",
        "<b>ICAR Agro-Advisory Engine:</b> Season-specific crop recommendations (Kharif/Rabi/Zaid) "
        "for 700+ Indian districts with water-budget matching.",
        "<b>Borewell Regulation Compliance:</b> CGWA state-level NOC regulations, dark zone status, and portal links for all 29 states.",
        "<b>Twilio WhatsApp Bot:</b> Farmers query directly on WhatsApp — zero app installation, zero barrier.",
        "<b>Live Web App:</b> Hosted at jal-sathi.onrender.com with animated voice orb and SSE streaming chat.",
    ]
    for b in bullets:
        e.append(Paragraph(b, STYLES["bullet"]))
    e.append(Spacer(1, 0.2*cm))
    return e

def section2():
    e = []
    e.append(sec("02  Complete Tech Stack &amp; Runtime"))
    e.append(Spacer(1, 0.25*cm))
    hdr = [Paragraph("Layer / Module", STYLES["tbl_hdr"]),
           Paragraph("Technology", STYLES["tbl_hdr"]),
           Paragraph("Details", STYLES["tbl_hdr"])]
    rows = [
        ["Backend Framework",     "FastAPI (Python 3.11)",      "Async ASGI-native, high-concurrency, automatic OpenAPI docs."],
        ["ASGI Server",           "Gunicorn + Uvicorn Workers", "Production-grade process management with graceful hot-reload."],
        ["Database",              "SQLite + Custom Ingestion",  "21,048-entry CGWB dataset; phonetic fuzzy-search with Levenshtein distance."],
        ["NLP / Intent Router",   "Custom Indic NLP Pipeline",  "Regex-first, Devanagari normalization, HuggingFace zero-shot fallback."],
        ["LLM / AI Engine",       "Google Gemini API",          "Multi-tier cascade: gemini-2.5-flash > gemini-2.0-flash > gemini-3.5-flash-lite."],
        ["Voice / STT",           "Web Speech API (Browser)",   "Client-side native speech recognition — zero latency, no API cost."],
        ["Voice / TTS",           "edge-tts (Azure Neural)",    "Server-side Hindi (SwaraNeural) and English (NeerjaNeural) synthesis."],
        ["Frontend",              "Vanilla JS + CSS3",          "Animated robot orb, SSE streaming, AbortController for instant cancellation."],
        ["Weather Data",          "OpenWeatherMap + wttr.in",   "Real-time temperature, precipitation probability, 5-day agricultural forecast."],
        ["WhatsApp Integration",  "Twilio Programmable Msg",    "Webhook-based QA bot; access via standard WhatsApp without app downloads."],
        ["Deployment",            "Docker + Render.com",        "Containerized; auto-deploy on git push; free-tier SSL and custom domain."],
        ["Version Control / CI",  "Git + GitHub",               "Continuous deployment triggered on main branch push to Render build pipeline."],
    ]
    td = [hdr]
    for r in rows:
        td.append([Paragraph(r[0], STYLES["tbl_bold"]),
                   Paragraph(r[1], STYLES["tbl_cell"]),
                   Paragraph(r[2], STYLES["tbl_cell"])])
    t = Table(td, colWidths=[4.2*cm, 4.5*cm, 8.3*cm], repeatRows=1)
    style_cmds = [
        ("BACKGROUND",    (0,0), (-1,0),  TABLE_HDR),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("GRID",          (0,0), (-1,-1), 0.4, HexColor("#CBD5E1")),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]
    for i in range(1, len(td)):
        bg = LIGHT_GRAY if i % 2 == 1 else WHITE
        style_cmds.append(("BACKGROUND", (0,i), (-1,i), bg))
    t.setStyle(TableStyle(style_cmds))
    e.append(t)
    e.append(Spacer(1, 0.2*cm))
    return e

def section3():
    e = []
    e.append(sec("03  External APIs &amp; Cloud Services"))
    e.append(Spacer(1, 0.25*cm))
    apis = [
        {"name": "Google Gemini API (Multi-Tier Cascade)", "tier": "PRIMARY AI ENGINE", "color": GREEN,
         "models": "gemini-2.5-flash · gemini-2.0-flash · gemini-3.5-flash-lite · gemini-flash-latest",
         "why": [
             "Multilingual reasoning: Hindi, Hinglish, English, and regional transliterations.",
             "Zero-hallucination via Google Search Grounding — retrieves live government documents.",
             "Ultra-fast token throughput (~300 tokens in &lt;1.5s) using direct google-genai SDK.",
             "Automatic model cascade failover on 429 quota — guarantees zero downtime.",
         ]},
        {"name": "Google Search Grounding Tool", "tier": "LIVE KNOWLEDGE LAYER", "color": CYAN,
         "models": "Integrated with Google Gemini API",
         "why": [
             "Retrieves live borewell regulations, district dark-zone notifications, and CGWA orders.",
             "ICAR crop advisories for any Indian district on-demand — no stale static database.",
             "Government policy responses always current; verified URLs with every grounded response.",
             "Provides audit-traceable source citations for all advisory content.",
         ]},
        {"name": "OpenWeatherMap API", "tier": "WEATHER DATA LAYER", "color": AMBER,
         "models": "Current Weather API + 5-Day Forecast API",
         "why": [
             "Real-time temperature (C), humidity, wind speed, and precipitation probability.",
             "5-day forecast helps farmers plan sowing, irrigation, and harvest schedules.",
             "Localized city-level precision for any of India's 700+ districts.",
             "Critical for agro-climatic advisory — water requirement is weather-dependent.",
         ]},
        {"name": "Twilio Programmable WhatsApp Messaging", "tier": "ACCESSIBILITY LAYER", "color": PURPLE,
         "models": "Twilio Sandbox · Production WhatsApp API",
         "why": [
             "Farmers access Jal Sathi on WhatsApp — the most-used app in rural India.",
             "No app download, no account creation, no UI learning curve — pure accessibility.",
             "Real-time bidirectional conversation in farmer's native language via webhook.",
             "Supports voice note transcription and text query routing through the same pipeline.",
         ]},
    ]
    for api in apis:
        nt = Table([[Paragraph("  " + api["name"], STYLES["api_name"]),
                     Paragraph(api["tier"], STYLES["api_tier"])]],
                   colWidths=[12*cm, 5*cm])
        nt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), api["color"]),
            ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING", (0,0), (0,-1), 10), ("RIGHTPADDING", (-1,0), (-1,-1), 10),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        e.append(nt)
        mt = Table([[Paragraph("  Models / Endpoints: " + api["models"], STYLES["api_model"])]], colWidths=[17*cm])
        mt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), CYAN_LIGHT),
            ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
        ]))
        e.append(mt)
        for b in api["why"]:
            e.append(Paragraph(b, STYLES["api_bullet"]))
        e.append(Spacer(1, 0.3*cm))
    return e

def section4():
    e = []
    e.append(sec("04  Key Architectural Highlights"))
    e.append(Spacer(1, 0.25*cm))
    highlights = [
        ("Multi-Tier Dynamic Model Failover Cascade",
         "The AI engine never hits a dead-end. When gemini-2.5-flash returns 429 (Search Grounding quota "
         "exhaustion), the system instantly falls through to gemini-2.0-flash, then gemini-3.5-flash-lite "
         "for standard LLM generation — all within a single HTTP request lifecycle. This eliminates service "
         "disruption even under free-tier API rate limits."),
        ("Intent Classification & Typo-Tolerant Indic NLP Pipeline",
         "A multi-stage pipeline handles the full linguistic complexity of rural India: "
         "(1) Regex-first keyword detection for crop/water/weather terms. "
         "(2) Devanagari normalization (e.g. 'faslen' -> 'fasal', 'borwell' -> 'borewell'). "
         "(3) Phonetic Levenshtein fuzzy matching against 21,048 district/block names from CGWB corpus. "
         "(4) HuggingFace zero-shot classification as final fallback for ambiguous queries."),
        ("Real-Time SSE Streaming Chat with Instant Cancellation",
         "Responses stream word-by-word via Server-Sent Events (SSE), giving sub-200ms first-token latency. "
         "An AbortController instance allows cancellation of any ongoing generation (ChatGPT-style Stop). "
         "A 2-second hard timeout guard on TTS pre-computation ensures the frontend stream never hangs."),
        ("CGWB SQLite Database with 21,048-Entry Geospatial Corpus",
         "January 2026 CGWB telemetry is ingested, cleaned, and indexed into SQLite. Every district lookup "
         "resolves in under 5ms with zero network I/O. Phonetic fuzzy matching ensures voice-transcribed or "
         "misspelled location names ('Patana', 'Gorakhpuur') still match the correct district with high confidence."),
        ("Language-Matched Neural Speech Synthesis",
         "All responses include a spoken_text field stripped of markdown, emoji, and parenthetical English "
         "translations (e.g. 'dhan (Paddy)' becomes 'dhan' in TTS). Hindi queries receive "
         "hi-IN-SwaraNeural; English receives en-IN-NeerjaNeural. "
         "A 2-second async timeout guard prevents TTS latency from blocking the streaming HTTP response."),
    ]
    for i, (title, body) in enumerate(highlights):
        nt = Table([[Paragraph("  " + str(i+1).zfill(2), STYLES["num"]),
                     Paragraph(title, STYLES["arch_title"])]],
                   colWidths=[1.2*cm, 15.8*cm])
        nt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), NAVY),
            ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING", (0,0), (0,0), 8), ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        e.append(nt)
        bt = Table([[Paragraph(body, STYLES["arch_body"])]], colWidths=[17*cm])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), LIGHT_GRAY),
            ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("LEFTPADDING", (0,0), (-1,-1), 12), ("RIGHTPADDING", (0,0), (-1,-1), 12),
            ("BOX", (0,0), (-1,-1), 0.5, HexColor("#CBD5E1")),
        ]))
        e.append(bt)
        e.append(Spacer(1, 0.25*cm))
    return e

def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_FILE, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm,
        title="Jal Sathi Technical Architecture & Ecosystem Overview",
        author="Jal Sathi Engineering Team",
    )
    story = []
    story += cover()
    story += section1()
    story.append(Spacer(1, 0.3*cm))
    story += section2()
    story.append(Spacer(1, 0.3*cm))
    story += section3()
    story.append(Spacer(1, 0.3*cm))
    story += section4()
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=CYAN))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        "Jal Sathi  |  Ministry of Jal Shakti / CGWB Virtual Intelligence Platform  |  "
        "Live: jal-sathi.onrender.com  |  GitHub: github.com/Sauvi72/jal-sathi  |  (c) 2026",
        STYLES["footer"]
    ))
    doc.build(story)
    print(f"\n  PDF generated -> {os.path.abspath(OUTPUT_FILE)}")
    print(f"  Size: {os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB\n")

if __name__ == "__main__":
    build_pdf()
