from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Values are read from backend/.env. The defaults are for local development only.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./app.db"
    frontend_origin: str = "http://localhost:5173"
    session_cookie_secure: bool = False
    session_days: int = 7

    openrouter_api_key: str = ""
    openrouter_model: str = ""
    # Free models can be slow, so allow time before reporting a failure.
    openrouter_timeout_seconds: float = 60.0


settings = Settings()
