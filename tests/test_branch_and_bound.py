from dataclasses import replace

import pytest

from src.algorithms import branch_and_bound
from src.algorithms.branch_and_bound import build_branch_and_bound_learning_path
from src.algorithms.greedy import build_greedy_learning_path
from src.models.resource import Resource
from src.models.student import Student
from src.services import path_service
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


def test_branch_and_bound_returns_valid_path() -> None:
    student = make_student()
    resources = [
        make_resource("chatbot-basics"),
        make_resource("chatbot-project", prerequisites=["chatbot-basics"]),
    ]

    path = build_branch_and_bound_learning_path(student, resources)

    assert path.resources
    assert validate_learning_path(path, student)["is_valid"] is True


def test_branch_and_bound_respects_time_limit() -> None:
    student = make_student(available_hours=3)
    resources = [
        make_resource("short-chatbot-intro", duration_hours=2),
        make_resource("long-chatbot-project", duration_hours=5),
    ]

    path = build_branch_and_bound_learning_path(student, resources)

    assert path.total_duration <= student.available_hours
    assert validate_learning_path(path, student)["is_valid"] is True


def test_branch_and_bound_orders_prerequisites_before_dependents() -> None:
    student = make_student()
    resources = [
        make_resource("chatbot-project", prerequisites=["chatbot-basics"]),
        make_resource("chatbot-basics"),
    ]

    path = build_branch_and_bound_learning_path(student, resources)

    assert path.resource_ids.index("chatbot-basics") < path.resource_ids.index(
        "chatbot-project"
    )
    assert validate_learning_path(path, student)["is_valid"] is True


def test_branch_and_bound_does_not_include_duplicate_resources() -> None:
    student = make_student()
    resources = [
        make_resource("python-basics", topic="Programming"),
        make_resource("chatbot-api", prerequisites=["python-basics"]),
        make_resource("chatbot-ui", prerequisites=["python-basics"]),
    ]

    path = build_branch_and_bound_learning_path(student, resources)

    assert len(path.resource_ids) == len(set(path.resource_ids))
    assert validate_learning_path(path, student)["is_valid"] is True


def test_branch_and_bound_does_not_include_known_resources() -> None:
    student = make_student(known_resources=["python-basics"])
    resources = [
        make_resource("python-basics", topic="Programming"),
        make_resource("chatbot-api", prerequisites=["python-basics"]),
    ]

    path = build_branch_and_bound_learning_path(student, resources)

    assert "python-basics" not in path.resource_ids
    assert validate_learning_path(path, student)["is_valid"] is True


def test_branch_and_bound_utility_is_at_least_greedy_on_small_instance() -> None:
    student = make_student(available_hours=6)
    resources = [
        make_resource("dense-but-blocking", duration_hours=4, utility=10.0),
        make_resource("first-half", duration_hours=3, utility=7.0),
        make_resource("second-half", duration_hours=3, utility=7.0),
    ]

    greedy_path = build_greedy_learning_path(
        student,
        resources,
        use_precomputed_utility=True,
        min_utility_threshold=0.0,
    )
    branch_and_bound_path = build_branch_and_bound_learning_path(
        student,
        resources,
        use_precomputed_utility=True,
    )

    assert branch_and_bound_path.total_utility >= greedy_path.total_utility
    assert validate_learning_path(branch_and_bound_path, student)["is_valid"] is True


def test_path_service_accepts_branch_and_bound() -> None:
    student = make_student()
    resources = [make_resource("chatbot-basics")]

    result = path_service.generate_path_for_student_object(
        student=student,
        algorithm="branch_and_bound",
        use_llm=False,
        resources=resources,
    )

    assert result["algorithm"] == "branch_and_bound"
    assert result["validation"]["is_valid"] is True


def test_path_service_rejects_invalid_algorithm() -> None:
    with pytest.raises(ValueError, match="Unsupported algorithm"):
        path_service.generate_path_for_student_object(
            student=make_student(),
            algorithm="unknown",
            resources=[],
        )


def test_branch_and_bound_without_llm_does_not_call_llm(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("LLM scoring should not be called")

    monkeypatch.setattr(path_service, "build_llm_scored_resources", fail_if_called)

    result = path_service.generate_path_for_student_object(
        student=make_student(),
        algorithm="branch_and_bound",
        use_llm=False,
        resources=[make_resource("chatbot-basics")],
    )

    assert result["llm_debug"] is None
    assert result["path"]


def test_branch_and_bound_uses_precomputed_utility_without_rule_scoring(
    monkeypatch,
) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Rule-based scoring should not be recalculated")

    monkeypatch.setattr(
        branch_and_bound,
        "compute_rule_based_utility",
        fail_if_called,
    )
    resources = [
        make_resource("high-utility", duration_hours=2, utility=12.0),
        make_resource("low-utility", duration_hours=2, utility=1.0),
    ]

    path = build_branch_and_bound_learning_path(
        make_student(available_hours=2),
        resources,
        use_precomputed_utility=True,
    )

    assert path.resource_ids == ["high-utility"]
    assert path.total_utility == pytest.approx(12.0)


def test_branch_and_bound_uses_upper_bound(monkeypatch) -> None:
    calls = []
    original_upper_bound = branch_and_bound._fractional_utility_upper_bound

    def tracking_upper_bound(*args, **kwargs):
        calls.append((args, kwargs))
        return original_upper_bound(*args, **kwargs)

    monkeypatch.setattr(
        branch_and_bound,
        "_fractional_utility_upper_bound",
        tracking_upper_bound,
    )
    student = make_student(available_hours=4)
    resources = [
        make_resource("chatbot-basics", duration_hours=2),
        make_resource("chatbot-project", duration_hours=2),
    ]

    path = build_branch_and_bound_learning_path(student, resources)

    assert calls
    assert path.resources
    assert validate_learning_path(path, student)["is_valid"] is True


def test_path_service_with_llm_scores_once_and_uses_scored_resources(
    monkeypatch,
) -> None:
    student = make_student(available_hours=2)
    resources = [
        make_resource("a", duration_hours=2, utility=0.0),
        make_resource("b", duration_hours=2, utility=0.0),
    ]
    calls = []
    debug = {
        "utility_threshold": 0.0,
        "llm_scores": [],
        "combined_ranking": [],
    }

    def fake_build_llm_scored_resources(
        student,
        resources,
        top_k=None,
        score_weight=None,
    ):
        calls.append((student, resources, top_k, score_weight))
        return [
            replace(resources[0], utility=3.0),
            replace(resources[1], utility=15.0),
        ], debug

    monkeypatch.setattr(
        path_service,
        "build_llm_scored_resources",
        fake_build_llm_scored_resources,
    )

    result = path_service.generate_path_for_student_object(
        student=student,
        algorithm="branch_and_bound",
        use_llm=True,
        resources=resources,
    )

    assert len(calls) == 1
    assert [resource.id for resource in result["path"]] == ["b"]
    assert result["path"][0].utility == pytest.approx(15.0)
