from src.algorithms.backtracking import build_backtracking_learning_path
from src.algorithms.greedy import build_greedy_learning_path
from src.evaluation.metrics import evaluate_learning_path
from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.repositories.resource_repository import list_resources
from src.repositories.student_repository import get_student
from src.llm.evaluator import build_llm_scored_resources
from src.utils.validators import validate_learning_path

SUPPORTED_ALGORITHMS = {"greedy", "backtracking"}


def generate_path_for_student(
    student_id: str,
    algorithm: str = "greedy",
    use_llm: bool = False,
) -> dict:
    student = get_student(student_id)
    if student is None:
        raise ValueError(f"Student with id '{student_id}' was not found.")

    return generate_path_for_student_object(student, algorithm, use_llm=use_llm)


def generate_path_for_student_object(
    student: Student,
    algorithm: str = "greedy",
    use_llm: bool = False,
    llm_top_k: int | None = None,
    llm_score_weight: float | None = None,
    resources: list[Resource] | None = None,
) -> dict:
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"Unsupported algorithm '{algorithm}'. "
            "Supported algorithms are: greedy, backtracking."
        )

    source_resources = resources if resources is not None else list_resources()
    llm_debug = None
    if use_llm:
        source_resources, llm_debug = build_llm_scored_resources(
            student=student,
            resources=source_resources,
            top_k=llm_top_k,
            score_weight=llm_score_weight,
        )

    path = build_learning_path(
        algorithm=algorithm,
        student=student,
        resources=source_resources,
        use_precomputed_utility=use_llm,
    )
    validation = validate_learning_path(path, student)
    metrics = evaluate_learning_path(path, student, algorithm)

    return {
        "student": student,
        "algorithm": algorithm,
        "path": path.resources,
        "metrics": metrics,
        "validation": validation,
        "llm_debug": llm_debug,
    }


def build_learning_path(
    algorithm: str,
    student: Student,
    resources: list[Resource],
    use_precomputed_utility: bool = False,
) -> LearningPath:
    if algorithm == "greedy":
        return build_greedy_learning_path(
            student,
            resources,
            use_precomputed_utility=use_precomputed_utility,
        )
    if algorithm == "backtracking":
        return build_backtracking_learning_path(
            student,
            resources,
            use_precomputed_utility=use_precomputed_utility,
        )

    raise ValueError(
        f"Unsupported algorithm '{algorithm}'. "
        "Supported algorithms are: greedy, backtracking."
    )
