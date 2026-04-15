from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/fantasy_advisor"
    )

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # External APIs
    SLEEPER_API_BASE_URL: str = "https://api.sleeper.app/v1"
    FANTASYCALC_API_BASE_URL: str = "https://api.fantasycalc.com"

    # App
    ENVIRONMENT: str = "dev"
    LOG_LEVEL: str = "INFO"


settings = Settings()
