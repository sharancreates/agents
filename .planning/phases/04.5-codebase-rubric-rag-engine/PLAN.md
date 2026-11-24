# Phase 4.5 Plan: Codebase & Rubric RAG Engine (Vector DB)

## Goal
Implement an AST-aware codebase semantic indexing engine, sponsor track / rubric compliance auditor, and interactive **Judge Copilot Chat API** (`POST /v1/evaluations/{id}/chat`) using 384-dimensional dense vectors, dual PostgreSQL (`pgvector`) & SQLite compatibility, and exact line-numbered evidence citations.

---

## 1. Architecture & Vector Pipeline

```
Target Repository
      │
      ▼
AST Code Chunker (agents/rag/chunker.py)
      │  - Python AST visitor (functions, classes, route decorators)
      │  - Polyglot structural chunker (JS, TS, YAML)
      │  - Exact line tracking: file_path, start_line, end_line
      ▼
Dense Vector Embedder (agents/rag/embedder.py)
      │  - 384-dimensional unit vector (L2 normalized)
      │  - Fast deterministic fallback for offline / CI test environments
      ▼
Vector Storage & Retrieval (agents/rag/vector_store.py)
      │  - Models: CodeEmbedding, RubricRequirement in api/models.py
      │  - Hybrid: pgvector <=> on Postgres, dot-product on SQLite
      ▼
Consumer Systems
      ├── Council Search Tool (agents/rag/tools.py) -> used by QualityAgent / QAAgent
      ├── Sponsor Bounty Auditor (agents/rag/compliance.py) -> verifies required SDKs/APIs
      └── Judge Copilot REST API (api/rag_endpoints.py) -> POST /v1/evaluations/{id}/chat
```

---

## 2. Task Breakdown

### Task 1: [TRACER SLICE] Relational Models & Vector Storage Abstraction
- **Files**:
  - `api/models.py`:
    - `CodeEmbedding`: `id`, `submission_id` (index), `file_path` (index), `symbol_name`, `symbol_type` (`function`, `class`, `route`, `block`), `start_line`, `end_line`, `content` (Text), `embedding_json` (JSON / Vector), `created_at`.
    - `RubricRequirement`: `id`, `organization_id` (nullable), `track_name`, `requirement_text`, `mandatory_keywords` (JSON), `min_similarity_threshold` (Float, default 0.60).
  - `agents/rag/vector_store.py`:
    - `VectorStore`:
      - `store_embeddings(db, submission_id, chunks)`
      - `similarity_search(db, submission_id, query_vector, top_k=5, min_score=0.0)`
      - Computes cosine similarity via dot product on normalized 384-d vectors.
      - Handles SQLite JSON deserialization and Postgres native vector execution transparently.

### Task 2: AST Code Chunker & Embedding Engine
- **Files**:
  - `agents/rag/chunker.py`:
    - `ASTCodeChunker`:
      - Parses Python code into syntactic blocks: `ast.FunctionDef`, `ast.AsyncFunctionDef`, `ast.ClassDef`.
      - Extracts route decorators (e.g. `@app.get`, `@router.post`).
      - Records exact `start_line` and `end_line`.
      - `chunk_directory(repo_path)`: Scans repo while ignoring `.venv`, `node_modules`, `.git`, `__pycache__`.
      - Fallback regex chunker for JavaScript, TypeScript, Go, YAML.
  - `agents/rag/embedder.py`:
    - `DenseEmbedder`:
      - Method `embed_text(text: str) -> List[float]`: Returns 384-dimensional $L_2$-normalized vector.
      - Uses `sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")` when installed.
      - Deterministic hash-based feature vector fallback for offline and unit test environments with zero latency and zero dependency hurdles.

### Task 3: Codebase Indexer & Council Semantic Search Tool
- **Files**:
  - `agents/rag/indexer.py`:
    - `CodebaseIndexer`: Coordinates scanning, chunking, embedding, and storage in batch.
    - Exposes `index_submission(db, submission_id, repo_path) -> int` (returns chunk count).
  - `agents/rag/tools.py`:
    - `search_codebase(db, submission_id, query, top_k=5) -> List[Dict[str, Any]]`: Formats returned chunks with authoritative `file_path:start_line-end_line` citations.
  - Integration:
    - Update `agents/council/quality_agent.py` to optionally query the vector store for security/architectural hotspots.

### Task 4: Sponsor Bounty Compliance Auditor & Judge Copilot API
- **Files**:
  - `agents/rag/compliance.py`:
    - `SponsorComplianceAuditor`:
      - `audit_sponsor_track(db, submission_id, track_name, requirement_query) -> Dict[str, Any]`:
        Evaluates similarity against indexed embeddings, confirms compliance boolean, calculates confidence score, and attaches evidence snippets.
  - `api/rag_endpoints.py`:
    - `POST /v1/evaluations/{id}/index`: Triggers codebase indexing on-demand or background.
    - `POST /v1/evaluations/{id}/chat`: Conversational Q&A endpoint ("Chat with Submission / Ask AutoJudge") accepting `{ "question": "..." }`, retrieving top chunks, and returning grounded answers with line citations.
    - `GET /v1/evaluations/{id}/compliance`: Audits and returns sponsor track checklist.
  - `api/main.py`:
    - Mount `rag_router`.

### Task 5: Automated Verification Suite & Full Regression
- **Files**:
  - `person_2/tests/test_rag_engine.py`:
    - Test 1: AST chunker accurately captures function/class boundaries and line numbers.
    - Test 2: Dense embedder produces unit-length 384-d vectors with high self-similarity.
    - Test 3: Vector store persistence and top-k cosine similarity retrieval.
    - Test 4: Codebase indexer properly indexes a multi-file project and prunes noise.
    - Test 5: Sponsor compliance auditor accurately verifies presence vs absence of required tech.
    - Test 6: Judge Copilot endpoint `POST /v1/evaluations/{id}/chat` returns grounded answers with exact line citations.
  - Full Regression: Execute all 49 existing tests alongside the new RAG tests ensuring 100% pass rate.

---

## 3. Risk Mitigation & Technical Invariants
- **No network/download dependencies in tests**: Embedder test fallback ensures tests run offline in < 2 seconds.
- **Cross-database independence**: Seamless operation on SQLite in-memory and PostgreSQL `pgvector`.
- **Zero hallucinated code locations**: Every retrieved chunk and copilot response includes verifiable `file_path:start_line-end_line`.
