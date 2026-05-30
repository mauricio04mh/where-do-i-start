from dataclasses import dataclass, field


@dataclass
class Student:
    id: str
    goal: str
    available_hours: int
    known_resources: list[str]
    preferred_difficulty: int
    preference: str
    target_topics: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
