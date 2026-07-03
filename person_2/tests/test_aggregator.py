import os
import pytest
from person_2.core.aggregator import MetricsAggregator

def test_empty_or_missing_directory_graceful_handling():
    result = MetricsAggregator.evaluate_directory("invalid/non_existent_path")
    assert result["summary"]["total_files_evaluated"] == 0
    assert result["summary"]["overall_maintainability_rating"] == "HIGH"
    assert len(result["file_breakdown"]) == 0

def test_mock_directory_structural_parsing_evaluation(tmpdir):
    # Setup temporary directory structures matching active files
    test_file = tmpdir.join("sample_script.py")
    test_file.write("def main_calculation_process():\n    print('Hello World')\n")
    
    result = MetricsAggregator.evaluate_directory(str(tmpdir))
    
    assert result["summary"]["total_files_evaluated"] == 1
    assert "average_cyclomatic_complexity" in result["metrics"]
    assert len(result["file_breakdown"]) == 1
    assert result["file_breakdown"][0]["language"] == "python"