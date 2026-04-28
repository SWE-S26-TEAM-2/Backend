// Spike scenario: 0 -> 1000 VUs in 30 seconds, slamming the login + landing
// endpoints. This validates the rate limiter on /auth/login (service-layer
// limit, see app/services/auth_service.py) and the cost of CORS preflights
// + uvicorn accept queue.
//
// Thresholds:
//   - 429s are acceptable (rate limit firing is the expected protective
//     behaviour and is what we want to confirm).
//   - 5xx must be < 5%.
//   - Anything 0 (timeout, connection refused) counts as 5xx for the SLO.

import http from 'k6/http';
import { Rate } from 'k6/metrics';
import { sleep } from 'k6';

import { BASE, TEST_USER, jsonHeaders } from '../lib/config.js';

const fiveXxOrTimeout = new Rate('fivexx_or_timeout');
const tooManyRequests = new Rate('too_many_requests');

export const options = {
  scenarios: {
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 1000 },
        { duration: '1m', target: 1000 },
        { duration: '30s', target: 0 },
      ],
      gracefulRampDown: '10s',
      exec: 'execSpike',
    },
  },
  thresholds: {
    'fivexx_or_timeout': ['rate<0.05'],
    // Informational only - we want to see this go non-zero.
    'too_many_requests': ['rate>=0'],
  },
};

export function execSpike() {
  // Pick login or landing roughly 70/30 - login is the hot target.
  if (Math.random() < 0.7) {
    const res = http.post(
      `${BASE}/auth/login`,
      JSON.stringify({
        identifier: TEST_USER.email,
        password: TEST_USER.password,
      }),
      { headers: jsonHeaders(), tags: { endpoint: 'auth_login' } },
    );
    fiveXxOrTimeout.add(res.status === 0 || res.status >= 500);
    tooManyRequests.add(res.status === 429);
  } else {
    const res = http.get(`${BASE}/`, {
      headers: jsonHeaders(),
      tags: { endpoint: 'landing' },
    });
    fiveXxOrTimeout.add(res.status === 0 || res.status >= 500);
  }
  sleep(0.05);
}
