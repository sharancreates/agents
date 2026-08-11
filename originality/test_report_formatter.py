"""
Automated Verification Suite for Report Formatter & Evaluation Matrix.
Tests score calculation weighting, status verdict flagging, and Markdown export completeness.
"""

from report_formatter import ReportFormatter

def run_report_formatter_tests():
    print("=" * 60)
    print("RUNNING DAY 21: REPORT FORMATTER & EVALUATION MATRIX TESTS")
    print("=" * 60)

    formatter = ReportFormatter()

    # Test Case 1: High quality unique submission
    matrix_passed = formatter.generate_evaluation_matrix(
        submission_id="TEST_PASS",
        similarity_metrics={"max_similarity": 0.05, "matched_blocks": 0},
        architecture_metrics={"scores": {"design_integrity": 0.9, "structural_novelty": 0.85, "readme_consistency": 0.95}},
        filtering_summary={"boilerplate_files_count": 2, "neutralized_comments_count": 5}
    )
    print(f"Test Pass Submission -> Verdict: {matrix_passed['verdict']} | Score: {matrix_passed['composite_originality_score']}")
    assert matrix_passed["verdict"] == "PASSED"

    # Test Case 2: Plagiarized / Low quality submission
    matrix_flagged = formatter.generate_evaluation_matrix(
        submission_id="TEST_FLAG",
        similarity_metrics={"max_similarity": 0.85, "matched_blocks": 8},
        architecture_metrics={"scores": {"design_integrity": 0.2, "structural_novelty": 0.1, "readme_consistency": 0.3}},
        filtering_summary={"boilerplate_files_count": 0, "neutralized_comments_count": 0}
    )
    print(f"Test Flag Submission -> Verdict: {matrix_flagged['verdict']} | Score: {matrix_flagged['composite_originality_score']}")
    assert matrix_flagged["verdict"] == "FLAGGED"

    # Test Case 3: Markdown Export Validation
    md_output = formatter.export_markdown_report(matrix_passed)
    assert "# Originality & Architecture Evaluation Report" in md_output
    assert "`TEST_PASS`" in md_output

    print("-" * 60)
    print("ALL REPORT FORMATTER & MATRIX TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_report_formatter_tests()