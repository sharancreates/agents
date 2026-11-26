import os
import logging
from typing import List, Dict, Any
from agents.council.state import CouncilState, DimensionEvaluation
from person_2.core.aggregator import MetricsAggregator

logger = logging.getLogger("QualityAgent")

class QualityAgent:
    """
    Semantic Code Quality Agent.
    Audits codebase maintainability, AST complexity, architectural modularity,
    and linter violations with line citations.
    """

    @classmethod
    def evaluate_quality(cls, state: CouncilState) -> DimensionEvaluation:
        state.add_trace(
            agent_role="QualityAgent",
            action="START_QUALITY_AUDIT",
            reasoning=f"Parsing AST structures and linter smells across {state.repo_path}"
        )

        try:
            report = MetricsAggregator.evaluate_directory(state.repo_path)
        except Exception as e:
            logger.warning(f"MetricsAggregator encountered issue: {e}")
            eval_result = DimensionEvaluation(
                dimension="code_quality",
                score=40.0,
                summary=f"Code quality evaluation incomplete due to static analyzer exception: {str(e)}. Score assigned conservatively.",
                flags=["ANALYZER_FAILURE", "ANALYSIS_INCOMPLETE"],
                evidence_citations=[f"Static analysis exception: {str(e)}"],
                raw_metrics={
                    "total_files": 0,
                    "global_issues": 0,
                    "average_complexity": 0.0,
                    "max_complexity": 0,
                    "rating": "UNAVAILABLE",
                    "analyzer_error": str(e)
                }
            )
            state.dimensions["code_quality"] = eval_result
            state.add_trace(
                agent_role="QualityAgent",
                action="QUALITY_AUDIT_FAILED",
                reasoning=f"MetricsAggregator failed: {str(e)}",
                details=eval_result.raw_metrics
            )
            return eval_result

        summary_data = report.get("summary", {})
        metrics_data = report.get("metrics", {})
        breakdown = report.get("file_breakdown", [])

        total_files = summary_data.get("total_files_evaluated", 0)
        global_issues = summary_data.get("global_issue_count", 0)
        avg_complexity = metrics_data.get("average_cyclomatic_complexity", 1.0)
        max_complexity = metrics_data.get("max_complexity_observed", 1)

        # Build line-numbered evidence citations
        citations: List[str] = []
        flags: List[str] = []

        for item in breakdown:
            fpath = item.get("file_path", "")
            comp = item.get("cyclomatic_complexity", 1)
            issues = item.get("issues_found", 0)
            smells = item.get("smells", [])

            if comp > 10:
                citations.append(f"{fpath} - High cyclomatic complexity ({comp}) exceeds clean code threshold (10).")
            if issues > 5:
                citations.append(f"{fpath} - Contains {issues} linter smells or structural issues.")

        # Scoring calculation (0 - 100)
        base_score = 100.0
        # Deduct for complexity
        if avg_complexity > 5.0:
            base_score -= min(25.0, (avg_complexity - 5.0) * 5.0)
        # Deduct for issues / file density
        if total_files > 0:
            density = global_issues / total_files
            base_score -= min(35.0, density * 5.0)

        # Flag assignments
        if max_complexity > 15:
            flags.append("CRITICAL_COMPLEXITY_BLOCKS")
        if global_issues == 0 and total_files > 0:
            flags.append("CLEAN_LINTER_PASS")
        if avg_complexity <= 2.5:
            flags.append("EXCELLENT_MODULARITY")

        final_score = max(30.0, min(100.0, round(base_score, 1)))

        summary_text = (
            f"Evaluated {total_files} files. Average complexity: {avg_complexity}, "
            f"Max complexity: {max_complexity}. Discovered {global_issues} static issues."
        )

        eval_result = DimensionEvaluation(
            dimension="code_quality",
            score=final_score,
            summary=summary_text,
            flags=flags,
            evidence_citations=citations[:5], # Keep top 5 strongest citations
            raw_metrics={
                "total_files": total_files,
                "global_issues": global_issues,
                "average_complexity": avg_complexity,
                "max_complexity": max_complexity,
                "rating": summary_data.get("overall_maintainability_rating", "HIGH")
            }
        )

        state.dimensions["code_quality"] = eval_result
        state.add_trace(
            agent_role="QualityAgent",
            action="QUALITY_AUDIT_COMPLETE",
            reasoning=summary_text,
            details=eval_result.raw_metrics
        )

        return eval_result
