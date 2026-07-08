import os
import ast
import re
import logging
from typing import List, Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("OriginalitySearchAPI")

# Check for FastAPI and Uvicorn dependencies at startup
try:
    from fastapi import FastAPI, HTTPException, Query, status
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError as e:
    error_msg = (
        "Required libraries (fastapi, uvicorn, pydantic) are not installed in the current environment.\n"
        "To resolve this, please install them using: pip install fastapi uvicorn pydantic"
    )
    logger.error(error_msg)
    # Raise a clean ImportError rather than failing later with NameError
    raise ImportError(error_msg) from e

# Safe imports for db_client and pipeline modules
try:
    from originality.db_client import DatabaseManager
    from originality.pipeline import EmbeddingClient
except ImportError:
    try:
        from db_client import DatabaseManager
        from pipeline import EmbeddingClient
    except ImportError as e:
        logger.error("Failed to import DatabaseManager or EmbeddingClient. Check module paths.")
        raise e

# Helper to clean arbitrary raw code snippets submitted to the API
def clean_raw_code(raw_source: str) -> str:
    """
    Cleans raw code snippet by removing docstrings, comments, and extra whitespaces.
    This replicates the Day 2 AST cleaning parser for input snippets.
    """
    if not raw_source:
        return ""
    
    cleaned = raw_source
    try:
        # Parse snippet to AST to identify and strip docstrings
        tree = ast.parse(raw_source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring:
                    # Strip block docstrings
                    cleaned = cleaned.replace(f'"""{docstring}"""', '')
                    cleaned = cleaned.replace(f"'''{docstring}'''", '')
    except Exception:
        # Fallback to regex cleaning if AST parsing fails on partial/malformed snippets
        pass

    # Regex to remove single line comments (# ...)
    cleaned = re.sub(re.compile(r"#.*?\n"), "\n", cleaned)
    
    # Minimize extra whitespace lines
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned).strip()
    return cleaned

# FastAPI Application Definition
app = FastAPI(
    title="Originality Detection Search API",
    description="Vector similarity search and plagiarism analysis service using pgvector.",
    version="1.0.0"
)

# Enable CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class SearchRequest(BaseModel):
    code_snippet: str = Field(..., description="The raw code snippet to search for similarity.")
    limit: Optional[int] = Field(5, ge=1, le=50, description="Max number of matching functions to return.")
    model: Optional[str] = Field("all-MiniLM-L6-v2", description="Embedding model layout to use.")

# Response schema
class MatchDetail(BaseModel):
    id: int
    file_path: str
    function_name: str
    signature: Optional[str]
    cleaned_source: str
    similarity_score: float
    classification: str

class SearchResponse(BaseModel):
    query_cleaned: str
    matches: List[MatchDetail]
    max_similarity: float
    overall_classification: str

# Cache of embedding clients to avoid reloading model on every request
embedding_clients = {}

def get_embedder(model_name: str) -> EmbeddingClient:
    if model_name not in embedding_clients:
        embedding_clients[model_name] = EmbeddingClient(model_name=model_name)
    return embedding_clients[model_name]

# Helper to classify threshold
def classify_similarity(score: float) -> str:
    """
    Plagiarism classification logic based on cosine similarity score:
    - >= 0.95: Exact Match (highly likely direct copy-paste)
    - 0.85 to 0.95: Suspicious/Refactored (likely copy-paste with renaming/refactoring)
    - < 0.85: Original (independently developed code)
    """
    if score >= 0.95:
        return "Exact Match"
    elif score >= 0.85:
        return "Suspicious/Refactored"
    else:
        return "Original"

@app.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
def search_similar_code(request: SearchRequest):
    """
    Accepts raw code, cleans it, generates the vector embedding, 
    queries the pgvector index, and outputs similarity analysis.
    """
    if not request.code_snippet.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code snippet cannot be empty."
        )

    try:
        # 1. Clean the snippet to remove obfuscations
        cleaned_code = clean_raw_code(request.code_snippet)
        
        # 2. Get the embedding client
        embedder = get_embedder(request.model)
        
        # 3. Vectorize the cleaned code snippet
        query_vector = embedder.get_embedding(cleaned_code)
        
        # 4. Search PostgreSQL database using cosine distance (<=>)
        # Cosine similarity is computed as 1 - cosine distance
        db_matches = DatabaseManager.query_similar_functions(
            query_embedding=query_vector,
            limit=request.limit,
            metric="cosine"
        )
        
        # 5. Format results and classify
        formatted_matches = []
        max_score = 0.0
        
        for item in db_matches:
            # PostgreSQL query returns score as similarity_score
            score = float(item["similarity_score"])
            
            # Bound score to [0.0, 1.0] range to handle float precision issues
            score = max(0.0, min(1.0, score))
            
            classification = classify_similarity(score)
            
            if score > max_score:
                max_score = score
                
            formatted_matches.append(MatchDetail(
                id=item["id"],
                file_path=item["file_path"],
                function_name=item["function_name"],
                signature=item.get("signature"),
                cleaned_source=item["cleaned_source"],
                similarity_score=score,
                classification=classification
            ))
            
        # Determine overall status classification
        overall_status = classify_similarity(max_score) if formatted_matches else "Original"
        
        return SearchResponse(
            query_cleaned=cleaned_code,
            matches=formatted_matches,
            max_similarity=max_score,
            overall_classification=overall_status
        )
        
    except Exception as e:
        logger.error(f"Search API request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during search processing: {str(e)}"
        )

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """
    Verifies that the API service is healthy and database pool connectivity exists.
    """
    db_status = "unhealthy"
    try:
        # Quick database connection probe
        with DatabaseManager.get_cursor() as cursor:
            cursor.execute("SELECT 1;")
            db_status = "healthy"
    except Exception as e:
        logger.warning(f"Health check failed to query database: {e}")
        
    return {
        "status": "healthy",
        "database": db_status
    }

if __name__ == "__main__":
    uvicorn.run("search_api:app", host="127.0.0.1", port=8000, reload=True)
