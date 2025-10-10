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
    prompt: str
    model: str = "openai/gpt-5-mini"

    class Config:
        schema_extra = {
            "example": {
                "prompt": "Jelaskan tentang machine learning dalam bahasa sederhana",
                "model": "openai/gpt-5-mini"
            }
        }