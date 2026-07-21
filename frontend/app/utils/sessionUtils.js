/**
 * sessionUtils.js
 * Helpers for displaying human-friendly session identifiers.
 * New sessions get a short_code like "SIM-A3K7" from the backend.
 * Older sessions fall back to first-8-chars of uuid.
 */

/**
 * Format a single session object into a short, readable ID.
 * @param {Object|null} session - session object with `short_code` and `session_id`
 * @returns {string}
 */
export function formatSessionId(session) {
    if (!session) return '—';
    if (session.short_code) return session.short_code;
    const id = session.session_id || session.id || '';
    return id ? id.slice(0, 8) : '—';
}

/**
 * Look up the short code for a session_id from a list of sessions.
 * @param {string} sessionId - the full UUID
 * @param {Array} sessions   - array of session objects
 * @returns {string}
 */
export function getShortCode(sessionId, sessions = []) {
    if (!sessionId) return '—';
    const match = sessions.find(
        s => (s.session_id || s.id) === sessionId
    );
    if (match) return formatSessionId(match);
    return sessionId.slice(0, 8);
}
