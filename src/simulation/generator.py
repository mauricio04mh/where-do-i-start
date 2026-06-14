import argparse
import json
import random
from pathlib import Path
from typing import Any


AVAILABLE_HOURS = [10, 20, 30, 40, 50]
LEVELS = ["beginner", "intermediate", "advanced"]
PREFERENCES = ["practical", "theoretical", "balanced"]

BASE_INTERMEDIATE_RESOURCES = [
    "python-basics",
    "git-foundations",
    "databases-sql",
]

ADVANCED_GOAL_RESOURCES = {
    "AI Chatbots": ["api-design", "nlp-basics", "llm-fundamentals"],
    "LLMs": ["api-design", "nlp-basics", "llm-fundamentals"],
    "RAG": ["api-design", "nlp-basics", "llm-fundamentals", "databases-sql"],
    "Data Science": ["data-analysis-pandas"],
    "Machine Learning": ["data-analysis-pandas"],
    "Backend Development": ["api-design"],
    "Databases": ["api-design"],
    "Deployment": ["api-design"],
    "Responsible AI": ["nlp-basics", "llm-fundamentals"],
}

GOAL_PROFILES = {
    "AI Chatbots": {
        "goal": "Build useful AI chatbots for real user workflows.",
        "target_topics": ["AI Chatbots", "LLMs"],
    },
    "LLMs": {
        "goal": "Build practical applications with LLM APIs and prompt engineering.",
        "target_topics": ["LLMs", "Backend Development"],
    },
    "RAG": {
        "goal": "Build a RAG system that answers questions from documents.",
        "target_topics": ["RAG", "LLMs", "Databases"],
    },
    "Data Science": {
        "goal": "Analyze datasets and communicate insights with Python.",
        "target_topics": ["Data Science", "Databases"],
    },
    "Machine Learning": {
        "goal": "Train and evaluate machine learning models for real datasets.",
        "target_topics": ["Machine Learning", "Data Science"],
    },
    "Backend Development": {
        "goal": "Build backend APIs connected to databases.",
        "target_topics": ["Backend Development", "Databases"],
    },
    "Databases": {
        "goal": "Design and query relational databases for applications.",
        "target_topics": ["Databases", "Backend Development"],
    },
    "Deployment": {
        "goal": "Deploy backend services with production-oriented configuration.",
        "target_topics": ["Deployment", "Backend Development"],
    },
    "Responsible AI": {
        "goal": "Design AI products with safety, evaluation, and responsible use in mind.",
        "target_topics": ["Responsible AI", "AI Chatbots", "LLMs"],
    },
}


def _preferred_difficulty(level: str, rng: random.Random) -> int:
    if level == "beginner":
        return rng.choice([1, 2])
    if level == "intermediate":
        return rng.choice([2, 3, 4])
    return rng.choice([4, 5])


def _known_resources(goal: str, level: str, rng: random.Random) -> list[str]:
    if level == "beginner":
        beginner_candidates = ["python-basics", "git-foundations"]
        known_count = rng.choice([0, 0, 1])
        return rng.sample(beginner_candidates, known_count)

    if level == "intermediate":
        known_count = rng.choice([2, 3])
        return rng.sample(BASE_INTERMEDIATE_RESOURCES, known_count)

    advanced_resources = [
        *BASE_INTERMEDIATE_RESOURCES,
        *ADVANCED_GOAL_RESOURCES[goal],
    ]
    return list(dict.fromkeys(advanced_resources))


def generate_simulated_students(count: int = 100, seed: int = 42) -> list[dict]:
    """Generate simulated student profiles compatible with load_students()."""
    if count < 0:
        raise ValueError("count must be non-negative")

    rng = random.Random(seed)
    goals = list(GOAL_PROFILES)
    students: list[dict[str, Any]] = []

    for index in range(count):
        goal_name = rng.choice(goals)
        level = rng.choice(LEVELS)
        profile = GOAL_PROFILES[goal_name]

        students.append(
            {
                "id": f"sim-student-{index + 1:04d}",
                "goal": profile["goal"],
                "available_hours": rng.choice(AVAILABLE_HOURS),
                "known_resources": _known_resources(goal_name, level, rng),
                "preferred_difficulty": _preferred_difficulty(level, rng),
                "preference": rng.choice(PREFERENCES),
                "target_topics": list(profile["target_topics"]),
                "constraints": [],
                "simulation_metadata": {
                    "level": level,
                    "scenario": goal_name.lower().replace(" ", "-"),
                    "generator_seed": seed,
                },
            }
        )

    return students


def save_simulated_students(students: list[dict], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(students, file, indent=2, ensure_ascii=False)
        file.write("\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate simulated student profiles for algorithm evaluation."
    )
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        default="data/processed/simulated_students.json",
        help="Path where the generated JSON list will be written.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    students = generate_simulated_students(count=args.count, seed=args.seed)
    save_simulated_students(students, args.output)


if __name__ == "__main__":
    main()
