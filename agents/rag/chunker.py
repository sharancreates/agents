import os
import ast
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ASTCodeChunker")

IGNORED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    "dist", "build", ".next", ".pytest_cache", ".gemini", "brain"
}

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yaml", ".yml",
    ".md", ".sh", ".sql", ".html"
}

class ASTCodeChunker:
    """
    Parses source code into semantically coherent AST chunks with exact line numbers.
    """

    @classmethod
    def chunk_python_source(cls, source_code: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts functions, classes, and decorated API routes using Python's AST module.
        """
        lines = source_code.splitlines()
        chunks = []

        try:
            tree = ast.parse(source_code, filename=file_path)
        except SyntaxError:
            # Fall back to structural text chunking if syntax error occurs
            return cls.chunk_text_fallback(source_code, file_path)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                if node.decorator_list:
                    start_line = min(start_line, min(d.lineno for d in node.decorator_list))
                end_line = getattr(node, "end_lineno", start_line)
                
                # Check if route handler decorator exists (e.g. @app.get, @router.post)
                symbol_type = "function"
                for dec in node.decorator_list:
                    dec_str = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                    if any(verb in dec_str.lower() for verb in ("get", "post", "put", "delete", "patch", "route")):
                        symbol_type = "route"
                        break

                chunk_content = "\n".join(lines[start_line - 1 : end_line])
                chunks.append({
                    "file_path": file_path,
                    "symbol_name": node.name,
                    "symbol_type": symbol_type,
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": chunk_content
                })

            elif isinstance(node, ast.ClassDef):
                start_line = node.lineno
                if node.decorator_list:
                    start_line = min(start_line, min(d.lineno for d in node.decorator_list))
                end_line = getattr(node, "end_lineno", start_line)
                chunk_content = "\n".join(lines[start_line - 1 : end_line])
                chunks.append({
                    "file_path": file_path,
                    "symbol_name": node.name,
                    "symbol_type": "class",
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": chunk_content
                })

        # If no AST symbols found (e.g. flat script or configuration), chunk as block
        if not chunks and lines:
            chunks.append({
                "file_path": file_path,
                "symbol_name": os.path.basename(file_path),
                "symbol_type": "module",
                "start_line": 1,
                "end_line": len(lines),
                "content": source_code.strip()
            })

        return chunks

    @classmethod
    def chunk_text_fallback(
        cls,
        source_code: str,
        file_path: str,
        chunk_size: int = 40,
        overlap: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Sliding-window structural chunker for non-Python or unparseable files.
        """
        lines = source_code.splitlines()
        if not lines:
            return []

        chunks = []
        step = max(1, chunk_size - overlap)
        for i in range(0, len(lines), step):
            start = i + 1
            end = min(len(lines), i + chunk_size)
            block = "\n".join(lines[i:end]).strip()
            if block:
                chunks.append({
                    "file_path": file_path,
                    "symbol_name": f"{os.path.basename(file_path)}:L{start}-L{end}",
                    "symbol_type": "block",
                    "start_line": start,
                    "end_line": end,
                    "content": block
                })
        return chunks

    @classmethod
    def chunk_file(cls, full_path: str, repo_root: str) -> List[Dict[str, Any]]:
        """Reads a file and returns semantic chunks with relative repository paths."""
        rel_path = os.path.relpath(full_path, repo_root).replace("\\", "/")
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Failed to read {full_path}: {e}")
            return []

        if full_path.endswith(".py"):
            return cls.chunk_python_source(content, rel_path)
        else:
            return cls.chunk_text_fallback(content, rel_path)

    @classmethod
    def chunk_directory(cls, repo_path: str) -> List[Dict[str, Any]]:
        """
        Recursively scans repository, ignores dependencies/caches, and chunks all source files.
        """
        all_chunks = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ALLOWED_EXTENSIONS or file in ("Dockerfile", "Makefile", "Procfile"):
                    full_path = os.path.join(root, file)
                    chunks = cls.chunk_file(full_path, repo_path)
                    all_chunks.extend(chunks)

        logger.info(f"Chunked {repo_path}: extracted {len(all_chunks)} semantic chunks.")
        return all_chunks
