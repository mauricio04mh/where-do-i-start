import json
from dataclasses import asdict
from pathlib import Path

from src.models.resource import Resource
from src.utils.loaders import load_resources


def list_resources(path: str = "data/resources.json") -> list[Resource]:
    return load_resources(path)


def get_resource(
    resource_id: str,
    path: str = "data/resources.json",
) -> Resource | None:
    for resource in list_resources(path):
        if resource.id == resource_id:
            return resource

    return None


def create_resource(
    resource: Resource,
    path: str = "data/resources.json",
) -> Resource:
    resources = list_resources(path)
    if any(existing_resource.id == resource.id for existing_resource in resources):
        raise ValueError(f"Resource with id '{resource.id}' already exists.")

    resources.append(resource)
    _write_resources(resources, path)
    return resource


def update_resource(
    resource_id: str,
    updates: dict,
    path: str = "data/resources.json",
) -> Resource | None:
    resources = list_resources(path)

    for index, resource in enumerate(resources):
        if resource.id == resource_id:
            resource_data = asdict(resource)
            resource_data.update(
                {
                    field: value
                    for field, value in updates.items()
                    if value is not None
                }
            )
            updated_resource = Resource(**resource_data)
            resources[index] = updated_resource
            _write_resources(resources, path)
            return updated_resource

    return None


def delete_resource(
    resource_id: str,
    path: str = "data/resources.json",
) -> bool:
    resources = list_resources(path)
    remaining_resources = [
        resource for resource in resources if resource.id != resource_id
    ]

    if len(remaining_resources) == len(resources):
        return False

    _write_resources(remaining_resources, path)
    return True


def _write_resources(resources: list[Resource], path: str) -> None:
    file_path = Path(path)
    with file_path.open("w", encoding="utf-8") as file:
        json.dump([asdict(resource) for resource in resources], file, indent=2)
        file.write("\n")
