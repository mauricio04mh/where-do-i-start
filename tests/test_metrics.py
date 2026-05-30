import pytest

from src.evaluation.metrics import compute_goal_coverage, evaluate_learning_path
from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student


def make_resource(
    resource_id: str,
    title: str | None = None,
    topic: str = "Programming",
    duration_hours: int = 5,
    difficulty: int = 2,
    prerequisites: list[str] | None = None,
    description: str | None = None,
    resource_type: str = "course",
    utility: float = 1.0,
) -> Resource:
    return Resource(
        id=resource_id,
        title=title or f"{resource_id} title",
        topic=topic,
        duration_hours=duration_hours,
        difficulty=difficulty,
        prerequisites=prerequisites or [],
        description=description or f"{resource_id} description",
        type=resource_type,
        utility=utility,
    )


def make_student(
    goal: str = "Learn programming fundamentals.",
    available_hours: int = 20,
    known_resources: list[str] | None = None,
    preferred_difficulty: int = 2,
) -> Student:
    return Student(
        id="student-test",
        goal=goal,
        available_hours=available_hours,
        known_resources=known_resources or [],
        preferred_difficulty=preferred_difficulty,
        preference="balanced",
    )


def test_evaluate_learning_path_returns_expected_keys() -> None:
    path = LearningPath(resources=[make_resource("intro")])
    student = make_student()

    metrics = evaluate_learning_path(path, student, "greedy")

    assert set(metrics) == {
        "student_id",
        "algorithm",
        "total_duration",
        "available_hours",
        "time_usage_ratio",
        "total_utility",
        "resource_count",
        "valid",
        "violation_count",
        "coverage_score",
    }


def test_time_usage_ratio_is_calculated_correctly() -> None:
    path = LearningPath(resources=[make_resource("intro", duration_hours=5)])
    student = make_student(available_hours=20)

    metrics = evaluate_learning_path(path, student, "greedy")

    assert metrics["time_usage_ratio"] == pytest.approx(0.25)


def test_time_usage_ratio_is_zero_when_available_hours_is_not_positive() -> None:
    path = LearningPath(resources=[make_resource("intro", duration_hours=5)])
    student = make_student(available_hours=0)

    metrics = evaluate_learning_path(path, student, "greedy")

    assert metrics["time_usage_ratio"] == 0.0


def test_total_utility_is_calculated_correctly() -> None:
    path = LearningPath(
        resources=[
            make_resource("intro", utility=2.5),
            make_resource("advanced", utility=3.75),
        ]
    )
    student = make_student()

    metrics = evaluate_learning_path(path, student, "greedy")

    assert metrics["total_utility"] == pytest.approx(6.25)


def test_valid_is_true_for_valid_path() -> None:
    intro = make_resource("intro")
    advanced = make_resource("advanced", prerequisites=["intro"])
    path = LearningPath(resources=[intro, advanced])
    student = make_student()

    metrics = evaluate_learning_path(path, student, "greedy")

    assert metrics["valid"] is True


def test_violation_count_increases_for_invalid_path() -> None:
    advanced = make_resource("advanced", prerequisites=["intro"])
    path = LearningPath(resources=[advanced])
    student = make_student()

    metrics = evaluate_learning_path(path, student, "greedy")

    assert metrics["valid"] is False
    assert metrics["violation_count"] > 0


def test_coverage_score_is_between_zero_and_one() -> None:
    path = LearningPath(resources=[make_resource("intro")])
    student = make_student()

    coverage_score = compute_goal_coverage(path, student)

    assert 0.0 <= coverage_score <= 1.0


def test_coverage_score_is_positive_when_goal_matches_resource_content() -> None:
    path = LearningPath(
        resources=[
            make_resource(
                "pandas",
                title="Data Analysis with Pandas",
                topic="Data Science",
                description="Analyze datasets with Python.",
                resource_type="project",
            )
        ]
    )
    student = make_student(
        goal="Learn data analysis to analyze datasets independently."
    )

    coverage_score = compute_goal_coverage(path, student)

    assert coverage_score > 0.0
