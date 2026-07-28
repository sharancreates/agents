"""
Feedback Agent Service
Generates participant-facing commentary (deliberately separate from judge-facing numeric scores).
Focuses on constructive feedback, technical highlights, growth areas, and actionable recommendations.
"""

def generate_participant_feedback(submission_data: dict) -> dict:
    """
    Ingests raw or synthesis submission data and produces a participant-facing commentary package.
    """
    if not submission_data:
        return {
            "status": "pending",
            "commentary": "Submission data unavailable.",
            "strengths": [],
            "improvements": []
        }

    team_name = submission_data.get("team_name") or "Participant Team"
    cq = submission_data.get("code_quality") or {}
    fn = submission_data.get("functionality") or {}
    orig = submission_data.get("originality") or {}
    innov = submission_data.get("innovation") or {}

    cq_score = cq.get("score")
    fn_score = fn.get("score")
    orig_score = orig.get("score")
    innov_score = innov.get("score")

    # If key dimensions are not yet finished
    if any(s is None for s in [cq_score, fn_score, orig_score]):
        return {
            "status": "pending",
            "commentary": "Evaluation is still underway. Participant commentary will be available once evaluations complete.",
            "strengths": [],
            "improvements": []
        }

    strengths = []
    improvements = []

    # Code Quality feedback
    if cq_score >= 85:
        strengths.append("High code readability and modular structural organization.")
        if cq.get("summary"):
            strengths.append(f"Static analysis highlight: {cq.get('summary')}")
    elif cq_score < 70:
        improvements.append("Refactor complex logic blocks to reduce cyclomatic complexity and improve maintainability.")
        if cq.get("summary"):
            improvements.append(f"Code quality note: {cq.get('summary')}")

    # Functionality feedback
    if fn_score >= 90:
        strengths.append("Robust implementation with smooth execution across automated test suites.")
    elif fn_score < 75:
        improvements.append("Increase unit test coverage and handle edge-case input validations to improve runtime reliability.")

    # Originality feedback
    if orig_score >= 85:
        strengths.append("Distinct algorithm design with very low code similarity patterns.")
    elif orig_score < 70:
        improvements.append("Avoid relying heavily on standard boilerplate templates; introduce custom abstractions.")

    # Innovation feedback
    if innov_score and innov_score >= 80:
        strengths.append("Creative problem-solving approach and thoughtful UX/architectural touches.")
        metrics = innov.get("raw_metrics") or {}
        if metrics.get("techniques"):
            strengths.append(f"Notable techniques demonstrated: {', '.join(metrics.get('techniques'))}.")
    elif innov_score and innov_score < 70:
        improvements.append("Explore more novel architectural patterns or advanced framework capabilities.")

    # General fallback strengths/improvements if lists are short
    if not strengths:
        strengths.append("Successfully delivered a functional submission matching the project criteria.")
    if not improvements:
        improvements.append("Consider profiling runtime memory performance and adding comprehensive inline documentation.")

    commentary = (
        f"Kudos to **{team_name}** for completing the hackathon challenge! "
        f"Your team demonstrated solid technical effort. Focus on refining architectural modularity "
        f"and expanding edge-case coverage to take your project to the next level."
    )

    return {
        "status": "complete",
        "team_name": team_name,
        "commentary": commentary,
        "strengths": strengths,
        "improvements": improvements,
        "visibility": "participant_visible"
    }
