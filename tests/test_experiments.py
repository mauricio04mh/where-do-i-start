import csv
import json

import pytest

from src.evaluation import experiments
from src.models.resource import Resource


def test_build_experiment_configs_for_each_mode() -> None:
    for mode in ["manual", "simulation", "sensitivity"]:
        configs = experiments.build_experiment_configs(
            mode=mode,
            algorithms=["greedy", "ant_colony"],
            include_llm=False,
        )

        assert [config.algorithm for config in configs] == ["greedy", "ant_colony"]
        assert all(config.use_llm is False for config in configs)


def test_build_experiment_configs_llm_comparison_includes_both_variants() -> None:
    configs = experiments.build_experiment_configs(
        mode="llm-comparison",
        algorithms=["greedy"],
        include_llm=False,
    )

    assert [config.use_llm for config in configs] == [False, True]
    assert [config.label for config in configs] == ["greedy-rule", "greedy-llm"]


def test_run_experiments_generates_csv_json_and_new_columns(
    tmp_path,
    monkeypatch,
) -> None:
    resources_path = _write_resources(tmp_path)
    students_path = _write_students(tmp_path)
    output_csv = tmp_path / "reports" / "experiment_results.csv"
    output_json = tmp_path / "reports" / "experiment_results.json"
    output_summary = tmp_path / "reports" / "experiment_summary.txt"

    monkeypatch.setattr(
        experiments,
        "generate_path_for_student_object",
        _fake_generate_path_for_student_object,
    )

    experiments.run_experiments(
        students_path=str(students_path),
        resources_path=str(resources_path),
        output_csv=str(output_csv),
        output_json=str(output_json),
        output_summary=str(output_summary),
        algorithms=["greedy"],
        seeds=[42],
    )

    with output_csv.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    with output_json.open("r", encoding="utf-8") as file:
        json_rows = json.load(file)

    assert output_summary.exists()
    assert len(rows) == 1
    assert len(json_rows) == 1
    for column in experiments.CSV_COLUMNS:
        assert column in rows[0]


def test_run_experiments_stores_selected_resource_details(
    tmp_path,
    monkeypatch,
) -> None:
    resources_path = _write_resources(tmp_path)
    students_path = _write_students(tmp_path)
    output_csv = tmp_path / "experiment_results.csv"
    output_json = tmp_path / "experiment_results.json"
    output_summary = tmp_path / "experiment_summary.txt"

    monkeypatch.setattr(
        experiments,
        "generate_path_for_student_object",
        _fake_generate_path_for_student_object,
    )

    experiments.run_experiments(
        students_path=str(students_path),
        resources_path=str(resources_path),
        output_csv=str(output_csv),
        output_json=str(output_json),
        output_summary=str(output_summary),
        algorithms=["greedy"],
        seeds=[42],
    )

    with output_json.open("r", encoding="utf-8") as file:
        rows = json.load(file)

    assert rows[0]["resource_ids"] == ["python-basics"]
    assert rows[0]["resource_titles"] == ["Python Basics"]
    assert rows[0]["resource_topics"] == ["Programming"]
    assert rows[0]["resource_types"] == ["course"]
    assert rows[0]["path_signature"] == "python-basics"


def test_run_experiments_calculates_greedy_comparison_metrics(
    tmp_path,
    monkeypatch,
) -> None:
    resources_path = _write_resources(tmp_path)
    students_path = _write_students(tmp_path)
    output_csv = tmp_path / "experiment_results.csv"
    output_json = tmp_path / "experiment_results.json"
    output_summary = tmp_path / "experiment_summary.txt"

    monkeypatch.setattr(
        experiments,
        "generate_path_for_student_object",
        _fake_generate_path_for_student_object,
    )

    experiments.run_experiments(
        students_path=str(students_path),
        resources_path=str(resources_path),
        output_csv=str(output_csv),
        output_json=str(output_json),
        output_summary=str(output_summary),
        algorithms=["greedy", "ant_colony"],
        seeds=[42],
    )

    with output_json.open("r", encoding="utf-8") as file:
        rows = json.load(file)

    greedy_row = rows[0]
    ant_colony_row = rows[1]

    assert greedy_row["same_as_greedy"] is True
    assert ant_colony_row["same_as_greedy"] is False
    assert 0 <= ant_colony_row["path_overlap_with_greedy"] <= 1
    assert ant_colony_row["path_overlap_with_greedy"] == pytest.approx(0.5)
    assert ant_colony_row["utility_delta_vs_greedy"] == pytest.approx(2.5)
    assert ant_colony_row["coverage_delta_vs_greedy"] == pytest.approx(0.25)


def test_run_experiments_error_does_not_stop_all_runs(tmp_path, monkeypatch) -> None:
    resources_path = _write_resources(tmp_path)
    students_path = _write_students(tmp_path)
    output_csv = tmp_path / "experiment_results.csv"
    output_json = tmp_path / "experiment_results.json"
    output_summary = tmp_path / "experiment_summary.txt"

    def fake_generate_path_for_student_object(**kwargs):
        if kwargs["algorithm"] == "branch_and_bound":
            raise RuntimeError("forced failure")
        return _fake_generate_path_for_student_object(**kwargs)

    monkeypatch.setattr(
        experiments,
        "generate_path_for_student_object",
        fake_generate_path_for_student_object,
    )

    experiments.run_experiments(
        students_path=str(students_path),
        resources_path=str(resources_path),
        output_csv=str(output_csv),
        output_json=str(output_json),
        output_summary=str(output_summary),
        algorithms=["greedy", "branch_and_bound"],
        seeds=[42],
    )

    with output_json.open("r", encoding="utf-8") as file:
        rows = json.load(file)

    assert [row["status"] for row in rows] == ["ok", "error"]
    assert rows[1]["error_message"] == "forced failure"


def test_run_experiments_llm_comparison_creates_with_and_without_llm(
    tmp_path,
    monkeypatch,
) -> None:
    resources_path = _write_resources(tmp_path)
    students_path = _write_students(tmp_path)
    output_csv = tmp_path / "experiment_results.csv"
    output_json = tmp_path / "experiment_results.json"
    output_summary = tmp_path / "experiment_summary.txt"

    monkeypatch.setattr(
        experiments,
        "generate_path_for_student_object",
        _fake_generate_path_for_student_object,
    )

    experiments.run_experiments(
        students_path=str(students_path),
        resources_path=str(resources_path),
        output_csv=str(output_csv),
        output_json=str(output_json),
        output_summary=str(output_summary),
        mode="llm-comparison",
        algorithms=["greedy"],
        seeds=[42],
    )

    with output_json.open("r", encoding="utf-8") as file:
        rows = json.load(file)

    assert [row["use_llm"] for row in rows] == [False, True]


def test_run_experiments_simulation_preserves_metadata(tmp_path, monkeypatch) -> None:
    resources_path = _write_resources(tmp_path)
    students_path = _write_students(
        tmp_path,
        simulation_metadata={
            "level": "advanced",
            "scenario": "rag-heavy",
            "generator_seed": 99,
        },
    )
    output_csv = tmp_path / "experiment_results.csv"
    output_json = tmp_path / "experiment_results.json"
    output_summary = tmp_path / "experiment_summary.txt"

    monkeypatch.setattr(
        experiments,
        "generate_path_for_student_object",
        _fake_generate_path_for_student_object,
    )

    experiments.run_experiments(
        students_path=str(students_path),
        resources_path=str(resources_path),
        output_csv=str(output_csv),
        output_json=str(output_json),
        output_summary=str(output_summary),
        mode="simulation",
        algorithms=["greedy"],
        seeds=[42],
    )

    with output_json.open("r", encoding="utf-8") as file:
        rows = json.load(file)

    assert rows[0]["level"] == "advanced"
    assert rows[0]["scenario"] == "rag-heavy"
    assert rows[0]["generator_seed"] == 99


def test_build_experiment_configs_rejects_invalid_mode() -> None:
    with pytest.raises(ValueError, match="Unsupported experiment mode"):
        experiments.build_experiment_configs(
            mode="unknown",
            algorithms=["greedy"],
            include_llm=False,
        )


def _fake_generate_path_for_student_object(**kwargs):
    student = kwargs["student"]
    algorithm = kwargs["algorithm"]
    path = _fake_path_for_algorithm(algorithm)
    total_utility = sum(resource.utility for resource in path)
    coverage_score = 0.5 if algorithm == "greedy" else 0.75
    return {
        "path": path,
        "metrics": {
            "student_id": student.id,
            "algorithm": algorithm,
            "total_duration": sum(resource.duration_hours for resource in path),
            "available_hours": student.available_hours,
            "time_usage_ratio": 0.25,
            "total_utility": total_utility,
            "resource_count": len(path),
            "valid": True,
            "violation_count": 0,
            "coverage_score": coverage_score,
        },
        "validation": {
            "is_valid": True,
            "violations": [],
        },
    }


def _fake_path_for_algorithm(algorithm: str) -> list[Resource]:
    python_basics = Resource(
        id="python-basics",
        title="Python Basics",
        topic="Programming",
        duration_hours=5,
        difficulty=1,
        prerequisites=[],
        description="Learn Python basics.",
        type="course",
        utility=10.0,
    )
    testing = Resource(
        id="testing-debugging",
        title="Testing and Debugging",
        topic="Software Quality",
        duration_hours=4,
        difficulty=2,
        prerequisites=["python-basics"],
        description="Practice tests and debugging.",
        type="workshop",
        utility=2.5,
    )

    if algorithm == "ant_colony":
        return [python_basics, testing]
    return [python_basics]


def _write_resources(tmp_path):
    resources_path = tmp_path / "resources.json"
    resources = [
        {
            "id": "python-basics",
            "title": "Python Basics",
            "topic": "Programming",
            "duration_hours": 5,
            "difficulty": 1,
            "prerequisites": [],
            "description": "Learn Python basics.",
            "type": "course",
            "utility": 0.0,
        },
        {
            "id": "testing-debugging",
            "title": "Testing and Debugging",
            "topic": "Software Quality",
            "duration_hours": 4,
            "difficulty": 2,
            "prerequisites": ["python-basics"],
            "description": "Practice tests and debugging.",
            "type": "workshop",
            "utility": 0.0,
        }
    ]
    resources_path.write_text(json.dumps(resources), encoding="utf-8")
    return resources_path


def _write_students(tmp_path, simulation_metadata=None):
    students_path = tmp_path / "students.json"
    student = {
        "id": "student-test",
        "goal": "Learn Python basics.",
        "available_hours": 20,
        "known_resources": [],
        "preferred_difficulty": 2,
        "preference": "balanced",
        "target_topics": ["Programming"],
        "constraints": [],
    }
    if simulation_metadata is not None:
        student["simulation_metadata"] = simulation_metadata

    students_path.write_text(json.dumps([student]), encoding="utf-8")
    return students_path
