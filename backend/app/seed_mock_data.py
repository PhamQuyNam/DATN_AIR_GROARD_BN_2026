import sys
import os
from datetime import datetime, timedelta
import random

# Tải cấu hình và database của app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import engine
from app.models.db_models import Village, AQILog
from sqlmodel import Session, select

def calculate_aqi_level(aqi: float) -> str:
    if aqi <= 50: return "Tốt"
    elif aqi <= 100: return "Trung bình"
    elif aqi <= 150: return "Kém"
    elif aqi <= 200: return "Xấu"
    elif aqi <= 300: return "Rất xấu"
    else: return "Nguy hại"

def seed_data_to_now():
    # Cộng thêm 7 tiếng vì môi trường Docker đang chạy ở múi giờ gốc (UTC), trong khi Việt Nam là UTC+7
    now = datetime.now() + timedelta(hours=7)
    # Chỉnh giờ về chẵn (VD: 22:51 -> 22:00)
    target_time = now.replace(minute=0, second=0, microsecond=0)
    
    with Session(engine) as session:
        villages = session.exec(select(Village)).all()
        
        for village in villages:
            # Lấy bản ghi mới nhất của làng này
            latest_log = session.exec(
                select(AQILog)
                .where(AQILog.village_name == village.name)
                .order_by(AQILog.timestamp.desc())
                .limit(1)
            ).first()
            
            if not latest_log:
                continue
                
            current_time = latest_log.timestamp + timedelta(hours=1)
            new_logs = []
            
            # Khởi tạo giá trị base từ bản ghi cuối (xử lý trường hợp null)
            base_pm25 = latest_log.pm25 or 50.0
            base_pm10 = latest_log.pm10 or 60.0
            base_temp = latest_log.temperature or 25.0
            base_hum = latest_log.humidity or 70.0
            base_co = latest_log.co or 1.0
            base_no2 = latest_log.no2 or 10.0
            base_so2 = latest_log.so2 or 10.0
            base_o3 = latest_log.o3 or 20.0
            base_wind_speed = latest_log.wind_speed or 2.0
            base_wind_dir = latest_log.wind_dir or 180.0
            base_pressure = latest_log.pressure or 1010.0
            base_precipitation = latest_log.precipitation or 0.0
            base_cloud_cover = latest_log.cloud_cover or 50.0
            base_visibility = latest_log.visibility or 10.0
            
            print(f"🔄 Đang sinh dữ liệu cho {village.name} từ {current_time} đến {target_time}...")
            
            while current_time <= target_time:
                # Random walk (trôi dạt ngẫu nhiên) để dữ liệu trông tự nhiên
                base_pm25 = max(5.0, min(250.0, base_pm25 + random.uniform(-10, 10)))
                base_pm10 = max(10.0, min(300.0, base_pm10 + random.uniform(-15, 15)))
                base_temp = max(15.0, min(40.0, base_temp + random.uniform(-1, 1)))
                base_hum = max(30.0, min(100.0, base_hum + random.uniform(-2, 2)))
                base_co = max(0.1, base_co + random.uniform(-0.1, 0.1))
                base_no2 = max(1.0, base_no2 + random.uniform(-2, 2))
                base_so2 = max(1.0, base_so2 + random.uniform(-1, 1))
                base_o3 = max(1.0, base_o3 + random.uniform(-5, 5))
                base_wind_speed = max(0.0, base_wind_speed + random.uniform(-1, 1))
                base_wind_dir = max(0.0, min(360.0, base_wind_dir + random.uniform(-10, 10)))
                base_pressure = max(990.0, min(1020.0, base_pressure + random.uniform(-2, 2)))
                base_precipitation = max(0.0, min(50.0, base_precipitation + random.uniform(-0.5, 0.5)))
                base_cloud_cover = max(0.0, min(100.0, base_cloud_cover + random.uniform(-5, 5)))
                base_visibility = max(1.0, min(20.0, base_visibility + random.uniform(-0.5, 0.5)))
                
                # Tính AQI giả lập
                mock_aqi = max(10, min(300, int(base_pm25 * random.uniform(1.2, 1.8))))
                
                new_log = AQILog(
                    village_name=village.name,
                    timestamp=current_time,
                    pm25=base_pm25,
                    pm10=base_pm10,
                    co=base_co,
                    no2=base_no2,
                    so2=base_so2,
                    o3=base_o3,
                    aod=latest_log.aod or 0.5,
                    dust=latest_log.dust or 0.0,
                    temperature=base_temp,
                    humidity=base_hum,
                    wind_speed=base_wind_speed,
                    wind_dir=base_wind_dir,
                    pressure=base_pressure,
                    precipitation=base_precipitation,
                    cloud_cover=base_cloud_cover,
                    visibility=base_visibility,
                    aqi=mock_aqi,
                    level=calculate_aqi_level(mock_aqi),
                    shap_values=None # SHAP sẽ được AI tự tính lại
                )
                new_logs.append(new_log)
                current_time += timedelta(hours=1)
                
            if new_logs:
                session.add_all(new_logs)
                session.commit()
                print(f"✅ Đã thêm {len(new_logs)} bản ghi cho {village.name}")

if __name__ == "__main__":
    print("🚀 Bắt đầu quá trình sinh dữ liệu giả lập (Mock Data) đến thời điểm hiện tại...")
    seed_data_to_now()
    print("🎉 Hoàn tất!")
