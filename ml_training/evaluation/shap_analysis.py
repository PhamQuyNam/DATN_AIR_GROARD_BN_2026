"""
So sánh kết quả 2 mô hình và xuất bảng tổng kết cho báo cáo.
"""
import json, joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

XGB_META  = "../models/xgboost/metadata.json"
LSTM_META = "../models/lstm/metadata.json"

with open(XGB_META)  as f: xgb_meta  = json.load(f)
with open(LSTM_META) as f: lstm_meta = json.load(f)

print("="*60)
print("SO SÁNH KẾT QUẢ 2 MÔ HÌNH")
print("="*60)

rows = [
    ["XGBoost",
     f"{xgb_meta['metrics']['test_accuracy']:.4f}",
     f"{xgb_meta['metrics']['test_f1']:.4f}",
     "—", "—",
     "Phân loại AQI + SHAP"],
    ["LSTM",
     "—", "—",
     f"{lstm_meta['metrics']['test_rmse']:.4f}",
     f"{lstm_meta['metrics']['test_r2']:.4f}",
     "Dự báo 24h tới"],
]

df_cmp = pd.DataFrame(rows, columns=[
    "Model", "Accuracy", "F1 (weighted)", "RMSE", "R²", "Mục đích"
])
print(df_cmp.to_string(index=False))

# Kiểm tra đạt target đề án không
print(f"\n{'='*60}")
print("KIỂM TRA TARGET ĐỀ ÁN")
print("="*60)

xgb_r2 = float(xgb_meta['metrics']['test_f1'])
lstm_r2 = float(lstm_meta['metrics']['test_r2'])

target_xgb  = 0.92
target_lstm = 0.90

print(f"XGBoost F1  : {xgb_r2:.4f}  {'✓ ĐẠT' if xgb_r2 >= target_xgb else '✗ CHƯA ĐẠT'} (target ≥ {target_xgb})")
print(f"LSTM R²     : {lstm_r2:.4f}  {'✓ ĐẠT' if lstm_r2 >= target_lstm else '✗ CHƯA ĐẠT'} (target ≥ {target_lstm})")

if lstm_r2 < target_lstm:
    print("\nGợi ý cải thiện LSTM:")
    print("  1. Tăng window lên 72h")
    print("  2. Thêm layer LSTM thứ 3 với units=32")
    print("  3. Thêm Attention mechanism")
    print("  4. Tăng n_trials Optuna cho LSTM")