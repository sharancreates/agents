# Phase 5: Context & Scope - Enterprise Portal & Real-Time Observability

## 1. Phase Objective
Equip AutoJudge with an **Enterprise Portal & Real-Time Observability Suite** providing hackathon organizers, judges, and developers with:
1. **Real-Time Deliberation Monitor**: Live Server-Sent Events (SSE) stream (`GET /v1/evaluations/{id}/stream`) and interactive UI timeline rendering Recon, QA, Quality, Forensics, Critic Consensus, and Participant Feedback agent thoughts in real-time.
2. **Developer & Billing Console (`/developer`)**: Self-serve portal for issuing scoped API keys (`ak_live_...`), configuring HTTPS webhook endpoints, viewing credit balances, purchasing Razorpay top-up packages, and inspecting usage ledgers.
3. **Interactive Rubric Customizer**: Dynamic rubric controls with 100% sum validation, custom disqualification criteria, and sponsor track bounty threshold overrides.
4. **Judge Copilot Chat Drawer**: Interactive Q&A interface inside the evaluation report backed by the Phase 4.5 RAG engine (`POST /v1/evaluations/{id}/chat`) citing exact `file:start_line-end_line` evidence.
5. **Sandbox Security & Audit Viewer**: Transparent visibility into microVM isolation parameters (memory caps, cgroup enforcement, network egress blocks, and security flags).

---

## 2. Scope Boundaries

### In Scope:
- **Backend Real-Time SSE Endpoint (`api/v1_endpoints.py`)**:
  - `GET /v1/evaluations/{id}/stream`: Streams real-time `text/event-stream` chunks of agent traces and pipeline status transitions.
- **Frontend Observability & Agent Deliberation Console (`frontend/src/components/report/AgentTraceStream.jsx`)**:
  - Visual stage progression (Recon -> QA -> Quality -> Forensics -> Critic -> Feedback).
  - Expandable thought logs, decision reasoning, and cyclomatic complexity metrics.
- **Developer Console (`frontend/src/pages/DeveloperConsole.jsx`)**:
  - Tab 1: **API Keys** - Generation modal (`ak_live_...`), scoping, revocation, last-used timestamp.
  - Tab 2: **Webhooks** - Target URL registration, secret display, test payload dispatch.
  - Tab 3: **Credits & Monetization** - Available credits, instant package top-ups (₹499/₹1,999/₹5,999) via Razorpay, usage audit trail.
- **Interactive Rubric Customizer (`frontend/src/components/submissions/RubricConfig.jsx`)**:
  - Sliders for Code Quality, Functionality, Originality, and Innovation with auto-balancing or 100% sum verification.
  - Custom challenge prompt and disqualification rules input.
- **Judge Copilot Chat Drawer (`frontend/src/components/report/JudgeCopilot.jsx`)**:
  - Drawer widget with suggested prompts ("Where is authentication handled?", "Are there security leaks?").
  - Displays answers with clickable file and line citations.
- **Routing & Navigation (`frontend/src/App.jsx`, `TopNavigationBar.jsx`)**:
  - New `/developer` route and top navigation item with badge.
- **Testing & Verification**:
  - Backend SSE & portal test suite in `person_2/tests/test_portal_observability.py`.
  - Frontend production build verification (`cd frontend; npm run build`).

### Out of Scope:
- Mobile native iOS/Android applications (responsive web handles mobile and desktop).
- Third-party SSO providers (Google/GitHub OAuth deferred to future milestone).
