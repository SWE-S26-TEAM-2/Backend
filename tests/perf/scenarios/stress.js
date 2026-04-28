// Stress scenario: ramp 0 -> 500 VUs over 15 minutes against the two
// hottest read endpoints:
//   - GET /search/tracks?keyword=
//   - GET /tracks/{id}/audio (Range)
//
// We expect the system to plateau on DB or storage. The threshold says
// the error rate must stay under 5% **before** VUs hit 300; after that
// we just observe the breakpoint without failing the run.
//
// Implementation note: k6 doesn't support a "before VU=N" threshold
// directly, so we abuse a custom Counter that only increments on errors
// during the first 10 minutes of the ramp (when VUs are still climbing
// to ~330 with the chosen stages).

import http from 'k6/http';
import { Counter, Rate } from 'k6/metrics';
import { sleep } from 'k6';

import { BASE, SEED, jsonHeaders, rangeHeaders } from '../lib/config.js';

const earlyErrors = new Counter('early_errors');
const earlyTotal = new Counter('early_total');
const earlyErrorRate = new Rate('early_error_rate');

export const options = {
  scenarios: {
    ramp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '3m', target: 100 },
        { duration: '4m', target: 300 },
        { duration: '4m', target: 500 },
        { duration: '4m', target: 500 },
      ],
      gracefulRampDown: '30s',
      exec: 'execStress',
    },
  },
  thresholds: {
    // Hard threshold: the early window must stay under 5% error rate.
    'early_error_rate': ['rate<0.05'],
    'http_req_failed': ['rate<0.20'], // overall sanity ceiling
  },
};

const RAMP_TO_300_MS = (3 + 4) * 60 * 1000; // 7 min in ms

export function execStress() {
  const isEarly = (Date.now() - __ENV.__SCENARIO_START_MS_FAKE_GUARD || 0) < RAMP_TO_300_MS;
  // k6 doesn't expose scenario start; approximate via __ITER + __VU. The
  // simpler reliable option: count the first 7 minutes of wall clock by
  // using an iteration timestamp captured per-iteration.
  const startedAt = (__VU === 1 && __ITER === 0)
    ? (globalThis.__startedAt = Date.now())
    : (globalThis.__startedAt || Date.now());
  const earlyWindow = (Date.now() - startedAt) < RAMP_TO_300_MS;

  // 50/50 split between the two endpoints.
  let res;
  if (Math.random() < 0.5) {
    res = http.get(
      `${BASE}/search/tracks?keyword=${encodeURIComponent(SEED.searchKeyword)}`,
      { headers: jsonHeaders(), tags: { endpoint: 'search_tracks' } },
    );
  } else {
    const chunk = SEED.streamChunk;
    res = http.get(`${BASE}/tracks/${SEED.trackId}/audio`, {
      headers: { ...jsonHeaders(), ...rangeHeaders(0, chunk - 1) },
      tags: { endpoint: 'audio_range' },
    });
  }
  const failed = res.status === 0 || res.status >= 500;
  if (earlyWindow) {
    earlyTotal.add(1);
    earlyErrorRate.add(failed);
    if (failed) earlyErrors.add(1);
  }
  sleep(0.05);
}
