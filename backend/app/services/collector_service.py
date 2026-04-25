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
    BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
    
    COL_MAPPING = {
        "pm2_5": "pm25",
        "pm10": "pm10",
        "carbon_monoxide": "co",
        "nitrogen_dioxide": "no2",
        "sulphur_dioxide": "so2",
        "ozone": "o3"
    }

    @staticmethod
    def fetch_live_data():
        """Lấy dữ liệu mới nhất từ Internet cho tất cả làng nghề và lưu vào DB"""
        print(f"🌐 [{datetime.now()}] Bắt đầu thu thập dữ liệu trực tuyến...")
        
        with Session(engine) as session:
            villages = session.exec(select(Village)).all()
            if not villages:
                print("⚠️ Không tìm thấy danh sách làng nghề trong DB. Hãy chạy data_ingestion trước.")
                return

            for v in villages:
                try:
                    params = {
                        "latitude": v.lat,
                        "longitude": v.lon,
                        "hourly": ",".join(AQICollector.COL_MAPPING.keys()),
                        "timezone": "Asia/Ho_Chi_Minh",
                        "forecast_days": 1 # Lấy dữ liệu của ngày hiện tại
                    }
                    
                    resp = requests.get(AQICollector.BASE_URL, params=params, timeout=15)
                    resp.raise_for_status()
                    data = resp.json().get("hourly", {})
                    
                    if not data: continue
                    
                    # Chuyển đổi dữ liệu sang DataFrame để dễ xử lý
                    df = pd.DataFrame({"timestamp": pd.to_datetime(data["time"])})
                    for api_col, db_col in AQICollector.COL_MAPPING.items():
                        if api_col in data:
                            df[db_col] = data[api_col]
                    
                    # Chỉ lấy bản ghi mới nhất (thường là giờ hiện tại hoặc gần nhất)
                    # Open-Meteo trả về cả ngày, ta chỉ lấy những giờ chưa có trong DB
                    # (Để đơn giản, ở đây ta lấy bản ghi của giờ hiện tại)
                    current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
                    latest_row = df[df['timestamp'] <= current_hour].iloc[-1:]
                    
                    if not latest_row.empty:
                        row = latest_row.iloc[0]
                        
                        # Tính AQI
                        aqi_val = max([calc_sub_aqi(row.get(p, 0), p) for p in ["pm25", "pm10", "so2", "no2", "co", "o3"]])
                        
                        # Kiểm tra xem bản ghi giờ này đã tồn tại chưa
                        existing = session.exec(
                            select(AQILog).where(
                                AQILog.village_name == v.name,
                                AQILog.timestamp == row['timestamp'].to_pydatetime()
                            )
                        ).first()
                        
                        if not existing:
                            log = AQILog(
                                village_name=v.name,
                                timestamp=row['timestamp'].to_pydatetime(),
                                pm25=row['pm25'],
                                pm10=row.get('pm10'),
                                co=row.get('co'),
                                no2=row.get('no2'),
                                so2=row.get('so2'),
                                o3=row.get('o3'),
                                aqi=aqi_val,
                                level=get_aqi_level(aqi_val)
                            )
                            session.add(log)
                            print(f"✅ Đã cập nhật AQI cho {v.name}: {aqi_val:.1f}")
                    
                except Exception as e:
                    print(f"❌ Lỗi khi lấy dữ liệu cho {v.name}: {e}")
            
            session.commit()
            print(f"🏁 Hoàn thành chu kỳ cập nhật.")

if __name__ == "__main__":
    # Test chạy thử một lần
    AQICollector.fetch_live_data()
