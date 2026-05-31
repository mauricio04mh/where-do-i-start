import pytest

from src.algorithms.backtracking import build_backtracking_learning_path
from src.algorithms.greedy import build_greedy_learning_path
from src.models.resource import Resource
from src.models.student import Student
from src.services.path_service import generate_path_for_student
from src.utils.validators import validate_learning_path


def make_resource(
    resource_id: str,
    title: str | None = None,
    duration_hours: int = 2,
    difficulty: int = 2,
    prerequisites: list[str] | None = None,
    topic: str = "AI Chatbots",
    description: str = "Build chatbot applications with Python.",
    resource_type: str = "course",
) -> Resource:
    return Resource(
        id=resource_id,
        title=title or resource_id.replace("-", " ").title(),
        topic=topic,
        duration_hours=duration_hours,
        difficulty=difficulty,
        prerequisites=prerequisites or [],
        description=description,
        type=resource_type,
    )


def make_student(
    available_hours: int = 8,
    known_resources: list[str] | None = None,
    preferred_difficulty: int = 2,
) -> Student:
    return Student(
        id="student-test",
        goal="Build an AI chatbot with Python",
        available_hours=available_hours,
        known_resources=known_resources or [],
        preferred_difficulty=preferred_difficulty,
        preference="balanced",
        target_topics=["AI Chatbots"],
    )


def test_backtracking_returns_valid_path() -> None:
    student = make_student()
    resources = [
        make_resource("chatbot-basics"),
        make_resource("chatbot-project", prerequisites=["chatbot-basics"]),
    ]

    path = build_backtracking_learning_path(student, resources)
    validation = validate_learning_path(path, student)

    assert validation["is_valid"] is True
    assert path.resources


def test_backtracking_respects_time_limit() -> None:
    student = make_student(available_hours=3)
    resources = [
        make_resource("short-chatbot-intro", duration_hours=2),
        make_resource("long-chatbot-project", duration_hours=5),
    ]

    path = build_backtracking_learning_path(student, resources)

    assert path.total_duration <= student.available_hours
    assert validate_learning_path(path, student)["is_valid"] is True


def test_backtracking_orders_prerequisites_before_dependents() -> None:
    student = make_student()
    resources = [
        make_resource("chatbot-project", prerequisites=["chatbot-basics"]),
        make_resource("chatbot-basics"),
    ]

    path = build_backtracking_learning_path(student, resources)

    assert path.resource_ids.index("chatbot-basics") < path.resource_ids.index(
        "chatbot-project"
    )
    assert validate_learning_path(path, student)["is_valid"] is True


def test_backtracking_does_not_include_duplicate_resources() -> None:
    student = make_student()
    resources = [
        make_resource("python-basics", topic="Programming"),
        make_resource("chatbot-api", prerequisites=["python-basics"]),
        make_resource("chatbot-ui", prerequisites=["python-basics"]),
    ]

    path = build_backtracking_learning_path(student, resources)

    assert len(path.resource_ids) == len(set(path.resource_ids))
    assert validate_learning_path(path, student)["is_valid"] is True


def test_backtracking_utility_is_at_least_greedy_on_small_instance() -> None:
    student = make_student(available_hours=6)
    resources = [
        make_resource("short-chatbot-intro", duration_hours=2),
        make_resource("short-chatbot-api", duration_hours=2),
        make_resource("short-chatbot-project", duration_hours=2),
        make_resource("long-chatbot-capstone", duration_hours=6),
    ]

    greedy_path = build_greedy_learning_path(student, resources)
    backtracking_path = build_backtracking_learning_path(student, resources)

    assert backtracking_path.total_utility >= greedy_path.total_utility
    assert validate_learning_path(backtracking_path, student)["is_valid"] is True


def test_path_service_accepts_backtracking() -> None:
    result = generate_path_for_student(
        "student-chatbot-beginner",
        algorithm="backtracking",
    )

    assert result["algorithm"] == "backtracking"
    assert result["validation"]["is_valid"] is True


def test_path_service_rejects_invalid_algorithm() -> None:
    with pytest.raises(ValueError, match="Unsupported algorithm"):
        generate_path_for_student("student-chatbot-beginner", algorithm="unknown")
