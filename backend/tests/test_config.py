from app.core.config import Settings


def test_settings():
    settings = Settings()

    assert settings.environment == "development"
    assert settings.log_level == "INFO"
