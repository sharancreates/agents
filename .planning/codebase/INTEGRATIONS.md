# External Integrations & Services

## 1. Database & Vector Storage
- **Service**: PostgreSQL + pgvector
- **Connection**: `DATABASE_URL=postgresql://admin:password@localhost:5433/submissions_db`
- **Tables**: `submissions` (storing metadata, status, JSON dimension reports, synthesis scores, feedback)
- **Vector Index**: 384-dimensional cosine distance index on code snippet embeddings for plagiarism detection.

## 2. Distributed Task Broker
- **Service**: Redis
- **Connection**: `REDIS_URL=redis://localhost:6379/0`
- **Usage**:
  - Celery task broker (`orchestrator.celery_app.process_submission_task`)
  - Celery backend for async task state tracking
  - Temporary caching and queue synchronization

## 3. LLM / AI Providers
- **Provider**: Anthropic Claude API (`anthropic` Python SDK)
- **Integration Points**:
  - `innovation/architecture_evaluator.py`: Prompts Claude to inspect repository tree layouts, manifests, and README files to assess design integrity and architectural authenticity.
  - Graceful Fallback: System operates in simulated/heuristic mode if `ANTHROPIC_API_KEY` or the SDK is absent.

## 4. Host OS Kernel & Memory Profiling
- **Linux**: Interacts directly with `/proc/{pid}/status` (extracting `VmHWM` peak memory bytes).
- **Windows**: Interacts with `psapi.dll` via `ctypes.windll.psapi.GetProcessMemoryCounters` (`PeakWorkingSetSize`).

## 5. Version Control Systems (Git / GitHub)
- **Local Git execution**: Commit SHA extraction, `.gitignore` parsing via `originality/pipeline.py`.
- **Target Repositories**: Remote git clone URLs for submissions (planned webhook triggers).
