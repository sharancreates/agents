import re
from typing import List, Dict, Any

class CodeSmellDetector:
    """Evaluates multi-language code quality rules and detects security vulnerabilities."""

    @classmethod
    def check_long_functions(cls, root_node: Any, max_lines: int = 20) -> List[Dict[str, Any]]:
        """Compatibility interface for long function validation checks supporting both native AST and mock objects."""
        smells = []
        if not root_node:
            return smells
            
        if type(root_node).__name__ == 'ParsedTreeResult':
            if isinstance(root_node.get("total_lines"), int) and root_node["total_lines"] > max_lines:
                smells.append({
                    "type": "long_function",
                    "rule": "Long Function Block",
                    "severity": "WARNING",
                    "line": 1,
                    "message": f"Code baseline exceeds standard execution limits ({root_node['total_lines']} lines)."
                })
            return smells

        # Process AST or mock structures safely via standard stack traversal
        nodes_to_visit = [root_node]
        while nodes_to_visit:
            current = nodes_to_visit.pop()
            
            current_type = getattr(current, "type", None)
            if current_type is not None:
                type_str = str(current_type)
                if "function_definition" in type_str or "def_statement" in type_str:
                    start_point = getattr(current, "start_point", (0, 0))
                    end_point = getattr(current, "end_point", (0, 0))
                    
                    start_line = start_point[0] if isinstance(start_point, tuple) else getattr(start_point, "line", 0)
                    end_line = end_point[0] if isinstance(end_point, tuple) else getattr(end_point, "line", 0)
                    
                    if (end_line - start_line) > max_lines:
                        smells.append({
                            "type": "long_function",
                            "rule": "Long Function Block",
                            "severity": "WARNING",
                            "line": start_line + 1,
                            "message": "Function body execution layout spans too many logical paths."
                        })

            # Check for direct child list configurations or alternative lambda implementations
            children = getattr(current, "children", None)
            if children and isinstance(children, list):
                nodes_to_visit.extend(children)
            elif hasattr(current, "child_count") and hasattr(current, "child"):
                try:
                    count = int(getattr(current, "child_count", 0))
                    for idx in range(count):
                        nodes_to_visit.append(current.child(idx))
                except Exception:
                    pass
                
        return smells

    @classmethod
    def check_deep_nesting(cls, root_node: Any, max_depth: int = 3) -> List[Dict[str, Any]]:
        """Compatibility interface for code block nesting validation checks supporting both native AST and mock objects."""
        smells = []
        if not root_node:
            return smells

        if type(root_node).__name__ == 'ParsedTreeResult':
            content = root_node.get("raw_content", "")
            if "if" in content and content.count("    ") > max_depth * 2:
                smells.append({
                    "type": "deep_nesting",
                    "rule": "Deep Nesting Block",
                    "severity": "WARNING",
                    "line": 1,
                    "message": "Block architecture patterns present elevated nesting indices."
                })
            return smells

        def crawl_depth(node, current_depth):
            if current_depth > max_depth:
                start_point = getattr(node, "start_point", (0, 0))
                line_no = start_point[0] if isinstance(start_point, tuple) else getattr(start_point, "line", 0)
                smells.append({
                    "type": "deep_nesting",
                    "rule": "Deep Nesting Block",
                    "severity": "WARNING",
                    "line": line_no + 1,
                    "message": "Architecture paths exhibit complex nesting depth profiles."
                })
                return
            
            # Traversal strategy matching either standard list elements or functional child models
            children = getattr(node, "children", None)
            if children and isinstance(children, list):
                for child in children:
                    child_type = getattr(child, "type", "")
                    type_str = str(child_type) if child_type is not None else ""
                    is_branch = any(k in type_str for k in ("if", "for", "while", "except", "definition", "statement"))
                    crawl_depth(child, current_depth + 1 if is_branch else current_depth)
            elif hasattr(node, "child_count") and hasattr(node, "child"):
                try:
                    count = int(getattr(node, "child_count", 0))
                    for idx in range(count):
                        child = node.child(idx)
                        child_type = getattr(child, "type", "")
                        type_str = str(child_type) if child_type is not None else ""
                        is_branch = any(k in type_str for k in ("if", "for", "while", "except", "definition", "statement"))
                        crawl_depth(child, current_depth + 1 if is_branch else current_depth)
                except Exception:
                    pass

        crawl_depth(root_node, 0)
        return smells

    @classmethod
    def analyze_node(cls, root_node: Any) -> List[Dict[str, Any]]:
        """Combines classic code smell checkers with our advanced multi-language and security sweeps."""
        smells = []
        if not root_node or type(root_node).__name__ != 'ParsedTreeResult':
            return smells

        smells.extend(cls.check_long_functions(root_node))
        smells.extend(cls.check_deep_nesting(root_node))

        lang = root_node["language"]
        content = root_node["raw_content"]

        # --- Security Vulnerability Scanner ---
        security_patterns = {
            "Hardcoded API Secret": r'(?i)(api_key|secret|token|password|passwd)\s*=\s*[\'"][a-zA-Z0-9_\-]{8,}[\'"]',
            "Unsafe Command Execution": r'\b(exec|eval|os\.system|child_process\.exec)\b'
        }

        for rule_name, pattern in security_patterns.items():
            matches = re.finditer(pattern, content)
            for match in matches:
                line_no = content[:match.start()].count("\n") + 1
                smells.append({
                    "type": "SECURITY_VULNERABILITY",
                    "rule": rule_name,
                    "severity": "CRITICAL",
                    "line": line_no,
                    "message": f"Critical risk detected: Flagged potential '{rule_name}' matching footprint."
                })

        # --- Language Specific Code Smells ---
        if lang in ("javascript", "typescript"):
            js_smells = {
                "Production Debugger Log": (r'\bconsole\.log\([^)]*\)', "Avoid leaving active console.log telemetry in production scripts."),
                "Nested Callback Pattern": (r'\)\s*=>\s*\{\s*.*=>\s*\{\s*.*=>', "High nesting warning: Detected deep callback chain pattern matching layout.")
            }
            for smell_name, (pattern, msg) in js_smells.items():
                for match in re.finditer(pattern, content):
                    line_no = content[:match.start()].count("\n") + 1
                    smells.append({
                        "type": "CODE_SMELL",
                        "rule": smell_name,
                        "severity": "WARNING",
                        "line": line_no,
                        "message": msg
                    })

        elif lang == "python":
            match = re.search(r'\bexcept\s*:', content)
            if match:
                line_no = content[:match.start()].count("\n") + 1
                smells.append({
                    "type": "CODE_SMELL",
                    "rule": "Bare Except Clause",
                    "severity": "WARNING",
                    "line": line_no,
                    "message": "Flagged empty or bare except catch-block. Masking runtime exceptions degrades safety."
                })

        return smells