from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_base_url: str = ""
    upload_max_mb: int = 10
    cors_origins: str = "null,http://localhost:5500,http://127.0.0.1:5500"
    log_level: str = "INFO"

    class Config:
        env_file = Path(__file__).parent / ".env"
        env_file_encoding = "utf-8"


settings = Settings()

BASE_DIR = Path(__file__).parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
DB_PATH = BASE_DIR / "redai.db"
