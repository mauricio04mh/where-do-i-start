import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from src.models.student import Student
from src.services.path_service import (
    SUPPORTED_ALGORITHMS,
    generate_path_for_student_object,
)
from src.utils.loaders import load_resources, load_students


DEFAULT_ALGORITHMS = [
    "greedy",
    "branch_and_bound",
    "simulated_annealing",
    "ant_colony",
]
DEFAULT_SEEDS = [42]
EXPERIMENT_MODES = {"manual", "simulation", "llm-comparison", "sensitivity"}
CSV_COLUMNS = [
    "mode",
    "student_id",
    "algorithm",
    "config_label",
    "use_llm",
    "seed",
    "status",
    "error_message",
    "total_duration",
    "available_hours",
    "time_usage_ratio",
    "total_utility",
    "resource_count",
    "valid",
    "violation_count",
    "coverage_score",
    "runtime_seconds",
    "resource_ids",
    "resource_titles",
    "resource_topics",
    "resource_types",
    "path_signature",
    "same_as_greedy",
    "path_overlap_with_greedy",
    "utility_delta_vs_greedy",
    "coverage_delta_vs_greedy",
    "runtime_delta_vs_greedy",
    "preference",
    "preferred_difficulty",
    "known_resource_count",
    "target_topics",
    "level",
    "scenario",
    "generator_seed",
]


@dataclass(frozen=True)
class ExperimentConfig:
    label: str
    algorithm: str
    use_llm: bool


def build_experiment_configs(
    mode: str,
    algorithms: list[str],
    include_llm: bool,
) -> list[ExperimentConfig]:
    if mode not in EXPERIMENT_MODES:
        raise ValueError(
            f"Unsupported experiment mode '{mode}'. "
            f"Supported modes are: {', '.join(sorted(EXPERIMENT_MODES))}."
        )

    _validate_algorithms(algorithms)

    use_llm_variants = [False, True] if mode == "llm-comparison" else [False]
    if include_llm and True not in use_llm_variants:
        use_llm_variants.append(True)

    return [
        ExperimentConfig(
            label=f"{algorithm}-{'llm' if use_llm else 'rule'}",
            algorithm=algorithm,
            use_llm=use_llm,
        )
        for algorithm in algorithms
        for use_llm in use_llm_variants
    ]


def run_experiments(
    students_path: str = "data/students.json",
    resources_path: str = "data/resources.json",
    output_csv: str = "reports/results/experiment_results.csv",
    output_json: str = "reports/results/experiment_results.json",
    output_summary: str = "reports/results/experiment_summary.txt",
    mode: str = "manual",
    algorithms: list[str] | None = None,
    seeds: list[int] | None = None,
    include_llm: bool = False,
    output_dir: str | None = None,
) -> None:
    if output_dir is not None:
        output_path = Path(output_dir)
        output_csv = str(output_path / "experiment_results.csv")
        output_json = str(output_path / "experiment_results.json")
        output_summary = str(output_path / "experiment_summary.txt")

    selected_algorithms = algorithms if algorithms is not None else DEFAULT_ALGORITHMS
    selected_seeds = seeds if seeds is not None else DEFAULT_SEEDS
    configs = build_experiment_configs(
        mode=mode,
        algorithms=selected_algorithms,
        include_llm=include_llm,
    )

    resources = load_resources(resources_path)
    students = load_students(students_path)

    rows: list[dict[str, Any]] = []
    for student in students:
        for seed in selected_seeds:
            for config in configs:
                rows.append(
                    _run_single_experiment(
                        mode=mode,
                        student=student,
                        resources=resources,
                        config=config,
                        seed=seed,
                    )
                )

    _add_greedy_comparison_metrics(rows)

    csv_path = Path(output_csv)
    json_path = Path(output_json)
    summary_path = Path(output_summary)
    _ensure_output_dirs(csv_path, json_path, summary_path)
    _write_results_csv(csv_path, rows)
    _write_results_json(json_path, rows)
    _write_summary(summary_path, rows)

    print(f"Wrote experiment CSV to {csv_path}")
    print(f"Wrote experiment JSON to {json_path}")
    print(f"Wrote experiment summary to {summary_path}")


def _run_single_experiment(
    mode: str,
    student: Student,
    resources: list,
    config: ExperimentConfig,
    seed: int,
) -> dict[str, Any]:
    base_row = _base_row(
        mode=mode,
        student=student,
        config=config,
        seed=seed,
    )
    start_time = time.perf_counter()

    try:
        result = generate_path_for_student_object(
            student=student,
            algorithm=config.algorithm,
            use_llm=config.use_llm,
            resources=resources,
            seed=seed,
        )
        runtime_seconds = time.perf_counter() - start_time
        metrics = result["metrics"]
        validation = result["validation"]
        path_resources = result.get("path", [])
        path_details = _path_details(path_resources)

        return {
            **base_row,
            "status": "ok",
            "error_message": "",
            "total_duration": metrics["total_duration"],
            "available_hours": metrics["available_hours"],
            "time_usage_ratio": metrics["time_usage_ratio"],
            "total_utility": metrics["total_utility"],
            "resource_count": metrics["resource_count"],
            "valid": validation["is_valid"],
            "violation_count": len(validation["violations"]),
            "coverage_score": metrics["coverage_score"],
            "runtime_seconds": runtime_seconds,
            **path_details,
        }
    except Exception as exc:
        runtime_seconds = time.perf_counter() - start_time
        return {
            **base_row,
            "status": "error",
            "error_message": str(exc),
            "total_duration": None,
            "available_hours": student.available_hours,
            "time_usage_ratio": None,
            "total_utility": None,
            "resource_count": None,
            "valid": None,
            "violation_count": None,
            "coverage_score": None,
            "runtime_seconds": runtime_seconds,
            **_empty_path_details(),
        }


def _base_row(
    mode: str,
    student: Student,
    config: ExperimentConfig,
    seed: int,
) -> dict[str, Any]:
    metadata = getattr(student, "simulation_metadata", {}) or {}
    return {
        "mode": mode,
        "student_id": student.id,
        "algorithm": config.algorithm,
        "config_label": config.label,
        "use_llm": config.use_llm,
        "seed": seed,
        "preference": student.preference,
        "preferred_difficulty": student.preferred_difficulty,
        "known_resource_count": len(student.known_resources),
        "target_topics": list(student.target_topics),
        "level": metadata.get("level", ""),
        "scenario": metadata.get("scenario", ""),
        "generator_seed": metadata.get("generator_seed", ""),
    }


def _path_details(path_resources: list) -> dict[str, Any]:
    resource_ids = [resource.id for resource in path_resources]
    return {
        "resource_ids": resource_ids,
        "resource_titles": [resource.title for resource in path_resources],
        "resource_topics": [resource.topic for resource in path_resources],
        "resource_types": [resource.type for resource in path_resources],
        "path_signature": " > ".join(resource_ids),
    }


def _empty_path_details() -> dict[str, Any]:
    return {
        "resource_ids": [],
        "resource_titles": [],
        "resource_topics": [],
        "resource_types": [],
        "path_signature": "",
    }


def _add_greedy_comparison_metrics(rows: list[dict[str, Any]]) -> None:
    greedy_rows: dict[tuple[str, int, bool], dict[str, Any]] = {}
    for row in rows:
        if row["status"] == "ok" and row["algorithm"] == "greedy":
            key = _comparison_key(row)
            greedy_rows.setdefault(key, row)

    for row in rows:
        greedy_row = greedy_rows.get(_comparison_key(row))
        if row["status"] != "ok" or greedy_row is None:
            row.update(_empty_greedy_comparison_metrics())
            continue

        row_resource_ids = set(row["resource_ids"])
        greedy_resource_ids = set(greedy_row["resource_ids"])
        row.update(
            {
                "same_as_greedy": row["resource_ids"] == greedy_row["resource_ids"],
                "path_overlap_with_greedy": _path_overlap(
                    row_resource_ids,
                    greedy_resource_ids,
                ),
                "utility_delta_vs_greedy": (
                    row["total_utility"] - greedy_row["total_utility"]
                ),
                "coverage_delta_vs_greedy": (
                    row["coverage_score"] - greedy_row["coverage_score"]
                ),
                "runtime_delta_vs_greedy": (
                    row["runtime_seconds"] - greedy_row["runtime_seconds"]
                ),
            }
        )


def _comparison_key(row: dict[str, Any]) -> tuple[str, int, bool]:
    return (row["student_id"], row["seed"], row["use_llm"])


def _empty_greedy_comparison_metrics() -> dict[str, Any]:
    return {
        "same_as_greedy": None,
        "path_overlap_with_greedy": None,
        "utility_delta_vs_greedy": None,
        "coverage_delta_vs_greedy": None,
        "runtime_delta_vs_greedy": None,
    }


def _path_overlap(resource_ids: set[str], greedy_resource_ids: set[str]) -> float:
    union = resource_ids | greedy_resource_ids
    if not union:
        return 1.0
    return len(resource_ids & greedy_resource_ids) / len(union)


def _validate_algorithms(algorithms: list[str]) -> None:
    if not algorithms:
        raise ValueError("At least one algorithm must be provided.")

    unsupported_algorithms = [
        algorithm for algorithm in algorithms if algorithm not in SUPPORTED_ALGORITHMS
    ]
    if unsupported_algorithms:
        raise ValueError(
            "Unsupported algorithms: "
            f"{', '.join(unsupported_algorithms)}. "
            f"Supported algorithms are: {', '.join(sorted(SUPPORTED_ALGORITHMS))}."
        )


def _ensure_output_dirs(*paths: Path) -> None:
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)


def _write_results_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(_format_csv_row(row) for row in rows)


def _write_results_json(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, indent=2)
        file.write("\n")


def _write_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    ok_rows = [row for row in rows if row["status"] == "ok"]
    error_rows = [row for row in rows if row["status"] == "error"]

    with path.open("w", encoding="utf-8") as file:
        file.write("Experiment summary\n")
        file.write("==================\n")
        file.write(f"Total runs: {len(rows)}\n")
        file.write(f"Successful runs: {len(ok_rows)}\n")
        file.write(f"Errors: {len(error_rows)}\n")
        file.write("\n")
        file.write("Averages by algorithm\n")
        file.write("---------------------\n")

        for algorithm in sorted({row["algorithm"] for row in rows}):
            algorithm_rows = [row for row in ok_rows if row["algorithm"] == algorithm]
            file.write(f"{algorithm}:\n")
            file.write(
                f"  average_utility: {_average_field(algorithm_rows, 'total_utility')}\n"
            )
            file.write(
                f"  average_runtime_seconds: "
                f"{_average_field(algorithm_rows, 'runtime_seconds')}\n"
            )
            file.write(
                f"  average_validity: {_average_validity(algorithm_rows)}\n"
            )
            file.write(
                f"  average_coverage: {_average_field(algorithm_rows, 'coverage_score')}\n"
            )
            file.write(
                f"  unique_paths: {_unique_path_count(algorithm_rows)}\n"
            )
            file.write(
                f"  average_path_overlap_with_greedy: "
                f"{_average_field(algorithm_rows, 'path_overlap_with_greedy')}\n"
            )
            file.write(
                f"  average_utility_delta_vs_greedy: "
                f"{_average_field(algorithm_rows, 'utility_delta_vs_greedy')}\n"
            )
            file.write(
                f"  utility_wins_vs_greedy: "
                f"{_count_positive_field(algorithm_rows, 'utility_delta_vs_greedy')}\n"
            )
            file.write(
                f"  coverage_wins_vs_greedy: "
                f"{_count_positive_field(algorithm_rows, 'coverage_delta_vs_greedy')}\n"
            )


def _average_field(rows: list[dict[str, Any]], field: str) -> str:
    values = [row[field] for row in rows if row[field] is not None]
    if not values:
        return "n/a"
    return f"{mean(values):.4f}"


def _average_validity(rows: list[dict[str, Any]]) -> str:
    values = [1.0 if row["valid"] else 0.0 for row in rows if row["valid"] is not None]
    if not values:
        return "n/a"
    return f"{mean(values):.4f}"


def _unique_path_count(rows: list[dict[str, Any]]) -> int:
    return len({row["path_signature"] for row in rows})


def _count_positive_field(rows: list[dict[str, Any]], field: str) -> int:
    return sum(1 for row in rows if row[field] is not None and row[field] > 0)


def _format_csv_row(row: dict[str, Any]) -> dict[str, Any]:
    formatted = {column: row.get(column, "") for column in CSV_COLUMNS}

    for key, value in list(formatted.items()):
        if value is None:
            formatted[key] = ""
        elif isinstance(value, bool):
            formatted[key] = str(value).lower()
        elif isinstance(value, float):
            formatted[key] = f"{value:.6f}"
        elif isinstance(value, (list, dict)):
            formatted[key] = json.dumps(value)

    return formatted


def main() -> None:
    run_experiments()


if __name__ == "__main__":
    main()
