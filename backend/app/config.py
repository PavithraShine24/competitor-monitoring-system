from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://monitor:monitor_password@localhost:5432/competitor_monitor"
    redis_url: str = "redis://localhost:6379/0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    jwt_secret: str = "change-this-development-secret"
    polling_interval_seconds: int = 300
    request_timeout_seconds: int = 20
    max_retries: int = 3
    worker_concurrency: int = 4
    sitemap_candidate_limit: int = 50
    allow_local_demo_targets: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
