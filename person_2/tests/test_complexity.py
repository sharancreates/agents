import pytest
from unittest.mock import MagicMock
from typing import List  # Added missing import to resolve NameError
from agents.person_2.core.complexity import CyclomaticComplexityCalculator

def mock_node_factory(node_type: str, children_nodes: List[MagicMock] = None) -> MagicMock:
    """Helper mock factory to mimic Tree-sitter tree elements safely."""
    node = MagicMock()
    node.type = node_type
    children = children_nodes or []
    node.child_count = len(children)
    node.child = lambda index: children[index]
    return node

def test_flat_linear_code_complexity():
    # Arrangement: Sequential expression rows with no conditional changes
    root = mock_node_factory("module", [
        mock_node_factory("expression_statement"),
        mock_node_factory("assignment")
    ])
    
    score = CyclomaticComplexityCalculator.calculate_complexity("python", root)
    assert score == 1

def test_single_conditional_branch_complexity():
    # Arrangement: Root containing one structural conditional block element
    if_node = mock_node_factory("if_statement", [mock_node_factory("block")])
    root = mock_node_factory("module", [if_node])
    
    score = CyclomaticComplexityCalculator.calculate_complexity("python", root)
    assert score == 2