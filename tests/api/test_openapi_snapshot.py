"""OpenAPI schema snapshot test.

Pinning the OpenAPI document protects against accidental contract drift –
e.g. a developer renames a field, adds an unintended public route, or
flips an endpoint from auth-required to public. The first run materialises
``tests/api/snapshots/openapi.json``; subsequent runs diff against it.

To intentionally update the snapshot, run pytest with
``UPDATE_OPENAPI_SNAPSHOT=1`` set::

    UPDATE_OPENAPI_SNAPSHOT=1 pytest tests/api/test_openapi_snapshot.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app.main import app


SNAPSHOT_PATH = Path(__file__).parent / "snapshots" / "openapi.json"


def _dump_openapi(schema: dict) -> str:
    """Serialize the OpenAPI schema deterministically (sorted keys, 2-space)."""
    return json.dumps(schema, sort_keys=True, indent=2) + "\n"


def _load_snapshot() -> str | None:
    if not SNAPSHOT_PATH.exists():
        return None
    return SNAPSHOT_PATH.read_text()


def _write_snapshot(serialized: str) -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(serialized)


def test_openapi_schema_matches_snapshot():
    """``app.openapi()`` is byte-stable against the pinned snapshot.

    On first run (snapshot missing) the file is created and the test
    passes. To intentionally refresh, set ``UPDATE_OPENAPI_SNAPSHOT=1``
    in the environment and re-run – the new schema is written and the
    test passes.
    """
    schema = app.openapi()
    serialized = _dump_openapi(schema)

    if os.environ.get("UPDATE_OPENAPI_SNAPSHOT") == "1":
        _write_snapshot(serialized)
        pytest.skip("Snapshot refreshed via UPDATE_OPENAPI_SNAPSHOT=1")

    snapshot = _load_snapshot()
    if snapshot is None:
        # First run – create snapshot and pass.
        _write_snapshot(serialized)
        return

    assert serialized == snapshot, (
        f"OpenAPI schema drifted from the pinned snapshot at {SNAPSHOT_PATH}.\n"
        "If the change is intentional, refresh with: "
        "UPDATE_OPENAPI_SNAPSHOT=1 pytest tests/api/test_openapi_snapshot.py"
    )


def test_openapi_includes_engagement_routes():
    """Sanity check: mounting the engagement router exposes /likes/* etc.

    This test guards against the historic bug where the engagement
    router was implemented but never ``include_router``'d.
    """
    schema = app.openapi()
    paths = set(schema.get("paths", {}).keys())

    expected = {
        "/likes/tracks/{track_id}",
        "/reposts/tracks/{track_id}",
        "/tracks/{track_id}/comments",
    }
    missing = expected - paths
    assert not missing, f"Expected engagement routes are missing: {missing}"


def test_openapi_includes_root_route():
    schema = app.openapi()
    assert "/" in schema.get("paths", {}), "Root health-check route missing"
