import os


def pytest_configure(config):
    """
    Set fallback env vars before any test module is imported.

    pytest_configure runs before collection, so app.core.config can
    be imported without DATABASE_URL / SECRET_KEY being present in
    the environment. setdefault means real values from .env or CI
    secrets are never overridden.
    """
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
