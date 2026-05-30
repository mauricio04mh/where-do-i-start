from dataclasses import dataclass

from src.models.resource import Resource


@dataclass
class LearningPath:
    resources: list[Resource]

    @property
    def resource_ids(self) -> list[str]:
        return [resource.id for resource in self.resources]

    @property
    def total_duration(self) -> int:
        return sum(resource.duration_hours for resource in self.resources)

    @property
    def total_utility(self) -> float:
        return sum(resource.utility for resource in self.resources)
