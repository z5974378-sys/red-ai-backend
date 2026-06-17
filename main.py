from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

from config import settings, BASE_DIR
from routers import analyze, generate, rewrite, compliance, sessions

app = FastAPI(title="Red AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(sessions.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(generate.router, prefix="/api")
app.include_router(rewrite.router, prefix="/api")
app.include_router(compliance.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/{filename}")
def static_files(filename: str):
    path = BASE_DIR / "static" / filename
    if path.exists():
        return FileResponse(path)
    return FileResponse(BASE_DIR / "static" / "index.html")
