from dataclasses import replace

from src.algorithms.greedy import compute_rule_based_utility
from src.evaluation.metrics import compute_goal_coverage
from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.utils.validators import validate_learning_path

MIN_ROOT_UTILITY = 1.0


def build_backtracking_learning_path(
    student: Student,
    resources: list[Resource],
    max_candidates: int = 20,
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
    utility_resources_by_id = {resource.id: resource for resource in utility_resources}

    candidates = [
        resource
        for resource in utility_resources
        if resource.id not in known_resource_ids
        and resource.difficulty <= max_allowed_difficulty
        and resource.utility >= root_utility_threshold
    ]
    candidates.sort(key=_candidate_sort_key)
    candidates = candidates[:max_candidates]

    best_path = LearningPath(resources=[])

    def backtrack(
        index: int,
        selected: list[Resource],
        selected_ids: set[str],
    ) -> None:
        nonlocal best_path

        current_path = LearningPath(resources=selected)
        if _is_better_path(current_path, best_path, student):
            best_path = current_path

        if index >= len(candidates):
            return

        resource = candidates[index]

        if resource.id not in selected_ids and resource.id not in known_resource_ids:
            additions = _resources_needed_for(
                resource=resource,
                resources_by_id=utility_resources_by_id,
                available_ids=known_resource_ids | selected_ids,
                visiting=set(),
            )

            if additions is not None:
                candidate_resources = selected + [
                    addition
                    for addition in additions
                    if addition.id not in selected_ids
                    and addition.id not in known_resource_ids
                ]
                candidate_path = LearningPath(resources=candidate_resources)
                validation = validate_learning_path(candidate_path, student)

                if validation["is_valid"]:
                    backtrack(
                        index=index + 1,
                        selected=candidate_resources,
                        selected_ids={resource.id for resource in candidate_resources},
                    )

        backtrack(index=index + 1, selected=selected, selected_ids=selected_ids)

    backtrack(index=0, selected=[], selected_ids=set())
    return best_path


def _candidate_sort_key(resource: Resource) -> tuple[float, float, int]:
    utility_per_hour = resource.utility / resource.duration_hours
    return (-resource.utility, -utility_per_hour, resource.duration_hours)


def _resources_needed_for(
    resource: Resource,
    resources_by_id: dict[str, Resource],
    available_ids: set[str],
    visiting: set[str],
) -> list[Resource] | None:
    if resource.id in visiting:
        return None

    visiting.add(resource.id)
    try:
        needed: list[Resource] = []
        needed_ids: set[str] = set()

        for prerequisite_id in resource.prerequisites:
            if prerequisite_id in available_ids or prerequisite_id in needed_ids:
                continue

            prerequisite = resources_by_id.get(prerequisite_id)
            if prerequisite is None:
                return None

            prerequisite_chain = _resources_needed_for(
                resource=prerequisite,
                resources_by_id=resources_by_id,
                available_ids=available_ids | needed_ids,
                visiting=visiting,
            )
            if prerequisite_chain is None:
                return None

            for chained_resource in prerequisite_chain:
                if (
                    chained_resource.id not in available_ids
                    and chained_resource.id not in needed_ids
                ):
                    needed.append(chained_resource)
                    needed_ids.add(chained_resource.id)

            if prerequisite_id not in available_ids and prerequisite_id not in needed_ids:
                needed.append(prerequisite)
                needed_ids.add(prerequisite_id)

        if resource.id not in available_ids and resource.id not in needed_ids:
            needed.append(resource)

        return needed
    finally:
        visiting.remove(resource.id)


def _is_better_path(
    candidate: LearningPath,
    current_best: LearningPath,
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
    current_best_score = (
        current_best.total_utility,
        compute_goal_coverage(current_best, student),
        current_best.total_duration,
        -len(current_best.resources),
    )

    return candidate_score > current_best_score
