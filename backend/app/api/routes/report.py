"""
app/api/routes/report.py
Endpoint tổng hợp báo cáo toàn diện theo làng nghề và kỳ thời gian.
"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_session
from app.models.db_models import AQILog, AlertHistory, Recommendation, Village
from app.api.routes.auth import get_current_manager
from app.models.db_models import User

router = APIRouter()

LEVEL_ORDER = ['Tốt', 'Trung bình', 'Kém', 'Xấu', 'Rất xấu', 'Nguy hại']

@router.get("/report/generate")
def generate_report(
    village: Optional[str] = Query(None, description="Tên làng nghề (None = tất cả)"),
    period: str = Query("week", description="'week' | 'month'"),
    session: Session = Depends(get_session),
    current_manager: User = Depends(get_current_manager)
):
    """MANAGER: Tạo báo cáo tổng hợp AQI, cảnh báo và khuyến nghị."""

    since = datetime.utcnow() - (timedelta(days=7) if period == "week" else timedelta(days=30))
    period_label = "7 ngày qua" if period == "week" else "30 ngày qua"

    # ── 1. Dữ liệu AQI trong kỳ ──────────────────────────────────────────────
    aqi_q = select(AQILog).where(AQILog.timestamp >= since)
    if village:
        aqi_q = aqi_q.where(AQILog.village_name == village)
    aqi_logs = session.exec(aqi_q.order_by(AQILog.timestamp)).all()

    all_aqi = [log.aqi for log in aqi_logs]
    overall_avg = round(sum(all_aqi) / len(all_aqi)) if all_aqi else 0
    overall_max = round(max(all_aqi)) if all_aqi else 0
    overall_min = round(min(all_aqi)) if all_aqi else 0

    # Thống kê theo từng ngày
    daily = {}
    for log in aqi_logs:
        day = log.timestamp.strftime("%Y-%m-%d")
        if day not in daily:
            daily[day] = []
        daily[day].append(log.aqi)
    daily_summary = [
        {
            "date": d,
            "avg": round(sum(v) / len(v)),
            "max": round(max(v)),
            "min": round(min(v)),
            "count": len(v)
        }
        for d, v in sorted(daily.items())
    ]

    # Phân phối mức độ ô nhiễm
    level_dist = {}
    for log in aqi_logs:
        level_dist[log.level] = level_dist.get(log.level, 0) + 1
    level_distribution = [
        {"level": lvl, "count": level_dist.get(lvl, 0)}
        for lvl in LEVEL_ORDER if lvl in level_dist
    ]

    # Thống kê theo làng (nếu query tất cả)
    village_stats = {}
    if not village:
        for log in aqi_logs:
            if log.village_name not in village_stats:
                village_stats[log.village_name] = []
            village_stats[log.village_name].append(log.aqi)
        village_ranking = sorted([
            {"village": v, "avg_aqi": round(sum(vals)/len(vals)), "max_aqi": round(max(vals))}
            for v, vals in village_stats.items()
        ], key=lambda x: x["avg_aqi"], reverse=True)[:10]
    else:
        village_ranking = []

    # ── 2. Cảnh báo trong kỳ ─────────────────────────────────────────────────
    alert_q = select(AlertHistory).where(AlertHistory.timestamp >= since)
    if village:
        alert_q = alert_q.where(AlertHistory.village_name == village)
    alerts = session.exec(alert_q.order_by(AlertHistory.timestamp.desc()).limit(50)).all()
    alert_list = [
        {
            "village": a.village_name,
            "timestamp": a.timestamp,
            "aqi": a.aqi_value,
            "threshold": a.threshold_value,
            "message": a.message
        }
        for a in alerts
    ]

    # ── 3. Khuyến nghị đã gửi ────────────────────────────────────────────────
    rec_q = select(Recommendation).where(Recommendation.created_at >= since)
    if village:
        rec_q = rec_q.where(Recommendation.village_name == village)
    recs = session.exec(rec_q.order_by(Recommendation.created_at.desc()).limit(30)).all()
    rec_list = [
        {"village": r.village_name, "content": r.content, "created_at": r.created_at}
        for r in recs
    ]

    # ── 4. Metadata báo cáo ───────────────────────────────────────────────────
    return {
        "metadata": {
            "title": f"Báo cáo Chất lượng Không khí — {'Làng ' + village if village else 'Toàn bộ 18 làng nghề'}",
            "period_label": period_label,
            "generated_at": datetime.now(),
            "generated_by": current_manager.full_name,
            "village": village or "Tất cả làng nghề",
        },
        "aqi_summary": {
            "total_records": len(aqi_logs),
            "overall_avg": overall_avg,
            "overall_max": overall_max,
            "overall_min": overall_min,
        },
        "daily_data": daily_summary,
        "level_distribution": level_distribution,
        "village_ranking": village_ranking,
        "alerts": alert_list,
        "recommendations": rec_list,
    }
