import os
import sys
import pandas as pd
import yaml
from datetime import datetime

# Thêm đường dẫn gốc vào sys.path để nhận diện module 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import Village, AQILog
import numpy as np

# AQI Calculation Constants (QCVN 05:2023)
AQI_BREAKPOINTS = {
    "pm25": [(0.0, 25.0, 0, 50), (25.1, 50.0, 51, 100), (50.1, 150.0, 101, 150), (150.1, 250.0, 151, 200), (250.1, 350.0, 201, 300), (350.1, 500.0, 301, 400)],
    "pm10": [(0, 50, 0, 50), (51, 150, 51, 100), (151, 250, 101, 150), (251, 350, 151, 200), (351, 420, 201, 300), (421, 600, 301, 400)],
    "so2": [(0, 50, 0, 50), (51, 150, 51, 100), (151, 500, 101, 150), (501, 750, 151, 200), (751, 1000, 201, 300), (1001, 1500, 301, 400)],
    "no2": [(0, 40, 0, 50), (41, 100, 51, 100), (101, 200, 101, 150), (201, 400, 151, 200), (401, 700, 201, 300), (701, 1200, 301, 400)],
    "co": [(0, 5, 0, 50), (5.1, 15, 51, 100), (15.1, 25, 101, 150), (25.1, 50, 151, 200), (50.1, 150, 201, 300), (150.1, 500, 301, 400)],
    "o3": [(0, 60, 0, 50), (61, 120, 51, 100), (121, 180, 101, 150), (181, 240, 151, 200), (241, 400, 201, 300), (401, 800, 301, 400)],
}

AQI_LEVELS = [
    (0, 50, "Tốt"), (51, 100, "Trung bình"), (101, 150, "Kém (nhạy cảm)"),
    (151, 200, "Kém"), (201, 300, "Rất xấu"), (301, 500, "Nguy hại")
]

def calc_sub_aqi(concentration, pollutant):
    if pd.isna(concentration) or concentration < 0: return np.nan
    breakpoints = AQI_BREAKPOINTS.get(pollutant)
    if not breakpoints: return np.nan
    if pollutant == "co": concentration /= 1000.0
    for (c_lo, c_hi, aqi_lo, aqi_hi) in breakpoints:
        if c_lo <= concentration <= c_hi:
            return ((aqi_hi - aqi_lo) / (c_hi - c_lo)) * (concentration - c_lo) + aqi_lo
    return 500.0

def get_aqi_level(aqi):
    if pd.isna(aqi): return "Không xác định"
    for lo, hi, label in AQI_LEVELS:
        if lo <= aqi <= hi: return label
    return "Nguy hại"

def import_villages(yaml_path: str):
    print(f"📦 Importing villages from {yaml_path}...")
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    with Session(engine) as session:
        for v_data in data['villages']:
            # Check if exists
            existing = session.exec(select(Village).where(Village.name == v_data['name'])).first()
            if not existing:
                village = Village(
                    name=v_data['name'],
                    location=v_data['location'],
                    lat=v_data['lat'],
                    lon=v_data['lon'],
                    pollution_level=v_data['pollution_level'],
                    is_baseline=v_data.get('is_baseline', False),
                    note=v_data.get('note')
                )
                session.add(village)
        session.commit()
    print("✅ Villages imported.")

def import_aqi_data(csv_dir: str):
    print(f"📊 Importing AQI data from {csv_dir}...")
    
    # Map for encoding issues (Da H?i -> Đa Hội, etc.)
    # Based on the villages in YAML
    with Session(engine) as session:
        villages = session.exec(select(Village)).all()
        village_names = [v.name for v in villages]
    
    # Simple normalization for matching
    def normalize(s):
        return s.replace('?', '').strip().lower() if isinstance(s, str) else ''

    for file in os.listdir(csv_dir):
        if file.endswith(".csv"):
            file_path = os.path.join(csv_dir, file)
            print(f"📄 Processing {file}...")
            df = pd.read_csv(file_path)
            
            # Data cleaning and AQI calculation
            df['aqi'] = df.apply(lambda r: max([calc_sub_aqi(r.get(p, 0), p) for p in ["pm25", "pm10", "so2", "no2", "co", "o3"]]), axis=1)
            df['level'] = df['aqi'].apply(get_aqi_level)
            
            # Batch insert
            with Session(engine) as session:
                logs = []
                for _, row in df.iterrows():
                    # Attempt to match village name
                    raw_name = row['village']
                    matched_name = None
                    for v_name in village_names:
                        # If the raw name is a substring or similar (handling the ? issue)
                        if normalize(v_name).startswith(normalize(raw_name)) or normalize(raw_name).startswith(normalize(v_name)[:5]):
                            matched_name = v_name
                            break
                    
                    if not matched_name:
                        continue # Skip unknown villages
                        
                    log = AQILog(
                        village_name=matched_name,
                        timestamp=pd.to_datetime(row['timestamp']),
                        pm25=row['pm25'],
                        pm10=row.get('pm10'),
                        co=row.get('co'),
                        no2=row.get('no2'),
                        so2=row.get('so2'),
                        o3=row.get('o3'),
                        aqi=row['aqi'],
                        level=row['level']
                    )
                    logs.append(log)
                    
                    if len(logs) >= 1000:
                        session.add_all(logs)
                        session.commit()
                        logs = []
                
                if logs:
                    session.add_all(logs)
                    session.commit()
    print("✅ AQI data imported.")

if __name__ == "__main__":
    # Tự động xác định thư mục gốc của dự án (parent của folder 'app')
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
    
    # Đường dẫn trong Docker thường là /app
    if os.path.exists("/app"):
        BASE_DIR = "/app"
        
    yaml_file = os.path.join(BASE_DIR, "configs", "villages.yaml")
    csv_folder = os.path.join(BASE_DIR, "data", "raw", "air")
    
    print(f"🔍 Base directory: {BASE_DIR}")
    import_villages(yaml_file)
    import_aqi_data(csv_folder)
