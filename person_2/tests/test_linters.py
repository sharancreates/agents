import pytest
from unittest.mock import patch, MagicMock
from agents.person_2.core.linters import LinterExecutionEngine

@patch("os.path.exists")
@patch("subprocess.run")
def test_ruff_violation_parsing(mock_run, mock_exists):
    mock_exists.return_value = True
    
    # Mock a standard json output payload string from ruff
    mock_response = MagicMock()
    mock_response.stdout = '[{"code": "F401", "message": "`os` imported but unused", "location": {"row": 1, "column": 8}}]'
    mock_run.return_value = mock_response
    
    issues = LinterExecutionEngine.execute_ruff("dummy.py")
    
    assert len(issues) == 1
    assert issues[0]["rule"] == "F401"
    assert "unused" in issues[0]["message"]

@patch("os.path.exists")
@patch("subprocess.run")
def test_eslint_violation_parsing(mock_run, mock_exists):
    mock_exists.return_value = True
    
    mock_response = MagicMock()
    mock_response.stdout = '[{"messages": [{"ruleId": "no-unused-vars", "message": "\'x\' is defined but never used", "line": 2, "column": 5, "severity": 2}]}]'
    mock_run.return_value = mock_response
    
    issues = LinterExecutionEngine.execute_eslint("dummy.js")
    
    assert len(issues) == 1
    assert issues[0]["rule"] == "no-unused-vars"
    assert issues[0]["severity"] == "error"