import logging
from typing import List
from agents.council.state import CouncilState, ParticipantFeedbackPackage

logger = logging.getLogger("FeedbackCoach")

class FeedbackCoach:
    """
    Participant Feedback Coach Agent.
    Generates actionable, constructive, and empathetic feedback reports for teams.
    """

    @classmethod
    def generate_coaching_package(cls, state: CouncilState) -> ParticipantFeedbackPackage:
        state.add_trace(
            agent_role="FeedbackCoach",
            action="GENERATE_FEEDBACK",
            reasoning="Synthesizing participant-facing feedback package from council findings."
        )

        strengths: List[str] = []
        growth_areas: List[str] = []
        recommendations: List[str] = []

        cq = state.dimensions.get("code_quality")
        fn = state.dimensions.get("functionality")
        orig = state.dimensions.get("originality")
        innov = state.dimensions.get("innovation")

        # Strengths synthesis
        if fn and fn.score >= 80.0:
            strengths.append("High runtime stability: Execution passed functional validation with clean exit codes.")
        if cq and cq.score >= 80.0:
            strengths.append("Clean code architecture: Low average cyclomatic complexity and well-modularized structures.")
        if orig and orig.score >= 80.0:
            strengths.append("Organic technical execution: Distinct algorithm design and steady commit progression.")
        if innov and innov.score >= 80.0:
            strengths.append("Well-chosen technical stack and clear architectural boundaries.")

        if not strengths:
            strengths.append("Working submission with foundational functional components successfully deployed.")

        # Growth areas synthesis
        if cq and cq.score < 80.0:
            growth_areas.append("Refactor complex conditional branches and long methods to improve maintainability.")
            for c in cq.evidence_citations[:2]:
                growth_areas.append(f"Area for refactoring: {c}")

        if fn and fn.score < 80.0:
            growth_areas.append("Strengthen input validation to handle edge cases, empty payloads, and boundary conditions.")

        if orig and "LIMITED_COMMIT_HISTORY" in orig.flags:
            growth_areas.append("Commit more frequently during hackathon sprints to document the evolution of your project.")

        if not growth_areas:
            growth_areas.append("Consider adding end-to-end integration tests and load benchmarks to further polish the project.")

        # High-leverage recommendations
        recommendations.append("Adopt automated static linting (e.g. Ruff or ESLint) in your CI pipeline.")
        recommendations.append("Expand unit test coverage around core data transformation logic.")
        if state.environment and state.environment.framework:
            recommendations.append(f"Explore production-grade deployment configurations for {state.environment.framework}.")

        overall_summary = (
            f"The team delivered a solid implementation achieving a composite score of {state.overall_score}/100 "
            f"with a verdict of {state.verdict}. The codebase demonstrated strong technical promise."
        )

        package = ParticipantFeedbackPackage(
            status="complete",
            overall_summary=overall_summary,
            strengths=strengths,
            growth_areas=growth_areas,
            recommendations=recommendations
        )

        state.participant_feedback = package
        state.add_trace(
            agent_role="FeedbackCoach",
            action="FEEDBACK_COMPLETE",
            reasoning="Constructive feedback report successfully created."
        )

        return package
