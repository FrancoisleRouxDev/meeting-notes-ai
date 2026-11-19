from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Values are read from backend/.env. The defaults are for local development only.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./app.db"
    frontend_origin: str = "http://localhost:5173"
    # Set to true in production, where the site runs on HTTPS.
    session_cookie_secure: bool = False
    session_days: int = 7


settings = Settings()