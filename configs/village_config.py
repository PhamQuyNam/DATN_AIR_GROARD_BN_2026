"""
configs/village_config.py

Module trung tâm quản lý cấu hình 18 làng nghề Bắc Ninh.
Import module này ở BẤT KỲ đâu trong dự án thay vì đọc YAML thủ công.

Cách dùng:
    from configs.village_config import VILLAGES, get_village, get_all_coords
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
import yaml

# ── Load YAML một lần duy nhất khi import ───────────────────────────────────
_CONFIG_PATH = Path(__file__).parent / "villages.yaml"

def _load() -> list[dict]:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)["villages"]

VILLAGES: list[dict] = _load()


# ── Lookup helpers ───────────────────────────────────────────────────────────

def get_village(name: str) -> Optional[dict]:
    """Tìm làng nghề theo tên (không phân biệt hoa/thường)."""
    name_lower = name.strip().lower()
    for v in VILLAGES:
        if v["name"].lower() == name_lower:
            return v
    return None


def get_village_by_id(village_id: int) -> Optional[dict]:
    """Tìm làng nghề theo ID (1–18)."""
    for v in VILLAGES:
        if v["id"] == village_id:
            return v
    return None


def get_villages_by_level(level: str) -> list[dict]:
    """
    Lọc theo mức độ ô nhiễm.
    level: 'very_high' | 'high' | 'medium' | 'low'
    """
    return [v for v in VILLAGES if v.get("pollution_level") == level]


def get_all_coords() -> list[tuple[str, float, float]]:
    """
    Trả về list (name, lat, lon) cho tất cả làng nghề.
    Dùng khi cần lặp qua tọa độ để gọi API.
    """
    return [(v["name"], v["lat"], v["lon"]) for v in VILLAGES]


def get_monitoring_villages() -> list[dict]:
    """
    Trả về tất cả làng nghề trừ trạm đối chứng baseline (Vọng Nguyệt).
    Dùng khi chỉ muốn thu thập dữ liệu ô nhiễm thực sự.
    """
    return [v for v in VILLAGES if not v.get("is_baseline", False)]


def get_baseline_village() -> Optional[dict]:
    """Trả về làng nghề đối chứng (Vọng Nguyệt)."""
    for v in VILLAGES:
        if v.get("is_baseline", False):
            return v
    return None


def get_names() -> list[str]:
    """Danh sách tên tất cả làng nghề."""
    return [v["name"] for v in VILLAGES]


def village_to_openmeteo_params(village: dict,
                                extra: Optional[dict] = None) -> dict:
    """
    Tạo dict params cơ bản để truyền vào Open-Meteo API call.

    Args:
        village: dict làng nghề từ VILLAGES
        extra  : tham số bổ sung (vd: {"start_date": "...", "end_date": "..."})

    Returns:
        dict params sẵn sàng truyền vào requests.get(..., params=...)
    """
    params = {
        "latitude":  village["lat"],
        "longitude": village["lon"],
        "timezone":  "Asia/Ho_Chi_Minh",
    }
    if extra:
        params.update(extra)
    return params


# ── Pretty print ─────────────────────────────────────────────────────────────

def print_village_summary():
    """In bảng tóm tắt 18 làng nghề ra console."""
    level_icon = {
        "very_high": "🔴",
        "high":      "🟠",
        "medium":    "🟡",
        "low":       "🟢",
    }
    print(f"\n{'ID':>3}  {'Tên làng nghề':<18} {'Vị trí':<30} "
          f"{'Lat':>8} {'Lon':>9}  {'Mức ô nhiễm':<12}  {'Chỉ số chính'}")
    print("─" * 110)
    for v in VILLAGES:
        icon  = level_icon.get(v.get("pollution_level", ""), "⚪")
        polls = ", ".join(v.get("key_pollutants", [])) or "(đối chứng)"
        baseline = " ★" if v.get("is_baseline") else ""
        print(f"{v['id']:>3}  {v['name']:<18} {v['location']:<30} "
              f"{v['lat']:>8.4f} {v['lon']:>9.4f}  "
              f"{icon} {v.get('pollution_level',''):<10}  {polls}{baseline}")
    print(f"\nTổng: {len(VILLAGES)} làng nghề  |  "
          f"★ = trạm đối chứng baseline")


# ── Xuất ra dict/list cho các module khác ────────────────────────────────────

# Dùng nhanh khi chỉ cần tên → tọa độ
VILLAGE_COORDS: dict[str, tuple[float, float]] = {
    v["name"]: (v["lat"], v["lon"]) for v in VILLAGES
}

# Dùng khi cần map tên → toàn bộ thông tin
VILLAGE_MAP: dict[str, dict] = {
    v["name"]: v for v in VILLAGES
}

# Danh sách làng nghề thực sự ô nhiễm (bỏ baseline)
MONITORING_VILLAGES: list[dict] = get_monitoring_villages()

# Tên tất cả làng nghề
VILLAGE_NAMES: list[str] = get_names()


# ── Test khi chạy trực tiếp ──────────────────────────────────────────────────
if __name__ == "__main__":
    print_village_summary()

    print(f"\n── Làng nghề ô nhiễm rất cao ──")
    for v in get_villages_by_level("very_high"):
        print(f"  • {v['name']} — {v['note']}")

    print(f"\n── Trạm đối chứng ──")
    baseline = get_baseline_village()
    if baseline:
        print(f"  • {baseline['name']} ({baseline['location']})")

    print(f"\n── Ví dụ params cho Open-Meteo (Đa Hội) ──")
    v = get_village("Đa Hội")
    params = village_to_openmeteo_params(v, {
        "start_date": "2023-01-01",
        "end_date":   "2023-12-31"
    })
    print(f"  {params}")