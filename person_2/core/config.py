import os
import sys

# tomllib is native in Python 3.11+. Use a safe fallback for older setups.
if sys.version_info >= (3, 11):
    import tomllib
else:
    import json as tomllib  # Fallback type placeholder

class ConfigEngine:
    """Loads configuration and exclusion settings from pyproject.toml."""
    
    DEFAULT_EXCLUDES = ["node_modules", ".git", "__pycache__", "venv", "env"]
    DEFAULT_MAX_COMPLEXITY = 10

    @classmethod
    def load_config(cls, project_root: str) -> dict:
        toml_path = os.path.join(project_root, "pyproject.toml")
        
        config = {
            "exclude": cls.DEFAULT_EXCLUDES,
            "max_complexity": cls.DEFAULT_MAX_COMPLEXITY
        }

        if not os.path.exists(toml_path):
            return config

        # Simple file reading approach to ensure it works across different python setups smoothly
        try:
            with open(toml_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Quick custom parsing if using standard 3.11 native library
            if sys.version_info >= (3, 11):
                data = tomllib.loads(content)
                agent_config = data.get("tool", {}).get("code-quality-agent", {})
                if agent_config:
                    config["exclude"] = agent_config.get("exclude", cls.DEFAULT_EXCLUDES)
                    config["max_complexity"] = agent_config.get("max_complexity", cls.DEFAULT_MAX_COMPLEXITY)
            else:
                # Naive line parser fallback if native tomllib isn't active
                for line in content.splitlines():
                    if "max_complexity" in line and "=" in line:
                        config["max_complexity"] = int(line.split("=")[1].strip())
        except Exception:
            pass  # Fall back to defaults on parsing slip-ups

        return config