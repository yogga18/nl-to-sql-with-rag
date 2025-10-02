import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Load konfigurasi dari .env
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Format URL koneksi SQLAlchemy untuk MySQL dengan PyMySQL
DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"

# Membuat engine SQLAlchemy
engine = create_engine(DATABASE_URL)

def execute_sql_query(query: str):
    """
    Mengeksekusi query SQL dan mengembalikan hasilnya sebagai
    DataFrame Pandas atau sebuah string error.
    """
    print(f"Mengeksekusi query: {query}")
    try:
        with engine.connect() as connection:
            result_df = pd.read_sql_query(sql=text(query), con=connection)
            # --> UBAHAN: Kembalikan DataFrame langsung
            return result_df 
            
    except Exception as e:
        print(f"Error saat eksekusi SQL: {e}")
        return f"Terjadi error saat eksekusi SQL: {str(e)}"
