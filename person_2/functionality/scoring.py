from typing import Dict, Any, Optional, List
from person_2.functionality.models import FunctionalityReport, ConsolidatedGradeReport

class EvaluationScoringEngine:
    """Consolidates dynamic execution metrics, sandbox safety alerts, and static code reports into a grade."""

    @classmethod
    def calculate_composite_grade(
        cls, 
        submission_id: str, 
        func_report: Optional[FunctionalityReport] = None, 
        static_metrics: Optional[Dict[str, Any]] = None,
        report: Optional[FunctionalityReport] = None,
        **kwargs
    ) -> ConsolidatedGradeReport:
        effective_report = func_report or report
        if not effective_report:
            effective_report = FunctionalityReport(
                total_tests=0,
                passed_tests=0,
                success_rate=0.0,
                peak_memory_bytes=0,
                test_breakdown=[]
            )

        metrics = static_metrics or {}
        flags: List[str] = []

        # 1. Component A: Functionality Score (0 - 100)
        func_score = float(effective_report.success_rate)

        # 2. Component B: Code Quality Score (0 - 100)
        smell_count = metrics.get("smell_count", 0)
        cyclomatic_complexity = metrics.get("cyclomatic_complexity", 1)
        quality_score = max(0.0, 100.0 - (smell_count * 5.0) - (max(0, cyclomatic_complexity - 5) * 2.0))

        # 3. Component C: Efficiency Score (0 - 100) & Security Checks
        efficiency_score = 100.0
        
        has_timeout = any("TIMEOUT" in (tc.error_message or "") for tc in effective_report.test_breakdown)
        has_oom = any("OOM_KILLED" in (tc.error_message or "") for tc in effective_report.test_breakdown)
        has_security = any("SECURITY_VIOLATION" in (tc.error_message or "") for tc in effective_report.test_breakdown)

        if has_security:
            flags.append("SECURITY_VIOLATION_BLOCKED")
            efficiency_score = 0.0
            func_score = 0.0

        if has_oom:
            flags.append("OOM_LIMIT_EXCEEDED")
            efficiency_score -= 50.0

        if has_timeout:
            flags.append("EXECUTION_TIMEOUT")
            efficiency_score -= 50.0
            
        # Penalize if peak RAM footprints exceed 32MB constraint
        if effective_report.peak_memory_bytes > 33554432:  
            flags.append("HIGH_MEMORY_FOOTPRINT")
            efficiency_score -= 20.0
            
        efficiency_score = max(0.0, efficiency_score)

        # 4. Compute Final Weighted Grade (Scaled out of 10.0 points)
        weighted_total = (func_score * 0.60) + (quality_score * 0.20) + (efficiency_score * 0.20)
        final_grade = round(weighted_total / 10.0, 2)

        # 5. Determine Automation Verdict
        if has_security:
            verdict = "DISQUALIFIED_SECURITY_POLICY"
        elif func_score < 70.0:
            verdict = "REJECTED_FUNCTIONAL_FAILURE"
        elif final_grade >= 8.0:
            verdict = "ACCEPTED_EXCELLENT"
        elif final_grade >= 6.0:
            verdict = "ACCEPTED_OPTIMIZATION_REQUIRED"
        else:
            verdict = "REJECTED_POOR_EFFICIENCY"

        score_20 = round(final_grade * 2.0, 1)

        return ConsolidatedGradeReport(
            submission_id=submission_id,
            functionality_score=round(func_score, 2),
            efficiency_score=round(efficiency_score, 2),
            code_quality_score=round(quality_score, 2),
            final_weighted_grade=final_grade,
            verdict=verdict,
            flags=flags,
            score_20=score_20
        )
