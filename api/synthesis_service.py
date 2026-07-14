import json
from datetime import datetime

def get_default_weights():
    return {
        "code_quality": 30,
        "functionality": 30,
        "originality": 20,
        "innovation": 20
    }

def calculate_synthesis_score(submission_data: dict, weights: dict = None) -> float:
    if not weights:
        weights = get_default_weights()
    
    cq = submission_data.get("code_quality") or {}
    fn = submission_data.get("functionality") or {}
    orig = submission_data.get("originality") or {}
    innov = submission_data.get("innovation") or {}
    
    # Check if required dimensions are complete
    if not cq or cq.get("status") != "complete":
        return None
    if not fn or fn.get("status") != "complete":
        return None
    if not orig or orig.get("status") != "complete":
        return None
    if not innov or innov.get("status") != "complete":
        return None

    cq_score = cq.get("score") or 0
    fn_score = fn.get("score") or 0
    orig_score = orig.get("score") or 0
    innov_score = innov.get("score") or 0

    total_score = (
        cq_score * (weights.get("code_quality", 30) / 100.0) +
        fn_score * (weights.get("functionality", 30) / 100.0) +
        orig_score * (weights.get("originality", 20) / 100.0) +
        innov_score * (weights.get("innovation", 20) / 100.0)
    )
    return round(total_score, 2)

def generate_synthesis_summary(submission_data: dict, weights: dict = None) -> str:
    if not weights:
        weights = get_default_weights()
        
    score = calculate_synthesis_score(submission_data, weights)
    if score is None:
        return "Synthesis pending: waiting for all evaluation dimensions to complete."
        
    cq = submission_data.get("code_quality") or {}
    fn = submission_data.get("functionality") or {}
    orig = submission_data.get("originality") or {}
    innov = submission_data.get("innovation") or {}

    # Determine qualitative verdict
    if score >= 90:
        verdict = "exceptional, standing out as a high-tier implementation with excellent execution across all evaluated domains"
    elif score >= 75:
        verdict = "strong, displaying commendable competency and solid technical delivery with minor areas for refinement"
    elif score >= 50:
        verdict = "adequate, meeting baseline criteria but requiring substantial refinement and polish to be production-ready"
    else:
        verdict = "critical issues detected, failing to satisfy basic hackathon thresholds in multiple dimensions"

    team_name = submission_data.get("team_name") or "Unknown Team"

    summary = (
        f"This submission for team **{team_name}** achieved a composite score of {score:.1f}/100, "
        f"evaluated using custom weights ({weights.get('code_quality')}% Code Quality, {weights.get('functionality')}% Functionality, "
        f"{weights.get('originality')}% Originality, and {weights.get('innovation')}% Innovation). "
        f"The evaluation team classifies this entry as {verdict}.\n\n"
    )

    # Core Strengths / Highlights
    dims = [
        {"name": "Code Quality", "score": cq.get("score") or 0},
        {"name": "Functionality", "score": fn.get("score") or 0},
        {"name": "Originality", "score": orig.get("score") or 0},
        {"name": "Innovation", "score": innov.get("score") or 0}
    ]
    
    dims_sorted = sorted(dims, key=lambda x: x["score"], reverse=True)
    best = dims_sorted[0]
    worst = dims_sorted[-1]

    summary += "### Core Strengths & Technical Highlights\n"
    summary += f"The project's primary strength is **{best['name']}**, where it scored **{best['score']}/100**. "

    if best["name"] == "Code Quality":
        summary += f"Our static analysis noted: \"{cq.get('summary', 'Clean structural setup.')}\" "
        metrics = cq.get("raw_metrics") or {}
        if metrics.get("complexity_score") is not None:
            summary += f"It maintained a low complexity rating of {metrics.get('complexity_score')} and only {metrics.get('lint_warnings', 0)} lint warnings."
    elif best["name"] == "Functionality":
        summary += f"The execution sandbox reported: \"{fn.get('summary', 'All test cases passed.')}\" "
        metrics = fn.get("raw_metrics") or {}
        if metrics.get("tests_passed") is not None:
            summary += f"It successfully passed {metrics.get('tests_passed')} out of {metrics.get('total_tests', metrics.get('tests_passed'))} tests in the test suite."
    elif best["name"] == "Originality":
        summary += f"The originality analysis concluded: \"{orig.get('summary', 'Highly unique code signature.')}\""
    elif best["name"] == "Innovation":
        summary += f"The innovation agent reported: \"{innov.get('summary', 'Highly innovative application features.')}\""
        metrics = innov.get("raw_metrics") or {}
        if metrics.get("techniques"):
            summary += f" It showcased cutting-edge techniques such as: {', '.join(metrics.get('techniques'))}."

    summary += "\n\n"

    # Opportunities for Improvement
    if worst["score"] < 90 and worst["name"] != best["name"]:
        summary += "### Opportunities for Improvement\n"
        summary += f"Conversely, the lowest scoring dimension was **{worst['name']}** at **{worst['score']}/100**. "
        if worst["name"] == "Code Quality":
            summary += f"Static analysis flags included: \"{cq.get('summary', 'Review complexity metrics.')}\""
        elif worst["name"] == "Functionality":
            summary += f"Sandbox suite noted: \"{fn.get('summary', 'Some runtime constraints.')}\""
        elif worst["name"] == "Originality":
            summary += f"Originality scans flagged matching content: \"{orig.get('summary', 'Minor similarity patterns.')}\""
        elif worst["name"] == "Innovation":
            summary += f"Innovation scoring noted: \"{innov.get('summary', 'Standard implementation pattern.')}\""
        summary += "\n\n"

    # Warnings
    all_flags = []
    for dim_name, dim_data in [("Code Quality", cq), ("Originality", orig), ("Functionality", fn), ("Innovation", innov)]:
        flags = dim_data.get("flags") or []
        for flag in flags:
            all_flags.append(f"**{dim_name}**: {flag.get('message', 'Unspecified flag')}")

    if all_flags:
        summary += "### Critical Warning Flags & Items Requiring Attention\n"
        for flag_str in all_flags:
            summary += f"- {flag_str}\n"
        summary += "\n"

    return summary.strip()
