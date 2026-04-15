from app.core.config import Settings
import math


def test_settings():
    settings = Settings()

    assert settings.ENVIRONMENT == "dev"
    assert settings.LOG_LEVEL == "INFO"
    assert True == False
