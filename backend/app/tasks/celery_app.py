from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "careerops",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.search_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # process one task at a time to avoid overlap
    task_routes={
        "app.tasks.search_tasks.run_linkedin_search": {"queue": "linkedin"},
    },
)
