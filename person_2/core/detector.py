import os
from typing import Dict

class LanguageDetector:
    MAP: Dict[str, str] = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java"
    }

    @classmethod
    def identify_file(cls, path: str) -> str:
        """Determines the programming language of a file based on extension/shebang fallback."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Target path does not resolve to a file: {path}")

        _, ext = os.path.splitext(path)
        normalized = ext.lower()
        if normalized in cls.MAP:
            return cls.MAP[normalized]

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as file:
                head = file.readline().strip()
                if head.startswith("#!"):
                    if "python" in head:
                        return "python"
                    if "node" in head:
                        return "javascript"
        except (IOError, OSError):
            pass

        return "unknown"

    @classmethod
    def identify_workspace(cls, directory: str) -> str:
        """Identifies the dominant programming language across an entire workspace folder structure."""
        if not os.path.isdir(directory):
            raise NotADirectoryError(f"Provided path is not an accessible directory: {directory}")

        tallies = {lang: 0 for lang in cls.MAP.values()}
        for root, _, items in os.walk(directory):
            if any(ex in root for ex in ["node_modules", ".git", "__pycache__", "dist", "build"]):
                continue
            for item in items:
                _, extension = os.path.splitext(item)
                matched = cls.MAP.get(extension.lower())
                if matched:
                    tallies[matched] += 1

        top_choice = max(tallies, key=tallies.get)
        return top_choice if tallies[top_choice] > 0 else "unknown"