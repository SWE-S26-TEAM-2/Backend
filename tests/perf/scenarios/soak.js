// Soak scenario: 100 VUs constant for 2 hours.
//
// The goal is to detect leaks: refresh token table growth, file handles
// from the audio streamer, DB connection pool starvation, and slow memory
// creep. We don't measure memory from k6 directly; instead, we use a
// "memory-stable proxy" - if the error rate stays under 1% for the full
// 2h window, we assume no catastrophic resource leak occurred. Pair this
// run with backend-side metrics (Datadog / prometheus) for the real
// memory-stable signal.

import { sleep } from 'k6';

import { setupTestUser } from '../lib/auth.js';
import {
  journey_listener,
  journey_browse_anon,
  journey_social,
} from '../lib/journeys.js';

export const options = {
  scenarios: {
    soak: {
      executor: 'constant-vus',
      vus: 100,
      duration: '2h',
      exec: 'execSoak',
    },
  },
  thresholds: {
    // Error rate < 1% throughout. If anything breaks the SLO during the
    // 2h, the run fails so the regression is obvious in CI.
    'http_req_failed': ['rate<0.01'],
    // Sanity: keep p99 reasonable so a slow leak that manifests as
    // latency creep also fails the run.
    'http_req_duration': ['p(99)<3000'],
  },
};

export function execSoak() {
  // Mostly reads to avoid filling the DB during a 2h run.
  const r = Math.random();
  if (r < 0.7) {
    journey_browse_anon();
  } else if (r < 0.95) {
    const session = setupTestUser();
    journey_listener(session);
  } else {
    const session = setupTestUser();
    journey_social(session);
  }
  // Slow loop - we want sustained light pressure, not a hammer.
  sleep(1 + Math.random() * 2);
}
