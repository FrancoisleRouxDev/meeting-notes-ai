# Meeting Notes AI

A small web application that urns meeting transcripts into structured notes. The users can paste or upload their meeting transcripts and the AI model produces a summary, list of decisions, and action items with owners and due dates where the transcript states them.

Every AI result is treated as untrusted input: it is validated against a schema before svaing, and users can edit everything the AI produces. Nothing is inveted. If the transcript doesn't name an owner or date, the field is left blank for review.

## Planned Features

- Register, log in and delete your account (soft delete)
- Upload or paste transcripts, stored with title, date and original text
- AI analysis: summary, decisions, action items (what, owner, due date)
- Edit any AI output: add, delete and tick off action items (to do, in progress, done)
- Meeting list and detail pages
"My open action items" view across meetings, filterable by status, owner, and overdue.

## Status
Early planning. Nothing is built yet.

## Setup
Instructions will be added once the project runs locally

## Key decisions
To be documented as they're made, including the stack, session method, and how AI tools are used.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React, TypeScript, Vite | Typed UI with a fast dev server |
| Data fetching | TanStack Query | Loading, error and retry states handled consistently |
| Routing | React Router | Meeting list, meeting detail and "my open items" pages |
| Backend | Python, FastAPI | Quick to build, with interactive API docs at `/docs` |
| Validation | Pydantic v2 | Validates requests, and defines the schema the AI output must match |
| Database | SQLite (development), SQLAlchemy 2.0 | No setup for reviewers; can move to Postgres later |
| Migrations | Alembic | The schema can be recreated from the repo |
| Passwords | argon2-cffi | Modern, memory-hard password hashing |
| Sessions | HTTP-only cookies backed by server-side session rows | Sessions can be revoked on logout or account deletion |
| AI provider | OpenRouter, free model set via environment variable | Required by the brief; model chosen for structured-output support |
| AI calls | httpx, one tool per task (summarise, extract decisions, extract action items) | Smaller, separately validated outputs instead of one large prompt |
| Testing | pytest (backend), Vitest and React Testing Library (frontend) | Covers AI validation, permission checks and key routes |
| API docs | FastAPI OpenAPI (Swagger UI) | Reviewers can exercise every route without reading the code |
| Deployment | Docker Compose (planned) | Starts the whole system with one command |

Hosting is still to be decided