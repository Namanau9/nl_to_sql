# Natural Language → SQL Analytics Assistant

An AI-powered analytics assistant that converts natural-language business questions into **safe, validated SQL**, executes them against a **read-only** relational database, and returns structured results with natural-language explanations.

```text
User Question
      ↓
Schema Discovery
      ↓
Relevant Schema Selection
      ↓
LLM SQL Generation
      ↓
SQL Validation & Guardrails
      ↓
Read-Only Query Execution
      ↓
Result Processing
      ↓
Natural Language Explanation
      ↓
Response to User
```

> Security is designed with **defense in depth**: prompt rules + AST-based SQL validation + allowed-schema boundary + a dedicated read-only database role + query limits. The LLM is never treated as a security boundary.

---

## Demo

Ask a question and get a SQL result with explanation:

```
User: What was our total revenue?
SQL:  select sum(quantity * unit_price) as total_revenue from public.order_items;
Result: $8,400,050.00
AI:   Your total revenue is $8,400,050.00.
```

<img width="600" alt="Chat interface preview" src="https://placehold.co/600x400/ffffff/cccccc?text=NL+to+SQL+Assistant+Interface" style="border: 1px solid #e5e7eb; border-radius: 8px;">

---

## Problem Statement

Business users often need answers from data but should not (and cannot) write SQL directly. Hand-built dashboards cover only predefined questions. This project lets users ask questions in plain language and receive trustworthy, safe, well-explained answers — without ever exposing the database to destructive queries or privileged credentials.

---

## Features

| Feature | Status |
| --- | --- |
| Dynamic schema discovery (tables, columns, types, PKs/FKs) | ✅ |
| Relevant schema selection (join-aware) | ✅ |
| LLM SQL generation (provider-agnostic) | ✅ |
| AST-based SQL validation & guardrails | ✅ |
| Read-only execution (dedicated DB role, timeout, row limits) | ✅ |
| Result processing | ✅ |
| Natural-language result explanation | ✅ |
| Error handling & structured query logging | ✅ |
| Analytics chat frontend (dark/light mode, sidebar, settings) | ✅ |
| Docker (db + backend + frontend) | ✅ |
| Test suite (success / failure / security) | ✅ |
| Query repair loop | ⏳ Optional |
| Chart generation | ⏳ Optional |
| Query history / saved questions | ⏳ Optional |

### Frontend Features

- **Chat interface** with message history and session management
- **Dark/light theme toggle** with persistent preference (`localStorage`)
- **Collapsible sidebar** for past conversations (desktop) / overlay (mobile)
- **SQL syntax highlighting** via `react-syntax-highlighter` with theme-aware colors
- **Settings modal** to switch LLM provider and model on the fly
- **Processing stages** shown inline with animated progress dots
- **Health status** indicator in the header
- **Auto-resizing textarea** with Shift+Enter for newlines

---

## Core Workflow

1. **Schema discovery** — introspects the live database (tables, columns, types, primary keys, foreign keys).
2. **Relevant schema selection** — picks the tables/columns that matter for the user's question, including join paths.
3. **SQL generation** — the LLM writes SQL limited to the authorized schema and permitted operations.
4. **Validation** — every query is parsed to an AST (via `sqlglot`) and checked for destructive/malformed/multiple statements and unauthorized tables.
5. **Read-only execution** — validated SQL runs through a dedicated `SELECT`-only PostgreSQL role with timeout and row limits.
6. **Result processing** — rows are normalized into a structured, JSON-safe format.
7. **Explanation** — the LLM summarizes results grounded strictly in the returned data.

---

## Technology Stack

- **Backend:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy, `sqlglot` (SQL AST validation), `httpx` (LLM calls), uvicorn
- **Frontend:** React 18 + TypeScript + Vite, Tailwind CSS, react-syntax-highlighter, lucide-react, clsx, tailwind-merge
- **Database:** PostgreSQL 16 (Docker), dedicated read-only execution role
- **LLM:** Provider-agnostic abstraction — **OpenRouter** (OpenAI-compatible HTTP) + a mock provider for tests/demos
- **Testing:** pytest (130 tests), 129 passing, 1 skipped (requires live PostgreSQL)
- **Deployment:** Docker + docker-compose

---

## Repository Structure

```text
.
├── README.md
├── SYSTEM_REQUIRMENTS.md
├── SECURITY.md
├── FEATURE_REQUIRMENT.md
├── SKILLS.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── backend/
│   ├── app/
│   │   ├── api/            # HTTP routes + dependency injection
│   │   ├── core/           # errors, logging, get_logger
│   │   ├── config/         # pydantic-settings Settings
│   │   ├── database/       # Database connection wrapper
│   │   ├── models/         # domain models
│   │   ├── schemas/        # pydantic request/response schemas
│   │   └── services/
│   │       ├── llm/        # LLM abstraction (OpenRouter + Mock)
│   │       ├── schema/     # discovery + relevance selection
│   │       ├── sql/        # generation + AST validation
│   │       ├── execution/  # read-only execution
│   │       ├── explanation/ # result explanation
│   │       └── logging/    # query logging
│   ├── tests/              # pytest test suite
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/               # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── hooks/          # Custom hooks (useTheme)
│   │   ├── lib/            # Utilities (cn)
│   │   └── types.ts        # TypeScript interfaces
│   ├── Dockerfile
│   ├── nginx.conf          # Production nginx config with reverse proxy
│   ├── tailwind.config.js
│   └── package.json
├── database/
│   ├── init/               # postgres init (schema, seed, read-only role)
│   └── seed/               # deterministic seed data
└── docker-compose.yml
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker + Docker Compose
- An OpenRouter API key (get one at [openrouter.ai](https://openrouter.ai))

---

### Quick Start (Docker)

```bash
# 1. Copy env template and add your keys
cp .env.example .env
# Edit .env: set LLM_API_KEY, POSTGRES_PASSWORD, READONLY_PASSWORD

# 2. Start everything
docker compose up --build

# 3. Open in browser
open http://localhost:5173
```

Services:
- **Frontend:** http://localhost:5173 (nginx serving React app)
- **Backend API:** http://localhost:8000 (FastAPI)
- **PostgreSQL:** localhost:5432
- **API proxy:** nginx forwards `/api/*` to backend automatically

---

### Manual Setup (without Docker)

#### 1. Configure environment

```bash
cp .env.example .env
# edit .env with real values
```

#### 2. Start the database

```bash
docker compose up -d db
```

This creates the schema, seed data, and the read-only `nlsql_readonly` role automatically.

#### 3. Run the backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate       # Windows
# or: source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | Main PostgreSQL connection (for schema discovery) |
| `READONLY_DATABASE_URL` | Yes | — | Read-only PostgreSQL connection (for query execution) |
| `POSTGRES_PASSWORD` | Yes | — | Password for `nlsql_app` user |
| `READONLY_PASSWORD` | Yes | — | Password for `nlsql_readonly` user |
| `LLM_PROVIDER` | No | `mock` | LLM provider: `openrouter` or `mock` |
| `LLM_API_KEY` | See below | — | OpenRouter API key (required if `LLM_PROVIDER=openrouter`) |
| `LLM_BASE_URL` | No | `https://openrouter.ai/api/v1` | LLM API base URL |
| `LLM_MODEL` | No | `google/gemini-2.0-flash-exp:free` | Model identifier |
| `LLM_TEMPERATURE` | No | `0.0` | LLM temperature (0 = deterministic) |
| `LLM_TIMEOUT_SECONDS` | No | `30` | LLM request timeout |
| `QUERY_TIMEOUT_SECONDS` | No | `10` | SQL execution timeout |
| `MAX_RESULT_ROWS` | No | `1000` | Maximum rows to return |
| `MAX_REPAIR_ATTEMPTS` | No | `2` | Max SQL repair loop attempts |
| `APP_ENV` | No | `development` | Application environment |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `CORS_ORIGINS` | No | `["http://localhost:5173"]` | CORS allowed origins |

**Note on `LLM_PROVIDER`:** Use `openrouter` for real LLM queries (requires `LLM_API_KEY`). Use `mock` for deterministic testing without an API key.

---

## API Reference

### `GET /api/health`

Health check with available schema tables.

```bash
curl http://localhost:8000/api/health
```

```json
{
  "status": "ok",
  "schema_tables": ["products", "customers", "orders", "order_items"]
}
```

### `POST /api/query`

Run a natural-language question through the full pipeline.

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What was our total revenue?"}'
```

Response (200):
```json
{
  "question": "What was our total revenue?",
  "sql": "select sum(quantity * unit_price) as total_revenue from public.order_items",
  "explanation": "Your total revenue is $8,400,050.00.",
  "results": {
    "columns": ["total_revenue"],
    "rows": [["8400050.00"]],
    "row_count": 1,
    "execution_ms": 42
  },
  "status": "success",
  "error": null,
  "execution_ms": 4190
}
```

**Security rejection** (422):
```json
{
  "detail": "The generated SQL was unsafe or invalid."
}
```

**LLM refusal** (502):
```json
{
  "detail": "The language model did not return a usable response."
}
```

---

## Example Questions

- How many customers do we have?
- What was our revenue last month?
- Which product sold the most?
- Show revenue by region.
- Which category generated the most revenue?
- Who are our top 10 customers?
- Show monthly revenue for 2026.

---

## Security Model

See `SECURITY.md`. Layered controls:

1. **Prompt rules** — system instructions + schema boundary.
2. **AST-based SQL validation** (`sqlglot`) — rejects destructive (`DELETE`, `DROP`, `UPDATE`, `INSERT`), multi-statement, and unauthorized-table queries.
3. **Allowed-schema boundary** — only tables from the relevance-selected schema are exposed to the LLM.
4. **Dedicated read-only role** — execution runs under `nlsql_readonly` (SELECT-only, no DDL/DML privileges).
5. **Query limits** — configurable timeout (`QUERY_TIMEOUT_SECONDS`) and max result rows (`MAX_RESULT_ROWS`).
6. **No secrets in code** — all credentials in environment variables; `.env` is git-ignored.

---

## Testing

```bash
cd backend
python -m pytest tests/ -v
```

Covers:
- Successful query execution with result verification
- Failure cases (invalid SQL, unknown tables, execution errors)
- Security cases: `DELETE`, `DROP`, `UPDATE`, `INSERT`, multi-statement, `SELECT INTO`, unauthorized tables, and error message sanitization (no SQL or table names leaked)

**129 tests pass, 1 skipped** (the skipped test requires a live PostgreSQL instance).

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Connection refused` on localhost:5173 | Run `docker compose up --build` from project root |
| `Connection refused` on localhost:8000 | Check backend container: `docker compose logs backend` |
| `LLM returned an empty or refused response` | The LLM refused a destructive query. Try a valid business question. |
| `The generated SQL was unsafe or invalid` | A destructive query was rejected by the SQL validator. |
| `Database not initialised` | Wait for PostgreSQL healthcheck to pass (`docker compose ps`) |
| Tests can't connect to DB | Tests use in-memory SQLite by default. Set `DATABASE_URL` for live PostgreSQL tests. |
| Frontend not loading styles | Clear browser cache; the `dist/` is rebuilt fresh in Docker |
| Dark theme reverts after refresh | Theme preference is stored in `localStorage`; ensure cookies are enabled |

---

## Known Limitations

- Requires a real LLM API key for fully open-ended natural-language questions; without one the mock provider is used (deterministic, for tests/demos).
- Explanation accuracy is bounded by the LLM and the returned data.
- Single, first-party database instance (one schema namespace).

---

## Future Improvements

- Query repair loop (bounded retries)
- Chart generation (line/bar/pie when appropriate)
- Query history / saved questions
- Role-based access control
- Multi-database / multi-tenant support
- Semantic business metrics layer
