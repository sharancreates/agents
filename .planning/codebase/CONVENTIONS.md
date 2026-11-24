# Code Conventions & Engineering Standards

## 1. Code Style & Formatting
- **Python**: PEP 8 compliance enforced via `ruff`.
- **Typing**: Type annotations used across service interfaces (`Dict[str, Any]`, `List[str]`, `Optional[float]`).
- **Data Models**: Pydantic models for validation at boundaries (`BaseModel`, `Field`), with fallback definitions when Pydantic is optional.
- **JavaScript / React**: Functional components, React Hooks (`useState`, `useEffect`, `useContext`), standard ES modules.

## 2. Architectural Conventions
- **Defensive Importing & Degradation**:
  - Optional dependencies (e.g. `anthropic`, `tree_sitter`, `pydantic`) are wrapped in `try/except ImportError` blocks.
  - When external dependencies are missing, modules log warnings and fall back gracefully to heuristic or simulation modes rather than crashing.
- **Separation of Concerns**:
  - Judge-facing quantitative scoring (`api/synthesis_service.py`) is decoupled from participant-facing qualitative commentary (`api/feedback_service.py`).
  - Worker tasks handle computation asynchronously; the FastAPI web service remains non-blocking.
- **State Mutation in ORM**:
  - Because dimension reports are stored as JSON columns on the `Submission` model, mutations explicitly invoke `sqlalchemy.orm.attributes.flag_modified(sub, field_name)` prior to `db.commit()`.

## 3. Error Handling & Resilience
- **Process Timeouts**: Dynamic execution enforces explicit deadlines (`FunctionalityConfig(timeout_seconds=5)`) and terminates timed-out child processes.
- **Safe File Reads**: Repository inspection limits file reads (e.g., first 5000 chars of README, filtered manifests) to prevent memory exhaustion on giant submissions.
- **Frontend Fallbacks**: The frontend client checks backend health and falls back seamlessly to `localStorage` mock data if the API server is unavailable.
