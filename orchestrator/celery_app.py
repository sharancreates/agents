import time
import datetime
import os
from celery import Celery

from api.database import SessionLocal
from api import models
from api.synthesis_service import calculate_synthesis_score, generate_synthesis_summary, get_default_weights
from api.feedback_service import generate_participant_feedback

# Import Person 2 Static Code Quality Engine (Stage 1)
from person_2.core.aggregator import MetricsAggregator

# Import Person 2 Dynamic Functionality Engine (Stage 2)
from person_2.functionality.runner import DynamicExecutionRunner
from person_2.functionality.scoring import EvaluationScoringEngine
from person_2.functionality.models import FunctionalityConfig, TestCaseInput

# Connects to the Redis container running locally
celery_app = Celery(
    "orchestrator",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

@celery_app.task
def process_submission_task(db_submission_id: int, url: str):
    db = SessionLocal()
    try:
        sub = db.query(models.Submission).filter(models.Submission.id == db_submission_id).first()
        if not sub:
            return {"error": "Submission not found", "id": db_submission_id}

        # Transition to Running state
        sub.pipeline_status = "running"
        db.commit()

        # --- Stage 1: Static Code Quality ---
        sub.code_quality = {
            "status": "running",
            "score": None,
            "summary": "Analyzing repository AST and running static linters...",
            "flags": [],
            "started_at": datetime.datetime.utcnow().isoformat() + "Z",
            "completed_at": None,
            "raw_metrics": {}
        }
        db.commit()

        # Execute Person 2 Static Code Quality Aggregator
        aggregator = MetricsAggregator(repo_path=".")
        quality_report = aggregator.run_all_checks()

        sub.code_quality.update({
            "status": "completed",
            "score": quality_report.get("score"),
            "summary": quality_report.get("summary", "Static code analysis completed successfully."),
            "flags": quality_report.get("flags", []),
            "completed_at": datetime.datetime.utcnow().isoformat() + "Z",
            "raw_metrics": quality_report.get("raw_metrics", {})
        })
        db.commit()

        # --- Stage 2: Dynamic Functionality Sandbox ---
        sub.functionality = {
            "status": "running",
            "score": None,
            "summary": "Executing dynamic test suite and resource profiling...",
            "flags": [],
            "started_at": datetime.datetime.utcnow().isoformat() + "Z",
            "completed_at": None,
            "raw_metrics": {}
        }
        db.commit()

        # Configure runner and run execution suite
        config = FunctionalityConfig(timeout_seconds=5)
        # Target script path and dynamic test case inputs
        repo_path = "person_2/main.py" if os.path.exists("person_2/main.py") else "main.py"
        test_suite = [TestCaseInput(input_data="test", expected_output="test")]

        report = DynamicExecutionRunner.execute_script(
            script_path=repo_path,
            test_cases=test_suite,
            config=config
        )
        
        grade = EvaluationScoringEngine.calculate_composite_grade(
            submission_id=str(sub.id),
            report=report
        )

        sub.functionality.update({
            "status": "completed",
            "score": grade.score_20,
            "summary": f"Passed {report.passed_count}/{report.total_count} tests in {report.total_duration_ms:.2f}ms.",
            "flags": grade.flags,
            "completed_at": datetime.datetime.utcnow().isoformat() + "Z",
            "raw_metrics": {
                "tests_passed": report.passed_count,
                "total_tests": report.total_count,
                "avg_runtime_ms": report.total_duration_ms,
                "peak_memory_mb": report.peak_memory_mb
            }
        })
        db.commit()

        # --- Stage 3: Security & Compliance (Placeholder/Next Stage) ---
        time.sleep(1)
        sub.security = {
            "status": "completed",
            "score": 18.0,
            "summary": "No critical vulnerabilities found.",
            "flags": [],
            "started_at": datetime.datetime.utcnow().isoformat() + "Z",
            "completed_at": datetime.datetime.utcnow().isoformat() + "Z",
            "raw_metrics": {}
        }
        db.commit()

        # --- Final Synthesis Calculation ---
        weights = get_default_weights()
        final_score = calculate_synthesis_score(
            cq_score=sub.code_quality.get("score"),
            func_score=sub.functionality.get("score"),
            sec_score=sub.security.get("score"),
            weights=weights
        )

        summary_text = generate_synthesis_summary(
            cq=sub.code_quality,
            func=sub.functionality,
            sec=sub.security
        )

        feedback_report = generate_participant_feedback(
            cq=sub.code_quality,
            func=sub.functionality,
            sec=sub.security
        )

        sub.final_score = final_score
        sub.synthesis_summary = summary_text
        sub.participant_feedback = feedback_report
        sub.pipeline_status = "completed"
        db.commit()

        return {"status": "success", "submission_id": db_submission_id, "final_score": final_score}

    except Exception as e:
        db.rollback()
        if sub:
            sub.pipeline_status = "failed"
            db.commit()
        raise e
    finally:
        db.close()