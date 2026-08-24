"""
indic_nlp.py
Hugging Face Serverless Inference API Integration for Indic NLP Intent & Entity Routing.
Supports zero-shot multilingual intent classification (BART/mDeBERTa/Indic-BERT)
and strict geographical entity validation for Indian groundwater queries.
"""

import re
import logging
from typing import Optional, Dict, Any, Tuple
import httpx

from config import HUGGINGFACE_API_KEY, HUGGINGFACE_MODEL, is_huggingface_configured

logger = logging.getLogger("indic_nlp")

# Comprehensive Transliteration Dictionary for Indian Districts & Locations
TRANSLITERATION_MAP = {
    # Uttar Pradesh
    "मेरठ": "Meerut", "वाराणसी": "Varanasi", "काशी": "Varanasi", "बनारस": "Varanasi",
    "आगरा": "Agra", "लखनऊ": "Lucknow", "अलीगढ़": "Aligarh", "गोरखपुर": "Gorakhpur",
    "झांसी": "Jhansi", "प्रयागराज": "Prayagraj", "इलाहाबाद": "Prayagraj",
    "कानपुर": "Kanpur", "बरेली": "Bareilly", "मुरादाबाद": "Moradabad", "सहारनपुर": "Saharanpur",
    
    # Punjab
    "लुधियाना": "Ludhiana", "संगरूर": "Sangrur", "जालंधर": "Jalandhar",
    "अमृतसर": "Amritsar", "बठिंडा": "Bathinda", "पटियाला": "Patiala",
    "होशियारपुर": "Hoshiarpur", "मोहाली": "Mohali", "फिरोजपुर": "Firozpur",
    
    # Rajasthan
    "जयपुर": "Jaipur", "जोधपुर": "Jodhpur", "जैसलमेर": "Jaisalmer", "बीकानेर": "Bikaner",
    "सीकर": "Sikar", "अलवर": "Alwar", "झुंझुनू": "Jhunjhunu", "कोटा": "Kota",
    "नागौर": "Nagaur", "उदयपुर": "Udaipur", "अजमेर": "Ajmer", "बाड़मेर": "Barmer", "चूरू": "Churu",
    
    # Maharashtra
    "पुणे": "Pune", "नागपुर": "Nagpur", "नासिक": "Nashik",
    "छत्रपति संभाजीनगर": "Chhatrapati Sambhajinagar", "औरंगाबाद": "Chhatrapati Sambhajinagar",
    "अहमदनगर": "Ahmednagar", "सोलापुर": "Solapur", "मुंबई": "Mumbai", "ठाणे": "Thane",
    
    # Haryana
    "करनाल": "Karnal", "कुरुक्षेत्र": "Kurukshetra", "सिरसा": "Sirsa",
    "गुरुग्राम": "Gurugram", "गुड़गांव": "Gurugram", "हिसार": "Hisar", "अंबाला": "Ambala",
    "पानीपत": "Panipat", "रोहतक": "Rohtak", "सोनीपत": "Sonipat",
    
    # Madhya Pradesh
    "इंदौर": "Indore", "उज्जैन": "Ujjain", "भोपाल": "Bhopal",
    "जबलपुर": "Jabalpur", "ग्वालियर": "Gwalior", "सागर": "Sagar", "रीवा": "Rewa",
    
    # Bihar
    "पटना": "Patna", "गया": "Gaya", "मुजफ्फरपुर": "Muzaffarpur",
    "भागलपुर": "Bhagalpur", "नालंदा": "Nalanda", "दरभंगा": "Darbhanga", "पूर्णिया": "Purnia",
    
    # Southern & Other States
    "नेल्लोर": "Nellore", "रायचूर": "Raichur", "अनंतपुर": "Anantapur", "वारंगल": "Warangal",
    "कोयंबटूर": "Coimbatore", "मदुरै": "Madurai", "बेलगाम": "Belagavi"
}

# Strict blacklist of words that must NEVER be parsed as district entities
NON_DISTRICT_WORDS = {
    # Conceptual / category words
    "high", "low", "dark", "zone", "zones", "safe", "critical", "semi", "semi-critical", "semicritical",
    "over", "exploited", "over-exploited", "overexploited", "darkzone", "dark-zone", "category", "categories",
    "stage", "stages", "status", "level", "levels", "depth", "rate", "rates", "percentage", "percent",
    "extraction", "groundwater", "water", "waters", "aquifer", "depletion", "overdraft", "resource", "resources",
    
    # Agriculture / crop / borewell terms
    "crop", "crops", "fasal", "faslein", "kheti", "farming", "farmer", "farmers", "agriculture",
    "borewell", "borewells", "tubewell", "tubewells", "boring", "drilling", "drill", "pump", "pumps",
    "irrigation", "sichai", "drip", "sprinkler", "mulch", "mulching", "scheme", "schemes",
    "subsidy", "subsidies", "yojana", "anudan", "pmksy", "dbt", "cgwb", "cgwa", "ingres", "ministry", "portal",
    "permission", "allowed", "feasible", "prohibited", "rule", "rules", "law", "advisory", "advice", "guideline", "guidelines",
    "save", "saving", "harvesting", "recharge", "rainwater", "shaft", "soil", "sand", "pot", "tips", "technique", "techniques",
    "moisture", "nami", "mitti", "satellite", "telemetry", "temperature",
    
    # Conversational & question words
    "what", "which", "where", "how", "who", "whom", "whose", "when", "why", "tell", "give", "show", "check", "know", "find", "get", "explain", "meaning", "definition", "list", "types",
    "is", "are", "was", "were", "the", "a", "an", "and", "or", "nor", "but", "so", "yet", "both", "either", "neither",
    "i", "can", "could", "should", "would", "may", "might", "must", "grow", "suggest", "suggestion", "suggestions",
    "you", "your", "yours", "me", "my", "mine", "he", "she", "it", "they", "them", "this", "that", "these", "those", "self", "yourself",
    "kya", "kaise", "kitna", "kitni", "kitne", "batao", "bataye", "batana", "jankari", "suchna", "hai", "hain", "hoon", "hun", "ho", "ka", "ki", "ke", "aur", "ya", "mein", "par", "se", "ko",
    "mera", "meri", "mere", "khet", "khet me", "khet mein", "main", "hum", "aap", "tum",
    "hi", "hello", "hey", "namaste", "namaskar", "pranam", "please", "kisan", "sahayak", "jal", "shakti", "india", "bharat", "state", "district", "block", "city", "village", "area", "region",
    "help", "madad", "chahiye", "good", "morning", "evening", "afternoon",

    
    # Hindi verbs & terms
    "डार्क", "जोन", "अतिदोहित", "अति-दोहित", "क्रिटिकल", "सुरक्षित", "सेमी", "पानी", "भूजल", "फसल", "फसलें", "सिंचाई", "बोरवेल", "नलकूप", "नियम", "सब्सिडी", "योजना", "अनुदान", "बचत", "तरीके", "सलाह", "कैटेगरी", "श्रेणी", "श्रेणियां", "दोहन", "स्तर", "अनुमति", "ड्रिप", "स्प्रिंकलर", "सहायक", "इंग्रेस",
    "नमी", "मिट्टी", "तापमान", "सैटेलाइट",
    "बताएं", "बताइए", "बताओ", "बताने", "होता", "होती", "होते", "सकते", "सकती", "सकता", "चाहिए", "लगाना", "लगाए", "लगाएं", "जानना", "पूछना", "दिखाइए", "करना", "बचाएं", "कम", "ज्यादा", "अधिक", "क्या", "कैसे", "कितना", "कहाँ", "कहा", "कौन", "कौनसा", "कौनसी", "है", "हैं", "हूँ", "हो", "का", "की", "के", "में", "पर", "से", "को", "और", "या"
}

# Common query typo corrections dictionary
TYPO_CORRECTIONS = {
    r"\bborwell\b": "borewell",
    r"\bborwells\b": "borewells",
    r"\bboring\b": "borewell",
    r"\btubwell\b": "tubewell",
    r"\bkponsi\b": "kaun si",
    r"\bkaunsi\b": "kaun si",
    r"\bkon si\b": "kaun si",
    r"\bkonsi\b": "kaun si",
    r"\bmausam\b": "weather",
    r"\bmosam\b": "weather",
    r"\bfasle\b": "fasal",
    r"\bfaslen\b": "fasal",
    r"\bfaslein\b": "fasal",
    r"\bfaslo\b": "fasal",
    r"\bfaslon\b": "fasal",
    r"\bfasalon\b": "fasal",
    r"\bfashal\b": "fasal",
    r"\bfashle\b": "fasal",
    r"\bfashlen\b": "fasal",
    r"\bफैसले\b": "फसल",
    r"\bफैसल\b": "फसल",
    r"\bफैसलों\b": "फसल",
    r"\bफैसलें\b": "फसल",
    r"\bफसलें\b": "फसल",
    r"\bफसलों\b": "फसल",
    r"\bpanni\b": "paani",
    r"\bpanie\b": "paani",
    r"\bbarish\b": "rain",
    r"\bbaaris\b": "rain",
    r"\bvarsa\b": "rain",
    r"\bsichaye\b": "sichai"
}



def clean_query_typos(text: str) -> str:
    """Applies high-speed regex typo replacements on the incoming query."""
    if not text:
        return ""
    cleaned = text
    for pattern, repl in TYPO_CORRECTIONS.items():
        cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)
    return cleaned

INDIAN_STATES_AND_METROS = {
    "delhi": {"name": "Delhi", "type": "ut_metro", "aliases": ["delhi", "dilli", "nct", "दिल्ली", "नई दिल्ली", "new delhi"]},
    "bihar": {"name": "Bihar", "type": "state", "aliases": ["bihar", "बिहार"]},
    "uttar pradesh": {"name": "Uttar Pradesh", "type": "state", "aliases": ["uttar pradesh", "up", "उत्तर प्रदेश", "यूपी"]},
    "punjab": {"name": "Punjab", "type": "state", "aliases": ["punjab", "पंजाब"]},
    "haryana": {"name": "Haryana", "type": "state", "aliases": ["haryana", "हरियाणा"]},
    "rajasthan": {"name": "Rajasthan", "type": "state", "aliases": ["rajasthan", "राजस्थान"]},
    "tamil nadu": {"name": "Tamil Nadu", "type": "state", "aliases": ["tamil nadu", "tamilnadu", "तमिलनाडु", "तमिलनाडू"]},
    "maharashtra": {"name": "Maharashtra", "type": "state", "aliases": ["maharashtra", "महाराष्ट्र"]},
    "karnataka": {"name": "Karnataka", "type": "state", "aliases": ["karnataka", "कर्नाटक"]},
    "gujarat": {"name": "Gujarat", "type": "state", "aliases": ["gujarat", "गुजरात"]},
    "west bengal": {"name": "West Bengal", "type": "state", "aliases": ["west bengal", "bengal", "पश्चिम बंगाल", "बंगाल"]},
    "madhya pradesh": {"name": "Madhya Pradesh", "type": "state", "aliases": ["madhya pradesh", "mp", "मध्य प्रदेश", "एमपी"]},
    "kerala": {"name": "Kerala", "type": "state", "aliases": ["kerala", "केरल"]},
    "andhra pradesh": {"name": "Andhra Pradesh", "type": "state", "aliases": ["andhra pradesh", "andhra", "आंध्र प्रदेश"]},
    "telangana": {"name": "Telangana", "type": "state", "aliases": ["telangana", "तेलंगाना"]},
    "odisha": {"name": "Odisha", "type": "state", "aliases": ["odisha", "orissa", "ओडिशा", "उड़ीसा"]},
    "jharkhand": {"name": "Jharkhand", "type": "state", "aliases": ["jharkhand", "झारखंड"]},
    "chhattisgarh": {"name": "Chhattisgarh", "type": "state", "aliases": ["chhattisgarh", "छत्तीसगढ़"]},
    "uttarakhand": {"name": "Uttarakhand", "type": "state", "aliases": ["uttarakhand", "उत्तराखंड", "uttaranchal"]},
    "himachal pradesh": {"name": "Himachal Pradesh", "type": "state", "aliases": ["himachal pradesh", "himachal", "हिमाचल प्रदेश"]},
    "assam": {"name": "Assam", "type": "state", "aliases": ["assam", "असम"]},
    "mumbai": {"name": "Mumbai", "type": "metro", "aliases": ["mumbai", "bombay", "मुंबई"]},
    "bengaluru": {"name": "Bengaluru", "type": "metro", "aliases": ["bengaluru", "bangalore", "बेंगलुरु", "बैंगलोर"]},
    "kolkata": {"name": "Kolkata", "type": "metro", "aliases": ["kolkata", "calcutta", "कोलकाता"]},
    "chennai": {"name": "Chennai", "type": "metro", "aliases": ["chennai", "madras", "चेन्नई"]},
    "hyderabad": {"name": "Hyderabad", "type": "metro", "aliases": ["hyderabad", "हैदराबाद"]}
}

def extract_state_or_metro(query: str) -> Optional[Dict[str, Any]]:
    """Detects if query targets an Indian State, UT, or Major Metro."""
    q_clean = clean_query_typos(query).lower()
    for key, data in INDIAN_STATES_AND_METROS.items():
        for alias in data["aliases"]:
            pattern = rf'\b{re.escape(alias)}\b'
            if re.search(pattern, q_clean):
                return {
                    "key": key,
                    "name": data["name"],
                    "type": data["type"]
                }
    return None

INDIAN_STATES = set(INDIAN_STATES_AND_METROS.keys())

# Candidate labels for Hugging Face Zero-Shot Intent Classification
HF_INTENT_LABELS = {
    "borewell drilling permission rules or CGWA NOC": "borewell_rule",
    "crop recommendation agriculture farming or fasal": "crop_advisory",
    "groundwater water level depth or extraction status": "water_status",
    "casual greeting namaste or general conversation": "casual_chat"
}


def detect_language(text: str, preferred_lang: Optional[str] = None) -> str:
    """Detects if input is Hindi or English."""
    if re.search(r'[\u0900-\u097F]', text):
        return "hi"
    hinglish_keywords = {
        "kya", "kyu", "kaise", "kitna", "kitni", "kitne", "pani", "paani", "jal", "kisan",
        "fasal", "faslein", "khet", "kheti", "sichai", "laga", "lagaye", "lagana", "sakta", "sakte", "sakti",
        "hai", "hain", "hoon", "hun", "ho", "batao", "bataye", "batana", "chahiye", "namaste", "namaskar",
        "jankari", "suchna", "sahayak", "aur", "ya", "mera", "meri", "mere", "aap", "hum",
        "yojana", "anudan", "pranam", "sthir", "kare", "karna", "krishi",
        "hal", "kaisa", "kaisi", "kaun", "kaha", "kahan", "mujhe", "bataiye", "ram", "bhai", "hisab", "shukriya", "dhanyawad"
    }
    words = set(re.findall(r'[a-zA-Z]+', text.lower()))
    if any(w in hinglish_keywords for w in words):
        return "hi"
    if preferred_lang and preferred_lang.lower() in ("hi", "hindi"):
        return "hi"
    return "en"

def is_valid_district_entity(candidate: Optional[str]) -> bool:
    """Strict guardrail to ensure an entity is a genuine location and not a conceptual term."""
    if not candidate or len(candidate.strip()) < 3:
        return False
    c_lower = candidate.strip().lower()
    if c_lower in NON_DISTRICT_WORDS:
        return False
    for w in c_lower.split():
        if w in NON_DISTRICT_WORDS and len(c_lower.split()) == 1:
            return False
    return True

def extract_district_entity(query: str) -> Optional[str]:
    """
    Extracts a verified geographical district/block/village/state from query.
    Prioritizes State/Metro detection to avoid false village substring matches.
    """
    cleaned_query = clean_query_typos(query)
    normalized = cleaned_query.lower()
    for hi_name, en_name in TRANSLITERATION_MAP.items():
        if hi_name in query:
            normalized = normalized.replace(hi_name, en_name.lower())

    # 1. State / UT / Metro Check (Highest Priority)
    state_match = extract_state_or_metro(cleaned_query)
    if state_match:
        return state_match["name"]

    # 2. Match transliteration / seeded district dictionary
    for hi_name, en_name in TRANSLITERATION_MAP.items():
        if (re.search(rf"\b{re.escape(en_name.lower())}\b", normalized) or hi_name in query):
            return en_name.title()

    # 3. Match explicit preposition patterns
    geo_patterns = [
        r'\bin\s+([a-zA-Z\u0900-\u097F]{3,}(?:\s+[a-zA-Z\u0900-\u097F]{3,})?)\b',
        r'\bfor\s+([a-zA-Z\u0900-\u097F]{3,}(?:\s+[a-zA-Z\u0900-\u097F]{3,})?)\b',
        r'\b([a-zA-Z\u0900-\u097F]{3,})\s+(?:district|zilla|zila|block|tehsil|mandal|state|city|town|village|gram|panchayat)\b',
        r'\b([a-zA-Z\u0900-\u097F]{3,})\s+(?:mein|me|ka|ki|ke|par|se)\b'
    ]
    for pat in geo_patterns:
        m = re.search(pat, normalized)
        if m:
            cand = m.group(1).strip().title()
            if is_valid_district_entity(cand):
                return cand

    # 4. Check word tokens/bi-grams against CGWB database directly (District > Block > Village)
    words = [w for w in re.findall(r'[a-zA-Z\u0900-\u097F]+', cleaned_query) if len(w) >= 3]
    for i in range(len(words) - 1):
        ngram = f"{words[i]} {words[i+1]}"
        if is_valid_district_entity(ngram):
            try:
                from app.db_service import get_cgwb_water_level
                station = get_cgwb_water_level(ngram)
                if station:
                    return ngram.title()
            except Exception:
                pass

    for w in words:
        if is_valid_district_entity(w):
            try:
                from app.db_service import get_cgwb_water_level
                station = get_cgwb_water_level(w)
                if station:
                    return w.title()
            except Exception:
                pass

    return None


def classify_intent_local(query: str) -> Tuple[str, float]:
    """
    High-precision local Indic rule/regex classifier for fallback or instant routing.
    """
    q_lower = query.lower().strip()
    clean_q = re.sub(r'[^\w\s\u0900-\u097F]', ' ', q_lower).strip()

    greetings = {
        "hi", "hello", "hey", "namaste", "namaskar", "good morning", "good afternoon",
        "good evening", "kaise ho", "kya haal hai", "who are you", "aap kaun ho",
        "aap kaun hain", "kya kar sakte ho", "help", "madad", "hi sahayak", "hello bot",
        "who is jal", "what is your name", "tum kaun ho", "kaun ho tum",
        "ram ram", "ram ram bhai", "radhe radhe", "pranam", "pranam bhai", "jai shree ram",
        "नमस्ते", "नमस्कार", "प्रणाम", "जय हिंद", "राम राम", "राधे राधे", "हाय", "हेलो",
        "सुप्रभात", "शुभ संध्या", "आप कौन हैं", "आप क्या कर सकते हैं", "नमसते", "प्रनाम",
        "तुम कौन हो", "आपका नाम क्या है", "कैसे हो", "क्या हाल है"
    }
    if clean_q in greetings or any(clean_q.startswith(g + " ") or clean_q == g for g in greetings):
        return "casual_chat", 0.99

    borewell_keywords = [
        "borewell", "tubewell", "boring", "drilling", "permission", "noc",
        "बोरवेल", "नलकूप", "बोरिंग", "अनुमति", "मंजूरी", "खुदाई", "एनओसी"
    ]
    if any(w in q_lower for w in borewell_keywords):
        return "borewell_rule", 0.95

    crop_keywords = [
        "crop", "crops", "farming", "fasal", "faslen", "fasle", "faslein", "faslon", "fasalon", "fashal", "fashle",
        "kheti", "sichai", "irrigation", "kya ugana chahiye", "konsi fasal", "kaun si fasal", "kaun si faslen", "what to grow",
        "agriculture", "ugana", "ugayein", "ugaye", "ugana chahiye", "uga sakta", "uga sakte", "uga sakti",
        "boye", "boyen", "bona", "kheti badi", "grow", "plant", "produce",
        "फसल", "फसलें", "फसलों", "फैसले", "फैसलें", "खेती", "सिंचाई", "उपयुक्त फसल", "मोटे अनाज", "ड्रिप", "बोएं",
        "बोना", "क्या उगाएं", "कौनसी फसल", "उपज", "कृषि", "उगा सकते", "उगा सकता", "उगाएं"
    ]

    if any(w in q_lower for w in crop_keywords):
        return "crop_advisory", 0.95

    water_keywords = [
        "water", "groundwater", "extraction", "level", "percentage", "safe", "critical",
        "semi-critical", "over-exploited", "stage", "पानी", "भूजल", "दोहन", "जल स्तर", "अतिदोहित", "डार्क"
    ]
    if any(w in q_lower for w in water_keywords):
        return "water_status", 0.95

    return "water_status", 0.70

async def call_huggingface_inference(text: str) -> Optional[Dict[str, Any]]:
    """
    Calls Hugging Face Serverless Inference API for zero-shot classification.
    """
    if not is_huggingface_configured():
        return None

    model_name = HUGGINGFACE_MODEL or "facebook/bart-large-mnli"
    endpoints = [
        f"https://router.huggingface.co/hf-inference/models/{model_name}",
        f"https://api-inference.huggingface.co/models/{model_name}"
    ]
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": text,
        "parameters": {
            "candidate_labels": list(HF_INTENT_LABELS.keys())
        }
    }

    for api_url in endpoints:
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                resp = await client.post(api_url, headers=headers, json=payload)

                if resp.status_code == 200:
                    data = resp.json()
                    # Format 1: List of dicts [{'label': '...', 'score': 0.95}, ...]
                    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "label" in data[0]:
                        top = data[0]
                        top_label = top.get("label", "")
                        top_score = float(top.get("score", 0.0))
                        mapped_intent = HF_INTENT_LABELS.get(top_label, "water_status")
                        return {
                            "intent": mapped_intent,
                            "confidence": top_score,
                            "raw_label": top_label,
                            "model": model_name
                        }
                    # Format 2: Dict {'labels': [...], 'scores': [...]}
                    elif isinstance(data, dict):
                        labels = data.get("labels", [])
                        scores = data.get("scores", [])
                        if labels and scores:
                            top_label = labels[0]
                            top_score = float(scores[0])
                            mapped_intent = HF_INTENT_LABELS.get(top_label, "water_status")
                            return {
                                "intent": mapped_intent,
                                "confidence": top_score,
                                "raw_label": top_label,
                                "model": model_name
                            }
                else:
                    logger.warning(f"HF endpoint {api_url} returned HTTP {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            logger.warning(f"HF Inference call on {api_url} failed: {e}")

    return None

async def parse_indic_intent_and_entities(text: str) -> Dict[str, Any]:
    """
    Main entry point for Indic Intent & Entity Routing.
    1. Extracts verified geographical district (or None if conceptual).
    2. Identifies language (Hindi / English / Hinglish).
    3. Runs Hugging Face Serverless Zero-Shot classification (with graceful local fallback).
    """
    lang = detect_language(text)
    district = extract_district_entity(text)

    # Fast-path for high-confidence local rules (greetings, borewell keywords, crop keywords)
    local_intent, local_conf = classify_intent_local(text)
    if local_intent == "casual_chat":
        return {
            "intent": "casual_chat",
            "district": None,
            "confidence": local_conf,
            "language": lang,
            "model_used": "local_indic_rules",
            "source": "local_indic_nlp"
        }
    if local_conf >= 0.70:
        return {
            "intent": local_intent,
            "district": district,
            "confidence": local_conf,
            "language": lang,
            "model_used": "local_indic_rules",
            "source": "local_indic_nlp"
        }


    # Query Hugging Face Serverless API if configured
    hf_result = await call_huggingface_inference(text)
    if hf_result and hf_result.get("confidence", 0.0) >= 0.35:
        inferred_intent = hf_result["intent"]
        # Guardrail: If district is extracted, it cannot be casual_chat
        if district and inferred_intent == "casual_chat":
            q_lower = text.lower()
            if any(w in q_lower for w in ["borewell", "boring", "tubewell", "permission", "noc", "बोरवेल", "नलकूप", "नियम"]):
                inferred_intent = "borewell_rule"
            elif any(w in q_lower for w in ["crop", "fasal", "kheti", "sichai", "फसल", "खेती", "सिंचाई"]):
                inferred_intent = "crop_advisory"
            else:
                inferred_intent = "water_status"

        return {
            "intent": inferred_intent,
            "district": district,
            "confidence": round(hf_result["confidence"], 3),
            "language": lang,
            "model_used": hf_result.get("model", "huggingface"),
            "source": "huggingface_inference"
        }

    # Local Indic NLP Fallback
    fallback_intent = local_intent
    if district and fallback_intent == "casual_chat":
        fallback_intent = "water_status"

    return {
        "intent": fallback_intent,
        "district": district,
        "confidence": round(local_conf, 3),
        "language": lang,
        "model_used": "local_indic_rules",
        "source": "local_indic_nlp"
    }
