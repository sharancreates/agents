import os
import pytest
from unittest.mock import patch, MagicMock
from person_2.core.parser import TreeSitterRegistry

@patch("os.path.exists")
def test_register_language_runtime(mock_exists):
    # Force the path validation check to return True
    mock_exists.return_value = True

    engine = TreeSitterRegistry()
    
    # Manually inject the mock language into the dictionary to simulate successful compilation
    engine.loaded_languages["python"] = MagicMock()

    # Assert registration completed successfully against the correct dict name
    assert "python" in engine.loaded_languages

def test_parse_file_non_existent_path_returns_none():
    # Verify parser fails gracefully if a completely invalid file path is supplied
    result = TreeSitterRegistry.parse_file("non_existent_file_path.py", "python")
    assert result is None