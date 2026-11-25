from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401  (registers the tables with SQLAlchemy)
from app.core.config import settings
from app.routers import action_items, auth, integrations, meetings, password_reset

app = FastAPI(title="Meeting Notes AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,  # the browser needs this to send the session cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

# All API routes live under /api. In development the Vite proxy forwards /api here.
# In production, FastAPI serves the frontend from the same origin.
app.include_router(auth.router, prefix="/api")
app.include_router(meetings.router, prefix="/api")
app.include_router(action_items.router, prefix="/api")
app.include_router(integrations.router, prefix="/api")
app.include_router(password_reset.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}


# The Docker image copies the built React app to ./static. Locally that folder doesn't exist,
# and the Vite dev server serves the frontend instead.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        # Real files from the build (such as favicon.ico) are served directly.
        # Anything else returns index.html, so routes like /meetings/3 still work on refresh.
        candidate = (STATIC_DIR / full_path).resolve()
        if full_path and candidate.is_file() and STATIC_DIR.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")

