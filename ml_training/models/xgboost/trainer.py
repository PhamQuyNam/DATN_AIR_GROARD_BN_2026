"""
ml_training/models/xgboost/trainer.py
Train XGBoost phân loại AQI + tối ưu Optuna + phân tích SHAP.
"""
import numpy as np
import pandas as pd
import joblib, os, json
from sklearn.metrics import (classification_report, confusion_matrix,
                              accuracy_score, f1_score)
from sklearn.utils.class_weight import compute_class_weight
import xgboost as xgb
import optuna
import shap
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

EXPORT_DIR  = "../../data/exports"
MODEL_DIR   = "../../../models/xgboost"
os.makedirs(MODEL_DIR, exist_ok=True)

# ── Load dữ liệu đã split ────────────────────────────────────────────────────
from sys import path
path.insert(0, "../../preprocessing")
from data_loader import (load_and_prepare, temporal_split,
                            build_xgb_data, XGB_FEATURES)

print("="*55)
print("PIPELINE A — XGBoost + SHAP")
print("="*55)

df, le        = load_and_prepare()
train, val, test = temporal_split(df)

X_tr, X_vl, X_te, y_tr, y_vl, y_te = build_xgb_data(train, val, test)
feat_names = joblib.load(f"{EXPORT_DIR}/xgb_feature_names.pkl")

# ── Tính class weight để xử lý imbalanced ────────────────────────────────────
classes = np.unique(y_tr)
weights = compute_class_weight("balanced", classes=classes, y=y_tr)
w_dict  = dict(zip(classes.tolist(), weights.tolist()))
sample_weights = np.array([w_dict[y] for y in y_tr])

print(f"\nClass weights (balanced):")
for cls_id, w in w_dict.items():
    print(f"  [{le.classes_[cls_id]}] weight={w:.3f}")


# ── Bước 1: Baseline nhanh (không tune) ──────────────────────────────────────
print("\n[1/3] Train baseline XGBoost...")
baseline = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    use_label_encoder=False,
    eval_metric="mlogloss",
    random_state=42,
    n_jobs=-1,
)
baseline.fit(
    X_tr, y_tr,
    sample_weight=sample_weights,
    eval_set=[(X_vl, y_vl)],
    verbose=False,
)
y_pred_base = baseline.predict(X_vl)
f1_base = f1_score(y_vl, y_pred_base, average="weighted")
print(f"  Val F1 (weighted): {f1_base:.4f}")


# ── Bước 2: Optuna hyperparameter tuning ─────────────────────────────────────
print("\n[2/3] Optuna tuning (50 trials)...")

def objective(trial):
    params = {
        "n_estimators":      trial.suggest_int("n_estimators", 200, 800),
        "max_depth":         trial.suggest_int("max_depth", 4, 10),
        "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample":         trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree":  trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "min_child_weight":  trial.suggest_int("min_child_weight", 1, 10),
        "gamma":             trial.suggest_float("gamma", 0, 5),
        "reg_alpha":         trial.suggest_float("reg_alpha", 0, 1),
        "reg_lambda":        trial.suggest_float("reg_lambda", 0.5, 5),
    }
    model = xgb.XGBClassifier(
        **params,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_tr, y_tr,
              sample_weight=sample_weights,
              eval_set=[(X_vl, y_vl)],
              verbose=False)
    y_pred = model.predict(X_vl)
    return f1_score(y_vl, y_pred, average="weighted")

optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=50, show_progress_bar=True)

best_params = study.best_params
print(f"\n  Best F1 (val): {study.best_value:.4f}")
print(f"  Best params  : {best_params}")


# ── Bước 3: Train model tốt nhất ─────────────────────────────────────────────
print("\n[3/3] Train model tốt nhất...")
best_model = xgb.XGBClassifier(
    **best_params,
    use_label_encoder=False,
    eval_metric="mlogloss",
    random_state=42,
    n_jobs=-1,
)
best_model.fit(
    X_tr, y_tr,
    sample_weight=sample_weights,
    eval_set=[(X_vl, y_vl)],
    verbose=False,
)


# ── Đánh giá trên Test set ────────────────────────────────────────────────────
y_pred_test = best_model.predict(X_te)
acc  = accuracy_score(y_te, y_pred_test)
f1   = f1_score(y_te, y_pred_test, average="weighted")

print(f"\n{'='*55}")
print(f"KẾT QUẢ TEST SET")
print(f"{'='*55}")
print(f"Accuracy (weighted): {acc:.4f}")
print(f"F1-score (weighted): {f1:.4f}")
print(f"\nClassification Report:")
print(classification_report(y_te, y_pred_test,
                             target_names=le.classes_))


# ── SHAP Analysis ─────────────────────────────────────────────────────────────
print("\nTính SHAP values...")
explainer    = shap.TreeExplainer(best_model)
# Dùng 2000 mẫu đại diện để tính nhanh hơn
sample_idx   = np.random.choice(len(X_te), 2000, replace=False)
shap_values  = explainer.shap_values(X_te[sample_idx])

# Summary plot — top 20 features quan trọng nhất
shap.summary_plot(
    shap_values, X_te[sample_idx],
    feature_names=feat_names,
    max_display=20,
    show=False
)
plt.title("SHAP Summary — Top 20 features ảnh hưởng AQI")
plt.tight_layout()
plt.savefig(f"{MODEL_DIR}/shap_summary.png", dpi=150, bbox_inches="tight")
plt.show()
print(f"  Lưu: {MODEL_DIR}/shap_summary.png")

# Feature importance từ XGBoost
fi = pd.DataFrame({
    "feature":    feat_names,
    "importance": best_model.feature_importances_
}).sort_values("importance", ascending=False)
print(f"\nTop 15 features quan trọng nhất:")
print(fi.head(15).to_string(index=False))


# ── Lưu model và artifacts ────────────────────────────────────────────────────
joblib.dump(best_model, f"{MODEL_DIR}/model.pkl")
joblib.dump(explainer,  f"{MODEL_DIR}/shap_explainer.pkl")

metadata = {
    "model_type":    "XGBoostClassifier",
    "n_features":    len(feat_names),
    "feature_names": feat_names,
    "classes":       le.classes_.tolist(),
    "best_params":   best_params,
    "metrics": {
        "val_f1_baseline": round(f1_base, 4),
        "val_f1_tuned":    round(study.best_value, 4),
        "test_accuracy":   round(acc, 4),
        "test_f1":         round(f1, 4),
    },
    "optuna_n_trials": 50,
}
with open(f"{MODEL_DIR}/metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print(f"\nModel lưu tại: {MODEL_DIR}/")
print(f"  model.pkl            — XGBoost model")
print(f"  shap_explainer.pkl   — SHAP TreeExplainer")
print(f"  metadata.json        — Thông tin model + metrics")
print(f"  shap_summary.png     — Biểu đồ SHAP")