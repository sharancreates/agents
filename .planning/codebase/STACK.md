# Technology Stack & Environment

## 1. Programming Languages & Runtimes
- **Python**: Version `3.10+` (primary backend, static analysis, Celery pipeline, ML/vector search)
- **JavaScript / TypeScript**: Node.js `18+` (frontend dashboard, target code execution in dynamic runner)
- **SQL**: PostgreSQL 15/16 dialect with `pgvector` extension

## 2. Frameworks & Core Libraries
- **FastAPI**: Core REST API framework (`api/main.py`, `person_2/api/app.py`)
- **Uvicorn**: ASGI web server running FastAPI on port 8000
- **Celery**: Distributed task queue engine (`orchestrator/celery_app.py`, `innovation/celery_app.py`)
- **SQLAlchemy**: ORM for database modeling and query execution (`api/models.py`, `api/database.py`)
- **Pydantic**: Request/response validation schemas (`api/main.py`, `innovation/schemas.py`, `person_2/api/schemas.py`)
- **React 19**: Modern frontend single-page application (`frontend/`) built with Vite

## 3. Data Storage & Messaging
- **PostgreSQL**: Primary relational database for submissions, scores, and participant feedback
- **pgvector**: High-dimensional vector search extension for semantic code embeddings
- **Redis**: In-memory data store acting as Celery message broker and result backend (`redis://localhost:6379/0`)

## 4. Machine Learning & Code Analysis
- **Sentence-Transformers**: `all-MiniLM-L6-v2` for generating dense code snippet embeddings
- **Tree-Sitter**: Multi-language AST parsing (Python, JavaScript/TypeScript)
- **Radon / AST Visitors**: Cyclomatic complexity and maintainability index computation
- **Ruff**: High-performance Python linter
- **ESLint**: JavaScript/TypeScript linter
- **Anthropic Claude SDK**: Optional LLM client for architectural reasoning and evaluation

## 5. Infrastructure & Tooling
- **Docker & Docker Compose**: Containerized services (`postgres` with pgvector on port 5433, `redis` on port 6379)
- **Pytest**: Backend unit and integration test framework
