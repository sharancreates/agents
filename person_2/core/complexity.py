from typing import Any, List

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

        # Fallback to linear execution value if non-Python sources are supplied for now
        if language.lower() != "python":
            return 1

        decision_points = 0
        nodes_to_traverse = [root_node]

        # Use an explicit queue-stack array to protect our runtime loop from stack overflows
        while nodes_to_traverse:
            current_node = nodes_to_traverse.pop()
            
            if current_node.type in cls.PYTHON_BRANCH_NODES:
                decision_points += 1

            # Append all structural child elements to the queue stack
            for i in range(current_node.child_count):
                nodes_to_traverse.append(current_node.child(i))

        return decision_points + 1