from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    model: str = "gemini-2.5-flash"

    class Config:
        schema_extra = {
            "example": {
                "question": "Tampilkan 5 program dengan anggaran terbesar di tahun 2024",
                "model": "openai/gpt-4.1"
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
