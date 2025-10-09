from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from src.middleware.token_counter import TokenCountMiddleware
from src.api.router import router, limiter as api_limiter

load_dotenv()

# Thin FastAPI app: middleware, CORS and mounted router
app = FastAPI(
    title="🤖 NL-to-SQL Service API",
    version="1.0.0",
)

app.add_middleware(TokenCountMiddleware)

# CORS
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

# Attach limiter from router to app state so slowapi can access it
try:
    app.state.limiter = api_limiter
except Exception:
    # If slowapi isn't available at import time, ignore; routes will still work without global limiter
    pass

# Mount API router
app.include_router(router)