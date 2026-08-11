"""
Automated Test Suite for Cross-Branch Merge Validation.
Verifies module integrity, dependency trees, and branch readiness.
"""

from merge_validator import MergeValidator

def run_cross_branch_tests():
    print("=" * 60)
    print("RUNNING DAY 23: CROSS-BRANCH INTEGRATION & MERGE SANITY TESTS")
    print("=" * 60)

    validator = MergeValidator()
    results = validator.audit_module_imports()

    passed_count = sum(1 for status in results.values() if status)
    total_count = len(results)

    for mod, status in results.items():
        state_str = "PASSED" if status else "FAILED"
        print(f"Module Audit: {mod:<25} | Status: {state_str}")

    print("-" * 60)
    print(f"Merge Audit Summary: {passed_count}/{total_count} modules verified.")
    print("=" * 60)

    assert passed_count == total_count, "Cross-branch merge audit failed! Fix broken imports before merging."
    print("ALL CROSS-BRANCH PRE-MERGE SANITY TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_cross_branch_tests()