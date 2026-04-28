#!/usr/bin/env bash
# Seed wrapper for k6 perf tests.
#
# Strategy:
#   1. If the backend repo's seed_team.py is reachable, run it (truncates
#      users and creates 11 verified team accounts including the perf user).
#   2. Otherwise, fall back to the k6-native seeder (seed_perf.js) which
#      hits POST /auth/register over HTTP.
#
# Required env:
#   DATABASE_URL  - only for the python path
#   BACKEND_URL   - only for the k6 path (default http://localhost:8000)
#
# Usage:
#   bash tests/perf/scripts/seed.sh
#   BACKEND_URL=https://staging.example.com bash tests/perf/scripts/seed.sh

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/../../.." && pwd)"
SEED_PY="$REPO_ROOT/scripts/seed_team.py"

if [[ -f "$SEED_PY" && -n "${DATABASE_URL:-}" ]]; then
  echo "[seed] Running backend seed_team.py against $DATABASE_URL"
  (cd "$REPO_ROOT" && PYTHONPATH=. python "$SEED_PY")
  echo "[seed] Done (DB seed)."
  exit 0
fi

if command -v k6 >/dev/null 2>&1; then
  echo "[seed] Falling back to k6 HTTP seeder (BACKEND_URL=${BACKEND_URL:-http://localhost:8000})"
  k6 run "$HERE/seed_perf.js"
  echo "[seed] Done (HTTP seed)."
  exit 0
fi

echo "[seed] Neither DATABASE_URL+seed_team.py nor k6 are available." >&2
echo "[seed] Install k6 (https://k6.io/docs/get-started/installation/)" >&2
echo "[seed] or set DATABASE_URL and run: PYTHONPATH=. python scripts/seed_team.py" >&2
exit 1
