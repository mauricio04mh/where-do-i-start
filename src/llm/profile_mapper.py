from src.llm.schemas import StudentProfileExtraction
from src.models.resource import Resource
from src.models.student import Student


def normalize_text(text: str) -> str:
    return text.lower().replace("-", " ").replace("_", " ").strip()


def topic_matches_resource(topic: str, resource: Resource) -> bool:
    normalized_topic = normalize_text(topic)
    topic_words = normalized_topic.split()

    if not topic_words:
        return False

    searchable_text = normalize_text(
        " ".join(
            [
                resource.id,
                resource.title,
                resource.topic,
                resource.description,
            ]
        )
    )
    match_count = sum(1 for word in topic_words if word in searchable_text)
    required_matches = max(1, (len(topic_words) + 1) // 2)

    return match_count >= required_matches


def map_known_topics_to_resources(
    known_topics: list[str],
    resources: list[Resource],
) -> list[str]:
    known_resources: list[str] = []
    seen_resource_ids: set[str] = set()

    for topic in known_topics:
        for resource in resources:
            if topic_matches_resource(topic, resource):
                if resource.id not in seen_resource_ids:
                    known_resources.append(resource.id)
                    seen_resource_ids.add(resource.id)
                break

    return known_resources


def profile_to_student(
    profile: StudentProfileExtraction,
    resources: list[Resource] | None = None,
    student_id: str = "llm_student_001",
) -> Student:
    known_resources = (
        map_known_topics_to_resources(profile.known_topics, resources)
        if resources is not None
        else []
    )

    return Student(
        id=student_id,
        goal=profile.goal,
        available_hours=profile.available_hours,
        known_resources=known_resources,
        preferred_difficulty=profile.preferred_difficulty,
        preference=profile.preference,
        target_topics=profile.target_topics,
        constraints=profile.constraints,
    )
