import string

from src.models.learning_path import LearningPath
from src.models.student import Student
from src.utils.validators import validate_learning_path


def compute_goal_coverage(path: LearningPath, student: Student) -> float:
    goal_words = _significant_words(student.goal)
    if not goal_words:
        return 0.0

    resource_text = " ".join(
        " ".join(
            [
                resource.title,
                resource.topic,
                resource.description,
                resource.type,
            ]
        )
        for resource in path.resources
    )
    resource_words = _significant_words(resource_text)

    matched_goal_words = goal_words & resource_words
    return len(matched_goal_words) / len(goal_words)


def evaluate_learning_path(
    path: LearningPath,
    student: Student,
    algorithm: str,
) -> dict:
    validation = validate_learning_path(path, student)
    time_usage_ratio = (
        path.total_duration / student.available_hours
        if student.available_hours > 0
        else 0.0
    )

    return {
        "student_id": student.id,
        "algorithm": algorithm,
        "total_duration": path.total_duration,
        "available_hours": student.available_hours,
        "time_usage_ratio": time_usage_ratio,
        "total_utility": path.total_utility,
        "resource_count": len(path.resources),
        "valid": validation["is_valid"],
        "violation_count": len(validation["violations"]),
        "coverage_score": compute_goal_coverage(path, student),
    }


def _significant_words(text: str) -> set[str]:
    translator = str.maketrans("", "", string.punctuation)
    normalized_text = text.lower().translate(translator)
    return {word for word in normalized_text.split() if len(word) > 3}
