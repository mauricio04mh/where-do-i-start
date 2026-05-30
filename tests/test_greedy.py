from src.algorithms.greedy import compute_rule_based_utility
from src.models.resource import Resource
from src.models.student import Student


def make_resource(
    resource_id: str,
    title: str,
    topic: str,
    resource_type: str = "course",
    difficulty: int = 3,
    prerequisites: list[str] | None = None,
    description: str = "Focused learning resource.",
) -> Resource:
    return Resource(
        id=resource_id,
        title=title,
        topic=topic,
        duration_hours=5,
        difficulty=difficulty,
        prerequisites=prerequisites or [],
        description=description,
        type=resource_type,
    )


def make_student(
    goal: str,
    preference: str = "balanced",
    known_resources: list[str] | None = None,
    preferred_difficulty: int = 3,
) -> Student:
    return Student(
        id="student-test",
        goal=goal,
        available_hours=20,
        known_resources=known_resources or [],
        preferred_difficulty=preferred_difficulty,
        preference=preference,
    )


def test_data_goal_prefers_data_science_over_unrelated_nlp() -> None:
    student = make_student(goal="Analyze CSV datasets with Python")
    data_resource = make_resource(
        resource_id="data-analysis-pandas",
        title="Data Analysis with Pandas",
        topic="Data Science",
        description="Analyze datasets with Python and pandas.",
    )
    nlp_resource = make_resource(
        resource_id="text-preprocessing",
        title="Text Preprocessing Workshop",
        topic="Natural Language Processing",
        resource_type="workshop",
        description="Clean and tokenize text for NLP applications.",
    )

    data_utility = compute_rule_based_utility(data_resource, student)
    nlp_utility = compute_rule_based_utility(nlp_resource, student)

    assert data_utility > nlp_utility


def test_chatbot_goal_prefers_chatbot_resource_over_data_science() -> None:
    student = make_student(goal="Build a simple AI chatbot for customer support")
    chatbot_resource = make_resource(
        resource_id="chatbot-concepts",
        title="Chatbot Design Concepts",
        topic="AI Chatbots",
        description="Design chatbot flows for customer support.",
    )
    data_resource = make_resource(
        resource_id="statistics-basics",
        title="Statistics Basics for Data Science",
        topic="Data Science",
        description="Study distributions, sampling, and correlation.",
    )

    chatbot_utility = compute_rule_based_utility(chatbot_resource, student)
    data_utility = compute_rule_based_utility(data_resource, student)

    assert chatbot_utility > data_utility


def test_practical_preference_favors_project_over_reading() -> None:
    student = make_student(
        goal="Build data analysis skills",
        preference="practical",
    )
    project_resource = make_resource(
        resource_id="data-project",
        title="Data Analysis Project",
        topic="Data Science",
        resource_type="project",
    )
    reading_resource = make_resource(
        resource_id="data-reading",
        title="Data Analysis Reading",
        topic="Data Science",
        resource_type="reading",
    )

    project_utility = compute_rule_based_utility(project_resource, student)
    reading_utility = compute_rule_based_utility(reading_resource, student)

    assert project_utility > reading_utility


def test_theoretical_preference_favors_reading_over_project() -> None:
    student = make_student(
        goal="Understand data analysis concepts",
        preference="theoretical",
    )
    reading_resource = make_resource(
        resource_id="data-reading",
        title="Data Analysis Reading",
        topic="Data Science",
        resource_type="reading",
    )
    project_resource = make_resource(
        resource_id="data-project",
        title="Data Analysis Project",
        topic="Data Science",
        resource_type="project",
    )

    reading_utility = compute_rule_based_utility(reading_resource, student)
    project_utility = compute_rule_based_utility(project_resource, student)

    assert reading_utility > project_utility


def test_known_prerequisites_increase_resource_utility() -> None:
    resource = make_resource(
        resource_id="data-visualization",
        title="Data Visualization with Python",
        topic="Data Science",
        prerequisites=["data-analysis-pandas"],
    )
    prepared_student = make_student(
        goal="Create data visualizations",
        known_resources=["data-analysis-pandas"],
    )
    unprepared_student = make_student(
        goal="Create data visualizations",
        known_resources=[],
    )

    prepared_utility = compute_rule_based_utility(resource, prepared_student)
    unprepared_utility = compute_rule_based_utility(resource, unprepared_student)

    assert prepared_utility > unprepared_utility
