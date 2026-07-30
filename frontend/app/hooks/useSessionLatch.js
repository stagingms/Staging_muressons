'use client';
import { useCallback, useState } from 'react';

/**
 * useSessionLatch — a one-way "the player has done this" flag that cannot
 * outlive the session it was earned in.
 *
 * WHY THIS EXISTS
 * ---------------
 * Several gates in the cockpit are confirmed by the server (globalState carries
 * `csrd_completed`, `stakeholder_map_completed`, …) but need a LOCAL flag as
 * well, because the authoritative value only lands on the next dashboard
 * refresh. Without the local flag a flaky refresh reads as "not done" and the
 * player is sent back through a mini-game they already completed — the
 * "double materiality repeats twice" class of bug, which took three separate
 * fixes.
 *
 * A plain `useState(false)` is the wrong shape for that flag. Page state
 * survives a change of session in the same tab: a facilitator or tester who
 * logs in as a second player, or impersonates another cohort, keeps every latch
 * from the first one. `page.js` compensated with a hand-maintained reset effect
 * keyed on `sim.sessionId` — and that is precisely how this broke. `csrdDone`
 * was declared 87 lines BELOW that effect and never joined it, so a tester who
 * submitted the CSRD assessment in one cohort saw the next player arrive in
 * Round 2 with "✅ CSRD Assessment Submitted" already ticked, having entered
 * nothing. Worse than the cosmetic tick: `isCommitBlocked` reads the same flag,
 * so that player could commit Round 2 without ever opening the assessment.
 * `boardroomDone` had drifted the same way.
 *
 * A reset list only works while everyone remembers to join it. Two of three
 * latches did not. So the scoping is structural here instead: the latch stores
 * WHICH session set it and reports itself latched only while that session is
 * still current. A new session is a new latch, with nothing to remember.
 *
 * DELIBERATELY NOT KEYED ON ROUND. Every latch that uses this belongs to one
 * round by construction (stakeholder map = R1, CSRD = R2) and its server flag
 * persists once set, so the round adds no safety — while `roundNumber` is known
 * to flicker during the post-submit dashboard refresh, and a latch that dropped
 * on that flicker would resurrect the very re-do loop these flags prevent.
 *
 * A momentarily absent session id is treated as "not yet known", NOT as a
 * different session, for the same reason: the latch must never drop while the
 * app is mid-refresh.
 *
 * @param {string|null|undefined} sessionId  the session the latch belongs to
 * @returns {[boolean, () => void]} [latched, latch]
 */
export default function useSessionLatch(sessionId) {
    const [owner, setOwner] = useState(null);

    const latch = useCallback(() => {
        // Record the owner even when the id is momentarily unknown; `latched`
        // below treats an unknown current id as "still the same session", so a
        // latch set during a refresh is honoured rather than silently lost.
        setOwner(sessionId ?? null);
    }, [sessionId]);

    const latched = owner !== null && (!sessionId || owner === sessionId);

    return [latched, latch];
}
