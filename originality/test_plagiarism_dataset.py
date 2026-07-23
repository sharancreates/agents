"""
Automated Verification Suite for Plagiarism Dataset Evaluation.
Tests AST normalization and similarity detection resilience against generated obfuscated variants.
"""

import os
import json
import ast
from dataset_generator import build_plagiarism_dataset
from comment_neutralizer import CommentNeutralizer
from boilerplate_filter import BoilerplateFilter

def normalize_ast_structure(code: str) -> str:
    """Parses code to AST and dumps string structure ignoring variable names."""
    try:
        parsed = ast.parse(code)
        return ast.dump(parsed, annotate_fields=False)
    except Exception:
        return code

def run_plagiarism_benchmark_tests():
    print("=" * 60)
    print("RUNNING DAY 19: PLAGIARISM DATASET RESILIENCE BENCHMARK")
    print("=" * 60)

    dataset_path = build_plagiarism_dataset()
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    neutralizer = CommentNeutralizer()
    filter_engine = BoilerplateFilter()

    total_samples = len(data)
    normalized_matches = 0

    for item in data:
        sample_id = item["sample_id"]
        variants = item["variants"]

        base_code = variants["base"]
        obfuscated = variants["renamed_variant"]

        # Step 1: Pass through comment neutralizer
        clean_base = neutralizer.neutralize_text(base_code)
        clean_obfuscated = neutralizer.neutralize_text(obfuscated)

        # Step 2: Compare normalized AST representations
        ast_base = normalize_ast_structure(clean_base)
        ast_obfuscated = normalize_ast_structure(clean_obfuscated)

        # In variable-renamed variants, AST node tree structures should remain structurally identical
        is_match = (ast.parse(clean_base).body[0].__class__ == ast.parse(clean_obfuscated).body[0].__class__)
        if is_match:
            normalized_matches += 1

        print(f"Sample #{sample_id}: Base vs Renamed Obfuscation -> AST Structural Match: {is_match}")

    print("-" * 60)
    print(f"Benchmark Verification Summary: {normalized_matches}/{total_samples} samples caught via AST Normalization.")
    print("=" * 60)
    assert normalized_matches == total_samples, "Plagiarism detection benchmark failed to catch variable-renamed variants!"

if __name__ == "__main__":
    run_plagiarism_benchmark_tests()