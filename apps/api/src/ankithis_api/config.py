from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ANKITHIS_")

    database_url: str = "postgresql+asyncpg://ankithis:ankithis@localhost:5432/ankithis"
    redis_url: str = "redis://localhost:6379/0"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Storage
    storage_backend: str = "local"  # "local" or "s3"
    storage_local_path: str = "./data/uploads"
    s3_endpoint: str = ""
    s3_bucket: str = "ankithis"
    s3_access_key: str = ""
    s3_secret_key: str = ""

    # Limits
    max_upload_bytes: int = 50 * 1024 * 1024  # 50 MB
    max_pages: int = 300
    max_cards: int = 300

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
