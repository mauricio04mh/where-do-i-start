from src.algorithms.greedy import build_greedy_learning_path
from src.evaluation.metrics import evaluate_learning_path
from src.models.student import Student
from src.repositories.resource_repository import list_resources
from src.repositories.student_repository import get_student
from src.utils.validators import validate_learning_path


def generate_path_for_student(
    student_id: str,
    algorithm: str = "greedy",
) -> dict:
    student = get_student(student_id)
    if student is None:
        raise ValueError(f"Student with id '{student_id}' was not found.")

    return generate_path_for_student_object(student, algorithm)


def generate_path_for_student_object(
    student: Student,
    algorithm: str = "greedy",
) -> dict:
    if algorithm != "greedy":
        raise ValueError(
            f"Unsupported algorithm '{algorithm}'. Currently only 'greedy' is supported."
        )

    resources = list_resources()
    path = build_greedy_learning_path(student, resources)
    validation = validate_learning_path(path, student)
    metrics = evaluate_learning_path(path, student, algorithm)

    return {
        "student": student,
        "algorithm": algorithm,
        "path": path.resources,
        "metrics": metrics,
        "validation": validation,
    }
