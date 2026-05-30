import json
from pathlib import Path
from typing import TypeVar

from src.models.resource import Resource
from src.models.student import Student

T = TypeVar("T")


def _read_json_list(path: str) -> list[dict]:
    file_path = Path(path)

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Data file not found: {file_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {file_path}: {exc.msg}") from exc

    if not isinstance(data, list):
        raise ValueError(f"Expected {file_path} to contain a JSON list.")

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Expected item {index} in {file_path} to be an object.")

    return data


def _build_items(path: str, model_type: type[T]) -> list[T]:
    items = _read_json_list(path)
    built_items: list[T] = []

    for index, item in enumerate(items):
        try:
            built_items.append(model_type(**item))
        except TypeError as exc:
            raise ValueError(
                f"Invalid {model_type.__name__} at index {index} in {path}: {exc}"
            ) from exc

    return built_items


def load_resources(path: str) -> list[Resource]:
    return _build_items(path, Resource)


def load_students(path: str) -> list[Student]:
    items = _read_json_list(path)
    students: list[Student] = []

    for index, item in enumerate(items):
        student_data = {
            **item,
            "target_topics": item.get("target_topics", []),
            "constraints": item.get("constraints", []),
        }
        try:
            students.append(Student(**student_data))
        except TypeError as exc:
            raise ValueError(
                f"Invalid Student at index {index} in {path}: {exc}"
            ) from exc

    return students


def get_student_by_id(students: list[Student], student_id: str) -> Student:
    for student in students:
        if student.id == student_id:
            return student

    raise ValueError(f"Student with id '{student_id}' was not found.")
