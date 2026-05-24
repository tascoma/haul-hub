from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str
    host: str = "127.0.0.1"
    port: int = 8000
    # Plain str — pydantic-settings would JSON-decode a list[str] field before validators run.
    allowed_origins: str = "http://localhost:5173"
    database_url: str = "sqlite+aiosqlite:///./haul_hub.db"
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    storage_bucket: str = "uploads"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"
    log_level: str = "INFO"

    # JWT auth — uses secret_key as the signing key.
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    model_config = {"env_file": "../.env"}


settings = Settings()
