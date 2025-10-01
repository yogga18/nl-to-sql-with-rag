# src/query_validator.py
import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML
import re

# --- DAFTAR HITAM (BLACKLIST) ---
# Daftar ini berisi fungsi dan kata kunci SQL yang berpotensi berbahaya
# bahkan di dalam sebuah query SELECT.
BLACKLISTED_FUNCTIONS = {
    'SLEEP', 'BENCHMARK', 'LOAD_FILE',
    'SYS_EVAL', 'SYS_EXEC', 'SYS_GET'
}
BLACKLISTED_KEYWORDS = {
    'INTO', # Untuk mencegah INTO OUTFILE dan INTO DUMPFILE
    'FOR'   # Untuk mencegah FOR UPDATE dan FOR SHARE (locking)
}

def sanitize_sql_output(sql_string: str) -> str:
    """Membersihkan output LLM dari format Markdown code block."""
    # Menghapus ```sql di awal dan ``` di akhir
    match = re.search(r"```sql\n(.*?)\n```", sql_string, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Jika tidak ada format markdown, hapus whitespace saja
    return sql_string.strip()

def is_safe_select_query(query: str) -> bool:
    """
    Memvalidasi sebuah string query SQL untuk memastikan itu adalah
    query SELECT tunggal yang aman dan tidak mengandung fungsi/klausa berbahaya.
    """
    # --- Pemeriksaan Awal (Tetap Dipertahankan) ---
    parsed = sqlparse.parse(query)
    if not parsed or len(parsed) == 0:
        return False

    if len(parsed) > 1:
        print("Validasi Gagal: Terdeteksi lebih dari satu statement SQL.")
        return False
        
    statement = parsed[0]
    
    if statement.get_type() != 'SELECT':
        print(f"Validasi Gagal: Tipe statement bukan SELECT, melainkan {statement.get_type()}.")
        return False
        
    # --- Pemeriksaan Lanjutan: Inspeksi Token ---
    # Kita akan memeriksa setiap "kata" di dalam query
    for token in statement.flatten():
        # 1. Periksa Kata Kunci Berbahaya (INTO, FOR)
        if token.ttype is Keyword and token.normalized in BLACKLISTED_KEYWORDS:
            print(f"Validasi Gagal: Terdeteksi kata kunci berbahaya '{token.normalized}'.")
            return False

        # 2. Periksa Fungsi Berbahaya (SLEEP, BENCHMARK, dll.)
        # Fungsi di sqlparse diidentifikasi sebagai Identifier yang memiliki tanda kurung
        if isinstance(token, Identifier):
            # Periksa apakah token ini adalah pemanggilan fungsi
            is_function_call = any(isinstance(sub_token, sqlparse.sql.Parenthesis) for sub_token in token.tokens)
            if is_function_call:
                # Ambil nama fungsinya (biasanya token pertama di dalam Identifier)
                function_name = token.get_name()
                if function_name and function_name.upper() in BLACKLISTED_FUNCTIONS:
                    print(f"Validasi Gagal: Terdeteksi pemanggilan fungsi berbahaya '{function_name.upper()}'.")
                    return False
        
    # Jika semua pemeriksaan lolos
    print("Validasi query SELECT berhasil.")
    return True