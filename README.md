# Ctrl-F

Ctrl-F is a full-stack AI company knowledge assistant. Employees ask natural-language questions in a React/TypeScript chat UI and receive concise answers from a Python/FastAPI backend using retrieval-augmented generation over approved company documents.

The prototype is built to demonstrate the core safety and trust behavior expected from an internal knowledge assistant:

- Answers grounded in approved source documents
- Clickable source citations
- Authentication with role and department-aware access control
- Follow-up questions with bounded conversation context
- Low-confidence warnings below the 85% threshold
- Safe fallback when no reliable source is available
- Helpful/not helpful feedback collection
- Admin source management, feedback review, and audit logs

For a step-by-step demo script, see [docs/DEMO_FLOW.md](docs/DEMO_FLOW.md).

## Stack

Frontend:

- React
- TypeScript
- Vite

Backend:

- Python
- FastAPI
- Pydantic
- SQLModel
- Uvicorn
- `uv` for Python dependency management

Runtime and data:

- Docker Compose for the full-stack environment
- PostgreSQL for relational app data
- ChromaDB as the vector store
- OpenAI `text-embedding-3-small` for embeddings when `OPENAI_API_KEY` is available
- Anthropic, OpenAI, or Ollama for answer generation, selected by configuration

## Repository Layout

```text
Ctrl-F/
  backend/                 Python/FastAPI backend
  frontend/                React/TypeScript frontend
  data/
    approved_sources/      Fictitious sample Markdown sources
    evaluation/            RAG evaluation cases
  docs/
    DEMO_FLOW.md           End-to-end setup and demo flow
    IMPLEMENTATION_PLAN.md Architecture and implementation plan
  docker-compose.yml
  docker-compose.dev.yml
  .env.example
```

## Prerequisites

Install:

- Docker Desktop or another Docker Compose-compatible runtime
- `uv`
- Node.js 22+
- npm

Optional:

- OpenAI API key for embeddings and OpenAI chat
- Anthropic API key for Anthropic chat
- Ollama for local fallback models

## Environment

Copy the example file if you want to customize local settings:

```bash
cp .env.example .env
```

Important variables:

```text
DATABASE_URL=postgresql+psycopg://ctrlf:ctrlf@postgres:5432/ctrlf
VECTOR_STORE_PROVIDER=chroma
CHROMA_HOST=chroma
CHROMA_INTERNAL_PORT=8000
EMBEDDING_PROVIDER=auto
OPENAI_API_KEY=
LLM_PROVIDER=auto
ANTHROPIC_API_KEY=
OLLAMA_BASE_URL=http://ollama:11434
SEED_DEMO_SOURCES=true
JWT_SECRET=change-me
```

Provider behavior:

- `EMBEDDING_PROVIDER=auto` uses OpenAI embeddings when `OPENAI_API_KEY` is set, otherwise Ollama.
- `LLM_PROVIDER=auto` uses Anthropic first, then OpenAI, then Ollama.
- `SEED_DEMO_SOURCES=true` registers the fictitious demo source records on backend startup in the Docker development stack. It does not index them.
- Do not commit `.env` or real API keys.

## Run With Docker

From the repository root:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Open:

- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`
- ChromaDB: `http://localhost:8001`

Stop the stack:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

## Optional Ollama Fallback

Start the stack with the Ollama profile:

```bash
docker compose --profile ollama -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Pull the local embedding and chat models:

```bash
docker compose --profile ollama exec ollama ollama pull nomic-embed-text
docker compose --profile ollama exec ollama ollama pull llama3.2
```

## Seed And Index Sample Sources

Markdown files in `data/approved_sources/` are sample documents only. They are fictitious and safe to commit. Real private company documents should not be committed unless the repository is approved to store them.

The files alone are not enough for chat. Source records must be registered in Postgres, then indexed into ChromaDB.

In the Docker development stack, the backend automatically registers the demo source records on startup with `SEED_DEMO_SOURCES=true`. This makes all five demo records appear in the admin Source Registry, but it does not index them.

If you disable auto-registration with `SEED_DEMO_SOURCES=false`, or if you are running the backend outside Docker, register the source records manually:

```bash
docker compose exec backend uv run python -m app.scripts.seed_demo_sources
```

1. Sign in as admin:

```text
admin@example.com
password: demo
```

2. In the Source Registry panel, click **Index** for each approved source you want available for chat.

Indexing loads the Markdown file, chunks it, creates embeddings, and stores searchable vectors in ChromaDB with role and department metadata.

Current ingestion supports local Markdown/text-style source files. PDF ingestion is not implemented yet.

## Local Prototype Accounts

The local login screen uses fixed prototype accounts so you can test role and department access without configuring an identity provider. All prototype accounts use password `demo`.

The email selects the role and department. After sign-in, the app displays a realistic generated name for that role instead of generic demo labels.

| Email | Role | Department | Notable access |
| --- | --- | --- | --- |
| `employee@example.com` | employee | People Operations | Chat |
| `intern@example.com` | intern | Engineering | Chat |
| `manager@example.com` | manager | Engineering | Chat, feedback review |
| `hr@example.com` | hr | Human Resources | Chat, feedback review |
| `admin@example.com` | admin | IT | Source management, feedback review, audit logs |

## Demo Questions

After seeding and indexing sources, try:

```text
How many paid vacation days do full-time employees receive?
What should I do if my company laptop is lost or stolen?
What training does a new hire need to finish?
How soon does it need to be completed?
Which engineering changes require two reviewers?
What is the cafeteria menu next Friday?
```

Expected behavior:

- Relevant answers include source citations.
- Follow-up questions use conversation context.
- Out-of-scope questions return the safe fallback.
- Restricted source content is not exposed to unauthorized users.

## Local Development Without Docker

Backend:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Direct local backend development defaults to SQLite unless `DATABASE_URL` is set. The Docker stack uses PostgreSQL.

## Backend Commands

Run from `backend/`:

```bash
uv sync
uv run pytest
uv run python -m compileall app tests
uv run python -m app.scripts.seed_demo_sources
uv run python -m app.scripts.run_evaluation --help
```

Run the evaluation against a running, seeded, indexed backend:

```bash
uv run python -m app.scripts.run_evaluation
```

The evaluation runner checks response time, expected citations, fallback behavior, low-confidence warnings, and restricted-source exposure.

## Frontend Commands

Run from `frontend/`:

```bash
npm install
npm run dev
npm run build
npm run smoke
```

`npm run smoke` builds the production bundle and checks that the main chat, source-management, and feedback-review UI surfaces are present.

## API Surface

Main endpoints:

```text
GET  /health
POST /api/auth/login
GET  /api/auth/me
POST /api/chat
POST /api/feedback
GET  /api/admin/feedback
GET  /api/admin/feedback/stats
GET  /api/admin/audit
GET  /api/sources
POST /api/sources
GET  /api/sources/{source_id}
PATCH /api/sources/{source_id}
DELETE /api/sources/{source_id}
POST /api/sources/{source_id}/index
```

The generated OpenAPI docs are available at `http://localhost:8000/docs` when the backend is running.

## Troubleshooting

If chat always returns:

```text
I don't know based on the approved company sources available to me.
```

Check:

- Demo sources were seeded in the same environment you are running. Docker uses PostgreSQL, not the local SQLite file.
- Each source was indexed into ChromaDB.
- The logged-in user has access to the source role or department.
- The embedding provider is configured and reachable.
- ChromaDB is running.

If Docker build fails with BuildKit `input/output error`, check disk space:

```bash
df -h
docker system df
```

Docker builds need several GB of free space. Prefer freeing at least 15-20 GB before rebuilding.

Avoid `docker volume prune` unless you are okay losing local PostgreSQL and ChromaDB volumes.

## Documentation

- [docs/DEMO_FLOW.md](docs/DEMO_FLOW.md): end-to-end setup and demo flow
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md): project architecture and implementation plan
- [backend/README.md](backend/README.md): backend-specific commands and API notes
