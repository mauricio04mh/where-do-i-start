from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from src.api.schemas import ChatAskRequest, ChatAskResponse
from src.llm.interpreter import interpret_student_profile
from src.llm.profile_mapper import profile_to_student
from src.repositories.resource_repository import list_resources
from src.services.path_service import generate_path_for_student_object

router = APIRouter()


@router.post("/ask", response_model=ChatAskResponse)
def ask_chat(payload: ChatAskRequest) -> dict:
    try:
        profile = interpret_student_profile(payload.message)
        generated_student = profile_to_student(
            profile,
            resources=list_resources(),
        )
        result = generate_path_for_student_object(
            generated_student,
            payload.algorithm,
            use_llm=payload.use_llm,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"LLM profile interpretation failed: {exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "interpreted_profile": _model_dump(profile),
        "generated_student": asdict(generated_student),
        "algorithm": result["algorithm"],
        "path": [asdict(resource) for resource in result["path"]],
        "metrics": result["metrics"],
        "validation": result["validation"],
        "llm_debug": result.get("llm_debug"),
    }


def _model_dump(model) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()
