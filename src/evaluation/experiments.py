import csv
import json
import time
from pathlib import Path

from src.evaluation.metrics import evaluate_learning_path
from src.llm.config import load_llm_config
from src.llm.evaluator import build_llm_scored_resources
from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.services.path_service import build_learning_path
from src.utils.loaders import load_resources, load_students
from src.utils.validators import validate_learning_path

CONFIGS = [
    {"algorithm": "greedy", "use_llm": False},
    {"algorithm": "backtracking", "use_llm": False},
    {"algorithm": "greedy", "use_llm": True},
    {"algorithm": "backtracking", "use_llm": True},
]
CSV_COLUMNS = [
    "student_id",
    "algorithm",
    "use_llm",
    "llm_candidate_top_k",
    "llm_score_weight",
    "total_duration",
    "available_hours",
    "time_usage_ratio",
    "total_utility",
    "resource_count",
    "valid",
    "violation_count",
    "coverage_score",
    "runtime_seconds",
    "llm_scoring_runtime_seconds",
]


def run_experiments(
    resources_path: str = "data/resources.json",
    students_path: str = "data/students.json",
    output_dir: str = "reports/results",
) -> None:
    resources = load_resources(resources_path)
    students = load_students(students_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    metrics_rows: list[dict] = []
    generated_paths: list[dict] = []
    llm_config = load_llm_config()

    for student in students:
        llm_resources: list[Resource] | None = None
        llm_debug: dict | None = None
        llm_scoring_runtime_seconds = 0.0

        if any(config["use_llm"] for config in CONFIGS):
            start_scoring = time.perf_counter()
            llm_resources, llm_debug = build_llm_scored_resources(
                student=student,
                resources=resources,
            )
            llm_scoring_runtime_seconds = time.perf_counter() - start_scoring

        for config in CONFIGS:
            algorithm = str(config["algorithm"])
            use_llm = bool(config["use_llm"])
            path_resources = llm_resources if use_llm else resources
            if path_resources is None:
                raise RuntimeError("LLM resources were not prepared for LLM experiment.")

            start_time = time.perf_counter()
            path = build_learning_path(
                algorithm=algorithm,
                student=student,
                resources=path_resources,
                use_precomputed_utility=use_llm,
            )
            runtime_seconds = time.perf_counter() - start_time

            validation = validate_learning_path(path, student)
            metrics = evaluate_learning_path(
                path=path,
                student=student,
                algorithm=algorithm,
            )
            metrics["use_llm"] = use_llm
            metrics["llm_candidate_top_k"] = (
                llm_config.llm_candidate_top_k if use_llm else ""
            )
            metrics["llm_score_weight"] = (
                llm_config.llm_score_weight if use_llm else ""
            )
            metrics["runtime_seconds"] = runtime_seconds
            metrics["llm_scoring_runtime_seconds"] = (
                llm_scoring_runtime_seconds if use_llm else ""
            )

            metrics_rows.append(metrics)
            generated_paths.append(
                _serialize_generated_path(
                    path=path,
                    student=student,
                    algorithm=algorithm,
                    use_llm=use_llm,
                    validation=validation,
                    llm_debug=llm_debug if use_llm else None,
                )
            )

    _write_metrics_csv(output_path / "experiment_results.csv", metrics_rows)
    _write_generated_paths_json(output_path / "generated_paths.json", generated_paths)
    _write_generated_paths_txt(output_path / "generated_paths.txt", generated_paths)

    print(f"Wrote metrics to {output_path / 'experiment_results.csv'}")
    print(f"Wrote generated paths to {output_path / 'generated_paths.json'}")
    print(f"Wrote readable paths to {output_path / 'generated_paths.txt'}")


def _write_metrics_csv(path: Path, metrics_rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(_format_metrics_row(row) for row in metrics_rows)


def _format_metrics_row(row: dict) -> dict:
    formatted = dict(row)
    formatted["time_usage_ratio"] = f"{row['time_usage_ratio']:.4f}"
    formatted["total_utility"] = f"{row['total_utility']:.4f}"
    formatted["valid"] = str(row["valid"]).lower()
    formatted["coverage_score"] = f"{row['coverage_score']:.4f}"
    formatted["runtime_seconds"] = f"{row['runtime_seconds']:.4f}"
    if row["llm_scoring_runtime_seconds"] != "":
        formatted["llm_scoring_runtime_seconds"] = (
            f"{row['llm_scoring_runtime_seconds']:.4f}"
        )
    return formatted


def _write_generated_paths_json(path: Path, generated_paths: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(generated_paths, file, indent=2)
        file.write("\n")


def _write_generated_paths_txt(path: Path, generated_paths: list[dict]) -> None:
    separator = "=" * 60
    with path.open("w", encoding="utf-8") as file:
        for generated_path in generated_paths:
            file.write(f"{separator}\n")
            file.write(f"Student: {generated_path['student_id']}\n")
            file.write(f"Algorithm: {generated_path['algorithm']}\n")
            file.write(f"Use LLM: {generated_path['use_llm']}\n")
            file.write(f"Goal: {generated_path['goal']}\n")
            file.write(
                f"Available time: {generated_path['available_hours']} hours\n\n"
            )
            file.write("Recommended path:\n")

            if not generated_path["path"]:
                file.write("No resources could be recommended.\n")

            for resource in generated_path["path"]:
                file.write(f"{resource['position']}. {resource['title']}\n")
                file.write(f"   id: {resource['id']}\n")
                file.write(f"   topic: {resource['topic']}\n")
                file.write(f"   duration: {resource['duration_hours']}h\n")
                file.write(f"   difficulty: {resource['difficulty']}\n")
                file.write(f"   utility: {resource['utility']:.2f}\n\n")

            file.write(f"Total duration: {generated_path['total_duration']}h\n")
            file.write(f"Total utility: {generated_path['total_utility']:.2f}\n")
            file.write(f"Valid: {generated_path['valid']}\n")
            if generated_path["violations"]:
                file.write("Violations:\n")
                for violation in generated_path["violations"]:
                    file.write(f"- {violation}\n")
            else:
                file.write("Violations: none\n")
            file.write(f"{separator}\n\n")


def _serialize_generated_path(
    path: LearningPath,
    student: Student,
    algorithm: str,
    use_llm: bool,
    validation: dict,
    llm_debug: dict | None,
) -> dict:
    return {
        "student_id": student.id,
        "algorithm": algorithm,
        "use_llm": use_llm,
        "goal": student.goal,
        "available_hours": student.available_hours,
        "path": [
            _serialize_resource(resource=resource, position=position)
            for position, resource in enumerate(path.resources, start=1)
        ],
        "total_duration": path.total_duration,
        "total_utility": path.total_utility,
        "valid": validation["is_valid"],
        "violations": validation["violations"],
        "llm_debug": llm_debug,
    }


def _serialize_resource(resource: Resource, position: int) -> dict:
    return {
        "position": position,
        "id": resource.id,
        "title": resource.title,
        "topic": resource.topic,
        "duration_hours": resource.duration_hours,
        "difficulty": resource.difficulty,
        "utility": resource.utility,
        "prerequisites": resource.prerequisites,
        "type": resource.type,
    }


def main() -> None:
    run_experiments()


if __name__ == "__main__":
    main()
