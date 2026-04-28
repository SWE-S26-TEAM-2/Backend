// k6-native seeder for perf tests. Creates the shared perf user and a
// handful of "other" users + tracks so journeys have data to operate on.
//
// Run:
//   k6 run tests/perf/scripts/seed_perf.js
//
// This script is best-effort: 4xx on already-existing rows is fine.

import http from 'k6/http';
import { check } from 'k6';

import { BASE, TEST_USER, FLAGS, jsonHeaders } from '../lib/config.js';

export const options = {
  vus: 1,
  iterations: 1,
  thresholds: {
    // Don't fail the seed run on individual 4xx; it's idempotent on
    // re-seeds.
    'http_req_failed': ['rate<0.5'],
  },
};

const OTHERS = [
  { username: 'mostafayasser', email: 'mostafa.yasser@soundwave.com' },
  { username: 'mohamedkhaled', email: 'mohamed.khaled@soundwave.com' },
  { username: 'amiraelwakeel', email: 'amira.elwakeel@soundwave.com' },
];

function tryRegister(u) {
  const body = JSON.stringify({
    email: u.email,
    password: TEST_USER.password,
    username: u.username,
    display_name: u.username,
  });
  const r = http.post(`${BASE}/auth/register`, body, { headers: jsonHeaders() });
  check(r, {
    [`register ${u.username} accepted`]: (res) =>
      [200, 201, 409, 400].includes(res.status),
  });
  return r;
}

export default function () {
  console.log(`Seeding against ${BASE}`);
  console.log(`Engagement mounted: ${FLAGS.engagementMounted}`);

  // Perf user.
  tryRegister({ email: TEST_USER.email, username: TEST_USER.username });
  for (const o of OTHERS) tryRegister(o);

  // Login as perf user.
  const login = http.post(
    `${BASE}/auth/login`,
    JSON.stringify({ identifier: TEST_USER.email, password: TEST_USER.password }),
    { headers: jsonHeaders() },
  );
  if (login.status !== 200) {
    console.warn(`perf login failed: ${login.status} ${login.body}`);
    console.warn('If email verification is enforced, set VERIFICATION_BACKDOOR=true');
    console.warn('or run scripts/seed_team.py against the same DB.');
    return;
  }
  const token = login.json('access_token');
  console.log('Perf user logged in.');

  // Upload a couple of placeholder tracks so SEED_TRACK_ID actually
  // resolves to a real row. Send fake bytes - the server will exercise
  // its multipart pipeline.
  for (let i = 0; i < 3; i++) {
    const audio = http.file(new Uint8Array(2048).buffer, `seed-${i}.mp3`, 'audio/mpeg');
    const cover = http.file(new Uint8Array(1024).buffer, `seed-${i}.jpg`, 'image/jpeg');
    const r = http.post(
      `${BASE}/tracks/`,
      {
        title: `seed track ${i} ${Date.now()}`,
        description: 'perf seed',
        audio_file: audio,
        cover_image: cover,
      },
      { headers: { Authorization: `Bearer ${token}` } },
    );
    console.log(`Seed track ${i}: status=${r.status}`);
  }
  console.log('Seed complete.');
}
