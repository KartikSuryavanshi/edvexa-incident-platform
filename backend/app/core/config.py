from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./edvexa.db"
    cors_origins: str = "http://localhost:5173"
    ai_api_key: str | None = None
    auth_tokens: str = ""
    threshold_degraded_latency_ms: float = 300.0
    threshold_unhealthy_latency_ms: float = 1000.0
    threshold_degraded_error_rate: float = 0.05
    threshold_unhealthy_error_rate: float = 0.20
    threshold_degraded_availability: float = 0.995
    threshold_unhealthy_availability: float = 0.95
    recovery_max_attempts: int = 3
    recovery_backoff_seconds: float = 0.05

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
