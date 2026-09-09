/**
 * API error text — one normaliser for the whole front end.
 *
 * THE DEFECT THIS EXISTS FOR
 *   Forms across this app reported server rejections as the literal text
 *   "[object Object]". That is the one failure state an operator cannot act on:
 *   the app knows why it failed and will not say.
 *
 *   FastAPI's `detail` is a string only for a plain HTTPException. A 422
 *   validation error returns an ARRAY of {loc, msg, type}; a structured raise
 *   returns a dict. `new Error(detail)` coerces either to "[object Object]".
 *   (React throws on an object child rather than printing one, so that text can
 *   only have come from such a coercion — which is how the source is identified.)
 *
 * WHY A MODULE AND NOT A FIX AT EACH SITE
 *   There are ~56 `.detail ||` sites across app/. Patching them one at a time is
 *   a fix that regresses the moment someone writes the fifty-seventh, which is
 *   why __tests__/no-raw-detail-coercion.test.js bans the pattern rather than
 *   trusting a sweep.
 */

const DEFAULT_FALLBACK = 'Something went wrong. See the browser console for details.';

/** Any thrown/returned value → a string safe to render, or null. */
export const toErrorText = (value, fallback = DEFAULT_FALLBACK) => {
    if (value == null) return null;

    if (typeof value === 'string') return value.trim() || fallback;

    if (value instanceof Error) {
        const m = (value.message || '').trim();
        // An Error already poisoned by the coercion this module prevents: its
        // message is unrecoverable, so prefer the fallback over showing it.
        return m && m !== '[object Object]' ? m : fallback;
    }

    if (Array.isArray(value)) {
        // FastAPI 422: [{loc:['body','region_id'], msg:'Input should be a valid
        // string', type:'string_type'}] → "region_id: Input should be a valid string".
        const parts = value.map((e) => {
            if (typeof e === 'string') return e.trim() || null;
            const field = Array.isArray(e && e.loc)
                ? e.loc.filter((x) => x !== 'body' && x !== 'query').join('.')
                : null;
            const msg = (e && (e.msg || e.message)) || null;
            if (field && msg) return `${field}: ${msg}`;
            if (msg) return msg;
            try { return JSON.stringify(e); } catch { return null; }
        }).filter(Boolean);
        if (parts.length) return parts.join('; ');
        return fallback;
    }

    if (typeof value === 'object') {
        if (typeof value.message === 'string' && value.message.trim()) return value.message;
        if (value.detail != null) return toErrorText(value.detail, fallback);
        try {
            const j = JSON.stringify(value);
            if (j && j !== '{}' && j !== 'null') return j;
        } catch { /* circular structure — fall through to the fallback */ }
    }

    return fallback;
};

/**
 * A failed fetch as a sentence an operator can act on: what failed, what the
 * server said, and the status. `where` is not decoration — "Pedagogical
 * Settings (500)" identifies which of eleven sub-config calls broke; "failed"
 * does not.
 */
export const describeHttpFailure = (where, status, body) => {
    const said = toErrorText(body && body.detail, null) || toErrorText(body, null);
    return said ? `${where} failed (${status}): ${said}` : `${where} failed (HTTP ${status}).`;
};
