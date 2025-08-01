from __future__ import annotations

from typing import Callable

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.schemas.events import DomainEvent
from app.services.event_bus import EventBus

SessionFactory = Callable[[], Session]


EVENTS_TO_AUDIT = {"appointment.created", "appointment.updated", "lab_result.created"}
_REGISTERED = False


def register_audit_subscriber(event_bus: EventBus, session_factory: SessionFactory) -> None:
    global _REGISTERED
    if _REGISTERED:
        return

    def _handler(event: DomainEvent) -> None:
        session = session_factory()
        try:
            audit_log = AuditLog(event_name=event.name, payload=event.payload)
            session.add(audit_log)
            session.commit()
        except Exception:  # pragma: no cover - defensive logging without failing request
            session.rollback()
        finally:
            session.close()

    for event_name in EVENTS_TO_AUDIT:
        event_bus.subscribe(event_name, _handler)

    _REGISTERED = True
