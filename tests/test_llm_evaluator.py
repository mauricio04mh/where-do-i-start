from dataclasses import replace

import pytest

from src.api.routes.paths import debug_scoring
from src.api.schemas import GeneratePathRequest
from src.llm import evaluator
from src.llm.schemas import ResourceRelevanceScore
from src.models.resource import Resource
from src.models.student import Student
from src.services import path_service


def make_resource(
    resource_id: str,
    duration_hours: int = 5,
    utility: float = 0.0,
) -> Resource:
    return Resource(
        id=resource_id,
        title=f"Resource {resource_id}",
        topic="LLMs",
        duration_hours=duration_hours,
        difficulty=2,
        prerequisites=[],
        description="Learn with focused examples.",
        type="course",
        utility=utility,
    )


def make_student(known_resources: list[str] | None = None) -> Student:
    return Student(
        id="student-test",
        goal="Build LLM apps",
        available_hours=20,
        known_resources=known_resources or [],
        preferred_difficulty=2,
        preference="balanced",
        target_topics=["LLMs"],
        constraints=[],
    )


def test_rank_resources_rule_based_excludes_known_and_orders(monkeypatch) -> None:
    student = make_student(known_resources=["known"])
    resources = [
        make_resource("low", duration_hours=2),
        make_resource("known", duration_hours=1),
        make_resource("top-short", duration_hours=2),
        make_resource("top-long", duration_hours=4),
    ]
    utilities = {
        "low": 4.0,
        "known": 99.0,
        "top-short": 10.0,
        "top-long": 10.0,
    }

    monkeypatch.setattr(
        evaluator,
        "compute_rule_based_utility",
        lambda resource, student, resources: utilities[resource.id],
    )

    ranked = evaluator.rank_resources_rule_based(student, resources)

    assert [resource.id for resource in ranked] == ["top-short", "top-long", "low"]
    assert [resource.utility for resource in ranked] == [10.0, 10.0, 4.0]


def test_select_llm_candidates_respects_top_k(monkeypatch) -> None:
    student = make_student()
    resources = [make_resource("a"), make_resource("b"), make_resource("c")]
    monkeypatch.setattr(
        evaluator,
        "rank_resources_rule_based",
        lambda student, resources: resources,
    )

    candidates = evaluator.select_llm_candidates(student, resources, top_k=2)

    assert [resource.id for resource in candidates] == ["a", "b"]


def test_apply_llm_scores_to_resources_combines_utility_and_uses_neutral_missing() -> None:
    resources = [
        make_resource("a", utility=10.0),
        make_resource("b", utility=3.0),
    ]
    scores = {
        "a": ResourceRelevanceScore(
            resource_id="a",
            relevance_score=8,
            reason="Directly relevant.",
        )
    }

    scored = evaluator.apply_llm_scores_to_resources(
        resources=resources,
        llm_scores=scores,
        score_weight=2.0,
    )

    assert scored[0].utility == pytest.approx(26.0)
    assert scored[1].utility == pytest.approx(13.0)
    assert resources[0].utility == pytest.approx(10.0)


def test_generate_path_for_student_object_without_llm_still_works() -> None:
    student = make_student()
    resources = [make_resource("a"), make_resource("b")]

    result = path_service.generate_path_for_student_object(
        student=student,
        algorithm="greedy",
        use_llm=False,
        resources=resources,
    )

    assert result["student"] == student
    assert result["algorithm"] == "greedy"
    assert isinstance(result["path"], list)
    assert result["llm_debug"] is None


def test_generate_path_for_student_object_with_llm_uses_mocked_batch_scoring(
    monkeypatch,
) -> None:
    student = make_student()
    resources = [make_resource("a"), make_resource("b")]
    debug = {"top_k": 2, "llm_scores": []}

    def fake_build_llm_scored_resources(student, resources, top_k=None, score_weight=None):
        return [replace(resource, utility=10.0) for resource in resources], debug

    monkeypatch.setattr(
        path_service,
        "build_llm_scored_resources",
        fake_build_llm_scored_resources,
    )

    result = path_service.generate_path_for_student_object(
        student=student,
        algorithm="greedy",
        use_llm=True,
        resources=resources,
    )

    assert result["llm_debug"] == debug
    assert result["path"]
    assert all(resource.utility == pytest.approx(10.0) for resource in result["path"])


def test_debug_scoring_route_without_llm_returns_rule_based_ranking() -> None:
    result = debug_scoring(
        GeneratePathRequest(
            student_id="student-chatbot-beginner",
            algorithm="greedy",
            use_llm=False,
        )
    )

    assert result["student"]["id"] == "student-chatbot-beginner"
    assert result["rule_based_ranking"]
    assert result["llm_scores"] == []
    assert result["combined_ranking"] == []
