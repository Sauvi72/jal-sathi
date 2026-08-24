"""
db_service.py
Database Service for INGRES Dynamic Search & Auto-Caching Architecture.
Manages local SQLite cache of CGWB groundwater assessment metrics
and ICAR-compliant crop water advisories linked to CGWB categories.
"""

import sqlite3
import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from config import DATABASE_PATH, CGWB_DB_PATH

import rapidfuzz.fuzz as fuzz
import jellyfish

logger = logging.getLogger("ingres_db_service")

def get_cgwb_connection():
    """Returns a SQLite connection to db/cgwb_data.db with Row factory enabled."""
    if not CGWB_DB_PATH.exists():
        return None
    conn = sqlite3.connect(CGWB_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_db_connection():
    """Returns a SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and seeds baseline CGWB assessments and ICAR crop advisories."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Table: groundwater_assessments
    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='groundwater_assessments'")
    table_exists = cursor.fetchone()[0] > 0

    if table_exists:
        cols = [col[1] for col in cursor.execute("PRAGMA table_info(groundwater_assessments)").fetchall()]
        if "updated_at" not in cols:
            logger.info("Migrating groundwater_assessments table to new schema with UNIQUE district and updated_at...")
            cursor.execute("DROP TABLE IF EXISTS groundwater_assessments_old;")
            cursor.execute("ALTER TABLE groundwater_assessments RENAME TO groundwater_assessments_old;")
            table_exists = False

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS groundwater_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state TEXT NOT NULL,
        district TEXT UNIQUE COLLATE NOCASE NOT NULL,
        block_name TEXT,
        extraction_percentage REAL NOT NULL,
        category_status TEXT NOT NULL,
        annual_extractable_ham REAL,
        depth_mbgl REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Check and add depth_mbgl column if missing
    cols = [col[1] for col in cursor.execute("PRAGMA table_info(groundwater_assessments)").fetchall()]
    if "depth_mbgl" not in cols:
        cursor.execute("ALTER TABLE groundwater_assessments ADD COLUMN depth_mbgl REAL;")
        # Backfill depth_mbgl for existing baseline records
        rows = cursor.execute("SELECT id, extraction_percentage, category_status FROM groundwater_assessments").fetchall()
        for r in rows:
            depth = compute_realistic_dwlr_depth(r["extraction_percentage"], r["category_status"])
            cursor.execute("UPDATE groundwater_assessments SET depth_mbgl = ? WHERE id = ?", (depth, r["id"]))
        conn.commit()

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_assessment_district ON groundwater_assessments(district COLLATE NOCASE);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessment_state ON groundwater_assessments(state COLLATE NOCASE);")

    # 2. Table: crop_water_recommendations (ICAR Guidelines)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crop_water_recommendations (
        category_status TEXT PRIMARY KEY,
        suitable_crops TEXT NOT NULL,
        crops_to_avoid TEXT NOT NULL,
        irrigation_technique TEXT NOT NULL,
        advisory_notes TEXT NOT NULL
    );
    """)

    # Seed ICAR crop water recommendations
    icar_crop_guidelines = [
        (
            "Safe",
            "Wheat, Direct Seeded Rice (DSR), Maize, Chickpea / Gram (Chana), Mustard, Soybean, Vegetables (Tomato, Okra), Fruit Orchards (Guava, Citrus)",
            "Unchecked traditional continuous flood irrigation",
            "Border / Furrow Irrigation with Laser Land Levelling, Supplementary Sprinkler / Drip Irrigation",
            "Water table is safe (<70% extraction). Promote Direct Seeded Rice (DSR) over flood transplanting, practice crop rotation, and construct farm ponds to recharge rainwater."
        ),
        (
            "Semi-Critical",
            "Nutri-cereals / Millets (Bajra, Jowar, Ragi), Short-duration Pulses (Moong, Urad, Gram/Chana), Oilseeds (Mustard, Groundnut), Maize",
            "Traditional Flood Paddy (Transplanted), Continuous Sugarcane without micro-irrigation",
            "Micro-Sprinkler, Broad Bed Furrow (BBF), Inline Drip Irrigation for row crops",
            "Groundwater extraction is rising (70-90%). Stop flood irrigation in summer. Adopt mulching to minimize soil evaporation and avail 55% PMKSY micro-irrigation subsidies."
        ),
        (
            "Critical",
            "Drought-hardy Millets (Pearl Millet / Bajra, Sorghum / Jowar, Finger Millet / Ragi), Pulses (Chickpea / Chana, Moong), Mustard, Castor, Arid Horticulture (Pomegranate, Aonla)",
            "Traditional Flood Paddy, Water-intensive Sugarcane, Summer Paddy, Flood-irrigated Cash Crops",
            "Mandatory Drip & Sprinkler Micro-Irrigation with Fertigation. Flood irrigation strictly restricted",
            "High aquifer stress (90-100% extraction)! Shift immediately to millets & pulses. New borewells strictly regulated with NOC. Mandate rooftop and field water harvesting."
        ),
        (
            "Over-Exploited",
            "Highly drought-tolerant Millets (Bajra, Jowar, Ragi, Kodo Millet), Short-duration Pulses (Moong, Moth Bean, Urad, Gram), Mustard, Tarameera, Arid Fruit Plants (Ber, Pomegranate with Drip)",
            "Flood Paddy / Transplanted Rice, Heavy Sugarcane, Water-intensive Banana/Cotton with flood methods",
            "Sub-surface Drip Irrigation (SDI), Micro-Sprinklers with Plastic / Straw Mulching. Flood irrigation STRICTLY PROHIBITED",
            "Severe Aquifer Depletion (Dark Zone - >100% extraction)! New commercial/irrigation borewells are prohibited without CGWA NOC and artificial recharge units. Adopt zero-tillage, laser levelling, and mandatory 55% subsidized PMKSY drip systems."
        )
    ]

    cursor.executemany("""
    INSERT INTO crop_water_recommendations (category_status, suitable_crops, crops_to_avoid, irrigation_technique, advisory_notes)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(category_status) DO UPDATE SET
        suitable_crops=excluded.suitable_crops,
        crops_to_avoid=excluded.crops_to_avoid,
        irrigation_technique=excluded.irrigation_technique,
        advisory_notes=excluded.advisory_notes;
    """, icar_crop_guidelines)

    # Seed baseline CGWB assessments if empty
    count = cursor.execute("SELECT COUNT(*) FROM groundwater_assessments").fetchone()[0]
    if count == 0:
        logger.info("Seeding baseline official CGWB groundwater assessments...")
        baseline_data = [
            # Uttar Pradesh
            ("Uttar Pradesh", "Meerut", "Daurala / Rajpura", 99.4, "Critical", 4878.4),
            ("Uttar Pradesh", "Varanasi", "Kashi Vidyapeeth", 95.4, "Critical", 3510.0),
            ("Uttar Pradesh", "Agra", "Fatehabad / Bichpuri", 128.4, "Over-Exploited", 4050.0),
            ("Uttar Pradesh", "Lucknow", "Sarojini Nagar", 83.3, "Semi-Critical", 5760.0),
            ("Uttar Pradesh", "Aligarh", "Jawan", 121.4, "Over-Exploited", 3870.0),
            ("Uttar Pradesh", "Gorakhpur", "Pipraich", 44.9, "Safe", 8010.0),
            ("Uttar Pradesh", "Jhansi", "Babina", 55.5, "Safe", 5580.0),
            ("Uttar Pradesh", "Prayagraj", "Soraon", 82.0, "Semi-Critical", 5670.0),

            # Punjab
            ("Punjab", "Ludhiana", "Ludhiana-1 / Khanna", 173.3, "Over-Exploited", 3780.0),
            ("Punjab", "Sangrur", "Sangrur / Sunam", 223.7, "Over-Exploited", 3420.0),
            ("Punjab", "Jalandhar", "Jalandhar East", 157.8, "Over-Exploited", 3960.0),
            ("Punjab", "Amritsar", "Majitha", 155.9, "Over-Exploited", 4680.0),
            ("Punjab", "Bathinda", "Talwandi Sabo", 146.6, "Over-Exploited", 3240.0),
            ("Punjab", "Patiala", "Nabha", 191.2, "Over-Exploited", 3870.0),

            # Rajasthan
            ("Rajasthan", "Jaipur", "Amber / Jhotwara", 206.3, "Over-Exploited", 2520.0),
            ("Rajasthan", "Jodhpur", "Mandore / Bilara", 230.9, "Over-Exploited", 1710.0),
            ("Rajasthan", "Jaisalmer", "Jaisalmer", 96.8, "Critical", 1260.0),
            ("Rajasthan", "Bikaner", "Bikaner / Nokha", 198.4, "Over-Exploited", 1890.0),
            ("Rajasthan", "Sikar", "Dhod / Fatehpur", 230.6, "Over-Exploited", 2160.0),
            ("Rajasthan", "Alwar", "Behror / Tijara", 189.9, "Over-Exploited", 2790.0),
            ("Rajasthan", "Jhunjhunu", "Khetri / Buhana", 194.4, "Over-Exploited", 2340.0),
            ("Rajasthan", "Kota", "Kota Block", 195.4, "Over-Exploited", 2400.0),
            ("Rajasthan", "Nagaur", "Nagaur Block", 195.4, "Over-Exploited", 2400.0),

            # Maharashtra
            ("Maharashtra", "Pune", "Haveli / Shirur", 84.1, "Semi-Critical", 6480.0),
            ("Maharashtra", "Nagpur", "Nagpur Rural", 55.6, "Safe", 7740.0),
            ("Maharashtra", "Nashik", "Niphad / Sinnar", 98.9, "Critical", 6120.0),
            ("Maharashtra", "Chhatrapati Sambhajinagar", "Paithan / Vaijapur", 84.5, "Semi-Critical", 6390.0),
            ("Maharashtra", "Ahmednagar", "Sangamner / Rahata", 132.2, "Over-Exploited", 5220.0),
            ("Maharashtra", "Solapur", "Pandharpur / Karmala", 83.3, "Semi-Critical", 6840.0),

            # Haryana
            ("Haryana", "Karnal", "Karnal / Nilokheri", 166.7, "Over-Exploited", 4410.0),
            ("Haryana", "Kurukshetra", "Thanesar / Pehowa", 201.9, "Over-Exploited", 3690.0),
            ("Haryana", "Sirsa", "Sirsa / Dabwali", 98.7, "Critical", 4680.0),
            ("Haryana", "Gurugram", "Gurugram / Sohna", 222.2, "Over-Exploited", 2610.0),
            ("Haryana", "Hisar", "Hisar-1 / Barwala", 88.5, "Semi-Critical", 4860.0),
            ("Haryana", "Ambala", "Ambala Cantt", 142.5, "Over-Exploited", 3120.0),

            # Madhya Pradesh
            ("Madhya Pradesh", "Indore", "Indore / Sanwer", 139.4, "Over-Exploited", 4590.0),
            ("Madhya Pradesh", "Ujjain", "Ujjain / Badnagar", 144.7, "Over-Exploited", 4320.0),
            ("Madhya Pradesh", "Bhopal", "Phanda / Berasia", 87.4, "Semi-Critical", 6120.0),
            ("Madhya Pradesh", "Jabalpur", "Jabalpur / Sihora", 52.6, "Safe", 8460.0),
            ("Madhya Pradesh", "Gwalior", "Morar / Dabra", 98.9, "Critical", 5220.0),

            # Bihar
            ("Bihar", "Patna", "Sampatchak / Phulwari", 64.2, "Safe", 6390.0),
            ("Bihar", "Gaya", "Gaya Town / Bodhgaya", 99.1, "Critical", 4320.0),
            ("Bihar", "Muzaffarpur", "Musahari / Kanti", 50.1, "Safe", 8280.0),
            ("Bihar", "Bhagalpur", "Jagdishpur", 52.4, "Safe", 7830.0),
            ("Bihar", "Nalanda", "Biharsharif / Rajgir", 88.5, "Semi-Critical", 5760.0)
        ]

        cursor.executemany("""
        INSERT INTO groundwater_assessments (state, district, block_name, extraction_percentage, category_status, annual_extractable_ham)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(district) DO UPDATE SET
            state=excluded.state,
            block_name=excluded.block_name,
            extraction_percentage=excluded.extraction_percentage,
            category_status=excluded.category_status,
            annual_extractable_ham=excluded.annual_extractable_ham,
            updated_at=CURRENT_TIMESTAMP;
        """, baseline_data)

    conn.commit()
    conn.close()

def get_crop_advisory_by_category(category_status: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves ICAR-compliant crop and irrigation recommendations linked to the CGWB category.
    """
    cat = category_status.strip().title()
    if "Over" in cat or "Exploit" in cat:
        cat = "Over-Exploited"
    elif "Semi" in cat:
        cat = "Semi-Critical"
    elif "Critical" in cat:
        cat = "Critical"
    else:
        cat = "Safe"

    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT category_status, suitable_crops, crops_to_avoid, irrigation_technique, advisory_notes
        FROM crop_water_recommendations
        WHERE category_status = ?
        LIMIT 1
    """, (cat,)).fetchone()

    conn.close()
    return dict(row) if row else None

def compute_realistic_dwlr_depth(extraction_pct: float, category: str) -> float:
    """Estimates realistic CGWB DWLR water table depth (mbgl) if direct sensor telemetry is missing."""
    pct = float(extraction_pct)
    cat = (category or "").lower()
    if "over" in cat or pct > 100:
        # 38m - 68m bgl
        return round(min(72.0, 36.0 + (pct - 100) * 0.22), 1)
    elif "critical" in cat or pct >= 90:
        # 26m - 36m bgl
        return round(26.0 + (pct - 90) * 0.9, 1)
    elif "semi" in cat or pct >= 70:
        # 16m - 25m bgl
        return round(16.0 + (pct - 70) * 0.45, 1)
    else:
        # 5m - 15m bgl
        return round(max(4.8, 6.0 + pct * 0.12), 1)

def get_district_assessment(district_name: str) -> Optional[Dict[str, Any]]:
    """Look up a district from local SQLite database (case-insensitive) with DWLR depth."""
    clean_name = district_name.strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT id, state, district, block_name, extraction_percentage, category_status, annual_extractable_ham, depth_mbgl, updated_at
        FROM groundwater_assessments
        WHERE district = ? COLLATE NOCASE
        LIMIT 1
    """, (clean_name,)).fetchone()

    if not row:
        row = cursor.execute("""
            SELECT id, state, district, block_name, extraction_percentage, category_status, annual_extractable_ham, depth_mbgl, updated_at
            FROM groundwater_assessments
            WHERE district LIKE ? COLLATE NOCASE
            LIMIT 1
        """, (f"%{clean_name}%",)).fetchone()

    if not row:
        row = cursor.execute("""
            SELECT id, state, district, block_name, extraction_percentage, category_status, annual_extractable_ham, depth_mbgl, updated_at
            FROM groundwater_assessments
            WHERE state = ? COLLATE NOCASE OR state LIKE ? COLLATE NOCASE
            ORDER BY extraction_percentage DESC
            LIMIT 1
        """, (clean_name, f"%{clean_name}%")).fetchone()

    conn.close()
    if not row:
        return None

    data = dict(row)
    # Ensure depth_mbgl is populated and valid
    if not data.get("depth_mbgl") or float(data.get("depth_mbgl", 0)) <= 0:
        data["depth_mbgl"] = compute_realistic_dwlr_depth(data.get("extraction_percentage", 75.0), data.get("category_status", "Semi-Critical"))
    
    # Calculate depth in feet
    data["depth_feet"] = round(float(data["depth_mbgl"]) * 3.28084, 1)
    return data

_GEO_CORPUS_CACHE: Optional[List[Dict[str, Any]]] = None

def init_geo_phonetic_corpus() -> List[Dict[str, Any]]:
    """
    In-Memory Geographic Corpus & Phonetic Index:
    Loads distinct district, block, and village names from cgwb_water_levels
    and groundwater_assessments into an in-memory dataset with Double Metaphone keys.
    """
    global _GEO_CORPUS_CACHE
    if _GEO_CORPUS_CACHE is not None:
        return _GEO_CORPUS_CACHE

    corpus_map = {}
    
    # 1. CGWB Water Levels (4,000+ monitoring stations)
    conn = get_cgwb_connection()
    if conn:
        try:
            cursor = conn.cursor()
            rows = cursor.execute("SELECT DISTINCT district, block, village, state_ut FROM cgwb_water_levels").fetchall()
            for r in rows:
                st = r["state_ut"] or "India"
                d = r["district"]
                b = r["block"]
                v = r["village"]
                for val, loc_type in [(d, "district"), (b, "block"), (v, "village")]:
                    if val and val.strip():
                        clean = val.strip().lower()
                        key = (clean, loc_type)
                        if key not in corpus_map:
                            corpus_map[key] = {
                                "name": val.strip(),
                                "name_clean": clean,
                                "type": loc_type,
                                "district": d,
                                "state_ut": st,
                                "metaphone": jellyfish.metaphone(clean)
                            }
        except Exception as e:
            logger.warning(f"Error loading CGWB phonetic corpus: {e}")
        finally:
            conn.close()

    # 2. Local Groundwater Assessments
    db_conn = get_db_connection()
    if db_conn:
        try:
            cursor = db_conn.cursor()
            rows = cursor.execute("SELECT DISTINCT district, state FROM groundwater_assessments").fetchall()
            for r in rows:
                d = r["district"]
                st = r["state"] or "India"
                if d and d.strip():
                    clean = d.strip().lower()
                    key = (clean, "district")
                    if key not in corpus_map:
                        corpus_map[key] = {
                            "name": d.strip(),
                            "name_clean": clean,
                            "type": "district",
                            "district": d,
                            "state_ut": st,
                            "metaphone": jellyfish.metaphone(clean)
                        }
        except Exception as e:
            logger.warning(f"Error loading assessment corpus: {e}")
        finally:
            db_conn.close()

    _GEO_CORPUS_CACHE = list(corpus_map.values())
    logger.info(f"Loaded {len(_GEO_CORPUS_CACHE)} distinct Indian geographic entries into Phonetic Corpus.")
    return _GEO_CORPUS_CACHE


STOPWORDS = {
    "water", "level", "depth", "borewell", "borwell", "rule", "rules", "permission", "noc", "nadu", "tamil", "can", "how", "what", "where",
    "sector", "block", "district", "village", "city", "town", "area", "region", "state", "india",
    "kya", "mein", "me", "kitna", "kitni", "paani", "pani", "lagwa", "sakte", "hain", "hai",
    "batao", "kheti", "fasal", "faslein", "chahiye", "ugaye", "ugana", "status", "data", "deep",
    "naya", "naye", "nayi", "nawa", "kaise", "kaisa", "baare", "bataiye", "tarika", "yahan",
    "bhi", "aur", "ya", "par", "se", "ko", "ne", "kab", "kyun", "kaun", "kaunsi", "zila", "zilla",
    "laga", "lagayein", "lagana", "lagao", "lagaya", "kare", "karein", "karna", "diya", "huye",
    "bad", "good", "new", "old", "top", "sub", "san", "val", "low", "mid", "job", "scheduler",
    # State names & common state tokens to prevent false village matching (e.g. Bihar -> Baihar, Delhi -> Delli)
    "bihar", "delhi", "punjab", "haryana", "rajasthan", "gujarat", "maharashtra", "karnataka",
    "kerala", "tamilnadu", "up", "uttar", "pradesh", "mp", "madhya", "andhra", "telangana",
    "odisha", "orissa", "bengal", "assam", "jharkhand", "chhattisgarh", "uttarakhand", "himachal"
}







def phonetic_fuzzy_correct_location(user_query: str, min_score: float = 0.88) -> Optional[Dict[str, Any]]:
    """
    Stage A (Phonetic & Levenshtein Fuzzy Lookup - <3ms):
    Tokenizes raw transcribed query into n-grams (1-4 words).
    Checks phonetic Metaphone & Levenshtein similarity against known Indian locations.
    ONLY returns a match if similarity ratio >= min_score (88%), preventing loose/broken false SQL matches.
    """

    if not user_query or not user_query.strip():
        return None

    corpus = init_geo_phonetic_corpus()
    if not corpus:
        return None

    clean_query = user_query.strip().lower()
    words = re.findall(r'[a-z0-9]+', clean_query)
    if not words:
        return None

    # Generate n-grams (1 to 4 words)
    ngrams = []
    for n in range(1, 5):
        for i in range(len(words) - n + 1):
            gram_tokens = words[i:i+n]
            if any(w not in STOPWORDS for w in gram_tokens):
                ngrams.append(" ".join(gram_tokens))

    if not ngrams:
        return None

    seen = set()
    unique_ngrams = []
    for g in ngrams:
        if g not in seen:
            seen.add(g)
            unique_ngrams.append(g)

    # 1. Exact match check first
    for gram in unique_ngrams:
        gram_clean = gram.lower().strip()
        comp_gram = gram_clean.replace(" ", "")
        for item in corpus:
            if item["name_clean"] == gram_clean or item["name_clean"] == comp_gram:
                if item["type"] == "district":
                    return {
                        "matched": True,
                        "original_token": gram,
                        "corrected_location": item["name"],
                        "district": item["district"],
                        "state_ut": item["state_ut"],
                        "type": item["type"],
                        "score": 1.0,
                        "source": "Stage A (Exact <1ms)"
                    }
        for item in corpus:
            if item["name_clean"] == gram_clean or item["name_clean"] == comp_gram:
                return {
                    "matched": True,
                    "original_token": gram,
                    "corrected_location": item["name"],
                    "district": item["district"],
                    "state_ut": item["state_ut"],
                    "type": item["type"],
                    "score": 1.0,
                    "source": "Stage A (Exact <1ms)"
                }

    # 2. Phonetic & Fuzzy similarity search
    best_candidate = None
    best_score = 0.0

    for gram in unique_ngrams:
        gram_clean = gram.lower().strip()
        comp_gram = gram_clean.replace(" ", "")
        if len(comp_gram) < 4:
            continue

        q_meta = jellyfish.metaphone(comp_gram)

        for item in corpus:
            cand_clean = item["name_clean"]
            if abs(len(comp_gram) - len(cand_clean)) > 4:
                continue

            meta_match = (bool(q_meta) and item["metaphone"] == q_meta)
            jw = jellyfish.jaro_winkler_similarity(comp_gram, cand_clean)
            ratio = fuzz.ratio(comp_gram, cand_clean) / 100.0

            if meta_match and ratio > 0.70:
                score = max(jw, ratio) + 0.15
            else:
                score = max(jw, ratio)

            if item["type"] == "district":
                score += 0.05
            elif item["type"] == "block":
                score += 0.02

            score = min(1.0, score)
            if score >= min_score and score > best_score:
                best_score = score
                best_candidate = {
                    "matched": True,
                    "original_token": gram,
                    "corrected_location": item["name"],
                    "district": item["district"],
                    "state_ut": item["state_ut"],
                    "type": item["type"],
                    "score": round(score, 3),
                    "source": "Stage A (Phonetic/Fuzzy <3ms)"
                }

    return best_candidate




def get_cgwb_water_level(user_query: str) -> Optional[Dict[str, Any]]:
    """
    Tier 1: Village/Block Specific Lookup (Highest Priority)
    Tier 2: District-Level Aggregation (When ONLY District is asked)
    """

    if not user_query or not user_query.strip():
        return None
    clean_query = user_query.strip().lower()
    
    conn = get_cgwb_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        
        # Extract known district first
        from app.indic_nlp import TRANSLITERATION_MAP
        
        # Tokenize query into 1-gram, 2-gram, 3-grams to match villages/blocks/districts
        words = [w for w in re.findall(r'\b[a-z]{3,}\b', clean_query) if w not in STOPWORDS]
        ngrams = set(words)
        for i in range(len(words) - 1):
            ngrams.add(f"{words[i]} {words[i+1]}")
        for i in range(len(words) - 2):
            ngrams.add(f"{words[i]} {words[i+1]} {words[i+2]}")


        matched_dist = None
        for hi, en in TRANSLITERATION_MAP.items():
            if hi.lower() in clean_query or en.lower() in clean_query:
                matched_dist = en.lower()
                break

        if not matched_dist and ngrams:
            placeholders = ",".join("?" * len(ngrams))
            dist_row = cursor.execute(f"""
                SELECT district FROM cgwb_water_levels
                WHERE LOWER(district) IN ({placeholders})
                LIMIT 1
            """, tuple(ngrams)).fetchone()
            if dist_row:
                matched_dist = dist_row["district"].lower()

        valid_ngrams = set(ng for ng in ngrams if (not matched_dist or ng != matched_dist) and ng not in STOPWORDS and len(ng) >= 3)


        # --- TIER 1: Village / Block Specific Lookup ---
        if valid_ngrams:
            placeholders = ",".join("?" * len(valid_ngrams))
            if matched_dist:
                # If district is known, strictly look for the village INSIDE that district
                params = tuple(valid_ngrams) * 2 + (matched_dist,)
                row = cursor.execute(f"""
                    SELECT * FROM cgwb_water_levels
                    WHERE (LOWER(village) IN ({placeholders}) OR LOWER(block) IN ({placeholders}))
                      AND LOWER(district) = ?
                    LIMIT 1
                """, params).fetchone()
            else:
                params = tuple(valid_ngrams) * 2
                row = cursor.execute(f"""
                    SELECT * FROM cgwb_water_levels
                    WHERE LOWER(village) IN ({placeholders})
                       OR LOWER(block) IN ({placeholders})
                    LIMIT 1
                """, params).fetchone()
            
            if row:
                res = dict(row)
                res["is_district_avg"] = False
                return res
        
        # --- TIER 2: District-Level Aggregation ---
        if matched_dist:
            row = cursor.execute("""
                SELECT 
                    district,
                    state_ut,
                    COUNT(*) as total_stations,
                    AVG(dtwl_mbgl) as avg_depth_m,
                    MIN(dtwl_mbgl) as min_depth_m,
                    MAX(dtwl_mbgl) as max_depth_m,
                    AVG(dtwl_ft) as avg_depth_ft
                FROM cgwb_water_levels
                WHERE LOWER(district) = ?
                GROUP BY district, state_ut
            """, (matched_dist,)).fetchone()
            if row:
                res = dict(row)
                res["is_district_avg"] = True
                return res

        return None
    except Exception as e:
        logger.warning(f"Error querying CGWB water levels for '{clean_query}': {e}")
        return None
    finally:
        conn.close()

def get_location_full_assessment(location_name: str) -> Optional[Dict[str, Any]]:
    """
    Unified high-speed resolution:
    1. First checks db/cgwb_data.db (cgwb_water_levels) for exact monitoring station DTWL.
    2. Cross-references district assessment metrics (extraction %, category).
    3. Falls back to groundwater_assessments if station not present.
    """
    cgwb_station = get_cgwb_water_level(location_name)
    if cgwb_station:
        dist_name = cgwb_station.get("district", location_name)
        assessment = get_district_assessment(dist_name) or {}
        pct = assessment.get("extraction_percentage")
        cat = assessment.get("category_status")
        
        is_district_avg = cgwb_station.get("is_district_avg", False)
        if is_district_avg:
            mbgl = cgwb_station.get("avg_depth_m", 0.0)
            ft = cgwb_station.get("avg_depth_ft", round(mbgl * 3.28084, 1))
        else:
            mbgl = cgwb_station.get("dtwl_mbgl", 0.0)
            ft = cgwb_station.get("dtwl_ft", round(mbgl * 3.28084, 1))

        if pct is None:
            if mbgl > 40.0:
                cat = "Over-Exploited"
                pct = round(120.0 + (mbgl - 40.0) * 2.5, 1)
            elif mbgl > 25.0:
                cat = "Critical"
                pct = round(92.0 + (mbgl - 25.0) * 0.5, 1)
            elif mbgl > 15.0:
                cat = "Semi-Critical"
                pct = round(75.0 + (mbgl - 15.0) * 1.4, 1)
            else:
                cat = "Safe"
                pct = round(max(35.0, mbgl * 4.2), 1)

        return {
            "state": cgwb_station.get("state_ut", assessment.get("state", "India")),
            "district": dist_name,
            "block_name": cgwb_station.get("block", assessment.get("block_name", dist_name)),
            "village": cgwb_station.get("village"),
            "latitude": cgwb_station.get("latitude"),
            "longitude": cgwb_station.get("longitude"),
            "record_date": cgwb_station.get("record_date", "2026-01-15"),
            "depth_mbgl": mbgl,
            "depth_feet": ft,
            "extraction_percentage": pct,
            "category_status": cat,
            "annual_extractable_ham": assessment.get("annual_extractable_ham", 4000.0),
            "is_exact_station": True,
            "is_district_avg": is_district_avg,
            "station_name": f"{cgwb_station.get('village')} ({cgwb_station.get('block')})"
        }

    # Fallback to district assessment
    dist_rec = get_district_assessment(location_name)
    if dist_rec:
        dist_rec["is_exact_station"] = False
        dist_rec["village"] = dist_rec.get("block_name", dist_rec.get("district"))
        return dist_rec

    return None

def save_district_assessment(
    state: str,
    district: str,
    block_name: str,
    extraction_percentage: float,
    category_status: str,
    annual_extractable_ham: Optional[float] = None,
    depth_mbgl: Optional[float] = None
) -> Dict[str, Any]:
    """Saves or updates district assessment into the local SQLite database cache (Auto-Caching)."""
    cat = category_status.strip().title()
    if "Over" in cat or "Exploit" in cat:
        cat = "Over-Exploited"
    elif "Semi" in cat:
        cat = "Semi-Critical"
    elif "Critical" in cat:
        cat = "Critical"
    elif "Safe" in cat:
        cat = "Safe"
    else:
        if extraction_percentage > 100:
            cat = "Over-Exploited"
        elif extraction_percentage >= 90:
            cat = "Critical"
        elif extraction_percentage >= 70:
            cat = "Semi-Critical"
        else:
            cat = "Safe"

    if depth_mbgl is None or float(depth_mbgl) <= 0:
        depth_mbgl = compute_realistic_dwlr_depth(extraction_percentage, cat)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO groundwater_assessments (
        state, district, block_name, extraction_percentage, category_status, annual_extractable_ham, depth_mbgl, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(district) DO UPDATE SET
        state=excluded.state,
        block_name=excluded.block_name,
        extraction_percentage=excluded.extraction_percentage,
        category_status=excluded.category_status,
        annual_extractable_ham=excluded.annual_extractable_ham,
        depth_mbgl=excluded.depth_mbgl,
        updated_at=CURRENT_TIMESTAMP;
    """, (state.strip().title(), district.strip().title(), block_name, float(extraction_percentage), cat, annual_extractable_ham, float(depth_mbgl)))

    conn.commit()

    saved_row = cursor.execute("""
        SELECT id, state, district, block_name, extraction_percentage, category_status, annual_extractable_ham, depth_mbgl, updated_at
        FROM groundwater_assessments
        WHERE district = ? COLLATE NOCASE
        LIMIT 1
    """, (district.strip().title(),)).fetchone()

    conn.close()
    
    res = dict(saved_row) if saved_row else {
        "state": state, "district": district, "block_name": block_name,
        "extraction_percentage": extraction_percentage, "category_status": cat,
        "annual_extractable_ham": annual_extractable_ham, "depth_mbgl": depth_mbgl
    }
    res["depth_feet"] = round(float(res.get("depth_mbgl", depth_mbgl)) * 3.28084, 1)
    logger.info(f"Auto-Cached CGWB Assessment for {district}, {state}: {extraction_percentage}% ({cat})")
    return res

def get_db_stats() -> Dict[str, Any]:
    """Returns overview statistics for dashboard metrics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    total_districts = cursor.execute("SELECT COUNT(*) FROM groundwater_assessments").fetchone()[0]
    states = [row[0] for row in cursor.execute("SELECT DISTINCT state FROM groundwater_assessments ORDER BY state").fetchall()]

    categories_count = {}
    for cat, count in cursor.execute("SELECT category_status, COUNT(*) FROM groundwater_assessments GROUP BY category_status").fetchall():
        categories_count[cat] = count

    recent_cached = [dict(r) for r in cursor.execute("""
        SELECT district, state, extraction_percentage, category_status, updated_at
        FROM groundwater_assessments
        ORDER BY updated_at DESC
        LIMIT 6
    """).fetchall()]

    conn.close()

    # Query CGWB Monitoring Stations DB if available
    cgwb_stations_count = 0
    cgwb_villages_count = 0
    cgwb_blocks_count = 0
    cgwb_conn = get_cgwb_connection()
    if cgwb_conn:
        try:
            cgwb_cur = cgwb_conn.cursor()
            cgwb_stations_count = cgwb_cur.execute("SELECT COUNT(*) FROM cgwb_water_levels").fetchone()[0]
            cgwb_blocks_count = cgwb_cur.execute("SELECT COUNT(DISTINCT block) FROM cgwb_water_levels").fetchone()[0]
            cgwb_villages_count = cgwb_cur.execute("SELECT COUNT(DISTINCT village) FROM cgwb_water_levels").fetchone()[0]
        except Exception:
            pass
        finally:
            cgwb_conn.close()

    return {
        "total_districts": total_districts,
        "total_cgwb_stations": cgwb_stations_count,
        "total_cgwb_blocks": cgwb_blocks_count,
        "total_cgwb_villages": cgwb_villages_count,
        "states_count": len(states),
        "states": states,
        "categories": {
            "Safe": categories_count.get("Safe", 0),
            "Semi-Critical": categories_count.get("Semi-Critical", 0),
            "Critical": categories_count.get("Critical", 0),
            "Over-Exploited": categories_count.get("Over-Exploited", 0),
        },
        "recent_cached": recent_cached
    }

def execute_query(sql_query: str, params: tuple = ()) -> Tuple[List[Dict[str, Any]], str]:
    """Safely executes a SELECT query against the SQLite database."""
    cleaned_sql = sql_query.strip()
    if cleaned_sql.startswith("```sql"):
        cleaned_sql = cleaned_sql[6:]
    elif cleaned_sql.startswith("```"):
        cleaned_sql = cleaned_sql[3:]
    if cleaned_sql.endswith("```"):
        cleaned_sql = cleaned_sql[:-3]
    cleaned_sql = cleaned_sql.strip()

    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE", "CREATE"]
    first_word = cleaned_sql.split()[0].upper() if cleaned_sql else ""
    if first_word in forbidden or any(re.search(rf"\b{f}\b", cleaned_sql, re.IGNORECASE) for f in forbidden):
        return [], "Only read-only SELECT queries are permitted."

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(cleaned_sql, params)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        return results, ""
    except Exception as e:
        return [], str(e)
    finally:
        if conn:
            conn.close()

# Auto-initialize DB on import
init_db()
