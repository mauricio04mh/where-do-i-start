import random
from dataclasses import replace

from src.algorithms.greedy import compute_rule_based_utility
from src.evaluation.metrics import compute_goal_coverage
from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.utils.validators import validate_learning_path


def build_ant_colony_learning_path(
    student: Student,
    resources: list[Resource],
    num_ants: int = 30,
    num_iterations: int = 60,
    alpha: float = 1.0,
    beta: float = 2.0,
    evaporation_rate: float = 0.15,
    pheromone_deposit_weight: float = 1.0,
    seed: int | None = None,
    use_precomputed_utility: bool = False,
    min_utility_threshold: float | None = None,
) -> LearningPath:
    prepared_resources = _prepare_resources(
        student=student,
        resources=resources,
        use_precomputed_utility=use_precomputed_utility,
    )
    pheromones: dict[str, float] = {
        resource.id: 1.0 for resource in prepared_resources
    }
    rng = random.Random(42 if seed is None else seed)

    best_path = LearningPath(resources=[])
    best_score = _score_path(best_path, student)

    for _ in range(max(0, num_iterations)):
        iteration_paths = [
            _build_ant_path(
                student=student,
                resources=prepared_resources,
                pheromones=pheromones,
                rng=rng,
                alpha=alpha,
                beta=beta,
                min_utility_threshold=min_utility_threshold,
            )
            for _ in range(max(0, num_ants))
        ]

        for path in iteration_paths:
            if not path.resources:
                continue
            validation = validate_learning_path(path, student)
            if not validation["is_valid"]:
                continue

            score = _score_path(path, student)
            if score > best_score:
                best_path = _copy_path(path)
                best_score = score

        _evaporate_pheromones(
            pheromones=pheromones,
            evaporation_rate=evaporation_rate,
        )
        _deposit_pheromones(
            pheromones=pheromones,
            paths=iteration_paths,
            student=student,
            pheromone_deposit_weight=pheromone_deposit_weight,
        )

    if best_path.resources and validate_learning_path(best_path, student)["is_valid"]:
        return best_path

    return LearningPath(resources=[])


def _prepare_resources(
    student: Student,
    resources: list[Resource],
    use_precomputed_utility: bool,
) -> list[Resource]:
    if use_precomputed_utility:
        return [replace(resource) for resource in resources]

    return [
        replace(
            resource,
            utility=compute_rule_based_utility(resource, student, resources),
        )
        for resource in resources
    ]


def _build_ant_path(
    student: Student,
    resources: list[Resource],
    pheromones: dict[str, float],
    rng: random.Random,
    alpha: float,
    beta: float,
    min_utility_threshold: float | None,
) -> LearningPath:
    selected: list[Resource] = []
    selected_ids: set[str] = set()

    while True:
        candidates = _valid_candidates(
            student=student,
            resources=resources,
            selected=selected,
            selected_ids=selected_ids,
            min_utility_threshold=min_utility_threshold,
        )
        if not candidates:
            break

        next_resource = _select_next_resource(
            candidates=candidates,
            pheromones=pheromones,
            alpha=alpha,
            beta=beta,
            rng=rng,
        )
        selected.append(next_resource)
        selected_ids.add(next_resource.id)

    path = LearningPath(resources=selected)
    if validate_learning_path(path, student)["is_valid"]:
        return path

    return LearningPath(resources=[])


def _valid_candidates(
    student: Student,
    resources: list[Resource],
    selected: list[Resource],
    selected_ids: set[str],
    min_utility_threshold: float | None,
) -> list[Resource]:
    available_ids = set(student.known_resources) | selected_ids
    remaining_time = student.available_hours - sum(
        resource.duration_hours for resource in selected
    )
    max_allowed_difficulty = student.preferred_difficulty + 1

    candidates = [
        resource
        for resource in resources
        if resource.id not in available_ids
        and resource.duration_hours <= remaining_time
        and resource.difficulty <= max_allowed_difficulty
        and all(
            prerequisite_id in available_ids
            for prerequisite_id in resource.prerequisites
        )
    ]

    return _apply_utility_preference(
        candidates=candidates,
        min_utility_threshold=min_utility_threshold,
    )


def _apply_utility_preference(
    candidates: list[Resource],
    min_utility_threshold: float | None,
) -> list[Resource]:
    if not candidates:
        return []
    if min_utility_threshold is None:
        positive_candidates = [
            resource for resource in candidates if resource.utility > 0
        ]
        return positive_candidates or candidates

    threshold_candidates = [
        resource
        for resource in candidates
        if resource.utility >= min_utility_threshold
    ]
    if threshold_candidates:
        return threshold_candidates

    return [resource for resource in candidates if resource.utility > 0]


def _select_next_resource(
    candidates: list[Resource],
    pheromones: dict[str, float],
    alpha: float,
    beta: float,
    rng: random.Random,
) -> Resource:
    weighted_candidates = [
        (
            resource,
            _candidate_weight(
                resource=resource,
                pheromones=pheromones,
                alpha=alpha,
                beta=beta,
            ),
        )
        for resource in candidates
    ]
    total_weight = sum(weight for _, weight in weighted_candidates)
    if total_weight <= 0:
        return rng.choice(candidates)

    target = rng.uniform(0, total_weight)
    cumulative = 0.0
    for resource, weight in weighted_candidates:
        cumulative += weight
        if cumulative >= target:
            return resource

    return weighted_candidates[-1][0]


def _candidate_weight(
    resource: Resource,
    pheromones: dict[str, float],
    alpha: float,
    beta: float,
) -> float:
    pheromone = pheromones.get(resource.id, 1.0)
    heuristic = max(resource.utility / max(resource.duration_hours, 1), 0.01)
    return (pheromone**alpha) * (heuristic**beta)


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


def _evaporate_pheromones(
    pheromones: dict[str, float],
    evaporation_rate: float,
) -> None:
    bounded_evaporation_rate = min(max(evaporation_rate, 0.0), 1.0)
    for resource_id in pheromones:
        pheromones[resource_id] *= 1.0 - bounded_evaporation_rate
        pheromones[resource_id] = max(pheromones[resource_id], 0.01)


def _deposit_pheromones(
    pheromones: dict[str, float],
    paths: list[LearningPath],
    student: Student,
    pheromone_deposit_weight: float,
) -> None:
    for path in paths:
        if not path.resources:
            continue
        if not validate_learning_path(path, student)["is_valid"]:
            continue

        score = _score_path(path, student)
        deposit = pheromone_deposit_weight * max(score, 0.0) / max(
            path.total_duration,
            1,
        )
        for resource in path.resources:
            pheromones[resource.id] = pheromones.get(resource.id, 1.0) + deposit


def _copy_path(path: LearningPath) -> LearningPath:
    return LearningPath(resources=list(path.resources))
