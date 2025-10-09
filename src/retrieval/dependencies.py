import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.retrievers import BaseRetriever
from src.db.config_qdrant import get_qdrant_client, get_qdrant_settings

load_dotenv()

# Embedding model (must match ingest)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")


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
    Memuat database vektor Qdrant dan mengembalikannya sebagai retriever.
    Retriever ini bertugas mencari konteks skema yang relevan.
    """
    embedding_function = get_embedding_function()
    
    # Connect to Qdrant using centralized config helper
    client = get_qdrant_client()
    settings = get_qdrant_settings()

    db = Qdrant(
        client=client,
        collection_name=settings.get("collection", "schema_vectors"),
        embeddings=embedding_function
    )
    
    # Mengambil 2 potongan konteks paling relevan
    return db.as_retriever(search_kwargs={"k": 2})
