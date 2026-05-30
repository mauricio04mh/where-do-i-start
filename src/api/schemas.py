from typing import Literal

from pydantic import BaseModel, Field


Preference = Literal["practical", "theoretical", "balanced"]
Algorithm = Literal["greedy"]


class StudentBase(BaseModel):
    id: str
    goal: str
    available_hours: int = Field(ge=1)
    known_resources: list[str]
    preferred_difficulty: int = Field(ge=1, le=5)
    preference: Preference
    target_topics: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    goal: str | None = None
    available_hours: int | None = Field(default=None, ge=1)
    known_resources: list[str] | None = None
    preferred_difficulty: int | None = Field(default=None, ge=1, le=5)
    preference: Preference | None = None
    target_topics: list[str] | None = None
    constraints: list[str] | None = None


class StudentResponse(StudentBase):
    pass


class ResourceBase(BaseModel):
    id: str
    title: str
    topic: str
    duration_hours: int = Field(ge=1)
    difficulty: int = Field(ge=1, le=5)
    prerequisites: list[str]
    description: str
    type: str
    utility: float = 0.0


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    title: str | None = None
    topic: str | None = None
    duration_hours: int | None = Field(default=None, ge=1)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    prerequisites: list[str] | None = None
    description: str | None = None
    type: str | None = None
    utility: float | None = None


class ResourceResponse(ResourceBase):
    pass


class GeneratePathRequest(BaseModel):
    student_id: str
    algorithm: Algorithm = "greedy"
    use_llm: bool = False


class PathResourceResponse(BaseModel):
    id: str
    title: str
    topic: str
    duration_hours: int
    difficulty: int
    prerequisites: list[str]
    description: str
    type: str
    utility: float


class GeneratePathResponse(BaseModel):
    student: StudentResponse
    algorithm: str
    path: list[PathResourceResponse]
    metrics: dict
    validation: dict


class ChatAskRequest(BaseModel):
    message: str
    algorithm: Algorithm = "greedy"


class ChatAskResponse(BaseModel):
    interpreted_profile: dict
    generated_student: StudentResponse
    algorithm: str
    path: list[PathResourceResponse]
    metrics: dict
    validation: dict
