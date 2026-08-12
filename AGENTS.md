# AGENTS.md

Development conventions for the Natural Language → SQL Analytics Assistant.

## Language & Runtime

- Backend: Python 3.11+ (FastAPI, SQLAlchemy, sqlglot, pydantic v2)
- Frontend: React + TypeScript + Vite
- Database: PostgreSQL 16 (Docker)

## Project Layout

```
backend/                  Python backend
  app/
    api/                  HTTP routes + dependency injection
    core/                 errors, logging, get_logger
    config/               pydantic-settings Settings
    database/             Database connection wrapper
    models/               domain models
    schemas/              pydantic request/response schemas
    services/             LLM, schema, SQL, execution, explanation, logging
  tests/                  pytest test suite
database/
  init/                   SQL schema + read-only role
  seed/                   deterministic seed data
frontend/                 React + Vite frontend
```

## Branch & Merge Workflow

Every feature is developed on its own branch:

```
main → feature/<name> → implement → test → commit → merge → push → delete
```

1. `git checkout main && git pull`
2. `git checkout -b feature/<short-name>`
3. Implement + test
4. `git add -A && git commit -m "feat: ..."`
5. `git checkout main && git merge --no-ff feature/<name>`
6. `git push origin main && git push origin --delete feature/<name>`
7. `git branch -d feature/<name>`

## Commands

### Run tests (from `backend/`)
```bash
python -m pytest tests/ -v
```

### Lint (if ruff is installed)
```bash
ruff check backend/ tests/
ruff format --check backend/ tests/
```

### Run backend (from `backend/`)
```bash
uvicorn app.main:app --reload
```

### Run full stack with Docker
```bash
docker compose up --build
```

## Code Style

- `from __future__ import annotations` at the top of every Python file
- Use `app.core.get_logger(__name__)` for logging
- Use `app.core.errors.AppError` subclasses for user-facing errors
- Dataclasses for domain models
- Type hints everywhere
- No inline comments unless absolutely necessary
- 4-space indentation, line length ≤ 100

## Testing

- All new features must include tests
- Tests run against in-memory SQLite built from `database/init/01_schema.sql`
- Live PostgreSQL tests are gated on `DATABASE_URL` / `READONLY_DATABASE_URL` env vars
- Security tests must verify: destructive ops rejected, multi-statement rejected, unauthorized tables rejected, error messages never leak SQL or table names

## Security

- Never commit secrets. `.env` is git-ignored; `.env.example` has placeholders only.
- All SQL must be validated before execution (AST-based via sqlglot).
- Error messages must never echo raw SQL or sensitive table/column names.
- Use read-only database credentials for execution.
