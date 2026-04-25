from apscheduler.schedulers.background import BackgroundScheduler
from app.services.collector_service import AQICollector
from app.services.inference_service import inference_service

scheduler = BackgroundScheduler()

def scheduled_update_job():
    print("⏰ Starting scheduled update job...")
    # 1. Thu thập dữ liệu từ Internet
    AQICollector.fetch_live_data()
    
    # 2. Chạy model dự báo
    inference_service.run_forecast_all()
    print("⏰ Scheduled update job finished.")

def start_scheduler():
    # Chạy lần đầu tiên ngay khi khởi động
    # scheduled_update_job() 
    
    # Thiết lập chạy định kỳ mỗi 1 giờ
    scheduler.add_job(scheduled_update_job, 'interval', hours=1)
    scheduler.start()
    print("🚀 Scheduler started. Jobs scheduled every 1 hour.")
