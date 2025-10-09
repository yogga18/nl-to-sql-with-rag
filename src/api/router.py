# from fastapi import APIRouter, Request
# from slowapi import Limiter
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded
# from fastapi.responses import JSONResponse

# from src.schemas import QueryRequest, ContextualQueryRequest
# from src.services.api_service import (
#     generate_sql_only,
#     route_and_generate_sql,
#     contextual_nl_to_sql,
# )

# router = APIRouter()

# # Rate limiter instance (can be replaced with app.state.limiter in main)
# limiter = Limiter(key_func=get_remote_address)


# @router.get("/", tags=["Health Check"], summary="🏥 Health Check")
# def read_root():
#     return {"message": "🚀 NL-to-SQL API is running successfully!", "status": "healthy", "version": "1.0.0"}


# @router.post("/generate-sql-only", tags=["SQL Generation"], summary="🔧 Generate SQL Query Only")
# @limiter.limit("25/minute")
# def generate_sql(request_body: QueryRequest, request: Request):
#     return generate_sql_only(request_body.question, request_body.model)


# @router.post("/generate-sql-execute-analyze", tags=["Complete Workflow"])
# def ask(request_body: QueryRequest):
#     return route_and_generate_sql(request_body.question, request_body.model)


# @router.post("/context-nl-to-sql", tags=["Conversational AI"], summary="💬 Contextual NL-to-SQL with Memory")
# @limiter.limit("25/minute")
# def ask_contextual(request_body: ContextualQueryRequest, request: Request):
#     # TODO: wire conversation history store (in-memory or redis)
#     conversation_histories = {}
#     formatted_history = ""  # placeholder: transform conversation_histories[request_body.conversation_id]
#     return contextual_nl_to_sql(request_body.question, formatted_history)

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

# Update import ini
from src.schemas import QueryRequest, ContextualQueryRequest, OpenRouterRequest
from src.services.api_service import (
    generate_sql_only,
    route_and_generate_sql,
    contextual_nl_to_sql,
)
# Tambahkan import ini
from src.services.openrouter_service import (
    chat_with_openrouter,
    get_available_models,
    openrouter_nl_to_sql_workflow
)

router = APIRouter()

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
    conversation_histories = {}
    formatted_history = ""
    return contextual_nl_to_sql(request_body.question, formatted_history)


# ============= TAMBAHKAN 2 ENDPOINT INI =============
@router.post("/openrouter/chat", tags=["OpenRouter"], summary="🤖 Chat with OpenRouter (Multi-Model)")
@limiter.limit("30/minute")
def openrouter_chat(request_body: OpenRouterRequest, request: Request):
    """
    Chat dengan berbagai model AI melalui OpenRouter.
    
    - **prompt**: Pertanyaan atau instruksi Anda
    - **model**: Model AI yang ingin digunakan (contoh: "anthropic/claude-3-opus")
    
    Lihat daftar model yang tersedia di endpoint `/openrouter/models`
    """
    return chat_with_openrouter(request_body.prompt, request_body.model)


@router.get("/openrouter/models", tags=["OpenRouter"], summary="📋 Get Available Models")
def list_openrouter_models():
    """
    Menampilkan daftar model populer yang tersedia di OpenRouter.
    """
    return get_available_models()

@router.post("/openrouter/nl-to-sql", tags=["OpenRouter"], summary="🔧 NL-to-SQL with OpenRouter Models")
def openrouter_nl_to_sql(request_body: OpenRouterRequest, request: Request):
    """
    Generate SQL query from natural language using OpenRouter models.
    
    - **question**: Your natural language question
    - **model**: The OpenRouter model to use (e.g., "anthropic/claude-3-opus")
    
    See available models at `/openrouter/models`
    """
    return openrouter_nl_to_sql_workflow(request_body.prompt, request_body.model)
