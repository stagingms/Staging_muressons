/**
 * adminFetch — the single authed fetch path for the admin dashboards.
 *
 * Phase 2 (G6/G8): every admin call must (a) carry the HttpOnly JWT cookie
 * via credentials:'include' — several god-mode fetches previously omitted it,
 * which silently 401'd in cross-origin deployments and rendered as "empty"
 * data — and (b) let callers distinguish "failed to load" from "empty".
 *
 * This helper deliberately does NOT alter methods, paths, headers, or bodies:
 * request payloads stay byte-identical to the pre-refactor contract.
 */
const API = process.env.NEXT_PUBLIC_API_URL || '';

export function adminFetch(path, options = {}) {
    return fetch(`${API}${path}`, { credentials: 'include', ...options });
}

/**
 * adminJson — fetch + JSON with a normalized result envelope.
 * @returns {Promise<{ok: boolean, status: number, data: any|null}>}
 *          status 0 means a network-level failure (offline, CORS, timeout).
 */
export async function adminJson(path, options = {}) {
    try {
        const res = await adminFetch(path, options);
        if (!res.ok) return { ok: false, status: res.status, data: null };
        return { ok: true, status: res.status, data: await res.json() };
    } catch {
        return { ok: false, status: 0, data: null };
    }
}
