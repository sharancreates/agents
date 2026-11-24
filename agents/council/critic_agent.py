import logging
from typing import Dict, Any, List
from agents.council.state import CouncilState, DimensionEvaluation

logger = logging.getLogger("CriticAgent")

class CriticAgent:
    """
    Adversarial Critic & Consensus Adjudicator.
    Validates evidence across specialized agents, challenges ungrounded score penalties,
    evaluates innovation, and computes calibrated composite grades.
    """

    @classmethod
    def adjudicate_and_synthesize(cls, state: CouncilState) -> CouncilState:
        state.add_trace(
            agent_role="CriticAgent",
            action="START_ADJUDICATION",
            reasoning="Auditing agent claims and validating evidence citations."
        )

        critic_notes: List[str] = []

        # 1. Evaluate Innovation & Architectural Integrity
        env = state.environment
        innov_score = 80.0
        innov_flags = []
        innov_citations = []

        if env and env.framework:
            innov_score += 10.0
            innov_flags.append(f"FRAMEWORK_ADOPTION_{env.framework.upper()}")
            innov_citations.append(f"Modern {env.framework} framework leveraged for structured architecture.")

        if env and env.readme_summary and len(env.readme_summary) > 200:
            innov_score += 5.0
            innov_flags.append("DOCUMENTATION_COMPREHENSIVE")
            innov_citations.append("Clear project documentation and problem framing present in README.")

        innov_eval = DimensionEvaluation(
            dimension="innovation",
            score=min(100.0, round(innov_score, 1)),
            summary=f"Technical architecture validated with {env.framework or 'custom'} layout.",
            flags=innov_flags,
            evidence_citations=innov_citations,
            raw_metrics={"framework": env.framework if env else None}
        )
        state.dimensions["innovation"] = innov_eval

        # 2. Evidence validation loop across dimensions
        for dim_name, eval_item in list(state.dimensions.items()):
            # If an agent gave a severe penalty (< 50) without citations, challenge and adjust
            if eval_item.score < 50.0 and len(eval_item.evidence_citations) == 0:
                critic_notes.append(f"Rebounded ungrounded penalty in '{dim_name}' from {eval_item.score} to 65.0 due to lack of citations.")
                eval_item.score = 65.0

        state.critic_notes = critic_notes

        # 3. Check for security disqualification
        fn_eval = state.dimensions.get("functionality")
        if fn_eval and "SECURITY_VIOLATION_BLOCKED" in fn_eval.flags:
            state.overall_score = 0.0
            state.verdict = "DISQUALIFIED_SECURITY_POLICY"
            state.add_trace(
                agent_role="CriticAgent",
                action="DISQUALIFY",
                reasoning="Disqualified submission due to critical sandbox security violation."
            )
            return state

        # 4. Synthesize composite score using rubric weights
        weights = state.rubric_weights
        total_weight = sum(weights.values()) or 100.0

        cq_score = state.dimensions.get("code_quality", DimensionEvaluation(dimension="code_quality", score=70.0, summary="")).score
        fn_score = state.dimensions.get("functionality", DimensionEvaluation(dimension="functionality", score=70.0, summary="")).score
        orig_score = state.dimensions.get("originality", DimensionEvaluation(dimension="originality", score=80.0, summary="")).score
        innov_score = state.dimensions.get("innovation", DimensionEvaluation(dimension="innovation", score=80.0, summary="")).score

        weighted_score = (
            (cq_score * weights.get("code_quality", 30.0)) +
            (fn_score * weights.get("functionality", 30.0)) +
            (orig_score * weights.get("originality", 20.0)) +
            (innov_score * weights.get("innovation", 20.0))
        ) / total_weight

        overall_score = round(weighted_score, 1)
        state.overall_score = overall_score

        # 5. Determine qualitative consensus verdict
        if overall_score >= 85.0:
            verdict = "ACCEPTED_EXCELLENT"
        elif overall_score >= 75.0:
            verdict = "ACCEPTED_COMMENDABLE"
        elif overall_score >= 60.0:
            verdict = "ACCEPTED_NEEDS_IMPROVEMENT"
        else:
            verdict = "REJECTED_BELOW_BAR"

        state.verdict = verdict
        state.add_trace(
            agent_role="CriticAgent",
            action="CONSENSUS_REACHED",
            reasoning=f"Consensus finalized. Overall Score: {overall_score}/100. Verdict: {verdict}.",
            details={
                "overall_score": overall_score,
                "verdict": verdict,
                "weights_applied": weights,
                "critic_adjustments": len(critic_notes)
            }
        )

        return state
