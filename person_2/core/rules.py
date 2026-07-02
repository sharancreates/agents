from typing import List, Dict, Any

class CodeSmellDetector:
    @classmethod
    def check_long_functions(cls, root_node: Any, max_lines: int = 20) -> List[Dict[str, Any]]:
        """
        Scans the AST for function definitions that exceed the max_lines limit.
        """
        smells = []
        if not root_node:
            return smells

        nodes_to_visit = [root_node]
        while nodes_to_visit:
            current = nodes_to_visit.pop()
            
            if current.type in ("function_definition", "def_statement"):
                start_row = current.start_point[0]
                end_row = current.end_point[0]
                total_lines = end_row - start_row + 1
                
                if total_lines > max_lines:
                    smells.append({
                        "type": "long_function",
                        "message": f"Function exceeds maximum length limit ({total_lines}/{max_lines} lines).",
                        "line": start_row + 1
                    })
            
            for i in range(current.child_count):
                nodes_to_visit.append(current.child(i))
                
        return smells

    @classmethod
    def check_deep_nesting(cls, root_node: Any, max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        Scans the AST to find code blocks nested deeper than the max_depth threshold.
        """
        smells = []
        if not root_node:
            return smells

        # Using a tuple stack: (node, current_depth)
        nodes_to_visit = [(root_node, 0)]
        nesting_nodes = {"if_statement", "for_statement", "while_statement", "try_statement"}

        while nodes_to_visit:
            current, depth = nodes_to_visit.pop()
            
            if current.type in nesting_nodes:
                depth += 1
                if depth > max_depth:
                    smells.append({
                        "type": "deep_nesting",
                        "message": f"Code block nested too deep ({depth}/{max_depth}).",
                        "line": current.start_point[0] + 1
                    })

            for i in range(current.child_count):
                nodes_to_visit.append((current.child(i), depth))

        return smells