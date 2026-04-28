// Reusable user journeys for k6 scenarios. Each journey is exported as a
// function that returns nothing; metrics are emitted via k6 http checks.
//
// All journeys are best-effort: if a precondition (seeded data, mounted
// router) is missing, the journey logs and continues so load tests don't
// crash on a single 404.

import http from 'k6/http';
import { check, sleep } from 'k6';

import { BASE, SEED, FLAGS, jsonHeaders, authHeaders, rangeHeaders } from './config.js';
import { login, setupTestUser } from './auth.js';

// Small sleep helper that scales with random jitter to avoid lockstep.
function jitter(min = 0.2, max = 1.0) {
  sleep(min + Math.random() * (max - min));
}

// 1) Listener journey
//    feed -> search -> open track -> stream chunk -> POST plays -> like
export function journey_listener(session) {
  if (!session) {
    session = setupTestUser();
  }
  const headers = session ? authHeaders(session.accessToken) : jsonHeaders();

  // a) Feed-ish: GET /  (root) and recently-played for authenticated user.
  http.get(`${BASE}/`, { headers, tags: { journey: 'listener', step: 'feed' } });
  if (session) {
    http.get(`${BASE}/users/me/recently-played?limit=20`, {
      headers,
      tags: { journey: 'listener', step: 'recently_played' },
    });
  }
  jitter();

  // b) Search for a keyword we know is seeded.
  const search = http.get(
    `${BASE}/search/tracks?keyword=${encodeURIComponent(SEED.searchKeyword)}`,
    { headers, tags: { journey: 'listener', step: 'search' } },
  );
  check(search, { 'search 200': (r) => r.status === 200 });

  // Pick a track id from search if possible, otherwise fall back to seed.
  let trackId = SEED.trackId;
  try {
    const items = search.json();
    if (Array.isArray(items) && items.length > 0 && items[0].id) {
      trackId = items[0].id;
    } else if (items && Array.isArray(items.results) && items.results.length > 0) {
      trackId = items.results[0].id;
    }
  } catch (_) {
    // ignore parse errors, keep fallback
  }

  // c) Open the track detail.
  http.get(`${BASE}/tracks/${trackId}`, {
    headers,
    tags: { journey: 'listener', step: 'open_track' },
  });
  jitter();

  // d) Stream a single chunk via Range header.
  const chunk = SEED.streamChunk;
  const stream = http.get(`${BASE}/tracks/${trackId}/audio`, {
    headers: { ...headers, ...rangeHeaders(0, chunk - 1) },
    tags: { journey: 'listener', step: 'stream_chunk' },
  });
  check(stream, { 'stream 206 or 200': (r) => r.status === 206 || r.status === 200 });

  // e) Record a play.
  http.post(
    `${BASE}/tracks/${trackId}/plays`,
    JSON.stringify({ progress_seconds: 30 }),
    { headers, tags: { journey: 'listener', step: 'record_play' } },
  );

  // f) Optional: like the track. The engagement router is gated by a flag.
  if (FLAGS.engagementMounted && session) {
    const like = http.post(
      `${BASE}/tracks/${trackId}/like`,
      null,
      { headers, tags: { journey: 'listener', step: 'like' } },
    );
    check(like, {
      'like 200/201/409': (r) => [200, 201, 409].includes(r.status),
    });
  }
}

// 2) Creator journey
//    login -> upload track (multipart) -> create playlist -> add track
export function journey_creator(session) {
  if (!session) session = setupTestUser();
  if (!session) return; // no auth, skip

  // a) Build a tiny dummy audio payload (~2 KiB of silence-ish bytes).
  // We can't easily ship an mp3 from k6 without binary fixtures; we fake
  // the multipart so the route is exercised even if the service rejects
  // the file content. The server's size + type checks should still run.
  const audioBlob = http.file(
    new Uint8Array(2048).buffer, 'sample.mp3', 'audio/mpeg',
  );
  const cover = http.file(
    new Uint8Array(1024).buffer, 'cover.jpg', 'image/jpeg',
  );

  const uploadRes = http.post(
    `${BASE}/tracks/`,
    {
      title: `perf-${Date.now()}-${Math.floor(Math.random() * 1e6)}`,
      description: 'perf test track',
      audio_file: audioBlob,
      cover_image: cover,
    },
    {
      headers: { Authorization: `Bearer ${session.accessToken}` },
      tags: { journey: 'creator', step: 'upload' },
    },
  );
  // 200/201 happy, 4xx if validation rejects fake bytes - both acceptable
  // signals for perf, since the request did real I/O server-side.
  check(uploadRes, { 'upload reached server': (r) => r.status > 0 });
  let newTrackId = null;
  try {
    newTrackId = uploadRes.json('id');
  } catch (_) { /* ignore */ }

  // b) Create a playlist.
  const plist = http.post(
    `${BASE}/playlists/`,
    JSON.stringify({
      title: `perf-pl-${Date.now()}`,
      description: 'perf',
      is_public: true,
    }),
    {
      headers: authHeaders(session.accessToken),
      tags: { journey: 'creator', step: 'create_playlist' },
    },
  );
  check(plist, { 'playlist created': (r) => [200, 201].includes(r.status) });
  let playlistId = null;
  try { playlistId = plist.json('id'); } catch (_) { /* ignore */ }

  // c) Add a track to the playlist.
  const trackToAdd = newTrackId || SEED.trackId;
  if (playlistId) {
    http.post(
      `${BASE}/playlists/${playlistId}/tracks`,
      JSON.stringify({ track_id: trackToAdd }),
      {
        headers: authHeaders(session.accessToken),
        tags: { journey: 'creator', step: 'add_track' },
      },
    );
  }
}

// 3) Social journey
//    open profile -> follow -> message -> view notifications
export function journey_social(session) {
  if (!session) session = setupTestUser();
  if (!session) return;

  const headers = authHeaders(session.accessToken);

  // a) Open another user's profile.
  const other = SEED.otherUsername;
  http.get(`${BASE}/users/${other}`, {
    headers,
    tags: { journey: 'social', step: 'profile' },
  });
  jitter();

  // b) Follow them (idempotent: 409 fine).
  const follow = http.post(`${BASE}/users/${other}/follow`, null, {
    headers,
    tags: { journey: 'social', step: 'follow' },
  });
  check(follow, { 'follow ok or already': (r) => [200, 201, 409].includes(r.status) });

  // c) Create a conversation + send a message.
  const conv = http.post(
    `${BASE}/conversations`,
    JSON.stringify({ participant_username: other }),
    { headers, tags: { journey: 'social', step: 'create_conversation' } },
  );
  let convId = null;
  try { convId = conv.json('id'); } catch (_) { /* ignore */ }
  if (convId) {
    http.post(
      `${BASE}/conversations/${convId}/messages`,
      JSON.stringify({ content: `perf hello ${Date.now()}` }),
      { headers, tags: { journey: 'social', step: 'send_message' } },
    );
  }

  // d) View notifications.
  http.get(`${BASE}/notifications?limit=20&offset=0`, {
    headers,
    tags: { journey: 'social', step: 'notifications' },
  });
  http.get(`${BASE}/notifications/unread-count`, {
    headers,
    tags: { journey: 'social', step: 'unread_count' },
  });
}

// 4) Anonymous browse
//    GET / -> GET /search/tracks?keyword= -> GET /tracks/{id}
export function journey_browse_anon() {
  const headers = jsonHeaders();
  http.get(`${BASE}/`, { headers, tags: { journey: 'anon', step: 'root' } });
  jitter();
  http.get(
    `${BASE}/search/tracks?keyword=${encodeURIComponent(SEED.searchKeyword)}`,
    { headers, tags: { journey: 'anon', step: 'search' } },
  );
  http.get(`${BASE}/tracks/${SEED.trackId}`, {
    headers,
    tags: { journey: 'anon', step: 'open_track' },
  });
}
