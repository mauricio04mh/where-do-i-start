from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.utils.validators import validate_learning_path


def make_resource(
    resource_id: str,
    duration_hours: int = 5,
    difficulty: int = 2,
    prerequisites: list[str] | None = None,
) -> Resource:
    return Resource(
        id=resource_id,
        title=f"{resource_id} title",
        topic="Programming",
        duration_hours=duration_hours,
        difficulty=difficulty,
        prerequisites=prerequisites or [],
        description=f"{resource_id} description",
        type="course",
        utility=1.0,
    )


def make_student(
    available_hours: int = 20,
    known_resources: list[str] | None = None,
    preferred_difficulty: int = 2,
) -> Student:
    return Student(
        id="student-test",
        goal="Learn programming fundamentals.",
        available_hours=available_hours,
        known_resources=known_resources or [],
        preferred_difficulty=preferred_difficulty,
        preference="balanced",
    )


def test_valid_path_with_prerequisites_in_order() -> None:
    intro = make_resource("intro")
    advanced = make_resource("advanced", prerequisites=["intro"])
    path = LearningPath(resources=[intro, advanced])
    student = make_student()

    validation = validate_learning_path(path, student)

    assert validation == {"is_valid": True, "violations": []}


def test_invalid_path_exceeds_available_time() -> None:
    path = LearningPath(
        resources=[
            make_resource("intro", duration_hours=8),
            make_resource("advanced", duration_hours=9),
        ]
    )
    student = make_student(available_hours=10)

    validation = validate_learning_path(path, student)

    assert validation["is_valid"] is False
    assert "Total duration 17 exceeds available time 10." in validation["violations"]


def test_invalid_path_missing_prerequisite() -> None:
    advanced = make_resource("advanced", prerequisites=["intro"])
    path = LearningPath(resources=[advanced])
    student = make_student()

    validation = validate_learning_path(path, student)

    assert validation["is_valid"] is False
    assert (
        "Resource advanced is missing prerequisite intro."
        in validation["violations"]
    )


def test_invalid_path_prerequisite_in_wrong_order() -> None:
    intro = make_resource("intro")
    advanced = make_resource("advanced", prerequisites=["intro"])
    path = LearningPath(resources=[advanced, intro])
    student = make_student()

    validation = validate_learning_path(path, student)

    assert validation["is_valid"] is False
    assert (
        "Resource advanced is missing prerequisite intro."
        in validation["violations"]
    )


def test_invalid_path_duplicated_resource() -> None:
    intro = make_resource("intro")
    path = LearningPath(resources=[intro, intro])
    student = make_student()

    validation = validate_learning_path(path, student)

    assert validation["is_valid"] is False
    assert (
        "Learning path contains duplicated resources: intro."
        in validation["violations"]
    )


def test_invalid_path_difficulty_too_high() -> None:
    hard_resource = make_resource("hard", difficulty=4)
    path = LearningPath(resources=[hard_resource])
    student = make_student(preferred_difficulty=2)

    validation = validate_learning_path(path, student)

    assert validation["is_valid"] is False
    assert (
        "Resource hard difficulty 4 is too high for preferred difficulty 2."
        in validation["violations"]
    )
