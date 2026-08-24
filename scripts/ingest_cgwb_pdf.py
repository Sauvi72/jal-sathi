#!/usr/bin/env python3
"""
scripts/ingest_cgwb_pdf.py
High-speed extraction and ingestion of official CGWB Ground Water Level Monitoring Report
(from waterlevel.pdf / January_2026.pdf) into a high-performance SQLite database (db/cgwb_data.db).

Schema:
  cgwb_water_levels (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      state_ut TEXT NOT NULL,
      district TEXT NOT NULL,
      block TEXT NOT NULL,
      village TEXT NOT NULL,
      latitude REAL NOT NULL,
      longitude REAL NOT NULL,
      record_date TEXT NOT NULL,
      dtwl_mbgl REAL NOT NULL,
      dtwl_ft REAL NOT NULL
  )
Indexes created on district, block, and village (lowercased / case-insensitive)
for sub-millisecond query performance.
"""

import os
import sys
import time
import sqlite3
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_CANDIDATES = [
    BASE_DIR / "waterlevel.pdf",
    BASE_DIR / "January_2026.pdf"
]
DB_DIR = BASE_DIR / "db"
DB_PATH = DB_DIR / "cgwb_data.db"

INDIAN_STATES_UTS = [
    "Andaman and Nicobar Islands", "Dadra and Nagar Haveli and Daman and Diu",
    "The Dadra And Nagar Haveli And Daman And Diu", "Dadra & Nagar Haveli",
    "Jammu and Kashmir", "Jammu & Kashmir", "Himachal Pradesh", "Madhya Pradesh",
    "Uttar Pradesh", "Andhra Pradesh", "Arunachal Pradesh", "West Bengal",
    "Tamil Nadu", "Chhattisgarh", "Uttarakhand", "Maharashtra", "Puducherry",
    "Lakshadweep", "Chandigarh", "Telangana", "Rajasthan", "Jharkhand",
    "Karnataka", "Meghalaya", "Nagaland", "Gujarat", "Haryana", "Manipur",
    "Mizoram", "Tripura", "Ladakh", "Sikkim", "Odisha", "Punjab", "Kerala",
    "Assam", "Bihar", "Delhi", "Goa"
]
# Sort longest first so "Uttar Pradesh" matches before "Uttar"
INDIAN_STATES_UTS.sort(key=lambda s: len(s), reverse=True)


def parse_location_parts(rest_text: str) -> Tuple[str, str, str]:
    """
    Intelligently extracts (district, block, village) from the remaining location string.
    Handles 1-token, 2-token, 3-token, and multi-word names.
    """
    clean = re.sub(r'\s+', ' ', rest_text).strip()
    if not clean:
        return ("Unknown", "Unknown", "Unknown")

    tokens = clean.split()
    n = len(tokens)

    if n == 1:
        dist = tokens[0].title()
        return (dist, dist, dist)
    elif n == 2:
        dist = tokens[0].title()
        blk = tokens[1].title()
        return (dist, blk, blk)
    elif n == 3:
        return (tokens[0].title(), tokens[1].title(), tokens[2].title())
    elif n == 4:
        # e.g., "Agra Achhnera Achchnera Rural" or "Alluri Sitharama Raju Addateegala"
        return (f"{tokens[0]} {tokens[1]}".title(), tokens[2].title(), tokens[3].title())
    elif n == 5:
        # e.g., "Alluri Sitharama Raju Addateegala Addateegala"
        return (f"{tokens[0]} {tokens[1]} {tokens[2]}".title(), tokens[3].title(), tokens[4].title())
    else:
        # Split roughly into 3 parts
        p1 = " ".join(tokens[:2]).title()
        p2 = " ".join(tokens[2:n-1]).title()
        p3 = tokens[-1].title()
        return (p1, p2 or p1, p3 or p2 or p1)


def extract_records_from_pdf(pdf_path: Path) -> List[Tuple[str, str, str, str, float, float, str, float, float]]:
    """
    Fast extraction of 16,000+ CGWB records using pypdf / pdfplumber.
    Returns list of tuples: (state_ut, district, block, village, latitude, longitude, record_date, dtwl_mbgl, dtwl_ft)
    """
    records = []
    print(f"📄 Reading PDF from: {pdf_path}")
    t0 = time.time()

    # Pattern for trailing: LATITUDE LONGITUDE DATE DTWL
    # E.g. "17.46330 82.02710 10-01-2026 7.58" or "22.23389 75.86139 10-01-2026 4.33"
    pattern = re.compile(
        r'(\d{1,2}\.\d+)\s+(\d{1,3}\.\d+)\s+(\d{2}[-/]\d{2}[-/]\d{4}|\d{4}[-/]\d{2}[-/]\d{2})\s+([-+]?\d*\.?\d+)\s*$'
    )

    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        print(f"📖 Total pages found in PDF: {total_pages}")

        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue

            for line in text.splitlines():
                line = line.strip()
                if not line or "DEPTH TO WATER LEVEL" in line or "STATE_UT DISTRICT" in line:
                    continue

                m = pattern.search(line)
                if not m:
                    # Try loose match if font overlapping merged date/number
                    loose = re.search(r'(\d{1,2}\.\d+)\s+(\d{1,3}\.\d+)\s+(\d{2}[-/]\d{2}[-/]\d{4})\s+([-+]?\d*\.?\d+)', line)
                    if loose:
                        m = loose

                if m:
                    try:
                        lat = float(m.group(1))
                        lon = float(m.group(2))
                        rdate = m.group(3)
                        dtwl_mbgl = float(m.group(4))
                    except ValueError:
                        continue

                    # Extract prefix (State, District, Block, Village)
                    prefix = line[:m.start()].strip()
                    if not prefix:
                        continue

                    matched_state = ""
                    rest = prefix
                    for s in INDIAN_STATES_UTS:
                        if prefix.lower().startswith(s.lower()):
                            matched_state = s
                            rest = prefix[len(s):].strip()
                            break

                    if not matched_state:
                        # Fallback first word
                        parts = prefix.split(" ", 1)
                        matched_state = parts[0].title()
                        rest = parts[1].strip() if len(parts) > 1 else parts[0].title()

                    # Clean up Dadra UT name if present
                    if "Dadra" in matched_state:
                        matched_state = "Dadra and Nagar Haveli and Daman and Diu"

                    dist, blk, vil = parse_location_parts(rest)

                    if dtwl_mbgl > 0:
                        dtwl_ft = round(dtwl_mbgl * 3.28084, 2)
                        dtwl_mbgl = round(dtwl_mbgl, 2)
                        records.append((
                            matched_state,
                            dist,
                            blk,
                            vil,
                            round(lat, 5),
                            round(lon, 5),
                            rdate,
                            dtwl_mbgl,
                            dtwl_ft
                        ))

    except Exception as e:
        print(f"⚠️ Warning during pypdf parsing: {e}. Falling back to pdfplumber...")
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.splitlines():
                    line = line.strip()
                    if not line or "DEPTH TO WATER LEVEL" in line or "STATE_UT DISTRICT" in line:
                        continue
                    m = pattern.search(line)
                    if m:
                        lat = float(m.group(1))
                        lon = float(m.group(2))
                        rdate = m.group(3)
                        dtwl_mbgl = float(m.group(4))
                        prefix = line[:m.start()].strip()
                        matched_state = ""
                        rest = prefix
                        for s in INDIAN_STATES_UTS:
                            if prefix.lower().startswith(s.lower()):
                                matched_state = s
                                rest = prefix[len(s):].strip()
                                break
                        if not matched_state:
                            parts = prefix.split(" ", 1)
                            matched_state = parts[0].title()
                            rest = parts[1].strip() if len(parts) > 1 else parts[0].title()
                        dist, blk, vil = parse_location_parts(rest)
                        if dtwl_mbgl > 0:
                            dtwl_ft = round(dtwl_mbgl * 3.28084, 2)
                            records.append((
                                matched_state, dist, blk, vil,
                                round(lat, 5), round(lon, 5), rdate, round(dtwl_mbgl, 2), dtwl_ft
                            ))

    dur = time.time() - t0
    print(f"✅ Extracted {len(records):,} records from PDF in {dur:.2f} seconds.")
    return records


def ingest_to_sqlite(records: List[Tuple[str, str, str, str, float, float, str, float, float]]) -> int:
    """
    Inserts records into db/cgwb_data.db and creates high-speed indexes.
    Returns total inserted row count.
    """
    DB_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table with optimal structure
    cursor.execute("DROP TABLE IF EXISTS cgwb_water_levels;")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cgwb_water_levels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state_ut TEXT NOT NULL,
        district TEXT NOT NULL,
        block TEXT NOT NULL,
        village TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        record_date TEXT NOT NULL,
        dtwl_mbgl REAL NOT NULL,
        dtwl_ft REAL NOT NULL
    );
    """)

    # Fast bulk insert
    cursor.executemany("""
    INSERT INTO cgwb_water_levels (
        state_ut, district, block, village, latitude, longitude, record_date, dtwl_mbgl, dtwl_ft
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, records)

    # Create indexes for sub-millisecond query performance
    print("⚡ Creating high-speed indexes on district, block, village...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cgwb_district ON cgwb_water_levels (district COLLATE NOCASE);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cgwb_block ON cgwb_water_levels (block COLLATE NOCASE);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cgwb_village ON cgwb_water_levels (village COLLATE NOCASE);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cgwb_district_lower ON cgwb_water_levels (LOWER(district));")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cgwb_block_lower ON cgwb_water_levels (LOWER(block));")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cgwb_village_lower ON cgwb_water_levels (LOWER(village));")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cgwb_state ON cgwb_water_levels (state_ut COLLATE NOCASE);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cgwb_composite ON cgwb_water_levels (district COLLATE NOCASE, block COLLATE NOCASE, village COLLATE NOCASE);")

    conn.commit()

    # Query metrics
    cursor.execute("SELECT COUNT(*) FROM cgwb_water_levels;")
    total_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT state_ut), COUNT(DISTINCT district), COUNT(DISTINCT block), COUNT(DISTINCT village) FROM cgwb_water_levels;")
    states_cnt, dist_cnt, blk_cnt, vil_cnt = cursor.fetchone()

    conn.close()

    dur = time.time() - t0
    print(f"\n🎉 Database Ingestion Completed in {dur:.2f} seconds!")
    print(f"==========================================================")
    print(f"📊 CGWB Groundwater Database Metrics (db/cgwb_data.db):")
    print(f"   • Total Records Ingested: {total_count:,}")
    print(f"   • States & UTs Covered:   {states_cnt}")
    print(f"   • Distinct Districts:     {dist_cnt:,}")
    print(f"   • Distinct Blocks:        {blk_cnt:,}")
    print(f"   • Distinct Villages:      {vil_cnt:,}")
    print(f"==========================================================")

    return total_count


def benchmark_lookups():
    """Validates sub-millisecond query execution on ingested database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    test_queries = [
        ("District Pune", "SELECT * FROM cgwb_water_levels WHERE district = 'Pune' COLLATE NOCASE LIMIT 3"),
        ("District Ludhiana", "SELECT * FROM cgwb_water_levels WHERE district = 'Ludhiana' COLLATE NOCASE LIMIT 3"),
        ("District Jaipur", "SELECT * FROM cgwb_water_levels WHERE district = 'Jaipur' COLLATE NOCASE LIMIT 3"),
        ("Block Khanna", "SELECT * FROM cgwb_water_levels WHERE block = 'Khanna' COLLATE NOCASE LIMIT 3"),
        ("Village Wagholi", "SELECT * FROM cgwb_water_levels WHERE village LIKE '%Wagholi%' COLLATE NOCASE LIMIT 3"),
    ]

    print("\n⏱️ Testing sub-millisecond lookup latency:")
    for label, sql in test_queries:
        t0 = time.perf_counter()
        cursor.execute(sql)
        rows = cursor.fetchall()
        latency_ms = (time.perf_counter() - t0) * 1000
        print(f"   [{label:18}] -> {len(rows)} rows found in {latency_ms:.3f} ms")
        if rows:
            r = rows[0]
            print(f"      Sample: {r['state_ut']} -> {r['district']}, {r['block']}, {r['village']} => {r['dtwl_mbgl']} mbgl (~{r['dtwl_ft']} ft)")

    conn.close()


def main():
    print("==========================================================")
    print("CGWB Water Level PDF Ingestion Pipeline")
    print("==========================================================")

    target_pdf = None
    for p in PDF_CANDIDATES:
        if p.exists():
            target_pdf = p
            break

    if not target_pdf:
        print(f"❌ Error: No waterlevel PDF found among: {[str(p) for p in PDF_CANDIDATES]}")
        sys.exit(1)

    records = extract_records_from_pdf(target_pdf)
    if not records:
        print("❌ Error: No records extracted.")
        sys.exit(1)

    total_rows = ingest_to_sqlite(records)
    benchmark_lookups()
    print(f"\n✅ SUCCESS: Ingested {total_rows:,} rows into db/cgwb_data.db successfully.\n")


if __name__ == "__main__":
    main()
