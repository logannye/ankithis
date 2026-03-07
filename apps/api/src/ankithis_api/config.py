from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ANKITHIS_")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    database_url: str = "postgresql+asyncpg://ankithis:ankithis@localhost:5432/ankithis"
    redis_url: str = "redis://localhost:6379/0"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    # Per-stage model overrides (Haiku for bulk, Sonnet for generation, Opus for critique)
    model_stage_a: str = "claude-haiku-4-5-20251001"   # concept extraction — high volume, simple
    model_stage_b: str = "claude-sonnet-4-20250514"    # concept merge — synthesis
    model_stage_c: str = "claude-sonnet-4-20250514"    # card planning — pedagogical judgment
    model_stage_d: str = "claude-sonnet-4-20250514"    # card generation — structured writing
    model_stage_e: str = "claude-opus-4-20250514"      # critique — quality gate, nuanced evaluation
    model_stage_f: str = "claude-haiku-4-5-20251001"   # dedup — simple comparison

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

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_expiry_seconds: int = 86400  # 24 hours

    # Rate limiting (per user, per hour)
    rate_limit_uploads: int = 10
    rate_limit_generations: int = 20

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
