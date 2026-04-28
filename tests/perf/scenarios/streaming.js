// Streaming scenario: 200 VUs for 30 minutes, all VUs continuously fetching
// `/tracks/{id}/audio` with Range headers. Walks `bytes=N-N+CHUNK` windows
// to emulate real player chunk reads and resumes from offset.
//
// Tracks:
//   - bytes_received_total (built-in `data_received`)
//   - 206 vs 200 vs 5xx ratio
//   - p95 first-byte latency (http_req_waiting)

import http from 'k6/http';
import { Counter, Rate } from 'k6/metrics';
import { sleep } from 'k6';

import { BASE, SEED, jsonHeaders, rangeHeaders } from '../lib/config.js';

const partial206 = new Rate('partial_content_206');
const fivexx = new Rate('stream_5xx');
const bytes = new Counter('stream_bytes_total');

export const options = {
  scenarios: {
    streaming: {
      executor: 'constant-vus',
      vus: 200,
      duration: '30m',
      exec: 'execStream',
    },
  },
  thresholds: {
    'partial_content_206': ['rate>0.95'],
    'stream_5xx': ['rate<0.01'],
    'http_req_waiting{endpoint:audio_range}': ['p(95)<800'],
  },
};

export function execStream() {
  const chunk = SEED.streamChunk;
  // Each VU walks 12 chunks (~3 MiB) per iteration.
  let offset = 0;
  for (let i = 0; i < 12; i++) {
    const res = http.get(`${BASE}/tracks/${SEED.trackId}/audio`, {
      headers: { ...jsonHeaders(), ...rangeHeaders(offset, offset + chunk - 1) },
      tags: { endpoint: 'audio_range' },
    });
    partial206.add(res.status === 206);
    fivexx.add(res.status >= 500);
    if (res.body && res.body.length) {
      bytes.add(res.body.length);
    }
    if (res.status === 416) {
      // EOF - restart from 0 next iteration.
      break;
    }
    offset += chunk;
    sleep(0.05);
  }
}
