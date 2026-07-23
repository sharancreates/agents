"""
Automated Latency & Throughput Benchmark Test Runner.
Verifies that key pipeline functions execute within defined target latency SLAs.
"""

from benchmark_performance import LatencyProfiler

def run_performance_benchmark_tests():
    print("=" * 60)
    print("RUNNING DAY 20: PERFORMANCE & LATENCY BENCHMARK SUITE")
    print("=" * 60)

    profiler = LatencyProfiler()

    # Synthetic test payload with mixed complexity
    test_files = [
        ("app/main.py", "def root():\n    return {'status': 'ok'}"),
        ("app/services/analytics.py", "\n".join([f"def func_{i}():\n    return {i} * 10" for i in range(50)])),
        ("app/utils/helpers.py", "# Unicode comment: सहायता फ़ंक्शन\ndef help_me():\n    pass")
    ]

    total_latency = 0
    file_count = len(test_files)
    MAX_LATENCY_PER_FILE_MS = 50.0  # 50ms SLA boundary

    for file_path, content in test_files:
        profile = profiler.profile_file_processing(file_path, content)
        latency = profile["total_latency_ms"]
        memory = profile["peak_memory_kb"]
        total_latency += latency

        print(f"File: {file_path:<30} | Latency: {latency:>6.2f} ms | Peak Mem: {memory:>6.2f} KB")
        assert latency < MAX_LATENCY_PER_FILE_MS, f"Latency SLA violated for {file_path}: {latency}ms > {MAX_LATENCY_PER_FILE_MS}ms"

    avg_latency = round(total_latency / file_count, 2)
    print("-" * 60)
    print(f"Benchmark Summary: Average Latency = {avg_latency} ms across {file_count} files.")
    print("=" * 60)
    print("ALL PERFORMANCE BENCHMARK SLAs PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_performance_benchmark_tests()