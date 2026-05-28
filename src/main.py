import json

from src.llm.interpreter import interpret_student_profile
from src.test_llm_profile import SAMPLE_USER_TEXT
from src.utils.loaders import load_resources, load_students


def _profile_to_dict(profile) -> dict:
    if hasattr(profile, "model_dump"):
        return profile.model_dump()
    return profile.dict()


def main() -> None:
    resources = load_resources("data/resources.json")
    students = load_students("data/students.json")

    print(f"Loaded {len(resources)} resources.")
    print(f"Loaded {len(students)} students.")

    try:
        profile = interpret_student_profile(SAMPLE_USER_TEXT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    print(json.dumps(_profile_to_dict(profile), indent=2))


if __name__ == "__main__":
    main()
