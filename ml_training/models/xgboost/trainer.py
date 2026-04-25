import os
import json
import joblib
import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ─────────────────────────────────────────────
# 1. CẤU HÌNH ĐƯỜNG DẪN
# ─────────────────────────────────────────────
INPUT_PATH = r"C:\Users\Acer\Desktop\DATN\DATN_AIR_GROARD_BN_2026\data\finally\final_dataset_target_6h.csv"
MODEL_DIR  = r"C:\Users\Acer\Desktop\DATN\DATN_AIR_GROARD_BN_2026\models\xgboost"
os.makedirs(MODEL_DIR, exist_ok=True)

def train_xgboost_model():
    # 2. LOAD DATA
    print(f"--- Đang đọc dữ liệu từ: {INPUT_PATH} ---")
    df = pd.read_csv(INPUT_PATH)

    # Loại bỏ các cột không phải đặc trưng huấn luyện
    # Lưu ý: Bỏ 'aqi_category' vì đây là nhãn phân loại, không dùng cho Regression
    drop_cols = ['timestamp', 'village', 'aqi_category', 'target_aqi_6h']
    X = df.drop(columns=drop_cols)
    y = df['target_aqi_6h']

    feat_names = X.columns.tolist()

    # 3. CHIA DỮ LIỆU (Train/Test theo tỉ lệ 8:2)
    # Vì là chuỗi thời gian, lý tưởng nhất là split theo thời gian thay vì random
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    print(f"Số lượng Features: {len(feat_names)}")
    print(f"Kích thước Train: {X_train.shape}, Test: {X_test.shape}")

    # 4. KHỞI TẠO VÀ HUẤN LUYỆN XGBOOST REGRESSOR
    model = xgb.XGBRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        early_stopping_rounds=50,
        random_state=42,
        tree_method='hist' # Chạy nhanh hơn trên tập dữ liệu lớn
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=100
    )

    # 5. ĐÁNH GIÁ MÔ HÌNH
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n" + "="*30)
    print("📊 KẾT QUẢ ĐÁNH GIÁ (TEST SET)")
    print(f"MAE:  {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R2 Score: {r2:.4f}")
    print("="*30)

    # 6. PHÂN TÍCH GIẢI THÍCH MÔ HÌNH VỚI SHAP
    print("\n🔍 Đang chạy phân tích SHAP...")
    explainer = shap.TreeExplainer(model)
    # Lấy một mẫu 500 dòng để tính toán nhanh
    shap_values = explainer.shap_values(X_test.iloc[:500])

    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test.iloc[:500], feature_names=feat_names, show=False)
    plt.tight_layout()
    plt.savefig(os.path.join(MODEL_DIR, "shap_summary_6h.png"), dpi=150)
    print(f"✅ Đã lưu biểu đồ SHAP tại: {MODEL_DIR}")

    # 7. LƯU MÔ HÌNH
    joblib.dump(model, os.path.join(MODEL_DIR, "xgboost_aqi_6h_model.pkl"))

    # Lưu metadata (danh sách features) để phục vụ dự báo sau này
    metadata = {
        "features": feat_names,
        "metrics": {"mae": mae, "r2": r2}
    }
    with open(os.path.join(MODEL_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f)

    print("🚀 Đã lưu mô hình và metadata hoàn tất!")

if __name__ == "__main__":
    train_xgboost_model()