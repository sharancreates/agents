# Technical Blueprint: Nearest-Neighbor Vector Lookups

This blueprint covers the mathematical operations, index search speed trade-offs, and result sorting strategies implemented for vector queries in the Originality Agent.

---

## 1. Vector Distance Mathematical Operations

The `pgvector` extension supports three primary operators to compute proximity between vector embeddings:

### 1. Cosine Distance (`<=>`)
*   **Formula**: $1.0 - \frac{A \cdot B}{\|A\| \|B\|}$
*   **Value Range**: $[0.0, 2.0]$
*   **Usage**: Cosine similarity is computed as $1.0 - \text{Cosine Distance}$. This measures the angle direction between two code fragments regardless of length or scale, making it the most robust metric for semantic similarity.

### 2. Negative Inner Product (`<#>`)
*   **Formula**: $-(A \cdot B)$
*   **Usage**: If vectors are L2-normalized to unit length ($\|A\| = \|B\| = 1$), the inner product is mathematically equivalent to cosine similarity. `pgvector` negates the inner product because PostgreSQL indexes expect sorting in ascending order (where smaller distances represent closer matches). This is the fastest metric to execute when unit-normalization is guaranteed.

### 3. L2 / Euclidean Distance (`<->`)
*   **Formula**: $\sqrt{\sum (A_i - B_i)^2}$
*   **Usage**: Measures the straight-line distance between two points in dimensional space. It is sensitive to differences in scale/magnitude. For normalized embeddings, L2 distance is directly correlated with Cosine distance but is less intuitive to map directly to plagiarism percentage classifications.

---

## 2. HNSW Indexing Search Speed Trade-offs

The Hierarchical Navigable Small World (HNSW) index builds a multi-layer graph of vectors to enable fast Approximate Nearest Neighbor (ANN) search:

*   **Speed vs. Recall Trade-off**:
    *   **HNSW Search (ANN)**: Completes in sub-millisecond ranges even with millions of records ($O(\log N)$ complexity). However, it is *approximate*, meaning it has a slight probability of missing the absolute closest vector (recall is typically $95\% - 99\%$).
    *   **Flat Search (Exact)**: Guarantees finding the exact nearest neighbors by scanning every row ($O(N)$ complexity), but search times scale linearly, which becomes a bottleneck on large datasets.
*   **HNSW Construction Parameters**:
    *   `m` (default: 16): Maximum number of connections per node. Higher values improve accuracy for high-dimensional vectors but increase index size and build time.
    *   `ef_construction` (default: 64): Search size used during index creation. Higher values improve recall accuracy at the cost of slower build times.
    *   `ef_search` (session setting): Size of the dynamic candidate list checked during queries. Tuning `SET pgvector.hnsw_ef_search = 100` dynamically increases query recall at a slight query time cost.

---

## 3. Result Filtering & Sorting Architecture

To deliver precise code originality results without overhead:

1.  **Direct Index Utilization**: The query forces a direct index scan by ordering directly on the column and operator (`ORDER BY embedding <=> %s LIMIT %s`).
2.  **Metadata Exclusion**: Parameterized array checks (`AND file_path != ALL(%s)`) exclude the target file during search, preventing a searched function from matching against itself if it is already indexed in the database.
3.  **Threshold Pruning**: Adding a lower boundary check (`AND similarity_score >= %s`) prevents the API from processing and returning weak matches, saving network serialization overhead.
4.  **RealDictCursor Mapping**: Database rows are instantly parsed into dictionaries to provide metadata comparisons alongside raw cosine distances and similarity percentages.

---

## 4. Implementation Location
*   Vector Query Manager: [db_client.py](file:///c:/Users/MANAV/Desktop/Adani%20Uni/Projects/Aiagents/agents/originality/db_client.py)
