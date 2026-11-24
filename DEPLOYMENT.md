# AutoJudge Production Deployment Guide

This guide details how to configure, containerize, and deploy the **AutoJudge Agentic AI B2B SaaS Platform** to local staging and cloud production environments (AWS, GCP, DigitalOcean, or Kubernetes).

---

## Architecture Topology

```
             ┌─────────────────────────┐
             │ Cloudflare / Load Balancer │
             │      (HTTPS / SSL)       │
             └────────────┬────────────┘
                          │
         ┌────────────────┴────────────────┐
         │                                 │
         ▼                                 ▼
┌─────────────────┐               ┌─────────────────┐
│ Frontend Nginx  │               │  FastAPI (API)  │
│  (React 19 SPA) │──────────────▶│ (Port 8000)     │
│   (Port 3000)   │  /v1/, /api/  │                 │
└─────────────────┘               └────────┬────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
           ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
           │ PostgreSQL +    │    │      Redis      │    │ Celery Workers  │
           │ pgvector (5432) │    │  Broker (6379)  │◀───│ (Agent Council) │
           └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                                  │
                                                                  ▼
                                                         ┌─────────────────┐
                                                         │ Isolated MicroVM│
                                                         │ Sandbox (Docker/│
                                                         │      E2B)       │
                                                         └─────────────────┘
```

---

## 1. Quickstart: 1-Command Local Deployment

Run the complete multi-service stack with persistent vector database, Celery workers, API server, and Nginx-proxied React frontend:

```bash
# 1. Clone repository
git clone https://github.com/sharancreates/agents.git
cd agents

# 2. Configure environment
cp .env.example .env
# Fill in your GEMINI_API_KEY / OPENAI_API_KEY / RAZORPAY credentials in .env

# 3. Build and launch all 5 containers
docker compose up --build -d
```

### Verification Ports:
- **Enterprise Web Portal**: [http://localhost:3000](http://localhost:3000)
- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **PostgreSQL (pgvector)**: `localhost:5433` (mapped from container `5432`)
- **Redis Broker**: `localhost:6379`

---

## 2. Environment Configuration Matrix

All configuration is managed through environment variables. See [`.env.example`](./.env.example) for exact defaults.

| Variable | Description | Production Default / Recommendation |
| :--- | :--- | :--- |
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql://user:pass@host:5432/submissions_db` |
| `REDIS_URL` | Redis URL for Celery & Caching | `redis://redis_host:6379/0` |
| `CELERY_BROKER_URL` | Task queue broker | Same as `REDIS_URL` |
| `CELERY_RESULT_BACKEND` | Task result storage | Same as `REDIS_URL` |
| `RAZORPAY_KEY_ID` | Razorpay Merchant Key ID | `rzp_live_...` (or `rzp_test_...` for staging) |
| `RAZORPAY_KEY_SECRET` | Razorpay Merchant Secret | Secure secret from dashboard |
| `RAZORPAY_WEBHOOK_SECRET`| Secret used to sign incoming webhooks | Strong random string (matches Razorpay webhook settings) |
| `SANDBOX_PROVIDER` | Execution backend for code analysis | `docker` or `e2b` |
| `E2B_API_KEY` | E2B Cloud Sandbox token | Required if `SANDBOX_PROVIDER=e2b` |
| `GEMINI_API_KEY` | Google Gemini LLM API key | Used by Agentic Council & Judge Copilot |
| `OPENAI_API_KEY` | OpenAI LLM API key | Alternate LLM provider |
| `API_RATE_LIMIT_PER_MINUTE`| Sliding-window API throttle | `60` |
| `CORS_ORIGINS` | Permitted browser origins | `https://yourdomain.com,https://app.yourdomain.com` |

---

## 3. Production Cloud Deployment Playbooks

### Option A: AWS (ECS Fargate + RDS Aurora + ElastiCache)
1. **Database**: Spin up Amazon Aurora PostgreSQL with `pgvector` extension enabled:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
2. **Cache**: Provision AWS ElastiCache for Redis (Cluster or Serverless).
3. **Containers**:
   - Push `Dockerfile.backend` to AWS ECR as `autojudge-backend`.
   - Push `frontend/Dockerfile` to AWS ECR as `autojudge-frontend`.
4. **ECS Task Definitions**:
   - `autojudge-api`: 1 vCPU, 2GB RAM, target group mapped to Application Load Balancer (ALB).
   - `autojudge-worker`: 2 vCPU, 4GB RAM (scales horizontally based on Redis queue depth).
   - `autojudge-frontend`: 0.5 vCPU, 1GB RAM on ALB port 443/80.
5. **Security**: Store all secrets in AWS Secrets Manager and inject into ECS container definitions via IAM role.

### Option B: Google Cloud Platform (Cloud Run / GKE + Cloud SQL)
1. **Database**: Provision Google Cloud SQL for PostgreSQL 15+ with `pgvector` flag enabled.
2. **Worker & API**: Deploy `Dockerfile.backend` to **Google Cloud Run** or **GKE**:
   ```bash
   gcloud builds submit --tag gcr.io/$PROJECT_ID/autojudge-backend -f Dockerfile.backend
   gcloud run deploy autojudge-api --image gcr.io/$PROJECT_ID/autojudge-backend --port 8000
   ```
3. For Celery asynchronous workers, deploy on **GKE (Google Kubernetes Engine)** or **Compute Engine VM** where long-running daemon processes are standard.

### Option C: DigitalOcean / Render / Railway
1. **Render / Railway**:
   - Add a managed PostgreSQL instance with `pgvector`.
   - Add a managed Redis instance.
   - Deploy backend as a Web Service running `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.
   - Deploy background worker running `celery -A orchestrator.celery_app worker --loglevel=info`.
   - Deploy frontend as a Static Site or Docker Web Service with build command `npm run build`.

---

## 4. Production Pre-Flight Checklist

Before making AutoJudge publicly available or accepting customer payments:

- [ ] **Razorpay Live Activation**:
  - Replace `rzp_test_...` with your activated `rzp_live_...` credentials in `.env`.
  - Configure the webhook endpoint in your Razorpay Dashboard: `https://api.yourdomain.com/v1/billing/webhook` with event `payment.captured`.
  - Enter the matching `RAZORPAY_WEBHOOK_SECRET`.
- [ ] **Domain & TLS/SSL**:
  - Point your production domain DNS to your load balancer or reverse proxy.
  - Enable SSL termination (e.g. Let's Encrypt, AWS ACM, or Cloudflare Universal SSL).
- [ ] **PostgreSQL Migration & Extension**:
  - Verify that `CREATE EXTENSION IF NOT EXISTS vector;` runs successfully upon database initialization.
  - SQLAlchemy auto-creates all schemas (`organizations`, `api_keys`, `submissions`, `code_embeddings`, `usage_events`, etc.) on API startup.
- [ ] **Execution Sandbox Hardening**:
  - For Docker sandbox: Ensure the Docker daemon socket is securely mounted or utilize the `e2b` provider (`SANDBOX_PROVIDER=e2b`) for fully isolated remote Firecracker microVMs.
- [ ] **CORS Restrictions**:
  - Update `CORS_ORIGINS` in production `.env` to reject non-whitelisted cross-origin domains.

---

## 5. Operations, Maintenance & Monitoring

### Viewing Live Logs:
```bash
# Backend API logs
docker compose logs -f api

# Celery Agent Council logs
docker compose logs -f worker

# Frontend Nginx logs
docker compose logs -f frontend
```

### Database Backup Strategy:
```bash
# Automated Daily Vector DB Dump
docker exec -t autojudge_db pg_dump -U admin submissions_db > backup_$(date +%Y%m%d).sql
```

### Running Test Suite Against Staging:
```bash
pytest -o pythonpath=".venv/Lib/site-packages ." person_2/tests/ -v
```
All 60 automated tests must pass before deploying any pull request to production.
