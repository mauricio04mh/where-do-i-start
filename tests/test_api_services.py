import pytest

from src.services.path_service import generate_path_for_student


def test_generate_path_for_existing_student() -> None:
    result = generate_path_for_student("student-chatbot-beginner")

    assert result["student"].id == "student-chatbot-beginner"
    assert result["algorithm"] == "greedy"
    assert isinstance(result["path"], list)


def test_generate_path_for_missing_student() -> None:
    with pytest.raises(ValueError, match="was not found"):
        generate_path_for_student("missing-student")


def test_generate_path_for_unsupported_algorithm() -> None:
    with pytest.raises(ValueError, match="Unsupported algorithm"):
        generate_path_for_student("student-chatbot-beginner", algorithm="unknown")


def test_generate_path_response_contains_expected_keys() -> None:
    result = generate_path_for_student("student-chatbot-beginner")

    assert set(result) == {
        "student",
        "algorithm",
        "path",
        "metrics",
        "validation",
        "llm_debug",
    }
