import os
import sys
import shutil
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[STRESS-TEST] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ResilienceTester")

# Ensure parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from originality.resilience_handler import ResilienceHandler
except ImportError:
    try:
        from resilience_handler import ResilienceHandler
    except ImportError as e:
        logger.error("Failed to import ResilienceHandler.")
        raise e

TEMP_TEST_DIR = Path("temp_stress_workspace")

def setup_stress_workspace():
    if TEMP_TEST_DIR.exists():
        shutil.rmtree(TEMP_TEST_DIR)
    TEMP_TEST_DIR.mkdir()

    # 1. Empty File
    with open(TEMP_TEST_DIR / "empty.py", "w", encoding="utf-8") as f:
        f.write("")

    # 2. Binary File (Contains Null Bytes)
    with open(TEMP_TEST_DIR / "binary.bin", "wb") as f:
        f.write(b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00")

    # 3. Giant File (Exceeds size limits, ~6MB)
    with open(TEMP_TEST_DIR / "giant.py", "w", encoding="utf-8") as f:
        # Generate 6MB of junk lines
        for i in range(150000):
            f.write(f"# This is line {i} of junk comment code that swells size.\n")

    # 4. Broken Syntax File
    with open(TEMP_TEST_DIR / "broken_syntax.py", "w", encoding="utf-8") as f:
        f.write("""
def calculate_sum(a, b):
    # Unmatched parenthesis syntax error
    val = (a + b
    return val
""")

    # 5. Deeply Nested Structures (Recursion risk)
    with open(TEMP_TEST_DIR / "deeply_nested.py", "w", encoding="utf-8") as f:
        # Generate 200 levels of nested operations
        f.write("def nested_function():\n")
        indent = "    "
        for i in range(150):
            f.write(f"{indent}if True:\n")
            indent += "    "
        f.write(f"{indent}return 42\n")

def run_stress_test_suite():
    setup_stress_workspace()
    
    logger.info("Starting extreme input and code error resilience testing...")
    
    test_cases = [
        {"name": "Empty File", "path": TEMP_TEST_DIR / "empty.py", "expect_fail": False, "check_ast": True},
        {"name": "Binary File", "path": TEMP_TEST_DIR / "binary.bin", "expect_fail": True, "check_ast": False},
        {"name": "Giant File", "path": TEMP_TEST_DIR / "giant.py", "expect_fail": True, "check_ast": False},
        {"name": "Broken Syntax File", "path": TEMP_TEST_DIR / "broken_syntax.py", "expect_fail": False, "check_ast": True},
        {"name": "Deeply Nested File", "path": TEMP_TEST_DIR / "deeply_nested.py", "expect_fail": False, "check_ast": True}
    ]
    
    passed_cases = 0
    
    for tc in test_cases:
        logger.info(f"\n--- Running Test: {tc['name']} ---")
        filepath = str(tc["path"])
        
        # 1. Read Test
        source = None
        try:
            source = ResilienceHandler.safe_read_file(filepath)
            logger.info(f"[{tc['name']}] Read succeeded.")
            read_status = "SUCCESS"
        except Exception as e:
            logger.info(f"[{tc['name']}] Read failed as expected or handled: {e}")
            read_status = "EXCEPTION_HANDLED"
            
        # Verify read outcome expectation
        if tc["expect_fail"] and read_status == "EXCEPTION_HANDLED":
            logger.info(f"[{tc['name']}] Read Guard: PASS")
        elif not tc["expect_fail"] and read_status == "SUCCESS":
            logger.info(f"[{tc['name']}] Read Guard: PASS")
        else:
            logger.error(f"[{tc['name']}] Read Guard: FAIL")
            continue
            
        # 2. Parse Test
        if tc["check_ast"] and source is not None:
            # Try normal AST parse
            tree = ResilienceHandler.safe_parse_ast(source)
            if tree is None:
                logger.info(f"[{tc['name']}] AST parser failed or skipped (Syntax/Recursion). Triggering Regex fallback...")
                # Run Regex fallback
                functions = ResilienceHandler.regex_fallback_parse(source)
                logger.info(f"[{tc['name']}] Regex Fallback parsed {len(functions)} functions.")
                if tc["name"] == "Broken Syntax File" and len(functions) > 0:
                    logger.info(f"[{tc['name']}] Successfully recovered '{functions[0]['function_name']}' from broken code.")
            else:
                logger.info(f"[{tc['name']}] AST parser succeeded.")
                
        passed_cases += 1
        
    # Cleanup stress folder
    shutil.rmtree(TEMP_TEST_DIR)
    
    logger.info("\n" + "="*50)
    logger.info(f"STRESS TEST SUMMARY: {passed_cases}/{len(test_cases)} CASES PASSED")
    logger.info("="*50)
    
    if passed_cases == len(test_cases):
        logger.info("Resilience verification succeeded. Continuous zero-halt run confirmed.")
        sys.exit(0)
    else:
        logger.error("Resilience verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_stress_test_suite()
