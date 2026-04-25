import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta

# Thêm đường dẫn gốc vào sys.path để nhận diện module 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import Village, AQILog
from app.services.data_ingestion import calc_sub_aqi, get_aqi_level

class AQICollector:
    AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    
    AIR_COLS = {
        "pm2_5": "pm25", "pm10": "pm10", "carbon_monoxide": "co",
        "nitrogen_dioxide": "no2", "sulphur_dioxide": "so2",
        "ozone": "o3", "aerosol_optical_depth": "aod", "dust": "dust"
    }
    
    WEATHER_COLS = {
        "temperature_2m": "temperature", "relative_humidity_2m": "humidity",
        "wind_speed_10m": "wind_speed", "wind_direction_10m": "wind_dir",
        "surface_pressure": "pressure", "precipitation": "precipitation",
        "cloud_cover": "cloud_cover", "visibility": "visibility"
    }

    @staticmethod
    def fetch_live_data():
        """Lấy dữ liệu không khí và thời tiết mới nhất cho tất cả làng nghề"""
        print(f"🌐 [{datetime.now()}] Bắt đầu thu thập dữ liệu trực tuyến...")
        
        with Session(engine) as session:
            villages = session.exec(select(Village)).all()
            if not villages:
                print("⚠️ Không tìm thấy danh sách làng nghề trong DB. Hãy chạy data_ingestion trước.")
                return

            for v in villages:
                try:
                    # 1. Lấy dữ liệu Không khí
                    air_params = {
                        "latitude": v.lat, "longitude": v.lon,
                        "hourly": ",".join(AQICollector.AIR_COLS.keys()),
                        "timezone": "Asia/Ho_Chi_Minh", "forecast_days": 1
                    }
                    air_resp = requests.get(AQICollector.AIR_URL, params=air_params, timeout=15)
                    air_resp.raise_for_status()
                    air_data = air_resp.json().get("hourly", {})
                    
                    # 2. Lấy dữ liệu Thời tiết
                    weather_params = {
                        "latitude": v.lat, "longitude": v.lon,
                        "hourly": ",".join(AQICollector.WEATHER_COLS.keys()),
                        "timezone": "Asia/Ho_Chi_Minh", "forecast_days": 1
                    }
                    weather_resp = requests.get(AQICollector.WEATHER_URL, params=weather_params, timeout=15)
                    weather_resp.raise_for_status()
                    weather_data = weather_resp.json().get("hourly", {})
                    
                    if not air_data or not weather_data: continue
                    
                    # Gộp dữ liệu
                    df = pd.DataFrame({"timestamp": pd.to_datetime(air_data["time"])})
                    
                    for api_col, db_col in AQICollector.AIR_COLS.items():
                        if api_col in air_data: df[db_col] = air_data[api_col]
                        
                    for api_col, db_col in AQICollector.WEATHER_COLS.items():
                        if api_col in weather_data: df[db_col] = weather_data[api_col]
                    
                    # Lấy bản ghi giờ hiện tại
                    current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
                    latest_row = df[df['timestamp'] <= current_hour].iloc[-1:]
                    
                    if not latest_row.empty:
                        row = latest_row.iloc[0]
                        
                        # Tính AQI
                        aqi_val = max([calc_sub_aqi(row.get(p, 0), p) for p in ["pm25", "pm10", "so2", "no2", "co", "o3"]])
                        
                        # Check exist
                        existing = session.exec(select(AQILog).where(
                            AQILog.village_name == v.name, AQILog.timestamp == row['timestamp'].to_pydatetime()
                        )).first()
                        
                        if not existing:
                            log = AQILog(
                                village_name=v.name, timestamp=row['timestamp'].to_pydatetime(),
                                pm25=row['pm25'], pm10=row.get('pm10'), co=row.get('co'),
                                no2=row.get('no2'), so2=row.get('so2'), o3=row.get('o3'),
                                aod=row.get('aod'), dust=row.get('dust'),
                                temperature=row.get('temperature'), humidity=row.get('humidity'),
                                wind_speed=row.get('wind_speed'), wind_dir=row.get('wind_dir'),
                                pressure=row.get('pressure'), precipitation=row.get('precipitation'),
                                cloud_cover=row.get('cloud_cover'), visibility=row.get('visibility'),
                                aqi=aqi_val, level=get_aqi_level(aqi_val)
                            )
                            session.add(log)
                            print(f"✅ Đã cập nhật Không khí + Thời tiết cho {v.name}")
                    
                except Exception as e:
                    print(f"❌ Lỗi khi lấy dữ liệu cho {v.name}: {e}")
            
            session.commit()
            print(f"🏁 Hoàn thành chu kỳ cập nhật.")

if __name__ == "__main__":
    AQICollector.fetch_live_data()
