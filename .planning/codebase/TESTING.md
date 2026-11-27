# Testing Infrastructure & Test Plan

## 1. Test Framework & Setup
- **Framework**: `pytest`
- **Execution**: Can be executed via `pytest` from the project root or subdirectories.
- **Test Locations**:
  - `person_2/tests/`: Unit and component tests for Static Code Quality and Dynamic Functionality.
  - `originality/test_*.py`: Standalone test scripts for originality calibration, CLI, and integration.

## 2. Test Suites Breakdown
### Person 2 Tests (`person_2/tests/`)
- `test_aggregator.py`: Validates end-to-end directory traversal and composite metrics calculation.
- `test_complexity.py`: Tests tree-sitter cyclomatic complexity scoring on mock Python and JS code snippets.
- `test_detector.py`: Tests language identification across various file extensions.
- `test_functionality.py`: Tests `DynamicExecutionRunner`, timeout enforcement, and memory calculation.
- `test_linters.py`: Tests Ruff and ESLint CLI invocation and error parsing.
- `test_parser.py`: Tests tree-sitter AST parser initialization and syntax error handling.
- `test_rules.py`: Tests code smell detection rules (long functions, deep nesting).
- `test_api.py`: Tests internal FastAPI endpoints in `person_2/api/`.

### Originality Tests (`originality/`)
- `test_calibration.py`: Tests similarity threshold tuning for plagiarism detection.
- `test_cli_runner.py`: Tests CLI execution options.
- `test_continuous_pipeline.py`: Tests embedding creation and vector insertion loops.
- `test_cross_branch_integration.py`: Tests cross-branch compatibility and merged reports.
- `test_latency_benchmarks.py`: Benchmarks vector query times against `pgvector`.
- `test_plagiarism_dataset.py`: Evaluates detection accuracy on synthetic plagiarism test cases.
- `test_unicode_neutralization.py`: Tests zero-width and homoglyph sanitization in code comments.

## 3. Testing Gaps & Areas for Improvement
- **Dynamic Test Generation**: Current functionality testing relies on hardcoded test inputs (`TestCaseInput(input_data="test", expected_output="test")`); tests need dynamic generation based on repository prompt requirements.
- **End-to-End CI Pipeline**: Full end-to-end integration test (FastAPI -> Celery -> Postgres -> Frontend) is not yet wired into GitHub Actions.
