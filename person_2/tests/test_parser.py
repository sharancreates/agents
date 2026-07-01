import pytest
from unittest.mock import patch
from agents.person_2.core.parser import TreeSitterRegistry

@patch("os.path.exists")
def test_register_language_runtime(mock_exists):
    # Force the path validation check to return True
    mock_exists.return_value = True
    
    engine = TreeSitterRegistry()
    # Register language using our secure cross-platform registration path
    engine.register_language("python", "agents/person_2/vendor/tree-sitter-grammars/python.so")
    
    # Assert registration completed successfully
    assert "python" in engine.parsers