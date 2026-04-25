"""
ml_training/preprocessing/data_splitter_per_village.py  (v2 — SHAP-guided)

Chuẩn bị dữ liệu train LSTM riêng cho từng làng nghề.
Áp dụng SHAP-guided feature selection: loại bỏ sub-AQI (aqi_pm25, aqi_o3...)
vì chúng gây data leakage — LSTM sẽ học shortcut thay vì pattern thực.

Thay đổi so với v1:
  ✗ Loại: aqi_o3, aqi_pm25, aqi_pm10, aqi_no2, aqi_so2 (leakage)
  ✗ Loại: village_encoded (train riêng từng làng, không cần)
  ✓ Giữ: aqi_roll3h (SHAP #1, 32%), o3 (SHAP #2, 17.5%)
  ✓ Giữ: aqi_lag1h (SHAP #5, 5.9%), hour_sin (SHAP #15)
  ✓ Thêm: aqi_eu, us_aqi làm tham chiếu nếu có

Output cho mỗi làng:
    data/exports/per_village_v2/<village_slug>/
        ├── train.parquet
        ├── val.parquet
        ├── test.parquet
        ├── scaler_X.pkl
        ├── scaler_y.pkl
        └── meta.json

Chạy:
    cd ml_training/preprocessing
    python data_splitter_per_village.py
"""

import os, re, json, joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# ── Đường dẫn ────────────────────────────────────────────────────────────────
DATASET_PATH = "../data/exports/ml_dataset.parquet"
OUTPUT_DIR   = "../data/exports/per_village_v3"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# FEATURE COLS — v3 REDUCED (12 features)
# Theo hướng dẫn update_features.md
# ══════════════════════════════════════════════════════════════════════════════
FEATURE_COLS = [
    # ── (A) Chất ô nhiễm gốc ─────────────────────────────────────────────────
    # Giữ 4 chất chính — bỏ co vì ít ảnh hưởng theo SHAP
    "pm25",    # PM2.5 — chỉ số trung tâm của AQI
    "pm10",    # PM10 — liên quan PM2.5
    "o3",      # Ozone — SHAP rank 2 (0.175)
    "no2",     # NO2 — đặc trưng làng nghề đốt nhiên liệu

    # ── (B) Temporal lag ngắn — QUAN TRỌNG NHẤT ─────────────────────────────
    # Chỉ giữ lag ngắn — lag xa (24h, 48h) thêm nhiễu
    "aqi_lag1h",    # SHAP rank 5 (0.059) — 1 giờ trước
    "aqi_lag3h",    # SHAP rank 12 (0.009) — 3 giờ trước

    # ── (C) Rolling mean — signal mượt ───────────────────────────────────────
    "aqi_roll3h",   # SHAP rank 1 (0.320) — QUAN TRỌNG NHẤT
    "aqi_roll6h",   # SHAP rank 7 (0.033) — xu hướng 6h

    # ── (D) Thời tiết tối thiểu ───────────────────────────────────────────────
    # Chỉ 3 biến thời tiết có ảnh hưởng vật lý rõ ràng
    "temperature",  # nhiệt độ — ảnh hưởng phát tán ô nhiễm
    "humidity",     # độ ẩm — PM2.5 tăng khi ẩm cao
    "wind_speed",   # tốc độ gió — phát tán ô nhiễm

    # ── (E) Time encoding tuần hoàn ──────────────────────────────────────────
    "hour_sin",     # SHAP rank 15 (0.007) — pattern theo giờ
    "hour_cos",     # cặp với hour_sin
]
# Tổng: 12 features

# Target: AQI tổng hợp theo QCVN 05:2023
TARGET_COL = "aqi_vn"

# Split ratio
TRAIN_RATIO = 0.70
VAL_RATIO   = 0.15
# TEST_RATIO  = 0.15

# Số records tối thiểu để train có ý nghĩa
MIN_RECORDS = 500


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def slugify(name: str) -> str:
    """Chuyển tên làng nghề sang tên thư mục an toàn."""
    replacements = {
        "à":"a","á":"a","ả":"a","ã":"a","ạ":"a",
        "ă":"a","ắ":"a","ằ":"a","ẳ":"a","ẵ":"a","ặ":"a",
        "â":"a","ấ":"a","ầ":"a","ẩ":"a","ẫ":"a","ậ":"a",
        "è":"e","é":"e","ẻ":"e","ẽ":"e","ẹ":"e",
        "ê":"e","ế":"e","ề":"e","ể":"e","ễ":"e","ệ":"e",
        "ì":"i","í":"i","ỉ":"i","ĩ":"i","ị":"i",
        "ò":"o","ó":"o","ỏ":"o","õ":"o","ọ":"o",
        "ô":"o","ố":"o","ồ":"o","ổ":"o","ỗ":"o","ộ":"o",
        "ơ":"o","ớ":"o","ờ":"o","ở":"o","ỡ":"o","ợ":"o",
        "ù":"u","ú":"u","ủ":"u","ũ":"u","ụ":"u",
        "ư":"u","ứ":"u","ừ":"u","ử":"u","ữ":"u","ự":"u",
        "ỳ":"y","ý":"y","ỷ":"y","ỹ":"y","ỵ":"y",
        "đ":"d","Đ":"d",
    }
    name = name.lower().strip()
    for k, v in replacements.items():
        name = name.replace(k, v)
    name = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    return name


def aqi_label(aqi: float) -> str:
    if   aqi <= 50:  return "Tốt"
    elif aqi <= 100: return "Trung bình"
    elif aqi <= 150: return "Kém (nhạy cảm)"
    elif aqi <= 200: return "Kém"
    elif aqi <= 300: return "Rất xấu"
    else:            return "Nguy hại"


def prepare_village(village_name: str,
                    df_village: pd.DataFrame) -> dict | None:
    """
    Chuẩn bị đầy đủ train/val/test + scaler cho 1 làng.
    Chỉ dùng features trong FEATURE_COLS (đã loại leakage).
    """
    slug = slugify(village_name)
    out  = os.path.join(OUTPUT_DIR, slug)
    os.makedirs(out, exist_ok=True)

    # ── Lọc features thực sự tồn tại trong dataset ───────────────────────────
    available = [c for c in FEATURE_COLS if c in df_village.columns]
    missing_f = [c for c in FEATURE_COLS if c not in df_village.columns]
    if missing_f:
        print(f"    ⚠  Thiếu {len(missing_f)} features: {missing_f[:5]}...")

    needed = available + [TARGET_COL, "timestamp"]
    df_v   = df_village[[c for c in needed if c in df_village.columns]]
    df_v   = df_v.dropna().sort_values("timestamp").reset_index(drop=True)

    if len(df_v) < MIN_RECORDS:
        print(f"    Bỏ qua — {len(df_v)} records < {MIN_RECORDS}")
        return None

    # ── Temporal split ────────────────────────────────────────────────────────
    n       = len(df_v)
    i_train = int(n * TRAIN_RATIO)
    i_val   = int(n * (TRAIN_RATIO + VAL_RATIO))

    train = df_v.iloc[:i_train].copy()
    val   = df_v.iloc[i_train:i_val].copy()
    test  = df_v.iloc[i_val:].copy()

    # ── Fit scaler trên TRAIN only ────────────────────────────────────────────
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    scaler_X.fit(train[available].values)
    scaler_y.fit(train[[TARGET_COL]].values)

    # ── Lưu parquet ──────────────────────────────────────────────────────────
    train.to_parquet(os.path.join(out, "train.parquet"), index=False)
    val.to_parquet(  os.path.join(out, "val.parquet"),   index=False)
    test.to_parquet( os.path.join(out, "test.parquet"),  index=False)

    # ── Lưu scaler ────────────────────────────────────────────────────────────
    joblib.dump(scaler_X, os.path.join(out, "scaler_X.pkl"))
    joblib.dump(scaler_y, os.path.join(out, "scaler_y.pkl"))

    # ── Thống kê AQI phân phối ────────────────────────────────────────────────
    aqi_dist = {}
    for sname, sdf in [("train", train), ("val", val), ("test", test)]:
        aqi_dist[sname] = sdf[TARGET_COL].apply(aqi_label)\
                                          .value_counts().to_dict()

    # ── Meta ──────────────────────────────────────────────────────────────────
    meta = {
        "village":        village_name,
        "slug":           slug,
        "version":        "v2_shap_guided",
        "n_features":     len(available),
        "feature_cols":   available,
        "removed_leakage": [
            "aqi_o3","aqi_pm25","aqi_pm10",
            "aqi_no2","aqi_so2","village_encoded"
        ],
        "target_col":     TARGET_COL,
        "records": {
            "total": n,
            "train": len(train),
            "val":   len(val),
            "test":  len(test),
        },
        "date_range": {
            "start": str(df_v["timestamp"].min()),
            "end":   str(df_v["timestamp"].max()),
            "train_end": str(train["timestamp"].max()),
            "val_end":   str(val["timestamp"].max()),
        },
        "aqi_stats": {
            "min":  round(float(df_v[TARGET_COL].min()), 2),
            "max":  round(float(df_v[TARGET_COL].max()), 2),
            "mean": round(float(df_v[TARGET_COL].mean()), 2),
            "std":  round(float(df_v[TARGET_COL].std()), 2),
        },
        "pm25_stats": {
            "mean": round(float(df_v["pm25"].mean()), 2),
            "max":  round(float(df_v["pm25"].max()), 2),
        } if "pm25" in df_v.columns else {},
        "aqi_distribution": aqi_dist,
    }
    with open(os.path.join(out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("CHUẨN BỊ DỮ LIỆU PER-VILLAGE v2  (SHAP-guided, no leakage)")
    print("=" * 65)
    print(f"\nFeatures sử dụng  : {len(FEATURE_COLS)}")
    print(f"Features loại bỏ  : aqi_o3, aqi_pm25, aqi_pm10, aqi_no2, aqi_so2")
    print(f"Target            : {TARGET_COL}")
    print(f"Split             : {TRAIN_RATIO}/{VAL_RATIO}/{1-TRAIN_RATIO-VAL_RATIO:.2f}")
    print(f"Output            : {OUTPUT_DIR}/\n")

    # Load
    print(f"Đọc: {DATASET_PATH}")
    df = pd.read_parquet(DATASET_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    print(f"  {len(df):,} records  |  {df['village'].nunique()} làng")

    if TARGET_COL not in df.columns:
        raise ValueError(
            f"Không tìm thấy cột '{TARGET_COL}'.\n"
            f"Cột AQI có sẵn: {[c for c in df.columns if 'aqi' in c.lower()]}"
        )

    # Xử lý từng làng
    villages = sorted(df["village"].unique())
    summary, skipped = [], []

    print(f"\nXử lý {len(villages)} làng nghề...\n")
    for v in villages:
        df_v = df[df["village"] == v].copy()
        print(f"  {v:<22} {len(df_v):>7,} records", end="  ")
        meta = prepare_village(v, df_v)
        if meta is None:
            skipped.append(v)
            continue
        r = meta["records"]
        print(f"→ train={r['train']:,} val={r['val']:,} "
              f"test={r['test']:,}  ✓")
        summary.append({
            "village":    v,
            "slug":       meta["slug"],
            "total":      r["total"],
            "train":      r["train"],
            "val":        r["val"],
            "test":       r["test"],
            "aqi_mean":   meta["aqi_stats"]["mean"],
            "n_features": meta["n_features"],
        })

    # Lưu summary
    summary_path = os.path.join(OUTPUT_DIR, "villages_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "version":          "v2_shap_guided",
            "total_villages":   len(summary),
            "skipped":          skipped,
            "feature_cols":     [c for c in FEATURE_COLS if c in df.columns],
            "removed_leakage":  ["aqi_o3","aqi_pm25","aqi_pm10",
                                  "aqi_no2","aqi_so2","village_encoded"],
            "target_col":       TARGET_COL,
            "split_ratio":      {"train": TRAIN_RATIO,
                                  "val":  VAL_RATIO,
                                  "test": round(1-TRAIN_RATIO-VAL_RATIO, 2)},
            "villages":         summary,
        }, f, ensure_ascii=False, indent=2)

    # Bảng kết quả
    print(f"\n{'=' * 65}")
    print(f"KẾT QUẢ")
    print(f"{'=' * 65}")
    print(f"  {'Làng nghề':<22} {'Total':>8} {'Train':>8} "
          f"{'Val':>6} {'Test':>6} {'AQI TB':>8} {'Feats':>6}")
    print(f"  {'-' * 63}")
    for r in summary:
        print(f"  {r['village']:<22} {r['total']:>8,} {r['train']:>8,} "
              f"{r['val']:>6,} {r['test']:>6,} "
              f"{r['aqi_mean']:>8.1f} {r['n_features']:>6}")
    print(f"\n  Thành công : {len(summary)} làng")
    if skipped:
        print(f"  Bỏ qua     : {skipped}")
    print(f"  Summary    : {summary_path}")


if __name__ == "__main__":
    main()