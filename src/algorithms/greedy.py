import string
import unicodedata
from dataclasses import replace

from src.models.learning_path import LearningPath
from src.models.resource import Resource
from src.models.student import Student
from src.utils.validators import validate_learning_path

STOPWORDS = {
    "learn",
    "build",
    "create",
    "using",
    "with",
    "from",
    "that",
    "this",
    "enough",
    "before",
    "after",
    "into",
    "about",
    "how",
    "and",
    "for",
    "the",
    "to",
    "of",
    "in",
    "on",
    "a",
    "an",
    "or",
    "as",
    "by",
    "de",
    "del",
    "la",
    "el",
    "los",
    "las",
    "mi",
    "mis",
    "con",
    "entre",
    "estos",
}

GOAL_TOPIC_KEYWORDS = {
    "data": {"Data Science", "Databases", "Machine Learning"},
    "dataset": {"Data Science", "Databases", "Machine Learning"},
    "datasets": {"Data Science", "Databases", "Machine Learning"},
    "csv": {"Data Science", "Databases"},
    "analyze": {"Data Science", "Databases"},
    "analysis": {"Data Science"},
    "visualization": {"Data Science"},
    "visualizations": {"Data Science"},
    "chatbot": {"AI Chatbots", "LLMs", "Natural Language Processing", "RAG"},
    "chatbots": {"AI Chatbots", "LLMs", "Natural Language Processing", "RAG"},
    "customer": {"AI Chatbots", "Backend Development"},
    "support": {"AI Chatbots", "Backend Development"},
    "rag": {"RAG", "LLMs", "AI Chatbots"},
    "retrieval": {"RAG", "LLMs"},
    "documents": {"RAG", "LLMs", "Databases"},
    "llm": {"LLMs", "AI Chatbots"},
    "llms": {"LLMs", "AI Chatbots"},
    "prompt": {"LLMs"},
    "prompts": {"LLMs"},
    "structured": {"LLMs", "Backend Development"},
    "fullstack": {"Web Development", "Backend Development", "Databases"},
    "full": {"Web Development", "Backend Development", "Databases"},
    "stack": {"Web Development", "Backend Development", "Databases"},
    "front": {"Web Development"},
    "frontend": {"Web Development"},
    "api": {"Backend Development"},
    "apis": {"Backend Development"},
    "backend": {"Backend Development", "Databases", "Deployment"},
    "back": {"Backend Development"},
    "base": {"Databases"},
    "datos": {"Databases"},
    "database": {"Databases", "Backend Development"},
    "databases": {"Databases", "Backend Development"},
    "communication": {"Backend Development"},
    "comunicacion": {"Backend Development"},
    "page": {"Web Development"},
    "pagina": {"Web Development"},
    "website": {"Web Development"},
    "web": {"Web Development"},
    "portfolio": {"Web Development", "Developer Tools"},
    "server": {"Backend Development"},
    "servidor": {"Backend Development"},
    "deploy": {"Deployment"},
    "deployment": {"Deployment"},
    "levantar": {"Deployment"},
    "publicar": {"Deployment"},
    "containers": {"Deployment"},
    "production": {"Deployment"},
    "machine": {"Machine Learning"},
    "learning": {"Machine Learning", "LLMs"},
    "model": {"Machine Learning"},
    "models": {"Machine Learning"},
    "evaluation": {"Machine Learning"},
    "responsible": {"Responsible AI"},
    "ethics": {"Responsible AI"},
    "privacy": {"Responsible AI", "Databases"},
    "risks": {"Responsible AI"},
    "safe": {"Responsible AI", "AI Chatbots"},
}

FOUNDATIONAL_TOPICS = {
    "Programming",
    "Developer Tools",
    "Computer Science",
    "Databases",
    "Web Development",
    "Backend Development",
}

FULL_STACK_CORE_TOPICS = {
    "Web Development",
    "Backend Development",
    "Databases",
}

DATA_SCIENCE_GOAL_TOKENS = {
    "data",
    "dataset",
    "datasets",
    "csv",
    "analyze",
    "analysis",
    "visualization",
    "visualizations",
}


def compute_rule_based_utility(
    resource: Resource,
    student: Student,
    resources: list[Resource] | None = None,
) -> float:
    utility = 0.0
    normalized_goal = _normalize_text(_student_intent_text(student))
    goal_tokens = _tokenize_goal(_student_intent_text(student))
    resource_text = _resource_search_text(resource)
    target_topics = {_normalize_topic(topic) for topic in student.target_topics}
    recommended_topics = _recommended_topics_for_student(student)
    is_prerequisite_for_relevant_resource = (
        _is_prerequisite_for_relevant_resource(resource, resources, student)
        if resources is not None
        else False
    )
    semantically_relevant = _resource_matches_goal_or_targets(resource, student)

    if _topic_matches_target(resource.topic, student.target_topics):
        utility += 10.0
    if resource.topic in recommended_topics:
        utility += 8.0

    if resource.topic in FULL_STACK_CORE_TOPICS and _is_full_stack_intent(
        recommended_topics,
        target_topics,
    ):
        utility += 7.0

    if resource.topic == "Data Science" and goal_tokens & DATA_SCIENCE_GOAL_TOKENS:
        utility += 4.0

    if _normalize_text(resource.topic) in normalized_goal:
        utility += 5.0

    resource_tokens = set(resource_text.split())
    token_match_bonus = sum(0.75 for token in goal_tokens if token in resource_tokens)
    utility += min(token_match_bonus, 4.0)

    if student.preference == "practical" and resource.type in ["project", "workshop"]:
        utility += 2.0
    elif student.preference == "theoretical" and resource.type in ["course", "reading"]:
        utility += 2.0
    elif student.preference == "balanced":
        utility += 0.5

    difficulty_distance = abs(resource.difficulty - student.preferred_difficulty)
    if difficulty_distance == 0:
        utility += 1.0
    elif difficulty_distance == 1:
        utility += 0.5
    elif resource.difficulty > student.preferred_difficulty + 1:
        utility -= 4.0

    known_resource_ids = set(student.known_resources)
    if resource.prerequisites:
        known_prerequisites = [
            prerequisite
            for prerequisite in resource.prerequisites
            if prerequisite in known_resource_ids
        ]
        if len(known_prerequisites) == len(resource.prerequisites):
            utility += 1.5
        elif known_prerequisites:
            utility += 0.5

    if is_prerequisite_for_relevant_resource:
        utility += 3.0

    has_topic_guidance = bool(recommended_topics or target_topics)
    is_foundational = _is_effective_foundational_topic(
        resource.topic,
        recommended_topics,
        target_topics,
    )
    if (
        has_topic_guidance
        and not semantically_relevant
        and not is_foundational
        and not is_prerequisite_for_relevant_resource
    ):
        utility -= 8.0

    if (
        not semantically_relevant
        and not is_foundational
        and not is_prerequisite_for_relevant_resource
    ):
        utility = min(utility, 0.1)

    return max(utility, 0.1)


def _normalize_text(text: str) -> str:
    text = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    text = text.lower().replace("-", " ").replace("_", " ")
    translator = str.maketrans("", "", string.punctuation)
    return text.translate(translator)


def _tokenize_goal(goal: str) -> set[str]:
    return {
        word
        for word in _normalize_text(goal).split()
        if (len(word) > 3 or word in GOAL_TOPIC_KEYWORDS) and word not in STOPWORDS
    }


def _resource_search_text(resource: Resource) -> str:
    return _normalize_text(
        " ".join(
            [
                resource.id,
                resource.title,
                resource.topic,
                resource.description,
                resource.type,
            ]
        )
    )


def _normalize_topic(topic: str) -> str:
    return _normalize_text(topic).strip()


def _student_intent_text(student: Student) -> str:
    return " ".join([student.goal, *student.target_topics, *student.constraints])


def _recommended_topics_for_student(student: Student) -> set[str]:
    recommended_topics: set[str] = set()

    for token in _tokenize_goal(_student_intent_text(student)):
        recommended_topics.update(GOAL_TOPIC_KEYWORDS.get(token, set()))

    return recommended_topics


def _is_full_stack_intent(
    recommended_topics: set[str],
    target_topics: set[str],
) -> bool:
    matched_topics = set(recommended_topics)
    matched_topics.update(
        topic
        for topic in FULL_STACK_CORE_TOPICS
        if _normalize_topic(topic) in target_topics
    )

    return len(matched_topics & FULL_STACK_CORE_TOPICS) >= 2


def _topic_matches_target(resource_topic: str, target_topics: list[str]) -> bool:
    normalized_resource_topic = _normalize_topic(resource_topic)
    return any(
        normalized_resource_topic == _normalize_topic(target_topic)
        for target_topic in target_topics
    )


def _target_topic_tokens(student: Student) -> set[str]:
    tokens: set[str] = set()
    for text in [*student.target_topics, *student.constraints]:
        tokens.update(_tokenize_goal(text))

    return tokens


def _resource_matches_goal_or_targets(resource: Resource, student: Student) -> bool:
    if _topic_matches_target(resource.topic, student.target_topics):
        return True

    recommended_topics = _recommended_topics_for_student(student)
    if resource.topic in recommended_topics:
        return True

    normalized_intent = _normalize_text(_student_intent_text(student))
    if _normalize_topic(resource.topic) in normalized_intent:
        return True

    intent_tokens = _tokenize_goal(_student_intent_text(student)) | _target_topic_tokens(
        student
    )
    resource_tokens = set(_resource_search_text(resource).split())

    return len(intent_tokens & resource_tokens) >= 2


def _is_effective_foundational_topic(
    resource_topic: str,
    recommended_topics: set[str],
    target_topics: set[str],
) -> bool:
    if resource_topic not in FOUNDATIONAL_TOPICS:
        return False

    if resource_topic in {"Web Development", "Backend Development"}:
        return resource_topic in recommended_topics or (
            _normalize_topic(resource_topic) in target_topics
        )

    return True


def _is_prerequisite_for_relevant_resource(
    resource: Resource,
    resources: list[Resource] | None,
    student: Student,
) -> bool:
    if resources is None:
        return False

    for candidate in resources:
        if resource.id not in candidate.prerequisites:
            continue
        if _resource_matches_goal_or_targets(candidate, student):
            return True

    return False


def build_greedy_learning_path(
    student: Student,
    resources: list[Resource],
) -> LearningPath:
    known_resource_ids = set(student.known_resources)
    resources_by_id = {resource.id: resource for resource in resources}
    utility_resources = [
        replace(
            resource,
            utility=compute_rule_based_utility(resource, student, resources),
        )
        for resource in resources
    ]

    candidates = [
        resource for resource in utility_resources if resource.id not in known_resource_ids
    ]
    candidates.sort(
        key=lambda resource: (
            -(resource.utility / resource.duration_hours),
            -resource.utility,
            resource.duration_hours,
        )
    )

    utility_resources_by_id = {resource.id: resource for resource in utility_resources}
    selected: list[Resource] = []
    selected_ids: set[str] = set()

    for resource in candidates:
        if resource.id in selected_ids:
            continue
        if resource.utility < 1.0 and not _is_prerequisite_for_relevant_resource(
            resource,
            resources,
            student,
        ):
            continue

        prerequisite_chain = _missing_prerequisite_chain(
            resource=resource,
            resources_by_id=resources_by_id,
            utility_resources_by_id=utility_resources_by_id,
            available_ids=known_resource_ids | selected_ids,
            visiting=set(),
        )
        if prerequisite_chain is None:
            continue

        candidate_additions = [
            prerequisite
            for prerequisite in prerequisite_chain + [resource]
            if prerequisite.id not in known_resource_ids
            and prerequisite.id not in selected_ids
        ]
        if not candidate_additions:
            continue

        candidate_path = LearningPath(resources=selected + candidate_additions)
        validation = validate_learning_path(candidate_path, student)
        if validation["is_valid"]:
            selected.extend(candidate_additions)
            selected_ids.update(resource.id for resource in candidate_additions)

    return LearningPath(resources=selected)


def _missing_prerequisite_chain(
    resource: Resource,
    resources_by_id: dict[str, Resource],
    utility_resources_by_id: dict[str, Resource],
    available_ids: set[str],
    visiting: set[str],
) -> list[Resource] | None:
    if resource.id in visiting:
        return None

    visiting.add(resource.id)
    try:
        chain: list[Resource] = []
        chain_ids: set[str] = set()

        for prerequisite_id in resource.prerequisites:
            if prerequisite_id in available_ids or prerequisite_id in chain_ids:
                continue

            prerequisite = resources_by_id.get(prerequisite_id)
            if prerequisite is None:
                return None

            prerequisite_chain = _missing_prerequisite_chain(
                resource=prerequisite,
                resources_by_id=resources_by_id,
                utility_resources_by_id=utility_resources_by_id,
                available_ids=available_ids | chain_ids,
                visiting=visiting,
            )
            if prerequisite_chain is None:
                return None

            for chained_resource in prerequisite_chain:
                if (
                    chained_resource.id not in available_ids
                    and chained_resource.id not in chain_ids
                ):
                    chain.append(chained_resource)
                    chain_ids.add(chained_resource.id)

            if prerequisite_id not in available_ids and prerequisite_id not in chain_ids:
                utility_prerequisite = utility_resources_by_id[prerequisite_id]
                chain.append(utility_prerequisite)
                chain_ids.add(prerequisite_id)

        return chain
    finally:
        visiting.remove(resource.id)
