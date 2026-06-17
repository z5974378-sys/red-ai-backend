from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings, BASE_DIR
from routers import analyze, generate, rewrite, compliance, sessions

app = FastAPI(title="Red AI Backend")

origins = [o.strip() for o in settings.cors_origins.split(",")]
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


app.mount("/", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
