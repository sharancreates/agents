# Technical Blueprint: Search API & Plagiarism Threshold Tuning

This document describes the design and usage of the search web API developed on Day 5 of the engineering sprint. The service exposes code similarity searches to external consumers and provides classification labels based on cosine similarity thresholds.

---

## 1. REST Endpoint Structure

The API is built using **FastAPI** to support high-throughput asynchronous workloads. It includes two primary endpoints:

### POST `/search`
Performs semantic code search against the pgvector database.

*   **Request Headers**: `Content-Type: application/json`
*   **Request Body JSON Schema**:
    ```json
    {
      "code_snippet": "def my_func(): pass",
      "limit": 5,
      "model": "all-MiniLM-L6-v2"
    }
    ```
    *   `code_snippet` *(string, required)*: The raw code snippet to evaluate.
    *   `limit` *(int, optional, default=5)*: Maximum number of closest matches to return.
    *   `model` *(string, optional, default="all-MiniLM-L6-v2")*: The embedding layout mapping (e.g. `all-MiniLM-L6-v2` = 384 dim, `text-embedding-3-small` = 1536 dim).

*   **Response JSON Schema**:
    ```json
    {
      "query_cleaned": "def my_func():\n    pass",
      "matches": [
        {
          "id": 12,
          "file_path": "originality/parser.py",
          "function_name": "clean_function_source",
          "signature": "def clean_function_source(node)",
          "cleaned_source": "def clean_function_source(node):\n    ...",
          "similarity_score": 0.9842,
          "classification": "Exact Match"
        }
      ],
      "max_similarity": 0.9842,
      "overall_classification": "Exact Match"
    }
    ```

### GET `/health`
Returns the status of the API instance and evaluates connection pooling health.

*   **Response JSON Schema**:
    ```json
    {
      "status": "healthy",
      "database": "healthy"
    }
    ```

---

## 2. Plagiarism Threshold Justification

Cosine similarity is computed as $1 - \text{Cosine Distance}$, bounded between $[0.0, 1.0]$. The classification boundaries are configured as follows:

| Cosine Similarity Range | Plagiarism Classification | Technical Justification |
| :--- | :--- | :--- |
| **Score $\ge 0.95$** | **Exact Match** | Structural syntax and token ordering are virtually identical. This indicates direct copy-paste, possibly with trivial alterations like changing comments, spacing, or variable names (which are stripped by our AST cleaner). |
| **$0.85 \le \text{Score} < 0.95$** | **Suspicious / Refactored** | Heavy semantic overlap. Indicates structural plagiarism where control flows remain the same but lines have been shuffled, minor helper wrappers added, or core functions refactored. |
| **Score $< 0.85$** | **Original** | Low-to-moderate semantic similarity. Represents independently written code solving similar tasks or code using different programmatic approaches. |

---

## 3. How to Start the API Server Locally

### Prerequisites
Install dependencies in the virtual environment:
```bash
# Activate virtual environment and install FastAPI + Uvicorn
..\venv\Scripts\pip install fastapi uvicorn
```

### Running the API
Execute the server script directly:
```bash
# Run server from the agents directory
..\venv\Scripts\python originality/search_api.py
```
By default, the server starts on `http://127.0.0.1:8000`. You can access:
- **Interactive Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **Alternative Redoc Documentation**: `http://127.0.0.1:8000/redoc`
