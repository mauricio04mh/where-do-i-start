import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class LLMConfig:
    openai_api_key: str | None
    model: str


def load_llm_config() -> LLMConfig:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY") or None
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    return LLMConfig(
        openai_api_key=api_key,
        model=model,
    )
