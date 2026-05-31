import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    gemini_api_key: str | None
    gemini_model: str
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: int
    llm_candidate_top_k: int
    llm_score_weight: float


def load_llm_config() -> LLMConfig:
    load_dotenv()

    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    gemini_api_key = os.getenv("GEMINI_API_KEY") or None
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    ollama_base_url = (
        os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
    ).rstrip("/")
    ollama_model = os.getenv("OLLAMA_MODEL") or "llama3.2:3b"
    ollama_timeout_seconds = _read_positive_int("OLLAMA_TIMEOUT_SECONDS", 120)
    llm_candidate_top_k = _read_positive_int("LLM_CANDIDATE_TOP_K", 15)
    llm_score_weight = _read_non_negative_float("LLM_SCORE_WEIGHT", 1.0)

    return LLMConfig(
        provider=provider,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        ollama_timeout_seconds=ollama_timeout_seconds,
        llm_candidate_top_k=llm_candidate_top_k,
        llm_score_weight=llm_score_weight,
    )


def _read_positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default

    if value < 1:
        return default

    return value


def _read_non_negative_float(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default

    if value < 0:
        return default

    return value
