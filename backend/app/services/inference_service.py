import joblib
import pandas as pd
import numpy as np
import json
import os
import sys
from datetime import datetime, timedelta

# Thêm đường dẫn gốc vào sys.path để nhận diện module 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import AQILog, ForecastLog, Village

# Tắt cảnh báo TF và ép dùng Legacy Keras để sửa lỗi quantization_mode
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_USE_LEGACY_KERAS'] = '1'

try:
    from tensorflow.keras.models import load_model
    import shap
except ImportError as e:
    print(f"⚠️ Cảnh báo: Chưa cài đặt thư viện AI (tensorflow, shap). Vui lòng cài đặt để chạy Inference: {e}")

class InferenceService:
    # Đường dẫn tới các model (Docker hoặc Local)
    MODEL_DIR = "/app/models" if os.path.exists("/app") else "C:/Users/Acer/Desktop/DATN/DATN_AIR_GROARD_BN_2026/models"
    
    LSTM_PATH = os.path.join(MODEL_DIR, "lstm", "best_lstm_model.h5")
    LSTM_META_PATH = os.path.join(MODEL_DIR, "lstm", "metadata_lstm.json")
    
    XGB_PATH = os.path.join(MODEL_DIR, "xgboost", "xgboost_aqi_6h.pkl")
    XGB_FEAT_PATH = os.path.join(MODEL_DIR, "xgboost", "features.json")
    
    def __init__(self):
        self.lstm_model = None
        self.lstm_meta = None
        self.xgb_model = None
        self.xgb_feat = None
        # Không nạp model khi khởi động để tránh treo server

    def _load_models(self):
        # 1. Load LSTM
        try:
            if os.path.exists(self.LSTM_PATH) and os.path.exists(self.LSTM_META_PATH):
                from tensorflow.keras.layers import LSTM
                from tensorflow.keras.models import load_model
                import tensorflow.keras as keras
                class CustomLSTM(LSTM):
                    def __init__(self, *args, **kwargs):
                        kwargs.pop('time_major', None)
                        kwargs.pop('quantization_mode', None)
                        super().__init__(*args, **kwargs)

                self.lstm_model = load_model(self.LSTM_PATH, compile=False, custom_objects={'LSTM': CustomLSTM})
                with open(self.LSTM_META_PATH, 'r') as f:
                    self.lstm_meta = json.load(f)
                print("🧠 LSTM model loaded successfully.")
            else:
                print(f"⚠️ LSTM model/meta not found at {self.MODEL_DIR}/lstm")
        except Exception as e:
            print(f"❌ Error loading LSTM model: {e}")

        # 2. Load XGBoost
        try:
            if os.path.exists(self.XGB_PATH) and os.path.exists(self.XGB_FEAT_PATH):
                self.xgb_model = joblib.load(self.XGB_PATH)
                with open(self.XGB_FEAT_PATH, 'r') as f:
                    self.xgb_feat = json.load(f)
                print("🧠 XGBoost model loaded successfully.")
            else:
                print(f"⚠️ XGBoost model/features not found at {self.MODEL_DIR}/xgboost")
        except Exception as e:
            print(f"❌ Error loading XGBoost model: {e}")

    def run_forecast_all(self):
        """Chạy dự báo (LSTM) và phân tích nguyên nhân (XGBoost SHAP) cho tất cả làng nghề"""
        # Tự động nạp model nếu chưa có (Lazy Loading)
        if not self.xgb_model:
            self._load_models()
            
        if not self.xgb_model:
            print("❌ Cannot run: XGBoost model (SHAP) not loaded.")
            return

        if not self.lstm_model:
            print("⚠️ Warning: LSTM model not loaded. Skipping forecasting, only running SHAP analysis.")

        print(f"🔮 [{datetime.now()}] Bắt đầu quy trình Trí tuệ Nhân tạo (AI)...")
        
        with Session(engine) as session:
            villages = session.exec(select(Village)).all()
            
            for v in villages:
                # 1. Lấy dữ liệu 48 giờ gần nhất của làng nghề này
                recent_data = session.exec(
                    select(AQILog)
                    .where(AQILog.village_name == v.name)
                    .order_by(AQILog.timestamp.desc())
                    .limit(12) # Model .h5 cũ train với window=12
                ).all()
                
                # Sắp xếp lại theo thời gian tăng dần (cũ đến mới)
                recent_data.reverse()
                
                if not recent_data or len(recent_data) == 0:
                    continue
                    
                latest_data = recent_data[-1]

                # ==========================================
                # A. DỰ BÁO VỚI LSTM (Chỉ chạy nếu load được model)
                # ==========================================
                if self.lstm_model and self.lstm_meta:
                    try:
                        lstm_window = 12
                        lstm_features = self.lstm_meta['config']['features'][:11]
                        
                        # Chuyển sang DataFrame để dễ map cột
                        df_recent = pd.DataFrame([d.dict() for d in recent_data])
                        
                        # Tính toán các cột hour_sin, hour_cos nếu chưa có
                        if 'hour_sin' not in df_recent.columns:
                            df_recent['hour'] = pd.to_datetime(df_recent['timestamp']).dt.hour
                            df_recent['hour_sin'] = np.sin(2 * np.pi * df_recent['hour'] / 24.0)
                            df_recent['hour_cos'] = np.cos(2 * np.pi * df_recent['hour'] / 24.0)
                            
                        # Đổi tên cột aqi thành aqi_current để khớp với danh sách features của model
                        if 'aqi' in df_recent.columns:
                            df_recent['aqi_current'] = df_recent['aqi']
                            
                        # Trích xuất đúng 11 features mà LSTM cần
                        X_raw = df_recent[lstm_features].fillna(0)
                        
                        # Chuẩn hóa (Scale) động dựa trên chính dữ liệu quá khứ gần nhất (Self-Scaling)
                        means = X_raw.mean()
                        stds = X_raw.std().replace(0, 1) 
                        X_scaled = (X_raw - means) / stds
                        
                        # Reshape thành (1, 12, 11)
                        X_lstm = X_scaled.values[-lstm_window:].reshape((1, lstm_window, len(lstm_features)))
                        
                        # Predict
                        preds_lstm = self.lstm_model.predict(X_lstm, verbose=0)[0]
                        
                        # Unscale
                        mean_aqi = means.get('aqi_current', 84.0)
                        std_aqi = stds.get('aqi_current', 42.0)
                        preds_real = (preds_lstm * std_aqi) + mean_aqi
                        
                        # Lưu vào ForecastLog
                        # Lưu vào ForecastLog
                        old_forecasts = session.exec(select(ForecastLog).where(ForecastLog.village_name == v.name)).all()
                        for old in old_forecasts: session.delete(old)
                        
                        if len(preds_real) == 1:
                            # Model chỉ dự báo 1 điểm (t+6), tiến hành nội suy tuyến tính (Linear Interpolation) 
                            # từ AQI hiện tại đến điểm t+6 để biểu đồ frontend vẽ đủ 6 điểm
                            current_aqi = df_recent['aqi_current'].iloc[-1]
                            target_aqi_6h = float(preds_real[0])
                            
                            for i in range(1, 7): # Từ t+1 đến t+6
                                interpolated_aqi = current_aqi + (target_aqi_6h - current_aqi) * (i / 6.0)
                                forecast = ForecastLog(
                                    village_name=v.name,
                                    timestamp=latest_data.timestamp + timedelta(hours=i),
                                    predicted_aqi=float(interpolated_aqi),
                                    forecast_hour=i,
                                    model_used="lstm_attention_48h"
                                )
                                session.add(forecast)
                        else:
                            # Nếu model dự báo nhiều điểm (multi-step)
                            for i in range(len(preds_real)):
                                forecast = ForecastLog(
                                    village_name=v.name,
                                    timestamp=latest_data.timestamp + timedelta(hours=i+1),
                                    predicted_aqi=float(preds_real[i]),
                                    forecast_hour=i+1,
                                    model_used="lstm_attention_48h"
                                )
                                session.add(forecast)
                        print(f"📈 LSTM Dự báo {v.name} thành công.")
                    except Exception as e:
                        print(f"❌ Lỗi LSTM dự báo cho {v.name}: {e}")
                else:
                    # Nếu không có LSTM, ta xóa dự báo cũ để tránh hiển thị sai lệch
                    pass

                # ==========================================
                # B. PHÂN TÍCH NGUYÊN NHÂN VỚI XGBOOST & SHAP
                # ==========================================
                try:
                    df_latest = pd.DataFrame([latest_data.dict()])
                    
                    # Tính lag features nếu cần (tạm lấy giá trị hiện tại nếu thiếu dữ liệu quá khứ)
                    df_latest['aqi_lag1h'] = recent_data[-2].aqi if len(recent_data) >= 2 else latest_data.aqi
                    df_latest['aqi_lag3h'] = recent_data[-4].aqi if len(recent_data) >= 4 else latest_data.aqi
                    df_latest['aqi_roll3h'] = np.mean([d.aqi for d in recent_data[-3:]]) if len(recent_data) >= 3 else latest_data.aqi
                    df_latest['hour'] = latest_data.timestamp.hour
                    df_latest['hour_sin'] = np.sin(2 * np.pi * df_latest['hour'] / 24.0)
                    df_latest['hour_cos'] = np.cos(2 * np.pi * df_latest['hour'] / 24.0)
                    df_latest['cloud_cover'] = df_latest.get('cloud_cover', 0)
                    df_latest['visibility'] = df_latest.get('visibility', 10)
                    
                    # Map đủ 22 features cho XGBoost
                    for f in self.xgb_feat:
                        if f not in df_latest.columns:
                            df_latest[f] = 0.0 # fallback
                            
                    X_xgb = df_latest[self.xgb_feat].fillna(0)
                    
                    # Dùng SHAP TreeExplainer
                    explainer = shap.TreeExplainer(self.xgb_model)
                    shap_vals = explainer.shap_values(X_xgb)
                    
                    # Tùy bản XGBoost/SHAP, shap_vals có thể là array hoặc list các array (nếu classification)
                    if isinstance(shap_vals, list):
                        shap_vals = shap_vals[1] # Lấy class 1 (nếu là phân loại ô nhiễm)
                    
                    if len(shap_vals.shape) == 2:
                        shap_vals = shap_vals[0]
                        
                    # Lấy Top 5 features có tác động lớn nhất (Absolute value)
                    shap_dict = {feat: float(val) for feat, val in zip(self.xgb_feat, shap_vals)}
                    sorted_shap = dict(sorted(shap_dict.items(), key=lambda item: abs(item[1]), reverse=True)[:5])
                    
                    # Update bản ghi hiện tại với giá trị SHAP
                    latest_data.shap_values = sorted_shap
                    session.add(latest_data)
                    print(f"🔍 SHAP Phân tích {v.name} thành công.")
                    
                except Exception as e:
                    print(f"❌ Lỗi SHAP cho {v.name}: {e}")
            
            session.commit()
            print(f"✅ Hoàn thành quy trình AI.")

# Khởi tạo singleton
inference_service = InferenceService()

