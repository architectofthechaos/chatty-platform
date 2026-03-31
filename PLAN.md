# Chatty Platform Engineering - Implementation Plan

## Overview
Take the working Chatty API and operationalize it into a platform-ready service.
Timebox: 2-4 hours. Quality and clarity over scope.

---

## Tier 1: Must Do

### 1. Dockerize the Application
- [ ] Create `app/Dockerfile` (Python 3.11, poetry install, uvicorn entrypoint)
- [ ] Create `docker-compose.yml` at repo root
- [ ] Add Postgres service in docker-compose (replace SQLite for realistic setup)
- [ ] Add `.dockerignore` to keep image lean
- [ ] Verify: `docker compose up` gets a working app at `localhost:8000/docs`

### 2. Config / Environment Variable Management
- [ ] Extract hardcoded values from code into env vars:
  - Database URL (`DATABASE_URL`)
  - CORS allowed origins (`CORS_ALLOWED_ORIGINS`)
  - App port (`APP_PORT`)
  - Debug/log level (`LOG_LEVEL`)
- [ ] Create `.env.example` with documented defaults (committed to repo)
- [ ] Create `.env` for local dev (added to `.gitignore`)
- [ ] Update `core/database.py` to read `DATABASE_URL` from env
- [ ] Update `main.py` to read CORS origins from env

### 3. Fix CORS TODO
- [ ] Replace `cors_allowed_origins="*"` with env-var-driven config
- [ ] Default to `"*"` in dev, require explicit origins in production

### 4. Basic GitHub Actions CI
- [ ] Create `.github/workflows/ci.yml`
- [ ] Steps:
  - Checkout code
  - Setup Python 3.11
  - Install dependencies (poetry install)
  - Run linter (ruff or flake8)
  - Run unit tests (pytest)
  - Build Docker image
  - Export OpenAPI spec (Option B script)
  - Upload OpenAPI spec as build artifact

---

## Tier 2: Should Do

### 5. OpenAPI Spec Generation (Option B)
- [ ] Create `app/scripts/generate_openapi.py`
- [ ] Script imports `app` and calls `app.openapi()` -- no server needed
- [ ] Integrate into CI workflow as a build artifact

### 6. DB Migration Instrumentation
- [ ] Add Alembic as a dependency
- [ ] Initialize Alembic config (`alembic init`)
- [ ] Create initial migration from existing models
- [ ] Remove the "drop all tables on startup" behavior from `main.py`
- [ ] Document how to run migrations (`alembic upgrade head`)

### 7. Socket.IO Error Handling (fix in-code TODOs)
- [ ] Create `core/socketio_errors.py` with decorator-based error handler
- [ ] Define error map (ValueError, PermissionError, KeyError, etc.)
- [ ] Apply decorator to `join` and `leave` events in `main.py`
- [ ] Structured error responses: `{code, message, event}`

---

## Tier 3: Describe in RATIONALE.md (don't implement)

### 8. Infra as Code / Terraform
- Describe: VPC, ECS Fargate or EKS, RDS Postgres, ALB, security groups
- Describe: Terraform dependency graph and module structure
- Mention what would go in the existing `terraform/` folder

### 9. CI/CD Full Pipeline
- Describe: dev → staging → production promotion
- Describe: Blue/green or canary deployment strategy
- Describe: Automated rollback on health check failure

### 10. Auth/Authz Approach
- Describe: JWT or OAuth2 for REST endpoints
- Describe: Token-based auth for Socket.IO connections
- Describe: Role-based access control for chatrooms

### 11. Exposing Service to Front-End
- Describe: API Gateway / ALB with WebSocket support
- Describe: CDN for static assets, reverse proxy config
- Describe: HTTPS termination at load balancer

### 12. Auto Scaling & Load Testing
- Describe: Horizontal scaling (ECS service auto-scaling or HPA in k8s)
- Describe: Load testing with k6 or Locust
- Describe: Scaling triggers (CPU, memory, request count)

### 13. Cloud Spend Management
- Describe: Right-sizing instances, spot/Fargate Spot
- Describe: Cost alerts and budgets (AWS Budgets)
- Describe: Dev/staging environments with auto-shutdown

### 14. General SDLC
- Describe: Branching strategy (trunk-based or GitFlow)
- Describe: PR review process, required checks
- Describe: Feature flags, environment parity

### 15. SLA, SLO, SLI & Infrastructure Monitoring
- Define SLIs: request latency (p50/p95/p99), error rate (5xx/total), uptime percentage, Socket.IO connection success rate
- Define SLOs: targets per SLI (e.g., p99 latency < 300ms, error rate < 0.1%, 99.9% uptime)
- Define SLAs: external commitments to consumers built on top of SLOs with consequences
- Describe: How to instrument SLIs (Prometheus metrics from FastAPI middleware, DB query duration, health check probes)
- Describe: Alerting on SLO burn rate (e.g., Prometheus + Alertmanager, PagerDuty integration)
- Describe: Dashboards for SLO tracking (Grafana SLO dashboards, error budgets)

### 16. Observability Stack (Monitoring, Logging, Tracing)
- Logging: Structured JSON logs (already in place via structlog) → ship to centralized log aggregation (ELK / Loki + Grafana)
- Metrics: Prometheus exposition from app (request count, latency histograms, DB pool stats) → Grafana dashboards
- Tracing: Distributed tracing with OpenTelemetry SDK → Jaeger or Tempo for request flow across services
- Describe: How the three pillars connect -- correlate trace IDs in logs, link metrics spikes to traces
- Describe: Health check endpoints (liveness vs readiness probes for k8s / ECS)

### 17. DevSecOps for GitHub Actions
- Describe: Dependency vulnerability scanning (Dependabot, `pip-audit`, Snyk)
- Describe: Container image scanning (Trivy, Grype) in CI before pushing to registry
- Describe: Secret scanning (GitHub secret scanning, gitleaks)
- Describe: SAST -- static analysis for security (Bandit for Python, Semgrep)
- Describe: Least-privilege CI permissions (GITHUB_TOKEN scoping, OIDC for cloud auth instead of long-lived keys)
- Describe: Signed commits and image signing (Sigstore/cosign)

### 18. Implementing AuthN & AuthZ
- AuthN: Authentication -- verifying identity (JWT issued by IdP like Auth0/Cognito, OAuth2 flows)
- AuthZ: Authorization -- verifying permissions (RBAC for chatroom access, middleware/dependency injection in FastAPI)
- Describe: Token validation middleware for REST endpoints
- Describe: Socket.IO auth -- token passed during handshake, validated on `connect` event
- Describe: Chatroom-level permissions (owner, member, read-only) enforced at API layer
- Describe: API key auth for service-to-service communication

### 19. Implementing TLS
- Describe: TLS termination at load balancer (ALB/Nginx) vs end-to-end encryption
- Describe: Certificate management (ACM for AWS, Let's Encrypt for self-managed, cert-manager for k8s)
- Describe: Enforcing HTTPS redirects, HSTS headers
- Describe: mTLS for internal service-to-service communication
- Describe: Local dev with self-signed certs or TLS-terminating reverse proxy in docker-compose

---

## Final Deliverables

### 20. RATIONALE.md
- [ ] Document every decision made and why
- [ ] Explain AI usage (what tools, how, why)
- [ ] Cover Tier 3 items with 2-3 sentences each
- [ ] Trade-offs and what you'd do with more time

### 21. Update README.md
- [ ] Replace existing TODOs with completed/remaining status
- [ ] Clear bootstrapping instructions (`docker compose up`)
- [ ] Link to RATIONALE.md

### 22. Submission
- [ ] Push to GitHub repo
- [ ] Take screenshots: CI run, Swagger docs, one key insight
- [ ] Verify: fresh clone → `docker compose up` → working app

---

## Suggested Execution Order
1. Understand codebase (done)
2. Dockerize (Dockerfile + docker-compose)
3. Config / env var management
4. Fix CORS
5. GitHub Actions CI
6. OpenAPI spec generation script
7. DB migration scaffold (if time allows)
8. Socket.IO error handling (if time allows)
9. Write RATIONALE.md
10. Update README.md
11. Final test: fresh clone → docker compose up
