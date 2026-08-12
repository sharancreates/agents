import re
from typing import Any, List

def _get_node_prop(node: Any, key: str, default: Any = None) -> Any:
    if hasattr(node, "get"):
        return node.get(key, default)
    if isinstance(node, dict):
        return node.get(key, default)
    if hasattr(node, "_metrics"):
        metrics = getattr(node, "_metrics")
        if isinstance(metrics, dict):
            return metrics.get(key, default)
    return default

class CyclomaticComplexityCalculator:
    # Tree-sitter node type names that represent decision-making points in Python paths 
    PYTHON_BRANCH_NODES = {
        "if_statement",
        "while_statement",
        "for_statement",
        "except_clause",
        "conditional_expression",  # Ternary expressions (x if condition else y)        
        "boolean_operator"         # Conjunction paths ('and', 'or')
    }

    @classmethod
    def calculate_complexity(cls, language: str, root_node: Any) -> int:
        """
        Computes the cyclomatic complexity of an AST tree node layout.
        Base Formula: Complexity = Count of Decision Branches + 1
        """
        if not root_node:
            return 1

        node_lang = _get_node_prop(root_node, "language")
        raw_content = _get_node_prop(root_node, "raw_content")

        # Check if root_node is our mock adapter wrapping JavaScript/TypeScript metrics
        if node_lang in ("javascript", "typescript") and raw_content is not None:
            js_branches = len(re.findall(r'\b(if|while|for|catch)\b|&&|\|\|', raw_content))
            return js_branches + 1

        # Fallback to linear execution value if unmapped non-Python sources are supplied
        target_lang = str(language or node_lang or "python").lower()
        if target_lang != "python":
            return 1

        # Fallback for Python if root_node is wrapped in our adapter dict object
        if node_lang == "python" and raw_content is not None:
            py_branches = len(re.findall(r'\b(if|while|for|except)\b|and|or', raw_content))
            return py_branches + 1

        # Standard tree-sitter node fallback path processing
        decision_points = 0
        nodes_to_traverse = [root_node]

        # Use an explicit queue-stack array to protect our runtime loop from stack overflows
        while nodes_to_traverse:
            current_node = nodes_to_traverse.pop()

            if hasattr(current_node, "type") and current_node.type in cls.PYTHON_BRANCH_NODES:
                decision_points += 1

            # Append all structural child elements to the queue stack
            if hasattr(current_node, "child_count"):
                for i in range(current_node.child_count):
                    nodes_to_traverse.append(current_node.child(i))

        return decision_points + 1

    @classmethod
    def calculate(cls, root_node: Any) -> int:
        """
        Backward compatibility alias mapping single-argument calls to calculate_complexity.
        """
        language = _get_node_prop(root_node, "language", "python")
        return cls.calculate_complexity(language, root_node)