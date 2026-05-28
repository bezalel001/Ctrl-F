# Ctrl-F Backend

Python/FastAPI backend for the Ctrl-F company knowledge assistant.

## Setup

```bash
uv sync
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

The API documentation is available at `http://127.0.0.1:8000/docs`.

## Test

```bash
uv run pytest
```

## Demo Authentication

The prototype uses local demo users until a real identity provider is added.

All demo users use password `demo`.

| Email | Role | Department |
| --- | --- | --- |
| `employee@example.com` | employee | People Operations |
| `intern@example.com` | intern | Engineering |
| `manager@example.com` | manager | Engineering |
| `hr@example.com` | hr | Human Resources |
| `admin@example.com` | admin | IT |

Login endpoint:

```text
POST /api/auth/login
```

Current user endpoint:

```text
GET /api/auth/me
```

## Source Registry

Knowledge owners and admins can manage approved source metadata through protected source endpoints.

Required permission:

```text
sources:manage
```

Endpoints:

```text
GET /api/sources
POST /api/sources
GET /api/sources/{source_id}
PATCH /api/sources/{source_id}
DELETE /api/sources/{source_id}
POST /api/sources/{source_id}/index
```

Source locations must use an approved URL scheme or live under `data/approved_sources/`.

The current indexing prototype supports local Markdown and text files. It chunks approved files, creates embeddings, and stores vectors in ChromaDB with source access metadata.

Embedding provider behavior:

- `EMBEDDING_PROVIDER=auto` uses OpenAI when `OPENAI_API_KEY` is set.
- If no OpenAI key is available, it falls back to Ollama at `OLLAMA_BASE_URL`.
- `OLLAMA_EMBEDDING_MODEL` defaults to `nomic-embed-text`.

For local Ollama fallback, pull the embedding model first:

```bash
ollama pull nomic-embed-text
```
