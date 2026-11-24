# Phase 5 Plan: Enterprise Portal & Real-Time Observability

## Goal
Implement a commercial-grade **Enterprise Portal and Real-Time Observability Suite** featuring live Server-Sent Events (SSE) agent thought streaming, an interactive Developer & Billing Console (`/developer`), an interactive Rubric Customizer, and an embedded **Judge Copilot Chat Drawer** backed by the codebase RAG engine.

---

## 1. Architecture & Component Hierarchy

```
AutoJudge Enterprise Portal (frontend/)
  ├── TopNavigationBar (/ , /submit , /leaderboard , /developer)
  │
  ├── Developer & Billing Console (/developer - DeveloperConsole.jsx)
  │     ├── API Keys Tab (create scoped keys, view prefixes, revoke)
  │     ├── Webhook Endpoints Tab (register HTTPS URL, view secret, test ping)
  │     └── Credits & Billing Tab (balance, Razorpay package checkout, usage ledger)
  │
  ├── Submission Detail & Real-Time Observability (/submission/:id - SubmissionDetail.jsx)
  │     ├── Agent Deliberation Console (AgentTraceStream.jsx - live SSE stream)
  │     │     └── Recon -> QA Sandbox -> Quality -> Forensics -> Critic -> Feedback
  │     ├── Evaluation Scorecard & Participant Dossier
  │     ├── Sandbox Security & Cgroup Audit Viewer
  │     └── Judge Copilot Chat Drawer (JudgeCopilot.jsx - asks RAG engine with line citations)
  │
  └── Interactive Rubric Customizer (RubricConfig.jsx)
        ├── 100% Weight Sum Validation & Auto-Normalizer
        ├── Custom Challenge & Disqualification Prompts
        └── Sponsor Track Bounty Overrides
```

---

## 2. Task Breakdown

### Task 1: [TRACER SLICE] Real-Time Observability & SSE Streaming Endpoint
- **Files**:
  - `api/v1_endpoints.py`:
    - Add `GET /v1/evaluations/{submission_id}/stream`:
      - Emits `text/event-stream` line-delimited events (`data: {...}\n\n`).
      - Streams initial state, existing traces, live updates, and terminal `pipeline.complete` event.
  - `frontend/src/services/api.js`:
    - Add `streamEvaluationTraces(submissionId, onTrace, onStatusChange, onError)` using browser `EventSource` with polling fallback.

### Task 2: Live Agent Deliberation Console Component
- **Files**:
  - `frontend/src/components/report/AgentTraceStream.jsx`:
    - Visual timeline of Council agents:
      - Recon (Stack & Entrypoint)
      - QA Agent (Dynamic Sandbox Test Synthesis)
      - Quality Agent (AST Cyclomatic Complexity & Maintainability)
      - Forensics Agent (Git Cadence & Originality Signals)
      - Critic Agent (Evidence Calibration & Final Verdict)
      - Feedback Coach (Constructive Participant Dossier)
    - Animated status pulses (running, complete, failed).
    - Expandable reasonings and code evidence snippets.
  - Mount component into `frontend/src/pages/SubmissionDetail.jsx`.

### Task 3: Developer & Billing Portal (`DeveloperConsole.jsx`)
- **Files**:
  - `frontend/src/pages/DeveloperConsole.jsx`:
    - **Tab 1: API Keys**:
      - List active keys (`ak_live_...`), scopes, last used dates.
      - "Generate New Key" modal with one-click copy and warning dialog.
    - **Tab 2: Webhooks**:
      - Register HTTPS webhook endpoint, display signing secret.
      - "Send Test Webhook" trigger.
    - **Tab 3: Credits & Billing**:
      - Live credit balance widget.
      - Buy Credit Packages (Starter ₹499, Pro ₹1,999, Enterprise ₹5,999) invoking `/v1/billing/orders` and `/v1/billing/verify-payment`.
      - Chronological consumption audit ledger.
  - `frontend/src/App.jsx`:
    - Register `/developer` route.
  - `frontend/src/components/layout/TopNavigationBar.jsx`:
    - Add "Developer" navigation link.

### Task 4: Interactive Rubric Customizer & Judge Copilot Widget
- **Files**:
  - `frontend/src/components/submissions/RubricConfig.jsx`:
    - Interactive sliders for Code Quality, Functionality, Originality, and Innovation.
    - Real-time sum validator with warning when $\ne 100\%$ and an "Auto-Balance" one-click action.
    - Custom prompt input for specialized evaluation focus.
  - `frontend/src/components/report/JudgeCopilot.jsx`:
    - Collapsible chat drawer in `SubmissionDetail.jsx`.
    - Preset quick prompts ("Where is authentication verified?", "Check for security violations").
    - Submits to `POST /v1/evaluations/{id}/chat`.
    - Renders answer with clickable citation chips (`file:start_line-end_line`).

### Task 5: Automated Verification Suite & Production Build
- **Files**:
  - `person_2/tests/test_portal_observability.py`:
    - Test SSE streaming endpoint headers and event formatting.
    - Test Developer Console endpoints (keys, webhooks, billing balance).
  - Production Build:
    - Execute `cd frontend; npm run build` verifying clean compilation of all new JSX components.
  - Full Regression:
    - Run all 56 existing unit and integration tests to ensure 100% green status.

---

## 3. Technical Invariants
- **Non-blocking SSE Streaming**: Backend streaming generator releases database connections defensively and uses non-blocking intervals.
- **Secret Hygiene**: Secret API keys are shown only once upon creation; subsequent views display only prefixes (`ak_live_xxxx...`).
- **Zero Frontend Bundle Failures**: Strict Vite production build passes with 0 syntax or import errors.
