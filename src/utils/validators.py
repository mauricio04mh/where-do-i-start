from collections import Counter

from src.models.learning_path import LearningPath
from src.models.student import Student


def validate_learning_path(path: LearningPath, student: Student) -> dict:
    violations: list[str] = []

    if path.total_duration > student.available_hours:
        violations.append(
            f"Total duration {path.total_duration} exceeds available time "
            f"{student.available_hours}."
        )

    duplicated_resource_ids = [
        resource_id
        for resource_id, count in Counter(path.resource_ids).items()
        if count > 1
    ]
    if duplicated_resource_ids:
        violations.append(
            "Learning path contains duplicated resources: "
            f"{', '.join(duplicated_resource_ids)}."
        )

    available_resources = set(student.known_resources)
    max_allowed_difficulty = student.preferred_difficulty + 1

    for resource in path.resources:
        for prerequisite in resource.prerequisites:
            if prerequisite not in available_resources:
                violations.append(
                    f"Resource {resource.id} is missing prerequisite "
                    f"{prerequisite}."
                )

        if resource.difficulty > max_allowed_difficulty:
            violations.append(
                f"Resource {resource.id} difficulty {resource.difficulty} "
                f"is too high for preferred difficulty "
                f"{student.preferred_difficulty}."
            )

        available_resources.add(resource.id)

    return {
        "is_valid": not violations,
        "violations": violations,
    }
