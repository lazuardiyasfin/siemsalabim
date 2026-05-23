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
