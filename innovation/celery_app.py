import os
from celery import Celery

# Redis configuration defaults
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Setup task namespace registration
include_modules = ["tasks"]
try:
    # Test namespace import
    import originality.tasks
    include_modules = ["originality.tasks"]
except ImportError:
    pass

# Initialize Celery app
app = Celery(
    "originality_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=include_modules
)

# Celery Configuration Settings
app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Broker Connection Retry Strategy
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=5,
    # Task Timeout Limits (to prevent stalled workers)
    task_time_limit=600,
    task_soft_time_limit=500,
    # Worker Settings
    worker_concurrency=4
)

if __name__ == "__main__":
    app.start()
