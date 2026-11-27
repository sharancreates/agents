import os
import logging
import tempfile
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api import models
from api.auth import get_current_org, get_db, require_scope
from agents.rag.indexer import CodebaseIndexer
from agents.rag.tools import search_codebase
from agents.rag.compliance import SponsorComplianceAuditor

logger = logging.getLogger("RAGEndpoints")

router = APIRouter(prefix="/v1/evaluations", tags=["Codebase RAG & Judge Copilot"])

# --- Request / Response Schemas ---

class IndexCodebaseRequest(BaseModel):
    repo_path: Optional[str] = Field(default=None, description="Local path to repository directory.")

class CopilotChatRequest(BaseModel):
    question: str = Field(..., description="Technical question regarding this submission's implementation.")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of supporting code citations to retrieve.")

# --- Endpoints ---

@router.post("/{submission_id}/index", status_code=status.HTTP_200_OK)
def index_submission_codebase(
    submission_id: str,
    request: IndexCodebaseRequest = IndexCodebaseRequest(),
    auth_ctx: tuple = Depends(require_scope("eval:write")),
    db: Session = Depends(get_db)
):
    """
    Parses and semantically indexes a submission's codebase into the vector database.
    Confines target path within authorized submission directories to prevent arbitrary indexing.
    """
    org, _ = auth_ctx
    sub = db.query(models.Submission).filter(
        models.Submission.submission_id == submission_id,
        models.Submission.organization_id == org.id
    ).first()

    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found.")

    # Confinement check with symlink resolution to prevent arbitrary host file indexing
    allowed_base = os.path.realpath(os.getenv("SUBMISSION_REPO_DIR", "."))
    if request.repo_path:
        requested_real = os.path.realpath(request.repo_path)
        try:
            is_under_base = (os.path.commonpath([allowed_base, requested_real]) == allowed_base)
        except ValueError:
            is_under_base = False

        trusted_temp_root = os.path.realpath(tempfile.gettempdir())
        try:
            is_under_temp = (os.path.commonpath([trusted_temp_root, requested_real]) == trusted_temp_root)
        except ValueError:
            is_under_temp = False

        # Only allow paths strictly under allowed base directory or explicit eval_repo_* directory inside tempdir
        is_safe_eval_dir = is_under_temp and os.path.basename(requested_real).startswith("eval_repo_")
        if not (is_under_base or is_safe_eval_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security policy violation: repo_path must be confined within the authorized submission directory."
            )
        target_path = requested_real
    else:
        target_path = allowed_base

    try:
        result = CodebaseIndexer.index_submission(db, submission_id, target_path)
        return result
    except Exception as e:
        logger.error(f"Failed to index codebase for {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )

@router.post("/{submission_id}/chat")
def chat_with_submission(
    submission_id: str,
    request: CopilotChatRequest,
    auth_ctx: tuple = Depends(require_scope("eval:read")),
    db: Session = Depends(get_db)
):
    """
    Judge Copilot: Interactive conversational Q&A endpoint.
    Answers technical questions backed by line-numbered code evidence from the vector index.
    """
    org, _ = auth_ctx
    sub = db.query(models.Submission).filter(
        models.Submission.submission_id == submission_id,
        models.Submission.organization_id == org.id
    ).first()

    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found.")

    # 1. Retrieve top relevant code chunks
    chunks = search_codebase(
        db=db,
        submission_id=submission_id,
        query=request.question,
        top_k=request.top_k,
        min_score=0.0
    )

    if not chunks:
        return {
            "submission_id": submission_id,
            "question": request.question,
            "answer": "No relevant codebase vectors found. Please index the submission repository first via POST /v1/evaluations/{id}/index.",
            "citations": []
        }

    # 2. Synthesize evidence-grounded response
    top_chunk = chunks[0]
    symbols_found = [c["symbol_name"] for c in chunks if c.get("symbol_name")]
    symbols_summary = ", ".join(f"`{s}`" for s in symbols_found[:3]) if symbols_found else "relevant code blocks"

    answer_parts = [
        f"Based on repository analysis for submission `{submission_id}`:",
        f"The implementation relevant to '{request.question}' was identified primarily in `{top_chunk['file_path']}` (lines {top_chunk['start_line']}-{top_chunk['end_line']}), spanning {symbols_summary}.",
        f"Key Implementation Logic:\n```\n{top_chunk['content'][:400].strip()}\n```",
        f"Verification Confidence: {round(top_chunk['score'] * 100, 1)}% match with query semantics."
    ]
    answer = "\n\n".join(answer_parts)

    citations = [
        {
            "citation": c["citation"],
            "file_path": c["file_path"],
            "lines": f"{c['start_line']}-{c['end_line']}",
            "symbol_name": c["symbol_name"],
            "symbol_type": c["symbol_type"],
            "similarity_score": c["score"],
            "snippet": c["content"][:200].strip()
        }
        for c in chunks
    ]

    return {
        "submission_id": submission_id,
        "question": request.question,
        "answer": answer,
        "citations": citations
    }

@router.get("/{submission_id}/compliance")
def check_sponsor_compliance(
    submission_id: str,
    track: Optional[str] = None,
    auth_ctx: tuple = Depends(require_scope("eval:read")),
    db: Session = Depends(get_db)
):
    """
    Audits submission code embeddings against sponsor track and hackathon rubric requirements.
    """
    org, _ = auth_ctx
    sub = db.query(models.Submission).filter(
        models.Submission.submission_id == submission_id,
        models.Submission.organization_id == org.id
    ).first()

    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found.")

    reports = SponsorComplianceAuditor.audit_all_tracks(db, submission_id)
    if track:
        reports = [r for r in reports if track.lower() in r["track_name"].lower()]

    return {
        "submission_id": submission_id,
        "total_tracks_evaluated": len(reports),
        "compliant_tracks_count": sum(1 for r in reports if r["is_compliant"]),
        "reports": reports
    }
