"""
app/api/routes/citizen.py
Cổng người dân: quản lý trạm yêu thích, xem feed AQI + cảnh báo + khuyến nghị cá nhân hóa.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, timedelta

from app.core.database import get_session
from app.models.db_models import (
    User, UserFavoriteStation, AQILog, AlertHistory, Recommendation, Village
)
from app.api.routes.auth import get_current_user

router = APIRouter()

# ── Quản lý trạm yêu thích ────────────────────────────────────────────────────

@router.get("/citizen/favorites")
def get_favorites(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Lấy danh sách trạm yêu thích của người dùng hiện tại."""
    favs = session.exec(
        select(UserFavoriteStation)
        .where(UserFavoriteStation.user_id == current_user.id)
    ).all()
    return {"favorites": [f.village_name for f in favs]}

@router.post("/citizen/favorites/{village_name}", status_code=201)
def add_favorite(
    village_name: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Thêm một làng vào danh sách quan tâm của người dùng."""
    village = session.exec(select(Village).where(Village.name == village_name)).first()
    if not village:
        raise HTTPException(status_code=404, detail="Không tìm thấy làng nghề")

    # Kiểm tra đã tồn tại chưa
    existing = session.exec(
        select(UserFavoriteStation)
        .where(UserFavoriteStation.user_id == current_user.id)
        .where(UserFavoriteStation.village_name == village_name)
    ).first()
    if existing:
        return {"message": "Đã có trong danh sách yêu thích"}

    fav = UserFavoriteStation(user_id=current_user.id, village_name=village_name)
    session.add(fav)
    session.commit()
    return {"message": f"Đã thêm {village_name} vào danh sách quan tâm"}

@router.delete("/citizen/favorites/{village_name}")
def remove_favorite(
    village_name: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Xóa một làng khỏi danh sách quan tâm."""
    fav = session.exec(
        select(UserFavoriteStation)
        .where(UserFavoriteStation.user_id == current_user.id)
        .where(UserFavoriteStation.village_name == village_name)
    ).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Không có trong danh sách yêu thích")
    session.delete(fav)
    session.commit()
    return {"message": f"Đã xóa {village_name} khỏi danh sách quan tâm"}

# ── Feed cá nhân hóa ──────────────────────────────────────────────────────────

@router.get("/citizen/feed")
def get_citizen_feed(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Lấy toàn bộ thông tin cá nhân hóa cho người dân:
    AQI mới nhất, dự báo, cảnh báo và khuyến nghị
    của các trạm trong danh sách yêu thích.
    """
    # Lấy danh sách trạm yêu thích
    favs = session.exec(
        select(UserFavoriteStation).where(UserFavoriteStation.user_id == current_user.id)
    ).all()
    fav_villages = [f.village_name for f in favs]

    stations_data = []
    for village_name in fav_villages:
        # AQI mới nhất
        latest_aqi = session.exec(
            select(AQILog)
            .where(AQILog.village_name == village_name)
            .order_by(AQILog.timestamp.desc())
            .limit(1)
        ).first()

        # ── Cảnh báo đã được Admin PHÊ DUYỆT (is_approved=True) ──────────────
        # Không giới hạn thời gian — chỉ cần admin đã duyệt
        approved_alerts = session.exec(
            select(AlertHistory)
            .where(AlertHistory.village_name == village_name)
            .where(AlertHistory.is_approved == True)
            .order_by(AlertHistory.approved_at.desc())
            .limit(20)  # Tăng từ 3 → 20 để hiển thị đủ cảnh báo
        ).all()

        # ── Tất cả khuyến nghị đang hoạt động từ Manager ──────────────────────
        all_recs = session.exec(
            select(Recommendation)
            .where(Recommendation.village_name == village_name)
            .where(Recommendation.is_active == True)
            .order_by(Recommendation.created_at.desc())
        ).all()

        stations_data.append({
            "village_name": village_name,
            "aqi": latest_aqi.aqi if latest_aqi else None,
            "level": latest_aqi.level if latest_aqi else "Không có dữ liệu",
            "pm25": latest_aqi.pm25 if latest_aqi else None,
            "temperature": latest_aqi.temperature if latest_aqi else None,
            "last_updated": latest_aqi.timestamp if latest_aqi else None,
            # Cảnh báo đã duyệt
            "has_alert": len(approved_alerts) > 0,
            "alert_message": approved_alerts[0].message if approved_alerts else None,
            "alert_aqi": approved_alerts[0].aqi_value if approved_alerts else None,
            "alert_time": approved_alerts[0].approved_at if approved_alerts else None,
            "all_alerts": [
                {
                    "message": a.message,
                    "aqi_value": a.aqi_value,
                    "threshold_value": a.threshold_value,
                    "approved_at": a.approved_at,
                }
                for a in approved_alerts
            ],
            # Tất cả khuyến nghị đang hoạt động (không giới hạn 1 bản)
            "recommendation": all_recs[0].content if all_recs else None,
            "rec_time": all_recs[0].created_at if all_recs else None,
            "all_recommendations": [
                {
                    "content": r.content,
                    "created_at": r.created_at,
                }
                for r in all_recs
            ],
        })

    return {
        "user": {"full_name": current_user.full_name, "email": current_user.email},
        "favorite_count": len(fav_villages),
        "stations": stations_data
    }
