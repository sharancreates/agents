import pytest
from person_2.core.complexity import CyclomaticComplexityCalculator

def test_cyclomatic_complexity_simple_function():
    code = "def simple_add(a, b):\n    return a + b\n"
    calculator = CyclomaticComplexityCalculator()
    score = calculator.calculate_complexity(code, "python")
    assert score >= 1

def test_cyclomatic_complexity_branching():
    code = "def check_value(x):\n    if x > 10:\n        return 'high'\n    elif x > 5:\n        return 'medium'\n    else:\n        return 'low'\n"
    calculator = CyclomaticComplexityCalculator()
    score = calculator.calculate_complexity(code, "python")
    assert score >= 1