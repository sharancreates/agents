# Project: AutoJudge (Agentic AI B2B Evaluation SaaS)

## Overview & Mission
**AutoJudge** is an autonomous code evaluation and judging platform designed to evaluate software hackathon submissions, technical assessments, and open-source contributions. The project's mission is to transition from a deterministic pipeline into a commercial **Agentic AI Product-as-a-Service (B2B SaaS)** sold to hackathon hosts (e.g. Devpost, DoraHacks), technical hiring platforms (e.g. HackerRank), universities, and enterprise hackathons.

## Core Value Proposition
- **Autonomous Multi-Agent Evaluation**: Instead of rigid static linters and hardcoded tests, specialized AI agents perceive repository structure, synthesize custom test cases, execute code in secure sandboxes, perform git forensics, and deliberate to reach fair, explainable verdicts.
- **Enterprise-Grade Sandboxing**: Complete isolation of untrusted third-party code in ephemeral MicroVMs.
- **Pluggable & Headless B2B API**: Third-party platforms can trigger evaluations via REST API, stream live agent progress over SSE, and receive webhooks upon completion.
- **Monetization Engine**: Native multi-tenancy, API key management, and metered usage billing.

## Current State & Evolution
- **Brownfield Foundation**:
  - FastAPI backend (`api/`) + Celery/Redis task queue (`orchestrator/`)
  - PostgreSQL with `pgvector` for vector embeddings
  - React 19 single-page dashboard (`frontend/`)
  - Four existing evaluation stages (Static Code Quality, Dynamic Functionality Runner, Originality Vector Search, Architecture/Innovation Evaluator)
- **Target Commercial Architecture**:
  - ReAct / Critic multi-agent workflow replacing sequential Celery stages
  - MicroVM sandboxes (E2B / Firecracker / gVisor) replacing host subprocess execution
  - Multi-tenant data model (Organizations, Workspaces, Scoped API Keys)
  - Stripe/Lago metered billing infrastructure
