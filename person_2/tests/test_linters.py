import pytest
from person_2.core.linters import LinterExecutionEngine

def test_linter_engine_initialization():
    engine = LinterExecutionEngine()
    assert engine is not None

def test_linter_execution_fallback():
    engine = LinterExecutionEngine()
    result = engine.run_static_analysis(source_code="print('hello')", language="python")
    assert isinstance(result, dict)