from datetime import datetime
from sqlalchemy import text
from src.db.config_mysql import get_engine

engine = get_engine()

def insert_trx_pertanyaan(
    unit: str,
    nip: str,
    user_prompt: str,
    token_in: int,
    token_out: int,
    token_total: int,
    output_query: str,
    output_data_raw: str,
    output_analisa: str,
    apps: str = "e - budgeting",
):
    try:
        insert_sql = text("""
            INSERT INTO trx_pertanyaan ( unit,
                                         nip,
                                         user_promt,
                                         token_in,
                                         token_out,
                                         token_total,
                                         output_query,
                                         output_data_raw,
                                         output_analisa,
                                         apps,
                                         udcr
                                        ) VALUES (
                                            :unit,
                                            :nip,
                                            :user_prompt,
                                            :token_in,
                                            :token_out,
                                            :token_total,
                                            :output_query,
                                            :output_data_raw,
                                            :output_analisa,
                                            :apps,
                                            :udcr
                                    )
                          """)
        with engine.connect() as connection:
            connection.execute(
                insert_sql,
                {
                    "unit": unit,
                    "nip": nip,
                    "user_prompt": user_prompt,
                    "token_in": token_in,
                    "token_out": token_out,
                    "token_total": token_total,
                    "output_query": output_query,
                    "output_data_raw": output_data_raw,
                    "output_analisa": output_analisa,
                    "apps": apps,
                    "udcr": datetime.now(),
                },
            )
            connection.commit()  # commit manual karena pakai connection-level
        print("✅ Insert trx_pertanyaan berhasil")

    except Exception as e:
        print(f"❌ Gagal insert trx_pertanyaan: {e}")

def get_all_trx_pertanyaan(limit: int = 300):
    try:
        select_sql = text("""
            SELECT * FROM trx_pertanyaan LIMIT :limit
        """)
        with engine.connect() as connection:
            result = connection.execute(select_sql, {"limit": limit})
            rows = result.fetchall()
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
        return data

    except Exception as e:
        print(f"❌ Gagal mengambil data trx_pertanyaan: {e}")
        return []

def get_trx_pertanyaan_by_id(id_pertanyaan: int):
    try:
        select_sql = text("""
            SELECT * FROM trx_pertanyaan WHERE id_pertanyaan = :id_pertanyaan
        """)
        with engine.connect() as connection:
            result = connection.execute(select_sql, {"id_pertanyaan": id_pertanyaan})
            row = result.fetchone()  # ✅ ambil satu baris
            if row:
                columns = result.keys()
                data = dict(zip(columns, row))
                return data
            else:
                return None
    except Exception as e:
        print(f"❌ Gagal mengambil data trx_pertanyaan by nip: {e}")
        return None

def get_trx_pertanyaan_by_nip(nip: int):
    try:
        select_sql = text("""
            SELECT * FROM trx_pertanyaan WHERE nip = :nip
        """)
        with engine.connect() as connection:
            result = connection.execute(select_sql, {"nip": nip})
            rows = result.fetchall()  # ✅ ambil semua baris
            if rows:
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]
                return data
            else:
                return []
    except Exception as e:
        print(f"❌ Gagal mengambil data trx_pertanyaan by nip: {e}")
        return []
