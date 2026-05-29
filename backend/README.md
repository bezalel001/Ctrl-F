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

## Chat

The chat endpoint retrieves authorized Chroma chunks, generates a grounded answer, returns source citations, and warns when confidence is below 85%. If retrieval confidence is below the reliable-answer threshold, it returns the safe fallback without calling the LLM. It stores each user's conversations and loads the recent bounded message history when `conversation_id` is provided for follow-up questions.

```text
POST /api/chat
```

Conversation history is used only to interpret follow-up wording. Approved retrieved source chunks remain the only grounding context for answer content.

Fallback responses include suggested contacts based on the retrieved source owner when available, or the user's department when no reliable source is available.

LLM provider behavior:

- `LLM_PROVIDER=auto` uses Anthropic when `ANTHROPIC_API_KEY` is set.
- If Anthropic is unavailable, it uses OpenAI when `OPENAI_API_KEY` is set.
- If neither cloud key is available, it falls back to Ollama at `OLLAMA_BASE_URL`.

For local Ollama chat fallback, pull the chat model first:

```bash
ollama pull llama3.2
```

## Feedback

Employees can rate generated answers for later review.

```text
POST /api/feedback
```

Reviewers with `feedback:review` can inspect feedback and summary counts.

```text
GET /api/admin/feedback
GET /api/admin/feedback/stats
```

Both admin feedback endpoints support optional filters:

- `rating=helpful|not_helpful`
- `user_id=<user-id>`
- `min_confidence=0.0..1.0`
- `max_confidence=0.0..1.0`
- `source_id=<source-id>`
- `limit=1..200`
