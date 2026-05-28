from dataclasses import dataclass


@dataclass
class InterpretedProfile:
    goal: str
    available_hours: int
    known_topics: list[str]
    preferred_difficulty: int
    preference: str
    target_topics: list[str]
    constraints: list[str]
