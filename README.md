# Health-Seeker-Backend

Health-Seeker-Backend is a FastAPI service that models a healthcare orchestration layer. It exposes REST endpoints for patients, doctors, and admins, records lab results, and coordinates appointment workflows through background workers and event subscribers.

---

## Highlights

- FastAPI application with automatic OpenAPI/Swagger docs
- PostgreSQL persistence via SQLAlchemy ORM and Pydantic models
- Celery + Redis background workers for long-running appointment tasks
- In-memory event bus with subscribers that persist an audit trail
- Docker-first deployment with dedicated services for the API, worker, Redis, and PostgreSQL

---

## Tech Stack

- Python 3.11
- FastAPI, Uvicorn
- SQLAlchemy 2.x, PostgreSQL
- Pydantic v2, pydantic-settings
- Celery 5, Redis 7
- Docker & docker-compose (optional)

---

## Local Development Setup

Follow these steps to boot the service locally without containers:

1. **Create a virtual environment and install dependencies**
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
   Update `DATABASE_URL`, `CELERY_BROKER_URL`, and `CELERY_RESULT_BACKEND` if you are not running PostgreSQL and Redis on `localhost`.

3. **Run PostgreSQL in Docker**
   ```bash
   docker run --name health-seeker-postgres \
     -p 5432:5432 \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=health_seeker \
     -d postgres:15-alpine
   ```
   With this container running, configure `DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/health_seeker` in your `.env`. Stop it via `docker stop health-seeker-postgres` and remove with `docker rm health-seeker-postgres` when finished.

4. **Provision the database schema**
   ```bash
   make init-db
   ```
   (Without `make`: `python -c "from app.db.init_db import init_db; init_db()"`)

5. **Run the FastAPI application**
   ```bash
   make run
   ```
   The API becomes available at `http://127.0.0.1:8000`. Interactive documentation lives at `http://127.0.0.1:8000/docs`.

6. **Start the background worker**
   - Local process (uses the current virtualenv):
     ```bash
     make worker
     ```
   - Dockerised worker (runs Celery inside a container alongside Dockerised dependencies):
     ```bash
     docker compose up --build worker
     ```
   The worker confirms appointments asynchronously and updates background task records.

---

## Docker Compose Setup

A fully containerised workflow is provided for parity with production-like environments.

```bash
docker compose up --build
```

Services launched:

- `api` – FastAPI application served by Uvicorn on port `8000`
- `worker` – Celery worker consuming the `appointments` queue
- `postgres` – PostgreSQL 15 instance seeded with a `health_seeker` database
- `redis` – Redis broker for Celery

Once the stack is healthy:

- Visit `http://localhost:8000/docs` for the interactive API explorer.
- Use `docker compose down` to stop the stack and `docker volume ls`/`docker volume rm` to manage the persisted PostgreSQL volume if needed.

---

## Example Workflow

1. Create a patient via `POST /api/v1/users/`.
2. Schedule an appointment with `POST /api/v1/appointments/`.
3. Track background execution using `GET /api/v1/tasks/appointments/{appointment_id}`.
4. Add lab results using `POST /api/v1/lab-results/`.
5. Inspect audit entries written by subscribers in the `audit_logs` table.

---

## API Surface

All endpoints are namespaced under `/api/v1`.

- `POST /api/v1/users/` – Register a new user (patient, doctor, or admin)
- `GET /api/v1/users/{id}` – Retrieve profile information
- `POST /api/v1/appointments/` – Schedule an appointment and enqueue background processing
- `PATCH /api/v1/appointments/{id}` – Update notes, schedule, or status
- `GET /api/v1/appointments/patients/{patient_id}` – View a patient’s appointments
- `GET /api/v1/appointments/doctors/{doctor_id}` – View a doctor’s appointments
- `POST /api/v1/lab-results/` – Persist lab results and publish an event
- `GET /api/v1/tasks/appointments/{appointment_id}` – Monitor background task records

---

## Project Layout

```
app/
├── api/               # FastAPI routers and dependency wiring
├── core/              # Settings, security helpers, global event bus
├── db/                # SQLAlchemy session management and bootstrap scripts
├── models/            # ORM models representing domain entities
├── schemas/           # Pydantic request/response schemas
├── services/          # Domain logic, event publication, task orchestration
├── subscribers/       # Event subscribers (audit logging, etc.)
└── tasks/             # Celery application and task definitions
```

---

## Background Tasks & Events

- Appointment creation writes a `BackgroundTaskRecord` and enqueues `schedule_appointment_task`.
- The Celery worker confirms appointments and updates task status transitions (`queued → running → succeeded/failed`).
- An in-memory `EventBus` publishes domain events (`appointment.created`, `appointment.updated`, `lab_result.created`).
- Audit subscribers listen for these events and persist payloads into the `audit_logs` table for traceability.

---

## Extending the Service

- Swap in JWT authentication or OAuth guards around the routers.
- Introduce role-based permission checks within the services.
- Add more subscribers (e.g., notification delivery, analytics sinks).
- Replace the simple event bus with a distributed broker if cross-service communication is required.

Health-Seeker-Backend illustrates how a pragmatic, event-driven FastAPI stack can underpin healthcare-grade workflows that demand reliability, auditability, and asynchronous processing.
