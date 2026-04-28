// Smoke scenario: 1 VU x 1 minute, runs every journey once.
// This is the gate that runs in CI on every push.
//
// Thresholds:
//   - http_req_failed < 1%
//   - http_req_duration p95 < 1500ms
//
// Run:
//   k6 run tests/perf/scenarios/smoke.js
//   BACKEND_URL=http://staging:8000 k6 run tests/perf/scenarios/smoke.js

import { sleep } from 'k6';

import { setupTestUser } from '../lib/auth.js';
import {
  journey_listener,
  journey_creator,
  journey_social,
  journey_browse_anon,
} from '../lib/journeys.js';

export const options = {
  vus: 1,
  duration: '1m',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1500'],
    'http_req_duration{endpoint:auth_login}': ['p(95)<2000'],
    'http_req_duration{step:stream_chunk}': ['p(95)<1500'],
  },
  // Tag every request with the scenario name so we can slice metrics later.
  tags: { scenario: 'smoke' },
};

export function setup() {
  return { ts: Date.now() };
}

export default function () {
  const session = setupTestUser();
  journey_browse_anon();
  sleep(0.5);
  journey_listener(session);
  sleep(0.5);
  journey_creator(session);
  sleep(0.5);
  journey_social(session);
  sleep(0.5);
}

export function teardown(data) {
  // No global state to clean. Print a marker so CI logs show end of run.
  console.log(`smoke teardown: setup_ts=${data.ts}`);
}
