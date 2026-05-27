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
