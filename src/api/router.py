from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.schemas import QueryRequest, ContextualQueryRequest, NLToSQLRequestEndpoint
from src.services.api_service import (
    generate_sql_only,
    route_and_generate_sql,
    contextual_nl_to_sql,
)

from src.services.openrouter_service import (
    get_available_models,
    openrouter_nl_to_sql_workflow
)
# NLToSQLRequest
from src.services.openrouter_service import NLToSQLRequest
from src.services.api_service import NLToSQLGeminiRequest

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)


@router.get("/", tags=["Health Check"], summary="🏥 Health Check")
def read_root():
    return {"message": "🚀 NL-to-SQL API is running successfully!", "status": "healthy", "version": "1.0.0"}

# GEMINI / LLM ENDPOINTS
@router.post("/generate-sql-only", tags=["SQL Generation"], summary="🔧 Generate SQL Query Only")
@limiter.limit("25/minute")
def generate_sql(request_body: QueryRequest, request: Request):
    return generate_sql_only(request_body.question, request_body.model)


@router.post("/generate-sql-execute-analyze", tags=["Complete Workflow"])
def ask(payload: NLToSQLRequestEndpoint, request: Request):
    print("Received payload:", payload)
    return route_and_generate_sql(
        NLToSQLGeminiRequest(
            question=payload.question,
            model_name=payload.model_name,
            unit=payload.unit,
            nip=payload.nip
        )
    )


# @router.post("/context-nl-to-sql", tags=["Conversational AI"], summary="💬 Contextual NL-to-SQL with Memory")
# @limiter.limit("25/minute")
# def ask_contextual(request_body: ContextualQueryRequest, request: Request):
#     conversation_histories = {}
#     formatted_history = ""
#     return contextual_nl_to_sql(request_body.question, formatted_history)


# OPENROUTER ENDPOINTS
@router.get("/openrouter/models", tags=["OpenRouter"], summary="📋 Get Available Models")
def list_openrouter_models():
    return get_available_models()

@router.post("/openrouter/nl-to-sql", tags=["OpenRouter"], summary="🔧 NL-to-SQL with OpenRouter Models")
def openrouter_nl_to_sql(payload: NLToSQLRequestEndpoint, request: Request):
    print("Received payload:", payload)
    return openrouter_nl_to_sql_workflow(
        NLToSQLRequest(
            question=payload.question,
            model_name=payload.model_name,
            unit=payload.unit,
            nip=payload.nip
        )
    )

# API DASHBOARD
from src.services.dashboard_service import get_all_trx_pertanyaan_service, get_trx_pertanyaan_by_nip_service, get_trx_pertanyaan_by_id_service
@router.get("/dashboard/getall", tags=["Dashboard"], summary="📊 Get All Questions")
def get_all_questions(limit: int = 300):
    return get_all_trx_pertanyaan_service(limit)

@router.get("/dashboard/getbynip/{nip}", tags=["Dashboard"], summary="📊 Get Questions by NIP")
def get_questions_by_nip(nip: int):
    return get_trx_pertanyaan_by_nip_service(nip)

@router.get("/dashboard/getbyid/{id}", tags=["Dashboard"], summary="📊 Get Questions by ID Question")
def get_questions_by_id(id: int):
    return get_trx_pertanyaan_by_id_service(id)