# Contributing

## Getting Started

```bash
git clone <repo-url>
cd chatty
cp .env.example .env
docker compose up --build
```

The app is ready when you see `Uvicorn running on 0.0.0.0:8000`. Open `http://localhost:8000/docs` to verify.

## Project Structure

```
app/src/chatty/
  core/         # Database connection, logging, middleware
  models/       # SQLAlchemy models (one file per table)
  schemas/      # Pydantic request/response schemas (mirrors models/)
  routers/      # API route handlers (one file per resource)
  main.py       # App setup, CORS, router registration, Socket.IO events
```

Each resource (users, chatrooms, messages, chatroom_participants) follows the same pattern: a model, a schema, and a router.

## Adding a New Feature

Example: adding a new API endpoint for reactions.

1. **Model**: Create `app/src/chatty/models/reaction.py` with a SQLAlchemy model. Follow the pattern in `models/message.py`.

2. **Migration**: Make sure docker compose is running (Alembic needs the database to compare against), then from the `app/` directory:
   ```bash
   poetry run alembic revision --autogenerate -m "add reactions table"
   ```
   Review the generated file in `app/alembic/versions/`. Alembic auto-detects changes but doesn't always get it right - check that the upgrade and downgrade functions match what you expect.

3. **Schema**: Create `app/src/chatty/schemas/reaction.py` with Pydantic models for the request body and response. See `schemas/message.py` for the pattern.

4. **Router**: Create `app/src/chatty/routers/reactions.py`. Define your endpoints here. See `routers/messages.py` for the pattern.

5. **Register**: Add the router in `app/src/chatty/main.py`:
   ```python
   from chatty.routers import reactions
   app.include_router(reactions.router, prefix="/reactions", tags=["reactions"])
   ```

6. **Test**: Add tests in `app/tests/test_reactions.py`. See `tests/test_chatrooms.py` for the pattern.

7. **Run and verify**:
   ```bash
   docker compose up --build
   ```
   The migration runs automatically on startup. Check `http://localhost:8000/docs` to see your new endpoints.

## Running Tests

```bash
# Run all tests
docker compose exec app poetry run pytest

# Run a specific test file
docker compose exec app poetry run pytest tests/test_chatrooms.py

# Run with verbose output
docker compose exec app poetry run pytest -v
```

## Code Style

Linting and formatting are enforced by `ruff` (config in `pyproject.toml`). Install pre-commit hooks after cloning so issues are caught before you push:

```bash
pre-commit install
```

CI will reject PRs that fail lint or tests.

## PR Checklist

Before opening a PR, verify:

- [ ] `docker compose up --build` starts without errors
- [ ] New migration is reviewed and committed
- [ ] Tests pass: `docker compose exec app poetry run pytest`
- [ ] New endpoints appear correctly in Swagger at `/docs`
- [ ] No hardcoded config values (use environment variables)

## Branching

Trunk-based development. Create a short-lived feature branch off `main`, merge back via PR with at least one review. CI must pass before merge.
