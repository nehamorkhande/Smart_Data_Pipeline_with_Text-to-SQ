from sqlalchemy import create_engine,text
from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DB_URL=(
    f"mysql+pymysql://{DB_USER}:{DB_PASS}"
    f"@{DB_HOST}/{DB_NAME}"
)
engine = create_engine(
    DB_URL,
    echo=False
)

def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ Database connected successfully!")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

# ── Run test when file is executed directly ──────────────────
if __name__ == "__main__":
    print(f"Connecting to  : {DB_HOST}")
    print(f"Database name  : {DB_NAME}")
    print(f"Username       : {DB_USER}")
    print("-" * 40)
    test_connection()