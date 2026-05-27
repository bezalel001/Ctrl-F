# Ctrl-F

AI-powered company knowledge assistant with a React/TypeScript frontend and Python/FastAPI backend.

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
