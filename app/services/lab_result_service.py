from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.lab_result import LabResult
from app.schemas import lab_result as lab_result_schema
from app.services.event_bus import EventBus


class LabResultService:
    def __init__(self, session: Session, event_bus: EventBus) -> None:
        self.session = session
        self.event_bus = event_bus

    def create(self, lab_in: lab_result_schema.LabResultCreate) -> LabResult:
        lab_result = LabResult(
            patient_id=lab_in.patient_id,
            test_name=lab_in.test_name,
            result_data=lab_in.result_data,
            recorded_at=lab_in.recorded_at,
        )
        self.session.add(lab_result)
        self.session.commit()
        self.session.refresh(lab_result)

        self.event_bus.publish(
            "lab_result.created",
            {
                "lab_result_id": lab_result.id,
                "patient_id": lab_result.patient_id,
                "test_name": lab_result.test_name,
            },
        )
        return lab_result

    def list_for_patient(self, patient_id: int) -> List[LabResult]:
        return (
            self.session.query(LabResult)
            .filter(LabResult.patient_id == patient_id)
            .order_by(LabResult.recorded_at.desc())
            .all()
        )
