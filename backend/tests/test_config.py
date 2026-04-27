from app.core.config import Settings


def test_settings():
    settings = Settings()

    assert settings.ENVIRONMENT == "development"
    assert settings.LOG_LEVEL == "INFO"
