# Ctrl-F Full-Stack Implementation Plan

## 1. Project Target

Ctrl-F is a web-based AI company knowledge assistant. Employees ask natural-language questions and receive concise answers grounded in approved company documents, with citations, confidence handling, role-aware access control, follow-up support, and feedback collection.

The first implementation should be a demonstrable RAG prototype that satisfies the documented core use cases:

- UC1: Ask question and receive answer
- UC2: Ask a follow-up question
- UC3: Ask a role-specific question
- UC4: Maintain approved knowledge sources
- UC5: Review feedback on answers
- SUC1: Authenticate user
- SUC2: Generate LLM answer with citation
- SUC3: Estimate confidence level
- SUC4: Validate source authorization
- SUC5: Record user feedback

## 2. Recommended Stack

The summary presentation already proposes React/TypeScript, FastAPI, a vector database, and either an API-hosted LLM or local Ollama model. The repo currently contains only a minimal Python backend stub, so the implementation should grow from that structure.

### Frontend

- React with TypeScript
- Vite for local development
- CSS modules or Tailwind CSS for styling
- React Router if multiple admin/chat routes are added
- Fetch or TanStack Query for API calls

### Backend

- FastAPI
- Pydantic models for request/response validation
- Uvicorn for development server
- `uv` for Python dependency management, virtual environment management, locking, and backend commands
- SQLAlchemy or SQLModel for relational data
- PostgreSQL for relational app data in local development and production-like Docker runs

### Full-Stack Runtime and Deployment

- Docker for containerizing the frontend, backend, database, and optional vector store services
- Docker Compose for local full-stack development and demos
- Separate backend `uv` workflow for fast Python-only development
- Environment variables managed through `.env` files, with committed `.env.example` templates
- Named Docker volumes for database and vector-store persistence

### AI and Retrieval

- ChromaDB as the default vector store for the prototype
- Embedding model:
  - Default: OpenAI `text-embedding-3-small`
  - Later option: local sentence-transformers if offline operation is needed
- LLM:
  - Default: configurable provider, either OpenAI or Anthropic
  - Later option: local model through Ollama
- RAG pipeline:
  - Document loading
  - Chunking
  - Metadata extraction
  - Embedding
  - Vector search with access filters
  - Prompt construction
  - Answer generation
  - Citation attachment
  - Confidence estimation

### Current Implementation Decisions

- Use local PostgreSQL for users, roles, conversations, messages, source registry, feedback, and audit logs.
- Use ChromaDB for document chunk embeddings and semantic retrieval.
- Use OpenAI embeddings with `text-embedding-3-small`.
- Keep answer generation provider-configurable through `LLM_PROVIDER=openai|anthropic`.
- Keep Pinecone as a future vector-store adapter option, not the default implementation.
- Build a `VectorStore` abstraction so Chroma can be replaced later without rewriting chat, ingestion, or retrieval routes.

## 3. Proposed Repository Structure

```text
Ctrl-F/
  docker-compose.yml
  docker-compose.dev.yml
  .env.example
  backend/
    app/
      main.py
      core/
        config.py
        security.py
        logging.py
      api/
        routes/
          auth.py
          chat.py
          feedback.py
          sources.py
          admin.py
      models/
        auth.py
        chat.py
        feedback.py
        source.py
        user.py
      services/
        auth_service.py
        role_service.py
        source_service.py
        ingestion_service.py
        retrieval_service.py
        context_service.py
        answer_service.py
        confidence_service.py
        feedback_service.py
        audit_service.py
      storage/
        database.py
        repositories.py
        vector_store.py
      tests/
        test_chat.py
        test_retrieval.py
        test_sources.py
        test_feedback.py
    Dockerfile
    .dockerignore
    pyproject.toml
    uv.lock
    README.md
  frontend/
    src/
      api/
        client.ts
        chat.ts
        feedback.ts
        sources.ts
      components/
        ChatWindow.tsx
        MessageList.tsx
        SourceList.tsx
        ConfidenceBadge.tsx
        FeedbackControls.tsx
        AdminSourceTable.tsx
      pages/
        ChatPage.tsx
        LoginPage.tsx
        AdminPage.tsx
        FeedbackReviewPage.tsx
      types/
        chat.ts
        source.ts
        feedback.ts
      App.tsx
      main.tsx
    Dockerfile
    .dockerignore
    package.json
    package-lock.json
  data/
    approved_sources/
    sample_documents/
  docs/
    IMPLEMENTATION_PLAN.md
```

## 4. Backend Components

### 4.0 Backend Package Management with uv

Use `uv` as the single source of truth for Python backend dependencies and commands.

Required setup:

- Keep backend dependencies in `backend/pyproject.toml`.
- Commit `backend/uv.lock`.
- Use `uv add` for runtime dependencies.
- Use `uv add --dev` for test, lint, and formatting tools.
- Run backend commands from the `backend/` directory with `uv run`.

Recommended backend dependency groups:

- Runtime: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy` or `sqlmodel`, `python-jose` or `pyjwt`, `passlib`, `chromadb`, document parsing libraries, embedding/LLM SDKs
- Development: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`

Recommended commands:

```bash
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
uv run ruff check .
uv run mypy app
```

The Docker backend image should also use `uv` to install locked dependencies so local and containerized runs stay aligned.

### 4.1 FastAPI Application Shell

Create a real FastAPI app in `backend/app/main.py`.

Required capabilities:

- Health endpoint: `GET /health`
- API prefix: `/api`
- CORS configured for local frontend development
- Central exception handling
- Structured response models
- Environment-based configuration

Acceptance criteria:

- Backend starts with `uv run uvicorn app.main:app --reload`
- `GET /health` returns status and app version
- OpenAPI docs are available at `/docs`

### 4.2 Authentication and Access Control

For the course prototype, start with simple local authentication and role metadata instead of a real identity provider.

Implementation:

- Mock login endpoint accepting predefined users
- Session token or JWT returned to frontend
- User profile contains:
  - user id
  - name
  - email
  - role
  - department
  - permissions
- Dependency guard for protected routes
- Role-based filters passed into retrieval

Example roles:

- employee
- intern
- manager
- hr
- it
- knowledge_owner
- compliance
- admin

Relevant requirements:

- Req07: verify identity through authentication
- Req08: tailor answers by department or role
- NfReq09: GDPR/privacy handling
- NfReq10: approved and authorized sources only

### 4.3 Source Management Service

This service manages the approved knowledge base.

Data fields for each source:

- id
- title
- description
- document type
- file path or URL
- owning department
- allowed roles
- approval status
- version
- created by
- created at
- updated at
- indexed at

Endpoints:

- `GET /api/sources`
- `POST /api/sources`
- `GET /api/sources/{source_id}`
- `PUT /api/sources/{source_id}`
- `DELETE /api/sources/{source_id}`
- `POST /api/sources/{source_id}/index`

Validation rules:

- Source must be in an approved local folder or repository.
- Source must have metadata.
- Source must define role or department access.
- Source must be marked approved before indexing.
- All source changes must be audit logged.

Relevant requirements:

- UC4, SUC4
- Req02, Req04
- NfReq10

### 4.4 Document Ingestion Pipeline

The ingestion pipeline converts approved documents into retrievable chunks.

Steps:

1. Load approved files from `data/approved_sources`.
2. Extract text from supported formats.
3. Split text into chunks with overlap.
4. Attach metadata to each chunk.
5. Generate embeddings.
6. Store embeddings in ChromaDB.
7. Store source and chunk metadata in the relational database.

Initial supported document types:

- `.txt`
- `.md`
- `.pdf`

Chunking recommendation:

- 600 to 1,000 tokens per chunk
- 100 to 150 token overlap
- Preserve source title, page number if available, section heading if available, role restrictions, and department metadata

Acceptance criteria:

- An admin can index a source.
- Indexed chunks can be retrieved by semantic search.
- Retrieval excludes chunks outside the authenticated user's role/department permissions.

### 4.5 Retrieval Service

The retrieval service is the core of the RAG pipeline.

Input:

- user question
- user profile
- conversation id
- role and department filters

Process:

- Embed the user question.
- Retrieve top-k matching chunks from the vector database.
- Apply metadata filters for role and department.
- Return ranked chunks with relevance scores.
- Detect no-result and low-relevance cases.

Recommended defaults:

- top_k: 5
- minimum relevance threshold: tune empirically
- no-answer path if no chunk passes threshold

Relevant requirements:

- Req02: answer based on company knowledge
- Req04: source references
- Req05: no reliable answer fallback
- Req12: outside-scope handling
- NfReq04: response within 5 seconds for 90% of requests

### 4.6 Context Manager

The context manager supports follow-up questions.

Implementation:

- Store conversation records in the database.
- Store user messages and assistant messages.
- Load recent turns for each new request.
- Use a sliding window to fit within model context limits.
- Optionally summarize older turns later.

Initial policy:

- Keep the last 6 to 10 turns.
- Never include conversations from another user.
- Do not use stored conversations for model retraining.

Relevant requirements:

- Req06: use prior conversation context
- NfReq11: no retraining on confidential conversations without approval

### 4.7 Answer Generation Service

The answer service converts retrieved context into a grounded response.

Prompt rules:

- Answer only from retrieved sources.
- Be concise and clear.
- If sources are insufficient, say that the system does not know.
- Mention uncertainty when retrieval confidence is low.
- Do not reveal restricted information.
- Include citations by source id or source title.

Output schema:

```json
{
  "answer": "string",
  "sources": [
    {
      "source_id": "string",
      "title": "string",
      "url": "string",
      "excerpt": "string",
      "score": 0.91
    }
  ],
  "confidence": 0.88,
  "warning": null,
  "suggested_contacts": []
}
```

Relevant requirements:

- Req01, Req02, Req03
- Req04
- Req06
- Req08
- SUC2

### 4.8 Confidence Service

The confidence score should be simple and explainable for the prototype.

Initial formula:

- Start with normalized top retrieval score.
- Penalize if fewer than two chunks pass threshold.
- Penalize if sources disagree or come from outdated versions.
- Penalize if the LLM output includes uncertainty markers.

Rules:

- If confidence is below 0.85, show a warning.
- If no retrieval score is available, show a warning that confidence could not be calculated.
- If confidence is very low, return fallback answer with human contact route.

Relevant requirements:

- Req11: warn below 85%
- NfReq06: 85% acceptable answer accuracy target
- SUC3

### 4.9 Feedback Service

Employees can mark answers helpful or not helpful.

Feedback fields:

- id
- conversation id
- message id
- user id
- rating: helpful or not_helpful
- optional comment
- question
- answer
- sources
- confidence
- created at

Endpoints:

- `POST /api/feedback`
- `GET /api/admin/feedback`
- `GET /api/admin/feedback/stats`

Relevant requirements:

- Req09: allow helpful/not helpful feedback
- Req10: record feedback for review
- UC5, SUC5

### 4.10 Audit Logging

Audit important events:

- login success/failure
- source added/updated/deleted
- source validation failure
- indexing run
- restricted access attempt
- admin feedback review access
- low-confidence answer event

Fields:

- id
- actor user id
- event type
- resource type
- resource id
- timestamp
- metadata

Relevant requirements:

- NfReq09
- NfReq10
- NfReq11

## 5. Frontend Components

### 5.1 Login Page

Purpose:

- Authenticate user and retrieve role/profile data.

Prototype behavior:

- Select or enter one of the predefined demo users.
- Store token in memory or local storage.
- Redirect to chat page after login.

### 5.2 Chat Page

Required UI:

- Message list
- Natural-language question input
- Loading state
- Answer content
- Source references with clickable links
- Confidence score or confidence badge
- Low-confidence warning
- Human contact suggestion when no answer is available
- Helpful/not helpful feedback controls

Behavior:

- Submit user question to `POST /api/chat`
- Keep conversation id across turns
- Render follow-up answers in the same thread
- Disable submit while request is active
- Show errors with retry option

Relevant requirements:

- Req01, Req02, Req03, Req04, Req05, Req06, Req09, Req11
- NfReq01, NfReq02, NfReq03

### 5.3 Admin Source Management Page

Required UI:

- Table of approved sources
- Add source form
- Edit source metadata
- Approval status
- Role/department access fields
- Index or reindex action
- Last indexed status

Relevant requirements:

- UC4
- SUC4
- NfReq10

### 5.4 Feedback Review Page

Required UI:

- Helpful/not helpful summary
- Filter by topic, department, date, confidence, and source
- List of low-rated answers
- Show question, answer, source references, and confidence

Relevant requirements:

- UC5
- Req10

## 6. Database Model

Use PostgreSQL as the relational database from the start. This keeps local development close to the production-like Docker setup and avoids a later migration from SQLite-specific behavior.

Core tables:

- users
- roles
- conversations
- messages
- sources
- source_chunks
- feedback
- audit_logs

Suggested relationships:

- A user has many conversations.
- A conversation has many messages.
- An assistant message may have many cited source chunks.
- A source has many chunks.
- Feedback belongs to one assistant message.
- Audit logs optionally reference users and resources.

## 7. API Contract

### Authentication

`POST /api/auth/login`

Request:

```json
{
  "email": "employee@example.com",
  "password": "demo"
}
```

Response:

```json
{
  "access_token": "string",
  "user": {
    "id": "u1",
    "name": "Demo Employee",
    "role": "employee",
    "department": "HR"
  }
}
```

### Chat

`POST /api/chat`

Request:

```json
{
  "conversation_id": "optional-string",
  "question": "How many vacation days do interns get?"
}
```

Response:

```json
{
  "conversation_id": "c1",
  "message_id": "m2",
  "answer": "Intern vacation entitlement is ...",
  "sources": [],
  "confidence": 0.87,
  "warning": null,
  "suggested_contacts": []
}
```

### Feedback

`POST /api/feedback`

Request:

```json
{
  "message_id": "m2",
  "rating": "helpful",
  "comment": "optional"
}
```

### Sources

`GET /api/sources`

`POST /api/sources`

`POST /api/sources/{source_id}/index`

### Admin Feedback

`GET /api/admin/feedback`

`GET /api/admin/feedback/stats`

## 8. Safety and Trust Rules

These rules should be implemented before the prototype is considered complete.

- The LLM must not answer from general knowledge when no approved source is found.
- Every factual answer should include at least one citation.
- If no reliable source is found, return "I don't know" plus suggested contact.
- If confidence is below 0.85, display a clear warning.
- Retrieval must apply role and department filters before answer generation.
- Restricted chunks must never be sent to the LLM for unauthorized users.
- Feedback and conversations must not be used for model retraining.
- Source changes and restricted access attempts must be audit logged.

## 9. Docker and Environment Plan

Docker should manage the complete full-stack app for local integration testing, demos, and deployment-like runs. The backend can still be run directly with `uv` during Python development.

### 9.1 Compose Services

Recommended services:

- `frontend`: React/TypeScript Vite app
- `backend`: FastAPI app started through `uv run uvicorn`
- `postgres`: production-like relational database for conversations, users, sources, feedback, and audit logs
- `chroma`: default vector database for document chunk embeddings and semantic retrieval
- `ollama`: optional local LLM service, if the project uses a local model instead of an API-hosted LLM

For the first prototype, PostgreSQL and ChromaDB should both run locally. Compose should also support using the user's local PostgreSQL by changing `DATABASE_URL`, while keeping Chroma as a containerized service for easy setup.

### 9.2 Docker Files

Backend Dockerfile:

- Use a Python base image compatible with the backend Python version.
- Install `uv`.
- Copy `pyproject.toml` and `uv.lock` first for dependency-layer caching.
- Run `uv sync --frozen`.
- Copy the backend app.
- Start with `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`.

Frontend Dockerfile:

- Use a Node base image for development builds.
- Install dependencies from the lockfile.
- Run Vite dev server in development Compose.
- Add a production build stage later with static assets served by Nginx or another lightweight web server.

Compose files:

- `docker-compose.yml`: stable full-stack services.
- `docker-compose.dev.yml`: development overrides for bind mounts, reload, and dev ports.

### 9.3 Environment Variables

Commit `.env.example` and keep real `.env` files uncommitted.

Core variables:

```text
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=5173
DATABASE_URL=postgresql+psycopg://ctrlf:ctrlf@postgres:5432/ctrlf
POSTGRES_USER=ctrlf
POSTGRES_PASSWORD=ctrlf
POSTGRES_DB=ctrlf
VECTOR_STORE_PROVIDER=chroma
CHROMA_HOST=chroma
CHROMA_PORT=8000
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
LLM_PROVIDER=anthropic
OLLAMA_BASE_URL=http://ollama:11434
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
JWT_SECRET=change-me
```

### 9.4 Local Development Modes

Backend-only development:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Full-stack development:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Testing backend locally:

```bash
cd backend
uv run pytest
```

Testing backend inside Docker:

```bash
docker compose run --rm backend uv run pytest
```

## 10. Implementation Phases

### Phase 1: Backend Foundation

Deliverables:

- Convert `backend/main.py` into a FastAPI app.
- Add project dependencies with `uv`.
- Commit `backend/uv.lock`.
- Add app configuration.
- Add health endpoint.
- Add CORS.
- Add basic test setup.

Acceptance criteria:

- Backend starts locally with `uv run uvicorn app.main:app --reload`.
- Health endpoint passes.
- Tests run successfully with `uv run pytest`.

### Phase 1b: Docker Foundation

Deliverables:

- Add backend Dockerfile using `uv`.
- Add frontend Dockerfile.
- Add `.env.example`.
- Add `docker-compose.yml`.
- Add `docker-compose.dev.yml`.
- Add persistent volumes for database/vector data where needed.

Acceptance criteria:

- `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build` starts the stack.
- Frontend can call the backend health endpoint from inside the Docker network.
- Backend container uses the same locked Python dependencies as local `uv` development.

### Phase 2: Authentication and Demo Users

Deliverables:

- Add mock login endpoint.
- Add JWT/session handling.
- Add current-user dependency.
- Seed demo users with roles and departments.

Acceptance criteria:

- Chat and admin endpoints require authentication.
- User role and department are available to services.

### Phase 3: Source Registry and Ingestion

Deliverables:

- Add source database model.
- Add source CRUD endpoints.
- Add source validation.
- Add local document loader.
- Add chunking and metadata extraction.
- Add ChromaDB integration.

Acceptance criteria:

- Admin can add an approved source.
- Admin can index the source.
- Chunks are retrievable with metadata.

### Phase 4: Retrieval and RAG Answering

Deliverables:

- Add retrieval service.
- Add answer generation service.
- Add prompt template.
- Add citation assembly.
- Add no-answer fallback.

Acceptance criteria:

- User can ask a question.
- System retrieves relevant chunks.
- System returns a grounded answer with source references.
- System returns fallback when no source is relevant.

### Phase 5: Conversation Context

Deliverables:

- Add conversations and messages tables.
- Store chat history.
- Load recent turns for follow-up questions.
- Add context window trimming.

Acceptance criteria:

- Follow-up questions use prior conversation context.
- Old context is bounded to avoid prompt overflow.

### Phase 6: Confidence and Safety Handling

Deliverables:

- Add confidence scoring.
- Add below-0.85 warning.
- Add outside-scope detection based on retrieval failure.
- Add restricted-access fallback.
- Add suggested contacts by department.

Acceptance criteria:

- Low-confidence answers are visibly marked.
- No-source answers do not hallucinate.
- Unauthorized role-specific requests are blocked.

### Phase 7: Feedback Capture and Admin Review

Deliverables:

- Add feedback endpoint.
- Link feedback to message/question/answer/source/confidence.
- Add admin feedback list and stats endpoints.
- Add filtering.

Acceptance criteria:

- User can submit helpful/not helpful feedback.
- Admin can review feedback records and summary statistics.

### Phase 8: Frontend Chat App

Deliverables:

- Create React/Vite frontend.
- Add login screen.
- Add chat screen.
- Add source reference rendering.
- Add confidence badge/warning.
- Add feedback controls.
- Add responsive desktop/mobile layout.

Acceptance criteria:

- User can log in, ask questions, read cited answers, and submit feedback.
- UI works on desktop and mobile widths.

### Phase 9: Admin Frontend

Deliverables:

- Add source management page.
- Add source add/edit/index flows.
- Add feedback review page.
- Add route guards for admin roles.

Acceptance criteria:

- Knowledge owner can manage sources.
- Reviewer can inspect feedback and filter low-rated answers.

### Phase 10: Evaluation and Hardening

Deliverables:

- Add sample policy/FAQ documents.
- Add realistic evaluation questions.
- Measure answer correctness, citation coverage, confidence behavior, and response time.
- Add backend unit tests.
- Add integration tests for chat flow.
- Add frontend smoke tests.
- Document setup and demo flow.

Acceptance criteria:

- 90% of test requests complete within 5 seconds in local/demo setup.
- 95% of factual answers include source attribution.
- Low-confidence cases produce warnings.
- Role-restricted documents are not exposed to unauthorized users.

## 11. Testing Strategy

### Unit Tests

- Source validation
- Chunking
- Retrieval filtering
- Confidence scoring
- Feedback persistence
- Access-control checks

### Integration Tests

- Login -> ask question -> retrieve -> answer -> cite source
- Follow-up question uses context
- Restricted user cannot retrieve restricted document
- No relevant source returns fallback
- Feedback is stored and visible to admin

### Evaluation Tests

Create a test set with:

- direct factual HR questions
- IT support questions
- intern-specific questions
- manager-specific questions
- ambiguous follow-ups
- out-of-scope questions
- contradictory source cases
- low-confidence cases

Track:

- answer correctness
- citation presence
- citation relevance
- confidence score
- response time
- fallback correctness

## 12. MVP Definition

The minimum viable prototype is complete when:

- A user can log in.
- A knowledge owner can register and index approved sample documents.
- An employee can ask a natural-language question.
- The backend retrieves relevant approved chunks.
- The LLM generates a concise answer grounded in those chunks.
- The answer shows citations and confidence.
- Low-confidence or no-source cases produce a safe fallback.
- Follow-up questions use conversation context.
- Role-restricted documents are filtered before retrieval.
- The employee can submit helpful/not helpful feedback.
- An admin can review stored feedback.

## 13. Requirement Traceability

| Requirement | Implementation Area |
| --- | --- |
| Req01 Natural-language input | Chat UI, chat API, answer service |
| Req02 Knowledge-based answer | Retrieval service, vector DB, answer service |
| Req03 Clear concise language | Prompt template, answer service, UI |
| Req04 Source references | Retrieval metadata, citation assembly, source links |
| Req05 No reliable answer fallback | Retrieval threshold, fallback handler, contact routing |
| Req06 Follow-up context | Context manager, conversation storage |
| Req07 Authentication | Auth service, route guards, user sessions |
| Req08 Role-specific answers | Role/profile service, retrieval filters |
| Req09 User feedback | Feedback controls, feedback API |
| Req10 Feedback review | Feedback store, admin review UI |
| Req11 Low-confidence warning | Confidence service, UI warning |
| Req12 Outside-scope handling | Retrieval threshold, scope/fallback handler |
| NfReq01 Web chat interface | React frontend |
| NfReq02 Clickable source links | Source list component, source URLs |
| NfReq03 Desktop/mobile browser support | Responsive frontend |
| NfReq04 Response within 5 seconds | Retrieval tuning, async backend, evaluation |
| NfReq05 200 concurrent users | Stateless API design, production DB, scalable deployment path |
| NfReq06 85% acceptable accuracy | Evaluation set, retrieval thresholds, prompt tuning |
| NfReq07 95% factual source attribution | Citation requirement in answer schema |
| NfReq08 99% availability | Health checks, deployment monitoring, error handling |
| NfReq09 GDPR compliance | Auth, access control, retention policy, audit logs |
| NfReq10 Approved sources only | Source registry, validation, retrieval filters |
| NfReq11 No retraining on private chats | Data policy, configuration, documentation |

## 14. Main Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| LLM hallucinates unsupported answer | Prompt rules, retrieval threshold, no-source fallback |
| User sees restricted information | Apply access filters before retrieval and before prompt construction |
| Citations are missing or misleading | Build citations from retrieved chunks, not generated text |
| Confidence score is not meaningful | Start with transparent retrieval-based score and tune using evaluation set |
| Response time exceeds 5 seconds | Cache embeddings, use top-k retrieval, keep prompts short, stream later if needed |
| Follow-up context grows too large | Sliding window and optional summarization |
| Source documents contradict each other | Detect multiple high-scoring conflicting chunks, warn user, show both sources |
| Feedback is collected but unused | Add admin review dashboard and basic statistics early |

## 15. Suggested First Sprint

The first sprint should focus on proving the main technical flow end to end.

Tasks:

1. Replace backend stub with FastAPI app.
2. Configure `uv` dependencies, lockfile, and backend scripts.
3. Add backend and frontend Dockerfiles.
4. Add Docker Compose files for the full-stack local environment.
5. Add mock authentication with demo users.
6. Add source registry model and a few sample approved documents.
7. Implement ingestion for Markdown or text files.
8. Add ChromaDB vector store.
9. Implement `POST /api/chat` with retrieval, answer generation, sources, and confidence.
10. Add minimal React chat UI.
11. Add feedback submission.
12. Write tests for source filtering, no-answer fallback, and feedback storage.

Sprint demo:

- Log in as an employee.
- Ask a policy question.
- Receive a cited answer.
- Ask a follow-up.
- See confidence warning on uncertain question.
- Submit feedback.
- Log in as admin and review feedback.
