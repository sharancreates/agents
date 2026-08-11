# Engineering Playbook: Baseline Integration & Phase Sync

This playbook contains instructions for verifying the Phase 1 loop locally and details the integration health checklist to ensure high-performance, deadlock-free execution in production.

---

## 1. Local Verification Tool

We have built a dedicated programmatic testing harness that validates AST cleaning, embedding layout compatibility, and distance classification boundaries:

### File Location:
*   [test_phase1_loop.py](file:///c:/Users/MANAV/Desktop/Adani%20Uni/Projects/Aiagents/agents/originality/test_phase1_loop.py)

### Execution:
To run the verification suite, execute the following command:
```bash
# Run verification suite from the agents folder
..\venv\Scripts\python originality/test_phase1_loop.py
```

---

## 2. Integration Health Checklist

To prepare the codebase for Phase 2, verify that the following system boundaries meet thread-safety and resource management guidelines:

### [ ] 1. AST Parser Thread Safety
*   **Verification**: Ensure `ast.parse` and `ast.walk` do not encounter infinite recursion on recursive circular definitions or massive source files.
*   **Status**: Safe. `ast` operations are CPU-bound and run on isolated local scopes with no shared mutable AST tree states.

### [ ] 2. Embedding Model Thread Safety
*   **Verification**: PyTorch and SentenceTransformer encoders can sometimes experience thread locks during concurrent inference.
*   **Best Practice**: Ensure the `EmbeddingClient` is instantiated as a thread-safe singleton, or safeguard encoder inference using thread-local storage or lock primitives if scaling to high concurrency.

### [ ] 3. Database Pool Exhaustion Prevention
*   **Verification**: Connection starvation occurs if database connections are checked out of the pool but not returned.
*   **Status**: Handled. `DatabaseManager` leverages Python's `contextmanager` structure with `try...finally` blocks. The `ThreadedConnectionPool` checked-out connections are guaranteed to run `.putconn()` even if the SQL execution throws exceptions.

### [ ] 4. FastAPI Event Loop Lockout (Critical)
*   **Verification**: Using `async def` for FastAPI endpoints that execute blocking synchronous calls (such as `psycopg2` or CPU-heavy AST parsing/embeddings) blocks the single-threaded event loop, leading to severe latency spikes.
*   **Status**: Handled. The `/search` endpoint in `search_api.py` is declared using standard synchronous `def` rather than `async def`. FastAPI automatically assigns synchronous endpoints to a background thread pool, preventing event loop blocking.
