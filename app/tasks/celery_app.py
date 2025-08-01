from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "health_seeker",
    broker=str(settings.celery_broker_url),
    backend=str(settings.celery_result_backend),
)

celery_app.conf.task_routes = {"app.tasks.appointment_tasks.*": {"queue": "appointments"}}
celery_app.conf.beat_schedule = {}
