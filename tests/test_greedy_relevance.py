from src.algorithms.greedy import build_greedy_learning_path
from src.models.student import Student
from src.utils.loaders import load_resources
from src.utils.validators import validate_learning_path


def make_student(
    goal: str,
    target_topics: list[str],
    known_resources: list[str] | None = None,
    available_hours: int = 30,
    preferred_difficulty: int = 2,
    preference: str = "balanced",
) -> Student:
    return Student(
        id="relevance-test",
        goal=goal,
        available_hours=available_hours,
        known_resources=known_resources or [],
        preferred_difficulty=preferred_difficulty,
        preference=preference,
        target_topics=target_topics,
    )


def test_full_stack_web_goal_avoids_unrelated_ai_resources() -> None:
    resources = load_resources("data/resources.json")
    student = make_student(
        goal=(
            "Learn to build a full-stack web application with frontend, "
            "backend, database and API communication"
        ),
        known_resources=["web-html-css", "javascript-essentials"],
        preferred_difficulty=2,
        target_topics=["Web Development", "Backend Development", "Databases"],
    )

    path = build_greedy_learning_path(student, resources)
    resource_ids = set(path.resource_ids)

    assert resource_ids & {
        "databases-sql",
        "api-design",
        "command-line-basics",
        "git-foundations",
        "python-basics",
    }
    assert not resource_ids & {
        "ai-ethics-basics",
        "chatbot-concepts",
        "llm-fundamentals",
        "prompt-engineering",
    }


def test_chatbot_goal_allows_chatbot_or_llm_resources() -> None:
    resources = load_resources("data/resources.json")
    student = make_student(
        goal="Learn how to build a simple AI chatbot",
        available_hours=25,
        target_topics=["AI Chatbots", "LLMs"],
    )

    path = build_greedy_learning_path(student, resources)

    assert any(
        resource.topic in {"AI Chatbots", "LLMs"} for resource in path.resources
    )


def test_relevance_paths_remain_valid() -> None:
    resources = load_resources("data/resources.json")
    students = [
        make_student(
            goal=(
                "Learn to build a full-stack web application with frontend, "
                "backend, database and API communication"
            ),
            known_resources=["web-html-css", "javascript-essentials"],
            target_topics=["Web Development", "Backend Development", "Databases"],
        ),
        make_student(
            goal="Learn how to build a simple AI chatbot",
            available_hours=25,
            target_topics=["AI Chatbots", "LLMs"],
        ),
    ]

    for student in students:
        path = build_greedy_learning_path(student, resources)
        validation = validate_learning_path(path, student)

        assert validation["is_valid"], validation["violations"]
