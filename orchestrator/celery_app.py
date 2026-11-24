import time
import datetime
import os
import logging
from celery import Celery
from sqlalchemy.orm.attributes import flag_modified

from api.database import SessionLocal
from api import models
from agents.council import CouncilOrchestrator

logger = logging.getLogger("OrchestratorCelery")

# Connects to the Redis container running locally
celery_app = Celery(
    "orchestrator",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

@celery_app.task
def process_submission_task(db_submission_id: int, url: str):
    """
    Executes the multi-agent evaluation council on a submission.
    Orchestrates Recon, Dynamic QA Sandbox, Semantic Quality, Forensics,
    Critic Consensus, and Participant Feedback.
    """
    db = SessionLocal()
    sub = None
    try:
        sub = db.query(models.Submission).filter(models.Submission.id == db_submission_id).first()
        if not sub:
            return {"error": "Submission not found", "id": db_submission_id}

        # Transition to Running state
        sub.pipeline_status = "running"
        db.commit()

        # Target repo path: in local development defaults to '.', in cloud workers targets cloned repo
        repo_path = os.getenv("SUBMISSION_REPO_DIR", ".")

        # Convene the Agentic Evaluation Council
        council_state = CouncilOrchestrator.evaluate(
            submission_id=sub.submission_id or str(sub.id),
            repo_path=repo_path,
            repo_url=url,
            challenge_prompt=f"Submission by team {sub.team_name}",
            rubric_weights=sub.rubric_weights
        )

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"

        # Map council dimension evaluations to database fields
        cq_dim = council_state.dimensions.get("code_quality")
        if cq_dim:
            sub.code_quality = {
                "status": "complete",
                "score": cq_dim.score,
                "summary": cq_dim.summary,
                "flags": cq_dim.flags,
                "evidence_citations": cq_dim.evidence_citations,
                "completed_at": now_iso,
                "raw_metrics": cq_dim.raw_metrics
            }
            flag_modified(sub, "code_quality")

        fn_dim = council_state.dimensions.get("functionality")
        if fn_dim:
            sub.functionality = {
                "status": "complete",
                "score": fn_dim.score,
                "summary": fn_dim.summary,
                "flags": fn_dim.flags,
                "evidence_citations": fn_dim.evidence_citations,
                "completed_at": now_iso,
                "raw_metrics": fn_dim.raw_metrics
            }
            flag_modified(sub, "functionality")

        orig_dim = council_state.dimensions.get("originality")
        if orig_dim:
            sub.originality = {
                "status": "complete",
                "score": orig_dim.score,
                "summary": orig_dim.summary,
                "flags": orig_dim.flags,
                "evidence_citations": orig_dim.evidence_citations,
                "completed_at": now_iso,
                "raw_metrics": orig_dim.raw_metrics
            }
            flag_modified(sub, "originality")

        innov_dim = council_state.dimensions.get("innovation")
        if innov_dim:
            sub.innovation = {
                "status": "complete",
                "score": innov_dim.score,
                "summary": innov_dim.summary,
                "flags": innov_dim.flags,
                "evidence_citations": innov_dim.evidence_citations,
                "completed_at": now_iso,
                "raw_metrics": innov_dim.raw_metrics
            }
            flag_modified(sub, "innovation")

        # Map synthesis and feedback
        sub.overall_score = council_state.overall_score
        sub.synthesis_summary = f"Council Consensus: {council_state.verdict} (Composite Score: {council_state.overall_score}/100)"
        
        if council_state.participant_feedback:
            sub.participant_feedback = (
                council_state.participant_feedback.model_dump()
                if hasattr(council_state.participant_feedback, "model_dump")
                else council_state.participant_feedback.dict()
            )
            flag_modified(sub, "participant_feedback")

        # Persist audit traces
        sub.agent_traces = [
            t.model_dump() if hasattr(t, "model_dump") else t.dict()
            for t in council_state.traces
        ]
        flag_modified(sub, "agent_traces")

        sub.pipeline_status = "complete"
        sub.pipeline_completed_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()

        # Metered Billing: Deduct 1 credit for completed evaluation
        if sub.organization_id:
            try:
                from api.billing_service import BillingService
                BillingService.deduct_credit(
                    db=db,
                    org_id=sub.organization_id,
                    submission_id=sub.submission_id,
                    credits=1.0,
                    reason="submission_evaluation"
                )
            except Exception as bill_err:
                logger.warning(f"Could not deduct credit for submission {sub.submission_id}: {bill_err}")

        # Asynchronously dispatch webhook notification if callback URL configured
        if sub.webhook_url:
            try:
                from api.webhook_service import dispatch_webhook_event
                dispatch_webhook_event(
                    webhook_url=sub.webhook_url,
                    secret="autojudge_webhook_secret_key",
                    event_type="evaluation.completed",
                    data={
                        "evaluation_id": sub.submission_id,
                        "overall_score": sub.overall_score,
                        "verdict": council_state.verdict,
                        "status": "complete",
                        "completed_at": sub.pipeline_completed_at.isoformat() + "Z"
                    }
                )
            except Exception as wh_err:
                logger.warning(f"Could not dispatch webhook for submission {sub.submission_id}: {wh_err}")

        return {
            "status": "complete",
            "submission_id": sub.submission_id,
            "overall_score": sub.overall_score,
            "verdict": council_state.verdict,
            "trace_count": len(council_state.traces)
        }

    except Exception as e:
        logger.error(f"Error executing agent council pipeline for submission {db_submission_id}: {e}", exc_info=True)
        if sub:
            sub.pipeline_status = "failed"
            db.commit()
        return {"error": str(e), "submission_id": db_submission_id}
    finally:
        db.close()
