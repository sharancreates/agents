import os
import sys
import logging
import json
import ast
import re

# Setup logging to console
logging.basicConfig(
    level=logging.INFO,
    format="[TEST-RUNNER] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Phase1LoopTest")

# Ensure parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Attempt imports of local originality models
try:
    from originality.db_client import DatabaseManager
    from originality.pipeline import EmbeddingClient
except ImportError:
    try:
        from db_client import DatabaseManager
        from pipeline import EmbeddingClient
    except ImportError as e:
        logger.error("Failed to import DatabaseManager or EmbeddingClient.")
        raise e

# Setup search_api import with local fallback to prevent script failure when FastAPI is missing
has_search_api = False
app = None
SearchRequest = None
search_similar_code = None

def clean_raw_code_local(raw_source: str) -> str:
    """Fallback clean code function if search_api cannot be imported."""
    if not raw_source:
        return ""
    cleaned = raw_source
    try:
        tree = ast.parse(raw_source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring:
                    cleaned = cleaned.replace(f'"""{docstring}"""', '').replace(f"'''{docstring}'''", '')
    except Exception:
        pass
    cleaned = re.sub(re.compile(r"#.*?\n"), "\n", cleaned)
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned).strip()
    return cleaned

try:
    from originality.search_api import app, SearchRequest, search_similar_code, clean_raw_code
    has_search_api = True
except ImportError:
    try:
        from search_api import app, SearchRequest, search_similar_code, clean_raw_code
        has_search_api = True
    except ImportError:
        logger.warning(
            "FastAPI dependencies not installed. "
            "Pipeline simulation will run using built-in AST parser and embedding mock fallbacks."
        )
        clean_raw_code = clean_raw_code_local

# Define sample code snippets for testing
EXACT_SOURCE = """
def calculate_factorial(n):
    # Calculate the factorial of a number
    if n == 0:
        return 1
    else:
        return n * calculate_factorial(n - 1)
"""

REFACTORED_SOURCE = """
def calculate_factorial(n):
    # Altered formatting and names but same semantic structure
    val = n
    if val == 0:
        return 1
    return val * calculate_factorial(val - 1)
"""

ORIGINAL_SOURCE = """
def get_user_profile(user_id):
    # Totally unrelated functionality
    query = "SELECT * FROM users WHERE id = %s"
    db = connect_to_database()
    return db.execute(query, (user_id,))
"""

def execute_verification_loop():
    logger.info("Starting Phase 1 End-to-End Loop local verification.")
    
    # 1. Check if we can configure the database
    db_connected = False
    TEST_DIMENSION = 384  # Default for all-MiniLM-L6-v2
    
    logger.info("Step 1: Initializing Database Schema...")
    try:
        DatabaseManager.setup_schema(vector_dim=TEST_DIMENSION)
        db_connected = True
        logger.info("Database schema setup succeeded (or table already existed).")
    except Exception as e:
        logger.warning(
            f"Could not connect to database: {e}.\n"
            "Continuing tests in Dry-Run/Mock mode. Database writes and queries will be skipped."
        )

    # 2. Setup mock data in database if connected
    if db_connected:
        logger.info("Step 2: Indexing mock template function...")
        embedder = EmbeddingClient(model_name="all-MiniLM-L6-v2")
        cleaned_exact = clean_raw_code(EXACT_SOURCE)
        mock_embedding = embedder.get_embedding(cleaned_exact)
        
        try:
            DatabaseManager.upsert_function_embedding(
                file_path="mock_workspace/factorial.py",
                function_name="calculate_factorial",
                signature="def calculate_factorial(n)",
                cleaned_source=cleaned_exact,
                embedding=mock_embedding
            )
            logger.info("Upserted baseline function to database successfully.")
        except Exception as e:
            logger.error(f"Failed to insert mock data: {e}")
            db_connected = False
    else:
        logger.info("Step 2: Skipped database indexing (Database offline).")

    # 3. Expose the test request payloads to search logic
    logger.info("Step 3: Sending query snippets to the Search API...")
    
    # Setup test runner depending on fastapi/testclient availability
    has_test_client = False
    if has_search_api:
        try:
            from fastapi.testclient import TestClient
            client = TestClient(app)
            has_test_client = True
            logger.info("FastAPI TestClient initialized. Testing via HTTP client layer.")
        except ImportError:
            logger.info("FastAPI TestClient not installed. Testing via direct API function calls.")

    test_cases = [
        {"name": "Verbatim Code (Exact Match)", "code": EXACT_SOURCE, "expected": "Exact Match"},
        {"name": "Slightly Obfuscated Code (Suspicious/Refactored)", "code": REFACTORED_SOURCE, "expected": "Suspicious/Refactored"},
        {"name": "Independent logic (Original)", "code": ORIGINAL_SOURCE, "expected": "Original"}
    ]

    for case in test_cases:
        logger.info(f"\n--- Running Test Case: {case['name']} ---")
        
        payload = {
            "code_snippet": case["code"],
            "limit": 3,
            "model": "all-MiniLM-L6-v2"
        }
        
        if db_connected and has_search_api:
            try:
                if has_test_client:
                    # Request via HTTP client mock
                    response = client.post("/search", json=payload)
                    result_data = response.json()
                    status_code = response.status_code
                    assert status_code == 200
                else:
                    # Call function directly
                    req = SearchRequest(
                        code_snippet=payload["code_snippet"],
                        limit=payload["limit"],
                        model=payload["model"]
                    )
                    result_data = search_similar_code(req)
                    if hasattr(result_data, "dict"):
                        result_data = result_data.dict()
                
                # Print result payload
                print(json.dumps(result_data, indent=2))
                logger.info(f"API Result classification: {result_data.get('overall_classification')}")
                logger.info(f"Max Similarity Score: {result_data.get('max_similarity')}")
                
            except Exception as e:
                logger.error(f"Error executing search query payload: {e}")
        else:
            # Replicate behavior locally using mock logic when DB is not running or search_api is missing
            logger.info("Simulating search classifications (Dry-Run Mode):")
            embedder = EmbeddingClient(model_name="all-MiniLM-L6-v2")
            
            # Get mock query vectors
            v_baseline = embedder.get_embedding(clean_raw_code(EXACT_SOURCE))
            v_query = embedder.get_embedding(clean_raw_code(case["code"]))
            
            # Simple cosine similarity helper
            dot_product = sum(x * y for x, y in zip(v_baseline, v_query))
            mag_b = sum(x * x for x in v_baseline) ** 0.5
            mag_q = sum(x * x for x in v_query) ** 0.5
            similarity = dot_product / (mag_b * mag_q) if mag_b * mag_q > 0 else 0.0
            
            # Determine classification
            if similarity >= 0.95:
                classification = "Exact Match"
            elif similarity >= 0.85:
                classification = "Suspicious/Refactored"
            else:
                classification = "Original"
                
            simulated_response = {
                "query_cleaned": clean_raw_code(case["code"]),
                "matches": [
                    {
                        "file_path": "mock_workspace/factorial.py",
                        "function_name": "calculate_factorial",
                        "similarity_score": similarity,
                        "classification": classification
                    }
                ] if similarity >= 0.1 else [],
                "max_similarity": similarity,
                "overall_classification": classification
            }
            print(json.dumps(simulated_response, indent=2))
            logger.info(f"Simulated Result: {classification} (Score: {similarity:.4f})")

    logger.info("\nVerification complete.")

if __name__ == "__main__":
    execute_verification_loop()
