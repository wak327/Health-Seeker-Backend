from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_background_task_service
from app.schemas import background_task as task_schema
from app.services.background_task_service import BackgroundTaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=task_schema.BackgroundTaskPublic)
def get_task(
    task_id: int,
    service: BackgroundTaskService = Depends(get_background_task_service),
) -> task_schema.BackgroundTaskPublic:
    task = service.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get(
    "/appointments/{appointment_id}",
    response_model=list[task_schema.BackgroundTaskPublic],
)
def list_tasks_for_appointment(
    appointment_id: int,
    service: BackgroundTaskService = Depends(get_background_task_service),
) -> list[task_schema.BackgroundTaskPublic]:
    return service.list_for_appointment(appointment_id)
