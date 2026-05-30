import json

from src.llm.config import load_llm_config
from src.llm.prompts import STUDENT_PROFILE_SYSTEM_PROMPT
from src.llm.schemas import StudentProfileExtraction


def interpret_student_profile(user_text: str) -> StudentProfileExtraction:
    config = load_llm_config()

    if config.provider != "gemini":
        raise RuntimeError(
            f"Gemini is the mandatory LLM provider, but LLM_PROVIDER is "
            f"{config.provider!r}."
        )

    if not config.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is required to interpret student profiles. "
            "Create a .env file from .env.example and set your API key."
        )

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.gemini_api_key)

    try:
        response = client.models.generate_content(
            model=config.gemini_model,
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=STUDENT_PROFILE_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=StudentProfileExtraction,
            ),
        )
        data = json.loads(response.text)
        return StudentProfileExtraction(**data)
    except Exception as exc:
        raise RuntimeError(
            "Gemini profile interpretation failed. Check your API key, model, "
            f"and network connection. Original error: {type(exc).__name__}: {exc}"
        ) from exc
