import pytest

from src.algorithms import simulated_annealing
from src.algorithms.simulated_annealing import (
    build_simulated_annealing_learning_path,
)
from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.services.path_service import SUPPORTED_ALGORITHMS
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
    utility: float = 10.0,
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
        utility=utility,
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
        constraints=[],
    )


def test_simulated_annealing_returns_learning_path() -> None:
    path = build_simulated_annealing_learning_path(
        make_student(),
        [make_resource("chatbot-basics")],
        max_iterations=50,
    )

    assert isinstance(path, LearningPath)


def test_simulated_annealing_returns_valid_path() -> None:
    student = make_student()
    resources = [
        make_resource("chatbot-project", prerequisites=["chatbot-basics"]),
        make_resource("chatbot-basics"),
    ]

    path = build_simulated_annealing_learning_path(
        student,
        resources,
        max_iterations=100,
    )

    assert validate_learning_path(path, student)["is_valid"] is True


def test_simulated_annealing_respects_time_limit() -> None:
    student = make_student(available_hours=3)
    resources = [
        make_resource("short-chatbot-intro", duration_hours=2),
        make_resource("long-chatbot-project", duration_hours=5),
    ]

    path = build_simulated_annealing_learning_path(
        student,
        resources,
        max_iterations=100,
    )

    assert path.total_duration <= student.available_hours
    assert validate_learning_path(path, student)["is_valid"] is True


def test_simulated_annealing_does_not_duplicate_resources() -> None:
    student = make_student()
    resources = [
        make_resource("python-basics", topic="Programming"),
        make_resource("chatbot-api", prerequisites=["python-basics"]),
        make_resource("chatbot-ui", prerequisites=["python-basics"]),
    ]

    path = build_simulated_annealing_learning_path(
        student,
        resources,
        max_iterations=100,
    )

    assert len(path.resource_ids) == len(set(path.resource_ids))
    assert validate_learning_path(path, student)["is_valid"] is True


def test_simulated_annealing_orders_prerequisites_before_dependents() -> None:
    student = make_student()
    resources = [
        make_resource("chatbot-project", prerequisites=["chatbot-basics"]),
        make_resource("chatbot-basics"),
    ]

    path = build_simulated_annealing_learning_path(
        student,
        resources,
        max_iterations=100,
    )

    assert path.resource_ids.index("chatbot-basics") < path.resource_ids.index(
        "chatbot-project"
    )
    assert validate_learning_path(path, student)["is_valid"] is True


def test_simulated_annealing_is_reproducible_with_seed() -> None:
    student = make_student(available_hours=6)
    resources = [
        make_resource("chatbot-basics", utility=8.0),
        make_resource("chatbot-flows", utility=7.0),
        make_resource("chatbot-api", utility=9.0),
        make_resource("chatbot-project", duration_hours=3, utility=12.0),
    ]

    first_path = build_simulated_annealing_learning_path(
        student,
        resources,
        max_iterations=150,
        seed=42,
        use_precomputed_utility=True,
        min_utility_threshold=0.0,
    )
    second_path = build_simulated_annealing_learning_path(
        student,
        resources,
        max_iterations=150,
        seed=42,
        use_precomputed_utility=True,
        min_utility_threshold=0.0,
    )

    assert first_path.resource_ids == second_path.resource_ids


def test_simulated_annealing_uses_precomputed_utility_without_rule_scoring(
    monkeypatch,
) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Rule-based scoring should not be recalculated")

    monkeypatch.setattr(
        simulated_annealing,
        "compute_rule_based_utility",
        fail_if_called,
    )
    student = make_student(available_hours=2)
    resources = [
        make_resource("high-utility", duration_hours=2, utility=15.0),
        make_resource("low-utility", duration_hours=2, utility=1.0),
    ]

    path = build_simulated_annealing_learning_path(
        student,
        resources,
        max_iterations=50,
        use_precomputed_utility=True,
        min_utility_threshold=0.0,
    )

    assert path.resource_ids == ["high-utility"]
    assert path.total_utility == pytest.approx(15.0)


def test_supported_algorithms_contains_simulated_annealing() -> None:
    assert "simulated_annealing" in SUPPORTED_ALGORITHMS
