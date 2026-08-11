"""
Performance & Latency Benchmarking Module.
Profiles individual pipeline stages (AST parsing, Unicode normalization,
boilerplate filtering, payload assembly) and reports latency distributions.
"""

import time
import tracemalloc
import os
from comment_neutralizer import CommentNeutralizer
from boilerplate_filter import BoilerplateFilter
from resilience_handler import ResilienceHandler

class LatencyProfiler:
    def __init__(self):
        self.neutralizer = CommentNeutralizer()
        self.boilerplate_filter = BoilerplateFilter()
        self.resilience_handler = ResilienceHandler()

    def profile_file_processing(self, file_path: str, code_content: str) -> dict:
        """Profiles the execution latency and memory overhead for a single file payload."""
        metrics = {}
        
        # Start memory tracking
        tracemalloc.start()
        start_total = time.perf_counter()

        # Stage 1: Unicode Normalization & Comment Neutralization
        t0 = time.perf_counter()
        clean_code = self.neutralizer.neutralize_text(code_content)
        t1 = time.perf_counter()
        metrics["unicode_neutralization_ms"] = round((t1 - t0) * 1000, 3)

        # Stage 2: Boilerplate & Framework Filtering
        t0 = time.perf_counter()
        is_boilerplate = self.boilerplate_filter.is_boilerplate_file(file_path, clean_code)
        t1 = time.perf_counter()
        metrics["boilerplate_filter_ms"] = round((t1 - t0) * 1000, 3)
        metrics["is_boilerplate"] = is_boilerplate

        # Stage 3: Safe Parsing & AST Extraction
        t0 = time.perf_counter()
        parsed_ast = self.resilience_handler.safe_parse_code(clean_code)
        t1 = time.perf_counter()
        metrics["ast_parsing_ms"] = round((t1 - t0) * 1000, 3)

        # Total Overhead
        end_total = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        metrics["total_latency_ms"] = round((end_total - start_total) * 1000, 3)
        metrics["peak_memory_kb"] = round(peak / 1024, 2)

        return metrics

if __name__ == "__main__":
    sample_code = """
def process_data_pipeline(data_batch):
    # Non-ASCII Hindi comment: डेटा प्रोसेसिंग लूप
    processed_results = []
    for item in data_batch:
        if item > 0:
            processed_results.append(item * 2)
    return processed_results
"""
    profiler = LatencyProfiler()
    results = profiler.profile_file_processing("sample_module.py", sample_code)
    print("Performance Profile Results:")
    for k, v in results.items():
        print(f"  {k}: {v}")