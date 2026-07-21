import os
import ast
import sys
import shutil
import time
import logging
import tracemalloc
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[SIMULATION] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("FullIntegrationSimulation")

# Ensure parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from originality.comment_neutralizer import CommentNeutralizer
    from originality.boilerplate_filter import BoilerplateFilter
    from originality.resilience_handler import ResilienceHandler
    from originality.architecture_evaluator import ArchitectureEvaluator
    from originality.schemas import ArchitectureEvaluationSchema, has_pydantic
except ImportError:
    try:
        from comment_neutralizer import CommentNeutralizer
        from boilerplate_filter import BoilerplateFilter
        from resilience_handler import ResilienceHandler
        from architecture_evaluator import ArchitectureEvaluator
        from schemas import ArchitectureEvaluationSchema, has_pydantic
    except ImportError as e:
        logger.error("Failed to import integration modules.")
        raise e

SIM_DIR = Path("simulated_hackathon_payloads")

def build_simulation_payloads():
    """
    Creates multiple mock project submissions containing variations:
    - Valid clean code.
    - Large framework boilerplate files.
    - Non-English comments and docstrings.
    - Binary files and syntax errors.
    """
    if SIM_DIR.exists():
        shutil.rmtree(SIM_DIR)
    SIM_DIR.mkdir()

    # Submission 1: Clean/Valid project
    sub1 = SIM_DIR / "sub1_clean"
    sub1.mkdir()
    with open(sub1 / "README.md", "w", encoding="utf-8") as f:
        f.write("# Clean Project\nSimple mock calculator application.")
    with open(sub1 / "requirements.txt", "w", encoding="utf-8") as f:
        f.write("requests==2.28.1\n")
    with open(sub1 / "main.py", "w", encoding="utf-8") as f:
        f.write("""
def calculate_salary(hours, wage):
    # Calculates base salary
    return hours * wage

def print_profile(name):
    # Outputs user profile
    print(f"Profile: {name}")
""")

    # Submission 2: Boilerplate project (FastAPI config setup)
    sub2 = SIM_DIR / "sub2_boilerplate"
    sub2.mkdir()
    # settings.py is in the boilerplate list
    with open(sub2 / "settings.py", "w", encoding="utf-8") as f:
        f.write("""
# Default Django settings file
DEBUG = True
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth']
""")
    with open(sub2 / "app.py", "w", encoding="utf-8") as f:
        # High ratio of boilerplate setup statements
        f.write("""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'])
""")

    # Submission 3: Multilingual (Hindi/Gujarati comment noise)
    sub3 = SIM_DIR / "sub3_multilingual"
    sub3.mkdir()
    with open(sub3 / "README.md", "w", encoding="utf-8") as f:
        f.write("# Multilingual Project\nHas non-English comments.")
    with open(sub3 / "logic.py", "w", encoding="utf-8") as f:
        f.write("""
# English comment: core operations
def process_data(data):
    \"\"\"
    ગુજરાતી ભાષામાં આ એક દસ્તાવેજીકરણ છે.
    This docstring is multi-lingual.
    \"\"\"
    # Hindi comment: उपयोगकर्ता प्रोफ़ाइल प्राप्त करें
    val = data * 10
    return val
""")

    # Submission 4: Corrupted/Extreme Payload (binary and syntax errors)
    sub4 = SIM_DIR / "sub4_corrupted"
    sub4.mkdir()
    # Binary file
    with open(sub4 / "image.png", "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")
    # Syntax error file
    with open(sub4 / "broken.py", "w", encoding="utf-8") as f:
        f.write("""
def broken_syntax_function(x):
    # Unclosed bracket
    z = [1, 2, 3
    return z
""")


class SimulatedTaskQueue:
    """
    Simulates Celery worker distribution using a thread pool.
    Tracks state transitions: PENDING -> STARTED -> SUCCESS/FAILURE.
    """
    @classmethod
    def execute_worker(cls, submission_path: Path) -> dict:
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] Worker assigned task for {submission_path.name}")
        
        tracemalloc.start()
        start_time = time.perf_counter()
        
        telemetry = {
            "submission": submission_path.name,
            "worker": thread_name,
            "processed_files": 0,
            "bypassed_files": 0,
            "neutralized_comments": 0,
            "recovered_functions": 0,
            "schema_verified": False,
            "status": "STARTED"
        }
        
        try:
            # 1. Scan files in submission
            for file in submission_path.glob("**/*"):
                if file.is_dir():
                    continue
                    
                # Framework Boilerplate check
                if BoilerplateFilter.is_boilerplate_file(str(file)):
                    telemetry["bypassed_files"] += 1
                    continue
                    
                # Safe Reading (Resilience)
                try:
                    source_code = ResilienceHandler.safe_read_file(str(file))
                except Exception as read_err:
                    logger.warning(f"File bypassed during resilience check ({file.name}): {read_err}")
                    telemetry["bypassed_files"] += 1
                    continue
                    
                telemetry["processed_files"] += 1
                
                # Check comment neutralization
                if CommentNeutralizer.NON_ASCII_PATTERN.search(source_code):
                    source_code = CommentNeutralizer.neutralize_source_code(source_code)
                    telemetry["neutralized_comments"] += 1
                
                # Parsing Check (AST / Regex Fallback)
                ast_tree = ResilienceHandler.safe_parse_ast(source_code)
                if ast_tree is None:
                    # Fallback triggered
                    funcs = ResilienceHandler.regex_fallback_parse(source_code)
                    if funcs:
                        telemetry["recovered_functions"] += len(funcs)
                else:
                    # Count top level functions
                    funcs_count = sum(1 for node in ast_tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
                    telemetry["recovered_functions"] += funcs_count
            
            # 2. Run Architectural Evaluation & Schema Locking
            eval_report = ArchitectureEvaluator.evaluate_repository(str(submission_path))
            
            # Schema Lock Verification
            if has_pydantic:
                try:
                    ArchitectureEvaluationSchema(**eval_report)
                    telemetry["schema_verified"] = True
                except Exception as schema_err:
                    logger.error(f"Schema verification failed for {submission_path.name}: {schema_err}")
            else:
                # Basic manual check
                required = ["detected_patterns", "manifest_mismatches", "scores"]
                telemetry["schema_verified"] = all(k in eval_report for k in required)
                
            telemetry["status"] = "SUCCESS"
            
        except Exception as task_err:
            logger.error(f"Worker task error for {submission_path.name}: {task_err}")
            telemetry["status"] = "FAILURE"
            
        end_time = time.perf_counter()
        mem_current, mem_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        telemetry["latency_ms"] = (end_time - start_time) * 1000.0
        telemetry["peak_mem_kb"] = mem_peak / 1024.0
        
        return telemetry

def run_integration_simulation():
    # Setup Windows UTF-8 stdout if needed
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    build_simulation_payloads()
    
    logger.info("Initializing multi-worker simulation run...")
    
    submissions = [
        SIM_DIR / "sub1_clean",
        SIM_DIR / "sub2_boilerplate",
        SIM_DIR / "sub3_multilingual",
        SIM_DIR / "sub4_corrupted"
    ]
    
    results = []
    
    # Simulate a pool of 3 asynchronous workers
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="CeleryWorker") as executor:
        futures = {executor.submit(SimulatedTaskQueue.execute_worker, sub): sub for sub in submissions}
        for future in as_completed(futures):
            results.append(future.result())
            
    # Cleanup simulation files
    shutil.rmtree(SIM_DIR)
    
    # ----------------------------------------------------
    # Output Simulation Metrics Matrix
    # ----------------------------------------------------
    print("\n" + "="*115)
    print(f"{'SUBMISSION':<20} | {'WORKER':<15} | {'FILES':<8} | {'BYPASS':<8} | {'NEUT':<6} | {'RECOV':<6} | {'SCHEMA':<8} | {'LATENCY':<12} | {'STATUS'}")
    print("="*115)
    
    for r in results:
        schema_status = "VERIFIED" if r["schema_verified"] else "FAILED"
        print(
            f"{r['submission']:<20} | "
            f"{r['worker']:<15} | "
            f"{r['processed_files']:<8} | "
            f"{r['bypassed_files']:<8} | "
            f"{r['neutralized_comments']:<6} | "
            f"{r['recovered_functions']:<6} | "
            f"{schema_status:<8} | "
            f"{r['latency_ms']:.2f} ms | "
            f"{r['status']}"
        )
        
    print("="*115 + "\n")
    logger.info("Hackathon submission batch simulation completed.")

if __name__ == "__main__":
    run_integration_simulation()
