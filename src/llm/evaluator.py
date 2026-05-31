import json
from dataclasses import asdict, replace

import requests

from src.algorithms.greedy import compute_rule_based_utility, resource_matches_student_goal
from src.llm.config import LLMConfig, load_llm_config
from src.llm.prompts import RESOURCE_RELEVANCE_SYSTEM_PROMPT
from src.llm.schemas import ResourceRelevanceScore, ResourceRelevanceScores
from src.models.resource import Resource
from src.models.student import Student

MISSING_SCORE_REASON = "Missing from LLM response; assigned neutral score."
NEUTRAL_SCORE_REASON = "LLM_PROVIDER=none; assigned neutral score."
PARSE_FAILURE_REASON = "Could not parse LLM response; assigned neutral score."
OLLAMA_UNREACHABLE_MESSAGE = (
    "Ollama is not running or is unreachable at {base_url}. "
    "Start it with `docker compose up -d ollama`."
)
OLLAMA_MODEL_MISSING_MESSAGE = (
    "Ollama model '{model}' is not available. Pull it with "
    "`docker exec -it where-do-i-start-ollama ollama pull {model}`."
)


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

    if config.provider == "gemini":
        return score_resources_relevance_with_gemini(student, resources, config)

    if config.provider == "ollama":
        return score_resources_relevance_with_ollama(student, resources, config)

    if config.provider == "none":
        return build_neutral_resource_scores(resources)

    raise RuntimeError(f"Unsupported LLM_PROVIDER: {config.provider}")


def score_resources_relevance_with_gemini(
    student: Student,
    resources: list[Resource],
    config: LLMConfig,
) -> dict[str, ResourceRelevanceScore]:
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

    return _build_scores_by_resource_id(parsed.scores, resources)


def score_resources_relevance_with_ollama(
    student: Student,
    resources: list[Resource],
    config: LLMConfig,
) -> dict[str, ResourceRelevanceScore]:
    payload = {
        "model": config.ollama_model,
        "messages": [
            {
                "role": "system",
                "content": RESOURCE_RELEVANCE_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": json.dumps(
                    _build_relevance_payload(student, resources),
                    ensure_ascii=True,
                ),
            },
        ],
        "stream": False,
        "format": "json",
    }

    response = _post_ollama_chat(payload, config)
    if response.status_code != 200 and _looks_like_format_rejection(response.text):
        fallback_payload = dict(payload)
        fallback_payload.pop("format", None)
        response = _post_ollama_chat(fallback_payload, config)

    if response.status_code != 200:
        _raise_ollama_http_error(response, config)

    try:
        response_json = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Ollama returned a non-JSON HTTP response. Body: "
            f"{_short_fragment(response.text)}"
        ) from exc

    if "error" in response_json and _looks_like_missing_ollama_model(
        str(response_json["error"])
    ):
        raise RuntimeError(
            OLLAMA_MODEL_MISSING_MESSAGE.format(model=config.ollama_model)
        )

    content = response_json.get("message", {}).get("content")
    if not isinstance(content, str):
        raise RuntimeError(
            "Ollama response did not include message.content. Body: "
            f"{_short_fragment(response.text)}"
        )

    try:
        parsed = parse_llm_json_response(content)
        raw_scores = _extract_score_items(parsed)
        if not isinstance(raw_scores, list):
            return build_neutral_resource_scores(
                resources,
                reason=PARSE_FAILURE_REASON,
            )
    except RuntimeError:
        return build_neutral_resource_scores(
            resources,
            reason=PARSE_FAILURE_REASON,
        )

    return _build_scores_by_resource_id(
        [_coerce_relevance_score(item) for item in raw_scores],
        resources,
    )


def _extract_score_items(parsed: dict) -> list | None:
    scores = parsed.get("scores")
    if isinstance(scores, list):
        return scores

    resources = parsed.get("resources")
    if isinstance(resources, list):
        return resources

    return None


def build_neutral_resource_scores(
    resources: list[Resource],
    reason: str = NEUTRAL_SCORE_REASON,
) -> dict[str, ResourceRelevanceScore]:
    return {
        resource.id: ResourceRelevanceScore(
            resource_id=resource.id,
            relevance_score=5,
            reason=reason,
        )
        for resource in resources
    }


def parse_llm_json_response(text: str) -> dict:
    candidates = [
        text,
        _strip_markdown_json_fence(text),
        _extract_first_json_object(text),
    ]

    for candidate in candidates:
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise RuntimeError(
        "Could not parse LLM response as JSON. Response fragment: "
        f"{_short_fragment(text)}"
    )


def _post_ollama_chat(payload: dict, config: LLMConfig) -> requests.Response:
    try:
        return requests.post(
            f"{config.ollama_base_url}/api/chat",
            json=payload,
            timeout=config.ollama_timeout_seconds,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            OLLAMA_UNREACHABLE_MESSAGE.format(base_url=config.ollama_base_url)
        ) from exc


def _raise_ollama_http_error(response: requests.Response, config: LLMConfig) -> None:
    body = response.text
    if _looks_like_missing_ollama_model(body):
        raise RuntimeError(
            OLLAMA_MODEL_MISSING_MESSAGE.format(model=config.ollama_model)
        )

    raise RuntimeError(
        "Ollama resource relevance scoring failed with HTTP status "
        f"{response.status_code}. Body: {_short_fragment(body)}"
    )


def _looks_like_format_rejection(body: str) -> bool:
    lowered = body.lower()
    return "format" in lowered and (
        "invalid" in lowered
        or "unsupported" in lowered
        or "unrecognized" in lowered
        or "not support" in lowered
        or "json" in lowered
    )


def _looks_like_missing_ollama_model(body: str) -> bool:
    lowered = body.lower()
    return "model" in lowered and (
        "not found" in lowered
        or "not available" in lowered
        or "pull" in lowered
        or "try pulling" in lowered
    )


def _strip_markdown_json_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        first_line = lines[0].strip().lower()
        if first_line in {"```", "```json"}:
            return "\n".join(lines[1:-1]).strip()

    return stripped


def _extract_first_json_object(text: str) -> str:
    start = -1
    depth = 0
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if start == -1:
            if char == "{":
                start = index
                depth = 1
            continue

        if escaped:
            escaped = False
            continue

        if char == "\\" and in_string:
            escaped = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return ""


def _coerce_relevance_score(item: object) -> ResourceRelevanceScore:
    if not isinstance(item, dict):
        return ResourceRelevanceScore(
            resource_id="",
            relevance_score=5,
            reason="Invalid LLM score item; assigned neutral score.",
        )

    resource_id = str(item.get("resource_id") or item.get("id") or "")
    reason = item.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        reason = "No reason provided by LLM."

    try:
        relevance_score = int(item.get("relevance_score", item.get("score", 5)))
    except (TypeError, ValueError):
        relevance_score = 5

    relevance_score = min(10, max(1, relevance_score))

    return ResourceRelevanceScore(
        resource_id=resource_id,
        relevance_score=relevance_score,
        reason=reason,
    )


def _build_scores_by_resource_id(
    scores: list[ResourceRelevanceScore],
    resources: list[Resource],
) -> dict[str, ResourceRelevanceScore]:
    allowed_ids = {resource.id for resource in resources}
    scores_by_id: dict[str, ResourceRelevanceScore] = {}
    for score in scores:
        if score.resource_id in allowed_ids:
            scores_by_id[score.resource_id] = score

    for resource_id in allowed_ids - scores_by_id.keys():
        scores_by_id[resource_id] = ResourceRelevanceScore(
            resource_id=resource_id,
            relevance_score=5,
            reason=MISSING_SCORE_REASON,
        )

    return scores_by_id


def _short_fragment(text: str, max_length: int = 300) -> str:
    one_line = " ".join(text.split())
    if len(one_line) <= max_length:
        return one_line

    return f"{one_line[:max_length]}..."


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
        final_utility = resource.utility + (score_weight * (relevance_score - 5))
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
    resolved_utility_threshold = config.llm_min_utility_threshold

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
        config=config,
        top_k=resolved_top_k,
        score_weight=resolved_score_weight,
        rule_based_ranking=rule_based_ranking,
        llm_scores=llm_scores,
        combined_resources=combined_resources,
        utility_threshold=resolved_utility_threshold,
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
    resolved_utility_threshold = config.llm_min_utility_threshold
    rule_based_ranking = rank_resources_rule_based(student, resources)

    return {
        "student": asdict(student),
        "provider": config.provider,
        "model": _model_name_for_provider(config),
        "top_k": resolved_top_k,
        "score_weight": resolved_score_weight,
        "utility_threshold": resolved_utility_threshold,
        "rule_based_ranking": _serialize_rule_based_ranking(rule_based_ranking),
        "llm_scores": [],
        "combined_ranking": [],
        "inconsistency_metrics": _empty_inconsistency_metrics(),
    }


def build_scoring_debug(
    student: Student,
    config: LLMConfig,
    top_k: int,
    score_weight: float,
    rule_based_ranking: list[Resource],
    llm_scores: dict[str, ResourceRelevanceScore],
    combined_resources: list[Resource],
    utility_threshold: float,
) -> dict:
    rule_based_by_id = {resource.id: resource for resource in rule_based_ranking}

    return {
        "student": asdict(student),
        "provider": config.provider,
        "model": _model_name_for_provider(config),
        "top_k": top_k,
        "score_weight": score_weight,
        "utility_threshold": utility_threshold,
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
                score_weight=score_weight,
                utility_threshold=utility_threshold,
            )
            for rank, resource in enumerate(combined_resources, start=1)
        ],
        "inconsistency_metrics": build_llm_inconsistency_metrics(
            student=student,
            resources=combined_resources,
            llm_scores=llm_scores,
            selected_resources=[],
        ),
    }


def update_llm_debug_with_selected_resources(
    llm_debug: dict,
    student: Student,
    resources: list[Resource],
    selected_resources: list[Resource],
) -> dict:
    selected_ids = {resource.id for resource in selected_resources}
    for item in llm_debug.get("combined_ranking", []):
        item["selected"] = item["id"] in selected_ids

    llm_scores = {
        item["resource_id"]: ResourceRelevanceScore(
            resource_id=item["resource_id"],
            relevance_score=item["relevance_score"],
            reason=item["reason"],
        )
        for item in llm_debug.get("llm_scores", [])
    }
    llm_debug["inconsistency_metrics"] = build_llm_inconsistency_metrics(
        student=student,
        resources=resources,
        llm_scores=llm_scores,
        selected_resources=selected_resources,
    )
    return llm_debug


def build_llm_inconsistency_metrics(
    student: Student,
    resources: list[Resource],
    llm_scores: dict[str, ResourceRelevanceScore],
    selected_resources: list[Resource] | None = None,
) -> dict:
    resources_by_id = {resource.id: resource for resource in resources}
    selected_resources = selected_resources or []
    selected_scores = [
        llm_scores[resource.id].relevance_score
        for resource in selected_resources
        if resource.id in llm_scores
    ]

    high_off_topic_count = 0
    for resource_id, score in llm_scores.items():
        resource = resources_by_id.get(resource_id)
        if resource is None:
            continue
        if score.relevance_score >= 8 and not resource_matches_student_goal(
            resource,
            student,
        ):
            high_off_topic_count += 1

    selected_avg_llm_score = (
        sum(selected_scores) / len(selected_scores) if selected_scores else None
    )

    return {
        "missing_llm_score_count": sum(
            1 for score in llm_scores.values() if score.reason == MISSING_SCORE_REASON
        ),
        "low_relevance_selected_count": sum(
            1 for score in selected_scores if score <= 3
        ),
        "high_llm_score_off_topic_count": high_off_topic_count,
        "selected_avg_llm_score": selected_avg_llm_score,
    }


def _empty_inconsistency_metrics() -> dict:
    return {
        "missing_llm_score_count": 0,
        "low_relevance_selected_count": 0,
        "high_llm_score_off_topic_count": 0,
        "selected_avg_llm_score": None,
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
    score_weight: float,
    utility_threshold: float,
) -> dict:
    relevance_score = llm_score.relevance_score if llm_score else 5
    return {
        "rank": rank,
        "id": resource.id,
        "title": resource.title,
        "topic": resource.topic,
        "duration_hours": resource.duration_hours,
        "rule_based_utility": rule_based_utility,
        "llm_relevance_score": relevance_score,
        "llm_utility_adjustment": score_weight * (relevance_score - 5),
        "final_utility": resource.utility,
        "passes_utility_threshold": resource.utility >= utility_threshold,
        "selected": False,
    }


def _model_name_for_provider(config: LLMConfig) -> str:
    if config.provider == "gemini":
        return config.gemini_model
    if config.provider == "ollama":
        return config.ollama_model

    return ""


def _model_dump(model) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()
