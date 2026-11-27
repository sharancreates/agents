import time
import datetime
import os
import logging
import tempfile
import subprocess
import shutil
import hashlib
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
    cloned_tmp_dir = None
    try:
        sub = db.query(models.Submission).filter(models.Submission.id == db_submission_id).first()
        if not sub:
            return {"error": "Submission not found", "id": db_submission_id}

        # Transition to Running state
        sub.pipeline_status = "running"
        db.commit()

        # Target repo path: clone remote git repository or use verified directory
        if url and (url.startswith("http://") or url.startswith("https://") or url.startswith("git@")):
            cloned_tmp_dir = tempfile.TemporaryDirectory(prefix=f"eval_repo_{sub.submission_id}_")
            try:
                clone_res = subprocess.run(
                    ["git", "clone", "--depth", "1", "--single-branch", url, cloned_tmp_dir.name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=60.0
                )
                if clone_res.returncode == 0:
                    repo_path = cloned_tmp_dir.name
                else:
                    logger.warning(f"Git clone failed for {url}: {clone_res.stderr}. Using fallback repo dir.")
                    repo_path = os.getenv("SUBMISSION_REPO_DIR", ".")
            except Exception as clone_err:
                logger.warning(f"Error cloning repository {url}: {clone_err}. Using fallback.")
                repo_path = os.getenv("SUBMISSION_REPO_DIR", ".")
        elif url and os.path.isdir(url):
            repo_path = url
        else:
            repo_path = os.getenv("SUBMISSION_REPO_DIR", ".")

        # Convene the Agentic Evaluation Council
        council_state = CouncilOrchestrator.evaluate(
            submission_id=sub.submission_id or str(sub.id),
            repo_path=repo_path,
            repo_url=url,
            challenge_prompt=f"Submission by team {sub.team_name}",
            rubric_weights=sub.rubric_weights
        )

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

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

        # Asynchronously dispatch webhook notification if callback URL configured
        if sub.webhook_url:
            try:
                from api.webhook_service import dispatch_webhook_event
                # Retrieve specific signing secret registered for this endpoint
                endpoint = db.query(models.WebhookEndpoint).filter(
                    models.WebhookEndpoint.organization_id == sub.organization_id,
                    models.WebhookEndpoint.url == sub.webhook_url,
                    models.WebhookEndpoint.is_active == True
                ).first()

                if endpoint and endpoint.signing_secret:
                    webhook_secret = endpoint.signing_secret
                else:
                    webhook_secret = hashlib.sha256(
                        f"webhook_sec_{sub.organization_id}_{os.getenv('APP_SECRET', 'default_sec')}".encode()
                    ).hexdigest()

                dispatch_webhook_event(
                    webhook_url=sub.webhook_url,
                    secret=webhook_secret,
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
            # Refund reserved credit on internal execution failure
            if sub.organization_id:
                try:
                    account = db.query(models.OrganizationCredit).filter(
                        models.OrganizationCredit.organization_id == sub.organization_id
                    ).first()
                    if account:
                        account.balance += 1.0
                        db.commit()
                except Exception:
                    pass
        return {"error": str(e), "submission_id": db_submission_id}
    finally:
        if cloned_tmp_dir:
            try:
                cloned_tmp_dir.cleanup()
            except Exception:
                pass
        db.close()
