import re
import hashlib
import ast
import logging
from pathlib import Path

logger = logging.getLogger("BoilerplateFilter")

# Common boilerplate license header pattern
LICENSE_REGEX = re.compile(
    r"(?i)(copyright|license|licenced|apache|mit|gpl|bsd|all rights reserved|software is provided \"as is\")"
)

# Common framework standard file name rules
BOILERPLATE_FILENAMES = {
    "manage.py", "wsgi.py", "asgi.py", "settings.py", 
    "webpack.config.js", "tailwind.config.js", "postcss.config.js",
    "next.config.js", "vite.config.js", "babel.config.js",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "setup.cfg", "pyproject.toml", "setup.py"
}

# Standard template file MD5 hashes (e.g., default Django, Flask, React templates)
KNOWN_BOILERPLATE_HASHES = {
    # Default Django manage.py template hash
    "7c0c16922d56a29e2ff9d71c4c1a2f64", 
    # Default React index.js template hash
    "6df695de8020ff64b3efbe2dbf88c83a",
    # Empty python init file hash
    "d41d8cd98f00b204e9800998ecf8427e"
}

class BoilerplateFilter:
    @classmethod
    def is_boilerplate_file(cls, file_path: str) -> bool:
        """
        Determines whether an entire file is standard framework boilerplate
        or vendor code based on filename rules and signature hashes.
        """
        path = Path(file_path)
        
        # 1. Check exact filename matches
        if path.name in BOILERPLATE_FILENAMES:
            logger.info(f"[Boilerplate] Excluded based on filename match: {path.name}")
            return True
            
        # 2. Check file hash signature
        if path.exists() and path.is_file():
            try:
                with open(path, "rb") as f:
                    content = f.read()
                    file_md5 = hashlib.md5(content).hexdigest()
                    if file_md5 in KNOWN_BOILERPLATE_HASHES:
                        logger.info(f"[Boilerplate] Excluded based on template signature MD5: {file_md5}")
                        return True
            except Exception as e:
                logger.warning(f"Could not compute hash for {file_path}: {e}")
                
        return False

    @classmethod
    def clean_license_headers(cls, source_code: str) -> str:
        """
        Scans comments at the beginning of source files and removes standard open-source
        license headers (MIT, Apache, GPL) to avoid matching common header licenses.
        """
        lines = source_code.splitlines()
        cleaned_lines = []
        in_header = True
        
        for line in lines:
            stripped = line.strip()
            # If line is comment and we are looking at the header
            if in_header and (stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*") or stripped.endswith("*/") or not stripped):
                # If comment matches license patterns, discard it
                if LICENSE_REGEX.search(stripped):
                    continue
            else:
                # Stop looking for license header once we encounter normal code
                in_header = False
                
            cleaned_lines.append(line)
            
        return "\n".join(cleaned_lines)

    @classmethod
    def calculate_boilerplate_ratio(cls, source_code: str) -> float:
        """
        Parses source code into an AST and calculates the ratio of boilerplate framework statements
        (imports, default initializations, CORS setups) compared to total AST statements.
        
        Returns:
            A ratio float between 0.0 and 1.0.
        """
        if not source_code.strip():
            return 0.0
            
        try:
            tree = ast.parse(source_code)
        except Exception:
            # If invalid syntax, fall back to basic regex ratios
            return cls._calculate_regex_ratio(source_code)
            
        total_nodes = 0
        boilerplate_nodes = 0
        
        # Standard boilerplate definitions
        boilerplate_keywords = {"fastapi", "flask", "django", "cors", "middleware", "import", "config"}
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                boilerplate_nodes += 1
                total_nodes += 1
            elif isinstance(node, ast.Assign):
                total_nodes += 1
                # Check if assign value relates to boilerplate setup (e.g. app = FastAPI())
                node_str = ast.unparse(node).lower()
                if any(kw in node_str for kw in boilerplate_keywords):
                    boilerplate_nodes += 1
            elif isinstance(node, ast.Expr):
                total_nodes += 1
                node_str = ast.unparse(node).lower()
                if any(kw in node_str for kw in boilerplate_keywords):
                    boilerplate_nodes += 1
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                total_nodes += 1
                
        if total_nodes == 0:
            return 0.0
            
        return boilerplate_nodes / total_nodes

    @classmethod
    def _calculate_regex_ratio(cls, source_code: str) -> float:
        """
        Fallback line-based regex ratio calculation for non-Python or syntax-invalid files.
        """
        lines = source_code.splitlines()
        if not lines:
            return 0.0
            
        boilerplate_lines = 0
        boilerplate_indicators = re.compile(
            r"(?i)(import |from |require\(|app\.use|app\.add_middleware|cors|middleware|settings|config)"
        )
        
        for line in lines:
            if boilerplate_indicators.search(line):
                boilerplate_lines += 1
                
        return boilerplate_lines / len(lines)

    @classmethod
    def should_exclude_source(cls, source_code: str, threshold: float = 0.70) -> bool:
        """
        Helper method checking if the code snippet has a boilerplate ratio higher than the threshold.
        """
        ratio = cls.calculate_boilerplate_ratio(source_code)
        if ratio >= threshold:
            logger.info(f"[Boilerplate] Excluded based on ratio: {ratio:.2f} >= {threshold:.2f}")
            return True
        return False

if __name__ == "__main__":
    # Test inputs
    test_code = """# MIT License
# Copyright (c) 2026 Developer
# All rights reserved.

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware)

def get_user_profile(user_id):
    # Core logic
    return {"user_id": user_id, "name": "Alice"}
"""
    print("="*60)
    print("BOILERPLATE FILTER SELF-TEST:")
    print("="*60)
    print("1. Testing license header cleaning:")
    cleaned = BoilerplateFilter.clean_license_headers(test_code)
    print(cleaned)
    print("2. Testing ratio calculation:")
    ratio = BoilerplateFilter.calculate_boilerplate_ratio(test_code)
    print(f"Calculated Boilerplate Ratio: {ratio:.4f}")
    exclude = BoilerplateFilter.should_exclude_source(test_code, threshold=0.60)
    print(f"Should exclude (threshold=0.60)? {exclude}")
    print("="*60)
