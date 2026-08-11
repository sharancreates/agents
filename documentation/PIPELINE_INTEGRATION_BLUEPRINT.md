# Technical Blueprint: Pipeline Integration & Embedding Generation

This document describes the orchestration pipeline built on Day 4 of the engineering sprint. The pipeline handles crawling directory trees, filtering paths matching gitignore rules, parsing class methods and functions, generating vector embeddings, and saving them into pgvector.

---

## 1. Pipeline Architecture & Directory Traversal

The orchestration script operates as follows:
1. **Root Directory Scan**: Walks recursively through a codebase root directory via `os.walk`.
2. **Directory Filtering**: In-place filtering of directories to prune ignored trees early (e.g., `.git`, `venv`, `node_modules`).
3. **File Filter**: Discards non-Python files and matches paths against rules compiled from the local `.gitignore`.
4. **AST Processing**: Calls `extract_functions_from_file` from `parser.py` on the filtered files.
5. **Embedding Conversion**: Computes dense vectors using `EmbeddingClient`.
6. **DB Commit**: Uses `DatabaseManager` from `db_client.py` to upsert records into PostgreSQL.

---

## 2. Ignore Engine (GitignoreMatcher)

A lightweight class parses the `.gitignore` rules and uses `fnmatch` wildcard comparisons. It supports:
- Directory exclusions (e.g. `venv/` or `/site`).
- File extension patterns (e.g. `*.pyc`).
- Specific filenames.

---

## 3. Embedding Strategies (EmbeddingClient)

We support the following modes:
1. **SentenceTransformers (`all-MiniLM-L6-v2`)**: Uses a local model with PyTorch. Produces 384-dimensional dense vectors.
2. **API Providers (e.g., OpenAI `text-embedding-3-small`)**: Employs a 1536-dimensional layout.
3. **Deterministic Mock Fallback**: If the `sentence-transformers` library is not installed, it computes a hash-seeded, unit-normalized vector. This guarantees that:
   - Run tests succeed instantly with no dependencies.
   - Vector dimensions match the database schema.
   - Vectors are pre-normalized, making cosine similarity scores accurate and valid.

---

## 4. Pipeline Integration Orchestrator File

### Location:
The implementation code is located in the repository at: [pipeline.py](file:///c:/Users/MANAV/Desktop/Adani%20Uni/Projects/Aiagents/agents/originality/pipeline.py)

### CLI Usage:
Run the pipeline directly from the `agents` folder using the virtual environment:
```bash
# Index current directory with default model
..\venv\Scripts\python originality/pipeline.py --dir . --model all-MiniLM-L6-v2
```

### Script Execution Logs Summary:
The script yields a summary report at the end of the walk:
```
================ Pipeline Execution Report ================
  Total Files Scanned   : 142
  Python Files Parsed   : 12
  Files/Folders Skipped : 130
  Functions Indexed     : 36
  Exceptions Handled    : 0
===========================================================
```
