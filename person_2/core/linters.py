import os
import json
import subprocess
from typing import Dict, List, Any

class LinterExecutionEngine:
    @classmethod
    def execute_ruff(cls, file_path: str) -> List[Dict[str, Any]]:
        """
        Executes the Ruff linter via an isolated subprocess on a Python target file
        and parses its structured JSON output report.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Python target file missing for linter pass: {file_path}")

        # Run ruff with explicit json output parameters
        command = ["ruff", "check", file_path, "--output-format", "json"]
        
        try:
            # We allow non-zero exit codes (1) since linting violations count as errors
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=15.0
            )
            
            if not result.stdout.strip():
                return []
                
            violations = json.loads(result.stdout)
            return [
                {
                    "rule": v.get("code"),
                    "message": v.get("message"),
                    "line": v.get("location", {}).get("row"),
                    "column": v.get("location", {}).get("column"),
                    "severity": "warning" if v.get("code", "").startswith("W") else "error"
                }
                for v in violations
            ]
        except subprocess.TimeoutExpired:
            return [{"rule": "TIMEOUT", "message": "Ruff execution exceeded security timeout limit.", "line": 0, "column": 0, "severity": "error"}]
        except Exception as e:
            return [{"rule": "LINTER_ERROR", "message": f"Failed to execute ruff: {str(e)}", "line": 0, "column": 0, "severity": "error"}]

    @classmethod
    def execute_eslint(cls, file_path: str) -> List[Dict[str, Any]]:
        """
        Executes the ESLint engine via an isolated subprocess on a JS/TS target file
        and parses its structured JSON array report layout.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"JavaScript target file missing for linter pass: {file_path}")

        command = ["npx", "eslint", file_path, "--format", "json"]
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=20.0
            )
            
            if not result.stdout.strip():
                return []
                
            report = json.loads(result.stdout)
            # ESLint wraps structural errors per file inside an array layout
            if not report or not isinstance(report, list):
                return []
                
            messages = report[0].get("messages", [])
            return [
                {
                    "rule": m.get("ruleId"),
                    "message": m.get("message"),
                    "line": m.get("line"),
                    "column": m.get("column"),
                    "severity": "error" if m.get("severity") == 2 else "warning"
                }
                for m in messages
            ]
        except subprocess.TimeoutExpired:
            return [{"rule": "TIMEOUT", "message": "ESLint execution exceeded security timeout limit.", "line": 0, "column": 0, "severity": "error"}]
        except Exception as e:
            return [{"rule": "LINTER_ERROR", "message": f"Failed to execute eslint: {str(e)}", "line": 0, "column": 0, "severity": "error"}]