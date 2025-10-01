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

# def execute_sql_query(query: str):
#     """
#     Mengeksekusi query SQL mentah dengan aman dan mengembalikan hasilnya
#     dalam format string yang bisa dibaca oleh LLM.
#     """
#     print(f"Mengeksekusi query: {query}")
#     try:
#         # Menggunakan 'with' memastikan koneksi ditutup secara otomatis
#         with engine.connect() as connection:
#             # Menggunakan text() dari SQLAlchemy membantu mencegah SQL Injection
#             result_df = pd.read_sql_query(sql=text(query), con=connection)
            
#             if result_df.empty:
#                 return "Query berhasil dieksekusi, namun tidak ada data yang ditemukan."
            
#             # Mengubah DataFrame menjadi format string tabel yang rapi
#             # Ini adalah format yang sangat baik untuk dipahami oleh LLM
#             return result_df.to_string()
            
#     except Exception as e:
#         # Menangkap error jika SQL yang di-generate oleh LLM tidak valid
#         print(f"Error saat eksekusi SQL: {e}")
#         return f"Terjadi error saat eksekusi SQL: {str(e)}"

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
