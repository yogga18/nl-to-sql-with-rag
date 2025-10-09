import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

# Load konfigurasi dari environment (.env)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_DATABASE = os.getenv("DB_DATABASE", "")
DB_USERNAME = os.getenv("DB_USERNAME", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Format URL koneksi SQLAlchemy untuk MySQL dengan PyMySQL
DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"

# Buat engine SQLAlchemy yang dapat digunakan di seluruh aplikasi
# Mengaktifkan pool_pre_ping agar koneksi dead/closed otomatis di-refresh
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def get_engine():
    """Kembalikan engine SQLAlchemy (helper)."""
    return engine
