from typing import Tuple, Dict, Any

def run_with_gemini_token_count(chain, inputs: Any, model_name: str) -> Tuple[Any, Dict[str, int]]:
    """
    Jalankan chain sekaligus hitung token input/output untuk Gemini.
    inputs bisa berupa dict atau string sesuai chain.
    """
    # Serialize input yang relevan untuk token count
    if isinstance(inputs, dict):
        serialized_input = " ".join(str(v) for v in inputs.values())
    else:
        serialized_input = str(inputs)

    from src.utils.token_usage import gemini_input_tokens, gemini_output_tokens

    input_tokens = gemini_input_tokens(model_name, serialized_input)

    output = chain.invoke(inputs)

    serialized_output = str(output)
    output_tokens = gemini_output_tokens(model_name, serialized_output)

    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }
    return output, usage