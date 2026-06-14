import json
from collections import Counter
from pathlib import Path

from src.simulation.resource_expander import (
    NEW_RESOURCES,
    REQUIRED_FIELDS,
    expand_resource_dataset,
)


ORIGINAL_RESOURCES_PATH = Path("data/resources.json")


def _generate_expanded_resources(tmp_path: Path) -> tuple[list[dict], list[dict], Path]:
    output_path = tmp_path / "data" / "processed" / "resources_expanded.json"

    with ORIGINAL_RESOURCES_PATH.open("r", encoding="utf-8") as file:
        original_resources = json.load(file)

    expanded_resources = expand_resource_dataset(ORIGINAL_RESOURCES_PATH, output_path)

    return original_resources, expanded_resources, output_path


def test_expand_resource_dataset_writes_expanded_file(tmp_path) -> None:
    _, expanded_resources, output_path = _generate_expanded_resources(tmp_path)

    assert output_path.exists()
    with output_path.open("r", encoding="utf-8") as file:
        saved_resources = json.load(file)

    assert saved_resources == expanded_resources


def test_expanded_resources_have_unique_ids(tmp_path) -> None:
    _, expanded_resources, _ = _generate_expanded_resources(tmp_path)
    resource_ids = [resource["id"] for resource in expanded_resources]

    assert len(resource_ids) == len(set(resource_ids))


def test_expanded_resources_have_required_fields(tmp_path) -> None:
    _, expanded_resources, _ = _generate_expanded_resources(tmp_path)

    for resource in expanded_resources:
        assert REQUIRED_FIELDS <= set(resource)


def test_expanded_resource_prerequisites_exist(tmp_path) -> None:
    _, expanded_resources, _ = _generate_expanded_resources(tmp_path)
    resource_ids = {resource["id"] for resource in expanded_resources}

    for resource in expanded_resources:
        assert set(resource["prerequisites"]) <= resource_ids


def test_expanded_resources_add_between_50_and_70_new_resources(tmp_path) -> None:
    original_resources, expanded_resources, _ = _generate_expanded_resources(tmp_path)

    added_count = len(expanded_resources) - len(original_resources)

    assert added_count == len(NEW_RESOURCES)
    assert 50 <= added_count <= 70


def test_expanded_resources_include_new_target_topics(tmp_path) -> None:
    original_resources, expanded_resources, _ = _generate_expanded_resources(tmp_path)
    original_ids = {resource["id"] for resource in original_resources}
    new_resources = [
        resource for resource in expanded_resources if resource["id"] not in original_ids
    ]
    new_topics = {resource["topic"] for resource in new_resources}

    assert {
        "LLMs",
        "RAG",
        "AI Chatbots",
        "Backend Development",
        "Data Science",
        "Deployment",
        "Responsible AI",
    } <= new_topics


def test_new_resources_are_distributed_across_requested_topics(tmp_path) -> None:
    original_resources, expanded_resources, _ = _generate_expanded_resources(tmp_path)
    original_ids = {resource["id"] for resource in original_resources}
    new_resources = [
        resource for resource in expanded_resources if resource["id"] not in original_ids
    ]
    topic_counts = Counter(resource["topic"] for resource in new_resources)

    assert 8 <= topic_counts["LLMs"] <= 10
    assert 10 <= topic_counts["RAG"] <= 12
    assert 8 <= topic_counts["AI Chatbots"] <= 10
    assert 8 <= topic_counts["Backend Development"] <= 10
    assert (
        8
        <= topic_counts["Data Science"] + topic_counts["Machine Learning"]
        <= 10
    )
    assert 6 <= topic_counts["Deployment"] <= 8
    assert 6 <= topic_counts["Responsible AI"] + topic_counts["Privacy"] <= 8


def test_expanded_resources_have_duration_variety(tmp_path) -> None:
    _, expanded_resources, _ = _generate_expanded_resources(tmp_path)
    durations = {resource["duration_hours"] for resource in expanded_resources}

    assert any(2 <= duration <= 4 for duration in durations)
    assert any(5 <= duration <= 8 for duration in durations)
    assert any(10 <= duration <= 16 for duration in durations)


def test_expanded_resources_have_type_variety(tmp_path) -> None:
    _, expanded_resources, _ = _generate_expanded_resources(tmp_path)
    resource_types = {resource["type"] for resource in expanded_resources}

    assert {"course", "reading", "workshop", "project"} <= resource_types
