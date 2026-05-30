# Ctrl-F Demo Flow

This flow uses fictitious source documents from `data/approved_sources/`. Do not use real private company documents unless this repository is approved to store them.

## 1. Configure Environment

Copy the example environment file if you want local overrides:

```bash
cp .env.example .env
```

For cloud providers, set at least one answer-generation key:

```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

`LLM_PROVIDER=auto` tries Anthropic first, then OpenAI, then Ollama. `EMBEDDING_PROVIDER=auto` uses OpenAI embeddings when `OPENAI_API_KEY` is set and falls back to Ollama otherwise.

## 2. Start The Stack

Docker-managed full stack:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

The app will be available at:

- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`
- ChromaDB: `http://localhost:8001`

Optional Ollama fallback:

```bash
docker compose --profile ollama -f docker-compose.yml -f docker-compose.dev.yml up --build
docker compose --profile ollama exec ollama ollama pull nomic-embed-text
docker compose --profile ollama exec ollama ollama pull llama3.2
```

## 3. Seed Demo Sources

Register the fictitious sample documents as approved source records:

```bash
docker compose exec backend uv run python -m app.scripts.seed_demo_sources
```

For direct backend development:

```bash
cd backend
uv run python -m app.scripts.seed_demo_sources
```

The command is idempotent. Running it again skips existing source records.

## 4. Index Sources

Sign in as `admin@example.com` with password `demo`, then use the Source Registry panel to index each approved source.

You can also index through the API:

```text
POST /api/sources/{source_id}/index
```

Indexing reads the approved Markdown files, chunks them, creates embeddings, and stores vectors in ChromaDB.

## 5. Demo Chat

Sign in as a demo user:

| User | Purpose |
| --- | --- |
| `employee@example.com` | Standard employee access |
| `intern@example.com` | Intern access |
| `manager@example.com` | Manager and feedback review access |
| `hr@example.com` | HR and feedback review access |
| `admin@example.com` | Source, feedback, and audit admin |

Useful demo questions:

- `How many paid vacation days do full-time employees receive?`
- `What should I do if my company laptop is lost or stolen?`
- `What training does a new hire need to finish?`
- `How soon does it need to be completed?`
- `Which engineering changes require two reviewers?`
- `What is the cafeteria menu next Friday?`

Expected behavior:

- Answers should cite approved sources when relevant.
- Follow-up questions should keep conversation context.
- Low-confidence or outside-scope questions should return the safe fallback.
- Restricted engineering source content should not be exposed to unauthorized users.

## 6. Feedback And Audit

Use Helpful or Not helpful on assistant answers to create feedback records.

Users with `feedback:review` can review feedback in the side panel. Users with `audit:read` can inspect audit logs through:

```text
GET /api/admin/audit
```

## 7. Run Checks

Backend:

```bash
cd backend
uv run pytest
uv run python -m compileall app tests
```

Frontend:

```bash
cd frontend
npm run smoke
```

Evaluation against a running, seeded, indexed backend:

```bash
cd backend
uv run python -m app.scripts.run_evaluation
```

The evaluation runner checks response time, expected citations, fallback behavior, confidence warnings, and restricted-source exposure.
