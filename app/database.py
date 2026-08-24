"""
database.py
Database interaction layer for INGRES Groundwater SQLite database.
Provides schema definitions, safe query execution, and summary metrics.
"""

import sqlite3
import re
from typing import List, Dict, Any, Tuple
from config import DATABASE_PATH

def get_db_connection():
    """Returns a SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(sql_query: str, params: tuple = ()) -> Tuple[List[Dict[str, Any]], str]:
    """
    Safely executes a SELECT query against the SQLite database.
    Returns: (list_of_results_as_dicts, error_message_if_any)
    """
    cleaned_sql = sql_query.strip()
    # Strip any markdown code fences if present
    if cleaned_sql.startswith("```sql"):
        cleaned_sql = cleaned_sql[6:]
    elif cleaned_sql.startswith("```"):
        cleaned_sql = cleaned_sql[3:]
    if cleaned_sql.endswith("```"):
        cleaned_sql = cleaned_sql[:-3]
    cleaned_sql = cleaned_sql.strip()

    # Safety check: enforce read-only SELECT
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE", "CREATE"]
    first_word = cleaned_sql.split()[0].upper() if cleaned_sql else ""
    if first_word in forbidden or any(re.search(rf"\b{f}\b", cleaned_sql, re.IGNORECASE) for f in forbidden):
        return [], "Only read-only SELECT queries are permitted on the INGRES database."

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

def get_schema_info() -> str:
    """Returns schema description formatted for SQL Agent prompts."""
    return """
Database: SQLite (ingres_groundwater.db)
Tables and Columns:

1. Table: groundwater_assessments
   - id: INTEGER PRIMARY KEY AUTOINCREMENT
   - state: TEXT (e.g. 'Uttar Pradesh', 'Punjab', 'Rajasthan', 'Maharashtra', 'Haryana', 'Madhya Pradesh', 'Bihar')
   - district: TEXT (e.g. 'Meerut', 'Jaipur', 'Sangrur', 'Ludhiana', 'Pune', 'Karnal', 'Indore', 'Patna', etc.)
   - block_name: TEXT (e.g. 'Daurala', 'Rajpura', 'Amber', 'Jhotwara', 'Sangrur', 'Khanna', 'Haveli', etc.)
   - annual_recharge_ham: REAL (Annual groundwater recharge in Hectare-Meters / ham)
   - extractable_resource_ham: REAL (Total extractable groundwater in ham)
   - current_extraction_irrigation_ham: REAL (Groundwater extraction for agriculture/irrigation in ham)
   - current_extraction_total_ham: REAL (Total extraction for all uses in ham)
   - extraction_percentage: REAL (Stage of groundwater extraction in %, e.g., 50.2, 99.4, 173.3, 239.8)
   - category_status: TEXT (Standard CGWB Category: 'Safe' [<70%], 'Semi-Critical' [70-90%], 'Critical' [90-100%], 'Over-Exploited' [>100%])
   - depth_mbgl: REAL (Water Table Depth from CGWB DWLR telemetry in meters below ground level; 1m ≈ 3.28 ft)

2. Table: water_table_trends
   - id: INTEGER PRIMARY KEY AUTOINCREMENT
   - state: TEXT
   - district: TEXT
   - block_name: TEXT
   - pre_monsoon_depth_meters: REAL (Depth to water level before monsoon, in meters below ground level / mbgl)
   - post_monsoon_depth_meters: REAL (Depth to water level after monsoon, in mbgl)
   - annual_trend: TEXT ('Falling', 'Stable', 'Rising')

3. Table: crop_irrigation_advisory
   - id: INTEGER PRIMARY KEY AUTOINCREMENT
   - crop_name: TEXT (e.g. 'Bajra (Pearl Millet)', 'Jowar (Sorghum)', 'Gram / Chickpea (Chana)', 'Mustard / Rapeseed', 'Wheat', 'Rice / Paddy (DSR)', 'Sugarcane', etc.)
   - water_requirement_mm: REAL (Total crop water requirement in mm)
   - suitable_in_overexploited_zones: BOOLEAN (1 if recommended for water-stressed/dark zones, 0 if discouraged/high water)
   - recommended_irrigation_method: TEXT (e.g. 'Drip Irrigation', 'Sprinkler Irrigation', 'Micro-Sprinkler', etc.)
   - advisory_notes: TEXT (Detailed guidance, water saving potential, and tips for farmers)
"""

def get_stats() -> Dict[str, Any]:
    """Returns overview statistics for dashboard metrics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    total_blocks = cursor.execute("SELECT COUNT(*) FROM groundwater_assessments").fetchone()[0]
    states = [row[0] for row in cursor.execute("SELECT DISTINCT state FROM groundwater_assessments ORDER BY state").fetchall()]
    districts = [row[0] for row in cursor.execute("SELECT DISTINCT district FROM groundwater_assessments ORDER BY district").fetchall()]

    categories_count = {}
    for cat, count in cursor.execute("SELECT category_status, COUNT(*) FROM groundwater_assessments GROUP BY category_status").fetchall():
        categories_count[cat] = count

    trends_count = {}
    for tr, count in cursor.execute("SELECT annual_trend, COUNT(*) FROM water_table_trends GROUP BY annual_trend").fetchall():
        trends_count[tr] = count

    crops_count = cursor.execute("SELECT COUNT(*) FROM crop_irrigation_advisory").fetchone()[0]

    conn.close()

    return {
        "total_blocks": total_blocks,
        "states_count": len(states),
        "states": states,
        "districts_count": len(districts),
        "categories": {
            "Safe": categories_count.get("Safe", 0),
            "Semi-Critical": categories_count.get("Semi-Critical", 0),
            "Critical": categories_count.get("Critical", 0),
            "Over-Exploited": categories_count.get("Over-Exploited", 0),
        },
        "trends": {
            "Rising": trends_count.get("Rising", 0),
            "Stable": trends_count.get("Stable", 0),
            "Falling": trends_count.get("Falling", 0),
        },
        "total_crops": crops_count
    }
