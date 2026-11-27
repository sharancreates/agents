# Phase 4.5: Research - Codebase & Rubric RAG Engine (Vector DB)

## 1. Problem Statement & Motivation
Evaluating modern hackathon submissions and real-world software repositories presents three major architectural challenges:
1. **Context Window Exhaustion**: Enterprise and hackathon repositories often contain hundreds of files and tens of thousands of lines of code. Passing full codebases into LLM contexts is cost-prohibitive, triggers high latency, and leads to the "needle-in-a-haystack" attention decay problem.
2. **Sponsor Track Verification**: Hackathons frequently offer \$10k-\$50k sponsor bounties requiring specific technology stacks (e.g. "Best use of Gemini API", "Best use of Razorpay", "Best use of Redis"). Deterministic string matching fails when developers alias imports or wrap client libraries. Semantic vector search reliably detects true architectural adoption.
3. **Judge Copilot Interactivity**: Hackathon judges need quick, authoritative answers to specific evaluation questions (e.g. *"Where is authentication validated?"*, *"How does the system handle websocket reconnects?"*) without manually cloning and searching through every repository.

---

## 2. Vector Mathematics & Embedding Model Selection

### 2.1 Embedding Dimensions & Model
- **Model Family**: `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Dimension**: 384 dimensions.
- **Latency / Memory**: ~15ms inference per chunk on CPU, ~80MB memory footprint. Sub-second indexing for average hackathon repos.

### 2.2 Cosine Similarity Formula
Cosine similarity measures the angular distance between a query vector $\mathbf{q}$ and a code chunk vector $\mathbf{c}$:

$$\text{Sim}(\mathbf{q}, \mathbf{c}) = \frac{\mathbf{q} \cdot \mathbf{c}}{\|\mathbf{q}\|_2 \|\mathbf{c}\|_2}$$

When embedding vectors are normalized to unit length ($\|\mathbf{u}\|_2 = 1.0$), cosine similarity reduces to the dot product:

$$\text{Sim}(\mathbf{q}, \mathbf{c}) = \sum_{i=1}^{384} q_i \cdot c_i$$

---

## 3. Database Architecture & Storage Engine

```
       PostgreSQL (Production)                 SQLite In-Memory (Test/CI)
      ┌───────────────────────┐               ┌────────────────────────┐
      │   code_embeddings     │               │    code_embeddings     │
      │ ───────────────────── │               │ ────────────────────── │
      │ id: Integer           │               │ id: Integer            │
      │ submission_id: String │               │ submission_id: String  │
      │ file_path: String     │               │ file_path: String      │
      │ symbol_name: String   │               │ symbol_name: String    │
      │ symbol_type: String   │               │ symbol_type: String    │
      │ start_line: Integer   │               │ start_line: Integer    │
      │ end_line: Integer     │               │ end_line: Integer      │
      │ content: Text         │               │ content: Text          │
      │ embedding: Vector(384)│               │ embedding_json: JSON   │
      └───────────────────────┘               └────────────────────────┘
                 │                                        │
                 ▼                                        ▼
      pgvector <=> Cosine Index                Pure-Python Dot Product Search
```

### Hybrid Strategy:
To maintain 100% test independence and rapid execution without requiring a live PostgreSQL container for every unit test run:
1. `VectorStore` inspects `db.bind.dialect.name`.
2. On `postgresql` with `pgvector`: executes native vector similarity queries using the `<=>` distance operator.
3. On `sqlite` or fallback: deserializes vectors from `JSON` and computes dot products in Python, returning identical ranked results.

---

## 4. AST-Aware Code Chunking Strategy

Traditional text chunking (fixed token windows) arbitrarily splits functions in half, destroys class definitions, and loses syntactic context. AutoJudge uses **AST-Aware Structural Chunking**:

### Python (`ast` standard library)
- **Functions & Methods** (`ast.FunctionDef`, `ast.AsyncFunctionDef`):
  - Extracts full signature, decorators (e.g. `@app.post("/v1/evaluations")`), docstring, and body.
  - Captures exact `lineno` and `end_lineno`.
- **Classes** (`ast.ClassDef`):
  - Captures class signature, base classes, docstring, and member declarations.
- **Route Handlers**:
  - Tags API endpoints with `symbol_type="route"` for fast endpoint lookup.

### Polyglot / Web Frameworks (JavaScript, TypeScript, Go, YAML)
- Structural regex / indentation block chunking identifying function declarations, export statements, class declarations, and configuration stanzas with start and end lines.

### Directory Pruning
Ignores non-source artifacts to prevent index bloating:
`node_modules`, `.venv`, `venv`, `__pycache__`, `.git`, `.next`, `dist`, `build`, `.pytest_cache`.

---

## 5. Sponsor Bounty Compliance Heuristics
Sponsor tracks specify required technologies. For example:
- **Track**: *"Gemini Live API Integration"*
  - Query: *"Gemini Live API WebSocket client multimodal bidirectional streaming"*
  - High similarity chunk ($> 0.70$) in code confirms genuine adoption.
  - Low similarity ($< 0.40$) indicates missing or nominal mention only.

The compliance auditor returns:
```json
{
  "sponsor_track": "Gemini API",
  "requirement": "Utilize Gemini model for generation or reasoning",
  "is_compliant": true,
  "confidence_score": 0.88,
  "evidence": [
    {
      "file_path": "services/gemini.py",
      "lines": "12-45",
      "symbol": "generate_response",
      "snippet": "from google.genai import Client..."
    }
  ]
}
```

---

## 6. Judge Copilot API Design
`POST /v1/evaluations/{id}/chat`
- **Input**: `{ "question": "Does this team validate API keys before running Docker sandboxes?" }`
- **Workflow**:
  1. Embeds question.
  2. Queries top 3 code chunks via `VectorStore`.
  3. Synthesizes an authoritative answer referencing the retrieved snippets.
  4. Returns `{ "answer": "...", "citations": [ { "file": "api/auth.py", "lines": "45-60", "symbol": "verify_api_key" } ] }`.
