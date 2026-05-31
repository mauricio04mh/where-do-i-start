from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from src.api.schemas import GeneratePathRequest, GeneratePathResponse
from src.llm.evaluator import (
    build_llm_scored_resources,
    build_rule_based_scoring_debug,
)
from src.repositories.resource_repository import list_resources
from src.repositories.student_repository import get_student
from src.services.path_service import generate_path_for_student

router = APIRouter()


@router.post("/generate", response_model=GeneratePathResponse)
def generate_path(payload: GeneratePathRequest) -> dict:
    try:
        result = generate_path_for_student(
            student_id=payload.student_id,
            algorithm=payload.algorithm,
            use_llm=payload.use_llm,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        message = str(exc)
        status_code = 400
        if "was not found" in message:
            status_code = 404
        raise HTTPException(status_code=status_code, detail=message) from exc

    return _serialize_path_result(result)


@router.post("/debug-scoring")
def debug_scoring(payload: GeneratePathRequest) -> dict:
    student = get_student(payload.student_id)
    if student is None:
        raise HTTPException(
            status_code=404,
            detail=f"Student with id '{payload.student_id}' was not found.",
        )

    resources = list_resources()
    try:
        if payload.use_llm:
            _, debug = build_llm_scored_resources(student, resources)
            return debug

        return build_rule_based_scoring_debug(student, resources)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _serialize_path_result(result: dict) -> dict:
    return {
        "student": asdict(result["student"]),
        "algorithm": result["algorithm"],
        "path": [asdict(resource) for resource in result["path"]],
        "metrics": result["metrics"],
        "validation": result["validation"],
        "llm_debug": result.get("llm_debug"),
    }
