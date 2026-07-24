"""
Automated Test Runner for Operational CLI.
Verifies CLI execution flows over mock test workspace directories.
"""

import os
import shutil
import tempfile
from cli import OriginalityCLI

def run_cli_tests():
    print("=" * 60)
    print("RUNNING DAY 22: OPERATIONAL CLI RUNNER TESTS")
    print("=" * 60)

    # Create temporary workspace folder
    temp_dir = tempfile.mkdtemp()
    try:
        sample_file = os.path.join(temp_dir, "app.py")
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write("def main():\n    # Hindi comment: मुख्य फ़ंक्शन\n    print('Hello World')\n")

        cli = OriginalityCLI()
        matrix = cli.evaluate_directory(temp_dir, submission_id="CLI_TEST_RUN")

        print(f"CLI Evaluation Completed -> Submission ID: {matrix['submission_id']}")
        print(f"Composite Score: {matrix['composite_originality_score']} | Verdict: {matrix['verdict']}")

        assert matrix["submission_id"] == "CLI_TEST_RUN"
        assert matrix["composite_originality_score"] > 0.0
        assert "verdict" in matrix

        print("-" * 60)
        print("OPERATIONAL CLI TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)

    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    run_cli_tests()