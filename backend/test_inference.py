import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import joblib
import pandas as pd
import numpy as np
import json
from tensorflow.keras.models import load_model
import shap

MODEL_DIR = "C:/Users/Acer/Desktop/DATN/DATN_AIR_GROARD_BN_2026/models"
LSTM_PATH = os.path.join(MODEL_DIR, "lstm", "best_lstm_model.h5")
LSTM_META_PATH = os.path.join(MODEL_DIR, "lstm", "metadata_lstm.json")
XGB_PATH = os.path.join(MODEL_DIR, "xgboost", "xgboost_aqi_6h.pkl")
XGB_FEAT_PATH = os.path.join(MODEL_DIR, "xgboost", "features.json")

print("Loading LSTM:", LSTM_PATH)
lstm_model = load_model(LSTM_PATH, compile=False)
lstm_meta = json.load(open(LSTM_META_PATH))
print("LSTM input shape:", lstm_model.input_shape)

print("Loading XGBoost:", XGB_PATH)
xgb_model = joblib.load(XGB_PATH)
xgb_feat = json.load(open(XGB_FEAT_PATH))
print("XGBoost loaded successfully, expected features:", len(xgb_feat))

# Try creating a dummy input for XGBoost and getting SHAP
dummy_xgb = pd.DataFrame([np.zeros(len(xgb_feat))], columns=xgb_feat)
pred_xgb = xgb_model.predict(dummy_xgb)
print("XGBoost prediction:", pred_xgb)

explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(dummy_xgb)
print("SHAP values shape:", np.array(shap_values).shape)

# Try LSTM dummy input
dummy_lstm = np.zeros((1, lstm_meta['config']['window'], len(lstm_meta['config']['features'])))
pred_lstm = lstm_model.predict(dummy_lstm)
print("LSTM prediction shape:", pred_lstm.shape)
print("LSTM prediction:", pred_lstm)
