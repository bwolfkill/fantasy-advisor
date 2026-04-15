from app.core.config import Settings


def test_settings():
    settings = Settings()

    assert settings.ENVIRONMENT == "dev"
    assert settings.LOG_LEVEL == "INFO"
