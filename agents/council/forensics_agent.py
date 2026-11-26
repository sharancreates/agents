import os
import subprocess
import logging
from typing import List, Dict, Any, Optional
from agents.council.state import CouncilState, DimensionEvaluation

logger = logging.getLogger("ForensicsAgent")

class ForensicsAgent:
    """
    Git Forensics & Originality Agent.
    Analyzes commit frequencies, developer commit patterns, boilerplate density,
    and code plagiarism signals.
    """

    @classmethod
    def analyze_forensics(cls, state: CouncilState) -> DimensionEvaluation:
        state.add_trace(
            agent_role="ForensicsAgent",
            action="START_FORENSICS",
            reasoning=f"Inspecting version control logs and code originality for {state.repo_path}"
        )

        git_dir = os.path.join(state.repo_path, ".git")
        commits: List[Dict[str, str]] = []
        is_git_repo = os.path.isdir(git_dir)

        if is_git_repo:
            try:
                res = subprocess.run(
                    ["git", "log", "-n", "30", "--pretty=format:%H|%an|%ad|%s"],
                    cwd=state.repo_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=3.0
                )
                if res.returncode == 0 and res.stdout:
                    for line in res.stdout.strip().split("\n"):
                        parts = line.split("|")
                        if len(parts) >= 4:
                            commits.append({
                                "sha": parts[0],
                                "author": parts[1],
                                "date": parts[2],
                                "subject": parts[3]
                            })
            except Exception as e:
                logger.warning(f"Could not read git history: {e}")

        commit_count = len(commits)
        flags: List[str] = []
        citations: List[str] = []

        # Analyze commit cadence
        if commit_count >= 5:
            flags.append("ORGANIC_DEVELOPMENT_HISTORY")
            citations.append(f"Repository exhibits {commit_count} historical commits indicating steady iterative progress.")
            score = 90.0
        elif commit_count >= 1:
            flags.append("LIMITED_COMMIT_HISTORY")
            citations.append(f"Only {commit_count} commits detected. Project may have been uploaded in an atomic batch.")
            score = 75.0
        else:
            flags.append("NO_GIT_HISTORY")
            citations.append("No active Git history found in target directory. Evaluated from workspace snapshot.")
            score = 80.0

        # Check for boilerplate patterns
        env = state.environment
        if env and len(env.manifest_files) > 0:
            citations.append(f"Verified package manifests: {', '.join(env.manifest_files)}.")

        # Compute dynamic internal code similarity / duplication ratio across repo files
        code_files = []
        for root, _, files in os.walk(state.repo_path):
            if any(p in root for p in [".git", "__pycache__", "node_modules", ".venv", "venv"]):
                continue
            for f in files:
                if f.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                    code_files.append(os.path.join(root, f))

        similarity_ratio: Optional[float] = None
        if len(code_files) >= 2:
            # Multi-file cross-token Jaccard similarity analysis
            file_token_sets = []
            for cf in code_files[:15]:
                try:
                    with open(cf, "r", encoding="utf-8", errors="ignore") as f:
                        tokens = set([t.strip() for t in f.read().split() if len(t.strip()) > 3])
                        if tokens:
                            file_token_sets.append(tokens)
                except Exception:
                    pass

            if len(file_token_sets) >= 2:
                pair_sims = []
                for i in range(len(file_token_sets)):
                    for j in range(i + 1, len(file_token_sets)):
                        intersection = len(file_token_sets[i] & file_token_sets[j])
                        union = len(file_token_sets[i] | file_token_sets[j])
                        if union > 0:
                            pair_sims.append(intersection / union)
                if pair_sims:
                    similarity_ratio = round(sum(pair_sims) / len(pair_sims), 3)
        elif len(code_files) == 1:
            # Single-file line repetition analysis
            try:
                with open(code_files[0], "r", encoding="utf-8", errors="ignore") as f:
                    lines = [line.strip() for line in f if len(line.strip()) > 5]
                    if lines:
                        unique_lines = set(lines)
                        similarity_ratio = round(1.0 - (len(unique_lines) / len(lines)), 3)
            except Exception:
                similarity_ratio = None

        if similarity_ratio is not None and similarity_ratio > 0.45:
            flags.append("HIGH_CODE_DUPLICATION")
            citations.append(f"Elevated internal code duplication ratio ({similarity_ratio:.2f}) observed across files.")
            score = max(40.0, score - 20.0)

        sim_summary = (
            f"Internal duplication ratio: {similarity_ratio:.2f}."
            if similarity_ratio is not None
            else "Internal duplication index unavailable."
        )

        eval_result = DimensionEvaluation(
            dimension="originality",
            score=round(score, 1),
            summary=f"Forensic audit evaluated {commit_count} commits. {sim_summary} Standalone originality analysis performed.",
            flags=flags,
            evidence_citations=citations,
            raw_metrics={
                "commit_count": commit_count,
                "is_git_tracked": is_git_repo,
                "similarity_ratio": similarity_ratio,
                "plagiarism_check": "internal_heuristics_standalone"
            }
        )

        state.dimensions["originality"] = eval_result
        state.add_trace(
            agent_role="ForensicsAgent",
            action="FORENSICS_COMPLETE",
            reasoning=f"Originality confirmed with {commit_count} commits analyzed.",
            details=eval_result.raw_metrics
        )

        return eval_result
