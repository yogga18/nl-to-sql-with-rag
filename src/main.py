from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import os
from .nl2sql_service import create_nl2sql_chain, create_router_chain, create_analysis_chain, create_nl2sql_with_conversation_chain, create_analysis_with_conversation_chain
from .db_executor import execute_sql_query
import pandas as pd
from .query_validator import is_safe_select_query, sanitize_sql_output
from typing import Dict, List, Tuple, Optional

# Rate limiter using slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

load_dotenv()

# Model untuk request body
class QueryRequest(BaseModel):
    question: str
    
    class Config:
        schema_extra = {
            "example": {
                "question": "Tampilkan 5 program dengan anggaran terbesar di tahun 2024"
            }
        }

# Inisialisasi aplikasi FastAPI dengan dokumentasi lengkap
app = FastAPI(
    title="🤖 NL-to-SQL Service API",
    description="""
    ## API Cerdas untuk Mengkonversi Bahasa Natural ke Query SQL
    
    API ini menggunakan teknologi RAG (Retrieval-Augmented Generation) dan Google Gemini AI untuk:
    - 🔍 Menganalisis pertanyaan dalam bahasa Indonesia
    - 🛡️ Memvalidasi keamanan query SQL 
    - 💾 Mengeksekusi query ke database dengan aman
    - 🧠 Menganalisis hasil dan memberikan jawaban dalam bahasa natural
    - 💬 Mendukung percakapan berkelanjutan dengan memori konteks
    
    ### 🚀 Fitur Utama:
    - **Smart Routing**: Otomatis mendeteksi pertanyaan yang relevan dengan data perusahaan
    - **SQL Security**: Validasi keamanan untuk mencegah SQL injection dan query berbahaya
    - **Conversation Memory**: Mendukung percakapan multi-turn dengan konteks
    - **Flexible Output**: Berbagai endpoint untuk kebutuhan yang berbeda
    
    ### 📊 Database Target:
    Tabel utama: `drauk_unit` (Data Rencana Anggaran dan Kegiatan Unit)
    """,
    version="1.0.0",
    contact={
        "name": "NL-to-SQL Development Team",
        "email": "yogga@ecampus.ut.ac.id"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# ============================================================================
# CORS CONFIGURATION - PRODUCTION READY
# ============================================================================
# Konfigurasi CORS untuk mengizinkan akses dari domain yang diizinkan
# Untuk security yang lebih baik, set ALLOWED_ORIGINS di environment variable

# Get allowed origins from environment variable
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
if ALLOWED_ORIGINS == "*":
    origins = ["*"]
else:
    # Split multiple origins separated by comma
    origins = [origin.strip() for origin in ALLOWED_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Inisialisasi rate limiter
# Limit setiap IP 25 request per menit
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Custom rate limit exceeded handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please wait before making more requests."},
        headers={"Retry-After": "60"}
    )

# Membuat semua chain yang dibutuhkan saat aplikasi dimulai
router_chain = create_router_chain()
sql_chain = create_nl2sql_chain()
analysis_chain = create_analysis_chain()
sql_with_conversation_chain = create_nl2sql_with_conversation_chain()
analysis_with_conversation_chain = create_analysis_with_conversation_chain()

# --- MANAJEMEN MEMORI SEDERHANA ---
# Kamus di memori untuk menyimpan riwayat percakapan. Key adalah conversation_id.
# Untuk produksi, ganti ini dengan database seperti Redis.
conversation_histories: Dict[str, List[Tuple[str, str]]] = {}

class ContextualQueryRequest(BaseModel):
    question: str
    conversation_id: str
    
    class Config:
        schema_extra = {
            "example": {
                "question": "Bagaimana dengan program di Direktorat Keuangan?",
                "conversation_id": "user_123_session_1"
            }
        }

def format_history_for_prompt(history: List[Tuple[str, str]]) -> str:
    """Mengubah list riwayat menjadi format string yang bisa dibaca LLM."""
    if not history:
        return "Tidak ada riwayat percakapan."
    
    formatted = ""
    for user_msg, ai_msg in history:
        formatted += f"Pengguna: {user_msg}\nAsisten: {ai_msg}\n"
    return formatted

# Healt check endpoint
@app.get("/", 
    tags=["Health Check"],
    summary="🏥 Health Check",
    description="Endpoint untuk mengecek status kesehatan API")
def read_root():
    """
    ## Health Check Endpoint
    
    Mengembalikan status API dan informasi dasar untuk memastikan service berjalan dengan baik.
    
    **Returns:**
    - **message**: Status API dan panduan penggunaan
    - **status**: Status kesehatan service
    - **version**: Versi API yang sedang berjalan
    """
    return {
        "message": "🚀 NL-to-SQL API is running successfully!", 
        "status": "healthy",
        "version": "1.0.0",
        "documentation": "/docs",
        "available_endpoints": [
            "/generate-sql-only",
            "/generate-sql-execute-analyze", 
            "/context-nl-to-sql",
            "/generate-sql-without-analyze",
            "/context-nl-to-sql-without-query"
        ]
    }

@app.post("/generate-sql-only",
    tags=["SQL Generation"],
    summary="🔧 Generate SQL Query Only",
    description="Mengkonversi pertanyaan bahasa natural menjadi query SQL tanpa eksekusi")
@limiter.limit("25/minute")
def generate_sql(request_body: QueryRequest, request: Request):
    """
    ## Generate SQL Query Only
    
    Endpoint ini hanya mengkonversi pertanyaan bahasa natural menjadi query SQL tanpa mengeksekusinya.
    Cocok untuk:
    - 🔍 Preview query sebelum eksekusi
    - 🧪 Testing dan debugging
    - 📝 Mendapatkan SQL untuk keperluan lain
    
    **Process Flow:**
    1. 🔍 Klasifikasi pertanyaan (data perusahaan vs pengetahuan umum)
    2. 🤖 Generate SQL menggunakan RAG + Gemini AI
    3. 📤 Return query SQL
    
    **Output Types:**
    - **REJECTED**: Pertanyaan di luar scope data perusahaan
    - **SQL_GENERATED**: Query SQL berhasil dibuat
    
    **Example Questions:**
    - "Tampilkan 10 program dengan anggaran terbesar"
    - "Berapa total realisasi anggaran tahun 2024?"
    - "Daftar unit kerja di Direktorat Keuangan"
    """
    question = request_body.question
    print(f"Menerima pertanyaan: {question}")

    # --- LANGKAH 1: ROUTING ---
    # Router chain dimulai dengan Prompt, jadi inputnya harus DICT
    # dengan key yang cocok dengan variabel di dalam prompt ({question})
    print("Melakukan klasifikasi pertanyaan...")
    klasifikasi = router_chain.invoke({"question": question})
    print(f"Hasil klasifikasi: {klasifikasi}")
    
    # --- LANGKAH 2: LOGIKA KONTROL ---
    if "pengetahuan_umum" in klasifikasi.lower():
        return {
            "type": "REJECTED",
            "answer": "Maaf, saya adalah model privat yang hanya bisa menjawab pertanyaan seputar data perusahaan."
        }
    
    # --- LANGKAH 3: PEMBUATAN SQL ---
    print("Pertanyaan relevan, melanjutkan ke pembuatan SQL...")
    # SQL chain dimulai dengan Retriever, yang mengharapkan input berupa STRING
    sql_query = sql_chain.invoke(question)
    
    print(f"Query SQL yang dihasilkan: {sql_query}")
    return {
        "type": "SQL_GENERATED",
        "sql_query": sql_query
    }

@app.post("/generate-sql-execute-analyze",
    tags=["Complete Workflow"],
    summary="🚀 Complete NL-to-SQL Workflow",
    description="Alur kerja lengkap: Generate SQL → Validasi → Eksekusi → Analisis hasil")
@limiter.limit("25/minute")
def ask(request_body: QueryRequest, request: Request):
    """
    ## Complete NL-to-SQL Workflow
    
    **🎯 Endpoint Utama** yang menjalankan alur kerja lengkap dan aman untuk mengkonversi pertanyaan 
    bahasa natural menjadi insight data yang mudah dipahami.
    
    **🔄 Process Flow:**
    1. 🔍 **Smart Routing**: Klasifikasi pertanyaan
    2. 🤖 **SQL Generation**: Buat query menggunakan RAG + AI
    3. 🛡️ **Security Validation**: Validasi keamanan query SQL
    4. 💾 **Safe Execution**: Eksekusi query ke database
    5. 🧠 **Intelligent Analysis**: Analisis hasil dan buat jawaban natural
    
    **✅ Safety Features:**
    - SQL injection prevention
    - Blacklist dangerous functions (SLEEP, BENCHMARK, etc.)
    - Only SELECT queries allowed
    - Input sanitization
    
    **📊 Output Types:**
    - **SUCCESS**: Analisis lengkap dengan data
    - **REJECTED**: Pertanyaan di luar scope
    - **SQL_GENERATION_FAILED**: Gagal membuat SQL
    - **UNSAFE_SQL_QUERY**: Query tidak aman
    - **SQL_EXECUTION_ERROR**: Error database
    
    **💡 Best For:**
    - End-user applications
    - Business intelligence queries
    - Quick data insights
    """
    question = request_body.question
    print(f"Menerima pertanyaan: {question}")

    # === LANGKAH 1: ROUTING ===
    print("Melakukan klasifikasi pertanyaan...")
    klasifikasi = router_chain.invoke({"question": question})
    print(f"Hasil klasifikasi: {klasifikasi}")

    if "pengetahuan_umum" in klasifikasi.lower():
        return {
            "type": "REJECTED",
            "answer": "Maaf, saya adalah model privat yang hanya bisa menjawab pertanyaan seputar data perusahaan."
        }

    # === LANGKAH 2: PEMBUATAN SQL ===
    print("Pertanyaan relevan, melanjutkan ke pembuatan SQL...")
    sql_query = sql_chain.invoke(question)
    
    if "error" in sql_query.lower() or len(sql_query) < 5:
        return {"type": "SQL_GENERATION_FAILED", "answer": "Maaf, saya tidak dapat membuat query SQL untuk pertanyaan tersebut."}
    print(f"Query SQL yang dihasilkan: {sql_query}")

    print("sql_query", sql_query)

    # === LANGKAH BARU: VALIDASI KEAMANAN QUERY ===
    print("Memvalidasi keamanan query SQL...")
    if not is_safe_select_query(sql_query):
        # Jika fungsi mengembalikan False, hentikan proses dan beri respons error
        return {
            "type": "UNSAFE_SQL_QUERY", 
            "answer": "Maaf, query SQL yang dihasilkan tidak diizinkan untuk dieksekusi karena alasan keamanan.",
            "generated_sql": sql_query
        }
    print("Validasi SQL berhasil.")

    # === LANGKAH 3: EKSEKUSI QUERY SQL ===
    # Langkah ini hanya akan berjalan jika validasi di atas berhasil
    print("Mengeksekusi query ke database...")
    sql_result_df = execute_sql_query(sql_query) 

    # Periksa jika terjadi error (fungsi akan mengembalikan string jika error)
    if isinstance(sql_result_df, str):
        return {"type": "SQL_EXECUTION_ERROR", "answer": f"Terjadi masalah saat mengambil data: {sql_result_df}", "generated_sql": sql_query}
    
    sql_result_for_llm = "Query berhasil dieksekusi, namun tidak ada data yang ditemukan."
    if not sql_result_df.empty:
        sql_result_for_llm = sql_result_df.to_string()
    print(f"Hasil data mentah (untuk LLM):\n{sql_result_for_llm}")

    # === LANGKAH 4: ANALISIS HASIL (REASONING) ===
    print("Menganalisis hasil data...")
    final_answer = analysis_chain.invoke({
        "question": question,
        "sql_result": sql_result_for_llm
    })
    print(f"Jawaban akhir yang dihasilkan: {final_answer}")

    # Mengembalikan jawaban lengkap
    return {
        "type": "SUCCESS",
        "answer": final_answer,
        "generated_sql": sql_query,
        "raw_data": sql_result_df.to_dict(orient="records")
    }

@app.post("/context-nl-to-sql",
    tags=["Conversational AI"],
    summary="💬 Contextual NL-to-SQL with Memory",
    description="Alur kerja lengkap dengan memori percakapan untuk pertanyaan follow-up")
@limiter.limit("25/minute")
def ask_contextual(request_body: ContextualQueryRequest, request: Request):
    """
    ## Contextual NL-to-SQL with Conversation Memory
    
    **🧠 Smart Endpoint** yang mendukung percakapan berkelanjutan dengan memori konteks.
    Ideal untuk sesi tanya-jawab interaktif dan analisis data bertahap.
    
    **🔄 Enhanced Process Flow:**
    1. 📚 **Memory Retrieval**: Ambil riwayat percakapan
    2. 🔍 **Contextual Routing**: Klasifikasi dengan konteks
    3. 🤖 **Context-Aware SQL**: Generate SQL dengan pemahaman konteks
    4. 🧹 **SQL Sanitization**: Bersihkan format markdown
    5. 🛡️ **Security Validation**: Validasi keamanan
    6. 💾 **Safe Execution**: Eksekusi ke database
    7. 🧠 **Contextual Analysis**: Analisis dengan konteks percakapan
    8. 💾 **Memory Update**: Simpan ke riwayat percakapan
    
    **💡 Conversation Examples:**
    ```
    User: "Tampilkan 5 program dengan anggaran terbesar"
    AI: [Menampilkan data program...]
    
    User: "Bagaimana dengan yang terkecil?"
    AI: [Memahami konteks dan menampilkan program dengan anggaran terkecil]
    
    User: "Fokus ke Direktorat Keuangan saja"
    AI: [Menyaring hasil untuk Direktorat Keuangan]
    ```
    
    **🔑 Key Features:**
    - **Persistent Memory**: Riwayat tersimpan per conversation_id
    - **Context Understanding**: Memahami rujukan seperti "yang tadi", "bagaimana dengan..."
    - **Follow-up Queries**: Mendukung pertanyaan lanjutan
    - **Session Management**: Isolasi percakapan per user/session
    """
    question = request_body.question
    conversation_id = request_body.conversation_id
    print(f"Menerima pertanyaan untuk sesi [{conversation_id}]: {question}")

    # 1. Ambil atau buat riwayat untuk sesi ini
    history = conversation_histories.get(conversation_id, [])
    formatted_history = format_history_for_prompt(history)

    # 2. Routing
    klasifikasi = router_chain.invoke({"question": question})
    if "pengetahuan_umum" in klasifikasi.lower():
        return {"type": "REJECTED", "answer": "Maaf, saya adalah model privat yang hanya bisa menjawab pertanyaan seputar data perusahaan."}

    # 3. Pembuatan SQL dengan konteks riwayat
    # Menerima output mentah dari LLM
    raw_sql_query = sql_with_conversation_chain.invoke({
        "question": question,
        "chat_history": formatted_history
    })
    
    # 4. Sanitasi Output SQL (LANGKAH PENTING BARU)
    # Membersihkan format markdown ```sql dari output LLM
    sql_query = sanitize_sql_output(raw_sql_query)
    print(f"Query SQL (setelah sanitasi): {sql_query}")

    # Periksa jika LLM gagal membuat query
    if "error" in sql_query.lower() or len(sql_query) < 5:
        return {"type": "SQL_GENERATION_FAILED", "answer": "Maaf, saya tidak dapat membuat query SQL untuk pertanyaan tersebut."}

    # 5. Validasi Keamanan SQL
    if not is_safe_select_query(sql_query):
        return {
            "type": "UNSAFE_SQL_QUERY", 
            "answer": "Maaf, query SQL yang dihasilkan tidak diizinkan untuk dieksekusi karena alasan keamanan.",
            "generated_sql": sql_query
        }

    # 6. Eksekusi SQL
    sql_result_df = execute_sql_query(sql_query)
    if isinstance(sql_result_df, str):
        return {"type": "SQL_EXECUTION_ERROR", "answer": sql_result_df, "generated_sql": sql_query}
    
    sql_result_for_llm = sql_result_df.to_string() if not sql_result_df.empty else "Tidak ada data yang ditemukan."

    # 7. Analisis Hasil
    final_answer = analysis_chain.invoke({
        "question": question,
        "chat_history": formatted_history,
        "sql_result": sql_result_for_llm
    })

    # 8. Perbarui Riwayat Percakapan
    history.append((question, final_answer))
    conversation_histories[conversation_id] = history

    # 9. Kembalikan Jawaban
    return {
        "type": "SUCCESS",
        "answer": final_answer,
        "generated_sql": sql_query,
        "raw_data": sql_result_df.to_dict(orient="records")
    }

@app.post("/generate-sql-without-analyze",
    tags=["SQL Execution"],
    summary="⚡ Generate SQL + Execute (Raw Data)",
    description="Generate SQL dan eksekusi langsung, return data mentah tanpa analisis AI")
@limiter.limit("25/minute")
def generate_sql_without_analyze(request_body: QueryRequest, request: Request):
    """
    ## Generate SQL + Execute (Raw Data Only)
    
    **⚡ High-Performance Endpoint** untuk mendapatkan data mentah tanpa overhead analisis AI.
    Cocok untuk aplikasi yang membutuhkan data mentah atau sudah memiliki logic analisis sendiri.
    
    **🔄 Streamlined Process:**
    1. 🔍 Smart routing dan klasifikasi
    2. 🤖 Generate SQL query
    3. 🛡️ Security validation
    4. 💾 Execute query
    5. 📤 Return raw data
    
    **💡 Best For:**
    - **API Integration**: Aplikasi yang butuh data untuk diproses lebih lanjut
    - **Dashboard Backends**: Feeding data ke visualization tools
    - **Bulk Data Retrieval**: Ambil data besar tanpa analisis
    - **Performance Critical**: Butuh response time cepat
    
    **📊 Output Format:**
    - **SUCCESS**: Raw data dalam format JSON array
    - **generated_sql**: Query SQL yang dieksekusi
    - **raw_data**: Array of objects dengan data mentah
    
    **⚠️ Note**: Tidak ada analisis AI, cocok untuk developer yang ingin mengolah data sendiri.
    """
    question = request_body.question
    print(f"Menerima pertanyaan: {question}")

    # Routing
    klasifikasi = router_chain.invoke({"question": question})
    print(f"Hasil klasifikasi: {klasifikasi}")

    if "pengetahuan_umum" in klasifikasi.lower():
        return {
            "type": "REJECTED",
            "answer": "Maaf, saya adalah model privat yang hanya bisa menjawab pertanyaan seputar data perusahaan."
        }

    # Generate SQL
    sql_query = sql_chain.invoke(question)
    print(f"Query SQL yang dihasilkan: {sql_query}")

    if "error" in sql_query.lower() or len(sql_query) < 5:
        return {"type": "SQL_GENERATION_FAILED", "answer": "Maaf, saya tidak dapat membuat query SQL untuk pertanyaan tersebut."}

    # Validasi Keamanan SQL
    if not is_safe_select_query(sql_query):
        return {
            "type": "UNSAFE_SQL_QUERY", 
            "answer": "Maaf, query SQL yang dihasilkan tidak diizinkan untuk dieksekusi karena alasan keamanan.",
            "generated_sql": sql_query
        }

    # Eksekusi SQL
    sql_result_df = execute_sql_query(sql_query)
    if isinstance(sql_result_df, str):
        return {"type": "SQL_EXECUTION_ERROR", "answer": sql_result_df, "generated_sql": sql_query}

    # Kembalikan hasil
    return {
        "type": "SUCCESS",
        "generated_sql": sql_query,
        "raw_data": sql_result_df.to_dict(orient="records")
    }

@app.post("/context-nl-to-sql-without-query",
    tags=["Conversational AI"],
    summary="💬 Contextual Analysis (No SQL Exposure)",
    description="Percakapan contextual dengan analisis lengkap, tidak menampilkan query SQL")
@limiter.limit("25/minute")
def context_nl_to_sql_without_query(request_body: ContextualQueryRequest, request: Request):
    """
    ## Contextual Analysis (No SQL Exposure)
    
    **🎭 User-Friendly Endpoint** yang memberikan pengalaman conversational natural tanpa 
    mengekspos detail teknis SQL kepada end-user.
    
    **🔄 Complete Process (SQL Hidden):**
    1. 📚 Retrieve conversation history
    2. 🔍 Contextual question classification
    3. 🤖 Generate SQL (internal only)
    4. 🛡️ Security validation
    5. 💾 Execute query safely
    6. 🧠 AI-powered analysis
    7. 💾 Update conversation memory
    8. 📤 Return natural language answer only
    
    **✨ Perfect For:**
    - **End-User Applications**: Chat interfaces, chatbots
    - **Business Users**: Non-technical stakeholders
    - **Clean UI/UX**: Interface yang tidak ingin show SQL
    - **Security Conscious**: Tidak expose query structure
    
    **🎯 Key Differences:**
    - ✅ Full conversation memory
    - ✅ AI analysis and insights
    - ✅ Natural language responses
    - ❌ No SQL query in response
    - ❌ No technical details exposed
    
    **💬 Use Case Example:**
    Business user bertanya tentang budget, mendapat jawaban natural tanpa perlu tahu 
    SQL query apa yang dijalankan di background.
    """
    question = request_body.question
    conversation_id = request_body.conversation_id
    print(f"Menerima pertanyaan untuk sesi [{conversation_id}]: {question}")

    # Ambil riwayat percakapan
    history = conversation_histories.get(conversation_id, [])
    formatted_history = format_history_for_prompt(history)

    # Routing
    klasifikasi = router_chain.invoke({"question": question})
    if "pengetahuan_umum" in klasifikasi.lower():
        return {"type": "REJECTED", "answer": "Maaf, saya adalah model privat yang hanya bisa menjawab pertanyaan seputar data perusahaan."}

    # Generate SQL dengan konteks riwayat
    raw_sql_query = sql_with_conversation_chain.invoke({
        "question": question,
        "chat_history": formatted_history
    })
    sql_query = sanitize_sql_output(raw_sql_query)
    print(f"Query SQL (setelah sanitasi): {sql_query}")

    if "error" in sql_query.lower() or len(sql_query) < 5:
        return {"type": "SQL_GENERATION_FAILED", "answer": "Maaf, saya tidak dapat membuat query SQL untuk pertanyaan tersebut."}

    # Validasi Keamanan SQL
    if not is_safe_select_query(sql_query):
        return {
            "type": "UNSAFE_SQL_QUERY", 
            "answer": "Maaf, query SQL yang dihasilkan tidak diizinkan untuk dieksekusi karena alasan keamanan."
        }

    # Eksekusi SQL
    sql_result_df = execute_sql_query(sql_query)
    if isinstance(sql_result_df, str):
        return {"type": "SQL_EXECUTION_ERROR", "answer": sql_result_df}

    sql_result_for_llm = sql_result_df.to_string() if not sql_result_df.empty else "Tidak ada data yang ditemukan."

    # Analisis hasil
    final_answer = analysis_chain.invoke({
        "question": question,
        "chat_history": formatted_history,
        "sql_result": sql_result_for_llm
    })

    # Simpan riwayat percakapan
    history.append((question, final_answer))
    conversation_histories[conversation_id] = history

    # Kembalikan hanya data dan hasil analisa
    return {
        "type": "SUCCESS",
        "answer": final_answer,
        "raw_data": sql_result_df.to_dict(orient="records")
    }