import json
from dataclasses import asdict, replace

from src.algorithms.greedy import compute_rule_based_utility
from src.llm.config import load_llm_config
from src.llm.prompts import RESOURCE_RELEVANCE_SYSTEM_PROMPT
from src.llm.schemas import ResourceRelevanceScore, ResourceRelevanceScores
from src.models.resource import Resource
from src.models.student import Student

MISSING_SCORE_REASON = "Missing from LLM response; assigned neutral score."


def rank_resources_rule_based(
    student: Student,
    resources: list[Resource],
) -> list[Resource]:
    known_resource_ids = set(student.known_resources)
    ranked = [
        replace(
            resource,
            utility=compute_rule_based_utility(resource, student, resources),
        )
        for resource in resources
        if resource.id not in known_resource_ids
    ]
    ranked.sort(key=_rule_based_sort_key)
    return ranked


def select_llm_candidates(
    student: Student,
    resources: list[Resource],
    top_k: int | None = None,
) -> list[Resource]:
    if top_k is None:
        top_k = load_llm_config().llm_candidate_top_k

    return rank_resources_rule_based(student, resources)[:top_k]


def score_resources_relevance_with_llm(
    student: Student,
    resources: list[Resource],
) -> dict[str, ResourceRelevanceScore]:
    config = load_llm_config()

    if config.provider != "gemini":
        raise RuntimeError(
            f"Gemini is the mandatory LLM provider, but LLM_PROVIDER is "
            f"{config.provider!r}."
        )

    if not config.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is required to score resource relevance. "
            "Create a .env file from .env.example and set your API key."
        )

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.gemini_api_key)
    payload = _build_relevance_payload(student, resources)

    try:
        response = client.models.generate_content(
            model=config.gemini_model,
            contents=json.dumps(payload, ensure_ascii=True),
            config=types.GenerateContentConfig(
                system_instruction=RESOURCE_RELEVANCE_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=ResourceRelevanceScores,
            ),
        )
        parsed = ResourceRelevanceScores(**json.loads(response.text))
    except Exception as exc:
        raise RuntimeError(
            "Gemini resource relevance scoring failed. Check your API key, "
            "model, and network connection. Original error: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    allowed_ids = {resource.id for resource in resources}
    scores_by_id: dict[str, ResourceRelevanceScore] = {}
    for score in parsed.scores:
        if score.resource_id in allowed_ids:
            scores_by_id[score.resource_id] = score

    for resource_id in allowed_ids - scores_by_id.keys():
        scores_by_id[resource_id] = ResourceRelevanceScore(
            resource_id=resource_id,
            relevance_score=5,
            reason=MISSING_SCORE_REASON,
        )

    return scores_by_id


def apply_llm_scores_to_resources(
    resources: list[Resource],
    llm_scores: dict[str, ResourceRelevanceScore],
    score_weight: float | None = None,
) -> list[Resource]:
    if score_weight is None:
        score_weight = load_llm_config().llm_score_weight

    scored_resources = []
    for resource in resources:
        score = llm_scores.get(resource.id)
        relevance_score = score.relevance_score if score is not None else 5
        final_utility = resource.utility + (score_weight * relevance_score)
        scored_resources.append(replace(resource, utility=final_utility))

    return scored_resources


def build_llm_scored_resources(
    student: Student,
    resources: list[Resource],
    top_k: int | None = None,
    score_weight: float | None = None,
) -> tuple[list[Resource], dict]:
    config = load_llm_config()
    resolved_top_k = top_k if top_k is not None else config.llm_candidate_top_k
    resolved_score_weight = (
        score_weight if score_weight is not None else config.llm_score_weight
    )

    rule_based_ranking = rank_resources_rule_based(student, resources)
    candidates = rule_based_ranking[:resolved_top_k]
    llm_scores = score_resources_relevance_with_llm(student, candidates)
    combined_resources = apply_llm_scores_to_resources(
        resources=candidates,
        llm_scores=llm_scores,
        score_weight=resolved_score_weight,
    )
    combined_resources.sort(key=_combined_sort_key)

    debug = build_scoring_debug(
        student=student,
        top_k=resolved_top_k,
        score_weight=resolved_score_weight,
        rule_based_ranking=rule_based_ranking,
        llm_scores=llm_scores,
        combined_resources=combined_resources,
    )

    return combined_resources, debug


def build_rule_based_scoring_debug(
    student: Student,
    resources: list[Resource],
    top_k: int | None = None,
    score_weight: float | None = None,
) -> dict:
    config = load_llm_config()
    resolved_top_k = top_k if top_k is not None else config.llm_candidate_top_k
    resolved_score_weight = (
        score_weight if score_weight is not None else config.llm_score_weight
    )
    rule_based_ranking = rank_resources_rule_based(student, resources)

    return {
        "student": asdict(student),
        "top_k": resolved_top_k,
        "score_weight": resolved_score_weight,
        "rule_based_ranking": _serialize_rule_based_ranking(rule_based_ranking),
        "llm_scores": [],
        "combined_ranking": [],
    }


def build_scoring_debug(
    student: Student,
    top_k: int,
    score_weight: float,
    rule_based_ranking: list[Resource],
    llm_scores: dict[str, ResourceRelevanceScore],
    combined_resources: list[Resource],
) -> dict:
    rule_based_by_id = {resource.id: resource for resource in rule_based_ranking}

    return {
        "student": asdict(student),
        "top_k": top_k,
        "score_weight": score_weight,
        "rule_based_ranking": _serialize_rule_based_ranking(rule_based_ranking),
        "llm_scores": [
            _model_dump(score)
            for score in sorted(llm_scores.values(), key=lambda item: item.resource_id)
        ],
        "combined_ranking": [
            _serialize_combined_resource(
                resource=resource,
                rank=rank,
                rule_based_utility=rule_based_by_id[resource.id].utility,
                llm_score=llm_scores.get(resource.id),
            )
            for rank, resource in enumerate(combined_resources, start=1)
        ],
    }


def _rule_based_sort_key(resource: Resource) -> tuple[float, float, int]:
    utility_per_hour = resource.utility / resource.duration_hours
    return (-resource.utility, -utility_per_hour, resource.duration_hours)


def _combined_sort_key(resource: Resource) -> tuple[float, float, int]:
    utility_per_hour = resource.utility / resource.duration_hours
    return (-resource.utility, -utility_per_hour, resource.duration_hours)


def _build_relevance_payload(student: Student, resources: list[Resource]) -> dict:
    return {
        "student": {
            "goal": student.goal,
            "available_hours": student.available_hours,
            "preferred_difficulty": student.preferred_difficulty,
            "preference": student.preference,
            "target_topics": student.target_topics,
            "constraints": student.constraints,
        },
        "resources": [
            {
                "id": resource.id,
                "title": resource.title,
                "topic": resource.topic,
                "duration_hours": resource.duration_hours,
                "difficulty": resource.difficulty,
                "description": resource.description,
                "type": resource.type,
                "rule_based_utility": resource.utility,
            }
            for resource in resources
        ],
    }


def _serialize_rule_based_ranking(resources: list[Resource]) -> list[dict]:
    return [
        {
            "rank": rank,
            "id": resource.id,
            "title": resource.title,
            "topic": resource.topic,
            "duration_hours": resource.duration_hours,
            "utility": resource.utility,
        }
        for rank, resource in enumerate(resources, start=1)
    ]


def _serialize_combined_resource(
    resource: Resource,
    rank: int,
    rule_based_utility: float,
    llm_score: ResourceRelevanceScore | None,
) -> dict:
    return {
        "rank": rank,
        "id": resource.id,
        "title": resource.title,
        "topic": resource.topic,
        "duration_hours": resource.duration_hours,
        "rule_based_utility": rule_based_utility,
        "llm_relevance_score": llm_score.relevance_score if llm_score else 5,
        "final_utility": resource.utility,
    }


def _model_dump(model) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()
