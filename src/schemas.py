from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    model: str = "gemini-2.5-flash"

    class Config:
        schema_extra = {
            "example": {
                "question": "Tampilkan 5 program dengan anggaran terbesar di tahun 2024",
                "model": "gemini-2.5-flash"
            }
        }


class ContextualQueryRequest(BaseModel):
    question: str
    conversation_id: str

    class Config:
        schema_extra = {
            "example": {
                "question": "Bagaimana dengan program di Direktorat Keuangan?",
                "conversation_id": "user_123_session_1"
            }
        }

class OpenRouterRequest(BaseModel):
    question: str
    model_name: str

    class Config:
        schema_extra = {
            "example": {
                "prompt": "Jelaskan tentang machine learning dalam bahasa sederhana",
                "model": "openai/gpt-5-mini"
            }
        }

class NLToSQLRequestEndpoint(BaseModel):
    question: str
    model_name: str
    unit: str
    nip: str
    token_in: int = 0
    token_out: int = 0
    total_token: int = 0

    class Config:
        schema_extra = {
            "example": {
                "question": "Tampilkan 5 program dengan anggaran terbesar di tahun 2024",
                "model_name": "meta-llama/llama-3-70b-instruct",
                "unit": "Direktorat Keuangan",
                "nip": "123456789"
            }
        }