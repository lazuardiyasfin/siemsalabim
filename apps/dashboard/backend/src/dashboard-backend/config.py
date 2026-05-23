from pydantic import field_validator
from pydantic_settings import BaseSettings


class DashboardConfig(BaseSettings):
    # Dashboard backend configuration

    model_config = {"env_prefix": "DASHBOARD_"}

    engine_url: str = "ws://localhost:8000/ws/dashboard"
    host: str = "0.0.0.0"
    port: int = 8001

    user: str = "admin"
    password_hash: str | None = None
    jwt_secret_key: str | None = None

    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:8001"]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v