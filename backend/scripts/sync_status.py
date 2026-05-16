import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import Village, AlertConfig

def sync_all():
    with Session(engine) as session:
        configs = session.exec(select(AlertConfig)).all()
        for c in configs:
            village = session.exec(select(Village).where(Village.name == c.village_name)).first()
            if village:
                # Sync Village status to AlertConfig status
                village.is_active = c.is_active
                session.add(village)
        session.commit()
        print("✅ Đã đồng bộ hóa trạng thái cho tất cả các trạm!")

if __name__ == "__main__":
    sync_all()
