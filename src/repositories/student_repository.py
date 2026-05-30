import json
from dataclasses import asdict
from pathlib import Path

from src.models.student import Student
from src.utils.loaders import load_students


def list_students(path: str = "data/students.json") -> list[Student]:
    return load_students(path)


def get_student(
    student_id: str,
    path: str = "data/students.json",
) -> Student | None:
    for student in list_students(path):
        if student.id == student_id:
            return student

    return None


def create_student(
    student: Student,
    path: str = "data/students.json",
) -> Student:
    students = list_students(path)
    if any(existing_student.id == student.id for existing_student in students):
        raise ValueError(f"Student with id '{student.id}' already exists.")

    students.append(student)
    _write_students(students, path)
    return student


def update_student(
    student_id: str,
    updates: dict,
    path: str = "data/students.json",
) -> Student | None:
    students = list_students(path)

    for index, student in enumerate(students):
        if student.id == student_id:
            student_data = asdict(student)
            student_data.update(
                {
                    field: value
                    for field, value in updates.items()
                    if value is not None
                }
            )
            updated_student = Student(**student_data)
            students[index] = updated_student
            _write_students(students, path)
            return updated_student

    return None


def delete_student(
    student_id: str,
    path: str = "data/students.json",
) -> bool:
    students = list_students(path)
    remaining_students = [
        student for student in students if student.id != student_id
    ]

    if len(remaining_students) == len(students):
        return False

    _write_students(remaining_students, path)
    return True


def _write_students(students: list[Student], path: str) -> None:
    file_path = Path(path)
    with file_path.open("w", encoding="utf-8") as file:
        json.dump([asdict(student) for student in students], file, indent=2)
        file.write("\n")
