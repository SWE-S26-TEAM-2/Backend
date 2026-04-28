# Backend Performance Tests (k6)

Performance and load tests for the SoundCloud-clone FastAPI backend, written
in [k6](https://k6.io). Co-located with backend code so the same repo can run
a smoke scenario in CI and longer scenarios on demand.

## Layout

```
tests/perf/
  README.md                 # this file
  lib/
    config.js               # env vars + base URL + header helpers
    auth.js                 # register/login helpers + setupTestUser
    journeys.js             # 4 reusable user journeys
  scenarios/
    smoke.js                # 1 VU x 1 min, runs all 4 journeys once
    load.js                 # 50 VU x 10 min, weighted scenarios block
    stress.js               # ramp 0->500 VU x 15 min on hot reads
    spike.js                # 0 -> 1000 VU in 30s on /auth/login + /
    soak.js                 # 100 VU constant x 2h (memory-stable proxy)
    streaming.js            # 200 VU x 30 min, Range chunks
    chat.js                 # constant-arrival-rate, ~2000 msg/min
  scripts/
    seed.sh                 # wrapper that calls scripts/seed_team.py
    seed_perf.js            # k6 setup-style seeder (users + tracks)
```

## Prerequisites

1. **k6 installed locally** (`brew install k6` on macOS, see
   [k6 install docs](https://k6.io/docs/get-started/installation/)).
2. **Backend running.** Either:
   - `uvicorn app.main:app --host 0.0.0.0 --port 8000` from the
     `Backend/` directory, or
   - Docker: `docker build -t backend:test . && docker run -p 8000:8000 backend:test`
3. **Database reachable** by the backend (`DATABASE_URL` env var).
4. **Seed data** loaded so `/search/tracks` and `/tracks/{id}/audio` return
   real rows. See [Seeding](#seeding).

## Environment variables

All scripts read from `lib/config.js`:

| Var               | Default                  | Notes                                        |
|-------------------|--------------------------|----------------------------------------------|
| `BACKEND_URL`     | `http://localhost:8000`  | Base URL, no trailing slash                  |
| `VUS`             | scenario default         | Override default VUs                         |
| `DURATION`        | scenario default         | Override default duration (e.g. `30s`)       |
| `TEST_USER_EMAIL` | `perf+seed@soundwave.dev`| Pre-seeded shared user                       |
| `TEST_USER_PASSWORD` | `SoundWave@2026`      | Matches `scripts/seed_team.py`               |
| `TEST_USERNAME`   | `perfseed`               | Pre-seeded username                          |
| `SEED_TRACK_ID`   | `1`                      | Track id used by streaming/journey scenarios |
| `STREAM_CHUNK`    | `262144`                 | 256 KiB Range chunk size                     |
| `K6_OUT`          | -                        | k6 output (e.g. `json=summary.json`)         |

## Running

From the `Backend/` repo root:

```bash
k6 run tests/perf/scenarios/smoke.js
k6 run --vus 50 --duration 10m tests/perf/scenarios/load.js
BACKEND_URL=https://staging.example.com k6 run tests/perf/scenarios/stress.js
k6 run --summary-export=summary.json tests/perf/scenarios/spike.js
```

Most scenarios use a `scenarios:` block, so `--vus`/`--duration` only override
when the file does not declare its own scenarios. `smoke.js` honors them.

## Seeding

Two options:

1. **Use the existing backend seeder.** From `Backend/`:

   ```bash
   PYTHONPATH=. python scripts/seed_team.py
   ```

   Then create one extra perf user and a few tracks via the API (the
   k6 helper script can do this).

2. **Use the k6-native seeder** (preferred for CI):

   ```bash
   k6 run tests/perf/scripts/seed_perf.js
   ```

   It calls `POST /auth/register`, then either uses a verification backdoor
   (`VERIFICATION_BACKDOOR=1`) or skips verification if the test backend
   has it disabled, and uploads a small placeholder audio file via
   `POST /tracks/`.

3. **Helper shell wrapper** for CI:

   ```bash
   bash tests/perf/scripts/seed.sh
   ```

## Thresholds

Each scenario defines its own `thresholds:` block (see the per-scenario file).
Summary:

| Scenario     | Headline thresholds                                  |
|--------------|------------------------------------------------------|
| `smoke`      | `http_req_failed < 1%`, `http_req_duration p95 < 1500ms` |
| `load`       | `p95 GET < 300ms`, `p99 < 1000ms`, error rate < 1%   |
| `stress`     | error rate < 5% before VUs hit 300                   |
| `spike`      | 5xx < 5% (429s expected and tolerated)               |
| `soak`       | error rate < 1% throughout (memory-stable proxy)     |
| `streaming`  | bytes/s tracked, 5xx < 1%, 206 share > 95%           |
| `chat`       | dropped requests < 1%, p95 send < 800ms              |

## CI

`smoke.js` runs on every push via
[`.github/workflows/perf-smoke.yml`](../../.github/workflows/perf-smoke.yml).
Long scenarios (`load`, `stress`, `spike`, `soak`, `streaming`, `chat`) are
gated behind `workflow_dispatch` only - they are not free.

## Failure modes the scenarios are designed to expose

- Login storm exhausts bcrypt CPU or hits `/auth/login` rate limiter.
- `/tracks/{id}/audio` Range read with high concurrency saturates uvicorn
  workers or local disk.
- `/search/tracks?keyword=` against an unindexed `ILIKE` plan.
- Refresh token table growth during 2h soak.
- Conversations / messages contention with the unique-constraint on
  `(conversation_id, message_id)`.
