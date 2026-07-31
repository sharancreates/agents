from typing import Dict, Any
from person_2.functionality.models import FunctionalityReport, ConsolidatedGradeReport

class EvaluationScoringEngine:
    """Consolidates dynamic execution metrics and static code smell reports into a final grade."""

    @classmethod
    def calculate_composite_grade(
        cls, 
        submission_id: str, 
        func_report: FunctionalityReport, 
        static_metrics: Dict[str, Any]
    ) -> ConsolidatedGradeReport:
        # 1. Component A: Functionality Score (0 - 100)
        func_score = float(func_report.success_rate)

        # 2. Component B: Code Quality Score (0 - 100)
        # Starts at 100, deducts points per discovered issue/complexity spike
        smell_count = static_metrics.get("smell_count", 0)
        cyclomatic_complexity = static_metrics.get("cyclomatic_complexity", 1)
        
        quality_score = max(0.0, 100.0 - (smell_count * 5.0) - (max(0, cyclomatic_complexity - 5) * 2.0))

        # 3. Component C: Efficiency Score (0 - 100)
        # Base efficiency starts at 100, penalized if timeouts occur or memory hits thresholds
        efficiency_score = 100.0
        
        # Look for timeouts or system failure signatures in test runs
        has_timeout = any("TIMEOUT" in (tc.error_message or "") for tc in func_report.test_breakdown)
        if has_timeout:
            efficiency_score -= 50.0
            
        # Penalize if peak RAM footprints exceed an arbitrary 32MB constraint for basic problems
        if func_report.peak_memory_bytes > 33554432:  
            efficiency_score -= 20.0
            
        efficiency_score = max(0.0, efficiency_score)

        # 4. Compute Final Weighted Grade (Scaled out of 10.0 points)
        # Weights: 60% Functionality, 20% Quality, 20% Efficiency
        weighted_total = (func_score * 0.60) + (quality_score * 0.20) + (efficiency_score * 0.20)
        final_grade = round(weighted_total / 10.0, 2)

        # 5. Determine Automation Verdict
        if func_score < 100.0:
            verdict = "REJECTED_FUNCTIONAL_FAILURE"
        elif final_grade >= 8.0:
            verdict = "ACCEPTED_EXCELLENT"
        elif final_grade >= 6.0:
            verdict = "ACCEPTED_OPTIMIZATION_REQUIRED"
        else:
            verdict = "REJECTED_POOR_EFFICIENCY"

        return ConsolidatedGradeReport(
            submission_id=submission_id,
            functionality_score=round(func_score, 2),
            efficiency_score=round(efficiency_score, 2),
            code_quality_score=round(quality_score, 2),
            final_weighted_grade=final_grade,
            verdict=verdict
        )