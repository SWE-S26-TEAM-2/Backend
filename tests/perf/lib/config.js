// Shared configuration for k6 perf scenarios.
// All values come from environment variables so the same scripts can run
// against localhost, a docker-compose stack, or a staging deployment.

const env = (typeof __ENV !== 'undefined') ? __ENV : {};

function trimRight(str, ch) {
  while (str && str.length > 0 && str[str.length - 1] === ch) {
    str = str.slice(0, -1);
  }
  return str;
}

export const BASE = trimRight(env.BACKEND_URL || 'http://localhost:8000', '/');

export const VUS = parseInt(env.VUS || '0', 10) || undefined;
export const DURATION = env.DURATION || undefined;

export const TEST_USER = {
  email: env.TEST_USER_EMAIL || 'perf+seed@soundwave.dev',
  password: env.TEST_USER_PASSWORD || 'SoundWave@2026',
  username: env.TEST_USERNAME || 'perfseed',
};

export const SEED = {
  trackId: env.SEED_TRACK_ID || '1',
  playlistId: env.SEED_PLAYLIST_ID || '1',
  otherUsername: env.SEED_OTHER_USERNAME || 'mostafayasser',
  searchKeyword: env.SEED_SEARCH || 'test',
  streamChunk: parseInt(env.STREAM_CHUNK || '262144', 10),
};

export const FLAGS = {
  // The engagement router (likes/reposts/comments) is not always mounted
  // in app/main.py. Journeys must skip it gracefully when missing.
  engagementMounted: (env.ENGAGEMENT_MOUNTED || 'false').toLowerCase() === 'true',
  // If your test backend exposes a verification backdoor, set this so
  // the seeder can auto-verify perf users without an SMTP round-trip.
  verificationBackdoor: (env.VERIFICATION_BACKDOOR || 'false').toLowerCase() === 'true',
};

// Default headers used by JSON requests.
export const jsonHeaders = () => ({
  'Content-Type': 'application/json',
  'Accept': 'application/json',
});

// Authenticated headers; pass the bearer token returned by login().
export const authHeaders = (token, extra = {}) => ({
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Authorization': `Bearer ${token}`,
  ...extra,
});

// Range header for audio streaming chunks. Returns Header object.
export const rangeHeaders = (start, end) => ({
  'Range': `bytes=${start}-${end}`,
});

// Tag helper: every request carries a "scenario" tag so thresholds in
// load.js and friends can be scoped per exec function.
export const tag = (name) => ({ tags: { exec: name } });
