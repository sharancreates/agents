# Onboarding Summary: AutoJudge

## Executive Summary
AutoJudge has been fully onboarded into the GSD planning system. The codebase has been surveyed and mapped across technology stack, architecture, integrations, structure, conventions, testing, and concerns. A comprehensive transformation plan has been defined to convert AutoJudge from a deterministic pipeline into a commercial **Agentic AI Product-as-a-Service (B2B SaaS)**.

---

## Codebase Map Quick Index
The complete evidence-backed codebase analysis is stored in `.planning/codebase/`:

| Document | Focus Area | Summary of Findings |
| :--- | :--- | :--- |
| [`STACK.md`](file:///c:/Users/Sharanya%20Nagar/Desktop/Projects/agentic-ai/agents/.planning/codebase/STACK.md) | Technologies & Versions | Python 3.10+, FastAPI, Celery, Redis, PostgreSQL + pgvector, React 19, Sentence-Transformers, Tree-Sitter, Ruff. |
| [`INTEGRATIONS.md`](file:///c:/Users/Sharanya%20Nagar/Desktop/Projects/agentic-ai/agents/.planning/codebase/INTEGRATIONS.md) | External Services & APIs | PostgreSQL pgvector, Redis broker, Anthropic Claude API, Windows `psapi` & Linux `/proc` kernel bindings. |
| [`ARCHITECTURE.md`](file:///c:/Users/Sharanya%20Nagar/Desktop/Projects/agentic-ai/agents/.planning/codebase/ARCHITECTURE.md) | Design & Data Flow | Asynchronous pipeline: FastAPI gateway -> Redis queue -> Celery worker executing 4 evaluation stages -> Synthesis & Feedback -> Postgres. |
| [`STRUCTURE.md`](file:///c:/Users/Sharanya%20Nagar/Desktop/Projects/agentic-ai/agents/.planning/codebase/STRUCTURE.md) | Directory Layout | Detailed breakdown of `api/`, `orchestrator/`, `person_2/`, `originality/`, `innovation/`, and `frontend/`. |
| [`CONVENTIONS.md`](file:///c:/Users/Sharanya%20Nagar/Desktop/Projects/agentic-ai/agents/.planning/codebase/CONVENTIONS.md) | Coding Standards | Defensive imports with graceful simulation fallbacks, Pydantic boundary validation, SQLAlchemy JSON flag tracking. |
| [`TESTING.md`](file:///c:/Users/Sharanya%20Nagar/Desktop/Projects/agentic-ai/agents/.planning/codebase/TESTING.md) | Test Coverage & Gaps | Pytest suites in `person_2/tests/` and `originality/`; identified gap in dynamic prompt-based test generation and full CI pipeline. |
| [`CONCERNS.md`](file:///c:/Users/Sharanya%20Nagar/Desktop/Projects/agentic-ai/agents/.planning/codebase/CONCERNS.md) | Vulnerabilities & Risks | **Critical**: Host-level subprocess execution of untrusted code in `runner.py`. **High**: Lack of multi-tenant auth and API key control. |

---

## Strategic Transformation Plan
To achieve the user's vision of creating a revenue-generating Agentic AI SaaS:
1. **Phase 1: Secure MicroVM Execution Sandbox**: Eliminate host RCE vulnerability by running submissions in isolated microVMs (E2B / gVisor).
2. **Phase 2: Agentic Evaluation Council**: Transition from static scripts to an autonomous multi-agent state graph (ReAct loop, dynamic test synthesis, adversarial QA, critic reflection).
3. **Phase 3: Multi-Tenancy & Developer B2B API**: Enable Devpost, DoraHacks, and recruitment platforms to embed AutoJudge via API keys, webhooks, and SSE streams.
4. **Phase 4: Monetization & Metered Billing**: Implement Stripe/Lago usage-based billing per evaluation and compute minute.
5. **Phase 5: Enterprise Portal & Observability**: Real-time agent thought streams, custom rubric designer, and API key management console.

---

## Next Steps
- To begin execution of Phase 1 (Secure Sandbox Engine), run:
  ```bash
  /gsd-plan-phase 1
  ```
- To review or update project requirements:
  - Inspect [`.planning/REQUIREMENTS.md`](file:///c:/Users/Sharanya%20Nagar/Desktop/Projects/agentic-ai/agents/.planning/REQUIREMENTS.md)
  - Inspect [`.planning/ROADMAP.md`](file:///c:/Users/Sharanya%20Nagar/Desktop/Projects/agentic-ai/agents/.planning/ROADMAP.md)
