import pandas as pd
from sqlalchemy import text
from src.db.config_mysql import get_engine

engine = get_engine()

def execute_sql_query(query: str):
    """
    Mengeksekusi query SQL dan mengembalikan hasilnya sebagai
    DataFrame Pandas atau sebuah string error.
    """
    print(f"Mengeksekusi query: {query}")
    try:
        with engine.connect() as connection:
            result_df = pd.read_sql_query(sql=text(query), con=connection)
            return result_df 
            
    except Exception as e:
        print(f"Error saat eksekusi SQL: {e}")
        return f"Terjadi error saat eksekusi SQL: {str(e)}"
