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
