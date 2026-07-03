from celery import Celery

# Connects to the Redis container running locally
celery_app = Celery(
    "orchestrator",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
def process_submission_task(submission_id: int, url: str):
    # TODO: Clone/extract repo, detect language
    # TODO: Dispatch P2 (Code Quality) and P3 (Originality) tasks
    return {"status": "cloning initiated", "submission_id": submission_id}