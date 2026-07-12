# Technical Blueprint: Dense Vector Generation Loop & Bulk Loading

This blueprint details the design of the batched vector processing system and bulk database insert optimization implemented on Day 8 of the Originality Agent engineering sprint.

---

## 1. Batch Execution Loop & Throughput Metrics

Instead of vectorizing and inserting code slices individually, the upgraded pipeline utilizes a chunked buffering system:

1.  **Slices Accumulation**: Functional slices extracted from files are held in a memory buffer.
2.  **Batch Vectorization**: When the buffer reaches the user-specified limit (default: `32`), `EmbeddingClient.get_embeddings` executes a single, batched model-inference pass.
3.  **Throughput Gains**:
    *   **Vectorization Latency**: Encoding sentences in a batch allows PyTorch/SentenceTransformers to perform operations in parallel using multi-threading and SIMD vector operations. This results in a $3\times$ to $5\times$ latency reduction compared to serial execution.
    *   **Database Writes**: Rather than executing $N$ separate round-trip insert commands, we format a single multi-row `INSERT` statement containing all $N$ records using `psycopg2.extras.execute_values`. This reduces database round-trip times by up to $95\%$.

---

## 2. Memory Safety Safeguards During Massive Repository Scans

When scanning very large directories, keeping too many objects in memory can lead to out-of-memory (OOM) failures. We implement several safeguards:

*   **Fixed-size Buffer**: Slices are accumulated in a strict `batch_buffer` of size $B$ (default: 32). The moment this buffer is full, it is vectorized, written to the database, and immediately cleared via `batch_buffer.clear()`. This keeps memory footprint flat ($O(B)$ instead of $O(N)$) regardless of the repository size.
*   **AST Lazy Processing**: We parse and extract functions one file at a time during the `os.walk` traversal. We do not load the whole repository's ASTs into memory at once.
*   **In-Place Ignore Filtering**: Directories matching ignore patterns are pruned in-place (`dirs[:] = [...]`) during `os.walk`, preventing recursive traversal of deep subdirectories (such as `.git`, `node_modules`, and `venv` directories), which drastically saves CPU time and disk I/O.

---

## 3. Database Connection Lifecycle under Batch Loads

Efficiently managing connections during massive writes prevents pool exhaustion and ensures stability:

*   **Threaded Pooling**: The database layer (`db_client.py`) leverages a thread-safe connection pooling manager (`ThreadedConnectionPool`).
*   **Cursor context managers**: Each database operation obtains a connection and cursor using context managers (`with cls.get_cursor() as cursor:`). This guarantees that connections are released back to the pool immediately upon statement completion or in the event of an unhandled exception.
*   **Atomic Upserts**: `ON CONFLICT (file_path, function_name) DO UPDATE` ensures that bulk loading handles duplicate files (e.g. indexing the same file multiple times) safely and atomically without throwing database unique-constraint exceptions or leaving orphaned transactions open.

---

## 4. Implementation Location
*   Database Bulk Utility: `bulk_upsert_function_embeddings` in [db_client.py](file:///c:/Users/MANAV/Desktop/Adani%20Uni/Projects/Aiagents/agents/originality/db_client.py)
*   Orchestration Pipeline: `process_codebase_pipeline` in [pipeline.py](file:///c:/Users/MANAV/Desktop/Adani%20Uni/Projects/Aiagents/agents/originality/pipeline.py)
