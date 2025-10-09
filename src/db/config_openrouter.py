import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("BASE_URL_OPEN_ROUTER")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME")

def get_openrouter_config():
    return {
        "api_key": OPENROUTER_API_KEY,
        "base_url": OPENROUTER_BASE_URL,
        "app_name": OPENROUTER_APP_NAME,
    }