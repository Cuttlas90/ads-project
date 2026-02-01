import os

from celery import Celery


def _redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://redis:6379/0")


celery_app = Celery("ads_worker", broker=_redis_url(), backend=_redis_url())
celery_app.autodiscover_tasks(["app.worker"])
celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "ton-escrow-watch": {
        "task": "app.worker.ton_watch.scan_escrows",
        "schedule": 60.0,
    }
}
