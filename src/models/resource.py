from dataclasses import dataclass


@dataclass
class Resource:
    id: str
    title: str
    topic: str
    duration_hours: int
    difficulty: int
    prerequisites: list[str]
    description: str
    type: str
    utility: float = 0.0
