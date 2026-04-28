// Chat scenario: 500 conversations seeded in setup(), then 2000 messages
// per minute via `constant-arrival-rate`. Validates write throughput on
// `POST /conversations/{id}/messages` and read-marker idempotency under
// contention.
//
// SLOs:
//   - dropped_iterations < 1% (i.e. arrival rate is sustainable)
//   - p95 message send < 800 ms

import http from 'k6/http';
import { Rate } from 'k6/metrics';
import { sleep } from 'k6';

import { BASE, SEED, authHeaders } from '../lib/config.js';
import { setupTestUser } from '../lib/auth.js';

const sendOk = new Rate('chat_send_ok');

export const options = {
  scenarios: {
    chat: {
      executor: 'constant-arrival-rate',
      // 2000 msgs/min == ~33.33/s. Round to 33.
      rate: 33,
      timeUnit: '1s',
      duration: '15m',
      preAllocatedVUs: 100,
      maxVUs: 500,
      exec: 'sendMessage',
    },
  },
  thresholds: {
    'http_req_failed{endpoint:send_message}': ['rate<0.01'],
    'http_req_duration{endpoint:send_message}': ['p(95)<800'],
    'chat_send_ok': ['rate>0.99'],
    'dropped_iterations': ['rate<0.01'],
  },
};

// setup() runs once and creates 500 conversations. Each VU iteration in the
// scenario picks a conversation id at random and posts a message.
export function setup() {
  const session = setupTestUser();
  if (!session) {
    console.warn('chat setup: no auth session; will run with empty conv list');
    return { convIds: [], headers: null };
  }
  const headers = authHeaders(session.accessToken);
  const convIds = [];
  // Create ~500 conversations against the seeded "other" user. If the
  // backend reuses the same conversation per (user_a, user_b) pair, we
  // fall back to whichever id it returned (so the array is just the same
  // id 500 times - still fine for write contention).
  const target = 500;
  for (let i = 0; i < target; i++) {
    const res = http.post(
      `${BASE}/conversations`,
      JSON.stringify({ participant_username: SEED.otherUsername }),
      { headers, tags: { endpoint: 'create_conv' } },
    );
    let id = null;
    try { id = res.json('id'); } catch (_) { /* ignore */ }
    if (id) convIds.push(id);
    if (convIds.length === 0 && i > 5) {
      // No conversations got created; bail to avoid 500x retries.
      console.warn('chat setup: cannot create conversations, aborting seed');
      break;
    }
  }
  return { convIds, accessToken: session.accessToken };
}

export function sendMessage(data) {
  if (!data || !data.accessToken || !data.convIds.length) {
    sendOk.add(false);
    return;
  }
  const id = data.convIds[Math.floor(Math.random() * data.convIds.length)];
  const res = http.post(
    `${BASE}/conversations/${id}/messages`,
    JSON.stringify({ content: `m-${Date.now()}-${__VU}-${__ITER}` }),
    {
      headers: authHeaders(data.accessToken),
      tags: { endpoint: 'send_message' },
    },
  );
  sendOk.add(res.status >= 200 && res.status < 300);

  // Every 10 messages, mark all read - tests the read-marker idempotency
  // under contention.
  if (__ITER % 10 === 0) {
    http.patch(
      `${BASE}/conversations/${id}/messages/read-all`,
      null,
      {
        headers: authHeaders(data.accessToken),
        tags: { endpoint: 'read_all' },
      },
    );
  }
  sleep(0.01);
}
