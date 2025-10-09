from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from pydantic import SecretStr
from operator import itemgetter

from src.db.config_openrouter import get_openrouter_config
from src.db.executor import execute_sql_query
from src.validation import is_safe_select_query, sanitize_sql_output
from src.retrieval.dependencies import get_retriever


# ========== PROMPT TEMPLATES ==========

ROUTER_PROMPT_TEMPLATE = """
Anda adalah sebuah AI klasifikasi. Klasifikasikan pertanyaan pengguna ke dalam salah satu dari dua kategori berikut:
1. "data_perusahaan": Jika pertanyaan berkaitan dengan anggaran, realisasi, sisa dana, kegiatan, unit kerja, sasaran strategis, program, atau data internal lainnya.
2. "pengetahuan_umum": Jika pertanyaan adalah tentang topik lain di luar data perusahaan.

Hanya kembalikan SATU KATA nama kategori dan tidak ada yang lain.

Pertanyaan Pengguna: {question}
Kategori:
"""

SQL_GENERATION_PROMPT_TEMPLATE = """
Anda adalah asisten AI yang bertugas mengubah bahasa natural menjadi query SQL yang valid untuk tabel bernama `drauk_unit`.

DAFTAR KOLOM YANG VALID (Whitelist):
[Tahun_Anggaran, Kode_DRAUK, Indikator_Tujuan, Kode_SS, Sasaran_Strategis, Kode_IKSS, Indikator_Kinerja_Sasaran_Strategis, Kode_PS, Program_Strategis, Kode_IKPS, Indikator_Kinerja_Program_Strategis, Kode_Unit, Nama_Unit, Tipe_Unit, Kegiatan_Universitas, Indikator_Capaian, Kegiatan_Unit, Kode_Standar_Kegiatan, Standar_Kegiatan, FTE, Detail_Kegiatan, Kelompok_Pagu, Akun, COA, Nama_COA, Satuan_Kegiatan, Barjas, Volume_1, Satuan_1, Volume_2, Satuan_2, Volume_3, Satuan_3, Volume_4, Satuan_4, Harga_Satuan, Sumber_Dana, Detail_Sumber_Dana, Jumlah, Realisasi, Sisa]

ATURAN PALING PENTING:
1. GUNAKAN HANYA nama kolom dari "DAFTAR KOLOM YANG VALID" di atas. Jangan mengarang atau mengubah nama kolom.
2. PENULISAN NAMA KOLOM HARUS SAMA PERSIS (case-sensitive). Jangan mengubah `Kegiatan_Unit` menjadi `kegiatan_unit`.
3. Gunakan "Konteks Skema" di bawah ini untuk memahami arti setiap kolom.
4. Untuk permintaan "terbesar", "tertinggi", gunakan `ORDER BY ... DESC LIMIT ...`.
5. Untuk permintaan "terkecil", "terendah", gunakan `ORDER BY ... ASC LIMIT ...`.
6. Kembalikan HANYA string query SQL mentah, tanpa format ```sql.

Konteks Skema:
{context}

Pertanyaan Pengguna: {question}

Query SQL:
"""

ANALYSIS_PROMPT_TEMPLATE = """
Anda adalah seorang analis data AI. Berdasarkan pertanyaan asli pengguna dan data hasil query berikut, berikan jawaban dalam satu atau dua kalimat yang informatif dan mudah dimengerti.

Pertanyaan Asli Pengguna: {question}
Data Hasil Query: {sql_result}

Jawaban Analisis:
"""


# ========== HELPER FUNCTIONS ==========

def create_openrouter_llm(model_name: str, temperature: float = 0.0):
    """Helper untuk membuat ChatOpenAI instance dengan OpenRouter config"""
    config = get_openrouter_config()
    
    return ChatOpenAI(
        model=model_name,
        api_key=SecretStr(config["api_key"]) if config["api_key"] is not None else None,
        base_url=config["base_url"],
        temperature=temperature,
        max_completion_tokens=2000,
        default_headers={
            "HTTP-Referer": "https://github.com/yogga18/nl-to-sql-with-rag.git",
            "X-Title": str(config["app_name"]) if config["app_name"] is not None else ""
        }
    )


# ========== CHAIN BUILDERS ==========

def create_openrouter_router_chain(model_name: str):
    """Chain untuk klasifikasi pertanyaan (router)"""
    llm = create_openrouter_llm(model_name, temperature=0.0)
    prompt = PromptTemplate.from_template(ROUTER_PROMPT_TEMPLATE)
    return prompt | llm | StrOutputParser()


def create_openrouter_nl2sql_chain(model_name: str):
    """Chain untuk konversi Natural Language ke SQL"""
    retriever = get_retriever()
    llm = create_openrouter_llm(model_name, temperature=0.0)
    
    prompt = PromptTemplate(
        template=SQL_GENERATION_PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )
    
    sql_chain = (
        {
            "context": retriever,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return sql_chain


def create_openrouter_analysis_chain(model_name: str):
    """Chain untuk analisis hasil SQL"""
    llm = create_openrouter_llm(model_name, temperature=0.1)
    prompt = PromptTemplate.from_template(ANALYSIS_PROMPT_TEMPLATE)
    return prompt | llm | StrOutputParser()


# ========== MAIN WORKFLOW ==========

def openrouter_nl_to_sql_workflow(question: str, model_name: str) -> Dict[str, Any]:
    """
    Workflow lengkap: Router -> SQL Generation -> Validation -> Execution -> Analysis
    
    Args:
        question: Pertanyaan user dalam bahasa natural
        model_name: Model OpenRouter yang akan digunakan (contoh: "anthropic/claude-3-opus")
    
    Returns:
        Dictionary berisi hasil lengkap workflow
    """
    try:
        # Step 1: ROUTER - Klasifikasi pertanyaan
        router_chain = create_openrouter_router_chain(model_name)
        klasifikasi = router_chain.invoke({"question": question})
        
        if "pengetahuan_umum" in klasifikasi.lower():
            return {
                "type": "REJECTED",
                "answer": "Maaf, saya hanya dapat menjawab pertanyaan terkait data perusahaan, anggaran, realisasi, program, kegiatan, dan unit kerja.",
                "model_used": model_name,
                "step": "router"
            }
        
        # Step 2: SQL GENERATION - Generate SQL dari pertanyaan
        sql_chain = create_openrouter_nl2sql_chain(model_name)
        raw_sql_query = sql_chain.invoke(question)
        sql_query = sanitize_sql_output(raw_sql_query)
        
        if "error" in sql_query.lower() or len(sql_query) < 5:
            return {
                "type": "SQL_GENERATION_FAILED",
                "answer": "Tidak dapat membuat query SQL dari pertanyaan Anda. Mohon coba formulasi ulang pertanyaan.",
                "model_used": model_name,
                "step": "sql_generation"
            }
        
        # Step 3: VALIDATION - Validasi keamanan SQL
        if not is_safe_select_query(sql_query):
            return {
                "type": "UNSAFE_SQL_QUERY",
                "answer": "Query yang dihasilkan tidak aman atau mengandung perintah yang tidak diizinkan.",
                "generated_sql": sql_query,
                "model_used": model_name,
                "step": "validation"
            }
        
        # Step 4: EXECUTION - Eksekusi SQL query
        sql_result_df = execute_sql_query(sql_query)
        
        if isinstance(sql_result_df, str):
            return {
                "type": "SQL_EXECUTION_ERROR",
                "answer": f"Terjadi error saat eksekusi query: {sql_result_df}",
                "generated_sql": sql_query,
                "model_used": model_name,
                "step": "execution"
            }
        
        # Prepare data untuk analisis
        sql_result_for_llm = "Query berhasil dieksekusi, namun tidak ada data yang ditemukan."
        if not sql_result_df.empty:
            sql_result_for_llm = sql_result_df.to_string()
        
        # Step 5: ANALYSIS - Analisis hasil dengan AI
        analysis_chain = create_openrouter_analysis_chain(model_name)
        final_answer = analysis_chain.invoke({
            "question": question,
            "sql_result": sql_result_for_llm
        })
        
        # Return hasil lengkap
        return {
            "type": "SUCCESS",
            "answer": final_answer,
            "generated_sql": sql_query,
            "raw_data": sql_result_df.to_dict(orient="records"),
            "data_count": len(sql_result_df),
            "model_used": model_name,
            "step": "completed"
        }
        
    except Exception as e:
        return {
            "type": "ERROR",
            "answer": f"Terjadi error dalam proses: {str(e)}",
            "model_used": model_name,
            "error": str(e),
            "step": "exception"
        }


# ========== SIMPLE CHAT (ORIGINAL) ==========

def create_openrouter_chain(model_name: str):
    """
    Membuat chain sederhana untuk chat umum dengan OpenRouter.
    Ini adalah fungsi original untuk chat bebas tanpa batasan.
    """
    config = get_openrouter_config()
    
    llm = ChatOpenAI(
        model=model_name,
        api_key=SecretStr(config["api_key"]) if config["api_key"] is not None else None,
        base_url=config["base_url"],
        temperature=0.7,
        max_completion_tokens=2000,
        default_headers={
            "HTTP-Referer": "https://github.com/yogga18/nl-to-sql-with-rag.git",
            "X-Title": str(config["app_name"]) if config["app_name"] is not None else ""
        }
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant."),
        ("human", "{prompt}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    return chain


def chat_with_openrouter(prompt: str, model_name: str) -> Dict[str, Any]:
    """
    Chat bebas dengan OpenRouter (tanpa batasan domain).
    """
    try:
        chain = create_openrouter_chain(model_name)
        response = chain.invoke({"prompt": prompt})
        
        return {
            "type": "SUCCESS",
            "answer": response,
            "model_used": model_name,
            "status": "completed"
        }
    
    except Exception as e:
        return {
            "type": "ERROR",
            "answer": f"Terjadi error: {str(e)}",
            "model_used": model_name,
            "status": "failed",
            "error": str(e)
        }


def get_available_models() -> Dict[str, list]:
    """
    Mengembalikan daftar model populer yang tersedia di OpenRouter.
    """
    return {
        "popular_models": [
            {
                "id": "anthropic/claude-3-opus",
                "name": "Claude 3 Opus",
                "provider": "Anthropic",
                "description": "Most capable model, best for complex tasks"
            },
            {
                "id": "anthropic/claude-3-sonnet",
                "name": "Claude 3 Sonnet",
                "provider": "Anthropic",
                "description": "Balanced performance and speed"
            },
            {
                "id": "anthropic/claude-3-haiku",
                "name": "Claude 3 Haiku",
                "provider": "Anthropic",
                "description": "Fastest and most compact"
            },
            {
                "id": "openai/gpt-4-turbo",
                "name": "GPT-4 Turbo",
                "provider": "OpenAI",
                "description": "Latest GPT-4 with improved performance"
            },
            {
                "id": "openai/gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "OpenAI",
                "description": "Fast and cost-effective"
            },
            {
                "id": "meta-llama/llama-3-70b-instruct",
                "name": "Llama 3 70B Instruct",
                "provider": "Meta",
                "description": "Open source, powerful reasoning"
            },
            {
                "id": "google/gemini-pro",
                "name": "Gemini Pro",
                "provider": "Google",
                "description": "Multimodal capabilities"
            },
            {
                "id": "mistralai/mixtral-8x7b-instruct",
                "name": "Mixtral 8x7B Instruct",
                "provider": "Mistral AI",
                "description": "Efficient mixture of experts"
            }
        ],
    }