from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StudentProfileExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str
    available_hours: int = Field(ge=1, le=500)
    known_topics: list[str]
    preferred_difficulty: int = Field(ge=1, le=5)
    preference: Literal["practical", "theoretical", "balanced"]
    target_topics: list[str]
    constraints: list[str]
