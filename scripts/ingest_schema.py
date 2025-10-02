# import yaml
# import os
# from dotenv import load_dotenv
# from langchain_core.documents import Document
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import Chroma
# from langchain_community.embeddings import HuggingFaceEmbeddings

# # --- 1. KONFIGURASI ---
# print("Memulai proses ingest data skema...")
# load_dotenv()

# # Path ke file YML dan direktori database vektor
# YAML_PATH = "data/schema_description.yml"
# DB_PATH = "chroma_db/"
# # Nama model embedding yang dipilih
# EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

# def format_schema_from_yaml(yaml_data: dict) -> str:
#     """
#     Mengubah data YML terstruktur menjadi satu blok teks kaya deskripsi untuk RAG.
#     Fungsi ini menyertakan tipe data, deskripsi, dan sinonim untuk setiap kolom.
#     """
#     formatted_texts = []
#     spec = yaml_data.get('spec', {})

#     for table_name, table_details in spec.items():
#         table_description = table_details.get('description', 'Tidak ada deskripsi.')
#         text = f"Informasi detail untuk tabel database bernama '{table_name}':\n"
#         text += f"Deskripsi umum tabel: {table_description}\n"
#         text += "Tabel ini memiliki kolom-kolom sebagai berikut:\n\n"
        
#         for column in table_details.get('columns', []):
#             col_name = column.get('name')
#             col_type = column.get('data_type', 'tipe tidak diketahui')
#             col_desc = column.get('description')
#             col_synonyms = ", ".join(column.get('synonyms', []))
            
#             text += (
#                 f"- Kolom `{col_name}` (tipe data: {col_type}): {col_desc}. "
#                 f"Pengguna mungkin menyebut kolom ini sebagai: '{col_synonyms}'.\n"
#             )
        
#         formatted_texts.append(text)
        
#     return "\n---\n".join(formatted_texts)

# # --- 2. LOAD & TRANSFORM: Membaca YML dan Mengubahnya jadi Teks ---
# print(f"Membaca dan memformat skema dari: {YAML_PATH}...")
# try:
#     with open(YAML_PATH, 'r', encoding='utf-8') as f:
#         yaml_content = yaml.safe_load(f)
# except FileNotFoundError:
#     print(f"Error: File tidak ditemukan di {YAML_PATH}. Pastikan path dan nama file sudah benar.")
#     exit()

# schema_text = format_schema_from_yaml(yaml_content)
# print("Berhasil memformat YML menjadi teks.")

# documents = [Document(page_content=schema_text, metadata={"source": YAML_PATH})]

# # --- 3. SPLIT: Memecah Dokumen menjadi Potongan Kecil (Chunks) ---
# text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
# chunks = text_splitter.split_documents(documents)
# print(f"Teks skema dipecah menjadi {len(chunks)} chunk.")

# # --- 4. EMBED & STORE: Mengubah Teks ke Vektor & Menyimpan ---
# print(f"Memuat model embedding: {EMBEDDING_MODEL}...")
# # Inisialisasi model embedding untuk berjalan di CPU
# embeddings = HuggingFaceEmbeddings(
#     model_name=EMBEDDING_MODEL,
#     model_kwargs={'device': 'cpu'}
# )

# print("Membuat embeddings dari chunks dan menyimpannya ke ChromaDB. Proses ini mungkin memakan waktu beberapa saat...")
# # Membuat database Chroma dari chunks dokumen dan menyimpannya secara lokal
# # Proses download model (sekitar 440 MB) akan terjadi otomatis saat pertama kali dijalankan
# db = Chroma.from_documents(
#     chunks, 
#     embeddings, 
#     persist_directory=DB_PATH
# )

# print("\n--- ✅ Proses Ingest Selesai ---")
# print(f"Database vektor berhasil dibuat dan disimpan di direktori: {DB_PATH}")

import yaml
import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from langchain_community.embeddings import HuggingFaceEmbeddings

# --- 1. KONFIGURASI ---
print("Memulai proses ingest data skema...")
load_dotenv()

# Path ke file YML
YAML_PATH = "data/schema_description.yml"

# Nama model embedding yang dipilih
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

# Nama koleksi di Qdrant
COLLECTION_NAME = "schema_vectors"

# Qdrant URL dari environment variable
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# --- 2. FORMATTER ---
def format_schema_from_yaml(yaml_data: dict) -> str:
    """
    Mengubah data YML terstruktur menjadi satu blok teks kaya deskripsi untuk RAG.
    Fungsi ini menyertakan tipe data, deskripsi, dan sinonim untuk setiap kolom.
    """
    formatted_texts = []
    spec = yaml_data.get('spec', {})

    for table_name, table_details in spec.items():
        table_description = table_details.get('description', 'Tidak ada deskripsi.')
        text = f"Informasi detail untuk tabel database bernama '{table_name}':\n"
        text += f"Deskripsi umum tabel: {table_description}\n"
        text += "Tabel ini memiliki kolom-kolom sebagai berikut:\n\n"
        
        for column in table_details.get('columns', []):
            col_name = column.get('name')
            col_type = column.get('data_type', 'tipe tidak diketahui')
            col_desc = column.get('description')
            col_synonyms = ", ".join(column.get('synonyms', []))
            
            text += (
                f"- Kolom `{col_name}` (tipe data: {col_type}): {col_desc}. "
                f"Pengguna mungkin menyebut kolom ini sebagai: '{col_synonyms}'.\n"
            )
        
        formatted_texts.append(text)
        
    return "\n---\n".join(formatted_texts)

# --- 3. LOAD & TRANSFORM ---
print(f"Membaca dan memformat skema dari: {YAML_PATH}...")
try:
    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        yaml_content = yaml.safe_load(f)
except FileNotFoundError:
    print(f"Error: File tidak ditemukan di {YAML_PATH}. Pastikan path dan nama file sudah benar.")
    exit()

schema_text = format_schema_from_yaml(yaml_content)
print("Berhasil memformat YML menjadi teks.")

documents = [Document(page_content=schema_text, metadata={"source": YAML_PATH})]

# --- 4. SPLIT ---
text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
chunks = text_splitter.split_documents(documents)
print(f"Teks skema dipecah menjadi {len(chunks)} chunk.")

# --- 5. EMBEDDINGS ---
print(f"Memuat model embedding: {EMBEDDING_MODEL}...")
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={'device': 'cpu'}  # force pakai CPU
)

# --- 6. CONNECT KE QDRANT ---
print(f"Menyambungkan ke Qdrant di {QDRANT_URL}...")
qdrant = QdrantClient(url=QDRANT_URL)

# --- 7. INGEST KE QDRANT ---
print(f"Menyimpan embeddings ke Qdrant collection: {COLLECTION_NAME}...")
db = Qdrant.from_documents(
    chunks,
    embeddings,
    url=QDRANT_URL,
    collection_name=COLLECTION_NAME
)

print("\n--- ✅ Proses Ingest Selesai ---")
print(f"Data berhasil disimpan ke collection '{COLLECTION_NAME}' di Qdrant.")
