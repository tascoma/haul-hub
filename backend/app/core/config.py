from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str
    host: str = "127.0.0.1"
    port: int = 8000
    # Plain str — pydantic-settings would JSON-decode a list[str] field before validators run.
    allowed_origins: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/haul_hub"
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    storage_bucket: str = "uploads"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"
    log_level: str = "INFO"

    # Google Maps server-side key (Geocoding API). Separate from the browser key the
    # web frontend uses. When None, geocoding is skipped and addresses stay uncoordinated.
    google_maps_api_key: str | None = None

    # JWT auth — uses secret_key as the signing key.
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Pricing (all in cents). Tune via env without code changes.
    price_base_cents: int = 2000  # flat dispatch fee
    price_per_mile_cents: int = 200  # per mile
    price_weight_surcharge_per_100lb_cents: int = 50  # per 100 lb
    price_express_multiplier: float = 1.5

    # Stripe Connect. When stripe_secret_key is None the payments service is in
    # bookkeeping-only mode: Payment rows are written but no API calls are made.
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_connect_refresh_url: str = "http://localhost:5173/onboarding/refresh"
    stripe_connect_return_url: str = "http://localhost:5173/onboarding/return"
    platform_fee_bps: int = 1000  # 10% of haul price

    model_config = {"env_file": "../.env"}


settings = Settings()
