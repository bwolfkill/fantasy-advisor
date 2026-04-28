from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str

    # CORS
    cors_origins: list[str]

    # Auth
    secret_key: str
    access_token_expire_seconds: int

    # External APIs
    sleeper_api_base_url: str = "https://api.sleeper.app/v1"
    fantasycalc_api_base_url: str = "https://api.fantasycalc.com"

    # App
    environment: str = "development"
    log_level: str = "INFO"


settings = Settings()
