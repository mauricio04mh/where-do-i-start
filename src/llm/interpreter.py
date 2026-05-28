from src.llm.config import load_llm_config
from src.llm.prompts import STUDENT_PROFILE_SYSTEM_PROMPT
from src.llm.schemas import StudentProfileExtraction


def interpret_student_profile(user_text: str) -> StudentProfileExtraction:
    config = load_llm_config()

    if not config.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required to interpret student profiles. "
            "Create a .env file from .env.example and set your API key."
        )

    return _interpret_with_llm(user_text, config.openai_api_key, config.model)


def _interpret_with_llm(
    user_text: str, api_key: str, model: str
) -> StudentProfileExtraction:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    try:
        if hasattr(client, "responses") and hasattr(client.responses, "parse"):
            response = client.responses.parse(
                model=model,
                input=[
                    {"role": "system", "content": STUDENT_PROFILE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                ],
                text_format=StudentProfileExtraction,
            )
            if response.output_parsed is not None:
                return response.output_parsed

        if (
            hasattr(client, "beta")
            and hasattr(client.beta, "chat")
            and hasattr(client.beta.chat.completions, "parse")
        ):
            completion = client.beta.chat.completions.parse(
                model=model,
                messages=[
                    {"role": "system", "content": STUDENT_PROFILE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                ],
                response_format=StudentProfileExtraction,
            )
            parsed = completion.choices[0].message.parsed
            if parsed is not None:
                return parsed
    except Exception as exc:
        raise RuntimeError(
            "OpenAI profile interpretation failed. Check your API key, model, "
            "and network connection."
        ) from exc

    raise RuntimeError(
        "The installed OpenAI SDK does not expose a supported structured "
        "output parsing method."
    )
