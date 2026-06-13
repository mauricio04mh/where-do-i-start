import pytest

from src.algorithms import ant_colony
from src.algorithms.ant_colony import build_ant_colony_learning_path
from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.services.path_service import SUPPORTED_ALGORITHMS
from src.utils.validators import validate_learning_path


def make_resource(
    resource_id: str,
    title: str,
    duration_hours: int,
    difficulty: int,
    prerequisites: list[str] | None = None,
    topic: str = "AI Chatbots",
    description: str = "Learn AI chatbot and LLM skills.",
    resource_type: str = "course",
    utility: float = 10.0,
) -> Resource:
    return Resource(
        id=resource_id,
        title=title,
        topic=topic,
        duration_hours=duration_hours,
        difficulty=difficulty,
        prerequisites=prerequisites or [],
        description=description,
        type=resource_type,
        utility=utility,
    )


def make_student(available_hours: int = 20) -> Student:
    return Student(
        id="student-test",
        available_hours=available_hours,
        known_resources=[],
        preferred_difficulty=2,
        goal="Learn to build AI chatbots",
        preference="practical",
        target_topics=["AI Chatbots", "LLMs"],
        constraints=[],
    )


def make_resources() -> list[Resource]:
    return [
        make_resource(
            "python-basics",
            "Python Basics",
            duration_hours=5,
            difficulty=1,
            topic="Programming",
            description="Python programming basics for AI projects.",
            utility=10.0,
        ),
        make_resource(
            "nlp-basics",
            "NLP Basics",
            duration_hours=5,
            difficulty=2,
            prerequisites=["python-basics"],
            topic="Natural Language Processing",
            description="Natural language processing basics.",
            utility=12.0,
        ),
        make_resource(
            "llm-fundamentals",
            "LLM Fundamentals",
            duration_hours=5,
            difficulty=2,
            prerequisites=["nlp-basics"],
            topic="LLMs",
            description="Core concepts for large language models.",
            utility=15.0,
        ),
        make_resource(
            "chatbot-project",
            "Chatbot Project",
            duration_hours=6,
            difficulty=3,
            prerequisites=["llm-fundamentals"],
            topic="AI Chatbots",
            description="Build a practical AI chatbot project.",
            resource_type="project",
            utility=20.0,
        ),
        make_resource(
            "too-hard",
            "Too Hard",
            duration_hours=2,
            difficulty=5,
            topic="AI Chatbots",
            description="Advanced chatbot systems.",
            utility=100.0,
        ),
    ]


def test_ant_colony_returns_learning_path() -> None:
    path = build_ant_colony_learning_path(
        make_student(),
        make_resources(),
        num_ants=10,
        num_iterations=10,
    )

    assert isinstance(path, LearningPath)


def test_ant_colony_returns_valid_path() -> None:
    student = make_student(available_hours=5)
    path = build_ant_colony_learning_path(
        student,
        make_resources(),
        num_ants=10,
        num_iterations=10,
    )

    assert path.resources
    assert validate_learning_path(path, student)["is_valid"] is True


def test_ant_colony_respects_time_limit() -> None:
    student = make_student(available_hours=5)
    path = build_ant_colony_learning_path(
        student,
        make_resources(),
        num_ants=10,
        num_iterations=10,
    )

    assert path.total_duration <= student.available_hours


def test_ant_colony_does_not_duplicate_resources() -> None:
    path = build_ant_colony_learning_path(
        make_student(),
        make_resources(),
        num_ants=10,
        num_iterations=10,
    )

    assert len(path.resource_ids) == len(set(path.resource_ids))


def test_ant_colony_respects_prerequisites() -> None:
    student = make_student()
    path = build_ant_colony_learning_path(
        student,
        make_resources(),
        num_ants=10,
        num_iterations=10,
    )

    for resource in path.resources:
        for prerequisite_id in resource.prerequisites:
            assert prerequisite_id in path.resource_ids
            assert path.resource_ids.index(prerequisite_id) < path.resource_ids.index(
                resource.id
            )
    assert validate_learning_path(path, student)["is_valid"] is True


def test_ant_colony_respects_difficulty_limit() -> None:
    student = make_student()
    path = build_ant_colony_learning_path(
        student,
        make_resources(),
        num_ants=10,
        num_iterations=10,
    )

    assert "too-hard" not in path.resource_ids
    assert all(
        resource.difficulty <= student.preferred_difficulty + 1
        for resource in path.resources
    )


def test_ant_colony_is_reproducible_with_seed() -> None:
    student = make_student()
    resources = make_resources()

    first_path = build_ant_colony_learning_path(
        student,
        resources,
        num_ants=12,
        num_iterations=12,
        seed=42,
        use_precomputed_utility=True,
        min_utility_threshold=0.0,
    )
    second_path = build_ant_colony_learning_path(
        student,
        resources,
        num_ants=12,
        num_iterations=12,
        seed=42,
        use_precomputed_utility=True,
        min_utility_threshold=0.0,
    )

    assert first_path.resource_ids == second_path.resource_ids


def test_ant_colony_uses_precomputed_utility_without_rule_scoring(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Rule-based scoring should not be recalculated")

    monkeypatch.setattr(
        ant_colony,
        "compute_rule_based_utility",
        fail_if_called,
    )
    student = make_student(available_hours=5)
    resources = [
        make_resource(
            "high-utility",
            "High Utility",
            duration_hours=5,
            difficulty=1,
            utility=20.0,
        ),
        make_resource(
            "low-utility",
            "Low Utility",
            duration_hours=5,
            difficulty=1,
            utility=1.0,
        ),
    ]

    path = build_ant_colony_learning_path(
        student,
        resources,
        num_ants=8,
        num_iterations=8,
        use_precomputed_utility=True,
        min_utility_threshold=10.0,
    )

    assert path.resource_ids == ["high-utility"]
    assert path.total_utility == pytest.approx(20.0)


def test_supported_algorithms_contains_ant_colony() -> None:
    assert "ant_colony" in SUPPORTED_ALGORITHMS
