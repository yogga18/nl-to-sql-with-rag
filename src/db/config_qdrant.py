import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()
# --- Qdrant configuration with sensible defaults --- GRPC off
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_PREFER_GRPC = False


def get_qdrant_client() -> QdrantClient:
    """Return a configured QdrantClient. Currently forces REST (HTTP) mode.

    If you want to enable gRPC later, change QDRANT_PREFER_GRPC to True or update this helper.
    """
    return QdrantClient(url=QDRANT_URL, prefer_grpc=False, api_key=QDRANT_API_KEY)


def get_qdrant_settings():
    return {
        "url": QDRANT_URL,
        "collection": os.getenv("QDRANT_COLLECTION", "schema_vectors"),
        "prefer_grpc": QDRANT_PREFER_GRPC,
    }
