# Meeting Notes AI

A web app where you paste or upload a meeting transcript and get back a summary, the key decisions and action items with owners and due dates. The AI does the reading. The app checks its output before saving anything, and an owner or date is only saved when the transcript states it.

Built as a take-hame challenge for Luckybeard's Launchpad programme.

## Status 

**Working now**

- Register, log in, log out, and delete your account (soft delete)
- Paste a transcript, or uploada '.txt', '.vtt' or '.md' file
- Meeting list and detail endpoints
- Delete a meeting, with explicit confirmation
- AI analysis: summary, decisions and action items, each validated before saving

**Not built yet**

- Editing and tracking action items (add, change, delete, tick off)
- The "my open action items" view with filters
- Frontend screens (the React project is scoffolded but shows only the default page)
- Database migrations (Alembic is installed, but tables are created on the startup for now)
- Seed users, automated tests, Docker and deployed link

## How it works

1. Log in, then paste or upload a transcript with title and date.
2. The transcript is saved immediately, before any AI call.
3. Run analysis. Three separate OpenRouter calls produce a summary, the decisions and the action items.
4. Each response is validated against a schema. If any part fails, nothing is saved, and the meeting is marked `failed` so you can retry. The transcript is never lost.
5. Analysis runs once per meeting. Running it again would overwrite edits made later, so the API returns 409 instead.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React, TypeScript, Vite | Typed UI with a fast dev server |
| Data fetching | TanStack Query | Loading, error and retry states handled consistently |
| Routing | React Router | Meeting list, meeting detail and "my open items" pages |
| Backend | Python, FastAPI | Quick to build, with interactive API docs at `/docs` |
| Validation | Pydantic v2 | Validates requests, and defines the schema the AI output must match |
| Database | SQLite (development), SQLAlchemy 2.0 | No setup for reviewers; can move to Postgres later |
| Migrations | Alembic | Planned; the schema can then be recreated from the repo |
| Passwords | argon2-cffi | Modern, memory-hard password hashing |
| Sessions | HTTP-only cookies backed by server-side session rows | Sessions can be revoked on logout or account deletion |
| AI provider | OpenRouter, free model set via environment variable | Required by the brief |
| AI calls | httpx, one focused call per output (summary, decisions, action items) | Smaller, separately validated outputs |
| Testing | pytest (backend), Vitest and React Testing Library (frontend) | Planned: AI validation, permission checks, key routes |
| API docs | FastAPI OpenAPI (Swagger UI) | Every route can be tried without reading the code |

## Running it locally

You will need Python 3.12 or newer, Node.js LTS, Git, and a free OpenRouter Account.

### 1. Clone the repository

```bash
    git clone https://github.com/francoislerouxdev/meeting-notes-ai.git
    cd meeting-notes-ai
```

### 2. Start the backend

```bash 
    cd backend
    python -m .venv venv
```

On Windows PowerShell, activate the environment and install:

```powershell
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    copy .env.example .env
```

On MacOS or Linux, use `source .venv/bin/activate` and `cp .env.example` instead.

Open `backend/.env` and set `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`. The start the server:

```bash 
    python -m uvicorn app.maim:app --reload
```

Open Http://127.0.0.1:8000/docs. Every endpoint can be tried there. Register first, then log in.

Registration and the meeting endpoint work without an OpenRouter key. Analysis return a 503 until the key and model and set.

### 3. Frontend (scoffold only for now)

```bash 
    cd ../frontend
    npm install
    nom run dev
```

The page at http://localhost:5173 currently shows the default Vite screen.

## Environment variables

Set these in `backend/.env`. The file is ignored by Git. `backend/.env.example` lists them with placeholder values.

| Variable | Required | Purpose |
|---|---|---|
| `OPENROUTER_API_KEY` | For analysis | Your OpenRouter key. Never commit it. |
| `OPENROUTER_MODEL` | For analysis | The OpenRouter model ID to use |
| `OPENROUTER_TIMEOUT_SECONDS` | No | How long to wait for the AI (default 60) |
| `DATABASE_URL` | No | Default `sqlite:///./app.db` |
| `FRONTEND_ORIGIN` | No | Allowed origin for the browser (default `http://localhost:5173`) |
| `SESSION_COOKIE_SECURE` | No | Set to `true` when served over HTTPS (default `false`) |
| `SESSION_DAYS` | No | How long a login lasts (default 7) |

## API overview

| Method | Route | Purpose |
|---|---|---|
| POST | `/auth/register` | Create an account and log in |
| POST | `/auth/login` | Log in |
| POST | `/auth/logout` | Log out |
| GET | `/auth/me` | The logged-in user |
| DELETE | `/auth/me` | Delete your account (soft delete) |
| POST | `/meetings` | Create a meeting from pasted text |
| POST | `/meetings/upload` | Create a meeting from an uploaded file |
| GET | `/meetings` | Your meetings, newest first |
| GET | `/meetings/{id}` | One meeting, with its transcript and AI results |
| DELETE | `/meetings/{id}?confirm=true` | Delete a meeting and its action items (permanent) |
| POST | `/meetings/{id}/analyse` | Run AI analysis once |
| GET | `/health` | Health check |

## Key decisions and trade-offs

- **FastAPI and SQLite.** Reviewers can run it with no database setup. SQLAlchemy keeps the move to Postgres simple.
- **Sessions.** Random tokens in HTTP-only cookies. Only a hash of each token is stored, so a leaked database can't be used to log in, and logout or account deletion revokes access immediately.
- **Passwords.** Hashed with Argon2. Passwords are never stored or returned.
- **Ownership.** Every meeting query filters on the logged-in user's ID. Another user's meeting returns 404, the same as a meeting that doesn't exist, so IDs in the URL reveal nothing.
- **Soft delete for accounts, hard delete for meetings.** The brief asks for soft delete on accounts. Deleting a meeting is permanent, and needs `confirm=true` so a stray request can't remove one.
- **Transcript first.** The transcript is saved before any AI call, so a failed analysis never loses it.
- **One call per output.** Three focused prompts, each with its own schema, instead of one large prompt. Each response is validated before anything is saved.
- **Owner guard.** An owner is only saved if the name appears in the transcript.
- **Analysis runs once.** Re-running would overwrite edits made later, so a completed meeting returns 409.

## Known limitations

- A deleted account's email stays reserved, so nobody can register with it again. This is a simplification, not a requirement.
- The owner guard is a case-insensitive text match, so a short name could match inside a longer word.
- The app doesn't check relative dates such as "Friday". It relies on the model to work them out from the meeting date.
- Free model output varies. Testing showed missed items and occasional wrong dates, so the output is checked and reviewed, but not guaranteed.
- The meeting list has no pagination yet.
- Tables are created on startup. Until migrations exist, a schema change means deleting `backend/app.db` and starting again.
- Analysis is synchronous, so the request waits for the model, up to the timeout.

## What I would do with another week

- Action item editing and tracking, plus the "my open items" view with filters
- Alembic migrations and seed users
- Frontend screens with loading, empty and error states
- Source linking, so each action item points to the transcript line it came from
- Tests for AI validation and permission checks
- Docker Compose, and a deployed link
- Pagination, and a limit on how often a failed analysis can be retried

## How I used AI

**In the product:** OpenRouter does the analysis. I split it into three calls (summary, decisions, action items) instead of one prompt, and each has its own Pydantic schema. I refined the prompts after testing them on sample transcripts. The first version invented a due date from a room booking, treated tentative tasks as commitments, and produced action items from a discussion with no commitments. The owner guard is plain code, not AI: it only keeps a name the transcript contains.
**In development:** I used an AI assistant to plan the build, draft code, and generate example transcripts to test the uploading, and analysis of the AI.