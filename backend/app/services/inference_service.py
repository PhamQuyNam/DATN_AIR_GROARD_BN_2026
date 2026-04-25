import joblib
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta

# Thêm đường dẫn gốc vào sys.path để nhận diện module 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import AQILog, ForecastLog, Village

class InferenceService:
    # Đường dẫn tới các model
    MODEL_DIR = "/app/models" if os.path.exists("/app") else "C:/Users/Acer/Desktop/DATN/DATN_AIR_GROARD_BN_2026/models"
    XGB_PATH = os.path.join(MODEL_DIR, "xgboost", "xgboost_aqi_6h.pkl")
    
    def __init__(self):
        self.xgb_model = None
        self._load_models()

    def _load_models(self):
        try:
            if os.path.exists(self.XGB_PATH):
                self.xgb_model = joblib.load(self.XGB_PATH)
                print("🧠 XGBoost model loaded successfully.")
            else:
                print(f"⚠️ XGBoost model not found at {self.XGB_PATH}")
        except Exception as e:
            print(f"❌ Error loading models: {e}")

    def run_forecast_all(self):
        """Chạy dự báo cho tất cả làng nghề dựa trên dữ liệu mới nhất trong DB"""
        if not self.xgb_model:
            print("❌ Cannot run forecast: Model not loaded.")
            return

        print(f"🔮 [{datetime.now()}] Bắt đầu chạy mô hình dự báo...")
        
        with Session(engine) as session:
            villages = session.exec(select(Village)).all()
            
            for v in villages:
                # 1. Lấy dữ liệu mới nhất của làng nghề này
                latest_data = session.exec(
                    select(AQILog)
                    .where(AQILog.village_name == v.name)
                    .order_by(AQILog.timestamp.desc())
                    .limit(1)
                ).first()
                
                if not latest_data: continue

                # 2. Chuẩn bị features cho XGBoost (Dựa trên cấu trúc model của bạn)
                # Lưu ý: Đây là ví dụ, bạn cần khớp chính xác các cột feature mà model yêu cầu
                features = pd.DataFrame([{
                    "pm25": latest_data.pm25,
                    "pm10": latest_data.pm10,
                    "co": latest_data.co,
                    "no2": latest_data.no2,
                    "so2": latest_data.so2,
                    "o3": latest_data.o3,
                    "hour": latest_data.timestamp.hour,
                    "dayofweek": latest_data.timestamp.weekday()
                }])

                try:
                    # 3. Dự báo (XGBoost thường dự báo Class hoặc giá trị AQI tiếp theo)
                    prediction = self.xgb_model.predict(features)[0]
                    
                    # 4. Lưu vào bảng dự báo (Dự báo cho 6h tới - ví dụ đơn giản)
                    # Xóa các dự báo cũ của làng nghề này trước
                    old_forecasts = session.exec(select(ForecastLog).where(ForecastLog.village_name == v.name)).all()
                    for old in old_forecasts: session.delete(old)
                    
                    for i in range(1, 7):
                        forecast = ForecastLog(
                            village_name=v.name,
                            timestamp=latest_data.timestamp + timedelta(hours=i),
                            predicted_aqi=float(prediction), # Giả định model dự báo AQI
                            forecast_hour=i
                        )
                        session.add(forecast)
                    
                    print(f"📈 Đã cập nhật dự báo cho {v.name}: {prediction:.1f}")
                except Exception as e:
                    print(f"❌ Lỗi dự báo cho {v.name}: {e}")
            
            session.commit()

# Khởi tạo singleton
inference_service = InferenceService()
