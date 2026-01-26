from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.core.database import create_db_and_tables
from app.api import auth, sessions, cards
import os


app = FastAPI(
    title="Code Swipe",
    description="Interactive code refactoring through swipe interface",
    version="0.1.0",
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create database tables on startup
@app.on_event("startup")
async def on_startup():
    create_db_and_tables()
    # Create repos working directory
    os.makedirs(settings.repos_work_dir, exist_ok=True)


# Include API routers
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(cards.router)


# Serve static files
static_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


# Serve frontend
@app.get("/")
async def serve_root():
    """Serve index.html"""
    index_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "templates", "index.html"
    )
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Code Swipe API"}


@app.get("/session/{session_id}")
async def serve_session(session_id: str):
    """Serve session.html"""
    session_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "templates", "session.html"
    )
    if os.path.exists(session_path):
        return FileResponse(session_path)
    return {"error": "Session page not found"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
