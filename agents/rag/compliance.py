import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from agents.rag.tools import search_codebase

logger = logging.getLogger("SponsorComplianceAuditor")

# Predefined standard sponsor bounty definitions
STANDARD_SPONSOR_TRACKS = [
    {
        "track_name": "Google Gemini API Integration",
        "query": "Google Gemini client generative AI models Live API bidirectional streaming",
        "mandatory_keywords": ["gemini", "google"],
        "min_threshold": 0.45
    },
    {
        "track_name": "Razorpay Payment & Monetization",
        "query": "Razorpay order checkout payment signature verification webhook paise",
        "mandatory_keywords": ["razorpay"],
        "min_threshold": 0.45
    },
    {
        "track_name": "Redis Distributed Cache & Broker",
        "query": "Redis Celery broker caching key value connection",
        "mandatory_keywords": ["redis"],
        "min_threshold": 0.45
    }
]

class SponsorComplianceAuditor:
    """
    Audits codebase vector index against hackathon sponsor track requirements.
    Confirms genuine architectural adoption with confidence scores and line citations.
    """

    @classmethod
    def audit_track(
        cls,
        db: Session,
        submission_id: str,
        track_name: str,
        query: str,
        mandatory_keywords: Optional[List[str]] = None,
        min_threshold: float = 0.45
    ) -> Dict[str, Any]:
        """
        Audits a single sponsor track requirement against indexed code embeddings.
        """
        results = search_codebase(
            db=db,
            submission_id=submission_id,
            query=query,
            top_k=5,
            min_score=0.0
        )

        if not results:
            return {
                "track_name": track_name,
                "requirement_query": query,
                "is_compliant": False,
                "confidence_score": 0.0,
                "reason": "No relevant codebase vectors found for this submission.",
                "evidence": []
            }

        top_score = results[0]["score"]

        # Keyword verification across retrieved chunks
        keyword_match = True
        if mandatory_keywords:
            combined_text = " ".join([r["content"].lower() for r in results])
            keyword_match = any(kw.lower() in combined_text for kw in mandatory_keywords)

        is_compliant = (top_score >= min_threshold) and keyword_match

        evidence = [
            {
                "citation": r["citation"],
                "file_path": r["file_path"],
                "lines": f"{r['start_line']}-{r['end_line']}",
                "symbol_name": r["symbol_name"],
                "symbol_type": r["symbol_type"],
                "similarity_score": r["score"],
                "snippet": r["content"][:250].strip()
            }
            for r in results[:3]
        ]

        return {
            "track_name": track_name,
            "requirement_query": query,
            "is_compliant": is_compliant,
            "confidence_score": top_score,
            "evidence": evidence
        }

    @classmethod
    def audit_all_tracks(
        cls,
        db: Session,
        submission_id: str,
        custom_tracks: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Audits submission against standard sponsor tracks and custom hackathon rules.
        """
        tracks = custom_tracks or STANDARD_SPONSOR_TRACKS
        reports = []
        for trk in tracks:
            rep = cls.audit_track(
                db=db,
                submission_id=submission_id,
                track_name=trk["track_name"],
                query=trk.get("query", trk.get("requirement_text", "")),
                mandatory_keywords=trk.get("mandatory_keywords"),
                min_threshold=trk.get("min_threshold", 0.45)
            )
            reports.append(rep)
        return reports
