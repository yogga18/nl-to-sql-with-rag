# src/dependencies.py

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.retrievers import BaseRetriever

DB_PATH = "chroma_db/"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

def get_embedding_function():
    """
    Menginisialisasi dan mengembalikan fungsi embedding.
    PENTING: Model ini harus SAMA PERSIS dengan yang digunakan saat ingest.
    """
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'}
    )

def get_retriever() -> BaseRetriever:
    """
    Memuat database vektor ChromaDB dan mengembalikannya sebagai retriever.
    Retriever ini bertugas mencari konteks skema yang relevan.
    """
    embedding_function = get_embedding_function()
    
    db = Chroma(
        persist_directory=DB_PATH, 
        embedding_function=embedding_function
    )
    
    # Mengambil 2 potongan konteks paling relevan
    return db.as_retriever(search_kwargs={"k": 2})