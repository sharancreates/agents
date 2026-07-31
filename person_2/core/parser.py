import os
import re
import ast
from typing import Dict, Any, Optional

class ParsedTreeResult:
    """
    A lightweight container that mimics a native AST/Tree-Sitter syntax object.
    Exposes properties expected by the legacy aggregator and rules infrastructure.
    """
    def __init__(self, metrics_dict: Dict[str, Any]):
        self._metrics = metrics_dict
        self.root_node = self
        
        # --- Compatibility attributes for legacy AST rules ---
        self.type = "program"
        self.child_count = 0

    def child(self, index):
        return None

    def __getitem__(self, key):
        return self._metrics.get(key)

    def get(self, key, default=None):
        return self._metrics.get(key, default)


# --- Keep the rest of your strategies and TreeSitterRegistry identical ---
class CodeParserStrategy:
    @staticmethod
    def parse_python(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        lines = content.splitlines()
        try:
            tree = ast.parse(content)
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        except SyntaxError:
            functions, classes = [], []
        return {
            "language": "python",
            "total_lines": len(lines),
            "blank_lines": sum(1 for line in lines if not line.strip()),
            "comment_lines": sum(1 for line in lines if line.strip().startswith("#")),
            "functions": functions,
            "classes": classes,
            "raw_content": content
        }

    @staticmethod
    def parse_javascript(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        lines = content.splitlines()
        comment_lines = 0
        in_block_comment = False
        for line in lines:
            stripped = line.strip()
            if in_block_comment:
                comment_lines += 1
                if "*/" in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith("/*"):
                comment_lines += 1
                if "*/" not in stripped:
                    in_block_comment = True
            elif stripped.startswith("//"):
                comment_lines += 1
        functions = re.findall(r'(?:function\s+([a-zA-Z0-9_]+)|const\s+([a-zA-Z0-9_]+)\s*=\s*(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>)', content)
        flattened_functions = [fn[0] or fn[1] for fn in functions if fn[0] or fn[1]]
        classes = re.findall(r'class\s+([a-zA-Z0-9_]+)', content)
        ext = os.path.splitext(file_path)[1].lower()
        return {
            "language": "typescript" if ext == ".ts" else "javascript",
            "total_lines": len(lines),
            "blank_lines": sum(1 for line in lines if not line.strip()),
            "comment_lines": comment_lines,
            "functions": flattened_functions,
            "classes": classes,
            "raw_content": content
        }

class TreeSitterRegistry:
    def __init__(self):
        self.loaded_languages = {"python": True, "javascript": True}

    @staticmethod
    def parse_file(file_path: str, lang: Optional[str] = None) -> Optional[ParsedTreeResult]:
        if not os.path.exists(file_path):
            return None
        ext = os.path.splitext(file_path)[1].lower()
        if lang == "python" or ext == ".py":
            raw_metrics = CodeParserStrategy.parse_python(file_path)
        elif lang in ("javascript", "typescript") or ext in [".js", ".ts"]:
            raw_metrics = CodeParserStrategy.parse_javascript(file_path)
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            raw_metrics = {
                "language": lang or (ext.lstrip(".") if ext else "unknown"),
                "total_lines": len(lines),
                "blank_lines": sum(1 for l in lines if not l.strip()),
                "comment_lines": 0,
                "functions": [],
                "classes": [],
                "raw_content": "".join(lines)
            }
        return ParsedTreeResult(raw_metrics) if raw_metrics else None