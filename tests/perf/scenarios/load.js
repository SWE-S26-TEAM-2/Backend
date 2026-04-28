// Load scenario: 50 VUs steady, 10 minutes, mixed realistic traffic.
// Mix:
//   - 70% reads (browse anon + listener feed/search/open)
//   - 20% playback (listener stream chunk loop)
//   - 10% writes (creator + social writes)
//
// Implemented via k6 `scenarios:` block with weighted exec functions sharing
// the same time window. Each exec gets its own VU pool, so the weights are
// expressed as VU counts that sum to 50.
//
// SLOs:
//   - p95 GET < 300 ms
//   - p99 < 1000 ms
//   - error rate < 1%

import http from 'k6/http';
import { sleep } from 'k6';

import { BASE, SEED, jsonHeaders, rangeHeaders } from '../lib/config.js';
import { setupTestUser } from '../lib/auth.js';
import {
  journey_listener,
  journey_creator,
  journey_social,
  journey_browse_anon,
} from '../lib/journeys.js';

export const options = {
  scenarios: {
    // 70% reads = 35 VUs
    reads: {
      executor: 'constant-vus',
      vus: 35,
      duration: '10m',
      exec: 'execReads',
      tags: { mix: 'reads' },
    },
    // 20% playback = 10 VUs continuously hitting Range
    playback: {
      executor: 'constant-vus',
      vus: 10,
      duration: '10m',
      exec: 'execPlayback',
      tags: { mix: 'playback' },
    },
    // 10% writes = 5 VUs
    writes: {
      executor: 'constant-vus',
      vus: 5,
      duration: '10m',
      exec: 'execWrites',
      tags: { mix: 'writes' },
    },
  },
  thresholds: {
    'http_req_failed': ['rate<0.01'],
    'http_req_duration{mix:reads}': ['p(95)<300', 'p(99)<1000'],
    'http_req_duration{mix:playback}': ['p(95)<800'],
    'http_req_duration{mix:writes}': ['p(95)<1500'],
    'http_reqs{mix:reads}': ['count>0'],
  },
};

export function execReads() {
  // Half listener (auth-aware), half anonymous browse.
  if (Math.random() < 0.5) {
    journey_browse_anon();
  } else {
    const session = setupTestUser();
    journey_listener(session);
  }
  sleep(Math.random() * 2);
}

export function execPlayback() {
  // Tight stream chunk loop. Each VU walks Range windows over the seed
  // track to simulate continuous playback.
  const headers = { ...jsonHeaders() };
  const chunk = SEED.streamChunk;
  let offset = 0;
  for (let i = 0; i < 5; i++) {
    const res = http.get(`${BASE}/tracks/${SEED.trackId}/audio`, {
      headers: { ...headers, ...rangeHeaders(offset, offset + chunk - 1) },
      tags: { mix: 'playback', step: 'stream_chunk' },
    });
    if (res.status === 416) break; // past EOF, restart
    offset += chunk;
    sleep(0.1);
  }
  // Record one play per iteration to emulate real client behaviour.
  http.post(
    `${BASE}/tracks/${SEED.trackId}/plays`,
    JSON.stringify({ progress_seconds: 30 }),
    { headers, tags: { mix: 'playback', step: 'plays' } },
  );
}

export function execWrites() {
  const session = setupTestUser();
  // Even split between creator and social writes.
  if (Math.random() < 0.5) {
    journey_creator(session);
  } else {
    journey_social(session);
  }
  sleep(Math.random() * 3);
}
