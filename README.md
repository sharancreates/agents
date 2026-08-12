# ⚖️ AutoJudge — Multi-Agent Hackathon Evaluation Platform

AutoJudge is an automated, multi-agent evaluation platform designed to assess software hackathon submissions across four core technical dimensions: **Code Quality**, **Functionality**, **Originality**, and **Innovation**.

---

## 🚀 Key Features & Subsystem Architecture

- **FastAPI Orchestrator Backend (`api/`)**: Provides REST endpoints for submission intake, manual evaluation overrides, synthesis recalculations, and participant commentary delivery.
- **Celery Task Pipeline (`orchestrator/`)**: Asynchronously manages 4-stage submission evaluation tasks backed by Redis queues.
- **Person 2 Evaluation Engines (`person_2/`)**:
  - *Static Analysis*: Cyclomatic complexity calculation, AST parsing, and linter rule enforcement.
  - *Dynamic Sandbox Runner*: Cross-platform execution profiling (RAM, CPU execution time, stdout/stderr validation, timeout enforcement).
- **Person 3 Evaluation Engines (`originality/`, `innovation/`)**:
  - *Originality*: AST fingerprinting, code vector embeddings, and similarity matching against indexed repositories.
  - *Innovation*: Architectural design pattern detection and README-to-code structural consistency scoring.
- **Synthesis & Feedback Agents (`api/synthesis_service.py`, `api/feedback_service.py`)**: Computes rubric-weighted composite scores and generates participant-facing constructive commentary.
- **React Dashboard Frontend (`frontend/`)**: Modern dark-mode dashboard featuring real-time submission tracking, evaluation breakdowns, and offline fallback mode.

---

## 🛠️ Quick Start & Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

### 1. Environment Setup
Copy the configuration template:
```bash
cp .env.example .env
```

### 2. Launch Infrastructure Services
Start PostgreSQL (with `pgvector`) and Redis:
```bash
docker compose up -d
```

### 3. Backend & Celery Worker Setup
Install dependencies:
```bash
pip install -r requirements.txt
```

Run FastAPI Backend Server:
```bash
uvicorn api.main:app --reload --port 8000
```

Run Celery Worker:
```bash
celery -A orchestrator.celery_app worker --loglevel=info
```

### 4. Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health status check |
| `GET` | `/api/submissions` | List all evaluated submissions |
| `GET` | `/api/submissions/{id}` | Get detailed evaluation breakdown for a submission |
| `POST` | `/api/submissions` | Submit new repository for multi-agent pipeline evaluation |
| `POST` | `/api/submissions/{id}/synthesize` | Recalculate synthesis score with custom rubric weights |
| `GET` | `/api/submissions/{id}/feedback` | Fetch participant-facing feedback report |