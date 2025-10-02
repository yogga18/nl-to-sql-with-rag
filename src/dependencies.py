# src/dependencies.py

from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.retrievers import BaseRetriever

# Qdrant Configuration
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "schema_vectors"
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
    Memuat database vektor Qdrant dan mengembalikannya sebagai retriever.
    Retriever ini bertugas mencari konteks skema yang relevan.
    """
    embedding_function = get_embedding_function()
    
    # Connect to Qdrant
    client = QdrantClient(url=QDRANT_URL)
    
    db = Qdrant(
        client=client,
        collection_name=COLLECTION_NAME,
        embeddings=embedding_function
    )
    
    # Mengambil 2 potongan konteks paling relevan
    return db.as_retriever(search_kwargs={"k": 2})