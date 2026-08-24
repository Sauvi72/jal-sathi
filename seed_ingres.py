#!/usr/bin/env python3
"""
seed_ingres.py
Initializes and seeds the INGRES (India Groundwater Resource Estimation System)
SQLite database with realistic Central Ground Water Board (CGWB) assessment metrics,
water table depth trends, and crop irrigation advisories.
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ingres_groundwater.db"

def init_database():
    """Initializes tables and seeds CGWB data."""
    if os.path.exists(DB_PATH):
        print(f"Removing existing database at {DB_PATH} for a clean seed...")
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Creating tables...")

    # Table 1: groundwater_assessments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS groundwater_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state TEXT NOT NULL,
        district TEXT NOT NULL,
        block_name TEXT NOT NULL,
        annual_recharge_ham REAL NOT NULL,
        extractable_resource_ham REAL NOT NULL,
        current_extraction_irrigation_ham REAL NOT NULL,
        current_extraction_total_ham REAL NOT NULL,
        extraction_percentage REAL NOT NULL,
        category_status TEXT NOT NULL CHECK(category_status IN ('Safe', 'Semi-Critical', 'Critical', 'Over-Exploited'))
    );
    """)

    # Table 2: water_table_trends
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS water_table_trends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state TEXT NOT NULL,
        district TEXT NOT NULL,
        block_name TEXT NOT NULL,
        pre_monsoon_depth_meters REAL NOT NULL,
        post_monsoon_depth_meters REAL NOT NULL,
        annual_trend TEXT NOT NULL CHECK(annual_trend IN ('Falling', 'Stable', 'Rising'))
    );
    """)

    # Table 3: crop_irrigation_advisory
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crop_irrigation_advisory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        crop_name TEXT NOT NULL,
        water_requirement_mm REAL NOT NULL,
        suitable_in_overexploited_zones BOOLEAN NOT NULL CHECK(suitable_in_overexploited_zones IN (0, 1)),
        recommended_irrigation_method TEXT NOT NULL,
        advisory_notes TEXT NOT NULL
    );
    """)

    # Indexes for performance and quick lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessment_state_dist ON groundwater_assessments(state, district);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessment_block ON groundwater_assessments(block_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_block ON water_table_trends(block_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crop_name ON crop_irrigation_advisory(crop_name);")

    print("Seeding groundwater assessments and water table trends...")

    assessments_and_trends = [
        # --- UTTAR PRADESH ---
        ("Uttar Pradesh", "Meerut", "Daurala", 5420.5, 4878.4, 4610.0, 4850.0, 99.4, "Critical", 28.5, 26.2, "Falling"),
        ("Uttar Pradesh", "Meerut", "Rajpura", 4800.0, 4320.0, 4750.0, 5020.0, 116.2, "Over-Exploited", 34.2, 32.8, "Falling"),
        ("Uttar Pradesh", "Meerut", "Hastinapur", 7850.0, 7065.0, 3200.0, 3550.0, 50.2, "Safe", 12.4, 8.6, "Rising"),
        ("Uttar Pradesh", "Meerut", "Sardhana", 6100.0, 5490.0, 4200.0, 4510.0, 82.1, "Semi-Critical", 22.8, 19.5, "Stable"),
        ("Uttar Pradesh", "Varanasi", "Kashi Vidyapeeth", 3900.0, 3510.0, 3100.0, 3350.0, 95.4, "Critical", 26.5, 24.1, "Falling"),
        ("Uttar Pradesh", "Varanasi", "Cholapur", 5200.0, 4680.0, 2600.0, 2900.0, 61.9, "Safe", 14.2, 10.8, "Rising"),
        ("Uttar Pradesh", "Varanasi", "Pindra", 6100.0, 5490.0, 3100.0, 3450.0, 62.8, "Safe", 15.1, 11.9, "Stable"),
        ("Uttar Pradesh", "Agra", "Fatehabad", 4500.0, 4050.0, 4900.0, 5200.0, 128.4, "Over-Exploited", 42.0, 40.5, "Falling"),
        ("Uttar Pradesh", "Agra", "Khandauli", 3800.0, 3420.0, 4200.0, 4500.0, 131.6, "Over-Exploited", 45.8, 44.1, "Falling"),
        ("Uttar Pradesh", "Agra", "Bichpuri", 4100.0, 3690.0, 3400.0, 3650.0, 98.9, "Critical", 31.2, 29.6, "Falling"),
        ("Uttar Pradesh", "Agra", "Bah", 8200.0, 7380.0, 3800.0, 4200.0, 56.9, "Safe", 18.4, 14.5, "Stable"),
        ("Uttar Pradesh", "Lucknow", "Sarojini Nagar", 6400.0, 5760.0, 4400.0, 4800.0, 83.3, "Semi-Critical", 21.0, 18.4, "Falling"),
        ("Uttar Pradesh", "Lucknow", "Bakshi Ka Talab", 7100.0, 6390.0, 3600.0, 3950.0, 61.8, "Safe", 15.6, 12.1, "Stable"),
        ("Uttar Pradesh", "Lucknow", "Mohanlalganj", 6900.0, 6210.0, 3500.0, 3820.0, 61.5, "Safe", 16.2, 12.8, "Stable"),
        ("Uttar Pradesh", "Aligarh", "Jawan", 4300.0, 3870.0, 4400.0, 4700.0, 121.4, "Over-Exploited", 38.6, 37.0, "Falling"),
        ("Uttar Pradesh", "Aligarh", "Atrauli", 5600.0, 5040.0, 3900.0, 4250.0, 84.3, "Semi-Critical", 24.1, 21.3, "Stable"),
        ("Uttar Pradesh", "Gorakhpur", "Pipraich", 8900.0, 8010.0, 3200.0, 3600.0, 44.9, "Safe", 9.5, 5.8, "Rising"),
        ("Uttar Pradesh", "Gorakhpur", "Bhathat", 8400.0, 7560.0, 3100.0, 3450.0, 45.6, "Safe", 10.1, 6.2, "Rising"),
        ("Uttar Pradesh", "Jhansi", "Babina", 6200.0, 5580.0, 2800.0, 3100.0, 55.5, "Safe", 18.2, 13.5, "Stable"),
        ("Uttar Pradesh", "Jhansi", "Mauranipur", 5100.0, 4590.0, 3500.0, 3850.0, 83.8, "Semi-Critical", 25.4, 21.8, "Falling"),
        ("Uttar Pradesh", "Prayagraj", "Soraon", 6300.0, 5670.0, 4300.0, 4650.0, 82.0, "Semi-Critical", 22.4, 18.9, "Falling"),
        ("Uttar Pradesh", "Prayagraj", "Karchhana", 7200.0, 6480.0, 3600.0, 3950.0, 60.9, "Safe", 16.5, 12.2, "Stable"),

        # --- PUNJAB ---
        ("Punjab", "Ludhiana", "Ludhiana-1", 4200.0, 3780.0, 6100.0, 6550.0, 173.3, "Over-Exploited", 48.5, 47.1, "Falling"),
        ("Punjab", "Ludhiana", "Khanna", 4900.0, 4410.0, 6900.0, 7400.0, 167.8, "Over-Exploited", 44.2, 43.0, "Falling"),
        ("Punjab", "Ludhiana", "Samrala", 4600.0, 4140.0, 6200.0, 6650.0, 160.6, "Over-Exploited", 42.1, 41.0, "Falling"),
        ("Punjab", "Ludhiana", "Jagraon", 5100.0, 4590.0, 7200.0, 7700.0, 167.7, "Over-Exploited", 43.8, 42.5, "Falling"),
        ("Punjab", "Sangrur", "Sangrur", 3800.0, 3420.0, 7100.0, 7650.0, 223.7, "Over-Exploited", 56.4, 55.2, "Falling"),
        ("Punjab", "Sangrur", "Sunam", 4100.0, 3690.0, 7400.0, 7950.0, 215.4, "Over-Exploited", 54.8, 53.9, "Falling"),
        ("Punjab", "Sangrur", "Dhuri", 3900.0, 3510.0, 6800.0, 7300.0, 207.9, "Over-Exploited", 51.2, 50.1, "Falling"),
        ("Punjab", "Jalandhar", "Jalandhar East", 4400.0, 3960.0, 5800.0, 6250.0, 157.8, "Over-Exploited", 39.5, 38.2, "Falling"),
        ("Punjab", "Jalandhar", "Nakodar", 4100.0, 3690.0, 5700.0, 6100.0, 165.3, "Over-Exploited", 41.0, 39.8, "Falling"),
        ("Punjab", "Jalandhar", "Shahkot", 4700.0, 4230.0, 6100.0, 6500.0, 153.6, "Over-Exploited", 38.2, 37.0, "Falling"),
        ("Punjab", "Amritsar", "Majitha", 5200.0, 4680.0, 6800.0, 7300.0, 155.9, "Over-Exploited", 36.8, 35.5, "Falling"),
        ("Punjab", "Amritsar", "Jandiala", 4800.0, 4320.0, 6200.0, 6650.0, 153.9, "Over-Exploited", 35.4, 34.1, "Falling"),
        ("Punjab", "Bathinda", "Talwandi Sabo", 3600.0, 3240.0, 4400.0, 4750.0, 146.6, "Over-Exploited", 29.5, 28.6, "Falling"),
        ("Punjab", "Bathinda", "Rampura", 4100.0, 3690.0, 3400.0, 3650.0, 98.9, "Critical", 24.1, 23.2, "Falling"),
        ("Punjab", "Patiala", "Nabha", 4300.0, 3870.0, 6900.0, 7400.0, 191.2, "Over-Exploited", 46.8, 45.7, "Falling"),
        ("Punjab", "Patiala", "Rajpura", 4600.0, 4140.0, 6700.0, 7150.0, 172.7, "Over-Exploited", 43.5, 42.4, "Falling"),

        # --- RAJASTHAN ---
        ("Rajasthan", "Jaipur", "Amber", 2800.0, 2520.0, 4800.0, 5200.0, 206.3, "Over-Exploited", 62.4, 61.5, "Falling"),
        ("Rajasthan", "Jaipur", "Jhotwara", 2200.0, 1980.0, 4300.0, 4750.0, 239.8, "Over-Exploited", 74.5, 73.8, "Falling"),
        ("Rajasthan", "Jaipur", "Sanganer", 2400.0, 2160.0, 4500.0, 4950.0, 229.1, "Over-Exploited", 68.2, 67.4, "Falling"),
        ("Rajasthan", "Jaipur", "Bassi", 3400.0, 3060.0, 2800.0, 3020.0, 98.7, "Critical", 48.2, 47.0, "Falling"),
        ("Rajasthan", "Jaipur", "Chaksu", 3100.0, 2790.0, 3900.0, 4250.0, 152.3, "Over-Exploited", 52.8, 51.9, "Falling"),
        ("Rajasthan", "Jodhpur", "Mandore", 1900.0, 1710.0, 3600.0, 3950.0, 230.9, "Over-Exploited", 82.5, 81.9, "Falling"),
        ("Rajasthan", "Jodhpur", "Bilara", 2400.0, 2160.0, 3800.0, 4100.0, 189.8, "Over-Exploited", 65.4, 64.6, "Falling"),
        ("Rajasthan", "Jodhpur", "Osian", 2700.0, 2430.0, 2200.0, 2400.0, 98.7, "Critical", 58.2, 57.5, "Falling"),
        ("Rajasthan", "Jaisalmer", "Jaisalmer", 1400.0, 1260.0, 1100.0, 1220.0, 96.8, "Critical", 78.4, 78.0, "Falling"),
        ("Rajasthan", "Jaisalmer", "Pokhran", 1800.0, 1620.0, 1200.0, 1380.0, 85.2, "Semi-Critical", 64.2, 63.5, "Stable"),
        ("Rajasthan", "Jaisalmer", "Fatehgarh", 2200.0, 1980.0, 950.0, 1120.0, 56.6, "Safe", 52.0, 51.2, "Stable"),
        ("Rajasthan", "Bikaner", "Bikaner", 2100.0, 1890.0, 3400.0, 3750.0, 198.4, "Over-Exploited", 72.0, 71.2, "Falling"),
        ("Rajasthan", "Bikaner", "Kolayat", 2600.0, 2340.0, 2100.0, 2290.0, 97.9, "Critical", 61.5, 60.8, "Falling"),
        ("Rajasthan", "Bikaner", "Nokha", 2300.0, 2070.0, 3800.0, 4150.0, 200.5, "Over-Exploited", 69.4, 68.7, "Falling"),
        ("Rajasthan", "Sikar", "Dhod", 2400.0, 2160.0, 4600.0, 4980.0, 230.6, "Over-Exploited", 67.8, 67.0, "Falling"),
        ("Rajasthan", "Sikar", "Neem Ka Thana", 2800.0, 2520.0, 4700.0, 5080.0, 201.6, "Over-Exploited", 59.2, 58.5, "Falling"),
        ("Rajasthan", "Sikar", "Fatehpur", 2500.0, 2250.0, 4400.0, 4750.0, 211.1, "Over-Exploited", 63.4, 62.6, "Falling"),
        ("Rajasthan", "Alwar", "Behror", 3100.0, 2790.0, 4900.0, 5300.0, 189.9, "Over-Exploited", 54.6, 53.8, "Falling"),
        ("Rajasthan", "Alwar", "Tijara", 3600.0, 3240.0, 3000.0, 3200.0, 98.8, "Critical", 42.1, 41.2, "Falling"),
        ("Rajasthan", "Alwar", "Thanagazi", 4200.0, 3780.0, 2800.0, 3100.0, 82.0, "Semi-Critical", 31.5, 29.8, "Stable"),
        ("Rajasthan", "Jhunjhunu", "Khetri", 2600.0, 2340.0, 4200.0, 4550.0, 194.4, "Over-Exploited", 58.7, 57.9, "Falling"),
        ("Rajasthan", "Jhunjhunu", "Buhana", 2400.0, 2160.0, 4300.0, 4680.0, 216.7, "Over-Exploited", 64.1, 63.4, "Falling"),

        # --- MAHARASHTRA ---
        ("Maharashtra", "Pune", "Haveli", 7200.0, 6480.0, 4900.0, 5450.0, 84.1, "Semi-Critical", 18.5, 14.8, "Falling"),
        ("Maharashtra", "Pune", "Shirur", 6500.0, 5850.0, 5300.0, 5750.0, 98.3, "Critical", 22.4, 18.9, "Falling"),
        ("Maharashtra", "Pune", "Baramati", 7100.0, 6390.0, 5100.0, 5600.0, 87.6, "Semi-Critical", 19.8, 16.1, "Falling"),
        ("Maharashtra", "Pune", "Daund", 8400.0, 7560.0, 4200.0, 4700.0, 62.2, "Safe", 14.1, 9.8, "Stable"),
        ("Maharashtra", "Pune", "Junnar", 9200.0, 8280.0, 4100.0, 4600.0, 55.6, "Safe", 12.6, 8.2, "Rising"),
        ("Maharashtra", "Nagpur", "Nagpur Rural", 8600.0, 7740.0, 3800.0, 4300.0, 55.6, "Safe", 11.8, 7.5, "Rising"),
        ("Maharashtra", "Nagpur", "Saoner", 8900.0, 8010.0, 3900.0, 4400.0, 54.9, "Safe", 10.9, 6.8, "Rising"),
        ("Maharashtra", "Nagpur", "Katol", 7400.0, 6660.0, 4800.0, 5350.0, 80.3, "Semi-Critical", 16.4, 12.8, "Stable"),
        ("Maharashtra", "Nashik", "Niphad", 6800.0, 6120.0, 5600.0, 6050.0, 98.9, "Critical", 24.8, 20.9, "Falling"),
        ("Maharashtra", "Nashik", "Sinnar", 5900.0, 5310.0, 6100.0, 6600.0, 124.3, "Over-Exploited", 29.5, 26.8, "Falling"),
        ("Maharashtra", "Nashik", "Dindori", 8800.0, 7920.0, 4100.0, 4600.0, 58.1, "Safe", 13.2, 9.1, "Rising"),
        ("Maharashtra", "Nashik", "Yeola", 6100.0, 5490.0, 5000.0, 5420.0, 98.7, "Critical", 26.4, 23.1, "Falling"),
        ("Maharashtra", "Chhatrapati Sambhajinagar", "Paithan", 7100.0, 6390.0, 4900.0, 5400.0, 84.5, "Semi-Critical", 19.5, 15.6, "Stable"),
        ("Maharashtra", "Chhatrapati Sambhajinagar", "Vaijapur", 5400.0, 4860.0, 5600.0, 6100.0, 125.5, "Over-Exploited", 28.7, 26.1, "Falling"),
        ("Maharashtra", "Chhatrapati Sambhajinagar", "Gangapur", 6200.0, 5580.0, 5100.0, 5510.0, 98.7, "Critical", 23.9, 20.4, "Falling"),
        ("Maharashtra", "Ahmednagar", "Sangamner", 5800.0, 5220.0, 6400.0, 6900.0, 132.2, "Over-Exploited", 31.4, 28.9, "Falling"),
        ("Maharashtra", "Ahmednagar", "Rahata", 6300.0, 5670.0, 5200.0, 5610.0, 98.9, "Critical", 25.1, 21.8, "Falling"),
        ("Maharashtra", "Ahmednagar", "Parner", 6900.0, 6210.0, 4700.0, 5150.0, 82.9, "Semi-Critical", 20.4, 16.5, "Stable"),
        ("Maharashtra", "Ahmednagar", "Shevgaon", 7800.0, 7020.0, 3900.0, 4350.0, 62.0, "Safe", 15.2, 10.9, "Rising"),
        ("Maharashtra", "Solapur", "Pandharpur", 7600.0, 6840.0, 5200.0, 5700.0, 83.3, "Semi-Critical", 19.1, 15.4, "Falling"),
        ("Maharashtra", "Solapur", "Karmala", 6100.0, 5490.0, 5100.0, 5430.0, 98.9, "Critical", 24.6, 21.2, "Falling"),
        ("Maharashtra", "Solapur", "Malshiras", 7400.0, 6660.0, 5300.0, 5800.0, 87.1, "Semi-Critical", 20.2, 16.8, "Falling"),

        # --- HARYANA ---
        ("Haryana", "Karnal", "Karnal", 4900.0, 4410.0, 6800.0, 7350.0, 166.7, "Over-Exploited", 36.2, 35.1, "Falling"),
        ("Haryana", "Karnal", "Nilokheri", 4500.0, 4050.0, 6400.0, 6900.0, 170.4, "Over-Exploited", 37.8, 36.7, "Falling"),
        ("Haryana", "Karnal", "Assandh", 4700.0, 4230.0, 6600.0, 7120.0, 168.3, "Over-Exploited", 35.4, 34.3, "Falling"),
        ("Haryana", "Karnal", "Gharaunda", 4600.0, 4140.0, 6500.0, 7000.0, 169.1, "Over-Exploited", 36.9, 35.8, "Falling"),
        ("Haryana", "Kurukshetra", "Thanesar", 4100.0, 3690.0, 6900.0, 7450.0, 201.9, "Over-Exploited", 44.5, 43.6, "Falling"),
        ("Haryana", "Kurukshetra", "Pehowa", 4300.0, 3870.0, 7200.0, 7800.0, 201.6, "Over-Exploited", 46.1, 45.2, "Falling"),
        ("Haryana", "Kurukshetra", "Shahbad", 4200.0, 3780.0, 7100.0, 7680.0, 203.2, "Over-Exploited", 45.8, 44.9, "Falling"),
        ("Haryana", "Sirsa", "Sirsa", 5200.0, 4680.0, 4200.0, 4620.0, 98.7, "Critical", 22.8, 21.9, "Falling"),
        ("Haryana", "Sirsa", "Ellenabad", 5800.0, 5220.0, 4100.0, 4550.0, 87.2, "Semi-Critical", 19.5, 18.2, "Stable"),
        ("Haryana", "Sirsa", "Dabwali", 4800.0, 4320.0, 3900.0, 4290.0, 99.3, "Critical", 24.1, 23.4, "Falling"),
        ("Haryana", "Gurugram", "Gurugram", 2900.0, 2610.0, 5200.0, 5800.0, 222.2, "Over-Exploited", 42.8, 42.1, "Falling"),
        ("Haryana", "Gurugram", "Sohna", 3200.0, 2880.0, 5400.0, 5950.0, 206.6, "Over-Exploited", 39.5, 38.7, "Falling"),
        ("Haryana", "Gurugram", "Pataudi", 3400.0, 3060.0, 5600.0, 6100.0, 199.3, "Over-Exploited", 38.2, 37.4, "Falling"),
        ("Haryana", "Hisar", "Hisar-1", 5400.0, 4860.0, 3900.0, 4300.0, 88.5, "Semi-Critical", 18.2, 16.9, "Stable"),
        ("Haryana", "Hisar", "Hansi-1", 6200.0, 5580.0, 3100.0, 3500.0, 62.7, "Safe", 14.8, 11.2, "Rising"),
        ("Haryana", "Hisar", "Barwala", 5600.0, 5040.0, 3800.0, 4250.0, 84.3, "Semi-Critical", 17.5, 15.9, "Stable"),

        # --- MADHYA PRADESH ---
        ("Madhya Pradesh", "Indore", "Indore", 5100.0, 4590.0, 5800.0, 6400.0, 139.4, "Over-Exploited", 38.2, 36.5, "Falling"),
        ("Madhya Pradesh", "Indore", "Sanwer", 4900.0, 4410.0, 5600.0, 6150.0, 139.5, "Over-Exploited", 36.8, 35.1, "Falling"),
        ("Madhya Pradesh", "Indore", "Depalpur", 5300.0, 4770.0, 4400.0, 4710.0, 98.7, "Critical", 29.4, 27.2, "Falling"),
        ("Madhya Pradesh", "Indore", "Mhow", 6400.0, 5760.0, 4300.0, 4800.0, 83.3, "Semi-Critical", 22.1, 18.5, "Stable"),
        ("Madhya Pradesh", "Ujjain", "Ujjain", 4800.0, 4320.0, 5700.0, 6250.0, 144.7, "Over-Exploited", 35.6, 34.0, "Falling"),
        ("Madhya Pradesh", "Ujjain", "Mahidpur", 5200.0, 4680.0, 4300.0, 4630.0, 98.9, "Critical", 28.5, 26.3, "Falling"),
        ("Madhya Pradesh", "Ujjain", "Badnagar", 4700.0, 4230.0, 5400.0, 5950.0, 140.7, "Over-Exploited", 34.8, 33.2, "Falling"),
        ("Madhya Pradesh", "Bhopal", "Phanda", 6800.0, 6120.0, 4800.0, 5350.0, 87.4, "Semi-Critical", 21.0, 17.5, "Falling"),
        ("Madhya Pradesh", "Bhopal", "Berasia", 7900.0, 7110.0, 3900.0, 4400.0, 61.9, "Safe", 14.5, 10.2, "Rising"),
        ("Madhya Pradesh", "Jabalpur", "Jabalpur", 9400.0, 8460.0, 3800.0, 4450.0, 52.6, "Safe", 11.2, 6.8, "Rising"),
        ("Madhya Pradesh", "Jabalpur", "Sihora", 8800.0, 7920.0, 3600.0, 4100.0, 51.8, "Safe", 12.0, 7.4, "Rising"),
        ("Madhya Pradesh", "Jabalpur", "Patan", 7600.0, 6840.0, 5100.0, 5650.0, 82.6, "Semi-Critical", 18.6, 14.9, "Stable"),
        ("Madhya Pradesh", "Gwalior", "Morar", 5800.0, 5220.0, 4800.0, 5160.0, 98.9, "Critical", 27.4, 25.1, "Falling"),
        ("Madhya Pradesh", "Gwalior", "Ghatigaon", 7600.0, 6840.0, 3200.0, 3600.0, 52.6, "Safe", 15.0, 11.2, "Rising"),
        ("Madhya Pradesh", "Gwalior", "Dabra", 6900.0, 6210.0, 4800.0, 5350.0, 86.2, "Semi-Critical", 20.8, 17.6, "Stable"),

        # --- BIHAR ---
        ("Bihar", "Patna", "Sampatchak", 6200.0, 5580.0, 4200.0, 4750.0, 85.1, "Semi-Critical", 16.4, 13.8, "Falling"),
        ("Bihar", "Patna", "Phulwari", 7100.0, 6390.0, 3600.0, 4100.0, 64.2, "Safe", 13.8, 10.2, "Stable"),
        ("Bihar", "Patna", "Danapur", 7400.0, 6660.0, 3800.0, 4350.0, 65.3, "Safe", 14.1, 10.5, "Stable"),
        ("Bihar", "Patna", "Bikram", 8200.0, 7380.0, 3900.0, 4400.0, 59.6, "Safe", 11.5, 7.8, "Rising"),
        ("Bihar", "Patna", "Barh", 8600.0, 7740.0, 3700.0, 4200.0, 54.3, "Safe", 10.8, 7.1, "Rising"),
        ("Bihar", "Gaya", "Gaya Town", 4800.0, 4320.0, 3900.0, 4280.0, 99.1, "Critical", 24.2, 21.8, "Falling"),
        ("Bihar", "Gaya", "Bodhgaya", 5600.0, 5040.0, 4100.0, 4550.0, 90.3, "Critical", 21.5, 18.6, "Falling"),
        ("Bihar", "Gaya", "Manpur", 5900.0, 5310.0, 4100.0, 4600.0, 86.6, "Semi-Critical", 19.8, 16.5, "Falling"),
        ("Bihar", "Gaya", "Sherghati", 7800.0, 7020.0, 3500.0, 3950.0, 56.3, "Safe", 13.2, 9.4, "Rising"),
        ("Bihar", "Muzaffarpur", "Musahari", 9200.0, 8280.0, 3600.0, 4150.0, 50.1, "Safe", 8.8, 5.2, "Rising"),
        ("Bihar", "Muzaffarpur", "Kanti", 9600.0, 8640.0, 3700.0, 4250.0, 49.2, "Safe", 8.4, 4.9, "Rising"),
        ("Bihar", "Muzaffarpur", "Motipur", 9800.0, 8820.0, 3800.0, 4350.0, 49.3, "Safe", 8.2, 4.7, "Rising"),
        ("Bihar", "Muzaffarpur", "Sakra", 9100.0, 8190.0, 3500.0, 4050.0, 49.5, "Safe", 8.6, 5.1, "Rising"),
        ("Bihar", "Bhagalpur", "Jagdishpur", 8700.0, 7830.0, 3600.0, 4100.0, 52.4, "Safe", 9.8, 6.2, "Rising"),
        ("Bihar", "Bhagalpur", "Nathnagar", 8900.0, 8010.0, 3700.0, 4200.0, 52.4, "Safe", 9.5, 5.9, "Rising"),
        ("Bihar", "Bhagalpur", "Sultanganj", 9300.0, 8370.0, 3500.0, 3980.0, 47.6, "Safe", 9.0, 5.4, "Rising"),
        ("Bihar", "Nalanda", "Biharsharif", 6400.0, 5760.0, 4600.0, 5100.0, 88.5, "Semi-Critical", 18.4, 15.2, "Falling"),
        ("Bihar", "Nalanda", "Rajgir", 7900.0, 7110.0, 3800.0, 4250.0, 59.8, "Safe", 13.5, 9.8, "Rising"),
        ("Bihar", "Nalanda", "Harnaut", 8100.0, 7290.0, 3900.0, 4380.0, 60.1, "Safe", 12.8, 8.9, "Stable"),
    ]

    for item in assessments_and_trends:
        state, dist, block, rech, ext_res, ext_irr, ext_tot, ext_pct, cat, pre_d, post_d, trend = item
        cursor.execute("""
        INSERT INTO groundwater_assessments (
            state, district, block_name, annual_recharge_ham, extractable_resource_ham,
            current_extraction_irrigation_ham, current_extraction_total_ham,
            extraction_percentage, category_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (state, dist, block, rech, ext_res, ext_irr, ext_tot, ext_pct, cat))

        cursor.execute("""
        INSERT INTO water_table_trends (
            state, district, block_name, pre_monsoon_depth_meters, post_monsoon_depth_meters, annual_trend
        ) VALUES (?, ?, ?, ?, ?, ?)
        """, (state, dist, block, pre_d, post_d, trend))

    print(f"Seeded {len(assessments_and_trends)} blocks in groundwater_assessments & water_table_trends.")

    print("Seeding crop irrigation advisories...")

    crop_advisories = [
        ("Bajra (Pearl Millet)", 350.0, 1, "Sprinkler / Rainfed", "Highly recommended for water-stressed/dark zones. Highly drought-tolerant, requires minimal groundwater."),
        ("Jowar (Sorghum)", 400.0, 1, "Furrow / Sprinkler", "Excellent climate-resilient crop for semi-arid areas. Low water consumption and restores soil health."),
        ("Ragi (Finger Millet)", 350.0, 1, "Micro-Sprinkler / Drip", "Nutri-cereal ideal for dry tracts; highly recommended under PMKSY water-saving crop rotation."),
        ("Mustard / Rapeseed", 300.0, 1, "Sprinkler Irrigation", "Rabi season oilseed requiring only 2-3 light irrigations. Ideal alternative to wheat in water-scarce zones."),
        ("Gram / Chickpea (Chana)", 280.0, 1, "Sprinkler / Broad Bed Furrow", "Pulse crop with low water requirement; fixes nitrogen naturally and requires 1-2 irrigations."),
        ("Moong / Green Gram", 250.0, 1, "Sprinkler Irrigation", "Short duration pulse (60-65 days). Requires minimal water, perfect for summer/kharif catch cropping."),
        ("Urad / Black Gram", 300.0, 1, "Sprinkler Irrigation", "Drought-hardy pulse crop suited for semi-critical and water deficit regions."),
        ("Groundnut (Peanut)", 500.0, 1, "Drip / Sprinkler Irrigation", "Profitable cash crop when combined with drip irrigation; avoids flood irrigation."),
        ("Soybean", 450.0, 1, "Broad Bed Furrow (BBF) / Sprinkler", "Kharif oilseed performing well under rainfed conditions with supplementary micro-irrigation."),
        ("Maize (Corn)", 550.0, 1, "Drip Irrigation", "Moderate water requirement. High yield with fertigation via drip; saves 40% water over flood methods."),
        ("Cotton", 700.0, 0, "Drip Irrigation with Mulching", "Medium-to-high water requirement. Strictly discourage flood irrigation; drip mandatory in stressed zones."),
        ("Wheat", 450.0, 1, "Sprinkler Irrigation / Border Strip", "Standard Rabi staple. Use CRI (Crown Root Initiation) stage focused irrigation and laser levelling."),
        ("Rice / Paddy (DSR)", 800.0, 0, "Direct Seeded Rice (DSR) / Alternate Wetting and Drying (AWD)", "Flood paddy strictly discouraged in Over-Exploited zones (Punjab/Haryana/West UP). Shift to DSR/Maize/Pulses."),
        ("Paddy (Traditional Flood)", 1600.0, 0, "Not Recommended in Stressed Zones", "Extremely water-intensive (>1500 mm). Causes steep water table depletion; shift to millets/pulses."),
        ("Sugarcane", 2000.0, 0, "Sub-surface Drip Irrigation (SDI) with Trash Mulching", "Extremely heavy water feeder. Strictly restrict flood irrigation in Critical/OE zones; mandate drip with 55% subsidy."),
        ("Vegetables (Tomato / Chilli / Okra)", 400.0, 1, "Drip Fertigation with Mulch", "High value crops yielding high income with 60% less water under micro-irrigation."),
        ("Pomegranate / Guava / Citrus Orchards", 600.0, 1, "Inline Drip Irrigation", "Perennial horticulture crop highly suitable for semi-arid tracts with drip irrigation.")
    ]

    for crop in crop_advisories:
        name, req, suitable, method, notes = crop
        cursor.execute("""
        INSERT INTO crop_irrigation_advisory (
            crop_name, water_requirement_mm, suitable_in_overexploited_zones,
            recommended_irrigation_method, advisory_notes
        ) VALUES (?, ?, ?, ?, ?)
        """, (name, req, suitable, method, notes))

    print(f"Seeded {len(crop_advisories)} crops in crop_irrigation_advisory.")

    conn.commit()
    conn.close()
    print(f"Database successfully initialized and seeded at: {DB_PATH}")

if __name__ == "__main__":
    init_database()
