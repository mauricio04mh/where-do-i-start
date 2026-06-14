import json

from src.simulation.generator import generate_simulated_students, save_simulated_students
from src.utils.loaders import load_students


REQUIRED_FIELDS = {
    "id",
    "goal",
    "available_hours",
    "known_resources",
    "preferred_difficulty",
    "preference",
    "target_topics",
    "constraints",
}


def test_generate_simulated_students_returns_requested_count() -> None:
    students = generate_simulated_students(count=25, seed=7)

    assert len(students) == 25


def test_generate_simulated_students_ids_are_unique() -> None:
    students = generate_simulated_students(count=100, seed=7)
    student_ids = [student["id"] for student in students]

    assert len(student_ids) == len(set(student_ids))


def test_generate_simulated_students_required_fields_exist() -> None:
    students = generate_simulated_students(count=10, seed=7)

    for student in students:
        assert REQUIRED_FIELDS <= set(student)


def test_generate_simulated_students_values_are_valid() -> None:
    students = generate_simulated_students(count=100, seed=7)

    for student in students:
        assert student["available_hours"] > 0
        assert 1 <= student["preferred_difficulty"] <= 5
        assert student["preference"] in {"practical", "theoretical", "balanced"}


def test_save_simulated_students_writes_json_compatible_with_loader(tmp_path) -> None:
    students = generate_simulated_students(count=12, seed=7)
    output_path = tmp_path / "data" / "processed" / "simulated_students.json"

    save_simulated_students(students, output_path)

    with output_path.open("r", encoding="utf-8") as file:
        saved_students = json.load(file)

    loaded_students = load_students(str(output_path))

    assert saved_students == students
    assert len(loaded_students) == 12
    assert loaded_students[0].id == students[0]["id"]

