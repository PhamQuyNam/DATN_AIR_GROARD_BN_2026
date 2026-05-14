import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Xử lý URL nếu cần (giống trong core/database.py)
if "Quynam26@" in DATABASE_URL and "Quynam26%40" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("Quynam26@", "Quynam26%40")

engine = create_engine(DATABASE_URL)

def add_is_active_column():
    print("Adding 'is_active' column to 'village' table...")
    try:
        with engine.connect() as conn:
            # Thêm cột is_active với giá trị mặc định là True
            conn.execute(text("ALTER TABLE village ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"))
            conn.commit()
            print("Successfully added 'is_active' column!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_is_active_column()
