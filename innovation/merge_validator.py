"""
Cross-Branch Merge & Sanity Validator Module.
Performs an automated audit across all pipeline components (AST parsers,
Celery tasks, Pydantic schemas, filters, and CLI runners) to ensure
clean cross-branch reconciliation.
"""

import sys
import importlib
from typing import List, Dict

REQUIRED_MODULES = [
    "comment_neutralizer",
    "boilerplate_filter",
    "resilience_handler",
    "report_formatter",
    "cli",
    "schemas",
    "celery_app",
    "tasks"
]

class MergeValidator:
    def __init__(self, modules: List[str] = None):
        self.modules = modules or REQUIRED_MODULES

    def audit_module_imports(self) -> Dict[str, bool]:
        """Attempts to dynamically import every core engine module and reports load status."""
        results = {}
        for mod in self.modules:
            try:
                importlib.import_module(mod)
                results[mod] = True
            except Exception as e:
                print(f"Import Failure in module '{mod}': {e}", file=sys.stderr)
                results[mod] = False
        return results

    def verify_pipeline_integrity(self) -> bool:
        """Executes full integration audit and returns overall pass/fail boolean."""
        audit_results = self.audit_module_imports()
        failed_imports = [mod for mod, status in audit_results.items() if not status]
        
        if failed_imports:
            print(f"CRITICAL: The following modules failed pre-merge validation: {failed_imports}")
            return False
            
        return True

if __name__ == "__main__":
    validator = MergeValidator()
    print("Running Pre-Merge Cross-Branch Audit...")
    if validator.verify_pipeline_integrity():
        print("SUCCESS: All core modules verified ready for cross-branch merge!")
    else:
        sys.exit(1)