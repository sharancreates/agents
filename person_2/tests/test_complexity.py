import pytest
from person_2.core.complexity import CyclomaticComplexityCalculator

def test_cyclomatic_complexity_simple_function():
    code = """
def simple_add(a, b):
    return a + b
"""
    calculator = CyclomaticComplexityCalculator()
    score = calculator.calculate_complexity(code, "python")
    assert score >= 1

def test_cyclomatic_complexity_branching():
    code = """
def check_value(x):
    if x > 10:
        return "high"
    elif x > 5:
        return "medium"
    else:
        return "low"
"""
    calculator = CyclomaticComplexityCalculator()
    score = calculator.calculate_complexity(code, "python")
    assert score >= 3