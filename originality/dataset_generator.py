"""
Dataset Generator for Plagiarism & Similarity Benchmarking.
Generates base Python functions and transforms them using common code obfuscation
techniques: variable renaming, dead code injection, loop transformation, and structural reordering.
"""

import os
import json
import random
import ast

class PlagiarismObfuscator:
    def __init__(self):
        self.variable_map = {
            "total": "acc_val",
            "items": "data_list",
            "index": "cursor_pos",
            "result": "output_res",
            "count": "tally_num"
        }

    def rename_variables(self, code: str) -> str:
        """Replaces common variable names with arbitrary identifier names."""
        transformed = code
        for orig, new_name in self.variable_map.items():
            transformed = transformed.replace(orig, new_name)
        return transformed

    def inject_dead_code(self, code: str) -> str:
        """Injects non-functional dead code statements into function bodies."""
        dead_lines = [
            "    _dummy_check = 100 * 2\n",
            "    # Internal buffer initialization\n",
            "    _unused_var = [i for i in range(5)]\n",
            "    if False:\n        print('Unreachable execution branch')\n"
        ]
        lines = code.splitlines(True)
        if len(lines) > 2:
            insert_pos = len(lines) // 2
            lines.insert(insert_pos, random.choice(dead_lines))
        return "".join(lines)

    def refactor_loops(self, code: str) -> str:
        """Converts standard for-loops to while-loops or list comprehensions where applicable."""
        # Simple string-level transformation substitute for benchmark pair creation
        if "for i in range(" in code:
            code = code.replace("for i in range(", "i = 0\n    while i < ")
            code = code.replace("):", ":\n        # loop body\n        i += 1")
        return code

    def generate_benchmark_pair(self, base_code: str) -> dict:
        """Generates ground-truth obfuscated variants from a base code snippet."""
        renamed = self.rename_variables(base_code)
        dead_code = self.inject_dead_code(renamed)
        refactored = self.refactor_loops(dead_code)

        return {
            "base": base_code,
            "renamed_variant": renamed,
            "dead_code_variant": dead_code,
            "fully_obfuscated_variant": refactored
        }

def build_plagiarism_dataset(output_dir: str = "benchmark_dataset") -> str:
    """Generates and writes a benchmark dataset JSON payload."""
    obfuscator = PlagiarismObfuscator()
    sample_codes = [
        """def calculate_sum(items):\n    total = 0\n    for index in range(len(items)):\n        total += items[index]\n    return total""",
        """def find_maximum(data_list):\n    result = data_list[0]\n    for count in range(1, len(data_list)):\n        if data_list[count] > result:\n            result = data_list[count]\n    return result""",
        """def filter_even_numbers(numbers):\n    result = []\n    for index in range(len(numbers)):\n        if numbers[index] % 2 == 0:\n            result.append(numbers[index])\n    return result"""
    ]

    dataset = []
    for idx, sample in enumerate(sample_codes):
        pairs = obfuscator.generate_benchmark_pair(sample)
        dataset.append({
            "sample_id": idx + 1,
            "variants": pairs
        })

    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "plagiarism_benchmarks.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    return file_path

if __name__ == "__main__":
    path = build_plagiarism_dataset()
    print(f"Benchmark dataset successfully generated at: {path}")