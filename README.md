# 🌊 Jal Sathi (जल साथी)
### Voice & WhatsApp-Enabled Groundwater Intelligence Assistant — Powered by Google Gemini + CGWB Data

<div align="center">

![Jal Sathi](https://img.shields.io/badge/Jal%20Sathi-%E0%A4%9C%E0%A4%B2%20%E0%A4%B8%E0%A4%BE%E0%A4%A5%E0%A5%80-0ea5e9?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Twilio](https://img.shields.io/badge/Twilio%20WhatsApp-Active-F22F46?style=for-the-badge&logo=twilio&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite%20CGWB-4000+%20Wells-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)

</div>

---

## 1. 🚨 Problem Statement

### India's Groundwater Crisis

India is experiencing one of the world's most severe groundwater crises. According to the Central Ground Water Board (CGWB), **more than 17% of India's assessment units are now classified as "Over-Exploited"**, meaning annual extraction exceeds the natural recharge rate. In states like Punjab, Haryana, and Rajasthan, water tables are falling at an alarming rate of **0.5–1.0 metre per year**.

| Indicator | Current Status |
|---|---|
| Over-Exploited Districts | 1,034+ (CGWB 2024 Report) |
| States with Critical Zones | Punjab, Haryana, Rajasthan, Tamil Nadu |
| Annual Groundwater Depletion | ~20 km³/year (among fastest globally) |
| Farmers Dependent on Groundwater | ~60% of irrigated agriculture |

### The Last-Mile Access Problem

Despite CGWB publishing comprehensive annual groundwater assessment data, this critical information is effectively **inaccessible to the 600 million rural citizens who need it most**:

- 📄 **Data Locked in PDFs**: Official CGWB reports are 400–600 page technical PDFs with dense tabular data, incomprehensible to non-specialists.
- 🖥️ **Complex Portals**: Official portals like cgwaonline.gov.in require technical knowledge and stable broadband internet.
- 🌐 **Language Barrier**: All official sources are in English, alienating the largely Hindi/regional-language speaking farming community.
- ⛏️ **Illegal Borewell Epidemic**: Without accessible data on groundwater depth or zone status, farmers drill borewells blindly — often in critically over-exploited zones — facing CGWA penalties up to ₹5 lakh.
- 🌾 **Crop Failure**: Wrong crop choices in water-scarce zones lead to massive losses. Farmers planting paddy in Over-Exploited zones face near-certain irrigation failure.

---

## 2. ✅ Solution Overview & Core Features

**Jal Sathi (जल साथी — "Water Companion")** is a production-grade, AI-powered groundwater intelligence assistant that makes CGWB data actionable and conversational. It is built on a 3-tier hierarchical search architecture backed by real CGWB monitoring station data.

### Core Features

#### 🎯 Real-Time Ground Data — Village to District Level
- Data sourced from official CGWB January 2026 Groundwater Level monitoring across **4,000+ observation wells** across India.
- Sub-millisecond SQLite lookup with indexed queries on `district`, `block`, `village`, and `latitude/longitude`.
- Returns exact **Depth to Water Level (DTWL)** in both **metres below ground level (mbgl)** and **feet**.

#### 🧠 3-Tier Intelligent Query Routing

| Tier | When Used | Example Query | Data Source |
|---|---|---|---|
| **Tier 1 — Exact Station** | User mentions a specific village or block | "Mithapur mein pani kitna deep hai?" | `cgwb_water_levels` SQLite (exact record) |
| **Tier 2 — District Average** | User mentions only a district | "Patna mein borewell lagwa sakte hain?" | `cgwb_water_levels` aggregated AVG/MIN/MAX |
| **Tier 3 — Web Search Fallback** | Location not in CGWB dataset | "Noida Sector 62 borewell rules?" | Gemini Google Search Grounding (live web) |

#### 🚰 Borewell Feasibility Verdicts
- ✅ **Safe Zone** (< 70% extraction): "हाँ, Borewell लगवा सकते हैं।"
- ⚠️ **Semi-Critical / Critical** (70–100%): "सशर्त अनुमति, CGWA से NOC ज़रूरी।"
- ❌ **Over-Exploited** (> 100%): "नहीं, Over-Exploited Zone है। CGWA की अनुमति के बिना बोरवेल नहीं खोदें।"

#### 🌾 Contextual Crop Farming Guidance
Crop suggestions are **strictly gated** — they appear **only when explicitly asked**. The bot never pollutes water-level or borewell answers with unsolicited farming advice.

#### 📡 Live Soil Moisture & Rain Telemetry
- Integrates with **Open-Meteo Satellite API** for real-time soil volumetric moisture content and 48-hour rainfall forecasts.

#### 🎙️ Multichannel Access

| Channel | Technology | Description |
|---|---|---|
| **WhatsApp Text** | Twilio Messaging API | Send text queries, receive formatted replies |
| **WhatsApp Voice** | Twilio + Gemini Audio | Send voice notes, auto-transcribed and answered |
| **Web Voice Interface** | Web Speech API + 3D CSS Avatar | Interactive real-time voice bot on the web |
| **REST API** | FastAPI /api/chat | Programmatic JSON access for developers |

---

## 3. 📱 WhatsApp Integration Flow

### Step-by-Step Workflow

**Step 1 — Farmer sends a message**
The farmer sends a WhatsApp text or voice note to the Twilio number. Examples:
- Text: `"Patna mein pani kaise hai?"`
- Voice Note: Speaks into WhatsApp — automatically recorded as `.ogg`

**Step 2 — Twilio Webhook triggers FastAPI**
Twilio sends an HTTP `POST` to the webhook URL (`https://<tunnel>.loca.lt/whatsapp/webhook`) with form fields: `From`, `Body`, `MediaUrl0`, `MediaContentType0`.

**Step 3 — Audio Transcription (if voice)**
If `MediaContentType0` contains `audio/ogg`, the service:
1. Downloads the voice note from Twilio's media CDN using Basic Auth.
2. Passes the raw audio bytes to **Gemini Multimodal** for verbatim Hindi/English transcription.

**Step 4 — Entity Extraction & 3-Tier DB Lookup**
`indic_nlp.py` detects language, intent (WATER_LEVEL, BOREWELL, CROP, EXTRACTION_LEVEL), and location entities. The raw query is then resolved through the 3-tier SQLite engine in `db_service.py`.

**Step 5 — Response Generation**
`agent.py` formats the output strictly based on intent with proper headers, depth values, and live soil moisture alerts.

**Step 6 — WhatsApp Reply**
`whatsapp_service.py` converts Markdown to WhatsApp-compatible formatting and returns it via `TwiML MessagingResponse`.

### Live Query Examples

| User Message (WhatsApp) | Tier | Sample Response |
|---|---|---|
| "Mithapur mein pani kitna deep hai?" | Tier 1 | 📍 Mithapur (Sadar), Patna: • 💧 भूजल स्तर: 0.2 m (0.66 ft) |
| "Kya Patna mein borewell lag sakta hai?" | Tier 2 | 📍 Patna जिला (औसत), Bihar: • ✅ हाँ, बोरवेल लगवा सकते हैं |
| "Jaipur mein paani kitna neeche hai?" | Tier 2 | 📍 Jaipur जिला (औसत), Rajasthan: • 💧 औसत भूजल स्तर: 18.3 m |
| "Borewell rules Noida Sector 62 mein?" | Tier 3 | 📍 Noida Sector 62: ... 🔗 स्रोत: cgwb.gov.in/... |

---

## 4. 🛠️ Tech Stack & Why It Was Chosen

### Backend

| Technology | Version | Role | Why Chosen |
|---|---|---|---|
| **FastAPI** | ≥ 0.110 | REST API & Webhook Gateway | Async-first, 3× faster than Flask, native OpenAPI docs |
| **Uvicorn** | Standard | ASGI server | Sub-millisecond event loop for concurrent requests |
| **Google Gemini Flash** | 2.5 Flash | LLM inference, response generation | 1–2s response times, native Hindi/English, Google Search Grounding |
| **google-genai SDK** | Latest | Gemini API client, audio transcription | First-party SDK with multimodal audio handling |
| **SQLite** | 3.x | Local groundwater database | Zero-dependency, sub-ms lookups, runs entirely offline |
| **SQLAlchemy** | ≥ 2.0 | ORM for assessments cache table | Type-safe queries, connection pooling |
| **Edge-TTS** | ≥ 7.0 | Neural Text-to-Speech | Zero-cost, Microsoft HD neural voices (hi-IN-MadhurNeural) |

### AI & NLP

| Component | Technology | Purpose |
|---|---|---|
| **Intent Classification** | Custom regex + TRANSLITERATION_MAP | Classify WATER_LEVEL / BOREWELL / CROP intent in O(1) |
| **Entity Extraction** | Hugging Face Inference API (BART/mDeBERTa) | Fallback multilingual NER for edge-case queries |
| **Audio Transcription** | Gemini 2.5 Flash Multimodal | Convert WhatsApp OGG voice notes to text |
| **Web Search Grounding** | Gemini google_search tool | Real-time web data for Tier 3 unknown locations |

### Frontend

| Technology | Role |
|---|---|
| **Web Speech API** | Browser STT/TTS, no SDK needed |
| **CSS 3D Animations** | Animated avatar orb with perspective transforms |
| **Vanilla JS + Fetch API** | UI logic, < 100ms page load |
| **Edge-TTS Base64** | Instant neural audio reply |

---

## 5. 🏗️ Project Architecture & Directory Structure

```
bot/
│
├── 📄 main.py                    # Entry point — starts uvicorn server
├── 📄 config.py                  # Environment config loader
├── 📄 requirements.txt           # Python dependencies
├── 📄 .env                       # Secret environment variables (NOT committed)
├── 📄 .env.example               # Template for .env setup
├── 📄 seed_ingres.py             # One-time DB seeder for district-level assessments
├── 📄 waterlevel.pdf             # Source: CGWB January 2026 Well Level Data (raw)
│
├── 📁 app/                       # Core application package
│   ├── 📄 main.py                # FastAPI app factory — routes, CORS, static files
│   ├── 📄 agent.py               # Core AI Agent — orchestrates Tier 1/2/3 routing
│   │                             #   • process_query() — main async pipeline
│   │                             #   • generate_tailored_response() — strict intent formatting
│   │                             #   • fetch_dynamic_grounded_advisory() — Gemini web search
│   ├── 📄 db_service.py          # Database Layer — all SQLite queries
│   │                             #   • get_cgwb_water_level(user_query) — Tier 1 + Tier 2
│   │                             #   • get_location_full_assessment() — unified resolver
│   │                             #   • save_district_assessment() — auto-caching new results
│   ├── 📄 indic_nlp.py           # NLP & Entity Extraction
│   │                             #   • parse_indic_intent_and_entities() — intent routing
│   │                             #   • TRANSLITERATION_MAP — 200+ Hindi→English districts
│   ├── 📄 whatsapp_service.py    # Twilio WhatsApp Webhook Handler
│   │                             #   • POST /whatsapp/webhook — main Twilio endpoint
│   │                             #   • _transcribe_whatsapp_audio() — Gemini multimodal STT
│   ├── 📄 soil_service.py        # Open-Meteo API Integration
│   │                             #   • get_live_soil_moisture(lat, lon) — satellite telemetry
│   ├── 📄 tts_service.py         # Neural Text-to-Speech (Edge-TTS)
│   │                             #   • Hindi: hi-IN-MadhurNeural
│   │                             #   • English: en-IN-PrabhatNeural
│   ├── 📄 database.py            # SQLAlchemy ORM models & engine setup
│   └── 📄 card_generator.py      # Visual info-card PDF generator
│
├── 📁 db/                        # SQLite databases
│   ├── 📄 cgwb_data.db           # Primary: CGWB monitoring wells (4,000+ stations)
│   │                             #   Table: cgwb_water_levels
│   │                             #   Columns: state_ut, district, block, village,
│   │                             #            latitude, longitude, record_date, dtwl_mbgl, dtwl_ft
│   │                             #   Indexes: district, block, village
│   └── 📄 ingres_groundwater.db  # Secondary: district-level assessments & AI response cache
│                                 #   Table: groundwater_assessments
│
├── 📁 scripts/                   # Data engineering scripts
│   ├── 📄 ingest_cgwb_pdf.py     # PDF → SQLite ETL pipeline (pdfplumber)
│   └── 📄 generate_sample_cgwb_pdf.py  # Test PDF generator for local development
│
└── 📁 static/                    # Frontend web application (served at /)
    ├── 📄 index.html             # Single-page Voice Interface with 3D animated avatar
    ├── 📄 style.css              # CSS 3D orb animations, glassmorphism UI, dark theme
    └── 📄 app.js                 # Web Speech API, Fetch API chat, audio playback
```

---

## 6. 🔑 API Keys & Environment Configuration

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

### Environment Variables Reference

| Variable | Required | Description | Where to Get |
|---|---|---|---|
| `GEMINI_API_KEY` | ✅ Required | Google Gemini API key for all LLM inference, intent detection, audio transcription, and Tier 3 Google Search Grounding | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `GEMINI_MODEL` | Optional | Model to use. Defaults to `gemini-2.5-flash` | — |
| `TWILIO_ACCOUNT_SID` | WhatsApp only | Your Twilio Account SID — authenticates all Twilio API calls | [Twilio Console](https://console.twilio.com) → Account Info |
| `TWILIO_AUTH_TOKEN` | WhatsApp only | Twilio Auth Token — used for webhook verification and media download auth | Twilio Console → Account Info |
| `TWILIO_API_KEY` | WhatsApp only | Twilio API Key SID (starts with `SK...`) — Basic Auth username for media downloads | Twilio Console → API Keys |
| `TWILIO_WHATSAPP_NUMBER` | WhatsApp only | WhatsApp-enabled number in `whatsapp:+1XXXXXXXXXX` format | Twilio Console → WhatsApp → Senders |
| `HUGGINGFACE_API_KEY` | Optional | API key for HuggingFace Inference API (mDeBERTa/BART for advanced NER). Falls back to regex NLP if not set | [Hugging Face Settings](https://huggingface.co/settings/tokens) |
| `HOST` | Optional | Server bind host. Default: `0.0.0.0` | — |
| `PORT` | Optional | Server bind port. Default: `8000` | — |
| `DEBUG` | Optional | Enable FastAPI hot-reload. Default: `True`. Set `False` in production | — |

### Example `.env` File

```env
# Google Gemini — Required for all AI features
GEMINI_API_KEY=AIzaSy...your_key_here
GEMINI_MODEL=gemini-2.5-flash

# Twilio WhatsApp — Required for WhatsApp channel
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_API_KEY=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Hugging Face — Optional (enhances NER for complex queries)
HUGGINGFACE_API_KEY=hf_...your_key_here

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

---

## 7. 🚀 Setup & Installation Guide

### Prerequisites

- Python **3.11+**
- pip / virtualenv
- A Google Gemini API Key (free tier sufficient for development)
- Twilio Account (for WhatsApp — free sandbox available)

### Step 1 — Clone & Create Virtual Environment

```bash
git clone https://github.com/your-repo/jal-sathi.git
cd jal-sathi

python3 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows PowerShell
```

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Configure Environment

```bash
cp .env.example .env
nano .env   # Fill in your API keys
```

### Step 4 — Ingest CGWB PDF Data

Ensure `waterlevel.pdf` (CGWB January 2026 monitoring data) is in the project root, then run:

```bash
python scripts/ingest_cgwb_pdf.py
```

This script will:
1. Parse all tabular data from `waterlevel.pdf` using `pdfplumber`.
2. Extract columns: `STATE_UT`, `DISTRICT`, `BLOCK`, `VILLAGE`, `LATITUDE`, `LONGITUDE`, `DATE`, `DTWL (mbgl)`.
3. Insert records into `db/cgwb_data.db` → table `cgwb_water_levels`.
4. Create indexes on `district`, `block`, and `village` for sub-millisecond lookups.
5. Print total row count on completion.

**Expected output:**
```
✅ Created table cgwb_water_levels
📄 Processing PDF page 1/47...
✅ Ingestion complete. Total rows inserted: 4,237
```

### Step 5 — Seed District Assessments (Optional)

```bash
python seed_ingres.py
```

### Step 6 — Start the Server

```bash
python main.py
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open **http://localhost:8000** to access the 3D Voice Interface.

**Health check:**
```bash
curl http://localhost:8000/api/health
```

### Step 7 — Expose for Twilio Webhook (WhatsApp Testing)

**Option A — Localtunnel (free, no account needed):**
```bash
npx -y localtunnel --port 8000
# Copy the URL, e.g.: https://huge-zebras-hear.loca.lt
```

**Option B — ngrok:**
```bash
ngrok http 8000
```

### Step 8 — Configure Twilio Webhook

1. Go to [Twilio Console](https://console.twilio.com) → **Messaging → WhatsApp Sandbox**.
2. Set **"When a message comes in"** to: `https://your-tunnel-url.loca.lt/whatsapp/webhook` (method: `HTTP POST`).
3. Send `join <sandbox-keyword>` from WhatsApp to the Twilio number to connect.
4. Start sending queries!

---

## 8. 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the 3D Voice Web Interface |
| `GET` | `/api/health` | System health and database stats |
| `GET` | `/api/stats` | Detailed database coverage statistics |
| `POST` | `/api/chat` | Main query endpoint (JSON) |
| `POST` | `/api/tts` | Text-to-Speech synthesis (streams MP3) |
| `POST` | `/whatsapp/webhook` | Twilio WhatsApp webhook receiver |
| `GET` | `/whatsapp/status` | WhatsApp gateway health check |

### POST /api/chat

**Request:**
```json
{
  "query": "Patna mein borewell lagwa sakte hain?",
  "language": "auto"
}
```

**Response:**
```json
{
  "query": "Patna mein borewell lagwa sakte hain?",
  "response": "📍 **Patna जिला (औसत), Bihar:**\n• ✅ **बोरवेल अनुमति:** हाँ...",
  "spoken_text": "पटना जिला में बोरवेल लगवाया जा सकता है...",
  "audio_base64": "//NkxAA...<base64 MP3>",
  "sql_query_used": "SELECT district, AVG(dtwl_mbgl)... WHERE LOWER(district) = 'patna'",
  "district": "Patna",
  "category_status": "Safe",
  "extraction_percentage": 64.2,
  "depth_mbgl": 4.017,
  "depth_feet": 13.18,
  "cached_from_db": true,
  "language": "hi",
  "status": "success"
}
```

---

## 9. 📊 Database Schema

### `cgwb_water_levels` (in `db/cgwb_data.db`)

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment row ID |
| `state_ut` | TEXT | State / Union Territory name |
| `district` | TEXT (indexed) | District name |
| `block` | TEXT (indexed) | Block/Tehsil name |
| `village` | TEXT (indexed) | Village name |
| `latitude` | REAL | GPS latitude of the monitoring well |
| `longitude` | REAL | GPS longitude of the monitoring well |
| `record_date` | TEXT | Date of measurement (e.g. `10-01-2026`) |
| `dtwl_mbgl` | REAL | Depth to Water Level in metres below ground level |
| `dtwl_ft` | REAL | Depth to Water Level in feet |

### `groundwater_assessments` (in `ingres_groundwater.db`)

| Column | Type | Description |
|---|---|---|
| `district` | TEXT UNIQUE | District name |
| `extraction_percentage` | REAL | % of annual extractable groundwater used |
| `category_status` | TEXT | Safe / Semi-Critical / Critical / Over-Exploited |
| `annual_extractable_ham` | REAL | Annual extractable groundwater in hectare-metres |
| `depth_mbgl` | REAL | Representative depth in metres |
| `updated_at` | TIMESTAMP | Last updated (for cache freshness) |

---

## 10. 🐛 Troubleshooting

**`ModuleNotFoundError: No module named 'pdfplumber'`**
```bash
pip install pdfplumber pypdf
```

**`GEMINI_API_KEY not set` on startup**
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GEMINI_API_KEY'))"
```

**Twilio Webhook returning 403**
Ensure your tunnel URL is fresh and matches exactly what's configured in the Twilio Console.

**`db/cgwb_data.db` is empty after ingestion**
Ensure `waterlevel.pdf` is in the **project root** (not inside `scripts/`). Run the script from the project root.

**Audio not playing in browser**
Requires Chrome 90+, Edge 90+, or Safari 15+. Ensure Microphone permission is granted.

---

## 11. 📜 License & Data Attribution

- **Code**: MIT License
- **Groundwater Data**: Central Ground Water Board (CGWB), Ministry of Jal Shakti, Government of India — January 2026 Groundwater Level Monitoring Data — [cgwb.gov.in](https://cgwb.gov.in)
- **Weather Data**: [Open-Meteo](https://open-meteo.com) — CC BY 4.0

---

<div align="center">

**Built with ❤️ for India's 600 million rural citizens**

*"जल है तो कल है" — If there is water, there is tomorrow.*

</div>
