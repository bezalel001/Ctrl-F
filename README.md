# Ctrl-F

AI-powered company knowledge assistant with a React/TypeScript frontend and Python/FastAPI backend.

For the full setup, seeding, indexing, demo, feedback, audit, and evaluation sequence, see [docs/DEMO_FLOW.md](docs/DEMO_FLOW.md).

## Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Full-Stack Services

Copy `.env.example` to `.env` if you want to override local defaults.

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

The initial Docker stack includes:

- React/TypeScript frontend
- FastAPI backend
- PostgreSQL for app data
- ChromaDB for vector search

Approved sample source files live under `data/approved_sources/`. The backend mounts that folder at `/data/approved_sources` in Docker.

## Ollama Fallback

Provider mode defaults to `auto`. The backend uses OpenAI embeddings when `OPENAI_API_KEY` is set and falls back to Ollama embeddings when it is not.

For answer generation, `LLM_PROVIDER=auto` uses Anthropic first, then OpenAI, then Ollama.

Start the optional Ollama container with:

```bash
docker compose --profile ollama -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Then pull the fallback embedding model:

```bash
docker compose --profile ollama exec ollama ollama pull nomic-embed-text
```

For local answer generation fallback:

```bash
docker compose --profile ollama exec ollama ollama pull llama3.2
```

## Feedback Review

Answers can be rated helpful or not helpful in the chat UI. Demo users with `feedback:review`, such as `hr@example.com`, `manager@example.com`, and `admin@example.com`, see feedback summary data in the side panel.
