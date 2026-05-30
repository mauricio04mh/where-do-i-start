from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from src.api.schemas import GeneratePathRequest, GeneratePathResponse
from src.services.path_service import generate_path_for_student

router = APIRouter()


@router.post("/generate", response_model=GeneratePathResponse)
def generate_path(payload: GeneratePathRequest) -> dict:
    # TODO: Use LLM-based scoring when use_llm is enabled.
    try:
        result = generate_path_for_student(
            student_id=payload.student_id,
            algorithm=payload.algorithm,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 400
        if "was not found" in message:
            status_code = 404
        raise HTTPException(status_code=status_code, detail=message) from exc

    return _serialize_path_result(result)


def _serialize_path_result(result: dict) -> dict:
    return {
        "student": asdict(result["student"]),
        "algorithm": result["algorithm"],
        "path": [asdict(resource) for resource in result["path"]],
        "metrics": result["metrics"],
        "validation": result["validation"],
    }
