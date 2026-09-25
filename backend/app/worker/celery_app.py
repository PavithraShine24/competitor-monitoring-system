from celery import Celery
from ..config import settings

celery_app = Celery("signalwatch", broker=settings.redis_url, backend=settings.redis_url, include=["app.worker.tasks"])
celery_app.conf.beat_schedule = {"enqueue-enabled-competitors": {"task": "app.worker.tasks.enqueue_enabled", "schedule": settings.polling_interval_seconds}}
celery_app.conf.task_routes = {"app.worker.tasks.*": {"queue": "monitoring"}}
