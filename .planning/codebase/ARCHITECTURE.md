# System Architecture & Design Patterns

## 1. High-Level System Architecture
AutoJudge uses an asynchronous distributed architecture designed to process long-running code analysis workloads without blocking client interactions:

```
[React SPA Frontend] (Port 5173)
       │ HTTP / REST
       ▼
[FastAPI Gateway] (Port 8000) ──────► [PostgreSQL + pgvector] (Port 5433)
       │ Enqueue Task
       ▼
 [Redis Broker] (Port 6379)
       │ Dequeue Task
       ▼
[Celery Worker Pipeline]
   ├── Stage 1: Static Code Quality Engine (AST, Cyclomatic, Ruff/ESLint)
   ├── Stage 2: Dynamic Functionality Sandbox (Process execution, RAM profiling)
   ├── Stage 3: Originality Engine (Boilerplate filter, SentenceTransformers, pgvector)
   ├── Stage 4: Innovation & Architecture Engine (Tree structure, Manifests, Claude)
   ├── Stage 5: Synthesis Engine (Weighted composite grading)
   └── Stage 6: Feedback Engine (Participant constructive commentary)
```

## 2. Key Components & Subsystems
- **API Gateway (`api/main.py`)**:
  - Validates submission intake (`POST /api/submissions`)
  - Enqueues evaluation tasks to Celery
  - Exposes synthesis recalculation endpoints (`/api/submissions/{id}/synthesize`, `/api/submissions/recalculate-all-synthesis`)
  - Serves participant commentary (`/api/submissions/{id}/feedback`)
  - Provides database seeding on startup from `mockData/submissions.json`

- **Task Orchestrator (`orchestrator/celery_app.py`)**:
  - Sequentially invokes each evaluation subsystem for a given submission ID
  - Persists intermediate and final statuses in PostgreSQL with `flag_modified` triggers for JSON fields
  - Synthesizes the overall score using dynamic rubric weights (default 30% CQ, 30% FN, 20% OR, 20% IN)

- **Static Analysis Subsystem (`person_2/core/`)**:
  - `MetricsAggregator`: Walks the target repository and invokes Tree-Sitter, Cyclomatic Complexity Calculator, and linters.
  - Generates maintainability ratings (`CRITICAL_RISK`, `MEDIUM_RISK`, `HIGH`).

- **Dynamic Execution Subsystem (`person_2/functionality/`)**:
  - `DynamicExecutionRunner`: Launches Python, JavaScript, or TypeScript files with timeout enforcement.
  - Collects runtime duration and peak memory usage via OS-specific bindings.

- **Originality Subsystem (`originality/`)**:
  - `CommentNeutralizer`: Strips code comments and normalizes unicode whitespace.
  - `BoilerplateFilter`: Discards standard scaffold code and vendor files.
  - `SearchAPI`: Queries `pgvector` for nearest-neighbor semantic matches.

- **Innovation Subsystem (`innovation/`)**:
  - `ArchitectureEvaluator`: Generates directory trees, scans dependency manifests, and invokes Anthropic Claude to detect architectural patterns (MVC, Monolith, Pipeline) and evaluate technical depth.

## 3. Data Flow
1. Submission request is accepted by FastAPI and given a unique ID (`sub_XXX`).
2. Celery worker picks up the job and moves `pipeline_status` from `pending` to `running`.
3. Worker runs Stages 1 through 4, updating JSON status objects on the Submission record in Postgres.
4. Synthesis service calculates weighted composite score and assigns qualitative bands.
5. Feedback service produces strength and growth bullet points for participants.
6. Worker updates status to `complete`. The frontend polls or retrieves finished reports.
