from dataclasses import replace
import json as json_module

import pytest
import requests

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


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text or json_module.dumps(payload or {})

    def json(self) -> dict:
        if self._payload is None:
            raise ValueError("No JSON body")
        return self._payload


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


def test_llm_provider_none_returns_neutral_scores(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "none")
    resources = [make_resource("a"), make_resource("b")]

    scores = evaluator.score_resources_relevance_with_llm(make_student(), resources)

    assert set(scores) == {"a", "b"}
    assert all(score.relevance_score == 5 for score in scores.values())
    assert all(
        score.reason == "LLM_PROVIDER=none; assigned neutral score."
        for score in scores.values()
    )


def test_parse_llm_json_response_parses_clean_json() -> None:
    parsed = evaluator.parse_llm_json_response(
        '{"scores": [{"resource_id": "a", "relevance_score": 8, "reason": "fit"}]}'
    )

    assert parsed["scores"][0]["resource_id"] == "a"


def test_parse_llm_json_response_parses_markdown_fence() -> None:
    parsed = evaluator.parse_llm_json_response(
        '```json\n{"scores": [{"resource_id": "a", "relevance_score": 8, "reason": "fit"}]}\n```'
    )

    assert parsed["scores"][0]["relevance_score"] == 8


def test_ollama_scoring_uses_single_batch_call_and_normalizes_scores(
    monkeypatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "120")
    student = make_student()
    resources = [make_resource("a"), make_resource("b"), make_resource("c")]
    calls = []

    def fake_post(url, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse(
            200,
            {
                "message": {
                    "content": json_module.dumps(
                        {
                            "scores": [
                                {
                                    "resource_id": "a",
                                    "relevance_score": 12,
                                    "reason": "Very relevant.",
                                },
                                {
                                    "resource_id": "b",
                                    "relevance_score": "bad",
                                    "reason": "Invalid score.",
                                },
                                {
                                    "resource_id": "unknown",
                                    "relevance_score": 9,
                                    "reason": "Unknown id.",
                                },
                            ]
                        }
                    )
                }
            },
        )

    monkeypatch.setattr(evaluator.requests, "post", fake_post)

    scores = evaluator.score_resources_relevance_with_llm(student, resources)

    assert len(calls) == 1
    assert calls[0]["url"] == "http://localhost:11434/api/chat"
    assert calls[0]["json"]["model"] == "llama3.2:3b"
    assert calls[0]["json"]["format"] == "json"
    assert calls[0]["timeout"] == 120
    assert set(scores) == {"a", "b", "c"}
    assert scores["a"].relevance_score == 10
    assert scores["b"].relevance_score == 5
    assert scores["c"].relevance_score == 5
    assert scores["c"].reason == "Missing from LLM response; assigned neutral score."


def test_ollama_scoring_accepts_resources_id_score_shape(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    resources = [
        make_resource("fastapi-basics"),
        make_resource("authentication-basics"),
        make_resource("prompt-engineering"),
    ]

    def fake_post(url, json, timeout):
        return FakeResponse(
            200,
            {
                "message": {
                    "content": json_module.dumps(
                        {
                            "resources": [
                                {"id": "fastapi-basics", "score": 7},
                                {"id": "authentication-basics", "score": 6},
                                {"id": "prompt-engineering", "score": 10},
                            ]
                        }
                    )
                }
            },
        )

    monkeypatch.setattr(evaluator.requests, "post", fake_post)

    scores = evaluator.score_resources_relevance_with_llm(make_student(), resources)

    assert scores["fastapi-basics"].relevance_score == 7
    assert scores["authentication-basics"].relevance_score == 6
    assert scores["prompt-engineering"].relevance_score == 10


def test_ollama_connection_error_has_clear_runtime_error(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def fake_post(url, json, timeout):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(evaluator.requests, "post", fake_post)

    with pytest.raises(RuntimeError) as exc_info:
        evaluator.score_resources_relevance_with_llm(make_student(), [make_resource("a")])

    assert "Ollama is not running or is unreachable at http://localhost:11434" in str(
        exc_info.value
    )
    assert "docker compose up -d ollama" in str(exc_info.value)


def test_ollama_missing_model_error_recommends_pull_command(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")

    def fake_post(url, json, timeout):
        return FakeResponse(404, {"error": "model 'llama3.2:3b' not found"})

    monkeypatch.setattr(evaluator.requests, "post", fake_post)

    with pytest.raises(RuntimeError) as exc_info:
        evaluator.score_resources_relevance_with_llm(make_student(), [make_resource("a")])

    assert "Ollama model 'llama3.2:3b' is not available" in str(exc_info.value)
    assert (
        "docker exec -it where-do-i-start-ollama ollama pull llama3.2:3b"
        in str(exc_info.value)
    )


def test_llm_debug_includes_provider_and_model(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "none")
    resources = [make_resource("a"), make_resource("b")]

    _, debug = evaluator.build_llm_scored_resources(
        student=make_student(),
        resources=resources,
        top_k=2,
    )

    assert debug["provider"] == "none"
    assert debug["model"] == ""


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
