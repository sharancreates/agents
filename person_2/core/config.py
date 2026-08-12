import os
import sys

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

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

        try:
            with open(toml_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            if tomllib is not None:
                data = tomllib.loads(content)
                agent_config = data.get("tool", {}).get("code-quality-agent", {})
                if agent_config:
                    config["exclude"] = agent_config.get("exclude", cls.DEFAULT_EXCLUDES)
                    config["max_complexity"] = agent_config.get("max_complexity", cls.DEFAULT_MAX_COMPLEXITY)
            else:
                for line in content.splitlines():
                    if "max_complexity" in line and "=" in line:
                        try:
                            config["max_complexity"] = int(line.split("=")[1].strip())
                        except ValueError:
                            pass
        except Exception:
            pass  # Fall back to defaults on parsing errors

        return config