# Ctrl-F

AI-powered company knowledge assistant with a React/TypeScript frontend and Python/FastAPI backend.

## Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

## Full-Stack Services

Copy `.env.example` to `.env` if you want to override local defaults.

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

The initial Docker stack includes:

- FastAPI backend
- PostgreSQL for app data
- ChromaDB for vector search

The frontend service will be added after the React/TypeScript app is scaffolded.
