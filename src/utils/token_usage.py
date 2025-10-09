import os
from typing import Dict, Any

try:
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # type: ignore
    GEMINI_AVAILABLE = True
except Exception:
    genai = None
    GEMINI_AVAILABLE = False

def gemini_input_tokens(model_name: str, text: str) -> int:
    if not GEMINI_AVAILABLE:
        return len(text) // 4
    try:
        model = genai.GenerativeModel(model_name)  # type: ignore
        resp = model.count_tokens([{"role": "user", "parts": [text]}])  # type: ignore
        return resp.total_tokens
    except Exception:
        return len(text) // 4

def gemini_output_tokens(model_name: str, text: str) -> int:
    if not GEMINI_AVAILABLE:
        return len(text) // 4
    try:
        model = genai.GenerativeModel(model_name)  # type: ignore
        resp = model.count_tokens([{"role": "model", "parts": [text]}])  # type: ignore
        return resp.total_tokens
    except Exception:
        return len(text) // 4

def merge_usage(existing: Dict[str, Any], add: Dict[str, Any]) -> Dict[str, Any]:
    merged = {**existing}
    for k, v in add.items():
        merged[k] = merged.get(k, 0) + v
    return merged