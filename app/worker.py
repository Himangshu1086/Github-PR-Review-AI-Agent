from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_BROKER = os.getenv("REDIS_BROKER_URL")

celery_app = Celery(
    "code_review_tasks",
    broker=REDIS_BROKER,
    backend=REDIS_BROKER
)

celery_app.autodiscover_tasks(['app'])
