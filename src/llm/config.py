import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    gemini_api_key: str | None
    gemini_model: str


def load_llm_config() -> LLMConfig:
    load_dotenv()

    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    gemini_api_key = os.getenv("GEMINI_API_KEY") or None
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

    return LLMConfig(
        provider=provider,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
    )
