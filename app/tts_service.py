"""
tts_service.py
High-Definition Neural Text-to-Speech Service using edge-tts.
Provides zero-cost, hyper-realistic human voice generation across 22 Indian regional languages and dialects.
Includes decimal-safe multi-stage text sanitization, unit expansions, and script mapping to eliminate stutters and lag.
Tuned for warm, calm, non-rushed natural human cadence (rate='-4%').
"""

import io
import re
import base64
import logging
from typing import Optional, Dict
import edge_tts

logger = logging.getLogger("ingres_tts")

# ============================================================================
# Comprehensive 22 Indian Regional Neural Voice Registry
# ============================================================================
NEURAL_VOICES: Dict[str, str] = {
    # 1. Hindi (हिंदी) - Central & North India
    "hi": "hi-IN-SwaraNeural",
    "hi-in": "hi-IN-SwaraNeural",
    "hi-female": "hi-IN-SwaraNeural",
    "hi-male": "hi-IN-MadhurNeural",
    "hindi": "hi-IN-SwaraNeural",
    "hindustani": "hi-IN-SwaraNeural",
    "dehati": "hi-IN-SwaraNeural",

    # 2. English (India) - National
    "en": "en-IN-NeerjaNeural",
    "en-in": "en-IN-NeerjaNeural",
    "en-female": "en-IN-NeerjaNeural",
    "en-male": "en-IN-PrabhatNeural",
    "english": "en-IN-NeerjaNeural",
    "hinglish": "hi-IN-SwaraNeural",

    # 3. Punjabi (ਪੰਜਾਬੀ) - Punjab & North
    "pa": "hi-IN-MadhurNeural",
    "pa-in": "hi-IN-MadhurNeural",
    "pa-female": "hi-IN-SwaraNeural",
    "pa-male": "hi-IN-MadhurNeural",
    "punjabi": "hi-IN-MadhurNeural",

    # 4. Bengali (বাংলা) - West Bengal & East
    "bn": "bn-IN-TanishaaNeural",
    "bn-in": "bn-IN-TanishaaNeural",
    "bn-female": "bn-IN-TanishaaNeural",
    "bn-male": "bn-IN-BashkarNeural",
    "bengali": "bn-IN-TanishaaNeural",
    "bangla": "bn-IN-TanishaaNeural",

    # 5. Marathi (मराठी) - Maharashtra
    "mr": "mr-IN-AarohiNeural",
    "mr-in": "mr-IN-AarohiNeural",
    "mr-female": "mr-IN-AarohiNeural",
    "mr-male": "mr-IN-ManoharNeural",
    "marathi": "mr-IN-AarohiNeural",

    # 6. Gujarati (ગુજરાતી) - Gujarat
    "gu": "gu-IN-DhwaniNeural",
    "gu-in": "gu-IN-DhwaniNeural",
    "gu-female": "gu-IN-DhwaniNeural",
    "gu-male": "gu-IN-NiranjanNeural",
    "gujarati": "gu-IN-DhwaniNeural",

    # 7. Tamil (தமிழ்) - Tamil Nadu & South
    "ta": "ta-IN-PallaviNeural",
    "ta-in": "ta-IN-PallaviNeural",
    "ta-female": "ta-IN-PallaviNeural",
    "ta-male": "ta-IN-ValluvarNeural",
    "tamil": "ta-IN-PallaviNeural",

    # 8. Telugu (తెలుగు) - Andhra Pradesh & Telangana
    "te": "te-IN-ShrutiNeural",
    "te-in": "te-IN-ShrutiNeural",
    "te-female": "te-IN-ShrutiNeural",
    "te-male": "te-IN-MohanNeural",
    "telugu": "te-IN-ShrutiNeural",

    # 9. Kannada (ಕನ್ನಡ) - Karnataka
    "kn": "kn-IN-SapnaNeural",
    "kn-in": "kn-IN-SapnaNeural",
    "kn-female": "kn-IN-SapnaNeural",
    "kn-male": "kn-IN-GaganNeural",
    "kannada": "kn-IN-SapnaNeural",

    # 10. Malayalam (മലയാളം) - Kerala
    "ml": "ml-IN-SobhanaNeural",
    "ml-in": "ml-IN-SobhanaNeural",
    "ml-female": "ml-IN-SobhanaNeural",
    "ml-male": "ml-IN-MidhunNeural",
    "malayalam": "ml-IN-SobhanaNeural",

    # 11. Odia (ଓଡ଼ିଆ) - Odisha
    "or": "hi-IN-SwaraNeural",
    "or-in": "hi-IN-SwaraNeural",
    "od": "hi-IN-SwaraNeural",
    "odia": "hi-IN-SwaraNeural",
    "oriya": "hi-IN-SwaraNeural",

    # 12. Assamese (অসমীয়া) - Assam & Northeast
    "as": "bn-IN-TanishaaNeural",
    "as-in": "bn-IN-TanishaaNeural",
    "assamese": "bn-IN-TanishaaNeural",
    "asomiya": "bn-IN-TanishaaNeural",

    # 13. Urdu (اردو) - Pan-India
    "ur": "ur-IN-GulNeural",
    "ur-in": "ur-IN-GulNeural",
    "ur-female": "ur-IN-GulNeural",
    "ur-male": "ur-IN-SalmanNeural",
    "urdu": "ur-IN-GulNeural",

    # 14. Bhojpuri (भोजपुरी) - Bihar & Eastern UP
    "bho": "hi-IN-MadhurNeural",
    "bhojpuri": "hi-IN-MadhurNeural",

    # 15. Maithili (मैथिली) - Bihar & Jharkhand
    "mai": "hi-IN-MadhurNeural",
    "maithili": "hi-IN-MadhurNeural",

    # 16. Sanskrit (संस्कृतम्)
    "sa": "hi-IN-SwaraNeural",
    "sa-in": "hi-IN-SwaraNeural",
    "sanskrit": "hi-IN-SwaraNeural",

    # 17. Sindhi (सिन्धी / سنڌي)
    "sd": "ur-IN-GulNeural",
    "sd-in": "ur-IN-GulNeural",
    "sindhi": "ur-IN-GulNeural",

    # 18. Konkani (कोंकणी) - Goa & Coastal Maharashtra/Karnataka
    "kok": "mr-IN-AarohiNeural",
    "kok-in": "mr-IN-AarohiNeural",
    "konkani": "mr-IN-AarohiNeural",

    # 19. Dogri (डोगरी) - Jammu & Himachal
    "doi": "hi-IN-MadhurNeural",
    "doi-in": "hi-IN-MadhurNeural",
    "dogri": "hi-IN-MadhurNeural",

    # 20. Kashmiri (कश्मीरी / کٲشُر) - Kashmir
    "ks": "ur-IN-GulNeural",
    "ks-in": "ur-IN-GulNeural",
    "kashmiri": "ur-IN-GulNeural",

    # 21. Nepali (नेपाली) - Sikkim & Northern Hills
    "ne": "ne-NP-HemkalaNeural",
    "ne-in": "ne-NP-HemkalaNeural",
    "ne-np": "ne-NP-HemkalaNeural",
    "nepali": "ne-NP-HemkalaNeural",

    # 22. Santhali & Bodo (संथाली / बड़ो)
    "sat": "hi-IN-MadhurNeural",
    "santhali": "hi-IN-MadhurNeural",
    "brx": "hi-IN-SwaraNeural",
    "bodo": "hi-IN-SwaraNeural",

    # Major Agricultural Dialects
    "bgc": "hi-IN-MadhurNeural",
    "haryanvi": "hi-IN-MadhurNeural",
    "raj": "hi-IN-MadhurNeural",
    "rajasthani": "hi-IN-MadhurNeural",
    "marwari": "hi-IN-MadhurNeural",
    "chhattisgarhi": "hi-IN-MadhurNeural"
}

# ============================================================================
# Non-Native Script to Phonetic Devanagari Mapping for Edge-TTS Compatibility
# ============================================================================
GURMUKHI_TO_DEVANAGARI = {
    "\u0a05": "अ", "\u0a06": "आ", "\u0a07": "इ", "\u0a08": "ई", "\u0a09": "उ", "\u0a0a": "ऊ",
    "\u0a0f": "ए", "\u0a10": "ऐ", "\u0a13": "ओ", "\u0a14": "औ",
    "\u0a15": "क", "\u0a16": "ख", "\u0a17": "ग", "\u0a18": "घ", "\u0a19": "ङ",
    "\u0a1a": "च", "\u0a1b": "छ", "\u0a1c": "ज", "\u0a1d": "झ", "\u0a1e": "ञ",
    "\u0a1f": "ट", "\u0a20": "ठ", "\u0a21": "ड", "\u0a22": "ढ", "\u0a23": "ण",
    "\u0a24": "त", "\u0a25": "थ", "\u0a26": "द", "\u0a27": "ध", "\u0a28": "न",
    "\u0a2a": "प", "\u0a2b": "फ", "\u0a2c": "ब", "\u0a2d": "भ", "\u0a2e": "म",
    "\u0a2f": "य", "\u0a30": "र", "\u0a32": "ल", "\u0a33": "ळ", "\u0a35": "व",
    "\u0a36": "श", "\u0a38": "स", "\u0a39": "ह",
    "\u0a59": "ख़", "\u0a5a": "ग़", "\u0a5b": "ज़", "\u0a5c": "ड़", "\u0a5e": "फ़",
    "\u0a3e": "ा", "\u0a3f": "ि", "\u0a40": "ी", "\u0a41": "ु", "\u0a42": "ू",
    "\u0a47": "े", "\u0a48": "ै", "\u0a4b": "ो", "\u0a4c": "ौ",
    "\u0a4d": "्", "\u0a01": "ँ", "\u0a02": "ं", "\u0a70": "ं", "\u0a71": "", "\u0a3c": "़"
}

ODIA_TO_DEVANAGARI = {
    "\u0b05": "अ", "\u0b06": "आ", "\u0b07": "इ", "\u0b08": "ई", "\u0b09": "उ", "\u0b0a": "ऊ",
    "\u0b0f": "ए", "\u0b10": "ऐ", "\u0b13": "ओ", "\u0b14": "औ",
    "\u0b15": "क", "\u0b16": "ख", "\u0b17": "ग", "\u0b18": "घ", "\u0b19": "ङ",
    "\u0b1a": "च", "\u0b1b": "छ", "\u0b1c": "ज", "\u0b1d": "झ", "\u0b1e": "ञ",
    "\u0b1f": "ट", "\u0b20": "ठ", "\u0b21": "ड", "\u0b22": "ढ", "\u0b23": "ण",
    "\u0b24": "त", "\u0b25": "थ", "\u0b26": "द", "\u0b27": "ध", "\u0b28": "न",
    "\u0b2a": "प", "\u0b2b": "फ", "\u0b2c": "ब", "\u0b2d": "भ", "\u0b2e": "म",
    "\u0b2f": "य", "\u0b30": "र", "\u0b32": "ल", "\u0b33": "ळ", "\u0b35": "व",
    "\u0b36": "श", "\u0b37": "ष", "\u0b38": "स", "\u0b39": "ह",
    "\u0b3e": "ा", "\u0b3f": "ि", "\u0b40": "ी", "\u0b41": "ु", "\u0b42": "ू",
    "\u0b47": "े", "\u0b48": "ै", "\u0b4b": "ो", "\u0b4c": "ौ",
    "\u0b4d": "्", "\u0b01": "ँ", "\u0b02": "ं", "\u0b3c": "़"
}

def transliterate_unsupported_scripts(text: str) -> str:
    """Converts unsupported scripts like Gurmukhi/Odia into phonetic Devanagari for smooth Edge-TTS speech."""
    if bool(re.search(r'[\u0a00-\u0a7f]', text)):
        return "".join(GURMUKHI_TO_DEVANAGARI.get(ch, ch) for ch in text)
    if bool(re.search(r'[\u0b00-\u0b7f]', text)):
        return "".join(ODIA_TO_DEVANAGARI.get(ch, ch) for ch in text)
    return text

# ============================================================================
# Decimal-Safe Text Sanitization Layer
# ============================================================================
def clean_text_for_tts(text: str, is_hindi: bool = False, lang: str = "hi-IN") -> str:
    """
    Strips raw markdown syntax, code snippets, hashtags, bullets, emojis, and URLs.
    Normalizes decimal numbers, percentages, temperatures, distances, and units
    so edge-tts speaks fluid human words with zero stuttering or decimal splitting.
    """
    if not text:
        return ""

    t = text

    # 1. Strip Markdown code blocks & inline backticks
    t = re.sub(r'```[\s\S]*?```', ' ', t)
    t = re.sub(r'`([^`]+)`', r'\1', t)

    # 2. Remove Source/स्रोत citation links and URLs so they are not read aloud
    t = re.sub(r'(?:Source|स्रोत)\s*:\s*\[.*?\]\(.*?\)', ' ', t, flags=re.IGNORECASE)
    t = re.sub(r'https?://\S+', ' ', t)
    t = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', t)

    # 3. Strip Markdown headers (#), asterisks (*), hashtags (#), tildes (~), pipes (|), underscores (_)
    t = re.sub(r'[#*_~|]', ' ', t)

    # 4. Remove brackets, braces, parentheses, bullets, dashes, em-dashes, middle-dots
    t = re.sub(r'[\[\]\(\)\{\}]', ' ', t)
    t = re.sub(r'[-—–•*+>»«·~]', ' ', t)

    # 5. Strip all UI emojis and symbols
    emoji_pattern = re.compile(
        r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]|'
        r'[🌾💧🚜📊📉🟢🟡🟠🔴⚠️✅🚫🛑💡🙏👋➡️📈📍⚡🌐💰📝🔗🏷️🧭🏛️ℹ️]'
    )
    t = emoji_pattern.sub(' ', t)

    # 6. Language-Sensitive Pronunciation & Unit Normalization
    l_clean = (lang or "").lower().strip()
    is_indic = is_hindi or any(l_clean.startswith(code) for code in [
        "hi", "pa", "bn", "mr", "gu", "ta", "te", "kn", "ml", "or", "as", "ur", "bho", "mai", "sa", "raj", "bgc"
    ]) or bool(re.search(r'[\u0900-\u097F\u0A00-\u0A7F\u0980-\u09FF\u0A80-\u0AFF\u0B00-\u0B7F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F]', text))

    if is_indic:
        # Percentages: 206.3% -> 206.3 प्रतिशत
        t = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'\1 प्रतिशत ', t)
        t = t.replace('%', ' प्रतिशत ')
        # Temperatures: 37.6°C -> 37.6 डिग्री सेल्सियस
        t = re.sub(r'(\d+(?:\.\d+)?)\s*°[Cc]', r'\1 डिग्री सेल्सियस ', t)
        # Distances and depths
        t = re.sub(r'(\d+(?:\.\d+)?)\s*mm\b', r'\1 मिलीमीटर ', t)
        t = re.sub(r'(\d+(?:\.\d+)?)\s*m\b', r'\1 मीटर ', t)
        t = re.sub(r'(\d+(?:\.\d+)?)\s*ft\b', r'\1 फुट ', t)
        t = re.sub(r'\bbgl\b', ' ज़मीन के नीचे ', t, flags=re.IGNORECASE)
        # Acronyms and agencies
        t = t.replace('Ham', ' हेक्टेयर मीटर ')
        t = t.replace('ham', ' हेक्टेयर मीटर ')
        t = t.replace('mbgl', ' मीटर गहराई ')
        t = t.replace('PMKSY', ' पीएमकेएसवाई ')
        t = t.replace('CGWB', ' केंद्रीय भूजल बोर्ड ')
        t = t.replace('CGWA', ' केंद्रीय भूजल प्राधिकरण ')
        t = t.replace('ICAR', ' आईसीएआर ')
        t = t.replace('NOC', ' एनओसी ')
    else:
        # Percentages: 206.3% -> 206.3 percent
        t = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'\1 percent ', t)
        t = t.replace('%', ' percent ')
        # Temperatures: 37.6°C -> 37.6 degrees Celsius
        t = re.sub(r'(\d+(?:\.\d+)?)\s*°[Cc]', r'\1 degrees Celsius ', t)
        # Distances and depths
        t = re.sub(r'(\d+(?:\.\d+)?)\s*mm\b', r'\1 millimeters ', t)
        t = re.sub(r'(\d+(?:\.\d+)?)\s*m\b', r'\1 meters ', t)
        t = re.sub(r'(\d+(?:\.\d+)?)\s*ft\b', r'\1 feet ', t)
        t = re.sub(r'\bbgl\b', ' below ground level ', t, flags=re.IGNORECASE)
        # Acronyms and agencies
        t = t.replace('Ham', ' Hectare meters ')
        t = t.replace('ham', ' Hectare meters ')
        t = t.replace('mbgl', ' meters depth ')
        t = t.replace('PMKSY', ' Pradhan Mantri Krishi Sinchayee Yojana ')
        t = t.replace('CGWB', ' Central Ground Water Board ')
        t = t.replace('CGWA', ' Central Ground Water Authority ')
        t = t.replace('ICAR', ' ICAR ')
        t = t.replace('NOC', ' NOC ')

    # 7. Convert unsupported scripts like Gurmukhi & Odia to phonetic Devanagari
    t = transliterate_unsupported_scripts(t)

    # 8. Normalize punctuation to standard natural breathing pauses
    t = re.sub(r'[:;]', ',', t)
    t = re.sub(r'\.{2,}', '.', t)
    t = re.sub(r'!{2,}', '.', t)
    t = re.sub(r'\?{2,}', '?', t)
    t = re.sub(r'[,]{2,}', ',', t)
    t = re.sub(r'\n+', '. ', t)

    # 9. Clean spacing without breaking decimals (e.g. 59.4 must NOT be split into 59. 4)
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'(?<!\d)([.,?])(?!\d)', r'\1 ', t)
    t = re.sub(r'\s+([.,?])', r'\1', t)
    t = re.sub(r'\s+', ' ', t).strip()

    return t

# ============================================================================
# Dynamic Voice Resolution
# ============================================================================
def resolve_voice(lang: str = "hi-IN", preferred_voice: Optional[str] = None, text: str = "") -> str:
    """
    Dynamically resolves the best Microsoft Neural Voice from the 22 Indian language registry.
    Detects native scripts automatically if language is unspecified.
    """
    if preferred_voice and preferred_voice in NEURAL_VOICES.values():
        return preferred_voice

    l_clean = (lang or "").lower().strip()

    # 1. Explicit mapping match
    if l_clean in NEURAL_VOICES:
        return NEURAL_VOICES[l_clean]

    # 2. Prefix mapping match (e.g. 'hi-IN-something' -> 'hi-IN')
    for key, voice in NEURAL_VOICES.items():
        if l_clean.startswith(key):
            return voice

    # 3. Automatic Script Detection for Indian Languages
    if text:
        if bool(re.search(r'[\u0900-\u097F\u0A00-\u0A7F\u0B00-\u0B7F]', text)): # Devanagari, Gurmukhi, Odia
            return NEURAL_VOICES["hi"]
        elif bool(re.search(r'[\u0980-\u09FF]', text)): # Bengali / Assamese
            return NEURAL_VOICES["bn"]
        elif bool(re.search(r'[\u0A80-\u0AFF]', text)): # Gujarati
            return NEURAL_VOICES["gu"]
        elif bool(re.search(r'[\u0B80-\u0BFF]', text)): # Tamil
            return NEURAL_VOICES["ta"]
        elif bool(re.search(r'[\u0C00-\u0C7F]', text)): # Telugu
            return NEURAL_VOICES["te"]
        elif bool(re.search(r'[\u0C80-\u0CFF]', text)): # Kannada
            return NEURAL_VOICES["kn"]
        elif bool(re.search(r'[\u0D00-\u0D7F]', text)): # Malayalam
            return NEURAL_VOICES["ml"]
        elif bool(re.search(r'[\u0600-\u06FF]', text)): # Perso-Arabic (Urdu, Kashmiri, Sindhi)
            return NEURAL_VOICES["ur"]

    # Default fallback: Indian English Neerja
    return "en-IN-NeerjaNeural"

# ============================================================================
# Pacing & Audio Delivery Engine
# ============================================================================
async def generate_speech(
    text: str,
    lang: str = "hi-IN",
    voice: Optional[str] = None,
    rate: str = "-4%",  # Tuned for calm, non-rushed natural human cadence
    pitch: str = "+0Hz"
) -> bytes:
    """
    Synthesizes speech using edge-tts into raw MP3 audio bytes with full text sanitization.
    Streams directly into an in-memory io.BytesIO buffer with automatic fallback recovery.
    """
    if not text or not text.strip():
        return b""

    is_hindi = (lang == "hi" or bool(re.search(r'[\u0900-\u097F]', text)))
    cleaned_text = clean_text_for_tts(text, is_hindi=is_hindi, lang=lang)

    if not cleaned_text:
        return b""

    chosen_voice = resolve_voice(lang, voice, cleaned_text)
    logger.info(f"Synthesizing neural speech with voice '{chosen_voice}' rate='{rate}' ({len(cleaned_text)} chars)")

    try:
        communicate = edge_tts.Communicate(cleaned_text, voice=chosen_voice, rate=rate, pitch=pitch)
        audio_stream = io.BytesIO()

        async for chunk in communicate.stream():
            if chunk.get("type") == "audio" and "data" in chunk:
                audio_stream.write(chunk["data"])

        return audio_stream.getvalue()
    except Exception as e:
        logger.warning(f"Edge-TTS synthesis failed for voice '{chosen_voice}': {e}")
        # Automatic fallback recovery to primary voice if voice-specific issue occurs
        try:
            fallback_voice = "hi-IN-SwaraNeural" if is_hindi else "en-IN-NeerjaNeural"
            if chosen_voice != fallback_voice:
                logger.info(f"Retrying with fallback voice '{fallback_voice}'...")
                communicate = edge_tts.Communicate(cleaned_text, voice=fallback_voice, rate=rate, pitch=pitch)
                audio_stream = io.BytesIO()
                async for chunk in communicate.stream():
                    if chunk.get("type") == "audio" and "data" in chunk:
                        audio_stream.write(chunk["data"])
                return audio_stream.getvalue()
        except Exception as fallback_err:
            logger.error(f"Fallback Edge-TTS also failed: {fallback_err}")
        return b""

async def generate_speech_base64(
    text: str,
    lang: str = "hi-IN",
    voice: Optional[str] = None,
    rate: str = "-4%"
) -> Optional[str]:
    """
    Synthesizes speech and returns a base64 encoded audio data URL for browser playback.
    Format: 'data:audio/mp3;base64,...'
    """
    try:
        audio_bytes = await generate_speech(text, lang=lang, voice=voice, rate=rate)
        if not audio_bytes:
            return None
        encoded = base64.b64encode(audio_bytes).decode("utf-8")
        return f"data:audio/mp3;base64,{encoded}"
    except Exception as e:
        logger.error(f"Failed to generate base64 speech: {e}")
        return None
