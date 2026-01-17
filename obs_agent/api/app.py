"""FastAPI application for ObsAgent."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import router

load_dotenv()

app = FastAPI(
    title="ObsAgent",
    description="Screenshot information extraction API for Obsidian with Git sync",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Static files
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def index():
    """Serve the test page or API info."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "message": "ObsAgent API is running",
        "docs": "/docs",
        "endpoints": {
            "POST /api/process": "Process screenshot (app_name, image_base64) -> analyze, save, git sync",
            "GET /api/health": "Health check",
        },
    }
