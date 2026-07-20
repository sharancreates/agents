import os
import re
import ast
import logging
from pathlib import Path

logger = logging.getLogger("ResilienceHandler")

# Threshold limits
DEFAULT_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
BINARY_CHECK_BYTES = 8192                # Check first 8KB for null bytes

class ResilienceHandler:
    @classmethod
    def safe_read_file(cls, file_path: str, max_size_bytes: int = DEFAULT_MAX_FILE_SIZE) -> str:
        """
        Reads a file defensively:
        - Rejects files exceeding the size limit.
        - Scans for null bytes to reject binary files.
        - Resolves encoding anomalies (UTF-8, Latin-1 fallback).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # 1. Size Guard
        file_size = path.stat().st_size
        if file_size > max_size_bytes:
            raise ValueError(f"File size {file_size} bytes exceeds safety limit of {max_size_bytes} bytes.")
        
        # 2. Binary / Null Byte Guard
        try:
            with open(path, "rb") as f:
                header = f.read(BINARY_CHECK_BYTES)
                if b"\x00" in header:
                    raise ValueError("Binary file format detected (contains null bytes).")
        except Exception as e:
            if not isinstance(e, ValueError):
                raise ValueError(f"Read verification failure: {e}")
            raise e
            
        # 3. Encoding Fallbacks
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        for encoding in encodings:
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
                
        raise ValueError("Could not decode file content under any supported encoding profile.")

    @classmethod
    def safe_parse_ast(cls, source_code: str) -> ast.AST:
        """
        Parses source code into an AST defensively, catching SyntaxError
        and RecursionError from deeply nested blocks.
        """
        if not source_code.strip():
            return None
            
        try:
            return ast.parse(source_code)
        except (SyntaxError, RecursionError) as err:
            logger.warning(f"AST Parser failure: {err}. Falling back to clean parsing modes.")
            return None

    @classmethod
    def regex_fallback_parse(cls, source_code: str) -> list:
        """
        Fallback parser that extracts top-level functions using regular expressions
        if the AST parser crashes on syntax errors or recursion boundaries.
        """
        functions = []
        # Pattern to capture top-level def and async def blocks
        pattern = re.compile(r"^(async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\):", re.MULTILINE)
        
        lines = source_code.splitlines()
        for match in pattern.finditer(source_code):
            func_name = match.group(2)
            sig = match.group(0).strip()
            
            # Simple line-scanning heuristic to collect function lines with indentation
            start_pos = match.start()
            start_line_idx = source_code[:start_pos].count("\n")
            
            func_lines = [lines[start_line_idx]]
            
            # Extract subsequent lines that are indented
            for idx in range(start_line_idx + 1, len(lines)):
                line = lines[idx]
                if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                    # Stop if we hit a line with no indentation (start of next block)
                    break
                func_lines.append(line)
                
            func_code = "\n".join(func_lines)
            functions.append({
                "function_name": func_name,
                "signature": sig,
                "cleaned_source": func_code,
                "parent_class": None
            })
            
        return functions
