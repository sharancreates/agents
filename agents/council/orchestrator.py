import logging
from typing import Optional, Dict, Any
from agents.council.state import CouncilState
from agents.council.recon_agent import ReconAgent
from agents.council.qa_agent import QAAgent
from agents.council.quality_agent import QualityAgent
from agents.council.forensics_agent import ForensicsAgent
from agents.council.critic_agent import CriticAgent
from agents.council.feedback_agent import FeedbackCoach

logger = logging.getLogger("CouncilOrchestrator")

class CouncilOrchestrator:
    """
    Central Coordinator for the Agentic Evaluation Council.
    Drives state transitions through the Recon, QA, Quality, Forensics,
    Critic, and Feedback agents.
    """

    @classmethod
    def evaluate(
        cls,
        submission_id: str,
        repo_path: str,
        repo_url: Optional[str] = None,
        challenge_prompt: Optional[str] = None,
        rubric_weights: Optional[Dict[str, float]] = None
    ) -> CouncilState:
        logger.info(f"[COUNCIL] Starting multi-agent evaluation for {submission_id} on {repo_path}")

        # Initialize central state
        state = CouncilState(
            submission_id=submission_id,
            repo_path=repo_path,
            repo_url=repo_url,
            challenge_prompt=challenge_prompt,
            rubric_weights=rubric_weights or {
                "code_quality": 30.0,
                "functionality": 30.0,
                "originality": 20.0,
                "innovation": 20.0
            }
        )

        state.add_trace(
            agent_role="CouncilOrchestrator",
            action="INITIALIZE",
            reasoning=f"Council convened for submission '{submission_id}'."
        )

        # 1. Reconnaissance Node
        ReconAgent.analyze_repository(state)

        # 2. Dynamic QA Node
        QAAgent.synthesize_and_execute(state)

        # 3. Semantic Quality Node
        QualityAgent.evaluate_quality(state)

        # 4. Forensics & Originality Node
        ForensicsAgent.analyze_forensics(state)

        # 5. Critic & Consensus Adjudication Node
        CriticAgent.adjudicate_and_synthesize(state)

        # 6. Participant Feedback Coaching Node
        FeedbackCoach.generate_coaching_package(state)

        state.add_trace(
            agent_role="CouncilOrchestrator",
            action="EVALUATION_FINISHED",
            reasoning=f"Evaluation completed with overall score: {state.overall_score} ({state.verdict})."
        )

        logger.info(f"[COUNCIL] Evaluation finished for {submission_id}: {state.overall_score} ({state.verdict})")
        return state
