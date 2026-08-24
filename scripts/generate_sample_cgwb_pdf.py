"""
scripts/generate_sample_cgwb_pdf.py
Generates an official-looking National Water Informatics Centre / CGWB
Ground Water Level Monitoring Report (January 2026) in PDF format with tabular data.
"""

import os
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUTPUT_PDF = Path(__file__).resolve().parent.parent / "January_2026.pdf"

DATA_ROWS = [
    # State/UT, District, Block, Village, Latitude, Longitude, Record Date, DTWL (m bgl)
    # Uttar Pradesh
    ("Uttar Pradesh", "Meerut", "Daurala", "Daurala", 29.1172, 77.7025, "2026-01-15", 28.45),
    ("Uttar Pradesh", "Meerut", "Mawana", "Mawana Kalan", 29.1028, 77.9231, "2026-01-15", 24.12),
    ("Uttar Pradesh", "Meerut", "Rohta", "Rohta", 28.9810, 77.5820, "2026-01-15", 26.80),
    ("Uttar Pradesh", "Meerut", "Rajpura", "Partapur", 28.9320, 77.6540, "2026-01-16", 29.10),
    ("Uttar Pradesh", "Meerut", "Jani Khurd", "Jani", 28.9140, 77.5420, "2026-01-16", 27.35),
    ("Uttar Pradesh", "Meerut", "Machhra", "Machhra", 28.8950, 77.8210, "2026-01-16", 23.50),
    ("Uttar Pradesh", "Meerut", "Kharkhoda", "Kharkhoda", 28.8420, 77.7420, "2026-01-16", 25.60),

    ("Uttar Pradesh", "Varanasi", "Kashi Vidyapeeth", "Shivpur", 25.3520, 82.9640, "2026-01-14", 14.20),
    ("Uttar Pradesh", "Varanasi", "Cholapur", "Cholapur", 25.4310, 83.0420, "2026-01-14", 12.80),
    ("Uttar Pradesh", "Varanasi", "Harahua", "Harahua", 25.3980, 82.9150, "2026-01-14", 15.10),
    ("Uttar Pradesh", "Varanasi", "Pindra", "Pindra", 25.4850, 82.8520, "2026-01-15", 13.90),
    ("Uttar Pradesh", "Varanasi", "Sevapuri", "Sevapuri", 25.2910, 82.7840, "2026-01-15", 16.30),
    ("Uttar Pradesh", "Varanasi", "Arajiline", "Arajiline", 25.2640, 82.8890, "2026-01-15", 14.75),

    ("Uttar Pradesh", "Agra", "Bichpuri", "Bichpuri", 27.1820, 77.9120, "2026-01-18", 34.50),
    ("Uttar Pradesh", "Agra", "Khandauli", "Khandauli", 27.2840, 78.0820, "2026-01-18", 32.10),
    ("Uttar Pradesh", "Agra", "Achhnera", "Achhnera", 27.1810, 77.7610, "2026-01-18", 36.80),
    ("Uttar Pradesh", "Agra", "Barauli Ahir", "Barauli Ahir", 27.1210, 78.0520, "2026-01-19", 31.40),
    ("Uttar Pradesh", "Agra", "Fatehpur Sikri", "Sikri Rural", 27.0940, 77.6680, "2026-01-19", 38.20),
    ("Uttar Pradesh", "Agra", "Shamsabad", "Shamsabad", 27.0210, 78.1250, "2026-01-19", 29.90),

    ("Uttar Pradesh", "Lucknow", "Bakshi Ka Talab", "BKT Village", 26.9820, 80.9230, "2026-01-12", 18.40),
    ("Uttar Pradesh", "Lucknow", "Sarojini Nagar", "Amausi", 26.7620, 80.8740, "2026-01-12", 19.80),
    ("Uttar Pradesh", "Lucknow", "Chinhat", "Chinhat", 26.8840, 81.0120, "2026-01-12", 17.60),
    ("Uttar Pradesh", "Lucknow", "Mohanlalganj", "Mohanlalganj", 26.6810, 80.9950, "2026-01-13", 16.90),
    ("Uttar Pradesh", "Lucknow", "Malihabad", "Malihabad", 26.9210, 80.7120, "2026-01-13", 15.80),
    ("Uttar Pradesh", "Lucknow", "Kakori", "Kakori", 26.8740, 80.8010, "2026-01-13", 17.20),

    ("Uttar Pradesh", "Aligarh", "Koil", "Koil", 27.8920, 78.0840, "2026-01-20", 22.40),
    ("Uttar Pradesh", "Aligarh", "Atrauli", "Atrauli", 28.0310, 78.2910, "2026-01-20", 24.10),
    ("Uttar Pradesh", "Aligarh", "Gabhana", "Gabhana", 28.0050, 77.9240, "2026-01-20", 21.80),
    ("Uttar Pradesh", "Aligarh", "Iglas", "Iglas", 27.7120, 77.9350, "2026-01-21", 26.50),
    ("Uttar Pradesh", "Aligarh", "Khair", "Khair", 27.9420, 77.8420, "2026-01-21", 25.30),

    ("Uttar Pradesh", "Gorakhpur", "Campierganj", "Campierganj", 26.9820, 83.2740, "2026-01-10", 7.80),
    ("Uttar Pradesh", "Gorakhpur", "Pipraich", "Pipraich", 26.8310, 83.5210, "2026-01-10", 6.90),
    ("Uttar Pradesh", "Gorakhpur", "Chargawan", "Chargawan", 26.7910, 83.3920, "2026-01-10", 8.20),
    ("Uttar Pradesh", "Gorakhpur", "Bhathat", "Bhathat", 26.8820, 83.4750, "2026-01-11", 7.40),
    ("Uttar Pradesh", "Gorakhpur", "Sahjanwa", "Sahjanwa", 26.7720, 83.2120, "2026-01-11", 8.90),
    ("Uttar Pradesh", "Gorakhpur", "Bansgaon", "Bansgaon", 26.5610, 83.3540, "2026-01-11", 7.10),

    ("Uttar Pradesh", "Jhansi", "Babina", "Babina", 25.2420, 78.4720, "2026-01-17", 19.50),
    ("Uttar Pradesh", "Jhansi", "Baragaon", "Baragaon", 25.5340, 78.7120, "2026-01-17", 18.20),
    ("Uttar Pradesh", "Jhansi", "Badaagaon", "Parichha", 25.5120, 78.7450, "2026-01-17", 17.80),
    ("Uttar Pradesh", "Jhansi", "Moth", "Moth", 25.7140, 78.9520, "2026-01-17", 20.10),
    ("Uttar Pradesh", "Jhansi", "Mauranipur", "Mauranipur", 25.2410, 79.1450, "2026-01-18", 21.40),

    ("Uttar Pradesh", "Prayagraj", "Karchhana", "Karchhana", 25.2910, 81.9120, "2026-01-15", 14.80),
    ("Uttar Pradesh", "Prayagraj", "Phulpur", "Phulpur", 25.5510, 82.0840, "2026-01-15", 15.30),
    ("Uttar Pradesh", "Prayagraj", "Soraon", "Soraon", 25.5820, 81.8420, "2026-01-15", 13.90),
    ("Uttar Pradesh", "Prayagraj", "Mauaima", "Mauaima", 25.7010, 81.9210, "2026-01-16", 14.40),
    ("Uttar Pradesh", "Prayagraj", "Holagarh", "Holagarh", 25.6420, 81.7950, "2026-01-16", 13.60),
    ("Uttar Pradesh", "Prayagraj", "Jasra", "Jasra", 25.2740, 81.7120, "2026-01-16", 16.20),

    # Punjab
    ("Punjab", "Ludhiana", "Khanna", "Khanna Kalan", 30.7020, 76.2210, "2026-01-20", 35.80),
    ("Punjab", "Ludhiana", "Samrala", "Samrala", 30.8350, 76.1920, "2026-01-20", 32.40),
    ("Punjab", "Ludhiana", "Jagraon", "Jagraon", 30.7840, 75.4810, "2026-01-20", 38.60),
    ("Punjab", "Ludhiana", "Ludhiana-1", "Gill", 30.8620, 75.8540, "2026-01-21", 34.20),
    ("Punjab", "Ludhiana", "Ludhiana-2", "Mangat", 30.9520, 75.9120, "2026-01-21", 31.90),
    ("Punjab", "Ludhiana", "Dehlon", "Dehlon", 30.7710, 75.8920, "2026-01-21", 36.10),

    ("Punjab", "Sangrur", "Sangrur", "Bhawanigarh", 30.2840, 76.0420, "2026-01-22", 42.50),
    ("Punjab", "Sangrur", "Sunam", "Sunam", 30.1250, 75.8010, "2026-01-22", 44.80),
    ("Punjab", "Sangrur", "Dhuri", "Dhuri", 30.3710, 75.8720, "2026-01-22", 39.40),
    ("Punjab", "Sangrur", "Malerkotla", "Amargarh", 30.6120, 75.9750, "2026-01-23", 37.80),
    ("Punjab", "Sangrur", "Lehragaga", "Lehra", 29.9340, 75.8120, "2026-01-23", 41.20),
    ("Punjab", "Sangrur", "Moonak", "Moonak", 29.8210, 75.8940, "2026-01-23", 40.60),

    ("Punjab", "Jalandhar", "Jalandhar East", "Jamsher", 31.2640, 75.6420, "2026-01-18", 29.40),
    ("Punjab", "Jalandhar", "Jalandhar West", "Lambra", 31.2820, 75.5120, "2026-01-18", 28.10),
    ("Punjab", "Jalandhar", "Nakodar", "Nakodar", 31.1250, 75.4740, "2026-01-18", 31.50),
    ("Punjab", "Jalandhar", "Shahkot", "Shahkot", 31.0820, 75.3410, "2026-01-19", 27.80),
    ("Punjab", "Jalandhar", "Phillaur", "Phillaur", 31.0210, 75.7840, "2026-01-19", 26.90),
    ("Punjab", "Jalandhar", "Nurmahal", "Nurmahal", 31.0940, 75.5920, "2026-01-19", 30.20),

    ("Punjab", "Amritsar", "Ajnala", "Ajnala", 31.8420, 74.7620, "2026-01-19", 23.40),
    ("Punjab", "Amritsar", "Majitha", "Majitha", 31.7610, 74.9540, "2026-01-19", 25.10),
    ("Punjab", "Amritsar", "Jandiala", "Jandiala Guru", 31.5620, 75.0210, "2026-01-19", 26.80),
    ("Punjab", "Amritsar", "Verka", "Verka", 31.6740, 74.9120, "2026-01-20", 24.50),
    ("Punjab", "Amritsar", "Rayya", "Rayya", 31.5410, 75.2240, "2026-01-20", 27.20),
    ("Punjab", "Amritsar", "Chogawan", "Chogawan", 31.7120, 74.6840, "2026-01-20", 22.90),

    ("Punjab", "Bathinda", "Bathinda", "Bhucho Mandi", 30.2610, 75.0520, "2026-01-21", 33.60),
    ("Punjab", "Bathinda", "Talwandi Sabo", "Talwandi Sabo", 29.9840, 75.0840, "2026-01-21", 36.40),
    ("Punjab", "Bathinda", "Rampura", "Rampura Phul", 30.2740, 75.2410, "2026-01-21", 32.10),
    ("Punjab", "Bathinda", "Maur", "Maur Mandi", 30.0820, 75.2340, "2026-01-22", 34.80),
    ("Punjab", "Bathinda", "Bhagta Bhaika", "Bhagta", 30.4520, 75.1210, "2026-01-22", 31.20),

    ("Punjab", "Patiala", "Patiala", "Sanour", 30.3010, 76.4520, "2026-01-22", 33.10),
    ("Punjab", "Patiala", "Nabha", "Nabha", 30.3740, 76.1520, "2026-01-22", 35.40),
    ("Punjab", "Patiala", "Rajpura", "Rajpura", 30.4820, 76.5940, "2026-01-23", 29.80),
    ("Punjab", "Patiala", "Samana", "Samana", 30.1540, 76.1920, "2026-01-23", 36.70),
    ("Punjab", "Patiala", "Patran", "Patran", 29.9520, 76.0610, "2026-01-23", 38.20),

    # Rajasthan
    ("Rajasthan", "Jaipur", "Amber", "Amer Village", 26.9850, 75.8510, "2026-01-16", 52.40),
    ("Rajasthan", "Jaipur", "Jhotwara", "Sirsi", 26.9240, 75.7210, "2026-01-16", 56.80),
    ("Rajasthan", "Jaipur", "Sanganer", "Sanganer", 26.8120, 75.7840, "2026-01-16", 58.20),
    ("Rajasthan", "Jaipur", "Bassi", "Bassi", 26.8340, 76.0420, "2026-01-17", 49.10),
    ("Rajasthan", "Jaipur", "Chaksu", "Chaksu", 26.6020, 75.9520, "2026-01-17", 46.50),
    ("Rajasthan", "Jaipur", "Govindgarh", "Govindgarh", 27.2340, 75.6620, "2026-01-17", 54.70),
    ("Rajasthan", "Jaipur", "Shahpura", "Shahpura", 27.3910, 75.9610, "2026-01-18", 51.30),
    ("Rajasthan", "Jaipur", "Jamwa Ramgarh", "Ramgarh", 27.0250, 76.0120, "2026-01-18", 48.90),

    ("Rajasthan", "Jodhpur", "Mandore", "Mandore", 26.3540, 73.0420, "2026-01-15", 48.20),
    ("Rajasthan", "Jodhpur", "Luni", "Salawas", 26.1520, 73.0120, "2026-01-15", 45.60),
    ("Rajasthan", "Jodhpur", "Bilara", "Bilara", 26.1820, 73.7120, "2026-01-15", 53.40),
    ("Rajasthan", "Jodhpur", "Osian", "Osian", 26.7240, 72.9050, "2026-01-16", 57.10),
    ("Rajasthan", "Jodhpur", "Shergarh", "Shergarh", 26.3210, 72.2840, "2026-01-16", 61.50),
    ("Rajasthan", "Jodhpur", "Balesar", "Balesar", 26.4120, 72.4820, "2026-01-16", 59.80),

    ("Rajasthan", "Jaisalmer", "Jaisalmer", "Badabagh", 26.9420, 70.8920, "2026-01-14", 68.50),
    ("Rajasthan", "Jaisalmer", "Sankra", "Ramdevra", 26.9920, 71.9120, "2026-01-14", 62.10),
    ("Rajasthan", "Jaisalmer", "Sam", "Sam Dunes", 26.8310, 70.5120, "2026-01-14", 74.80),
    ("Rajasthan", "Jaisalmer", "Pokhran", "Pokhran Rural", 26.9210, 71.9150, "2026-01-15", 59.40),
    ("Rajasthan", "Jaisalmer", "Fatehgarh", "Fatehgarh", 26.4820, 71.2140, "2026-01-15", 64.70),

    ("Rajasthan", "Bikaner", "Bikaner", "Napasar", 27.9620, 73.5420, "2026-01-17", 58.60),
    ("Rajasthan", "Bikaner", "Nokha", "Nokha Mandi", 27.6020, 73.4210, "2026-01-17", 63.20),
    ("Rajasthan", "Bikaner", "Kolayat", "Kolayat", 27.8420, 72.9520, "2026-01-17", 55.40),
    ("Rajasthan", "Bikaner", "Lunkaransar", "Lunkaransar", 28.5020, 73.7420, "2026-01-18", 52.80),
    ("Rajasthan", "Bikaner", "Sri Dungargarh", "Dungargarh", 28.1020, 74.0120, "2026-01-18", 60.10),

    ("Rajasthan", "Sikar", "Sikar", "Piprali", 27.6320, 75.2140, "2026-01-19", 64.20),
    ("Rajasthan", "Sikar", "Fatehpur", "Fatehpur", 27.9840, 74.9520, "2026-01-19", 61.80),
    ("Rajasthan", "Sikar", "Laxmangarh", "Laxmangarh", 27.8210, 75.0240, "2026-01-19", 66.50),
    ("Rajasthan", "Sikar", "Neem Ka Thana", "Neem Ka Thana", 27.7420, 75.7820, "2026-01-20", 59.20),
    ("Rajasthan", "Sikar", "Danta Ramgarh", "Danta", 27.3240, 75.1840, "2026-01-20", 68.10),
    ("Rajasthan", "Sikar", "Sri Madhopur", "Ringas", 27.3620, 75.5640, "2026-01-20", 62.40),

    ("Rajasthan", "Alwar", "Alwar", "Malakhera", 27.4210, 76.6210, "2026-01-21", 41.50),
    ("Rajasthan", "Alwar", "Tijara", "Tijara", 27.9320, 76.8540, "2026-01-21", 38.20),
    ("Rajasthan", "Alwar", "Kishangarh Bas", "Khairthal", 27.7940, 76.6420, "2026-01-21", 44.80),
    ("Rajasthan", "Alwar", "Behror", "Neemrana", 27.9820, 76.3840, "2026-01-22", 49.30),
    ("Rajasthan", "Alwar", "Thanagazi", "Thanagazi", 27.3940, 76.3210, "2026-01-22", 42.10),
    ("Rajasthan", "Alwar", "Rajgarh", "Rajgarh", 27.2340, 76.6320, "2026-01-22", 46.70),

    # Maharashtra
    ("Maharashtra", "Pune", "Haveli", "Wagholi", 18.5810, 73.9820, "2026-01-15", 14.80),
    ("Maharashtra", "Pune", "Baramati", "Baramati Rural", 18.1520, 74.5820, "2026-01-15", 18.20),
    ("Maharashtra", "Pune", "Shirur", "Shirur", 18.8240, 74.3750, "2026-01-15", 16.50),
    ("Maharashtra", "Pune", "Junnar", "Narayangaon", 19.1210, 73.9740, "2026-01-16", 12.90),
    ("Maharashtra", "Pune", "Khed", "Chakan", 18.7540, 73.8520, "2026-01-16", 15.30),
    ("Maharashtra", "Pune", "Indapur", "Bhigwan", 18.2840, 74.7720, "2026-01-16", 19.40),
    ("Maharashtra", "Pune", "Daund", "Patas", 18.4520, 74.5120, "2026-01-16", 17.10),

    ("Maharashtra", "Nagpur", "Nagpur Rural", "Kamptee Rural", 21.2240, 79.1950, "2026-01-18", 11.20),
    ("Maharashtra", "Nagpur", "Kamptee", "Kamptee", 21.2320, 79.2010, "2026-01-18", 10.80),
    ("Maharashtra", "Nagpur", "Hingna", "Butibori", 20.9240, 78.9950, "2026-01-18", 12.50),
    ("Maharashtra", "Nagpur", "Umred", "Umred", 20.8520, 79.3240, "2026-01-19", 9.80),
    ("Maharashtra", "Nagpur", "Saoner", "Saoner", 21.3840, 78.9120, "2026-01-19", 11.90),
    ("Maharashtra", "Nagpur", "Katol", "Katol", 21.2750, 78.5840, "2026-01-19", 13.40),

    ("Maharashtra", "Nashik", "Nashik", "Deolali", 19.9520, 73.8340, "2026-01-17", 13.80),
    ("Maharashtra", "Nashik", "Dindori", "Dindori", 20.2010, 73.8350, "2026-01-17", 11.50),
    ("Maharashtra", "Nashik", "Niphad", "Ozar", 20.0940, 73.9520, "2026-01-17", 15.20),
    ("Maharashtra", "Nashik", "Sinnar", "Musgaon", 19.8520, 74.0120, "2026-01-18", 17.60),
    ("Maharashtra", "Nashik", "Malegaon", "Malegaon Camp", 20.5540, 74.5320, "2026-01-18", 16.10),
    ("Maharashtra", "Nashik", "Yeola", "Yeola", 20.0420, 74.4850, "2026-01-18", 18.90),

    ("Maharashtra", "Chhatrapati Sambhajinagar", "Aurangabad", "Chikalthana", 19.8720, 75.3840, "2026-01-20", 21.40),
    ("Maharashtra", "Chhatrapati Sambhajinagar", "Paithan", "Paithan", 19.4820, 75.3850, "2026-01-20", 23.80),
    ("Maharashtra", "Chhatrapati Sambhajinagar", "Gangapur", "Gangapur", 19.7010, 75.0120, "2026-01-20", 22.10),
    ("Maharashtra", "Chhatrapati Sambhajinagar", "Vaijapur", "Vaijapur", 19.9240, 74.7320, "2026-01-21", 24.60),
    ("Maharashtra", "Chhatrapati Sambhajinagar", "Kannad", "Kannad", 20.2640, 75.1350, "2026-01-21", 19.80),
    ("Maharashtra", "Chhatrapati Sambhajinagar", "Sillod", "Sillod", 20.3050, 75.6540, "2026-01-21", 20.50),

    ("Maharashtra", "Ahmednagar", "Nagar", "Kedgaon", 19.0720, 74.7120, "2026-01-19", 22.80),
    ("Maharashtra", "Ahmednagar", "Rahata", "Shirdi", 19.7640, 74.4750, "2026-01-19", 26.40),
    ("Maharashtra", "Ahmednagar", "Shrirampur", "Shrirampur", 19.6150, 74.6540, "2026-01-19", 24.10),
    ("Maharashtra", "Ahmednagar", "Sangamner", "Sangamner", 19.5740, 74.2120, "2026-01-20", 25.30),
    ("Maharashtra", "Ahmednagar", "Kopargaon", "Kopargaon", 19.8920, 74.4840, "2026-01-20", 23.50),
    ("Maharashtra", "Ahmednagar", "Newasa", "Newasa", 19.5540, 74.9210, "2026-01-20", 21.90),

    ("Maharashtra", "Solapur", "North Solapur", "Bale", 17.7120, 75.9120, "2026-01-22", 18.50),
    ("Maharashtra", "Solapur", "South Solapur", "Mandrup", 17.5120, 75.8450, "2026-01-22", 19.80),
    ("Maharashtra", "Solapur", "Pandharpur", "Pandharpur Rural", 17.6740, 75.3240, "2026-01-22", 21.20),
    ("Maharashtra", "Solapur", "Barshi", "Barshi", 18.2340, 75.6920, "2026-01-23", 22.40),
    ("Maharashtra", "Solapur", "Mohol", "Mohol", 17.8120, 75.5540, "2026-01-23", 20.10),
    ("Maharashtra", "Solapur", "Karmala", "Karmala", 18.4120, 75.2010, "2026-01-23", 23.70),

    # Haryana
    ("Haryana", "Karnal", "Karnal", "Karnal Rural", 29.6920, 76.9820, "2026-01-16", 26.40),
    ("Haryana", "Karnal", "Gharaunda", "Gharaunda", 29.5420, 76.9740, "2026-01-16", 24.80),
    ("Haryana", "Karnal", "Nilokheri", "Taraori", 29.8010, 76.9240, "2026-01-16", 28.20),
    ("Haryana", "Karnal", "Indri", "Indri", 29.8820, 77.0640, "2026-01-17", 22.50),
    ("Haryana", "Karnal", "Assandh", "Assandh", 29.5240, 76.6020, "2026-01-17", 30.10),
    ("Haryana", "Karnal", "Nissing", "Nissing", 29.6640, 76.7840, "2026-01-17", 27.30),

    ("Haryana", "Kurukshetra", "Thanesar", "Thanesar", 29.9720, 76.8420, "2026-01-18", 31.50),
    ("Haryana", "Kurukshetra", "Pehowa", "Pehowa", 29.9820, 76.5840, "2026-01-18", 34.20),
    ("Haryana", "Kurukshetra", "Shahbad", "Shahbad Markanda", 30.1740, 76.8720, "2026-01-18", 32.80),
    ("Haryana", "Kurukshetra", "Ladwa", "Ladwa", 29.9950, 77.0420, "2026-01-19", 29.40),
    ("Haryana", "Kurukshetra", "Babain", "Babain", 30.0820, 76.9840, "2026-01-19", 30.70),

    ("Haryana", "Sirsa", "Sirsa", "Ding", 29.5340, 75.0320, "2026-01-20", 22.80),
    ("Haryana", "Sirsa", "Rania", "Rania", 29.5240, 74.8340, "2026-01-20", 21.40),
    ("Haryana", "Sirsa", "Ellenabad", "Ellenabad", 29.4520, 74.6540, "2026-01-20", 24.10),
    ("Haryana", "Sirsa", "Dabwali", "Mandi Dabwali", 29.9620, 74.7210, "2026-01-21", 20.50),
    ("Haryana", "Sirsa", "Nathusari Chopta", "Chopta", 29.3840, 74.9820, "2026-01-21", 23.60),

    ("Haryana", "Gurugram", "Gurugram", "Badshahpur", 28.3940, 77.0540, "2026-01-22", 48.90),
    ("Haryana", "Gurugram", "Sohna", "Sohna Rural", 28.2520, 77.0640, "2026-01-22", 44.50),
    ("Haryana", "Gurugram", "Pataudi", "Pataudi", 28.3240, 76.7820, "2026-01-22", 42.10),
    ("Haryana", "Gurugram", "Farrukhnagar", "Farrukhnagar", 28.4520, 76.8240, "2026-01-23", 46.30),

    ("Haryana", "Hisar", "Hisar-1", "Satrod", 29.1540, 75.7240, "2026-01-21", 18.90),
    ("Haryana", "Hisar", "Hansi", "Hansi Rural", 29.1020, 75.9640, "2026-01-21", 17.50),
    ("Haryana", "Hisar", "Barwala", "Barwala", 29.3740, 75.9120, "2026-01-21", 19.80),
    ("Haryana", "Hisar", "Narnaund", "Narnaund", 29.2240, 76.1420, "2026-01-22", 16.40),
    ("Haryana", "Hisar", "Adampur", "Mandi Adampur", 29.2840, 75.4520, "2026-01-22", 21.20),

    # Madhya Pradesh
    ("Madhya Pradesh", "Indore", "Indore", "Rau", 22.6240, 75.8010, "2026-01-14", 32.40),
    ("Madhya Pradesh", "Indore", "Depalpur", "Depalpur", 22.8520, 75.5540, "2026-01-14", 34.80),
    ("Madhya Pradesh", "Indore", "Mhow", "Harsola", 22.5540, 75.7620, "2026-01-14", 29.10),
    ("Madhya Pradesh", "Indore", "Sanwer", "Sanwer", 22.9740, 75.8340, "2026-01-15", 36.50),

    ("Madhya Pradesh", "Ujjain", "Ujjain", "Tajpur", 23.1840, 75.7740, "2026-01-16", 31.20),
    ("Madhya Pradesh", "Ujjain", "Badnagar", "Badnagar", 23.0150, 75.3840, "2026-01-16", 33.90),
    ("Madhya Pradesh", "Ujjain", "Khachrod", "Khachrod", 23.4240, 75.2840, "2026-01-16", 30.50),
    ("Madhya Pradesh", "Ujjain", "Mahidpur", "Mahidpur", 23.4840, 75.6540, "2026-01-17", 28.70),
    ("Madhya Pradesh", "Ujjain", "Tarana", "Tarana", 23.2340, 76.0420, "2026-01-17", 29.80),

    ("Madhya Pradesh", "Bhopal", "Phanda", "Misrod", 23.1520, 77.4720, "2026-01-15", 16.40),
    ("Madhya Pradesh", "Bhopal", "Berasia", "Berasia", 23.6340, 77.4320, "2026-01-15", 18.90),
    ("Madhya Pradesh", "Bhopal", "Huzur", "Bairagarh", 23.2840, 77.3420, "2026-01-15", 15.20),

    ("Madhya Pradesh", "Jabalpur", "Panagar", "Panagar", 23.2940, 79.9840, "2026-01-18", 12.40),
    ("Madhya Pradesh", "Jabalpur", "Sihora", "Sihora", 23.4840, 80.1240, "2026-01-18", 14.10),
    ("Madhya Pradesh", "Jabalpur", "Majholi", "Majholi", 23.5020, 79.9120, "2026-01-18", 13.50),
    ("Madhya Pradesh", "Jabalpur", "Patan", "Patan", 23.2840, 79.6950, "2026-01-19", 15.80),
    ("Madhya Pradesh", "Jabalpur", "Shahpura", "Bhitoni", 23.1420, 79.6640, "2026-01-19", 14.70),

    ("Madhya Pradesh", "Gwalior", "Gwalior", "Morar Rural", 26.2240, 78.2240, "2026-01-19", 24.50),
    ("Madhya Pradesh", "Gwalior", "Dabra", "Dabra", 25.8940, 78.3340, "2026-01-19", 22.80),
    ("Madhya Pradesh", "Gwalior", "Bhitarwar", "Bhitarwar", 25.7940, 78.1240, "2026-01-20", 21.20),
    ("Madhya Pradesh", "Gwalior", "Ghatigaon", "Mohna", 26.0420, 77.9540, "2026-01-20", 25.90),

    # Bihar
    ("Bihar", "Patna", "Patna Sadar", "Digha", 25.6420, 85.1020, "2026-01-12", 7.80),
    ("Bihar", "Patna", "Danapur", "Danapur Nizamat", 25.6340, 85.0420, "2026-01-12", 8.20),
    ("Bihar", "Patna", "Phulwari Sharif", "Phulwari", 25.5740, 85.0820, "2026-01-12", 9.10),
    ("Bihar", "Patna", "Bikram", "Bikram", 25.4420, 84.8540, "2026-01-13", 10.40),
    ("Bihar", "Patna", "Barh", "Barh Rural", 25.4840, 85.7120, "2026-01-13", 6.90),
    ("Bihar", "Patna", "Bihta", "Bihta", 25.5640, 84.8720, "2026-01-13", 8.70),

    ("Bihar", "Gaya", "Gaya Town", "Kendui", 24.7920, 85.0040, "2026-01-14", 12.80),
    ("Bihar", "Gaya", "Bodh Gaya", "Bodh Gaya Rural", 24.6950, 84.9920, "2026-01-14", 11.40),
    ("Bihar", "Gaya", "Manpur", "Manpur", 24.7840, 85.0340, "2026-01-14", 13.20),
    ("Bihar", "Gaya", "Tekari", "Tekari", 24.9340, 84.8340, "2026-01-15", 14.50),
    ("Bihar", "Gaya", "Sherghati", "Sherghati", 24.5740, 84.7920, "2026-01-15", 10.90),
    ("Bihar", "Gaya", "Wazirganj", "Wazirganj", 24.8020, 85.2420, "2026-01-15", 12.10),

    ("Bihar", "Muzaffarpur", "Musahari", "Musahari", 26.1120, 85.4210, "2026-01-16", 6.80),
    ("Bihar", "Muzaffarpur", "Kanti", "Kanti", 26.1950, 85.3020, "2026-01-16", 7.20),
    ("Bihar", "Muzaffarpur", "Motipur", "Motipur", 26.2740, 85.1840, "2026-01-16", 6.40),
    ("Bihar", "Muzaffarpur", "Marwan", "Marwan", 26.1540, 85.2420, "2026-01-17", 7.50),
    ("Bihar", "Muzaffarpur", "Kurhani", "Kurhani", 25.9920, 85.3840, "2026-01-17", 8.10),
    ("Bihar", "Muzaffarpur", "Sakra", "Sakra", 26.0420, 85.5540, "2026-01-17", 7.90),

    ("Bihar", "Bhagalpur", "Jagdishpur", "Jagdishpur", 25.2120, 87.0120, "2026-01-18", 7.40),
    ("Bihar", "Bhagalpur", "Nathnagar", "Champanagar", 25.2420, 86.9420, "2026-01-18", 6.80),
    ("Bihar", "Bhagalpur", "Sabour", "Sabour", 25.2340, 87.0540, "2026-01-18", 7.90),
    ("Bihar", "Bhagalpur", "Sultanganj", "Sultanganj", 25.2440, 86.7340, "2026-01-19", 8.20),
    ("Bihar", "Bhagalpur", "Kahalgaon", "Kahalgaon", 25.2640, 87.2420, "2026-01-19", 6.50),

    ("Bihar", "Nalanda", "Biharsharif", "Sohsarai", 25.1950, 85.5120, "2026-01-20", 9.80),
    ("Bihar", "Nalanda", "Rajgir", "Rajgir Rural", 25.0240, 85.4210, "2026-01-20", 11.20),
    ("Bihar", "Nalanda", "Harnaut", "Harnaut", 25.3740, 85.5340, "2026-01-20", 8.90),
    ("Bihar", "Nalanda", "Hilsa", "Hilsa", 25.3120, 85.2840, "2026-01-21", 9.40),
    ("Bihar", "Nalanda", "Islampur", "Islampur", 25.1420, 85.2140, "2026-01-21", 10.60),
    ("Bihar", "Nalanda", "Giriyak", "Pawapuri", 25.0920, 85.5340, "2026-01-21", 10.10),
]


def generate_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=landscape(letter),
        leftMargin=20,
        rightMargin=20,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="HeaderTitle",
        parent=styles["Heading1"],
        fontSize=14,
        leading=16,
        textColor=colors.HexColor("#0D47A1"),
        alignment=1
    )
    sub_style = ParagraphStyle(
        name="HeaderSub",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#333333"),
        alignment=1
    )
    cell_style = ParagraphStyle(
        name="CellText",
        parent=styles["Normal"],
        fontSize=8,
        leading=10
    )
    hdr_cell_style = ParagraphStyle(
        name="HeaderCellText",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName="Helvetica-Bold"
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("<b>CENTRAL GROUND WATER BOARD (CGWB) & NATIONAL WATER INFORMATICS CENTRE</b>", title_style))
    story.append(Paragraph("<b>GROUND WATER LEVEL MONITORING STATIONS REPORT - JANUARY 2026</b>", sub_style))
    story.append(Paragraph("Depth to Water Level (DTWL in meters below ground level - mbgl)", sub_style))
    story.append(Spacer(1, 10))

    # Table Header
    headers = [
        "State / UT",
        "District",
        "Block / Tehsil",
        "Village / Station",
        "Latitude",
        "Longitude",
        "Record Date",
        "DTWL (m bgl)"
    ]

    table_data = [[Paragraph(h, hdr_cell_style) for h in headers]]

    for row in DATA_ROWS:
        state, dist, block, village, lat, lon, rdate, dtwl = row
        table_data.append([
            Paragraph(state, cell_style),
            Paragraph(dist, cell_style),
            Paragraph(block, cell_style),
            Paragraph(village, cell_style),
            Paragraph(f"{lat:.4f}", cell_style),
            Paragraph(f"{lon:.4f}", cell_style),
            Paragraph(rdate, cell_style),
            Paragraph(f"{dtwl:.2f}", cell_style)
        ])

    col_widths = [110, 95, 95, 110, 70, 70, 80, 80]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0288D1")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#B0BEC5")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F9FC")]),
    ]))

    story.append(t)
    doc.build(story)
    print(f"Generated CGWB Monitoring Report PDF at: {OUTPUT_PDF}")


if __name__ == "__main__":
    generate_pdf()
