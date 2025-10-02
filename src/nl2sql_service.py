from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from operator import itemgetter
from .dependencies import get_retriever

# --- PROMPT UTAMA UNTUK SEMUA FUNGSI SQL ---
# Mendefinisikan prompt super kuat sebagai konstanta untuk digunakan kembali (Prinsip DRY)
# Ini adalah "otak" utama untuk mencegah halusinasi nama kolom.
SUPER_STRONG_SQL_PROMPT_TEMPLATE = """
Anda adalah asisten AI yang bertugas mengubah bahasa natural menjadi query SQL yang valid untuk tabel bernama `drauk_unit`.

DAFTAR KOLOM YANG VALID (Whitelist):
[Tahun_Anggaran, Kode_DRAUK, Indikator_Tujuan, Kode_SS, Sasaran_Strategis, Kode_IKSS, Indikator_Kinerja_Sasaran_Strategis, Kode_PS, Program_Strategis, Kode_IKPS, Indikator_Kinerja_Program_Strategis, Kode_Unit, Nama_Unit, Tipe_Unit, Kegiatan_Universitas, Indikator_Capaian, Kegiatan_Unit, Kode_Standar_Kegiatan, Standar_Kegiatan, FTE, Detail_Kegiatan, Kelompok_Pagu, Akun, COA, Nama_COA, Satuan_Kegiatan, Barjas, Volume_1, Satuan_1, Volume_2, Satuan_2, Volume_3, Satuan_3, Volume_4, Satuan_4, Harga_Satuan, Sumber_Dana, Detail_Sumber_Dana, Jumlah, Realisasi, Sisa]

ATURAN PALING PENTING:
1.  GUNAKAN HANYA nama kolom dari "DAFTAR KOLOM YANG VALID" di atas. Jangan mengarang atau mengubah nama kolom.
2.  PENULISAN NAMA KOLOM HARUS SAMA PERSIS (case-sensitive). Jangan mengubah `Kegiatan_Unit` menjadi `kegiatan_unit`. Salin nama kolom persis seperti yang tertulis di daftar.
3.  Gunakan "Konteks Skema" di bawah ini untuk memahami arti setiap kolom dan menghubungkannya dengan pertanyaan pengguna.
4.  Jika sebuah kata dalam pertanyaan tidak ada di daftar kolom, gunakan sinonim atau deskripsi dari "Konteks Skema" untuk menemukan kolom yang paling cocok dari daftar.
5.  Untuk permintaan "terbesar", "tertinggi", atau "paling banyak", GUNAKAN `ORDER BY ... DESC LIMIT ...`.
6.  Untuk permintaan "terkecil", "terendah", atau "paling sedikit", GUNAKAN `ORDER BY ... ASC LIMIT ...`.
7.  PERHATIKAN RIWAYAT PERCAKAPAN SEBELUMNYA untuk memahami konteks pertanyaan lanjutan.
8.  Kembalikan HANYA string query SQL mentah, tanpa format ```sql.

---
Riwayat Percakapan:
{chat_history}

Konteks Skema:
{context}

Pertanyaan Pengguna Baru: {question}

Query SQL:
"""

# --- FUNGSI-FUNGSI PEMBUAT CHAIN ---

def create_nl2sql_chain():
    """
    Membuat RAG chain (STATELESS) untuk proses Text-to-SQL.
    """
    retriever = get_retriever()
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0) 
    
    prompt = PromptTemplate(
        template=SUPER_STRONG_SQL_PROMPT_TEMPLATE,
        input_variables=["context", "question"],
        partial_variables={"chat_history": "Tidak ada riwayat percakapan."} # Mengabaikan history
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

def create_nl2sql_with_conversation_chain():
    """
    Membuat RAG chain (STATEFUL) untuk proses Text-to-SQL dengan memori.
    """
    retriever = get_retriever()
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    prompt = PromptTemplate(
        template=SUPER_STRONG_SQL_PROMPT_TEMPLATE,
        input_variables=["chat_history", "context", "question"]
    )

    # Struktur chain ini sudah benar
    chain = (
        RunnablePassthrough.assign(
            # itemgetter("question") akan mengambil nilai string dari key 'question'
            # dan HANYA string itulah yang diberikan ke retriever.
            context=itemgetter("question") | retriever
        )
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

def create_router_chain():
    """
    Membuat chain sederhana untuk mengklasifikasikan niat pengguna.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    template = """
    Anda adalah sebuah AI klasifikasi. Klasifikasikan pertanyaan pengguna ke dalam salah satu dari dua kategori berikut:
    1. "data_perusahaan": Jika pertanyaan berkaitan dengan anggaran, realisasi, sisa dana, kegiatan, unit kerja, sasaran strategis, program, atau data internal lainnya.
    2. "pengetahuan_umum": Jika pertanyaan adalah tentang topik lain di luar data perusahaan.
    Hanya kembalikan SATU KATA nama kategori dan tidak ada yang lain.
    Pertanyaan Pengguna: {question}
    Kategori:
    """
    prompt = PromptTemplate.from_template(template)
    router_chain = prompt | llm | StrOutputParser()
    return router_chain

def create_analysis_chain():
    """
    Membuat chain untuk menganalisis hasil data SQL (stateless).
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
    template = """
    Anda adalah seorang analis data AI. Berdasarkan pertanyaan asli pengguna dan data hasil query berikut, berikan jawaban dalam satu kalimat yang informatif dan mudah dimengerti.
    Pertanyaan Asli Pengguna: {question}
    Data Hasil Query: {sql_result}
    Jawaban Analisis:
    """
    prompt = PromptTemplate.from_template(template)
    analysis_chain = prompt | llm | StrOutputParser()
    return analysis_chain

def create_analysis_with_conversation_chain():
    """
    Membuat chain analisis yang mendukung riwayat percakapan (stateful).
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
    template = """
    Anda adalah seorang analis data AI. Berdasarkan pertanyaan asli pengguna, riwayat percakapan, dan data hasil query, berikan jawaban dalam satu atau dua kalimat informatif.
    Riwayat Percakapan: {chat_history}
    Pertanyaan Asli Pengguna: {question}
    Data Hasil Query: {sql_result}
    Jawaban Analisis:
    """
    prompt = PromptTemplate.from_template(template)
    analysis_chain = prompt | llm | StrOutputParser()
    return analysis_chain