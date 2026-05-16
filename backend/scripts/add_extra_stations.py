import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import Village, AlertConfig, AQILog

def add_extra():
    extra_villages = [
        ('Tràng An', 21.185, 106.085),
        ('Ninh Xá', 21.175, 106.065),
        ('Dương Ổ', 21.165, 106.015),
        ('Quế Cầm', 21.125, 106.155),
        ('Tương Giang', 21.145, 105.975),
        ('Vọng Nguyệt', 21.215, 105.970),
    ]
    
    with Session(engine) as session:
        for name, lat, lon in extra_villages:
            # 1. Thêm Village
            existing = session.exec(select(Village).where(Village.name == name)).first()
            if not existing:
                v = Village(name=name, location='Bắc Ninh', lat=lat, lon=lon, pollution_level='Trung bình', is_active=True)
                session.add(v)
            
            # 2. Thêm AlertConfig
            conf = session.exec(select(AlertConfig).where(AlertConfig.village_name == name)).first()
            if not conf:
                session.add(AlertConfig(village_name=name, aqi_threshold=150, is_active=True))
            
            # 3. Thêm dữ liệu AQI mẫu (để hiện lên bản đồ)
            log = AQILog(village_name=name, timestamp=datetime.now(), pm25=18.5, aqi=52.0, level='Trung bình')
            session.add(log)
            
        session.commit()
    print("✅ Hoàn tất bổ sung trạm và dữ liệu mẫu!")

if __name__ == "__main__":
    add_extra()
