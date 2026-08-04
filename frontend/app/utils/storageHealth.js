/**
 * Browser-storage probes for the two login screens (B4, pre-class register).
 *
 * THE FAILURE THIS EXPLAINS
 * -------------------------
 * "Login succeeds, then you are immediately logged out." A privacy extension,
 * Safari ITP or a locked-down lab/kiosk browser accepts the POST but never
 * keeps what the session depends on. Today that surfaces as the admin gateway
 * bouncing back with "Your session expired" — seconds after a successful
 * login, which sends the facilitator hunting for a password problem that does
 * not exist.
 *
 * THE TWO SCREENS DEPEND ON DIFFERENT THINGS — this is why there is no single
 * "enable cookies" banner:
 *
 *   Facilitator login → an HttpOnly JWT **cookie** set by the server.
 *                       JS cannot read it (that is the point), so we probe
 *                       whether this browser stores a first-party cookie at all.
 *   Player login      → **localStorage** (`muressons_session_id`,
 *                       `muressons_playerId`, the ws ticket) plus an
 *                       `X-Player-Id` header. No cookie is involved, so a
 *                       cookie warning here would be simply wrong.
 *
 * Both probes are optimistic during SSR and on any unexpected throw: a false
 * alarm on a working browser is worse than staying quiet, and the real
 * failure still shows up as a login that will not stick.
 */

const COOKIE_PROBE = 'muressons_probe';
const STORAGE_PROBE = '__muressons_probe__';

/** True if this browser will store and return a first-party cookie. */
export function cookiesWritable() {
  if (typeof document === 'undefined') return true;   // SSR — assume fine
  try {
    document.cookie = `${COOKIE_PROBE}=1; path=/; SameSite=Lax`;
    const stored = document.cookie
      .split(';')
      .some((c) => c.trim() === `${COOKIE_PROBE}=1`);
    // Clean up whether or not it stuck.
    document.cookie = `${COOKIE_PROBE}=; path=/; Max-Age=0; SameSite=Lax`;
    return stored;
  } catch {
    return false;
  }
}

/** True if this browser will store and return a localStorage value. */
export function localStorageWritable() {
  if (typeof window === 'undefined') return true;     // SSR — assume fine
  try {
    window.localStorage.setItem(STORAGE_PROBE, '1');
    const ok = window.localStorage.getItem(STORAGE_PROBE) === '1';
    window.localStorage.removeItem(STORAGE_PROBE);
    return ok;
  } catch {
    // Safari private mode historically threw QuotaExceededError on setItem.
    return false;
  }
}

/** Shown on the facilitator login when the cookie probe fails. */
export const COOKIE_BLOCKED_MESSAGE =
  'This browser is blocking cookies, so a sign-in here will not stick — '
  + 'you would be returned to this screen straight away. Allow cookies for '
  + 'this site, or use a normal (non-private) Chrome, Edge or Firefox window.';

/** Shown on the player login when the localStorage probe fails. */
export const STORAGE_BLOCKED_MESSAGE =
  'This browser is blocking site storage, so your session cannot be kept — '
  + 'you would be signed out on the next screen. Turn off private/incognito '
  + 'mode or allow site data, then try again.';
