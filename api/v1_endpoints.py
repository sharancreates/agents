import os
import uuid
import json
import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.database import SessionLocal
from api import models
from api.auth import get_current_org, generate_api_key, hash_secret, get_db
from api.billing_service import BillingService
from orchestrator.celery_app import process_submission_task

router = APIRouter(prefix="/v1", tags=["B2B Developer API"])

# --- Request / Response Schemas ---

class CreateEvaluationRequest(BaseModel):
    repo_url: str = Field(..., description="Target repository URL to clone and evaluate.")
    team_name: Optional[str] = Field(default="Participant Team", description="Name of submitting team.")
    challenge_prompt: Optional[str] = Field(default=None, description="Specific hackathon challenge description or rubric prompt.")
    rubric_weights: Optional[Dict[str, float]] = Field(default=None, description="Custom weights: code_quality, functionality, originality, innovation.")
    webhook_url: Optional[str] = Field(default=None, description="Optional callback URL to receive signed evaluation completion events.")
    workspace_slug: Optional[str] = Field(default=None, description="Optional target workspace slug.")

class CreateApiKeyRequest(BaseModel):
    name: str = Field(default="API Key", description="Descriptive label for the API key.")
    scopes: Optional[List[str]] = Field(default=["eval:read", "eval:write"], description="Permissions granted to this key.")

class RegisterWebhookRequest(BaseModel):
    url: str = Field(..., description="Target HTTPS webhook URL.")
    secret: str = Field(..., description="Secret used to generate HMAC-SHA256 signatures.")
    events: Optional[List[str]] = Field(default=["evaluation.completed", "evaluation.failed"])

# --- Endpoints ---

@router.post("/evaluations", status_code=status.HTTP_202_ACCEPTED)
def create_evaluation(
    request: CreateEvaluationRequest,
    auth_ctx: tuple = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Submits a repository for autonomous agent evaluation.
    Associates the run with the caller's organization and dispatches background analysis.
    """
    org, key_record = auth_ctx

    # Quota Gating: Verify sufficient credits (1 credit required per evaluation)
    if not BillingService.has_sufficient_credits(db, org.id, required_credits=1.0):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "INSUFFICIENT_CREDITS",
                "message": "Your organization credit balance is 0. Please top up your balance to run evaluations.",
                "organization_id": org.id,
                "top_up_endpoint": "/v1/billing/orders"
            }
        )

    # Generate sequential submission ID
    max_id_row = db.query(models.Submission.id).order_by(models.Submission.id.desc()).first()
    next_num = (max_id_row[0] + 1) if max_id_row else (db.query(models.Submission).count() + 1)
    sub_id = f"sub_{next_num:03d}"
    while db.query(models.Submission).filter(models.Submission.submission_id == sub_id).first():
        next_num += 1
        sub_id = f"sub_{next_num:03d}"

    # Resolve workspace if requested
    workspace_id = None
    if request.workspace_slug:
        ws = db.query(models.Workspace).filter(
            models.Workspace.organization_id == org.id,
            models.Workspace.slug == request.workspace_slug
        ).first()
        if ws:
            workspace_id = ws.id

    weights = request.rubric_weights or {
        "code_quality": 30.0,
        "functionality": 30.0,
        "originality": 20.0,
        "innovation": 20.0
    }

    pending_dim = {
        "status": "pending",
        "score": None,
        "summary": None,
        "flags": [],
        "started_at": None,
        "completed_at": None
    }

    new_sub = models.Submission(
        submission_id=sub_id,
        organization_id=org.id,
        workspace_id=workspace_id,
        team_name=request.team_name,
        repo_url=request.repo_url,
        commit_sha=str(uuid.uuid4()).replace("-", "")[:40],
        pipeline_status="pending",
        pipeline_started_at=datetime.datetime.now(datetime.timezone.utc),
        rubric_weights=weights,
        webhook_url=request.webhook_url,
        code_quality=pending_dim,
        functionality=pending_dim,
        originality=pending_dim,
        innovation=pending_dim
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)

    # Dispatch to Celery worker pipeline
    process_submission_task.delay(new_sub.id, new_sub.repo_url)

    return {
        "evaluation_id": new_sub.submission_id,
        "organization_slug": org.slug,
        "team_name": new_sub.team_name,
        "status": "pending",
        "created_at": new_sub.pipeline_started_at.isoformat() + "Z"
    }

@router.get("/evaluations/{submission_id}")
def get_evaluation(
    submission_id: str,
    auth_ctx: tuple = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Retrieves the status, metrics, and participant feedback for an evaluation.
    Enforces strict row-level tenant isolation.
    """
    org, _ = auth_ctx

    sub = db.query(models.Submission).filter(
        models.Submission.submission_id == submission_id,
        models.Submission.organization_id == org.id
    ).first()

    if not sub:
        raise HTTPException(status_code=404, detail="Evaluation not found.")

    return {
        "evaluation_id": sub.submission_id,
        "organization_slug": org.slug,
        "team_name": sub.team_name,
        "repo_url": sub.repo_url,
        "commit_sha": sub.commit_sha,
        "status": sub.pipeline_status,
        "overall_score": sub.overall_score,
        "synthesis_summary": sub.synthesis_summary,
        "dimensions": {
            "code_quality": sub.code_quality,
            "functionality": sub.functionality,
            "originality": sub.originality,
            "innovation": sub.innovation
        },
        "participant_feedback": sub.participant_feedback,
        "submitted_at": sub.pipeline_started_at.isoformat() + "Z" if sub.pipeline_started_at else None,
        "completed_at": sub.pipeline_completed_at.isoformat() + "Z" if sub.pipeline_completed_at else None
    }

@router.get("/evaluations/{submission_id}/traces")
def get_evaluation_traces(
    submission_id: str,
    auth_ctx: tuple = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Returns the immutable audit trace events generated by the Agentic Council."""
    org, _ = auth_ctx

    sub = db.query(models.Submission).filter(
        models.Submission.submission_id == submission_id,
        models.Submission.organization_id == org.id
    ).first()

    if not sub:
        raise HTTPException(status_code=404, detail="Evaluation not found.")

    return {
        "evaluation_id": sub.submission_id,
        "traces": sub.agent_traces or []
    }

@router.get("/evaluations/{submission_id}/stream")
def stream_evaluation_events(
    submission_id: str,
    auth_ctx: tuple = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Real-time Server-Sent Events (SSE) streaming endpoint.
    Emits line-delimited events (data: {...}\n\n) as Council agents deliberate.
    """
    org, _ = auth_ctx
    sub = db.query(models.Submission).filter(
        models.Submission.submission_id == submission_id,
        models.Submission.organization_id == org.id
    ).first()

    if not sub:
        raise HTTPException(status_code=404, detail="Evaluation not found.")

    def event_generator():
        sent_trace_count = 0
        current_db = SessionLocal()
        try:
            # Initial event: connection acknowledgment
            init_event = {
                "event": "connected",
                "submission_id": submission_id,
                "status": sub.pipeline_status,
                "overall_score": sub.overall_score
            }
            yield f"data: {json.dumps(init_event)}\n\n"

            # Stream existing traces if any
            traces = sub.agent_traces or []
            for tr in traces:
                msg = {
                    "event": "agent.trace",
                    "submission_id": submission_id,
                    "trace": tr
                }
                yield f"data: {json.dumps(msg)}\n\n"
                sent_trace_count += 1

            # If already completed or failed, emit terminal event
            if sub.pipeline_status in ("complete", "failed"):
                final_event = {
                    "event": "pipeline.complete",
                    "submission_id": submission_id,
                    "status": sub.pipeline_status,
                    "overall_score": sub.overall_score,
                    "verdict": sub.synthesis_summary
                }
                yield f"data: {json.dumps(final_event)}\n\n"
                return

            # If running or pending, stream updates up to max iterations
            import time
            for _ in range(60):
                time.sleep(1.0)
                current_db.expire_all()
                live_sub = current_db.query(models.Submission).filter(
                    models.Submission.submission_id == submission_id
                ).first()
                if not live_sub:
                    break

                live_traces = live_sub.agent_traces or []
                if len(live_traces) > sent_trace_count:
                    for tr in live_traces[sent_trace_count:]:
                        msg = {
                            "event": "agent.trace",
                            "submission_id": submission_id,
                            "trace": tr
                        }
                        yield f"data: {json.dumps(msg)}\n\n"
                    sent_trace_count = len(live_traces)

                if live_sub.pipeline_status in ("complete", "failed"):
                    final_event = {
                        "event": "pipeline.complete",
                        "submission_id": submission_id,
                        "status": live_sub.pipeline_status,
                        "overall_score": live_sub.overall_score,
                        "verdict": live_sub.synthesis_summary
                    }
                    yield f"data: {json.dumps(final_event)}\n\n"
                    break
        finally:
            current_db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# --- API Key Management ---

@router.post("/api-keys")
def create_new_api_key(
    request: CreateApiKeyRequest,
    auth_ctx: tuple = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Issues a new cryptographic API key for the caller's organization."""
    org, _ = auth_ctx
    plaintext_key, key_record = generate_api_key(
        db=db,
        organization_id=org.id,
        name=request.name,
        scopes=request.scopes
    )

    return {
        "id": key_record.id,
        "name": key_record.name,
        "api_key": plaintext_key,
        "key_prefix": key_record.key_prefix,
        "scopes": key_record.scopes,
        "warning": "Store this key in a secure location. It will never be displayed again."
    }

@router.get("/api-keys")
def list_api_keys(
    auth_ctx: tuple = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Lists all active API keys for the organization (masking secrets)."""
    org, _ = auth_ctx
    keys = db.query(models.ApiKey).filter(
        models.ApiKey.organization_id == org.id,
        models.ApiKey.is_active == True
    ).all()

    return [
        {
            "id": k.id,
            "name": k.name,
            "key_prefix": k.key_prefix,
            "scopes": k.scopes,
            "created_at": k.created_at.isoformat() + "Z" if k.created_at else None,
            "last_used_at": k.last_used_at.isoformat() + "Z" if k.last_used_at else None
        }
        for k in keys
    ]

@router.delete("/api-keys/{key_id}")
def revoke_api_key(
    key_id: int,
    auth_ctx: tuple = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Revokes an active API key."""
    org, _ = auth_ctx
    key_record = db.query(models.ApiKey).filter(
        models.ApiKey.id == key_id,
        models.ApiKey.organization_id == org.id
    ).first()

    if not key_record:
        raise HTTPException(status_code=404, detail="API key not found.")

    key_record.is_active = False
    db.commit()
    return {"message": "API key revoked successfully."}

# --- Webhook Management ---

@router.post("/webhooks")
def register_webhook(
    request: RegisterWebhookRequest,
    auth_ctx: tuple = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Registers an external webhook endpoint for HMAC-signed callbacks."""
    org, _ = auth_ctx
    secret_hash = hash_secret(request.secret)

    webhook = models.WebhookEndpoint(
        organization_id=org.id,
        url=request.url,
        secret_hash=secret_hash,
        events=request.events or ["evaluation.completed", "evaluation.failed"],
        is_active=True
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)

    return {
        "id": webhook.id,
        "url": webhook.url,
        "events": webhook.events,
        "status": "registered"
    }

@router.get("/webhooks")
def list_webhooks(
    auth_ctx: tuple = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Lists registered webhook endpoints for caller's organization."""
    org, _ = auth_ctx
    hooks = db.query(models.WebhookEndpoint).filter(
        models.WebhookEndpoint.organization_id == org.id,
        models.WebhookEndpoint.is_active == True
    ).all()

    return [
        {
            "id": h.id,
            "url": h.url,
            "events": h.events,
            "is_active": h.is_active,
            "created_at": h.created_at.isoformat() if h.created_at else None
        }
        for h in hooks
    ]

