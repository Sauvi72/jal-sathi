import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file (with override=True)
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

def get_api_key() -> str:
    """Retrieve Gemini or Google API key from environment."""
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    return key.strip()

# Gemini API Configuration
GEMINI_API_KEY = get_api_key()

# Propagate to standard Google SDK environment variables if present
if GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# LLM Model Configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

# Database Configuration
DATABASE_PATH = BASE_DIR / "ingres_groundwater.db"
DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
CGWB_DB_PATH = BASE_DIR / "db" / "cgwb_data.db"
CGWB_DATABASE_URI = f"sqlite:///{CGWB_DB_PATH}"

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
try:
    PORT = int(os.getenv("PORT", "8000"))
except ValueError:
    PORT = 8000
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

def is_gemini_configured() -> bool:
    """Check if a valid Gemini/Google API key is configured."""
    key = get_api_key()
    if not key:
        return False
    # Reject common placeholder templates
    placeholders = ["your_gemini_api_key_here", "your_api_key", "<your-key>", "placeholder"]
    return not any(p in key.lower() for p in placeholders)

# Hugging Face API Configuration
def get_huggingface_api_key() -> str:
    """Retrieve Hugging Face API key from environment."""
    key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN") or ""
    return key.strip()

HUGGINGFACE_API_KEY = get_huggingface_api_key()
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "facebook/bart-large-mnli")

def is_huggingface_configured() -> bool:
    """Check if a valid Hugging Face API key is configured."""
    key = get_huggingface_api_key()
    if not key:
        return False
    placeholders = ["your_hf_token_here", "your_huggingface_api_key_here", "placeholder", "<your-token>"]
    return not any(p in key.lower() for p in placeholders)

# OpenWeatherMap API Configuration
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()

def is_openweather_configured() -> bool:
    """Check if OpenWeatherMap API key is configured."""
    key = OPENWEATHER_API_KEY
    if not key:
        return False
    placeholders = ["your_openweather_api_key_here", "placeholder", "<your-key>"]
    return not any(p in key.lower() for p in placeholders)


