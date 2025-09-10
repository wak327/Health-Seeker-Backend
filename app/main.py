from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import appointments, auth, doctors, lab_results, patients, tasks, users
from app.core.config import get_settings
from app.core.events import event_bus
from app.db.session import SessionLocal
from app.subscribers.audit import register_audit_subscriber

settings = get_settings()

app = FastAPI(title=settings.project_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(doctors.router, prefix=settings.api_v1_prefix)
app.include_router(patients.router, prefix=settings.api_v1_prefix)
app.include_router(appointments.router, prefix=settings.api_v1_prefix)
app.include_router(lab_results.router, prefix=settings.api_v1_prefix)
app.include_router(tasks.router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def startup_event() -> None:
    if settings.enable_event_subscribers:
        register_audit_subscriber(event_bus, SessionLocal)


@app.get("/", tags=["system"])
def read_root() -> dict[str, str]:
    return {"status": "ok", "service": settings.project_name}
