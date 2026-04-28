// Authentication helpers for k6 perf scenarios.
// Backend routes used (from STEP 2 of the audit plan):
//   POST /auth/register
//   POST /auth/verify-email
//   POST /auth/login
//   POST /auth/logout (auth required)

import http from 'k6/http';
import { check, fail } from 'k6';

import { BASE, TEST_USER, FLAGS, jsonHeaders, authHeaders } from './config.js';

// Register a new user. Returns the response body parsed.
// Idempotent-ish: a 409/400 (already exists) is treated as success so the
// same seed user can be reused across runs.
export function register({ email, password, username, displayName } = {}) {
  const body = JSON.stringify({
    email: email,
    password: password,
    username: username,
    display_name: displayName || username,
  });
  const res = http.post(`${BASE}/auth/register`, body, {
    headers: jsonHeaders(),
    tags: { endpoint: 'auth_register' },
  });
  const ok = check(res, {
    'register accepted (200/201/409)': (r) => [200, 201, 409, 400].includes(r.status),
  });
  if (!ok) {
    // Don't fail the whole VU iteration in load tests; return null so the
    // caller can decide. In smoke.js we explicitly assert success.
    return null;
  }
  return res;
}

// Verify the email of a freshly-registered account if a backdoor is enabled.
// Real systems require a token from the verification email; we don't poll
// SMTP from k6. If `VERIFICATION_BACKDOOR=true` is set, callers can supply
// a token (e.g. derived from a fixed dev seed) via env.
export function verifyEmail(token) {
  if (!FLAGS.verificationBackdoor) return null;
  const res = http.post(
    `${BASE}/auth/verify-email`,
    JSON.stringify({ token }),
    { headers: jsonHeaders(), tags: { endpoint: 'auth_verify' } },
  );
  return res;
}

// Login. Returns { accessToken, refreshToken, raw } or null on failure.
export function login({ identifier, password } = {}) {
  const body = JSON.stringify({ identifier, password });
  const res = http.post(`${BASE}/auth/login`, body, {
    headers: jsonHeaders(),
    tags: { endpoint: 'auth_login' },
  });
  const ok = check(res, {
    'login 200': (r) => r.status === 200,
    'login has access_token': (r) => {
      try {
        return !!r.json('access_token');
      } catch (_) {
        return false;
      }
    },
  });
  if (!ok) {
    return null;
  }
  return {
    accessToken: res.json('access_token'),
    refreshToken: res.json('refresh_token'),
    raw: res,
  };
}

// Convenience: in setup() blocks we want one shared seed user.
// If login fails (user not yet seeded), this returns null so the scenario
// can decide to skip writes.
export function setupTestUser() {
  const session = login({
    identifier: TEST_USER.email,
    password: TEST_USER.password,
  });
  if (!session) {
    // Try register-then-login. Best-effort; in CI the seeder should have
    // run already.
    register({
      email: TEST_USER.email,
      password: TEST_USER.password,
      username: TEST_USER.username,
    });
    const retry = login({
      identifier: TEST_USER.email,
      password: TEST_USER.password,
    });
    return retry; // may still be null if email verification is enforced
  }
  return session;
}

// Logout - revokes refresh token server-side.
export function logout(accessToken, refreshToken) {
  const res = http.post(
    `${BASE}/auth/logout`,
    JSON.stringify({ refresh_token: refreshToken }),
    { headers: authHeaders(accessToken), tags: { endpoint: 'auth_logout' } },
  );
  return res;
}

// Hard fail used only in smoke (where any auth failure aborts the run).
export function mustLogin(creds) {
  const session = login(creds);
  if (!session) fail(`mustLogin failed for ${creds.identifier}`);
  return session;
}
