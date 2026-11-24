import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentTraceEvent(BaseModel):
    """Immutable audit trace of an autonomous agent decision, perception, or tool invocation."""
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z")
    agent_role: str
    action: str
    reasoning: str
    details: Dict[str, Any] = Field(default_factory=dict)

class EnvironmentBlueprint(BaseModel):
    """Autonomous discovery findings describing the target repository environment."""
    primary_language: str = "unknown"
    framework: Optional[str] = None
    manifest_files: List[str] = Field(default_factory=list)
    entrypoint_script: Optional[str] = None
    all_entrypoint_candidates: List[str] = Field(default_factory=list)
    readme_summary: str = ""
    challenge_spec: Optional[str] = None
    total_files_discovered: int = 0

class DimensionEvaluation(BaseModel):
    """The scored evaluation produced by a specialized council agent."""
    dimension: str  # "functionality", "code_quality", "originality", "innovation"
    score: float    # 0.0 to 100.0
    summary: str
    flags: List[str] = Field(default_factory=list)
    evidence_citations: List[str] = Field(default_factory=list)
    raw_metrics: Dict[str, Any] = Field(default_factory=dict)

class ParticipantFeedbackPackage(BaseModel):
    """Constructive, participant-facing coaching report."""
    status: str = "complete"
    overall_summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    growth_areas: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class CouncilState(BaseModel):
    """Central state graph model passed across all Agentic Council nodes."""
    submission_id: str
    repo_path: str
    repo_url: Optional[str] = None
    challenge_prompt: Optional[str] = None
    rubric_weights: Dict[str, float] = Field(default_factory=lambda: {
        "code_quality": 30.0,
        "functionality": 30.0,
        "originality": 20.0,
        "innovation": 20.0
    })
    environment: Optional[EnvironmentBlueprint] = None
    generated_tests: List[Dict[str, Any]] = Field(default_factory=list)
    dimensions: Dict[str, DimensionEvaluation] = Field(default_factory=dict)
    critic_notes: List[str] = Field(default_factory=list)
    overall_score: Optional[float] = None
    verdict: Optional[str] = None
    participant_feedback: Optional[ParticipantFeedbackPackage] = None
    traces: List[AgentTraceEvent] = Field(default_factory=list)

    def add_trace(self, agent_role: str, action: str, reasoning: str, details: Optional[Dict[str, Any]] = None):
        """Append an audit trace event to the execution history."""
        self.traces.append(AgentTraceEvent(
            agent_role=agent_role,
            action=action,
            reasoning=reasoning,
            details=details or {}
        ))
