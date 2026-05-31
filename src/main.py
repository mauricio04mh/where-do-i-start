import argparse
import os

from src.llm.evaluator import (
    build_llm_scored_resources,
    build_rule_based_scoring_debug,
)
from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.services.path_service import (
    SUPPORTED_ALGORITHMS,
    build_learning_path,
    generate_path_for_student_object,
)
from src.utils.loaders import get_student_by_id, load_resources, load_students
from src.utils.validators import validate_learning_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic learning path for a student."
    )
    parser.add_argument(
        "--student",
        help="Student id. Defaults to the first student in the students dataset.",
    )
    parser.add_argument(
        "--resources-path",
        default="data/resources.json",
        help="Path to resources JSON.",
    )
    parser.add_argument(
        "--students-path",
        default="data/students.json",
        help="Path to students JSON.",
    )
    parser.add_argument(
        "--algorithm",
        default="greedy",
        choices=sorted(SUPPORTED_ALGORITHMS),
        help="Algorithm to use.",
    )
    parser.add_argument(
        "--use-llm-profile",
        action="store_true",
        help="Build the student from SAMPLE_USER_TEXT using the LLM profile flow.",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use Gemini to score top-K rule-based candidates before path generation.",
    )
    parser.add_argument(
        "--debug-scoring",
        action="store_true",
        help="Print rule-based and optional LLM scoring rankings without generating a path.",
    )
    parser.add_argument(
        "--llm-top-k",
        type=int,
        help="Override LLM_CANDIDATE_TOP_K for this execution.",
    )
    parser.add_argument(
        "--llm-score-weight",
        type=float,
        help="Override LLM_SCORE_WEIGHT for this execution.",
    )
    parser.add_argument(
        "--llm-provider",
        choices=["gemini", "ollama", "none"],
        help="Override LLM_PROVIDER for this execution.",
    )
    parser.add_argument(
        "--ollama-model",
        help="Override OLLAMA_MODEL for this execution.",
    )
    parser.add_argument(
        "--ollama-base-url",
        help="Override OLLAMA_BASE_URL for this execution.",
    )
    parser.add_argument(
        "--run-experiments",
        action="store_true",
        help="Run all algorithms for all students and save evaluation reports.",
    )
    return parser.parse_args()


def apply_llm_runtime_overrides(args: argparse.Namespace) -> None:
    if args.llm_provider:
        os.environ["LLM_PROVIDER"] = args.llm_provider
    if args.ollama_model:
        os.environ["OLLAMA_MODEL"] = args.ollama_model
    if args.ollama_base_url:
        os.environ["OLLAMA_BASE_URL"] = args.ollama_base_url


def select_student(
    args: argparse.Namespace,
    students: list[Student],
    resources: list[Resource],
) -> Student:
    if args.use_llm_profile:
        from src.llm.interpreter import interpret_student_profile
        from src.llm.profile_mapper import profile_to_student
        from src.test_llm_profile import SAMPLE_USER_TEXT

        try:
            profile = interpret_student_profile(SAMPLE_USER_TEXT)
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
        return profile_to_student(profile, resources=resources)

    if not students:
        raise SystemExit("No students found in the students dataset.")

    if args.student is None:
        return students[0]

    try:
        return get_student_by_id(students, args.student)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def print_learning_path(
    path: LearningPath,
    student: Student,
    algorithm: str,
    validation: dict,
) -> None:
    print()
    print(f"Student: {student.id}")
    print(f"Goal: {student.goal}")
    print(f"Available time: {student.available_hours} hours")
    print(f"Algorithm: {algorithm}")
    print()
    print("Recommended learning path:")

    if not path.resources:
        print("No resources could be recommended without breaking constraints.")

    for index, resource in enumerate(path.resources, start=1):
        print(f"{index}. {resource.title}")
        print(f"   id: {resource.id}")
        print(f"   duration: {resource.duration_hours}h")
        print(f"   difficulty: {resource.difficulty}")
        print(f"   utility: {resource.utility:.2f}")
        print()

    print(f"Total duration: {path.total_duration}h")
    print(f"Total utility: {path.total_utility:.2f}")
    print(f"Valid path: {validation['is_valid']}")
    if validation["violations"]:
        print("Violations:")
        for violation in validation["violations"]:
            print(f"- {violation}")
    else:
        print("Violations: none")


def print_scoring_debug(debug: dict, include_llm: bool) -> None:
    print()
    print(f"Student: {debug['student']['id']}")
    print(f"LLM provider: {debug['provider']}")
    print(f"LLM model: {debug['model']}")
    print(f"Top K: {debug['top_k']}")
    print(f"Score weight: {debug['score_weight']}")
    print(f"Utility threshold: {debug['utility_threshold']}")
    print()
    print("Rule-based ranking:")
    for resource in debug["rule_based_ranking"]:
        print(
            f"{resource['rank']}. {resource['title']} "
            f"({resource['id']}) - utility {resource['utility']:.2f}"
        )

    if not include_llm:
        return

    print()
    print("Top K candidates sent to LLM:")
    for resource in debug["rule_based_ranking"][: debug["top_k"]]:
        print(
            f"{resource['rank']}. {resource['title']} "
            f"({resource['id']}) - utility {resource['utility']:.2f}"
        )

    print()
    print("LLM scores:")
    for score in debug["llm_scores"]:
        print(
            f"- {score['resource_id']}: {score['relevance_score']} "
            f"({score['reason']})"
        )

    print()
    print("Inconsistency metrics:")
    for name, value in debug["inconsistency_metrics"].items():
        print(f"- {name}: {value}")

    print()
    print("Combined ranking:")
    for resource in debug["combined_ranking"]:
        print(
            f"{resource['rank']}. {resource['title']} ({resource['id']}) - "
            f"rule {resource['rule_based_utility']:.2f}, "
            f"llm {resource['llm_relevance_score']}, "
            f"final {resource['final_utility']:.2f}"
        )


def main() -> None:
    args = parse_args()
    apply_llm_runtime_overrides(args)
    if args.run_experiments:
        from src.evaluation.experiments import run_experiments

        run_experiments(
            resources_path=args.resources_path,
            students_path=args.students_path,
        )
        return

    resources = load_resources(args.resources_path)
    students = load_students(args.students_path)

    print(f"Loaded {len(resources)} resources.")
    print(f"Loaded {len(students)} students.")

    student = select_student(args=args, students=students, resources=resources)

    if args.debug_scoring:
        try:
            if args.use_llm:
                _, debug = build_llm_scored_resources(
                    student=student,
                    resources=resources,
                    top_k=args.llm_top_k,
                    score_weight=args.llm_score_weight,
                )
            else:
                debug = build_rule_based_scoring_debug(
                    student=student,
                    resources=resources,
                    top_k=args.llm_top_k,
                    score_weight=args.llm_score_weight,
                )
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc

        print_scoring_debug(debug, include_llm=args.use_llm)
        return

    if args.use_llm:
        try:
            result = generate_path_for_student_object(
                student=student,
                algorithm=args.algorithm,
                use_llm=True,
                llm_top_k=args.llm_top_k,
                llm_score_weight=args.llm_score_weight,
                resources=resources,
            )
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc

        path = LearningPath(resources=result["path"])
        validation = result["validation"]
    else:
        path = build_learning_path(args.algorithm, student=student, resources=resources)
        validation = validate_learning_path(path, student)

    print_learning_path(
        path=path,
        student=student,
        algorithm=args.algorithm,
        validation=validation,
    )


if __name__ == "__main__":
    main()
