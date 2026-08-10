import os
from typing import Dict, Any, List
from person_2.core.detector import LanguageDetector
from person_2.core.parser import TreeSitterRegistry
from person_2.core.complexity import CyclomaticComplexityCalculator
from person_2.core.linters import LinterExecutionEngine
from person_2.core.rules import CodeSmellDetector

class MetricsAggregator:
    @classmethod
    def evaluate_directory(cls, dir_path: str) -> Dict[str, Any]:
        report = {
            "summary": {
                "total_files_evaluated": 0,
                "overall_maintainability_rating": "HIGH",
                "global_issue_count": 0
            },
            "metrics": {
                "average_cyclomatic_complexity": 1.0,
                "max_complexity_observed": 1
            },
            "file_breakdown": []
        }

        if not os.path.isdir(dir_path):
            return report

        total_complexity = 0
        max_complexity = 1
        file_count = 0
        total_issues = 0

        # Create instance to inspect methods safely
        detector = LanguageDetector()

        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check absolute variations of what your Day 1 class provides
                if hasattr(detector, 'detect_language'):
                    lang = detector.detect_language(file_path)
                elif hasattr(detector, 'detect'):
                    lang = detector.detect(file_path)
                elif hasattr(LanguageDetector, 'detect_language'):
                    lang = LanguageDetector.detect_language(file_path)
                elif hasattr(LanguageDetector, 'detect'):
                    lang = LanguageDetector.detect(file_path)
                else:
                    # Fallback default extension deduction if your Day 1 class names don't match
                    ext = os.path.splitext(file_path)[1]
                    lang = "python" if ext == ".py" else "javascript" if ext in (".js", ".ts") else "unknown"
                
                if lang in ("unknown", "text") or not lang:
                    continue
                    
                file_count += 1
                
                tree = TreeSitterRegistry.parse_file(file_path, lang)
                root_node = tree.root_node if tree else None
                
                complexity = CyclomaticComplexityCalculator.calculate(root_node) if root_node else 1
                long_funcs = CodeSmellDetector.check_long_functions(root_node) if root_node else []
                deep_nests = CodeSmellDetector.check_deep_nesting(root_node) if root_node else []
                
                linter_issues = []
                if lang == "python":
                    linter_issues = LinterExecutionEngine.execute_ruff(file_path)
                elif lang in ("javascript", "typescript"):
                    linter_issues = LinterExecutionEngine.execute_eslint(file_path)

                total_complexity += complexity
                if complexity > max_complexity:
                    max_complexity = complexity

                issue_pool_size = len(long_funcs) + len(deep_nests) + len(linter_issues)
                total_issues += issue_pool_size

                report["file_breakdown"].append({
                    "file_path": os.path.relpath(file_path, dir_path),
                    "language": lang,
                    "cyclomatic_complexity": complexity,
                    "issues_found": issue_pool_size,
                    "smells": long_funcs + deep_nests
                })

        if file_count > 0:
            avg_complexity = round(total_complexity / file_count, 2)
            report["summary"]["total_files_evaluated"] = file_count
            report["summary"]["global_issue_count"] = total_issues
            report["metrics"]["average_cyclomatic_complexity"] = avg_complexity
            report["metrics"]["max_complexity_observed"] = max_complexity
            
            if max_complexity > 15 or total_issues > 25:
                report["summary"]["overall_maintainability_rating"] = "CRITICAL_RISK"
            elif max_complexity > 8 or total_issues > 10:
                report["summary"]["overall_maintainability_rating"] = "MEDIUM_RISK"
            else:
                report["summary"]["overall_maintainability_rating"] = "HIGH"

        return report