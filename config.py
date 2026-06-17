from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_base_url: str = ""
    cors_origins: str = "null,http://localhost:5500,http://127.0.0.1:5500"
    log_level: str = "INFO"

    class Config:
        env_file = Path(__file__).parent / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

BASE_DIR = Path(__file__).parent
