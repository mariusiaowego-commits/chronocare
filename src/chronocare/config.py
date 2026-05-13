"""ChronoCare configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "ChronoCare"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/chronocare.db"

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent.parent.parent

    # LLM (OpenRouter)
    llm_provider: str = "openrouter"
    llm_api_key: str = ""  # read from OPENROUTER_API_KEY env var
    llm_model: str = "google/gemini-2.0-flash"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
