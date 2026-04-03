# RATIONALE

Decisions, trade-offs, and architectural thinking behind operationalizing the Chatty backend.

---

## Infra as Code Approach

Chatty is a containerized FastAPI service with a Postgres database and WebSocket (Socket.IO) support. For production infrastructure, I would deploy this on AWS using Terraform with the following core services:

- **Amazon EKS** for container orchestration. Kubernetes gives us a portable abstraction that avoids deep AWS lock-in. EKS also integrates well with security and compliance tooling. The trade-off vs. ECS is operational complexity, but the flexibility and ecosystem (Helm, Prometheus, cert-manager, ingress controllers) justify it for a team that expects to run multiple services.
- **Amazon RDS (Postgres)** for the database. Managed service handles backups, patching, failover. Multi-AZ for production, single-AZ for dev/staging to manage cost.
- **Application Load Balancer (ALB)** with WebSocket support, required for Socket.IO connections. HTTPS termination happens here via ACM certificates.
- **Amazon ECR** for container image storage. Private registry integrated with EKS, images scanned on push.

Infrastructure is managed as code with the same rigor as application code. GitOps deployment via CI, no developer runs `terraform apply` from their local machine. Remote state is stored in S3 with DynamoDB locking, versioning enabled, and bucket policies restricting access.

See [`terraform/README.md`](terraform/README.md) for the full proposed module structure, dependency graph, deployment workflow, and operational practices.

---

## CI/CD Pipeline

### What Was Implemented

The current GitHub Actions workflow (`.github/workflows/ci.yml`) covers the foundational CI stages: lint (`ruff check` + `ruff format --check`), unit tests (`pytest` with JUnit artifact upload), Docker image build, and OpenAPI spec generation. Lint and tests run in parallel. Build and OpenAPI are gated on both passing.

### Full Production Pipeline

The implemented CI is the first stage of a broader pipeline. Below is the full flow from developer machine to production:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ DEVELOPER MACHINE                                                       │
│                                                                         │
│  pre-commit hooks (ruff check, ruff format)                             │
│  Same tools as CI but gives instant local feedback.                     │
│  CI is the enforcer; hooks are a convenience.                           │
│  Developers run: pre-commit install (once after clone)                  │
│                                                                         │
│  git push / PR ─────────────────────────────────────────────┐           │
└─────────────────────────────────────────────────────────────┼───────────┘
                                                              │
                                                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ CI PIPELINE (GitHub Actions)                                            │
│                                                                         │
│  ┌──────────────────────┐                                               │
│  │ 1. Lint              │                                               │
│  │    ruff check + fmt  │                                               │
│  └──────────┬───────────┘                                               │
│             │                                                           │
│             ▼                                                           │
│  ┌──────────────────────┐    ┌──────────────────────────┐               │
│  │ 2. Unit Tests        │    │ 3. Security Scans        │               │
│  │    pytest --cov      │    │    CodeQL (SAST)         │               │
│  │    coverage report   │    │    pip-audit (deps)      │               │
│  │    to PR comment     │    │                          │               │
│  └──────────┬───────────┘    └─────────────┬────────────┘               │
│             │                              │                            │
│             └──────────┬───────────────────┘                            │
│                        ▼                                                │
│  ┌──────────────────────────┐                                           │
│  │ 4. Build Docker Image    │                                           │
│  └──────────┬───────────────┘                                           │
│             │                                                           │
│             ▼                                                           │
│  ┌──────────────────────┐    ┌──────────────────────────┐               │
│  │ 5. Integration Tests │    │ 6. Container Scan        │               │
│  │    Postgres + app    │    │    Trivy (CVEs)          │               │
│  │    tests_smoke/      │    │    fail on critical      │               │
│  └──────────┬───────────┘    └─────────────┬────────────┘               │
│             │                              │                            │
│             └──────────┬───────────────────┘                            │
│                        ▼                                                │
│  ┌──────────────────────────────────────────┐                           │
│  │ 7. Push to ECR (only if 1-6 all pass)    │                           │
│  │    tag: git SHA + semver                 │                           │
│  └──────────┬───────────────────────────────┘                           │
│             │                                                           │
│             ▼                                                           │
│  ┌──────────────────────────────────────────┐                           │
│  │ 8. Update GitOps Repo                    │                           │
│  │    image tag in Helm values / Kustomize  │                           │
│  └──────────┬───────────────────────────────┘                           │
└─────────────┼───────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ CD PIPELINE (ArgoCD)                                                    │
│                                                                         │
│  ┌──────────────────────────────────────────┐                           │
│  │ 9. Auto-sync to Staging                  │                           │
│  │    health checks validate deployment     │                           │
│  └──────────┬───────────────────────────────┘                           │
│             │                                                           │
│             ▼                                                           │
│  ┌──────────────────────────────────────────┐                           │
│  │ 10. Manual Approval Gate                 │                           │
│  └──────────┬───────────────────────────────┘                           │
│             │                                                           │
│             ▼                                                           │
│  ┌──────────────────────────────────────────┐                           │
│  │ 11. Production Deploy (blue/green)       │                           │
│  │     deploy to green, health check,       │                           │
│  │     switch traffic. If fail, stay on     │                           │
│  │     blue (instant rollback).             │                           │
│  └──────────────────────────────────────────┘                           │
│                                                                         │
│  Rollback: revert image tag in GitOps repo.                             │
│  ArgoCD syncs previous version. Auditable and reversible.               │
└─────────────────────────────────────────────────────────────────────────┘
```

### Branch Protection

GitHub branch protection rules enforce the workflow: require CI to pass before merge, require at least one PR review approval, prevent direct pushes to main, and require branches to be up-to-date with main before merging (prevents two PRs that pass CI independently but break when combined).

### Code Coverage

Coverage is measured with `pytest --cov=src/chatty --cov-report=xml`. A GitHub Action posts the coverage summary as a PR comment. A minimum threshold is enforced in CI. The specific number matters less than the trend: coverage should never silently degrade.

### Continuous Delivery, Not Continuous Deployment

Staging receives every merge automatically. Production requires a manual approval gate. This gives the team confidence that what's running in staging has been validated before it reaches users.

---

## Auth/AuthZ Approach

### Authentication (AuthN)

For identity verification, I would use **Keycloak** as the identity provider. Keycloak is open-source, self-hosted, and handles user registration, login, token issuance, and SSO. Its **realm** and **group** features provide multi-tenancy, allowing different teams or organizations to have isolated user pools while sharing the same Chatty infrastructure.

The flow:

1. Client authenticates with Keycloak (login, OAuth2, SSO)
2. Keycloak issues a JWT
3. Client sends the JWT on every API call via `Authorization: Bearer <token>`
4. FastAPI validates the token signature and expiration using Keycloak's JWKS (JSON Web Key Set) endpoint. No call to Keycloak on every request.

For **Socket.IO**, authentication happens once during the WebSocket handshake. The client passes the JWT in the `auth` object when connecting. The server validates it in the `connect` event handler. If the token is invalid or expired, the connection is rejected before any events are processed.

For **service-to-service** communication (e.g., another internal service calling the Chatty API), machine-to-machine tokens via the OAuth2 Client Credentials flow would be used instead of user JWTs.

### Authorization (AuthZ)

Authorization is role-based, built on top of the existing `chatroom_participant` table. The participant model would be extended with a `role` field:

- **owner**: can manage participants, delete the chatroom, delete any message
- **member**: can send messages, read messages
- **read-only**: can read messages only

In FastAPI, authorization checks would be implemented as **dependencies** injected into route handlers. For example, a `require_chatroom_member` dependency checks if the authenticated user exists in the `chatroom_participant` table for the target chatroom. This keeps authorization logic reusable and separate from business logic.

This example uses Keycloak, but any standards-compliant OIDC provider (Auth0, AWS Cognito, Okta, etc.) would work with the same approach since the integration relies on standard JWT validation and JWKS endpoints.

---

## Exposing Service to Front-End

### Request Path

```
┌─────────────────────────────────────────────────────────────────────────┐
│ CLIENT (Browser / Mobile)                                               │
│                                                                         │
│  REST:      POST /messages, GET /users, etc.                            │
│  WebSocket: Socket.IO for real-time messaging                           │
│                                                                         │
│  https://api.chatty.example.com                                         │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ DNS (Route 53)                                                          │
│                                                                         │
│  api-dev.chatty.example.com     → dev API Gateway                       │
│  api-staging.chatty.example.com → staging API Gateway                   │
│  api.chatty.example.com         → production API Gateway                │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ API GATEWAY (AWS API Gateway)                                           │
│                                                                         │
│  Rate limiting per client / API key                                     │
│  Request throttling                                                     │
│  API key management for service-to-service consumers                    │
│  Usage plans and quotas                                                 │
│  WAF integration for DDoS protection                                    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ALB (Application Load Balancer)                                         │
│                                                                         │
│  TLS termination (certificates managed by ACM)                          │
│  HTTPS on port 443, HTTP 80 redirects to HTTPS                          │
│  HSTS headers (browser remembers to always use HTTPS)                   │
│  WebSocket support for Socket.IO connections                            │
│  Sticky sessions: keeps a Socket.IO client routed to the                │
│    same pod for the lifetime of the connection (cookie-based)           │
│  Health checks against /health endpoint                                 │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ EKS CLUSTER                                                             │
│                                                                         │
│  Ingress Controller (ALB Ingress Controller)                            │
│    routes by hostname and path to Kubernetes services                   │
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  Chatty Pod 1  │  │  Chatty Pod 2  │  │  Chatty Pod N  │            │
│  │  FastAPI +     │  │  FastAPI +     │  │  FastAPI +     │            │
│  │  Socket.IO     │  │  Socket.IO     │  │  Socket.IO     │            │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘            │
│          │                   │                   │                      │
│          └───────────────────┼───────────────────┘                      │
│                              ▼                                          │
│                    ┌──────────────────┐                                  │
│                    │  Redis Adapter   │                                  │
│                    │  (pub/sub)       │                                  │
│                    └──────────────────┘                                  │
│  Socket.IO uses Redis as a message broker between pods.                 │
│  When Pod 1 emits an event to a chatroom, Redis fans it                 │
│  out to Pod 2 and Pod N so all connected clients receive it.            │
│  Sticky sessions keep individual connections stable.                    │
│  Redis handles cross-pod coordination.                                  │
│                                                                         │
│  CORS: CORS_ALLOWED_ORIGINS set to the front-end domain(s)             │
│  Internal traffic between pods and RDS stays in private subnets         │
└─────────────────────────────────────────────────────────────────────────┘
```

CORS is already implemented in the application via the `CORS_ALLOWED_ORIGINS` environment variable. In production, this would be set to the specific front-end domain(s) instead of `*`.

For local development, docker-compose exposes port 8000 directly, bypassing all production networking layers. This keeps the developer experience simple while the production path handles TLS, rate limiting, and load balancing.

---

## Auto Scaling and Load Testing

Chatty needs to handle variable traffic, from quiet periods to spikes when many users are active in chatrooms. The Kubernetes resources below define how the application scales, what resources each pod gets, and what guardrails prevent one workload from consuming the entire cluster.

### Pod Resources

```yaml
# k8s/deployment.yaml (relevant section)
containers:
  - name: chatty
    resources:
      requests:
        cpu: 250m
        memory: 256Mi
      limits:
        cpu: 1000m
        memory: 512Mi
```

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: chatty-hpa
  namespace: chatty
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chatty
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

Minimum 2 replicas for availability. Scale up aggressively (2 pods per minute) when CPU exceeds 70%. Scale down conservatively (1 pod every 2 minutes, 5-minute stabilization window) to avoid flapping. Cluster Autoscaler handles node-level scaling when pods can't be scheduled.

### Namespace Resource Controls

```yaml
# k8s/limit-range.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: chatty-limits
  namespace: chatty
spec:
  limits:
    - type: Container
      default:
        cpu: 500m
        memory: 256Mi
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      max:
        cpu: 2000m
        memory: 1Gi
```

```yaml
# k8s/resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: chatty-quota
  namespace: chatty
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 4Gi
    limits.cpu: "8"
    limits.memory: 8Gi
    pods: "20"
```

LimitRange sets defaults and ceilings per container. ResourceQuota caps total resources the namespace can consume across all pods.

### Load Testing

k6 or Locust simulates realistic traffic against staging: REST API calls for user/chatroom/message CRUD, and concurrent Socket.IO connections. The goal is to validate that HPA scales correctly under load and find the breaking point where latencies spike or errors appear.

### Database Connection Pooling

Connection pooling becomes critical as pods scale. Each Chatty pod opens a pool of connections to RDS. If you scale to 20 pods with a default pool size of 5, that's 100 connections to Postgres. Exhausting the RDS connection limit causes errors across the entire application. The mitigation is **RDS Proxy** or **PgBouncer** between the pods and RDS.

---

## Cloud Spend Management

The biggest cost lever for Chatty is environment differentiation. Dev and staging do not need to match production. The Terraform tfvars already separate environments, so the same module produces different infrastructure: spot instances and single-AZ RDS for non-production, on-demand nodes and multi-AZ RDS for production.

Beyond that, three practices keep spend visible and controlled:

1. **Shut down what's not in use.** Dev and staging don't need to run nights and weekends. Scheduled scaling (CronJob to scale EKS nodes to zero, stop RDS instances outside business hours) is the simplest way to cut non-production cost without any architectural change.

2. **Tag everything.** Every resource gets `environment`, `team`, and `service` tags. Without tags, cost reports are a single number. With tags, you can answer "how much does Chatty cost in staging vs. production" or "which team's workload drove the spike this month." Budget alerts at 50%, 80%, and 100% thresholds ensure no one is surprised at month-end.

3. **Commit to baseline, flex for the rest.** Production EKS nodes and RDS run 24/7 with predictable load. Savings Plans lock in a lower rate for that baseline. Everything above baseline (HPA scaling during traffic spikes, dev/staging with variable usage) stays on-demand. This avoids over-committing while still capturing savings on the workload that's always running.

---

## General SDLC

Chatty uses trunk-based development: short-lived feature branches off main, merged via PR within a day or two. No long-lived develop or release branches. This keeps the CI/CD pipeline described above simple since there's only one branch to build, test, and deploy.

New features are merged behind environment variable flags (e.g., `FEATURE_THREADED_REPLIES=false`). This separates deploying code from releasing it to users. A feature can sit in production, tested and ready, and get enabled by changing a config value. No redeploy needed. Env var flags are the right starting point for Chatty's size. A service like LaunchDarkly makes sense later if the team needs per-user targeting or percentage rollouts.

Dev, staging, and production run the same Docker image, same migrations, same config structure. Only the values change (via tfvars and env vars). This is already the case with the current docker-compose and Terraform setup. A bug that exists in production also exists in staging, which makes it reproducible before it reaches users.

---

## Additional Considerations

### Observability

Chatty already has structured JSON logging via structlog. The missing piece is a way to collect, store, and visualize that data across pods. The standard approach is three signals (logs, metrics, traces) collected separately and viewed together through Grafana:

- **Logs**: Chatty pods already emit structured JSON via structlog. A log collector (Promtail) ships them to Loki. Every log entry includes a request ID, so you can trace a single user's message from the HTTP handler through the database write to the Socket.IO emission across pods.
- **Metrics**: A FastAPI middleware (like `prometheus-fastapi-instrumentator`) exposes a `/metrics` endpoint on each pod. Prometheus scrapes it every 15-30 seconds and stores the time-series data. This is where request rates, latencies, and error counts come from.
- **Traces**: OpenTelemetry SDK instruments the app to capture the full lifecycle of a request across services. Tempo stores the trace data.

Grafana ties all three together. When you see a latency spike on a dashboard chart, you click into the specific time range, see the traces that caused it, and drill down into the logs for those requests. The diagram below shows how data flows from pods to dashboards:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ CHATTY PODS                                                             │
│                                                                         │
│  structlog (JSON) ──→ Promtail ──→ Loki (log storage)                  │
│  /metrics endpoint ──→ Prometheus (metric storage, scrapes every 15s)   │
│  OpenTelemetry SDK ──→ Tempo (trace storage)                            │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ GRAFANA (single dashboard, queries all three backends)                  │
│                                                                         │
│  API Health:                                                            │
│    request rate, p50/p95/p99 latency, error rate by endpoint            │
│                                                                         │
│  Socket.IO:                                                             │
│    active connections, join/leave rate, message delivery latency         │
│                                                                         │
│  Database:                                                              │
│    query duration, connection pool usage, active connections vs limit    │
│                                                                         │
│  Infrastructure:                                                        │
│    pod CPU/memory, node utilization, HPA scaling events                 │
└─────────────────────────────────────────────────────────────────────────┘
```

The existing `/health` endpoint would be split into separate liveness and readiness probes for Kubernetes pod lifecycle management.

### SLIs and SLOs for Chatty

Observability data is only useful if you define what "healthy" means. The table below sets specific targets for Chatty and ties each one to the metric that measures it:

| SLI | SLO | How it's measured |
|---|---|---|
| API latency (p99) | < 300ms | Prometheus histogram from FastAPI middleware |
| Error rate (5xx / total) | < 0.1% | Prometheus counter from middleware |
| Uptime | 99.9% | Health check probe success rate |
| Socket.IO delivery latency | < 500ms | Time from POST /messages to new_message event received |
| Message persistence success | 100% | Failed DB writes counter (should be zero) |

Alerting is based on SLO burn rate rather than static thresholds. A burn-rate alert fires when the service is consuming its error budget faster than expected (e.g., "at this rate, we'll breach the monthly SLO in 6 hours"). This avoids noisy alerts from brief spikes while catching sustained degradation early. Alerts route through Alertmanager to PagerDuty.

---

## AI Usage

### Where AI helped

- Quickly summarized the existing codebase structure and highlighted gaps / TODOs.
- Drafted first-pass boilerplate for supporting files such as the Dockerfile, docker-compose setup, GitHub Actions workflow, Alembic config, and OpenAPI generation script.
- Helped refine `README.md` and `RATIONALE.md` for structure, wording, and consistency.
- Accelerated iteration on implementation details, with outputs reviewed and adjusted before commit.

### What I owned

- Scoping and prioritization of what to implement versus what to leave as next steps.
- Architecture and tradeoff decisions for the final submission.
- Review, correction, and validation of all generated code and documentation.
