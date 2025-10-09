from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from src.schemas import QueryRequest, ContextualQueryRequest
from src.services.api_service import (
    generate_sql_only,
    route_and_generate_sql,
    contextual_nl_to_sql,
)

router = APIRouter()

# Rate limiter instance (can be replaced with app.state.limiter in main)
limiter = Limiter(key_func=get_remote_address)


@router.get("/", tags=["Health Check"], summary="🏥 Health Check")
def read_root():
    return {"message": "🚀 NL-to-SQL API is running successfully!", "status": "healthy", "version": "1.0.0"}


@router.post("/generate-sql-only", tags=["SQL Generation"], summary="🔧 Generate SQL Query Only")
@limiter.limit("25/minute")
def generate_sql(request_body: QueryRequest, request: Request):
    return generate_sql_only(request_body.question, request_body.model)


@router.post("/generate-sql-execute-analyze", tags=["Complete Workflow"])
def ask(request_body: QueryRequest):
    return route_and_generate_sql(request_body.question, request_body.model)


@router.post("/context-nl-to-sql", tags=["Conversational AI"], summary="💬 Contextual NL-to-SQL with Memory")
@limiter.limit("25/minute")
def ask_contextual(request_body: ContextualQueryRequest, request: Request):
    # TODO: wire conversation history store (in-memory or redis)
    conversation_histories = {}
    formatted_history = ""  # placeholder: transform conversation_histories[request_body.conversation_id]
    return contextual_nl_to_sql(request_body.question, formatted_history)
