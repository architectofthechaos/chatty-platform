# Chatty

Chatty Backend. A real-time chat API built with FastAPI, Socket.IO, and SQLAlchemy.

## Project Structure

```
chatty/
├── .github/workflows/ci.yml        # CI pipeline (lint, test, build, OpenAPI)
├── app/
│   ├── Dockerfile                   # Python 3.11 + Poetry
│   ├── entrypoint.sh                # Runs migrations then starts server
│   ├── pyproject.toml               # Dependencies and tool config
│   ├── alembic.ini                  # Alembic migration config
│   ├── alembic/                     # Migration scripts
│   ├── scripts/generate_openapi.py  # Offline OpenAPI spec generation
│   ├── src/chatty/
│   │   ├── main.py                  # App entrypoint, Socket.IO setup
│   │   ├── core/                    # Database, logging, middleware
│   │   ├── models/                  # SQLAlchemy models
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   └── routers/                 # API route handlers
│   ├── tests/                       # Unit tests
│   └── tests_smoke/                 # Integration / smoke tests
├── terraform/                       # IaC proposal (see terraform/README.md)
├── docker-compose.yml               # Postgres + app, one-command setup
├── .env.example                     # Documented environment variables
├── RATIONALE.md                     # Decisions, trade-offs, AI usage
└── CONTRIBUTING.md                  # How to extend the app
```

## Prerequisites

- Docker and Docker Compose
- (Optional) Python 3.11 and Poetry 2.2.0 for local development outside Docker

## Quick Start

```bash
# Clone the repo and copy the example env file
cp .env.example .env

# Start the app and database
docker compose up --build

# API docs in your browser:
# http://localhost:8000/docs
```

The entrypoint automatically runs Alembic migrations before starting the server. No manual setup needed.

## Local Development (without Docker)

```bash
cd app
poetry install

# Run Alembic migrations (must be run from app/)
poetry run alembic upgrade head

# Start the dev server
poetry run python run.py

# API docs: http://localhost:8000/docs
```

By default, local dev uses SQLite. To use Postgres, set `DATABASE_URL` in your `.env` file.

## Testing

```bash
cd app

# Unit tests
poetry run pytest -W ignore

# REST API smoke test (requires running server)
poetry run pytest tests_smoke/smoke_test.py

# Socket.IO smoke test (requires running server)
poetry run pytest tests_smoke/smoke_socketio.py
```

## CI/CD

GitHub Actions runs on every push (`.github/workflows/ci.yml`):

- **Lint**: ruff check + format verification
- **Test**: pytest with JUnit artifact upload
- **Build**: Docker image build (gates on lint + test)
- **OpenAPI**: generates and uploads the OpenAPI spec as a build artifact

## Environment Variables

See `.env.example` for all available settings. Key variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./chatty.db` | Database connection string |
| `CORS_ALLOWED_ORIGINS` | `*` | Comma-separated allowed origins, or `*` for all |
| `APP_PORT` | `8000` | Server port |
| `LOG_LEVEL` | `DEBUG` | Logging level |

## OpenAPI Spec Generation

```bash
cd app
poetry run python scripts/generate_openapi.py openapi.json
```

This runs offline (no server needed) and is also generated automatically in CI.

---

## Operational Readiness: Status

### Completed

- **Dockerize**: Dockerfile with Poetry, docker-compose with Postgres 16 and health checks
- **GitHub Actions CI**: lint, test, build, and OpenAPI generation with proper job gating
- **OpenAPI spec generation**: offline script integrated into CI as a build artifact
- **CORS approach**: environment-driven (`CORS_ALLOWED_ORIGINS`), defaults to `*` in dev
- **Config / env var management**: all hardcoded values extracted to environment variables with `.env.example`
- **DB migration instrumentation**: Alembic initialized, initial migration generated, auto-runs on container startup via entrypoint

### Described in RATIONALE.md

- Infra as code approach (Terraform module structure for EKS, RDS, ALB. See also `terraform/README.md`)
- CI/CD full pipeline (dev → staging → prod promotion, blue/green deploys, automated rollback)
- Auth/authz approach (JWT, RBAC, Socket.IO token auth)
- Exposing service to front-end (ALB with WebSocket support, HTTPS termination, API gateway)
- Auto scaling and load testing (HPA in EKS, k6/Locust, scaling triggers)
- Cloud spend management (right-sizing, spot nodes, budget alerts)
- General SDLC (trunk-based branching, PR process, feature flags)

---

See [RATIONALE.md](RATIONALE.md) for detailed decisions, trade-offs, and AI usage documentation.

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to extend the app and contribute.
