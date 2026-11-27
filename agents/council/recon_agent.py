import os
import re
from pathlib import Path
from typing import Optional, List, Dict
from agents.council.state import EnvironmentBlueprint, CouncilState

class ReconAgent:
    """
    Autonomous Discovery & Environment Reconnaissance Agent.
    Inspects repository layouts, detects frameworks, extracts manifest dependencies,
    and pinpoints execution entrypoints.
    """

    IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build", ".idea", ".vscode"}

    @classmethod
    def analyze_repository(cls, state: CouncilState) -> EnvironmentBlueprint:
        root = Path(state.repo_path).resolve()
        state.add_trace(
            agent_role="ReconAgent",
            action="START_SCAN",
            reasoning=f"Beginning repository discovery on {root}"
        )

        manifest_files = []
        entrypoint_candidates = []
        lang_counts: Dict[str, int] = {}
        readme_summary = ""
        total_files = 0

        # 1. Search for README
        readme_candidates = ["README.md", "readme.md", "README.txt", "README"]
        for r in readme_candidates:
            p = root / r
            if p.exists() and p.is_file():
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        readme_summary = f.read(4000)
                    break
                except Exception:
                    pass

        # 2. Walk directory structure
        manifest_names = {"package.json", "requirements.txt", "pyproject.toml", "setup.py", "Cargo.toml", "go.mod"}
        common_entry_names = {
            "main.py", "app.py", "run.py", "server.py", "cli.py", "index.py",
            "index.js", "app.js", "server.js", "main.js",
            "index.ts", "app.ts", "server.ts", "main.ts"
        }

        for dirpath, dirnames, filenames in os.walk(str(root)):
            # Prune ignored directories
            dirnames[:] = [d for d in dirnames if d not in cls.IGNORE_DIRS and not d.startswith(".")]

            for fname in filenames:
                total_files += 1
                rel_path = os.path.relpath(os.path.join(dirpath, fname), str(root)).replace("\\", "/")

                if fname in manifest_names:
                    manifest_files.append(rel_path)

                ext = os.path.splitext(fname)[1].lower()
                if ext == ".py":
                    lang_counts["python"] = lang_counts.get("python", 0) + 1
                elif ext in (".js", ".jsx", ".mjs"):
                    lang_counts["javascript"] = lang_counts.get("javascript", 0) + 1
                elif ext in (".ts", ".tsx"):
                    lang_counts["typescript"] = lang_counts.get("typescript", 0) + 1
                elif ext in (".java",):
                    lang_counts["java"] = lang_counts.get("java", 0) + 1

                if fname.lower() in common_entry_names:
                    entrypoint_candidates.append(rel_path)

        # 3. Determine primary language
        primary_lang = "python"  # Default
        if lang_counts:
            primary_lang = max(lang_counts.items(), key=lambda x: x[1])[0]

        # 4. Resolve primary entrypoint
        selected_entrypoint = None
        if entrypoint_candidates:
            # Prefer top-level entrypoints matching primary language
            matching_entries = [e for e in entrypoint_candidates if ("/" not in e or e.count("/") == 1)]
            selected_entrypoint = matching_entries[0] if matching_entries else entrypoint_candidates[0]

        # 5. Detect framework
        detected_framework = None
        readme_lower = readme_summary.lower()
        if "fastapi" in readme_lower or any("fastapi" in m for m in manifest_files):
            detected_framework = "fastapi"
        elif "express" in readme_lower or "package.json" in manifest_files:
            detected_framework = "express"
        elif "flask" in readme_lower:
            detected_framework = "flask"
        elif "next" in readme_lower:
            detected_framework = "nextjs"
        elif selected_entrypoint and "cli" in selected_entrypoint.lower():
            detected_framework = "cli"

        blueprint = EnvironmentBlueprint(
            primary_language=primary_lang,
            framework=detected_framework,
            manifest_files=manifest_files,
            entrypoint_script=selected_entrypoint,
            all_entrypoint_candidates=entrypoint_candidates,
            readme_summary=readme_summary[:500],
            challenge_spec=state.challenge_prompt,
            total_files_discovered=total_files
        )

        state.environment = blueprint
        state.add_trace(
            agent_role="ReconAgent",
            action="DISCOVERY_COMPLETE",
            reasoning=f"Identified {primary_lang} stack using {detected_framework or 'standard'} framework with entrypoint '{selected_entrypoint}'.",
            details={
                "language": primary_lang,
                "framework": detected_framework,
                "entrypoint": selected_entrypoint,
                "manifest_count": len(manifest_files),
                "total_files": total_files
            }
        )

        return blueprint
