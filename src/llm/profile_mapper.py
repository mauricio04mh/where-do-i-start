from src.llm.schemas import StudentProfileExtraction
from src.models.student import Student


def profile_to_student(
    profile: StudentProfileExtraction, student_id: str = "llm_student_001"
) -> Student:
    return Student(
        id=student_id,
        goal=profile.goal,
        available_hours=profile.available_hours,
        known_resources=[],
        preferred_difficulty=profile.preferred_difficulty,
        preference=profile.preference,
    )
