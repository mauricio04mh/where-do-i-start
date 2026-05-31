from src.algorithms.backtracking import build_backtracking_learning_path
from src.algorithms.greedy import build_greedy_learning_path
from src.evaluation.metrics import evaluate_learning_path
from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.repositories.resource_repository import list_resources
from src.repositories.student_repository import get_student
from src.utils.validators import validate_learning_path

SUPPORTED_ALGORITHMS = {"greedy", "backtracking"}


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
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"Unsupported algorithm '{algorithm}'. "
            "Supported algorithms are: greedy, backtracking."
        )

    resources = list_resources()
    path = build_learning_path(
        algorithm=algorithm,
        student=student,
        resources=resources,
    )
    validation = validate_learning_path(path, student)
    metrics = evaluate_learning_path(path, student, algorithm)

    return {
        "student": student,
        "algorithm": algorithm,
        "path": path.resources,
        "metrics": metrics,
        "validation": validation,
    }


def build_learning_path(
    algorithm: str,
    student: Student,
    resources: list[Resource],
) -> LearningPath:
    if algorithm == "greedy":
        return build_greedy_learning_path(student, resources)
    if algorithm == "backtracking":
        return build_backtracking_learning_path(student, resources)

    raise ValueError(
        f"Unsupported algorithm '{algorithm}'. "
        "Supported algorithms are: greedy, backtracking."
    )
