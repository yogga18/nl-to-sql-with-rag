import json
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import tiktoken

# Gemini
try:
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # type: ignore
    gemini_available = True
except ImportError:
    genai = None
    gemini_available = False

# Llama (lazy load)
llama_tokenizer = None
def get_llama_tokenizer():
    global llama_tokenizer
    if llama_tokenizer is None:
        from transformers import AutoTokenizer
        llama_tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B")
    return llama_tokenizer


class TokenCountMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token_count = 0
        model_name = "unknown"

        try:
            body = await request.body()
            data = {}
            if body:
                try:
                    data = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError:
                    data = {}

            model_name = data.get("model", "unknown")

            # Ambil teks
            if "messages" in data:
                text = " ".join([m.get("content", "") for m in data["messages"]])
            elif "prompt" in data:
                text = data["prompt"]
            else:
                text = str(data)

            # GPT / OpenAI
            if model_name.startswith("openai/") or model_name.startswith("gpt"):
                try:
                    encoding = tiktoken.encoding_for_model(model_name.replace("openai/", ""))
                except KeyError:
                    encoding = tiktoken.get_encoding("cl100k_base")
                token_count = len(encoding.encode(text))

            # Gemini
            elif gemini_available and ("google/" in model_name or "gemini" in model_name):
                try:
                    model = genai.GenerativeModel(model_name.replace("google/", ""))  # type: ignore
                    resp = model.count_tokens([{"role": "user", "parts": [text]}])   # type: ignore
                    token_count = resp.total_tokens
                except Exception as e:
                    print("Gemini token count error:", e)
                    token_count = len(text) // 4

            # Llama
            elif "llama" in model_name.lower():
                tokenizer = get_llama_tokenizer()
                token_count = len(tokenizer.encode(text))

            # Fallback
            else:
                token_count = len(text) // 4

        except Exception as e:
            print("Token count error:", e)

        # Simpan ke request.state
        request.state.token_count = token_count
        request.state.model_name = model_name

        response: Response = await call_next(request)
        response.headers["X-Token-Count"] = str(token_count)
        response.headers["X-Model-Name"] = model_name
        return response