import os

from celery import Celery


def _redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://redis:6379/0")


celery_app = Celery("ads_worker", broker=_redis_url(), backend=_redis_url())
