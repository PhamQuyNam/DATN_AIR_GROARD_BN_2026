import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL").replace("Quynam26@", "Quynam26%40")
engine = create_engine(DATABASE_URL)

def check():
    insp = inspect(engine)
    tables = insp.get_table_names()
    print(f"Tables found: {tables}")
    
    for table in ["village", "stations"]:
        if table in tables:
            cols = [c["name"] for c in insp.get_columns(table)]
            print(f"Columns in '{table}': {cols}")
        else:
            print(f"Table '{table}' does not exist.")

if __name__ == "__main__":
    check()
