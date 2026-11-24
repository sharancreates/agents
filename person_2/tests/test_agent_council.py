import os
import pytest
from agents.council.state import CouncilState, EnvironmentBlueprint
from agents.council.recon_agent import ReconAgent
from agents.council.qa_agent import QAAgent
from agents.council.quality_agent import QualityAgent
from agents.council.forensics_agent import ForensicsAgent
from agents.council.critic_agent import CriticAgent
from agents.council.feedback_agent import FeedbackCoach
from agents.council.orchestrator import CouncilOrchestrator

@pytest.fixture
def sample_repo(tmpdir):
    """Creates an isolated mock repository for testing agent council behaviors."""
    # Write README
    readme = tmpdir.join("README.md")
    readme.write("# FastCalculator\nA modern FastAPI math calculation service with unit tests.\n")

    # Write requirements manifest
    reqs = tmpdir.join("requirements.txt")
    reqs.write("fastapi\nuvicorn\npydantic\n")

    # Write main entrypoint
    entry = tmpdir.join("main.py")
    entry.write("""import sys

def main():
    data = sys.stdin.read().strip()
    if data:
        print(f"CALC_OUTPUT:{data}")
    else:
        print("EMPTY_INPUT")

if __name__ == '__main__':
    main()
""")

    return str(tmpdir)

def test_recon_agent_discovery(sample_repo):
    """Verifies that ReconAgent autonomously identifies languages, manifests, and entrypoints."""
    state = CouncilState(submission_id="sub_test_recon", repo_path=sample_repo)
    blueprint = ReconAgent.analyze_repository(state)

    assert blueprint.primary_language == "python"
    assert "requirements.txt" in blueprint.manifest_files
    assert blueprint.entrypoint_script == "main.py"
    assert "FastCalculator" in blueprint.readme_summary
    assert len(state.traces) >= 2

def test_qa_agent_dynamic_synthesis(sample_repo):
    """Verifies that QAAgent synthesizes challenge-aligned test cases and runs them in sandbox."""
    state = CouncilState(
        submission_id="sub_test_qa",
        repo_path=sample_repo,
        challenge_prompt="Build a math calculator CLI"
    )
    ReconAgent.analyze_repository(state)
    qa_eval = QAAgent.synthesize_and_execute(state)

    assert qa_eval.dimension == "functionality"
    assert qa_eval.score >= 70.0
    assert len(state.generated_tests) >= 3
    assert "main.py" in qa_eval.summary

def test_quality_agent_evaluation(sample_repo):
    """Verifies that QualityAgent audits code maintainability and produces evidence citations."""
    state = CouncilState(submission_id="sub_test_qual", repo_path=sample_repo)
    ReconAgent.analyze_repository(state)
    qual_eval = QualityAgent.evaluate_quality(state)

    assert qual_eval.dimension == "code_quality"
    assert qual_eval.score >= 50.0
    assert "total_files" in qual_eval.raw_metrics

def test_forensics_agent_analysis(sample_repo):
    """Verifies that ForensicsAgent inspects version control signals and originality."""
    state = CouncilState(submission_id="sub_test_forensics", repo_path=sample_repo)
    ReconAgent.analyze_repository(state)
    forensics_eval = ForensicsAgent.analyze_forensics(state)

    assert forensics_eval.dimension == "originality"
    assert forensics_eval.score >= 50.0
    assert len(forensics_eval.flags) >= 1

def test_critic_agent_deliberation(sample_repo):
    """Verifies that CriticAgent reconciles dimension scores, audits citations, and synthesizes consensus."""
    state = CouncilState(
        submission_id="sub_test_critic",
        repo_path=sample_repo,
        rubric_weights={"code_quality": 40.0, "functionality": 40.0, "originality": 10.0, "innovation": 10.0}
    )
    ReconAgent.analyze_repository(state)
    QAAgent.synthesize_and_execute(state)
    QualityAgent.evaluate_quality(state)
    ForensicsAgent.analyze_forensics(state)

    CriticAgent.adjudicate_and_synthesize(state)

    assert state.overall_score is not None
    assert state.overall_score >= 0.0
    assert state.verdict is not None
    assert "innovation" in state.dimensions

def test_feedback_coach_generation(sample_repo):
    """Verifies that FeedbackCoach creates strengths, growth areas, and recommendations."""
    state = CouncilState(submission_id="sub_test_coach", repo_path=sample_repo)
    ReconAgent.analyze_repository(state)
    QAAgent.synthesize_and_execute(state)
    QualityAgent.evaluate_quality(state)
    ForensicsAgent.analyze_forensics(state)
    CriticAgent.adjudicate_and_synthesize(state)

    feedback = FeedbackCoach.generate_coaching_package(state)

    assert feedback.status == "complete"
    assert len(feedback.strengths) >= 1
    assert len(feedback.recommendations) >= 1

def test_full_council_orchestrator(sample_repo):
    """Verifies end-to-end execution of the multi-agent council producing a complete evaluation dossier."""
    state = CouncilOrchestrator.evaluate(
        submission_id="sub_council_e2e",
        repo_path=sample_repo,
        challenge_prompt="Build an automated microservice"
    )

    assert state.submission_id == "sub_council_e2e"
    assert state.overall_score is not None
    assert state.verdict in ("ACCEPTED_EXCELLENT", "ACCEPTED_COMMENDABLE", "ACCEPTED_NEEDS_IMPROVEMENT", "REJECTED_BELOW_BAR")
    assert state.participant_feedback is not None
    assert len(state.dimensions) == 4
    assert len(state.traces) >= 8
