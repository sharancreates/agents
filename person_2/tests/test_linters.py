import pytest
from person_2.core.linters import LinterExecutionEngine

def test_linter_engine_initialization():
    engine = LinterExecutionEngine()
    assert engine is not None

def test_linter_execution_fallback(tmpdir):
    test_file = tmpdir.join("test_script.py")
    test_file.write("print('hello')\n")
    
    engine = LinterExecutionEngine()
    method = getattr(engine, "run_linters", getattr(engine, "run_linter", getattr(engine, "run", None)))
    result = method(str(test_file))
    assert isinstance(result, (list, dict))