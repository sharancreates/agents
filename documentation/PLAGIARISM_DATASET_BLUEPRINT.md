# Plagiarism Dataset & Obfuscation Blueprint

This blueprint describes the ground-truth target dataset generation and benchmark verification engine added on Day 19 of the engineering sprint.

## Obfuscation Taxonomy & Techniques
1. **Variable Renaming**: Replaces identifiers with arbitrary names (`total` -> `acc_val`). Caught via AST normalization and token stripping.
2. **Dead Code Injection**: Injects unexecuted branches, dummy computations, and comments. Filtered via AST statement pruning and comment neutralization.
3. **Loop Refactoring**: Converts `for` iteration constructs to `while` loops. Normalized via expression flattening.
4. **Structural Swapping**: Reorders independent functions within a file payload. Handled via individual function-level AST slicing.

## Benchmark Verification Metrics
- **AST Structural Alignment**: Asserts high-similarity node mapping across variable-renamed pairs.
- **Noise Resilience**: Verifies dead code injection does not drop similarity below detection thresholds.

The implementation files reside in:
- `agents/originality/dataset_generator.py`
- `agents/originality/test_plagiarism_dataset.py`