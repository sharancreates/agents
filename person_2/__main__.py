import os
import sys
import argparse
from person_2.core.aggregator import MetricsAggregator
from person_2.core.config import ConfigEngine

def main():
    parser = argparse.ArgumentParser(
        description="Code Quality Agent CLI - Scan codebases for complexity and smells instantly."
    )
    parser.add_argument(
        "path", 
        type=str, 
        nargs="?", 
        default=".", 
        help="Target directory path to evaluate (defaults to current directory)."
    )
    
    args = parser.parse_args()
    target_path = os.path.abspath(args.path)

    if not os.path.exists(target_path) or not os.path.isdir(target_path):
        print(f"❌ Error: Target path '{target_path}' does not exist or is not a valid directory.")
        sys.exit(1)

    print("\n" + "="*60)
    print(f"🚀 Code Quality Agent Execution Loop")
    print(f"Target Scope: {target_path}")
    print("="*60)

    # Load configuration exclusions
    config = ConfigEngine.load_config(target_path)
    print(f"⚙️ Loaded Exclusions: {', '.join(config['exclude'])}")
    print("⏳ Scanning files and compiling metrics...")

    try:
        report = MetricsAggregator.evaluate_directory(target_path)
        summary = report.get("summary", {})
        metrics = report.get("metrics", {})

        print("\n📊 ANALYSIS SUMMARY:")
        print(f" • Total Evaluated Files   : {summary.get('total_files_evaluated', 0)}")
        print(f" • Global Maintainability  : {summary.get('overall_maintainability_rating', 'N/A')}")
        print(f" • Total Code Smells Found : {summary.get('global_issue_count', 0)}")
        print(f" • Average Complexity      : {metrics.get('average_cyclomatic_complexity', 1.0)}")
        print(f" • Max Observed Complexity : {metrics.get('max_complexity_observed', 1)}")
        print("="*60 + "\n✅ Scan completed successfully.\n")

    except Exception as e:
        print(f"❌ Critical Failure during analysis execution: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()