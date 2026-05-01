from datetime import datetime
from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import Village, AQILog, AlertConfig, AlertHistory


def seed_alert_configs():
    """
    Tự động tạo cấu hình cảnh báo mặc định (ngưỡng AQI = 150) cho tất cả
    các làng nghề chưa có cấu hình. Hàm này an toàn để gọi nhiều lần.
    """
    with Session(engine) as session:
        villages = session.exec(select(Village)).all()
        created = 0
        for v in villages:
            existing = session.exec(
                select(AlertConfig).where(AlertConfig.village_name == v.name)
            ).first()
            if not existing:
                config = AlertConfig(
                    village_name=v.name,
                    aqi_threshold=150.0,  # Mức "Kém" theo tiêu chuẩn QCVN
                    is_active=True
                )
                session.add(config)
                created += 1
        session.commit()
        if created > 0:
            print(f"✅ AlertConfig: Đã khởi tạo cấu hình cho {created} làng nghề.")


def check_and_create_alerts():
    """
    So sánh AQI hiện tại (bản ghi mới nhất) với ngưỡng đã cấu hình.
    Nếu AQI > ngưỡng và chưa có cảnh báo trong vòng 1 giờ qua → Tạo cảnh báo mới.
    """
    with Session(engine) as session:
        configs = session.exec(
            select(AlertConfig).where(AlertConfig.is_active == True)
        ).all()

        alert_count = 0
        for config in configs:
            # Lấy bản ghi AQI mới nhất của làng nghề
            latest_log = session.exec(
                select(AQILog)
                .where(AQILog.village_name == config.village_name)
                .order_by(AQILog.timestamp.desc())
                .limit(1)
            ).first()

            if not latest_log:
                continue

            # Kiểm tra có vượt ngưỡng không
            if latest_log.aqi > config.aqi_threshold:
                # Tránh spam: chỉ tạo 1 cảnh báo mỗi giờ cho mỗi làng nghề
                from datetime import timedelta
                one_hour_ago = datetime.now() - timedelta(hours=1)

                recent_alert = session.exec(
                    select(AlertHistory)
                    .where(AlertHistory.village_name == config.village_name)
                    .where(AlertHistory.timestamp >= one_hour_ago)
                    .limit(1)
                ).first()

                if not recent_alert:
                    alert = AlertHistory(
                        village_name=config.village_name,
                        timestamp=datetime.now(),
                        aqi_value=latest_log.aqi,
                        threshold_value=config.aqi_threshold,
                        message=f"⚠️ AQI đạt {latest_log.aqi:.0f} - Mức '{latest_log.level}' tại {config.village_name}. Vượt ngưỡng cảnh báo {config.aqi_threshold:.0f}."
                    )
                    session.add(alert)
                    alert_count += 1

        session.commit()
        if alert_count > 0:
            print(f"🚨 AlertService: Đã tạo {alert_count} cảnh báo mới.")
        else:
            print("✅ AlertService: Không có làng nghề nào vượt ngưỡng.")
