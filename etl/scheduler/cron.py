from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron       import CronTrigger
import logging, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from etl.scheduler.jobs import hourly_update_job

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/etl.log", encoding="utf-8")
    ]
)

if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="Asia/Ho_Chi_Minh")
    scheduler.add_job(
        hourly_update_job,
        trigger=CronTrigger(minute=5),   # HH:05 mỗi giờ
        id="hourly_aqi_update",
        misfire_grace_time=300
    )
    logging.info("Scheduler khởi động — cập nhật lúc HH:05 mỗi giờ")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logging.info("Scheduler đã dừng.")