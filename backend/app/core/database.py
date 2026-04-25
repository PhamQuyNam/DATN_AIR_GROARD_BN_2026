import os
import time
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# HACK: Nếu chạy trong Docker, tự động đổi localhost thành db và xử lý ký tự đặc biệt
if os.path.exists("/app"):
    if "localhost" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("localhost", "db")
    # Đảm bảo mật khẩu được encode đúng nếu chứa ký tự đặc biệt như @
    # (Trường hợp Docker Compose truyền biến môi trường vào chưa chuẩn)
    if "Quynam26@" in DATABASE_URL and "Quynam26%40" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("Quynam26@", "Quynam26%40")

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            SQLModel.metadata.create_all(engine)
            print("✅ Database initialized successfully!")
            break
        except OperationalError as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Database not ready (attempt {attempt+1}/{max_retries}). Retrying in 5s...")
                time.sleep(5)
            else:
                print("❌ Max retries reached. Database connection failed.")
                raise e

def get_session():
    with Session(engine) as session:
        yield session
