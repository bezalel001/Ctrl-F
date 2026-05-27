# AGENTS.md

## Project Overview

Ctrl-F is a full-stack AI company knowledge assistant. Employees ask natural-language questions through a React/TypeScript web app and receive concise answers from a Python/FastAPI backend using retrieval-augmented generation over approved company documents.

The implementation must prioritize:

- Answers grounded in approved sources
- Clickable source citations
- Authentication and role-aware access control
- Follow-up questions with bounded conversation context
- Low-confidence warnings below the 85% threshold
- Safe fallback when no reliable answer is available
- Helpful/not helpful feedback collection
- Admin review of approved sources and feedback

Read `docs/IMPLEMENTATION_PLAN.md` before making architectural changes.

## Required Stack

Frontend:

- React
- TypeScript
- Vite

Backend:

- Python
- FastAPI
- Pydantic
- Uvicorn
- `uv` for dependency management, virtual environments, locking, and backend commands

Full-stack runtime:

- Docker
- Docker Compose

Data and AI:

- PostgreSQL for relational app data
- ChromaDB as the default vector store
- OpenAI `text-embedding-3-small` for embeddings
- OpenAI or Anthropic for answer generation, selected through configuration
- Local Ollama model only as a later optional provider

## Repository Conventions

Expected structure:

```text
Ctrl-F/
  AGENTS.md
  docker-compose.yml
  docker-compose.dev.yml
  .env.example
  backend/
    app/
    tests/
    Dockerfile
    .dockerignore
    pyproject.toml
    uv.lock
  frontend/
    src/
    Dockerfile
    .dockerignore
    package.json
  data/
    approved_sources/
    sample_documents/
  docs/
    IMPLEMENTATION_PLAN.md
```

Keep implementation changes aligned with this structure unless there is a clear reason to change it.

## Backend Commands

Run backend commands from `backend/`.

Install or sync dependencies:

```bash
uv sync
```

Start the FastAPI backend locally:

```bash
uv run uvicorn app.main:app --reload
```

Run backend tests:

```bash
uv run pytest
```

Run linting when configured:

```bash
uv run ruff check .
```

Run type checks when configured:

```bash
uv run mypy app
```

Add runtime dependencies:

```bash
uv add <package>
```

Add development dependencies:

```bash
uv add --dev <package>
```

After dependency changes, make sure `backend/uv.lock` is included in the user's manual commit.

## Docker Commands

Start the full-stack development environment:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Run backend tests inside Docker:

```bash
docker compose run --rm backend uv run pytest
```

Docker should manage the integrated full-stack environment. Direct `uv` commands are still preferred for fast backend-only development.

## Commit Workflow

The user wants to manually commit each implementation step.

- Do not create commits unless the user explicitly asks.
- Keep changes small and commit-sized.
- At the end of each step, explain what changed, why it was needed, how to verify it, and suggest a commit message.
- Prefer one logical implementation step per final response.
- If a step grows too large, stop at a stable checkpoint and suggest committing before continuing.

## Backend Implementation Rules

- Use FastAPI routers under `backend/app/api/routes/`.
- Use Pydantic models for request and response schemas.
- Keep business logic in services, not route handlers.
- Keep persistence details in storage or repository modules.
- Use dependency injection for authenticated user access.
- Make route responses stable and typed.
- Do not let unauthorized source chunks reach the LLM prompt.
- Do not answer from general model knowledge when approved sources are missing.

Core services should include:

- Authentication service
- Role/profile service
- Source management service
- Ingestion service
- Retrieval service
- Context service
- Answer generation service
- Confidence service
- Feedback service
- Audit service

## Frontend Implementation Rules

- Use React with TypeScript.
- Keep API calls in `frontend/src/api/`.
- Keep shared types in `frontend/src/types/`.
- Keep reusable UI in `frontend/src/components/`.
- Keep route-level screens in `frontend/src/pages/`.
- The first screen after login should be the actual chat experience, not a marketing page.
- The chat UI must show answer text, citations, confidence state, warnings, and feedback controls.
- Admin pages should support source management and feedback review.
- Ensure layouts work on desktop and mobile browsers.

## RAG and Safety Rules

The RAG pipeline must follow this order:

1. Authenticate the user.
2. Resolve role and department.
3. Retrieve only approved sources allowed for that user.
4. Build the LLM prompt only from authorized retrieved chunks.
5. Generate a concise answer.
6. Attach citations from retrieved source metadata.
7. Estimate confidence.
8. Warn when confidence is below 0.85.
9. Return a safe fallback when no reliable answer can be found.

Never:

- Send restricted chunks to the LLM for unauthorized users.
- Invent citations.
- Hide low-confidence answers as if they were certain.
- Use private conversations for model retraining.
- Commit real secrets, API keys, or private `.env` files.

Vector-store rule:

- Use ChromaDB first.
- Keep vector-store access behind a backend service interface so Pinecone or another vector store can be added later without changing API routes.

## Testing Expectations

Before finishing backend implementation work, run the most relevant tests:

```bash
cd backend
uv run pytest
```

Add or update tests for:

- Authentication and route protection
- Source validation
- Document chunking
- Retrieval filtering by role/department
- No-answer fallback
- Confidence warnings
- Feedback persistence
- Admin feedback review

For frontend implementation, add smoke tests or component tests once the frontend test framework is configured.

For full-stack changes, verify the Docker Compose environment starts successfully.

## Environment and Secrets

- Commit `.env.example`.
- Do not commit `.env`.
- Keep `JWT_SECRET`, API keys, database passwords, and LLM credentials out of git.
- Use environment variables for provider selection, database URL, vector store settings, and LLM configuration.

## Documentation Rules

Update documentation when implementation changes affect:

- Setup commands
- Docker services
- Environment variables
- API contracts
- RAG behavior
- Authentication or role behavior
- Demo flow

Primary planning reference:

- `docs/IMPLEMENTATION_PLAN.md`
