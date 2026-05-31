from dataclasses import replace

from src.algorithms.greedy import compute_rule_based_utility
from src.evaluation.metrics import compute_goal_coverage
from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.utils.validators import validate_learning_path

MIN_ROOT_UTILITY = 0.0


def build_branch_and_bound_learning_path(
    student: Student,
    resources: list[Resource],
    max_candidates: int = 24,
    use_precomputed_utility: bool = False,
    min_utility_threshold: float | None = None,
) -> LearningPath:
    root_utility_threshold = (
        MIN_ROOT_UTILITY if min_utility_threshold is None else min_utility_threshold
    )
    known_resource_ids = set(student.known_resources)
    max_allowed_difficulty = student.preferred_difficulty + 1

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

    resources_by_id = _resource_map(utility_resources)
    candidates = [
        resource
        for resource in utility_resources
        if resource.id not in known_resource_ids
        and resource.difficulty <= max_allowed_difficulty
        and _passes_root_utility_threshold(resource, root_utility_threshold)
    ]
    candidates.sort(key=_candidate_sort_key)
    candidates = candidates[:max(0, max_candidates)]

    best_path = LearningPath(resources=[])

    def branch(
        index: int,
        selected: list[Resource],
        selected_ids: set[str],
    ) -> None:
        nonlocal best_path

        current_path = LearningPath(resources=selected)
        if current_path.total_duration > student.available_hours:
            return

        validation = validate_learning_path(current_path, student)
        if not validation["is_valid"]:
            return

        if _is_better_path(current_path, best_path, student):
            best_path = current_path

        if index >= len(candidates):
            return

        remaining_time = student.available_hours - current_path.total_duration
        upper_bound = _fractional_utility_upper_bound(
            current_utility=current_path.total_utility,
            remaining_time=remaining_time,
            remaining_candidates=candidates[index:],
            unavailable_ids=known_resource_ids | selected_ids,
            resources_by_id=resources_by_id,
        )
        if upper_bound <= best_path.total_utility:
            return

        resource = candidates[index]
        if resource.id not in selected_ids and resource.id not in known_resource_ids:
            additions = _resolve_missing_prerequisites(
                resource=resource,
                resources_by_id=resources_by_id,
                available_ids=known_resource_ids | selected_ids,
                visiting=set(),
            )
            if additions is not None:
                candidate_resources = _append_unique(
                    selected=selected,
                    additions=additions,
                    known_resource_ids=known_resource_ids,
                )
                if len(candidate_resources) > len(selected):
                    candidate_path = LearningPath(resources=candidate_resources)
                    if validate_learning_path(candidate_path, student)["is_valid"]:
                        branch(
                            index=index + 1,
                            selected=candidate_resources,
                            selected_ids={
                                resource.id for resource in candidate_resources
                            },
                        )

        branch(index=index + 1, selected=selected, selected_ids=selected_ids)

    branch(index=0, selected=[], selected_ids=set())
    return best_path


def _passes_root_utility_threshold(
    resource: Resource,
    root_utility_threshold: float,
) -> bool:
    if root_utility_threshold <= 0:
        return resource.utility > 0

    return resource.utility >= root_utility_threshold


def _candidate_sort_key(resource: Resource) -> tuple[float, float, int]:
    utility_per_hour = resource.utility / resource.duration_hours
    return (-utility_per_hour, -resource.utility, resource.duration_hours)


def _fractional_utility_upper_bound(
    current_utility: float,
    remaining_time: int,
    remaining_candidates: list[Resource],
    unavailable_ids: set[str],
    resources_by_id: dict[str, Resource],
) -> float:
    if remaining_time <= 0:
        return current_utility

    bound = current_utility
    time_left = remaining_time
    candidates: list[tuple[Resource, float]] = []
    for resource in remaining_candidates:
        if resource.id in unavailable_ids or resource.duration_hours <= 0:
            continue

        optimistic_utility = _optimistic_resource_utility(
            resource=resource,
            resources_by_id=resources_by_id,
            available_ids=unavailable_ids,
            visiting=set(),
        )
        if optimistic_utility > 0:
            candidates.append((resource, optimistic_utility))

    candidates.sort(
        key=lambda item: (
            -(item[1] / item[0].duration_hours),
            -item[1],
            item[0].duration_hours,
        )
    )

    for resource, optimistic_utility in candidates:
        if time_left <= 0:
            break

        if resource.duration_hours <= time_left:
            bound += optimistic_utility
            time_left -= resource.duration_hours
            continue

        bound += optimistic_utility * (time_left / resource.duration_hours)
        break

    return bound


def _optimistic_resource_utility(
    resource: Resource,
    resources_by_id: dict[str, Resource],
    available_ids: set[str],
    visiting: set[str],
) -> float:
    if resource.id in visiting:
        return 0.0

    visiting.add(resource.id)
    try:
        utility = max(resource.utility, 0.0)
        for prerequisite_id in resource.prerequisites:
            if prerequisite_id in available_ids:
                continue

            prerequisite = resources_by_id.get(prerequisite_id)
            if prerequisite is None:
                continue

            utility += _optimistic_resource_utility(
                resource=prerequisite,
                resources_by_id=resources_by_id,
                available_ids=available_ids | {resource.id},
                visiting=visiting,
            )

        return utility
    finally:
        visiting.remove(resource.id)


def _resolve_missing_prerequisites(
    resource: Resource,
    resources_by_id: dict[str, Resource],
    available_ids: set[str],
    visiting: set[str],
) -> list[Resource] | None:
    if resource.id in visiting:
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


def _resource_map(resources: list[Resource]) -> dict[str, Resource]:
    return {resource.id: resource for resource in resources}


def _is_better_path(
    candidate: LearningPath,
    best: LearningPath,
    student: Student,
) -> bool:
    candidate_validation = validate_learning_path(candidate, student)
    if not candidate_validation["is_valid"]:
        return False

    candidate_score = (
        candidate.total_utility,
        compute_goal_coverage(candidate, student),
        candidate.total_duration,
        -len(candidate.resources),
    )
    best_score = (
        best.total_utility,
        compute_goal_coverage(best, student),
        best.total_duration,
        -len(best.resources),
    )

    return candidate_score > best_score
