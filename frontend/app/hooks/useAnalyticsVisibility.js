'use client';
import { useState, useEffect } from 'react';
import { playerIdHeader } from './useSimulation';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * Fail-open visibility check.
 *
 * A panel is hidden ONLY when the resolved map explicitly carries `false` for
 * its key. While the effective map is still loading, is unknown, or the request
 * failed (`map` is null/undefined), every panel is treated as visible — a
 * network hiccup must never blank a dashboard or the player's cockpit.
 *
 * @param {object|null} map  role sub-map, e.g. effective.facilitator or effective.player
 * @param {string} key       panel key, e.g. 'decision_heatmap' / 'what_if_simulator'
 */
export function isPanelVisible(map, key) {
    return !map || map[key] !== false;
}

/**
 * Fetch a cohort's EFFECTIVE analytics-visibility (global defaults merged with
 * per-cohort overrides) and expose fail-open checks for each role.
 *
 * Backend: GET /api/admin/cohort/{sessionId}/analytics-visibility → { effective:
 * { facilitator:{...}, player:{...} } }. `resolve_analytics_visibility` walks up
 * to the parent cohort automatically, so a player sub-session id resolves to its
 * cohort's settings — pass whichever session id you have.
 *
 * @param {string|null|undefined} sessionId  cohort id, or a player sub-session id
 * @returns {{ facilitator: object|null, player: object|null,
 *            isFacilitatorVisible: (key:string)=>boolean,
 *            isPlayerVisible: (key:string)=>boolean }}
 */
export function useAnalyticsVisibility(sessionId) {
    const [vis, setVis] = useState({ facilitator: null, player: null });

    useEffect(() => {
        if (!sessionId) return undefined;
        let cancelled = false;
        // The console route carries both columns and is facilitator-guarded
        // (F-21). A participant's tab gets 401 there — and used to fail open,
        // so every player-audience toggle the facilitator set was ignored on
        // the participant's screen (found by the 2026-09-10 rehearsal). A
        // team reads its own player column from the team-readable route.
        fetch(`${API}/api/admin/cohort/${sessionId}/analytics-visibility`, { credentials: 'include' })
            .then(r => (r.ok ? r.json() : null))
            .then(async d => {
                if (cancelled) return;
                if (d) {
                    const eff = d.effective || {};
                    setVis({ facilitator: eff.facilitator || null, player: eff.player || null });
                    return;
                }
                const r = await fetch(`${API}/api/simulations/${sessionId}/player-visibility`, { headers: { ...playerIdHeader() } });
                if (!r.ok || cancelled) return;
                const pd = await r.json();
                setVis({ facilitator: null, player: (pd.effective || {}).player || null });
            })
            .catch(() => { /* fail-open: keep nulls → everything stays visible */ });
        return () => { cancelled = true; };
    }, [sessionId]);

    return {
        facilitator: vis.facilitator,
        player: vis.player,
        isFacilitatorVisible: key => isPanelVisible(vis.facilitator, key),
        isPlayerVisible: key => isPanelVisible(vis.player, key),
    };
}
