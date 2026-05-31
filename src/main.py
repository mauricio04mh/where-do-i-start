import argparse

from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.services.path_service import SUPPORTED_ALGORITHMS, build_learning_path
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
        "--run-experiments",
        action="store_true",
        help="Run all algorithms for all students and save evaluation reports.",
    )
    return parser.parse_args()


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


def main() -> None:
    args = parse_args()
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
