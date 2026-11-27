# Codebase Structure & Directory Map

## Root Directory Overview
```
agents/
├── api/                    # FastAPI web server, database config, models, synthesis & feedback
├── orchestrator/           # Celery application & worker task definitions
├── person_2/               # Person 2 modules: Static Code Quality & Dynamic Functionality
│   ├── core/               # AST parsing, complexity calculation, linters, rules, detector
│   ├── functionality/      # Dynamic test runner, memory profiling, test execution scoring
│   ├── api/                # Internal prototype routes and schemas
│   └── tests/              # Pytest test suite for Person 2 modules
├── originality/            # Plagiarism detection, comment neutralization, vector embeddings
├── innovation/             # Architecture evaluation, tree hierarchy mapper, Claude LLM integration
├── frontend/               # React 19 + Vite dashboard application
│   └── src/
│       ├── components/     # UI widgets, badges, scorecards, metric bars
│       ├── pages/          # Dashboard, Leaderboard, SubmissionDetail, Submit, Login
│       ├── mockData/       # Seed submissions data for demo and offline fallback
│       └── services/       # API client communicating with FastAPI
├── documentation/          # 20+ engineering blueprints and technical architecture specs
├── docker-compose.yml      # Container definition for PostgreSQL (pgvector) and Redis
├── requirements.txt        # Python dependency manifest
└── schema_proposal.json    # JSON Schema definition for evaluation reports
```

## Detailed Module Responsibilities

### 1. `api/`
- `main.py`: Primary application entrypoint; routes for submissions, score synthesis, and feedback.
- `models.py`: SQLAlchemy ORM model `Submission` mapping database columns and JSON fields.
- `database.py`: SQLAlchemy engine, `SessionLocal` factory, and `Base` declaration.
- `synthesis_service.py`: Mathematical weight synthesis and qualitative verdict generator.
- `feedback_service.py`: Generates participant-facing highlights, growth points, and advice.

### 2. `orchestrator/`
- `celery_app.py`: Celery instance connected to Redis broker; hosts `process_submission_task`.

### 3. `person_2/`
- `core/aggregator.py`: `MetricsAggregator` traversing directories to execute static checks.
- `core/complexity.py`: Cyclomatic complexity calculator using tree-sitter AST nodes.
- `core/detector.py`: Multi-language file detector (Python, JS, TS).
- `core/linters.py`: Invokes Ruff and ESLint CLI executables.
- `functionality/runner.py`: `DynamicExecutionRunner` running processes with timeouts and memory monitoring.
- `functionality/scoring.py`: Scores test pass ratios, duration, and memory footprint.

### 4. `originality/`
- `comment_neutralizer.py`: Regex-based and AST comment stripping.
- `boilerplate_filter.py`: Filters standard frameworks, configs, and boilerplate files.
- `pipeline.py`: End-to-end file ingestion, embedding generation, and vector index persistence.
- `search_api.py`: Nearest neighbor vector query interface against `pgvector`.

### 5. `innovation/`
- `evaluator.py`: `UnifiedAgentEvaluator` bridging originality and innovation metrics.
- `architecture_evaluator.py`: Scans repo trees and prompts Claude for structural design analysis.
- `schemas.py`: Pydantic validation schemas for architecture scores and pattern detection.

### 6. `frontend/`
- `src/pages/Dashboard.jsx`: Main overview table of all submissions with live status badges.
- `src/pages/SubmissionDetail.jsx`: Drill-down view of the 4 dimensions, radar/metrics charts, and feedback.
- `src/pages/Submit.jsx`: Form to submit new repositories for evaluation.
