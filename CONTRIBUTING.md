# Contributing

## Adding a New Feature (e.g., a new API endpoint)

1. Create or update the SQLAlchemy model in `app/src/chatty/models/`
2. Generate an Alembic migration from `app/`:
   ```bash
   poetry run alembic revision --autogenerate -m "describe your change"
   ```
3. Review the generated migration file in `app/alembic/versions/`
4. Add Pydantic request/response schemas in `app/src/chatty/schemas/`
5. Create a router in `app/src/chatty/routers/`
6. Register the router in `app/src/chatty/main.py`
7. Add tests in `app/tests/`
8. Run locally:
   ```bash
   docker compose up --build
   ```

## Code Style

- Linting and formatting enforced by `ruff` (config in `pyproject.toml`)
- Install pre-commit hooks after cloning:
  ```bash
  pre-commit install
  ```
- CI will reject PRs that fail lint or tests

## Branching

Trunk-based development. Short-lived feature branches off `main`, merged via PR with at least one review. CI must pass before merge.
