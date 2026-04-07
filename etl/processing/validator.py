"""
etl/processing/validator.py

Kiểm tra chất lượng dataset sau khi clean.
Trả về báo cáo chi tiết và raise lỗi nếu dataset không đạt ngưỡng tối thiểu.
"""
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Cấu hình ngưỡng chấp nhận ───────────────────────────────────────────────
# Import 17 làng nghề cần giám sát (bỏ baseline Vọng Nguyệt)
# Phải khớp với MONITORING_VILLAGES trong các fetcher
try:
    from configs.village_config import MONITORING_VILLAGES as _MV
    EXPECTED_VILLAGES = [v["name"] for v in _MV]
except ImportError:
    import yaml, pathlib
    _yaml_path = pathlib.Path(__file__).parent.parent.parent / "configs" / "villages.yaml"
    with open(_yaml_path, encoding="utf-8") as _f:
        EXPECTED_VILLAGES = [
            v["name"] for v in yaml.safe_load(_f)["villages"]
            if not v.get("is_baseline", False)
        ]

# Tỷ lệ missing tối đa cho phép mỗi cột (%)
MAX_MISSING_PCT = {
    "pm25":        5.0,
    "pm10":       10.0,
    "so2":        15.0,
    "no2":        15.0,
    "co":         15.0,
    "o3":         15.0,
    "temperature": 5.0,
    "humidity":    5.0,
    "wind_speed": 10.0,
}

# Số records tối thiểu mỗi làng nghề (nếu backfill 2 năm ≈ 17520 giờ)
MIN_RECORDS_PER_VILLAGE = 1000

# Tần suất tối đa cho phép giữa 2 timestamp liên tiếp (giờ)
MAX_GAP_HOURS = 6

# Ngưỡng tương quan tối thiểu giữa pm25 và pm10 (chúng phải tương quan thuận)
MIN_PM25_PM10_CORR = 0.3


# ── Data class kết quả ───────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    passed: bool = True
    errors:   List[str] = field(default_factory=list)    # Lỗi nghiêm trọng → FAIL
    warnings: List[str] = field(default_factory=list)    # Cảnh báo → PASS nhưng cần xem
    stats:    Dict      = field(default_factory=dict)    # Thống kê chi tiết

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.passed = False
        logger.error(f"  [FAIL] {msg}")

    def add_warning(self, msg: str):
        self.warnings.append(msg)
        logger.warning(f"  [WARN] {msg}")

    def add_stat(self, key: str, value):
        self.stats[key] = value

    def summary(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        lines = [
            f"\n{'='*50}",
            f"KẾT QUẢ VALIDATION: {status}",
            f"{'='*50}",
            f"Lỗi    : {len(self.errors)}",
            f"Cảnh báo: {len(self.warnings)}",
        ]
        if self.errors:
            lines.append("\n--- Lỗi nghiêm trọng ---")
            for e in self.errors:
                lines.append(f"  ✗ {e}")
        if self.warnings:
            lines.append("\n--- Cảnh báo ---")
            for w in self.warnings:
                lines.append(f"  ! {w}")
        return "\n".join(lines)


# ── Hàm validation chính ─────────────────────────────────────────────────────

def validate_dataset(df: pd.DataFrame,
                     raise_on_error: bool = False) -> ValidationResult:
    """
    Chạy toàn bộ các kiểm tra chất lượng dữ liệu.

    Args:
        df             : DataFrame đã qua clean_dataset()
        raise_on_error : Nếu True, raise ValueError khi có lỗi nghiêm trọng

    Returns:
        ValidationResult với trạng thái passed/failed và chi tiết
    """
    result = ValidationResult()

    logger.info("Bắt đầu validation dataset...")

    _check_not_empty(df, result)
    if not result.passed:
        # Không tiếp tục nếu rỗng
        if raise_on_error:
            raise ValueError(result.errors[0])
        return result

    _check_required_columns(df, result)
    _check_villages_coverage(df, result)
    _check_record_count_per_village(df, result)
    _check_missing_rates(df, result)
    _check_time_continuity(df, result)
    _check_value_distributions(df, result)
    _check_pm25_pm10_correlation(df, result)
    _check_timestamp_timezone(df, result)
    _collect_statistics(df, result)

    print(result.summary())

    if raise_on_error and not result.passed:
        raise ValueError(
            f"Dataset không đạt yêu cầu: {len(result.errors)} lỗi. "
            f"Chi tiết: {result.errors}"
        )

    return result


# ── Các kiểm tra cụ thể ──────────────────────────────────────────────────────

def _check_not_empty(df: pd.DataFrame, result: ValidationResult):
    if df is None or len(df) == 0:
        result.add_error("Dataset rỗng — không có records nào")


def _check_required_columns(df: pd.DataFrame, result: ValidationResult):
    required = ["timestamp", "village", "pm25"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        result.add_error(f"Thiếu cột bắt buộc: {missing}")


def _check_villages_coverage(df: pd.DataFrame, result: ValidationResult):
    """Kiểm tra đủ 5 làng nghề."""
    found    = set(df["village"].unique())
    expected = set(EXPECTED_VILLAGES)
    missing  = expected - found
    extra    = found - expected

    if missing:
        result.add_error(f"Thiếu dữ liệu cho {len(missing)} làng nghề: {sorted(missing)}")
    if extra:
        result.add_warning(f"Có làng nghề không trong danh sách: {sorted(extra)}")

    result.add_stat("villages_found", sorted(found))
    result.add_stat("villages_missing", sorted(missing))


def _check_record_count_per_village(df: pd.DataFrame, result: ValidationResult):
    """Kiểm tra số lượng records tối thiểu cho mỗi làng nghề."""
    counts = df.groupby("village").size()
    result.add_stat("records_per_village", counts.to_dict())

    for village, count in counts.items():
        if count < MIN_RECORDS_PER_VILLAGE:
            result.add_error(
                f"[{village}] chỉ có {count:,} records "
                f"(tối thiểu {MIN_RECORDS_PER_VILLAGE:,})"
            )
        else:
            logger.info(f"  [{village}] {count:,} records — OK")


def _check_missing_rates(df: pd.DataFrame, result: ValidationResult):
    """Kiểm tra tỷ lệ missing value cho từng cột quan trọng."""
    missing_report = {}

    for col, max_pct in MAX_MISSING_PCT.items():
        if col not in df.columns:
            result.add_warning(f"Cột [{col}] không tồn tại trong dataset")
            continue

        pct = df[col].isna().mean() * 100
        missing_report[col] = round(pct, 2)

        if pct > max_pct:
            result.add_error(
                f"Cột [{col}] thiếu {pct:.1f}% (ngưỡng tối đa {max_pct}%)"
            )
        elif pct > max_pct * 0.7:
            result.add_warning(
                f"Cột [{col}] thiếu {pct:.1f}% — đang tiếp cận ngưỡng"
            )

    result.add_stat("missing_pct_per_col", missing_report)


def _check_time_continuity(df: pd.DataFrame, result: ValidationResult):
    """Kiểm tra khoảng cách thời gian giữa các records liên tiếp."""
    gaps_found = {}

    for village, group in df.groupby("village"):
        group = group.sort_values("timestamp")
        diffs = group["timestamp"].diff().dropna()

        # Khoảng cách tính bằng giờ
        gap_hours = diffs.dt.total_seconds() / 3600
        large_gaps = gap_hours[gap_hours > MAX_GAP_HOURS]

        if len(large_gaps) > 0:
            max_gap = large_gaps.max()
            gaps_found[village] = {
                "count": len(large_gaps),
                "max_gap_hours": round(max_gap, 1)
            }
            if max_gap > 24:
                result.add_error(
                    f"[{village}] có khoảng trống {max_gap:.0f}h — "
                    f"mất liên tục nghiêm trọng"
                )
            else:
                result.add_warning(
                    f"[{village}] có {len(large_gaps)} khoảng trống > {MAX_GAP_HOURS}h "
                    f"(lớn nhất: {max_gap:.1f}h)"
                )

    result.add_stat("time_gaps", gaps_found)


def _check_value_distributions(df: pd.DataFrame, result: ValidationResult):
    """
    Kiểm tra phân phối giá trị — phát hiện dữ liệu bất thường:
    - Toàn bộ giá trị giống nhau (stuck sensor)
    - Giá trị âm
    - Giá trị quá cao bất thường
    """
    suspicious = {}

    checks: List[Tuple[str, float, str]] = [
        ("pm25",  500.0, "µg/m³"),
        ("pm10",  800.0, "µg/m³"),
        ("so2",   500.0, "µg/m³"),
        ("no2",   400.0, "µg/m³"),
        ("co",  50000.0, "µg/m³"),
        ("o3",    300.0, "µg/m³"),
    ]

    for col, warn_threshold, unit in checks:
        if col not in df.columns:
            continue

        series = df[col].dropna()
        if len(series) == 0:
            continue

        # Kiểm tra giá trị âm
        neg_count = (series < 0).sum()
        if neg_count > 0:
            result.add_error(f"Cột [{col}] có {neg_count} giá trị âm")

        # Kiểm tra cực đại bất thường
        p99 = series.quantile(0.99)
        if p99 > warn_threshold:
            result.add_warning(
                f"Cột [{col}] p99 = {p99:.1f} {unit} — cực cao bất thường"
            )
            suspicious[col] = p99

        # Kiểm tra dữ liệu bị "đóng băng" (>80% giá trị giống nhau)
        top_val_pct = series.value_counts(normalize=True).iloc[0] * 100
        if top_val_pct > 80:
            result.add_warning(
                f"Cột [{col}] có {top_val_pct:.0f}% giá trị trùng nhau "
                f"— có thể cảm biến bị lỗi"
            )

    result.add_stat("suspicious_high_values", suspicious)


def _check_pm25_pm10_correlation(df: pd.DataFrame, result: ValidationResult):
    """
    PM2.5 và PM10 phải tương quan thuận (PM10 ≥ PM2.5 về mặt vật lý).
    Tương quan thấp hoặc âm = dữ liệu có vấn đề.
    """
    if "pm25" not in df.columns or "pm10" not in df.columns:
        return

    valid = df[["pm25", "pm10"]].dropna()
    if len(valid) < 10:
        result.add_warning("Không đủ dữ liệu để kiểm tra tương quan PM2.5/PM10")
        return

    corr = valid["pm25"].corr(valid["pm10"])
    result.add_stat("pm25_pm10_correlation", round(corr, 4))

    if corr < 0:
        result.add_error(
            f"PM2.5 và PM10 tương quan ÂM ({corr:.3f}) — dữ liệu có vấn đề"
        )
    elif corr < MIN_PM25_PM10_CORR:
        result.add_warning(
            f"Tương quan PM2.5/PM10 thấp ({corr:.3f}) — "
            f"kỳ vọng ≥ {MIN_PM25_PM10_CORR}"
        )
    else:
        logger.info(f"  Tương quan PM2.5/PM10: {corr:.3f} — OK")

    # Kiểm tra logic: PM10 phải ≥ PM2.5
    invalid_ratio = (valid["pm10"] < valid["pm25"]).sum()
    if invalid_ratio > len(valid) * 0.05:
        result.add_warning(
            f"{invalid_ratio:,} records có PM10 < PM2.5 "
            f"({invalid_ratio/len(valid)*100:.1f}%) — vi phạm vật lý"
        )


def _check_timestamp_timezone(df: pd.DataFrame, result: ValidationResult):
    """Kiểm tra timestamp có timezone-aware hay không."""
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        result.add_error("Cột timestamp không phải kiểu datetime")
        return

    if df["timestamp"].dt.tz is None:
        result.add_warning(
            "Timestamp không có timezone — nên dùng UTC để tránh lỗi DST"
        )
    else:
        logger.info(f"  Timezone: {df['timestamp'].dt.tz} — OK")


def _collect_statistics(df: pd.DataFrame, result: ValidationResult):
    """Thu thập thống kê tổng quát để báo cáo."""
    result.add_stat("total_records", len(df))
    result.add_stat("date_start", str(df["timestamp"].min()))
    result.add_stat("date_end",   str(df["timestamp"].max()))
    result.add_stat("days_covered",
                    (df["timestamp"].max() - df["timestamp"].min()).days)

    # Thống kê mô tả cho các chỉ số chính
    key_cols = [c for c in ["pm25","pm10","so2","no2","co","o3",
                             "temperature","humidity"] if c in df.columns]
    desc = df[key_cols].describe().round(2)
    result.add_stat("descriptive_stats", desc.to_dict())

    # Missing summary
    missing_counts = df.isna().sum()
    result.add_stat("total_missing_values", int(missing_counts.sum()))


# ── Hàm tiện ích độc lập ─────────────────────────────────────────────────────

def print_data_quality_report(df: pd.DataFrame):
    """In báo cáo chất lượng dữ liệu nhanh ra console."""
    print("\n" + "="*55)
    print("BÁO CÁO CHẤT LƯỢNG DỮ LIỆU")
    print("="*55)

    print(f"\nTổng records    : {len(df):,}")
    print(f"Số làng nghề    : {df['village'].nunique()}")

    if pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        print(f"Từ ngày         : {df['timestamp'].min()}")
        print(f"Đến ngày        : {df['timestamp'].max()}")

    print("\n--- Records theo làng nghề ---")
    for village, count in df.groupby("village").size().items():
        print(f"  {village:<20} {count:>8,} records")

    key_cols = [c for c in ["pm25","pm10","so2","no2","co","o3",
                             "temperature","humidity","wind_speed"]
                if c in df.columns]

    print("\n--- Tỷ lệ missing (%) ---")
    for col in key_cols:
        pct = df[col].isna().mean() * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        status = "OK" if pct < 10 else ("!" if pct < 20 else "✗")
        print(f"  [{status}] {col:<18} {pct:5.1f}%  {bar}")

    print("\n--- Thống kê PM2.5 theo làng nghề ---")
    if "pm25" in df.columns:
        stats = df.groupby("village")["pm25"].agg(
            ["mean", "median", "max", "std"]
        ).round(2)
        print(stats.to_string())


# ── Test nhanh ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    # Tạo dataset mẫu với 17 làng nghề giám sát (bỏ baseline)
    villages = EXPECTED_VILLAGES  # 17 làng từ villages.yaml
    times = pd.date_range("2023-01-01", periods=2000, freq="h", tz="UTC")

    frames = []
    rng = np.random.default_rng(42)
    for v in villages:
        frames.append(pd.DataFrame({
            "timestamp":   times,
            "village":     v,
            "pm25":        rng.uniform(10, 120, 2000),
            "pm10":        rng.uniform(20, 200, 2000),
            "so2":         rng.uniform(5,   50, 2000),
            "no2":         rng.uniform(5,   80, 2000),
            "co":          rng.uniform(200, 2000, 2000),
            "o3":          rng.uniform(20, 120, 2000),
            "temperature": rng.uniform(18,  38, 2000),
            "humidity":    rng.uniform(50,  95, 2000),
            "wind_speed":  rng.uniform(0,   10, 2000),
        }))

    sample_df = pd.concat(frames, ignore_index=True)

    print("=== Test Validator ===")
    print_data_quality_report(sample_df)

    result = validate_dataset(sample_df)
    print(f"\nKết quả: {'PASSED' if result.passed else 'FAILED'}")
    print(f"Errors  : {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")