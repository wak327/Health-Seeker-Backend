.PHONY: run worker init-db format lint

run:
	uvicorn app.main:app --reload --port 8000

worker:
	celery -A app.tasks.celery_app.celery_app worker --loglevel=info --queues=appointments

init-db:
	python -c "from app.db.init_db import init_db; init_db()"
