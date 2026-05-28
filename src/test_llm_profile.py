import json

from src.llm.interpreter import interpret_student_profile
from src.llm.profile_mapper import profile_to_student


SAMPLE_USER_TEXT = (
    "I want to learn how to build AI chatbots for customer support. "
    "I already know Python basics and a little bit of databases. "
    "I have around 20 hours available and I prefer practical projects."
)


def _profile_to_dict(profile) -> dict:
    if hasattr(profile, "model_dump"):
        return profile.model_dump()
    return profile.dict()


def main() -> None:
    try:
        profile = interpret_student_profile(SAMPLE_USER_TEXT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    print(json.dumps(_profile_to_dict(profile), indent=2))

    student = profile_to_student(profile)
    print(student)


if __name__ == "__main__":
    main()
