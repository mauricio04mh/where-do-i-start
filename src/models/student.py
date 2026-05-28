from dataclasses import dataclass


@dataclass
class Student:
    id: str
    goal: str
    available_hours: int
    known_resources: list[str]
    preferred_difficulty: int
    preference: str
