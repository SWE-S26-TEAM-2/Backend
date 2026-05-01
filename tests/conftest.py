import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _set_default_env():
    """
    Ensure DATABASE_URL and SECRET_KEY are present before any module
    that imports app.core.config is collected by pytest.

    Uses setdefault so real values from .env or CI secrets are never
    overridden — this only kicks in when neither source provides them.
    """
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
