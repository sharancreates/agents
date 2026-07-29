import pytest
from person_2.core.linters import LinterExecutionEngine

def test_linter_engine_initialization():
    engine = LinterExecutionEngine()
    assert engine is not None

def test_linter_execution_fallback(tmpdir):
    test_file = tmpdir.join("test_script.py")
    test_file.write("print('hello')\n")
    
    engine = LinterExecutionEngine()
    result = engine.run_linter(file_path=str(test_file), language="python")
    assert isinstance(result, (list, dict))