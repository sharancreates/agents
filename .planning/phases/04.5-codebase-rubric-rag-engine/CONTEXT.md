# Phase 4.5: Context & Scope - Codebase & Rubric RAG Engine

## 1. Phase Objective
Equip AutoJudge with an **AST-Aware Codebase & Rubric RAG Engine** that semantically indexes hackathon codebases into 384-dimensional dense vectors, enables council agents to query 500+ file repositories without context-window overflow, audits compliance against sponsor bounty rules (e.g. verifying specific SDKs, APIs, and cloud targets), and provides a conversational **Judge Copilot API** (`POST /v1/evaluations/{id}/chat`) that answers technical questions with exact line-numbered code citations.

---

## 2. Scope Boundaries

### In Scope:
1. **Relational & Vector Data Models (`api/models.py`)**:
   - `CodeEmbedding`: Stores semantic chunks, file path, symbol name, symbol type (`function`, `class`, `route`, `block`), start/end lines, text content, and embedding vector.
   - `RubricRequirement`: Stores sponsor tracks and custom hackathon rubric criteria to evaluate against indexed code.
2. **Vector Storage Abstraction (`agents/rag/vector_store.py`)**:
   - Hybrid support for PostgreSQL with `pgvector` and SQLite/in-memory test databases via normalized JSON arrays.
   - Sub-second cosine similarity search returning top-k matching code snippets.
3. **AST Code Chunker & Embedding Engine (`agents/rag/`)**:
   - `chunker.py`: Python AST parsing extracting classes, functions, async functions, and framework route decorators (`@app.get`, `@router.post`) with exact line numbers. Structural chunking for JS/TS/YAML.
   - `embedder.py`: Produces 384-dimensional normalized dense vectors (`all-MiniLM-L6-v2`) with a fast deterministic offline fallback for CI/tests without downloading 100MB model files.
4. **Codebase Indexer & Council Search Tool (`agents/rag/`)**:
   - `indexer.py`: Scans repositories, filters noisy directories (`.venv`, `node_modules`, `.git`), chunks source files, and indexes embeddings into the database.
   - `tools.py`: `search_codebase(query, submission_id, top_k=5)` providing Council agents with semantic retrieval.
5. **Sponsor Bounty Compliance Auditor (`agents/rag/compliance.py`)**:
   - Evaluates codebases against required sponsor technologies (e.g., "Must use Gemini API", "Must use Redis cache", "Must use Razorpay") and computes confidence scores with code citations.
6. **Headless Judge Copilot Chat Endpoint (`api/rag_endpoints.py`)**:
   - `POST /v1/evaluations/{id}/index`: Triggers vector indexing of submission files.
   - `POST /v1/evaluations/{id}/chat`: Conversational Q&A endpoint ("Ask AutoJudge") returning contextual answers with line-numbered citations.
   - `GET /v1/evaluations/{id}/compliance`: Retrieves sponsor track compliance verification.
7. **Automated Verification Suite (`person_2/tests/test_rag_engine.py`)**:
   - Comprehensive test matrix for chunking, vector storage, retrieval, compliance audits, and conversational copilot endpoints.

### Out of Scope:
- Front-end React chat modal & interactive code viewer (deferred to Phase 5: Enterprise Portal).
- Fine-tuning custom embedding models (standard 384-d MiniLM model meets latency/accuracy targets).

---

## 3. Invariants & Guarantees
1. **Deterministic Offline Fallback**: The RAG engine must operate without crashing or hanging if `sentence-transformers` or external model downloads are unavailable (e.g., in CI or offline test environments).
2. **Dual Database Compatibility**: Must function seamlessly on SQLite in-memory (for tests) and PostgreSQL with `pgvector` (for production).
3. **Exact Line Citations**: Every retrieved code snippet and copilot answer must include authoritative `file_path:start_line-end_line` references for transparency.
