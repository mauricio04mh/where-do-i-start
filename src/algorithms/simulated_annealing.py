import math
import random
from dataclasses import replace

from src.algorithms.greedy import (
    build_greedy_learning_path,
    compute_rule_based_utility,
)
from src.evaluation.metrics import compute_goal_coverage
from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.utils.validators import validate_learning_path

MIN_ROOT_UTILITY = 0.0


def build_simulated_annealing_learning_path(
    student: Student,
    resources: list[Resource],
    max_iterations: int = 1000,
    initial_temperature: float = 10.0,
    cooling_rate: float = 0.995,
    min_temperature: float = 0.01,
    seed: int | None = None,
    use_precomputed_utility: bool = False,
    min_utility_threshold: float | None = None,
) -> LearningPath:
    root_utility_threshold = (
        MIN_ROOT_UTILITY if min_utility_threshold is None else min_utility_threshold
    )
    rng = random.Random(42 if seed is None else seed)

    if use_precomputed_utility:
        utility_resources = [replace(resource) for resource in resources]
    else:
        utility_resources = [
            replace(
                resource,
                utility=compute_rule_based_utility(resource, student, resources),
            )
            for resource in resources
        ]

    initial_path = build_greedy_learning_path(
        student,
        utility_resources,
        use_precomputed_utility=True,
        min_utility_threshold=min_utility_threshold,
    )
    if validate_learning_path(initial_path, student)["is_valid"]:
        current_path = _copy_path(initial_path)
        best_path = _copy_path(initial_path)
    else:
        current_path = LearningPath(resources=[])
        best_path = LearningPath(resources=[])

    current_score = _score_path(current_path, student)
    best_score = _score_path(best_path, student)
    temperature = initial_temperature

    for _ in range(max(0, max_iterations)):
        if temperature < min_temperature:
            break

        neighbor = _generate_neighbor(
            current_path=current_path,
            student=student,
            resources=utility_resources,
            rng=rng,
            min_utility_threshold=root_utility_threshold,
        )
        neighbor_score = _score_path(neighbor, student)

        if _should_accept(
            current_score=current_score,
            neighbor_score=neighbor_score,
            temperature=temperature,
            rng=rng,
        ):
            current_path = neighbor
            current_score = neighbor_score

            if (
                validate_learning_path(current_path, student)["is_valid"]
                and current_score > best_score
            ):
                best_path = _copy_path(current_path)
                best_score = current_score

        temperature *= cooling_rate

    if validate_learning_path(best_path, student)["is_valid"]:
        return best_path

    empty_path = LearningPath(resources=[])
    if validate_learning_path(empty_path, student)["is_valid"]:
        return empty_path

    return LearningPath(resources=[])


def _score_path(path: LearningPath, student: Student) -> float:
    validation = validate_learning_path(path, student)
    time_usage_ratio = (
        path.total_duration / student.available_hours
        if student.available_hours > 0
        else 0.0
    )

    score = path.total_utility
    score += 10.0 * compute_goal_coverage(path, student)
    score += 2.0 * time_usage_ratio

    if not validation["is_valid"]:
        score -= 1000.0 * len(validation["violations"])

    return score


def _generate_neighbor(
    current_path: LearningPath,
    student: Student,
    resources: list[Resource],
    rng: random.Random,
    min_utility_threshold: float,
) -> LearningPath:
    resources_by_id = _resource_map(resources)
    current_resources = list(current_path.resources)
    operations = ["add"]
    if current_resources:
        operations.extend(["remove", "replace"])

    for _ in range(50):
        operation = rng.choice(operations)

        if operation == "add":
            neighbor = _try_add_resource(
                selected=current_resources,
                student=student,
                resources=resources,
                resources_by_id=resources_by_id,
                rng=rng,
                min_utility_threshold=min_utility_threshold,
            )
        elif operation == "remove":
            neighbor = _try_remove_resource(
                selected=current_resources,
                student=student,
                rng=rng,
            )
        else:
            neighbor = _try_replace_resource(
                selected=current_resources,
                student=student,
                resources=resources,
                resources_by_id=resources_by_id,
                rng=rng,
                min_utility_threshold=min_utility_threshold,
            )

        if neighbor is None or neighbor.resource_ids == current_path.resource_ids:
            continue
        if validate_learning_path(neighbor, student)["is_valid"]:
            return neighbor

    return _copy_path(current_path)


def _try_add_resource(
    selected: list[Resource],
    student: Student,
    resources: list[Resource],
    resources_by_id: dict[str, Resource],
    rng: random.Random,
    min_utility_threshold: float,
) -> LearningPath | None:
    selected_ids = {resource.id for resource in selected}
    candidate = _choose_candidate(
        resources=resources,
        unavailable_ids=set(student.known_resources) | selected_ids,
        student=student,
        rng=rng,
        min_utility_threshold=min_utility_threshold,
    )
    if candidate is None:
        return None

    additions = _resolve_missing_prerequisites(
        resource=candidate,
        resources_by_id=resources_by_id,
        available_ids=set(student.known_resources) | selected_ids,
        max_allowed_difficulty=student.preferred_difficulty + 1,
        visiting=set(),
    )
    if additions is None:
        return None

    return _validated_path(
        resources=_append_unique(
            selected=selected,
            additions=additions,
            known_resource_ids=set(student.known_resources),
        ),
        student=student,
    )


def _try_remove_resource(
    selected: list[Resource],
    student: Student,
    rng: random.Random,
) -> LearningPath | None:
    if not selected:
        return None

    resource = rng.choice(selected)
    return _validated_path(
        resources=_remove_with_dependents(
            selected=selected,
            resource_id=resource.id,
            known_resource_ids=set(student.known_resources),
        ),
        student=student,
    )


def _try_replace_resource(
    selected: list[Resource],
    student: Student,
    resources: list[Resource],
    resources_by_id: dict[str, Resource],
    rng: random.Random,
    min_utility_threshold: float,
) -> LearningPath | None:
    if not selected:
        return None

    removed_resource = rng.choice(selected)
    reduced = _remove_with_dependents(
        selected=selected,
        resource_id=removed_resource.id,
        known_resource_ids=set(student.known_resources),
    )
    reduced_ids = {resource.id for resource in reduced}
    candidate = _choose_candidate(
        resources=resources,
        unavailable_ids=set(student.known_resources) | reduced_ids,
        student=student,
        rng=rng,
        min_utility_threshold=min_utility_threshold,
        excluded_ids={removed_resource.id},
    )
    if candidate is None:
        return None

    additions = _resolve_missing_prerequisites(
        resource=candidate,
        resources_by_id=resources_by_id,
        available_ids=set(student.known_resources) | reduced_ids,
        max_allowed_difficulty=student.preferred_difficulty + 1,
        visiting=set(),
    )
    if additions is None:
        return None

    return _validated_path(
        resources=_append_unique(
            selected=reduced,
            additions=additions,
            known_resource_ids=set(student.known_resources),
        ),
        student=student,
    )


def _choose_candidate(
    resources: list[Resource],
    unavailable_ids: set[str],
    student: Student,
    rng: random.Random,
    min_utility_threshold: float,
    excluded_ids: set[str] | None = None,
) -> Resource | None:
    max_allowed_difficulty = student.preferred_difficulty + 1
    excluded = excluded_ids or set()
    candidates = [
        resource
        for resource in resources
        if resource.id not in unavailable_ids
        and resource.id not in excluded
        and resource.difficulty <= max_allowed_difficulty
        and resource.utility >= min_utility_threshold
    ]
    if not candidates:
        return None

    candidates.sort(key=_candidate_sort_key)
    index = int((rng.random() ** 2) * len(candidates))
    return candidates[min(index, len(candidates) - 1)]


def _resolve_missing_prerequisites(
    resource: Resource,
    resources_by_id: dict[str, Resource],
    available_ids: set[str],
    max_allowed_difficulty: int,
    visiting: set[str],
) -> list[Resource] | None:
    if resource.id in visiting:
        return None
    if resource.difficulty > max_allowed_difficulty:
        return None

    visiting.add(resource.id)
    try:
        additions: list[Resource] = []
        addition_ids: set[str] = set()

        for prerequisite_id in resource.prerequisites:
            if prerequisite_id in available_ids or prerequisite_id in addition_ids:
                continue

            prerequisite = resources_by_id.get(prerequisite_id)
            if prerequisite is None:
                return None

            prerequisite_chain = _resolve_missing_prerequisites(
                resource=prerequisite,
                resources_by_id=resources_by_id,
                available_ids=available_ids | addition_ids,
                max_allowed_difficulty=max_allowed_difficulty,
                visiting=visiting,
            )
            if prerequisite_chain is None:
                return None

            for chained_resource in prerequisite_chain:
                if (
                    chained_resource.id not in available_ids
                    and chained_resource.id not in addition_ids
                ):
                    additions.append(chained_resource)
                    addition_ids.add(chained_resource.id)

            if (
                prerequisite_id not in available_ids
                and prerequisite_id not in addition_ids
            ):
                additions.append(prerequisite)
                addition_ids.add(prerequisite_id)

        if resource.id not in available_ids and resource.id not in addition_ids:
            additions.append(resource)

        return additions
    finally:
        visiting.remove(resource.id)


def _remove_with_dependents(
    selected: list[Resource],
    resource_id: str,
    known_resource_ids: set[str],
) -> list[Resource]:
    removed_ids = {resource_id}
    changed = True

    while changed:
        changed = False
        available_ids = set(known_resource_ids)
        for resource in selected:
            if resource.id in removed_ids:
                continue

            if any(
                prerequisite not in available_ids
                for prerequisite in resource.prerequisites
            ):
                removed_ids.add(resource.id)
                changed = True
                continue

            available_ids.add(resource.id)

    return [resource for resource in selected if resource.id not in removed_ids]


def _append_unique(
    selected: list[Resource],
    additions: list[Resource],
    known_resource_ids: set[str],
) -> list[Resource]:
    selected_ids = {resource.id for resource in selected}
    appended = list(selected)

    for resource in additions:
        if resource.id in known_resource_ids or resource.id in selected_ids:
            continue

        appended.append(resource)
        selected_ids.add(resource.id)

    return appended


def _validated_path(resources: list[Resource], student: Student) -> LearningPath | None:
    path = LearningPath(resources=resources)
    if path.total_duration > student.available_hours:
        return None
    if validate_learning_path(path, student)["is_valid"]:
        return path

    return None


def _should_accept(
    current_score: float,
    neighbor_score: float,
    temperature: float,
    rng: random.Random,
) -> bool:
    if neighbor_score > current_score:
        return True
    if temperature <= 0:
        return False

    probability = math.exp((neighbor_score - current_score) / temperature)
    return rng.random() < probability


def _candidate_sort_key(resource: Resource) -> tuple[float, float, int]:
    duration = max(resource.duration_hours, 1)
    utility_per_hour = resource.utility / duration
    return (-utility_per_hour, -resource.utility, resource.duration_hours)


def _resource_map(resources: list[Resource]) -> dict[str, Resource]:
    return {resource.id: resource for resource in resources}


def _copy_path(path: LearningPath) -> LearningPath:
    return LearningPath(resources=list(path.resources))
