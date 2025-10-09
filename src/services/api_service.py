from typing import Dict, Any
from src.nl2sql_service import (
    create_nl2sql_chain,
    create_router_chain,
    create_analysis_chain,
    create_nl2sql_with_conversation_chain,
    create_analysis_with_conversation_chain,
)
from src.db.executor import execute_sql_query
from src.utils.chain_wrapper import run_with_gemini_token_count
from src.utils.token_usage import merge_usage
from src.validation import is_safe_select_query, sanitize_sql_output


def route_and_generate_sql(question: str, model_name: str):
    router_chain = create_router_chain(model_name) # check promt ( klasifikasi )
    klasifikasi, usage_router = run_with_gemini_token_count(router_chain, {"question": question}, model_name)
    usage = {
        "router_input": usage_router["input_tokens"],
        "router_output": usage_router["output_tokens"],
        "router_total": usage_router["total_tokens"],
    }

    if "pengetahuan_umum" in klasifikasi.lower():
        return {"type": "REJECTED", "answer": "Maaf, saya hanya menjawab data perusahaan.", "token_usage": {"model": model_name, **usage}}

    sql_chain = create_nl2sql_chain(model_name) # generate sql ( no to sql )
    sql_query, usage_sql = run_with_gemini_token_count(sql_chain, question, model_name)
    usage = merge_usage(usage, {
        "sql_input": usage_sql["input_tokens"],
        "sql_output": usage_sql["output_tokens"],
        "sql_total": usage_sql["total_tokens"],
    })

    if "error" in sql_query.lower() or len(sql_query) < 5:
        return {"type": "SQL_GENERATION_FAILED", "answer": "Tidak dapat membuat query SQL.", "token_usage": {"model": model_name, **usage}}

    if not is_safe_select_query(sql_query):
        return {"type": "UNSAFE_SQL_QUERY", "answer": "Query tidak aman.", "generated_sql": sql_query, "token_usage": {"model": model_name, **usage}}

    sql_result_df = execute_sql_query(sql_query)

    if isinstance(sql_result_df, str):
        return {"type": "SQL_EXECUTION_ERROR", "answer": sql_result_df, "generated_sql": sql_query, "token_usage": {"model": model_name, **usage}}

    sql_result_for_llm = "Query berhasil dieksekusi, namun tidak ada data yang ditemukan."

    if not sql_result_df.empty:
        sql_result_for_llm = sql_result_df.to_string()

    analysis_chain = create_analysis_chain(model_name) # analisa dan reasoning dari hasil sql
    final_answer, usage_analysis = run_with_gemini_token_count(
        analysis_chain,
        {"question": question, "sql_result": sql_result_for_llm},
        model_name
    )
    usage = merge_usage(usage, {
        "analysis_input": usage_analysis["input_tokens"],
        "analysis_output": usage_analysis["output_tokens"],
        "analysis_total": usage_analysis["total_tokens"],
    })

    return {
        "type": "SUCCESS",
        "answer": final_answer,
        "generated_sql": sql_query,
        "raw_data": sql_result_df.to_dict(orient="records"),
        "token_usage": {"model": model_name, **usage, "grand_total": sum(v for k, v in usage.items() if k.endswith("_total"))}
    }


def generate_sql_only(question: str, model_name: str):
    router_chain = create_router_chain(model_name)
    klasifikasi = router_chain.invoke({"question": question})
    if "pengetahuan_umum" in klasifikasi.lower():
        return {"type": "REJECTED", "answer": "Maaf, saya hanya menjawab data perusahaan."}

    sql_chain = create_nl2sql_chain(model_name)
    sql_query = sql_chain.invoke(question)
    return {"type": "SQL_GENERATED", "sql_query": sql_query}


def contextual_nl_to_sql(question: str, conversation_history: str):
    sql_with_conv = create_nl2sql_with_conversation_chain()
    raw_sql_query = sql_with_conv.invoke({"question": question, "chat_history": conversation_history})
    sql_query = sanitize_sql_output(raw_sql_query)
    if "error" in sql_query.lower() or len(sql_query) < 5:
        return {"type": "SQL_GENERATION_FAILED", "answer": "Tidak dapat membuat query SQL."}
    if not is_safe_select_query(sql_query):
        return {"type": "UNSAFE_SQL_QUERY", "answer": "Query tidak aman.", "generated_sql": sql_query}

    sql_result_df = execute_sql_query(sql_query)
    if isinstance(sql_result_df, str):
        return {"type": "SQL_EXECUTION_ERROR", "answer": sql_result_df, "generated_sql": sql_query}

    sql_result_for_llm = "Query berhasil dieksekusi, namun tidak ada data yang ditemukan."
    if not sql_result_df.empty:
        sql_result_for_llm = sql_result_df.to_string()

    analysis_chain = create_analysis_with_conversation_chain()
    final_answer = analysis_chain.invoke({"question": question, "chat_history": conversation_history, "sql_result": sql_result_for_llm})

    return {"type": "SUCCESS", "answer": final_answer, "generated_sql": sql_query, "raw_data": sql_result_df.to_dict(orient="records")}
