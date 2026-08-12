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

## Problem Statement

Business users often need answers from data but should not (and cannot) write SQL directly. Hand-built dashboards cover only predefined questions. This project lets users ask questions in plain language and receive trustworthy, safe, well-explained answers — without ever exposing the database to destructive queries or privileged credentials.

---

## Features

| Feature | Status |
| --- | --- |
| Dynamic schema discovery (tables, columns, types, PKs/FKs) | Implemented |
| Relevant schema selection | Implemented |
| LLM SQL generation (provider-agnostic) | Implemented |
| AST-based SQL validation & guardrails | Implemented |
| Read-only execution (dedicated DB role, timeout, row limits) | Implemented |
| Result processing | Implemented |
| Natural-language result explanation | Implemented |
| Error handling & structured query logging | Implemented |
| Analytics chat frontend | Implemented |
| Docker (db + backend + frontend) | Implemented |
| Test suite (success / failure / security) | Implemented |
| Query repair loop | Optional / stretch |
| Chart generation | Optional / stretch |
| Query history / saved questions | Optional / stretch |

---

## Core Workflow

1. **Schema discovery** — introspects the live database (tables, columns, types, primary keys, foreign keys).
2. **Relevant schema selection** — picks the tables/columns that matter for the user's question.
3. **SQL generation** — the LLM writes SQL limited to the authorized schema and permitted operations.
4. **Validation** — every query is parsed to an AST (via `sqlglot`) and checked for destructive/malformed/multiple statements and unauthorized tables.
5. **Read-only execution** — validated SQL runs through a dedicated `SELECT`-only PostgreSQL role with timeout and row limits.
6. **Result processing** — rows are normalized into a structured, JSON-safe format.
7. **Explanation** — the LLM summarizes results grounded strictly in the returned data.

---

## Technology Stack

- **Backend:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy, `sqlglot` (SQL AST validation), `httpx` (LLM calls), uvicorn
- **Database:** PostgreSQL 16 (Docker), dedicated read-only execution role
- **LLM:** Provider-agnostic abstraction; OpenAI-compatible HTTP client + a mock provider for tests/demos
- **Frontend:** React + TypeScript + Vite
- **Testing:** pytest
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
│   │   ├── api/            # HTTP routes
│   │   ├── core/           # errors, logging
│   │   ├── config/         # settings
│   │   ├── database/       # connection + DB init helpers
│   │   ├── models/         # domain models
│   │   ├── schemas/        # pydantic request/response
│   │   └── services/
│   │       ├── llm/        # LLM abstraction
│   │       ├── schema/     # discovery + relevance
│   │       ├── sql/        # generation + validation
│   │       ├── execution/  # read-only execution
│   │       ├── explanation/ # result explanation
│   │       └── logging/    # query logging
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/               # React + Vite
├── database/
│   ├── init/               # postgres init (schema, seed, read-only role)
│   ├── migrations/
│   └── seed/
├── docs/
├── scripts/
└── docker-compose.yml
```

---

## Setup

### Prerequisites
- Python 3.11+
- Node 18+
- Docker + Docker Compose

### 1. Configure environment

```bash
cp .env.example .env
# edit .env with real values (see Environment Variables below)
```

### 2. Start the database

```bash
docker compose up -d db
```

This creates the schema, seed data, and the read-only `nlsql_readonly` role automatically.

### 3. Run the backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate       # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## Environment Variables

See `.env.example`. Key variables:

```text
DATABASE_URL                 owner/read role used for schema discovery
READONLY_DATABASE_URL        read-only role used to execute approved queries
LLM_PROVIDER                 mock | openai
LLM_API_KEY                  (empty → uses MockProvider)
LLM_BASE_URL / LLM_MODEL
QUERY_TIMEOUT_SECONDS
MAX_RESULT_ROWS
MAX_REPAIR_ATTEMPTS
```

---

## Docker Setup

```bash
docker compose up --build
```

Services: `db` (PostgreSQL), `backend` (FastAPI on :8000), `frontend` (Vite on :5173).

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

1. Prompt rules (system instructions + schema boundary).
2. AST-based SQL validation (`sqlglot`) — rejects destructive/multi-statement/unauthorized queries.
3. Allowed-schema boundary — only authorized tables are exposed.
4. Dedicated **read-only** PostgreSQL role for execution.
5. Query limits — timeout and max result rows.
6. No secrets in code/docs; all in environment variables (never committed).

---

## Testing

```bash
cd backend
pytest
```

Covers successful queries, failure cases (invalid SQL, unknown tables), and security cases (DELETE/DROP/UPDATE/INSERT/multi-statement are rejected).

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
