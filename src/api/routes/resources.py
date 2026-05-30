from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from src.api.schemas import ResourceCreate, ResourceResponse, ResourceUpdate
from src.models.resource import Resource
from src.repositories.resource_repository import (
    create_resource,
    delete_resource,
    get_resource,
    list_resources,
    update_resource,
)

router = APIRouter()


@router.get("", response_model=list[ResourceResponse])
def get_resources() -> list[dict]:
    return [asdict(resource) for resource in list_resources()]


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource_by_id(resource_id: str) -> dict:
    resource = get_resource(resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found.")

    return asdict(resource)


@router.post("", response_model=ResourceResponse)
def post_resource(payload: ResourceCreate) -> dict:
    # TODO: Validate that prerequisite resource ids exist.
    try:
        resource = create_resource(Resource(**_model_dump(payload)))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return asdict(resource)


@router.put("/{resource_id}", response_model=ResourceResponse)
def put_resource(resource_id: str, payload: ResourceUpdate) -> dict:
    # TODO: Validate that prerequisite resource ids exist.
    resource = update_resource(resource_id, _model_dump(payload))
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found.")

    return asdict(resource)


@router.delete("/{resource_id}")
def delete_resource_by_id(resource_id: str) -> dict:
    deleted = delete_resource(resource_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resource not found.")

    return {"deleted": True, "resource_id": resource_id}


def _model_dump(model) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()
