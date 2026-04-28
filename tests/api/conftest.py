"""
Pytest fixtures for HTTP-level (TestClient) router tests.

These fixtures wire the FastAPI app up against an in-memory SQLite engine
so the API surface can be exercised end-to-end without touching a real
Postgres instance. Most existing service-layer logic is exercised by
overriding ``get_current_user`` and monkeypatching service classmethods
which keeps tests fast and free of repository wiring concerns. The
SQLite engine is still attached to ``get_db`` for tests that occasionally
hit ``UserRepository.get_by_username`` directly.

Layout:
  - ``client``        – TestClient + ``get_db`` overridden to a
                         ``DummyDB`` (cheap, no SQL involved).
  - ``db_client``     – TestClient + ``get_db`` overridden to a real
                         SQLite-in-memory + StaticPool engine, with
                         ``create_all`` / ``drop_all`` per function.
  - ``override_auth`` – swaps ``get_current_user`` for a fake user.
  - ``auth_headers``  – Bearer header factory using ``create_access_token``.
  - ``seed_user`` /
    ``seed_track`` /
    ``seed_playlist`` – insert real ORM rows when ``db_client`` is in use.
  - ``tmp_upload_dir`` – temp ``UPLOAD_DIR`` injected into the relevant
                         service modules.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.database.database import get_db
from app.main import app


# ── Lightweight DB stand-ins ──────────────────────────────


class DummyDB:
    """Plain object that quacks like a SQLAlchemy ``Session``.

    Used by the fast ``client`` fixture; routes that monkeypatch their
    service layer never actually consult the session, so a no-op object
    is sufficient and avoids any postgres-vs-sqlite UUID type drama.
    """

    def close(self) -> None:  # pragma: no cover - trivial
        pass


def _yield_dummy_db():
    yield DummyDB()


# ── Real SQLite engine (opt-in via db_client) ─────────────


@pytest.fixture(scope="function")
def db_engine():
    """Provide a fresh in-memory SQLite engine per test function.

    StaticPool keeps every TestClient request talking to the same
    in-memory DB connection so seeded rows are visible across requests.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    from app.database.database import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def db_session_factory(db_engine):
    from sqlalchemy.orm import sessionmaker

    return sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


# ── TestClient fixtures ───────────────────────────────────


@pytest.fixture(scope="function")
def client():
    """Fast TestClient: ``get_db`` returns a no-op ``DummyDB``.

    Constructed without a ``with`` block so the legacy ``on_event``
    startup hook in ``app.main`` (which would try to ``create_all`` on
    the production Postgres engine) does not fire during tests.

    All ``app.dependency_overrides`` are cleared on teardown so tests
    cannot leak fake users or DB sessions into the next test.
    """
    app.dependency_overrides[get_db] = _yield_dummy_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db_client(db_session_factory):
    """TestClient backed by a real SQLite session – use only when a test
    needs to actually round-trip through the repositories."""
    def _override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ── Fake user / auth helpers ──────────────────────────────


class FakeUser:
    """In-memory user object that quacks like the SQLAlchemy User model."""

    def __init__(
        self,
        user_id: uuid.UUID | None = None,
        email: str = "user@example.com",
        username: str = "testuser",
        display_name: str = "Test User",
        is_verified: bool = True,
        is_suspended: bool = False,
        is_private: bool = False,
        is_premium: bool = False,
        account_type: str = "listener",
        profile_picture: str | None = None,
        cover_photo: str | None = None,
        bio: str | None = None,
        location: str | None = None,
        follower_count: int = 0,
        following_count: int = 0,
        track_count: int = 0,
    ):
        self.user_id = user_id or uuid.uuid4()
        self.email = email
        self.username = username
        self.display_name = display_name
        self.account_type = account_type
        self.is_verified = is_verified
        self.is_suspended = is_suspended
        self.is_private = is_private
        self.is_premium = is_premium
        self.profile_picture = profile_picture
        self.cover_photo = cover_photo
        self.bio = bio
        self.location = location
        self.follower_count = follower_count
        self.following_count = following_count
        self.track_count = track_count
        self.password_hash = "$2b$12$placeholderhash"
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = None


@pytest.fixture
def fake_user_factory() -> Callable[..., FakeUser]:
    def _make(**overrides: Any) -> FakeUser:
        return FakeUser(**overrides)

    return _make


@pytest.fixture
def override_auth():
    """Helper that swaps ``get_current_user`` for a fake user for one test.

    Yields a callable; calling it with a ``FakeUser`` (or no args)
    installs the override. The override is cleared automatically on
    teardown.
    """
    from app.core.dependencies import get_current_user

    def _install(user: FakeUser | None = None) -> FakeUser:
        u = user or FakeUser()
        app.dependency_overrides[get_current_user] = lambda: u
        return u

    yield _install
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def auth_headers(fake_user_factory):
    """Return an ``auth_headers(user)`` factory.

    The token is signed with the real ``create_access_token`` so any
    middleware that inspects the header is exercised, even though most
    tests still override ``get_current_user`` for the actual user lookup.
    """
    def _make(user: FakeUser | None = None) -> dict[str, str]:
        u = user or fake_user_factory()
        token = create_access_token(str(u.user_id))
        return {"Authorization": f"Bearer {token}"}

    return _make


# ── DB seeding helpers (real SQLAlchemy rows) ─────────────


@pytest.fixture
def seed_user(db_session_factory):
    """Insert a real ``User`` row and return it.

    Use only with the ``db_client`` fixture (or another test that
    explicitly opts into the SQLite engine).
    """
    from app.models.user import User

    session = db_session_factory()

    def _make(
        username: str | None = None,
        email: str | None = None,
        display_name: str | None = None,
        **overrides: Any,
    ) -> User:
        uid = uuid.uuid4()
        u = User(
            user_id=uid,
            username=username or f"user_{uid.hex[:8]}",
            email=email or f"{uid.hex[:8]}@example.com",
            display_name=display_name or f"User {uid.hex[:6]}",
            password_hash="$2b$12$placeholderhash",
            account_type="listener",
            is_verified=True,
            is_suspended=False,
            is_private=False,
            is_premium=False,
            follower_count=0,
            following_count=0,
            track_count=0,
            **overrides,
        )
        session.add(u)
        session.commit()
        session.refresh(u)
        return u

    yield _make
    session.close()


@pytest.fixture
def seed_track(db_session_factory):
    """Insert a real ``Track`` row tied to ``user_id`` and return it."""
    from app.models.track import Track

    session = db_session_factory()

    def _make(user_id: uuid.UUID, title: str = "Demo Track", **overrides: Any) -> Track:
        track = Track(
            track_id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            description=overrides.pop("description", "Demo description"),
            file_url=overrides.pop("file_url", "https://example.com/demo.mp3"),
            visibility=overrides.pop("visibility", "public"),
            **overrides,
        )
        session.add(track)
        session.commit()
        session.refresh(track)
        return track

    yield _make
    session.close()


@pytest.fixture
def seed_playlist(db_session_factory):
    """Insert a real ``Playlist`` row owned by ``user_id`` and return it."""
    from app.models.playlist import Playlist

    session = db_session_factory()

    def _make(
        user_id: uuid.UUID,
        name: str = "Demo Playlist",
        description: str | None = "Demo description",
        **overrides: Any,
    ) -> Playlist:
        playlist = Playlist(
            playlist_id=uuid.uuid4(),
            user_id=user_id,
            name=name,
            description=description,
            **overrides,
        )
        session.add(playlist)
        session.commit()
        session.refresh(playlist)
        return playlist

    yield _make
    session.close()


# ── Upload directory isolation ────────────────────────────


@pytest.fixture
def tmp_upload_dir(tmp_path, monkeypatch):
    """Point UPLOAD_DIR at a temp directory for the duration of the test.

    Patches the env var and the resolved constants on each module that
    imported ``UPLOAD_DIR`` at module load time.
    """
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))

    from app.services import track_service, playlist_service, user_service

    monkeypatch.setattr(track_service, "UPLOAD_DIR", str(upload_dir), raising=False)
    monkeypatch.setattr(playlist_service, "UPLOAD_DIR", str(upload_dir), raising=False)
    monkeypatch.setattr(user_service, "UPLOAD_DIR", str(upload_dir), raising=False)

    return upload_dir


# ── Safety net ────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_overrides_safety_net():
    """Belt-and-suspenders: ensure no test leaks dependency overrides.

    The ``client`` fixture already clears overrides on teardown but tests
    that call ``override_auth`` outside ``client`` would otherwise leak.
    """
    yield
    app.dependency_overrides.clear()


def make_uuid_str() -> str:
    """Return a fresh UUID4 string – handy for response-payload mocks."""
    return str(uuid.uuid4())


__all__ = [
    "FakeUser",
    "DummyDB",
    "make_uuid_str",
]
