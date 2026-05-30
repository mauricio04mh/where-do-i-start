from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from src.api.schemas import StudentCreate, StudentResponse, StudentUpdate
from src.models.student import Student
from src.repositories.student_repository import (
    create_student,
    delete_student,
    get_student,
    list_students,
    update_student,
)

router = APIRouter()


@router.get("", response_model=list[StudentResponse])
def get_students() -> list[dict]:
    return [asdict(student) for student in list_students()]


@router.get("/{student_id}", response_model=StudentResponse)
def get_student_by_id(student_id: str) -> dict:
    student = get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    return asdict(student)


@router.post("", response_model=StudentResponse)
def post_student(payload: StudentCreate) -> dict:
    try:
        student = create_student(Student(**_model_dump(payload)))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return asdict(student)


@router.put("/{student_id}", response_model=StudentResponse)
def put_student(student_id: str, payload: StudentUpdate) -> dict:
    student = update_student(student_id, _model_dump(payload))
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    return asdict(student)


@router.delete("/{student_id}")
def delete_student_by_id(student_id: str) -> dict:
    deleted = delete_student(student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Student not found.")

    return {"deleted": True, "student_id": student_id}


def _model_dump(model) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()
