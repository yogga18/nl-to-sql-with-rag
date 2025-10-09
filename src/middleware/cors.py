import os
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
    if ALLOWED_ORIGINS == "*":
        origins = ["*"]
    else:
        origins = [origin.strip() for origin in ALLOWED_ORIGINS.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )