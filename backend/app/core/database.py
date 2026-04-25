import os
import time
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

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
