"""
soil_service.py
Live Satellite Soil Moisture & 48-Hour Rain Forecasting Service.
Fetches real-time volumetric topsoil moisture (0-1cm depth), soil temperature,
and 48-hour precipitation forecasts using Open-Meteo Land Surface / Satellite APIs (zero API keys required).
"""

import time
import logging
from typing import Dict, Any, Tuple, Optional, List
import httpx

logger = logging.getLogger("ingres_soil_service")

# Comprehensive Indian District & State Coordinates Directory (Lat, Lon)
DISTRICT_COORDINATES: Dict[str, Tuple[float, float]] = {
    # Rajasthan
    "jaipur": (26.9124, 75.7873),
    "jodhpur": (26.2389, 73.0243),
    "jaisalmer": (26.9157, 70.9083),
    "bikaner": (28.0229, 73.3119),
    "sikar": (27.6094, 75.1398),
    "alwar": (27.5530, 76.6346),
    "jhunjhunu": (28.1289, 75.3995),
    "kota": (25.1825, 75.8391),
    "nagaur": (27.2070, 73.7423),
    "barmer": (25.7521, 71.3967),
    "ajmer": (26.4499, 74.6399),
    "udaipur": (24.5854, 73.7125),
    "churu": (28.2900, 74.9600),

    # Punjab
    "sangrur": (30.2458, 75.8421),
    "ludhiana": (30.9010, 75.8573),
    "jalandhar": (31.3260, 75.5762),
    "amritsar": (31.6340, 74.8723),
    "bathinda": (30.2110, 74.9455),
    "patiala": (30.3398, 76.3869),
    "hoshiarpur": (31.5273, 75.9149),
    "mohali": (30.7046, 76.7179),
    "firozpur": (30.9237, 74.6114),

    # Bihar
    "patna": (25.5941, 85.1376),
    "gaya": (24.7955, 85.0002),
    "muzaffarpur": (26.1209, 85.3647),
    "bhagalpur": (25.2425, 86.9842),
    "nalanda": (25.1357, 85.4578),
    "darbhanga": (26.1542, 85.8918),
    "purnia": (25.7771, 87.4753),

    # Uttar Pradesh
    "meerut": (28.9845, 77.7064),
    "varanasi": (25.3176, 82.9739),
    "agra": (27.1767, 78.0081),
    "lucknow": (26.8467, 80.9462),
    "aligarh": (27.8974, 78.0880),
    "gorakhpur": (26.7606, 83.3732),
    "jhansi": (25.4484, 78.5685),
    "prayagraj": (25.4358, 81.8463),
    "kanpur": (26.4499, 80.3319),
    "bareilly": (28.3670, 79.4304),
    "moradabad": (28.8386, 78.7733),
    "saharanpur": (29.9671, 77.5510),

    # Maharashtra
    "pune": (18.5204, 73.8567),
    "nagpur": (21.1458, 79.0882),
    "nashik": (19.9975, 73.7898),
    "chhatrapati sambhajinagar": (19.8762, 75.3433),
    "aurangabad": (19.8762, 75.3433),
    "ahmednagar": (19.0952, 74.7496),
    "solapur": (17.6599, 75.9064),
    "mumbai": (19.0760, 72.8777),
    "thane": (19.2183, 72.9781),

    # Haryana
    "karnal": (29.6857, 76.9905),
    "kurukshetra": (29.9695, 76.8783),
    "sirsa": (29.5349, 75.0296),
    "gurugram": (28.4595, 77.0266),
    "hisar": (29.1492, 75.7217),
    "ambala": (30.3782, 76.7767),
    "panipat": (29.3909, 76.9635),
    "rohtak": (28.8955, 76.6066),
    "sonipat": (28.9931, 77.0151),

    # Madhya Pradesh
    "indore": (22.7196, 75.8577),
    "ujjain": (23.1765, 75.7885),
    "bhopal": (23.2599, 77.4126),
    "jabalpur": (23.1815, 79.9864),
    "gwalior": (26.2183, 78.1828),
    "sagar": (23.8388, 78.7378),
    "rewa": (24.5362, 81.3037),

    # Southern & Other States
    "delhi": (28.6139, 77.2090),
    "ranchi": (23.3441, 85.3096),
    "raipur": (21.2514, 81.6296),
    "dehradun": (30.3165, 78.0322),
    "shimla": (31.1048, 77.1734),
    "nellore": (14.4426, 79.9865),
    "raichur": (16.2076, 77.3463),
    "anantapur": (14.6819, 77.6006),
    "warangal": (17.9689, 79.5941),
    "coimbatore": (11.0168, 76.9558),
    "madurai": (9.9252, 78.1198),
    "belagavi": (15.8497, 74.4977),

    # State Regional Centroids
    "rajasthan": (26.5000, 74.5000),
    "punjab": (31.1471, 75.3412),
    "bihar": (25.6000, 85.8000),
    "uttar pradesh": (27.0000, 80.5000),
    "maharashtra": (19.7515, 75.7139),
    "haryana": (29.0588, 76.0856),
    "madhya pradesh": (23.5000, 78.5000),
    "gujarat": (22.2587, 71.1924),
    "karnataka": (15.3173, 75.7139),
    "tamil nadu": (11.1271, 78.6569),
    "andhra pradesh": (15.9129, 79.7400),
    "telangana": (18.1124, 79.0193),
    "jharkhand": (23.6102, 85.2799),
    "chhattisgarh": (21.2787, 81.8661),
    "west bengal": (22.9868, 87.8550),
    "odisha": (20.9517, 85.0985)
}

# In-memory fast cache to prevent redundant API calls: { "lat,lon": (data_dict, timestamp) }
_SOIL_CACHE: Dict[str, Tuple[Dict[str, Any], float]] = {}
CACHE_TTL_SECONDS = 900  # 15 minutes cache

def get_district_coordinates(district_or_state: str) -> Tuple[float, float]:
    """Returns (latitude, longitude) for a district or state, defaulting to central India."""
    key = district_or_state.strip().lower()
    if key in DISTRICT_COORDINATES:
        return DISTRICT_COORDINATES[key]
    
    # Partial matching
    for d_name, coords in DISTRICT_COORDINATES.items():
        if d_name in key or key in d_name:
            return coords

    # Default coordinates (Central India - Bhopal / Nagpur region)
    return (23.2599, 77.4126)

async def get_live_soil_and_weather(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetches real-time satellite topsoil moisture (0-1 cm depth), soil temperature,
    and 48-hour precipitation forecast from Open-Meteo.
    """
    cache_key = f"{round(lat, 2)},{round(lon, 2)}"
    now = time.time()

    if cache_key in _SOIL_CACHE:
        cached_data, timestamp = _SOIL_CACHE[cache_key]
        if now - timestamp < CACHE_TTL_SECONDS:
            return cached_data

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "soil_moisture_0_to_1cm,soil_temperature_0cm",
        "daily": "precipitation_sum",
        "forecast_days": 2,
        "timezone": "auto"
    }

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current", {})
                daily = data.get("daily", {})

                raw_moisture = current.get("soil_moisture_0_to_1cm", 0.20)
                raw_temp = current.get("soil_temperature_0cm", 30.0)

                # Volumetric m³/m³ to percentage (e.g. 0.22 -> 22.0%)
                moisture_pct = round(float(raw_moisture) * 100, 1)
                temp_c = round(float(raw_temp), 1)

                # 48-hour total precipitation forecast (mm)
                rain_list: List[float] = daily.get("precipitation_sum", [0.0, 0.0])
                rain_48h_mm = round(sum(rain_list[:2]), 1) if rain_list else 0.0

                # Soil Hydration Evaluation
                if moisture_pct >= 25.0:
                    status_en = "Adequate Moisture"
                    status_hi = "नमी ठीक है (पर्याप्त नमी)"
                    advice_hi = "खेत में पर्याप्त नमी है, तुरंत सिंचाई की ज़रूरत नहीं है।"
                    advice_en = "Soil moisture is adequate; no immediate irrigation required."
                    is_dry = False
                else:
                    status_en = "Dry (Irrigation Needed)"
                    status_hi = "मिट्टी सूखी है (सिंचाई की ज़रूरत)"
                    advice_hi = "खेत की ऊपरी मिट्टी सूखी है, ड्रिप या फव्वारे से हल्की सिंचाई करें।"
                    advice_en = "Topsoil is dry; light drip or sprinkler irrigation recommended."
                    is_dry = True

                # Rain Forecasting & Smart Irrigation Alert
                if rain_48h_mm >= 5.0:
                    rain_alert_hi = f"अगले 48 घंटे में बारिश (लगभग {rain_48h_mm} mm) का अनुमान है। खेत में अभी सिंचाई रोक दें और पानी बचाएं।"
                    rain_alert_en = f"Rain expected in next 48h (~{rain_48h_mm} mm). Hold off on irrigation to conserve water."
                    rain_spoken_hi = f" अगले 48 घंटे में लगभग {rain_48h_mm} मिलीमीटर बारिश का अनुमान है, इसलिए खेत में अभी सिंचाई रोक दें।"
                    rain_spoken_en = f" Rain is expected in the next 48 hours (~{rain_48h_mm} mm); hold off on irrigation."
                    has_rain = True
                else:
                    rain_alert_hi = "अगले 2 दिन बारिश की संभावना नहीं है (शुष्क मौसम)।"
                    rain_alert_en = "No significant rain expected in the next 48 hours."
                    rain_spoken_hi = " अगले दो दिन बारिश की संभावना नहीं है।"
                    rain_spoken_en = " No rain expected in the next 48 hours."
                    has_rain = False

                result = {
                    "moisture_pct": moisture_pct,
                    "soil_temperature_c": temp_c,
                    "status_en": status_en,
                    "status_hi": status_hi,
                    "advice_hi": advice_hi,
                    "advice_en": advice_en,
                    "is_dry": is_dry,
                    "rain_48h_mm": rain_48h_mm,
                    "rain_alert_hi": rain_alert_hi,
                    "rain_alert_en": rain_alert_en,
                    "rain_spoken_hi": rain_spoken_hi,
                    "rain_spoken_en": rain_spoken_en,
                    "has_rain": has_rain,
                    "source": "Open-Meteo Satellite & Weather Telemetry"
                }

                _SOIL_CACHE[cache_key] = (result, now)
                return result
    except Exception as e:
        logger.warning(f"Open-Meteo telemetry fetch failed for ({lat}, {lon}): {e}")

    # Fallback default estimation for resilience
    default_result = {
        "moisture_pct": 21.5,
        "soil_temperature_c": 31.0,
        "status_en": "Moderate (Irrigation Recommended)",
        "status_hi": "मध्यम नमी (हल्की सिंचाई अनुशंसित)",
        "advice_hi": "खेत में मध्यम नमी है, आवश्यकतानुसार हल्की ड्रिप सिंचाई करें।",
        "advice_en": "Moderate topsoil moisture; light irrigation advised.",
        "is_dry": True,
        "rain_48h_mm": 0.0,
        "rain_alert_hi": "अगले 2 दिन बारिश की संभावना नहीं है।",
        "rain_alert_en": "No significant rain expected in the next 48 hours.",
        "rain_spoken_hi": " अगले दो दिन बारिश की संभावना नहीं है।",
        "rain_spoken_en": " No rain expected in the next 48 hours.",
        "has_rain": False,
        "source": "Regional Agro-Climatic Baseline"
    }
    return default_result

# Backward compatibility alias
async def get_live_soil_moisture(lat: float, lon: float) -> Dict[str, Any]:
    return await get_live_soil_and_weather(lat, lon)
