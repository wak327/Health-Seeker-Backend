from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_lab_result_service
from app.schemas import lab_result as lab_schema
from app.services.lab_result_service import LabResultService

router = APIRouter(prefix="/lab-results", tags=["lab-results"])


@router.post("/", response_model=lab_schema.LabResultPublic, status_code=status.HTTP_201_CREATED)
def create_lab_result(
    lab_in: lab_schema.LabResultCreate,
    service: LabResultService = Depends(get_lab_result_service),
) -> lab_schema.LabResultPublic:
    return service.create(lab_in)


@router.get("/patients/{patient_id}", response_model=list[lab_schema.LabResultPublic])
def list_lab_results(
    patient_id: int,
    service: LabResultService = Depends(get_lab_result_service),
) -> list[lab_schema.LabResultPublic]:
    return service.list_for_patient(patient_id)
