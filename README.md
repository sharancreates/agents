<div align="center">

# ⚖️ AutoJudge

### Multi-Agent Hackathon Evaluation & Code Review Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-37B24D?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![React](https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

*An open-source, asynchronous platform that evaluates software hackathon submissions across **Code Quality**, **Functionality**, **Originality**, and **Innovation** using specialized evaluation modules.*

[Features](#-key-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API Reference](#-api-endpoints) • [Contributing](#-contributing)

</div>

---

## 💡 What is AutoJudge?

Evaluating hackathons manually is slow, inconsistent, and often focused purely on superficial UI or pass/fail test cases. **AutoJudge** automates hackathon evaluation by orchestrating **4 specialized evaluation modules** in an asynchronous pipeline:

1. **📊 Static Code Quality Agent** — Parses ASTs, computes cyclomatic complexity, and checks linter rule violations (Ruff, ESLint).
2. **⚡ Dynamic Functionality Sandbox** — Executes submissions in isolated environments with real-time memory profiling (Linux `/proc`, Windows `psapi`) and timeout enforcement.
3. **🔍 Originality Agent** — Performs AST fingerprinting, comment neutralization, boilerplate filtering, and vector similarity search (`SentenceTransformers` + `pgvector`).
4. **🏛️ Architecture & Innovation Agent** — Detects structural design patterns and checks README-to-code alignment.

All metrics are synthesized into a **weighted composite score**, **qualitative verdict**, and **constructive participant commentary**.

---

## 🌟 Key Features

* **⚡ Asynchronous Task Pipeline**: Powered by Celery and Redis to handle concurrent codebase evaluations without blocking.
* **🛡️ Isolated Dynamic Execution**: Runs Python, Node.js, and TypeScript test suites with timeout controls and peak RAM tracking.
* **🧠 Dynamic Rubric Recalculation**: Adjust weights (Code Quality, Functionality, Originality, Innovation) on the fly with real-time score synthesis.
* **💬 Participant-Facing Feedback Engine**: Separates judge-facing numeric metrics from participant-facing constructive feedback reports.
* **🎨 Resilient React Dashboard**: Polished dark-mode UI with full offline support (falls back gracefully to `localStorage` mock data if the backend is offline).

---

## 🏗️ Architecture

```mermaid
flowchart TD
    Client[React Dashboard / CLI] -->|POST /api/submissions| API[FastAPI Server]
    API -->|Enqueue Task| Redis[(Redis Broker)]
    Redis -->|Process| Worker[Celery Worker Pipeline]

    subgraph Evaluation Modules
        Worker --> Stage1[Stage 1: Code Quality Agent\nAST & Cyclomatic Complexity]
        Worker --> Stage2[Stage 2: Functionality Sandbox\nTest Suite & RAM Profiling]
        Worker --> Stage3[Stage 3: Originality Agent\nVector Embeddings & Fingerprinting]
        Worker --> Stage4[Stage 4: Innovation Agent\nArchitecture & Pattern Matching]
    end

    Stage1 & Stage2 & Stage3 & Stage4 --> Synthesis[Synthesis Engine\nWeighted Score & Qualitative Verdict]
    Synthesis --> Feedback[Feedback Agent\nParticipant Commentary]
    Feedback --> DB[(PostgreSQL + pgvector)]
    DB -->|Fetch Results| API
```

---

## 📋 Evaluation Criteria Breakdown

| Evaluation Dimension | Weight (Default) | Key Metrics & Signals Analyzed | Primary Subsystem |
| :--- | :---: | :--- | :--- |
| **Code Quality** | `30%` | Cyclomatic complexity, maintainability index, linter smells (Ruff/ESLint). | `person_2/core` |
| **Functionality** | `30%` | Automated test suite pass rate, peak RAM usage, runtime duration, timeout compliance. | `person_2/functionality` |
| **Originality** | `20%` | Vector similarity ratio, AST fingerprinting, boilerplate exclusion. | `originality` |
| **Innovation** | `20%` | Design pattern detection (MVC, Pipeline, Monolith), README-to-code consistency. | `innovation` |

---

## 🚀 Quick Start

### Prerequisites

* **Python 3.10+**
* **Node.js 18+**
* **Docker & Docker Compose**

### 1. Clone the Repository

```bash
git clone https://github.com/sharancreates/agents.git
cd agents
```

### 2. Configure Environment

Copy the environment template:

```bash
cp .env.example .env
```

Default `.env` configuration:

```env
DATABASE_URL=postgresql://admin:password@localhost:5433/submissions_db
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=development
LOG_LEVEL=INFO
PORT=8000
```

### 3. Launch Core Services (PostgreSQL + Redis)

Start PostgreSQL (with `pgvector`) and Redis via Docker Compose:

```bash
docker compose up -d
```

### 4. Install Dependencies & Start Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run FastAPI API Server
uvicorn api.main:app --reload --port 8000
```

In a separate terminal, launch the Celery task worker:

```bash
celery -A orchestrator.celery_app worker --loglevel=info
```

### 5. Launch Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser to view the evaluation dashboard.

---

## 💻 CLI Quick Scan

You can also run instant local static code quality checks directly via the CLI:

```bash
python -m person_2 .
```

Output:
```text
============================================================
🚀 Code Quality Agent Execution Loop
Target Scope: /path/to/project
============================================================
⚙️ Loaded Exclusions: node_modules, .git, __pycache__, venv, env
⏳ Scanning files and compiling metrics...

📊 ANALYSIS SUMMARY:
 • Total Evaluated Files   : 14
 • Global Maintainability  : HIGH
 • Total Code Smells Found : 2
 • Average Complexity      : 1.45
 • Max Observed Complexity : 4
============================================================
✅ Scan completed successfully.
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check endpoint. |
| `GET` | `/api/submissions` | Retrieve all evaluated hackathon submissions. |
| `GET` | `/api/submissions/{id}` | Get detailed score breakdown and flags for a submission. |
| `POST` | `/api/submissions` | Submit a repository URL for 4-stage pipeline evaluation. |
| `POST` | `/api/submissions/{id}/synthesize` | Recalculate synthesis score with custom weight overrides. |
| `POST` | `/api/submissions/recalculate-all-synthesis` | Recalculate composite scores across all complete submissions. |
| `GET` | `/api/submissions/{id}/feedback` | Fetch participant-facing commentary and actionable tips. |

---

## 🧪 Running Tests

Run the backend unit and integration test suite:

```bash
pytest person_2/tests/
```

Run originality pipeline tests:

```bash
pytest originality/
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.