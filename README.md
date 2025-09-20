# Health-Seeker Backend

Health-Seeker Backend is a FastAPI service that orchestrates healthcare workflows across superadmins, doctors, and patients. It exposes a secured REST API with JWT bearer authentication, role-aware authorization, appointment automation, and audit-friendly background processing.

---

## Core Capabilities

- Role-driven access controls guarding every endpoint (superadmin, doctor, patient).
- JWT bearer login flow with configurable secrets and token lifetimes.
- Doctor profiles, availability schedules, and capacity-aware appointment booking.
- Patient profiles and discovery endpoints for finding available doctors by speciality and time.
- Superadmin tooling to onboard and manage users with enforced uniqueness and activity flags.
- Background task orchestration and event publication to confirm appointments asynchronously.

---

## Architecture Overview

- **FastAPI** hosts versioned REST endpoints under `/api/v1`.
- **SQLAlchemy 2.x** models PostgreSQL tables for users, doctor/patient profiles, schedules, and appointments.
- **Celery + Redis** handle asynchronous appointment confirmation tasks.
- **In-memory event bus** broadcasts domain events that subscribers persist for audit trails.
- **Pydantic v2** schemas provide request/response validation with `from_attributes=True` ORM support.

The project is intentionally modular: routers expose HTTP contracts, services encapsulate business logic, and models/schemas express shared healthcare concepts.

---

## Prerequisites

- Python 3.11+
- PostgreSQL 15 (local install or container)
- Redis 7 (for Celery workers)
- Optional: Docker & docker-compose for single-command bootstrapping

---

## Local Development Setup

1. **Clone & install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Update at minimum:
   - `DATABASE_URL` – points at your PostgreSQL instance.
   - `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` – Redis endpoints.
   - `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` – auth secrets.
   - (Optional) `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD`, `SUPERADMIN_FULL_NAME` to auto-seed a superadmin during init.

3. **Run PostgreSQL (if needed)**
   ```bash
   docker run --name health-seeker-postgres \
     -p 5432:5432 \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=health_seeker \
     -d postgres:15-alpine
   ```

4. **Provision the database schema**
   ```bash
   make init-db
   # or
   python -c "from app.db.init_db import init_db; init_db()"
   ```
   This creates all tables and, when superadmin credentials are provided, seeds a default superadmin user.

5. **Run the FastAPI application**
   ```bash
   make run
   # Uvicorn serves on http://127.0.0.1:8000
   ```
   Interactive documentation is available at `http://127.0.0.1:8000/docs`.

6. **Start the Celery worker** (optional for async tasks)
   ```bash
   make worker
   # or docker compose up worker
   ```
   The worker processes `schedule_appointment` jobs and updates background task records.

---

## Docker Compose Quickstart

A compose file is provided for local parity with production.

```bash
docker compose up --build
```

Services:
- `api` – FastAPI + Uvicorn (port 8000)
- `worker` – Celery worker consuming appointment tasks
- `postgres` – PostgreSQL 15 with initial schema
- `redis` – Redis broker/result backend

Stop the stack with `docker compose down`. Remove persisted volumes if necessary: `docker volume rm health-seeker-backend_postgres-data`.

---

## Authentication & Roles

- **Login**: `POST /api/v1/auth/login` with email/password returns a bearer token and user payload.
- **Bearer usage**: Include `Authorization: Bearer <token>` on subsequent requests.
- **Roles**:
  - `superadmin` – full administrative rights; can create/update any user, inspect appointments, and act on behalf of patients.
  - `doctor` – manage their profile, schedules, and appointments they are assigned to.
  - `patient` – manage their profile, discover doctors, and book appointments for themselves.
- Users are marked `is_active`; inactive accounts are denied authentication.

The FastAPI dependencies in `app/api/dependencies.py` enforce role gates (`require_superadmin`, `require_doctor`, `require_patient`) to keep handlers concise.

---

## Typical Workflows

### Superadmin Onboarding
1. Authenticate with the seeded superadmin credentials.
2. `POST /api/v1/users/` to create doctors or patients (password hashed automatically).
3. Share credentials with end-users; they login via `/auth/login`.

### Doctor Availability & Appointment Management
1. Doctor logs in and sets up their profile via `PUT /api/v1/doctors/me/profile`.
2. Publish availability windows using `POST /api/v1/doctors/me/schedules`.
3. Review upcoming appointments with `GET /api/v1/doctors/me/appointments`.
4. Update appointment status, notes, diagnosis, or prescriptions through `PATCH /api/v1/appointments/{id}`.

### Patient Discovery & Booking
1. Patient updates their profile through `PUT /api/v1/patients/me/profile`.
2. Discover suitable doctors with `GET /api/v1/patients/doctors?specialization=cardiology`.
3. Inspect schedule slots via `GET /api/v1/patients/doctors/{doctor_user_id}/schedules`.
4. Book an appointment using `POST /api/v1/appointments/` (requires schedule id and reason).
5. Track personal appointments with `GET /api/v1/patients/me/appointments`.

### Appointment Lifecycle
- Booking triggers an appointment record with `pending` status.
- A background task enqueues confirmation logic (via Celery) and publishes `appointment.created` events.
- Doctors or superadmins can update statuses (`confirmed`, `completed`, `cancelled`), add notes, diagnoses, and prescriptions.

---

## Background Tasks & Events

- Creating an appointment stores a `BackgroundTaskRecord` and optionally dispatches a Celery job (`schedule_appointment_task`).
- Events emitted by `EventBus` include `appointment.created` and `appointment.updated` with contextual payloads.
- Audit subscribers persist events to an `audit_logs` table for compliance and observability.

---

## Project Layout

```
app/
├── api/               # FastAPI routers and dependency wiring
├── core/              # Settings, security helpers, event bus
├── db/                # SQLAlchemy session management and bootstrap
├── models/            # ORM models (users, profiles, schedules, appointments, tasks)
├── schemas/           # Pydantic models for requests/responses
├── services/          # Business logic, auth, scheduling, event orchestration
├── subscribers/       # Event subscribers (audit logging, etc.)
└── tasks/             # Celery configuration and background jobs
```

---

## Testing & Tooling

- Static type hints are provided across the codebase. Add `mypy`/`ruff` as needed for stricter linting.
- Use `python -m compileall app` (already part of CI scripts) or integrate `pytest` for behavioural coverage.

---

## Extending the Service

- Introduce fine-grained permissions (e.g., per-clinic scoping) atop the current role model.
- Replace the in-memory event bus with Kafka, RabbitMQ, or another distributed broker for multi-service deployments.
- Add notification subscribers (email/SMS) responding to appointment lifecycle events.
- Layer on analytics dashboards consuming the audit/event stream.

Health-Seeker Backend demonstrates how a pragmatic, event-driven FastAPI stack can support clinical-grade scheduling, traceability, and secure access control in a single service.
