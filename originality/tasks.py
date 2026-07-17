import os
from celery.utils.log import get_task_logger

# Import Celery application instance
try:
    from originality.celery_app import app
except ImportError:
    from celery_app import app

# Import core executors
try:
    from originality.pipeline import process_codebase_pipeline
    from originality.architecture_evaluator import ArchitectureEvaluator
except ImportError:
    from pipeline import process_codebase_pipeline
    from architecture_evaluator import ArchitectureEvaluator

logger = get_task_logger(__name__)

@app.task(bind=True, max_retries=3, default_retry_delay=15)
def process_repository_task(self, directory_path: str, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 32):
    """
    Asynchronous Celery task wrapping the AST parsing, normalization,
    and bulk vector generation pipeline.
    """
    logger.info(f"[Task] Starting codebase index loop on directory: {directory_path}")
    try:
        # Run pipeline
        process_codebase_pipeline(directory_path, model_name=model_name, batch_size=batch_size)
        logger.info(f"[Task] Successfully indexed codebase directory: {directory_path}")
        return {"status": "SUCCESS", "directory": directory_path}
    except Exception as e:
        logger.error(f"[Task] Error during repository indexing: {e}")
        # Retry in case of temporary connection losses
        try:
            self.retry(exc=e)
        except Exception as retry_exc:
            logger.error(f"[Task] Max retries exceeded for {directory_path}: {retry_exc}")
            raise e

@app.task(bind=True, max_retries=3, default_retry_delay=15)
def evaluate_architecture_task(self, directory_path: str):
    """
    Asynchronous Celery task wrapping the repository structural
    architecture evaluation via Claude.
    """
    logger.info(f"[Task] Starting architecture evaluation on directory: {directory_path}")
    try:
        # Run evaluation
        profile = ArchitectureEvaluator.evaluate_repository(directory_path)
        logger.info(f"[Task] Successfully analyzed architecture profile for: {directory_path}")
        return {"status": "SUCCESS", "profile": profile}
    except Exception as e:
        logger.error(f"[Task] Error during architecture analysis: {e}")
        try:
            self.retry(exc=e)
        except Exception as retry_exc:
            logger.error(f"[Task] Max retries exceeded for {directory_path}: {retry_exc}")
            raise e
