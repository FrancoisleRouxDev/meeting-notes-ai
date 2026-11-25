# Meeting Notes AI

A web app where you paste or upload a meeting transcript and get back a summary, the key decisions and action items with owners and due dates. The AI does the reading. The app checks its output before saving anything, and an owner or due date is only saved when the transcript states it.

Built as a take-home challenge for Luckybeard's Launchpad programme.

**Live app:** https://meeting-notes-ai-nbv6.onrender.com/login


## Status

**Working now**

- Register, log in, log out, and delete your account (soft delete)
- Paste a transcript, or upload a `.txt`, `.vtt` or `.md` file
- AI analysis: summary, decisions and action items, each validated before saving
- Meeting list and detail pages, with the summary, decisions, transcript and action items
- Edit a meeting's title, summary and decisions
- Edit each action item's text, owner, due date and status, tick items off, add items, and delete them
- "My action items" page with filters for status, owner and overdue items
- Delete a meeting, with explicit confirmation
- Account page with account deletion
- Backend tests (40 passing)
- Desktop app (Tauri) that opens the web app in a native window

**Not built yet**

- Frontend tests
- Database migrations (tables are created on startup for now)
- Source linking from action items back to the transcript line

## How it works

1. Log in, then paste or upload a transcript with a title and date.
2. The transcript is saved immediately, before any AI call.
3. Run analysis. Three separate OpenRouter calls produce a summary, the decisions and the action items.
4. Each response is validated against a schema. Owner and due-date values also need exact transcript quotes; dates are kept only when the quoted wording resolves to the returned date. If any part fails, nothing is saved, and the meeting is marked `failed` so you can retry. The transcript is never lost.
5. Analysis runs once per meeting. Running it again would overwrite edits made later, so the API returns 409 instead.
6. Edits and action item changes are saved as you make them. Only your own meetings and items are visible.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React, TypeScript, Vite | Typed UI with a fast dev server |
| Data fetching | TanStack Query | Loading, error and retry states handled consistently |
| Routing | React Router | Meetings, meeting detail, open items and account pages |
| Backend | Python, FastAPI | Quick to build, with interactive API docs at `/docs` |
| Validation | Pydantic v2 | Validates requests, and defines the schema the AI output must match |
| Database | SQLite (development), PostgreSQL on Supabase (production), SQLAlchemy 2.0 | No setup for reviewers locally; a hosted Postgres database for the live app |
| Migrations | Alembic | Installed; migrations still to be written |
| Passwords | argon2-cffi | Modern, memory-hard password hashing |
| Sessions | HTTP-only cookies backed by server-side session rows | Sessions can be revoked on logout or account deletion |
| AI provider | OpenRouter, free model set via environment variable | Required by the brief |
| AI calls | httpx, one focused call per output (summary, decisions, action items) | Smaller, separately validated outputs |
| Testing | pytest (backend) | Covers auth, permissions, uploads, open items and the AI failure paths |
| Desktop | Tauri (Rust) | Wraps the web app in a native window |
| Deployment | Docker, Render (web service), Supabase (database) | One container serves the API and the built frontend |
| API docs | FastAPI OpenAPI (Swagger UI) | Every route can be tried without reading the code |

## Running it locally

You will need Python 3.12 or newer, Node.js LTS, Git, and a free OpenRouter account.

### 1. Clone the repository

```bash
git clone https://github.com/francoislerouxdev/meeting-notes-ai.git
cd meeting-notes-ai
```

### 2. Start the backend

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

On macOS or Linux, use `source .venv/bin/activate` and `cp .env.example .env`.

Open `backend/.env` and set `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`. Then start the server:

```powershell
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. Every endpoint can be tried there. Register first, then log in.

Registration, meetings and the open items view work without an OpenRouter key. Analysis returns a 503 until the key and model are set.

To create two demo users, run `python seed.py` from the `backend` folder. It only creates missing accounts and does not change existing passwords. These credentials are for the demo only:

| Email | Password |
|---|---|
| `demo1@example.com` | `LaunchPadDemo1!` |
| `demo2@example.com` | `LaunchPadDemo2!` |

### 3. Start the frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server forwards `/api` requests to the backend, so the app works on one origin.

### 4. Run the tests

From the `backend` folder, with the virtual environment active:

```powershell
python -m pytest -q
```

The tests use their own temporary database, so your `app.db` is never touched. The AI tests replace the model call with a fake, so they need no API key.

## Desktop app (Tauri)

The `desktop` folder holds a Tauri wrapper. Its window loads the web app's URL, so the app runs without a local server once the web app is hosted.

You will need Rust (from https://rustup.rs) and the Visual Studio Build Tools with the "Desktop development with C++" workload.

```powershell
cd desktop
npm install
npm run tauri dev
```

The window URL is set in `desktop/src-tauri/tauri.conf.json`. Point it at the live app, or at `http://localhost:8000` for local testing. To test locally, build the frontend and copy it into `backend/static`, then start the backend on port 8000. `npm run tauri build` creates an installer in `desktop/src-tauri/target/release/bundle/`.

## Deployment

The live app runs as one Docker container on Render. The container serves the API and the built frontend. The database is PostgreSQL on Supabase.

1. Create a Supabase project and copy its **Session pooler** connection string. Change the scheme to `postgresql+psycopg://` and add `?sslmode=require`.
2. Create a Render web service from this repository, using the **Docker** runtime and the `Dockerfile` at the root. Set the health check path to `/health`.
3. Set these environment variables in Render. They are never stored in the repository:

| Variable | Value |
|---|---|
| `DATABASE_URL` | the Supabase URL from step 1 |
| `OPENROUTER_API_KEY` | your OpenRouter key |
| `OPENROUTER_MODEL` | `nvidia/nemotron-3.5-super-vl:free` |
| `SESSION_COOKIE_SECURE` | `true` |
| `FRONTEND_ORIGIN` | your Render URL |

4. Load the demo users once, from your machine, with the Supabase URL set for that terminal session only, then run `python seed.py` from the `backend` folder.

## Environment variables

Set these in `backend/.env` locally, or in the hosting dashboard when deployed. The file is ignored by Git. `backend/.env.example` lists them with placeholder values.

| Variable | Required | Purpose |
|---|---|---|
| `OPENROUTER_API_KEY` | For analysis | Your OpenRouter key. Never commit it. |
| `OPENROUTER_MODEL` | For analysis | The OpenRouter model ID to use |
| `OPENROUTER_TIMEOUT_SECONDS` | No | How long to wait for the AI (default 60) |
| `DATABASE_URL` | No | Default `sqlite:///./app.db`. Use the Postgres URL in production. |
| `FRONTEND_ORIGIN` | No | Allowed origin for the browser (default `http://localhost:5173`) |
| `SESSION_COOKIE_SECURE` | No | Set to `true` when served over HTTPS (default `false`) |
| `SESSION_DAYS` | No | How long a login lasts (default 7) |

## API overview

All routes are under `/api`. The full list, with request bodies, is in `/docs`.

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create an account and log in |
| POST | `/api/auth/login` | Log in |
| POST | `/api/auth/logout` | Log out |
| GET | `/api/auth/me` | The logged-in user |
| DELETE | `/api/auth/me` | Delete your account (soft delete) |
| POST | `/api/meetings` | Create a meeting from pasted text |
| POST | `/api/meetings/upload` | Create a meeting from an uploaded file |
| GET | `/api/meetings` | Your meetings, newest first |
| GET | `/api/meetings/{id}` | One meeting, with its transcript, AI results and action items |
| PATCH | `/api/meetings/{id}` | Edit the title, summary or decisions |
| DELETE | `/api/meetings/{id}?confirm=true` | Delete a meeting and its action items (permanent) |
| POST | `/api/meetings/{id}/analyse` | Run AI analysis once |
| POST | `/api/meetings/{id}/action-items` | Add an action item |
| GET | `/api/action-items` | Your action items, with `status`, `owner` and `overdue` filters |
| PATCH | `/api/action-items/{id}` | Edit an action item |
| DELETE | `/api/action-items/{id}` | Delete an action item |
| GET | `/health` | Health check |

## Key decisions and trade-offs

- **FastAPI and SQLite locally, Postgres in production.** Reviewers can run it with no database setup. SQLAlchemy keeps the move between the two simple.
- **Sessions.** Random tokens in HTTP-only cookies. Only a hash of each token is stored, so a leaked database can't be used to log in. Logout or account deletion revokes access immediately.
- **Passwords.** Hashed with Argon2. Passwords are never stored or returned.
- **Ownership.** Every query filters on the logged-in user's ID. Another user's meeting or item returns 404, the same as one that doesn't exist, so IDs in the URL reveal nothing.
- **Soft delete for accounts, hard delete for meetings.** The brief asks for soft delete on accounts. Deleting a meeting is permanent, and needs `confirm=true` so a stray request can't remove one.
- **Transcript first.** The transcript is saved before any AI call, so a failed analysis never loses it.
- **One call per output.** Three focused prompts, each with its own schema, instead of one large prompt. Each response is validated before anything is saved.
- **Evidence guard.** An owner is only saved if an exact transcript quote names them, and a due date is only saved if an exact quote resolves to that date. Unsupported date wording is left blank.
- **Analysis runs once.** Re-running would overwrite edits made later, so a completed meeting returns 409.
- **Manual editing after analysis.** The AI output is a starting point. Every field can be corrected by hand, and corrections are never overwritten by a later analysis.

## Known limitations

- A deleted account's email stays reserved, so nobody can register with it again. This is a simplification, not a requirement.
- Date evidence currently recognizes ISO dates, month-and-day dates, day-of-month dates, weekdays, and simple relative dates. Unsupported or ambiguous date wording is left blank.
- Weekday references are resolved from the meeting date; ambiguous phrases such as "end of next week" are left blank.
- Free model output varies between runs. Testing showed missed items and occasional wrong dates, so output is checked and should be reviewed, but it isn't guaranteed.
- The meeting list has no pagination yet.
- Tables are created on startup. Until migrations exist, a schema change means deleting `backend/app.db` locally, or re-creating the tables in the production database.
- Analysis is synchronous, so the request waits for the model, up to the timeout.
- The free Render service sleeps when idle, so the first request after a quiet period can be slow.

## What I would do with another week

- Alembic migrations, so schema changes don't require recreating tables
- Frontend tests (Vitest and React Testing Library)
- Source linking, so each action item points to the transcript line it came from
- A shareable read-only link for a meeting
- Pagination, and a limit on how often a failed analysis can be retried
- Running analysis in the background, with progress shown in the UI
- A Slack integration that posts a meeting's action items to a channel

## How I used AI

**In the product:** OpenRouter does the analysis. I split it into three calls (summary, decisions, action items) instead of one prompt, and each has its own Pydantic schema. I refined the prompts after testing them on sample transcripts. The first version invented a due date from a room booking, treated tentative tasks as commitments, and produced action items from a discussion with no commitments. Later versions added worked examples for the cases the model got wrong, such as scheduling notes being recorded as decisions. The owner guard is plain code, not AI: it only keeps a name the transcript contains.

**In development:** I used an AI assistant to plan the build, draft code, write the tests, and generate example transcripts to test uploads and analysis. I reviewed and ran everything myself, and fixed the issues I found.
