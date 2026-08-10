import pytest
from unittest.mock import MagicMock
from person_2.core.rules import CodeSmellDetector

def mock_node_with_points(node_type: str, start_row: int, end_row: int, children=None) -> MagicMock:
    node = MagicMock()
    node.type = node_type
    node.start_point = (start_row, 0)
    node.end_point = (end_row, 0)
    kids = children or []
    node.child_count = len(kids)
    node.child = lambda idx: kids[idx]
    return node

def test_long_function_detection():
    # A function block spanning 25 lines (exceeding default limit of 20)
    func_node = mock_node_with_points("function_definition", 10, 35)
    root = mock_node_with_points("module", 0, 40, [func_node])
    
    smells = CodeSmellDetector.check_long_functions(root, max_lines=20)
    assert len(smells) == 1
    assert smells[0]["type"] == "long_function"

def test_deep_nesting_detection():
    # Constructing nested blocks: if -> for -> while -> if (Depth 4)
    level_4 = mock_node_with_points("if_statement", 4, 5)
    level_3 = mock_node_with_points("while_statement", 3, 6, [level_4])
    level_2 = mock_node_with_points("for_statement", 2, 7, [level_3])
    level_1 = mock_node_with_points("if_statement", 1, 8, [level_2])
    root = mock_node_with_points("module", 0, 10, [level_1])
    
    smells = CodeSmellDetector.check_deep_nesting(root, max_depth=3)
    assert len(smells) == 1
    assert smells[0]["type"] == "deep_nesting"