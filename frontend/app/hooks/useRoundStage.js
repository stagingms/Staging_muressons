'use client';
/**
 * useRoundStage — the player round-flow stage machine.
 *
 * Phase A (player dashboard redesign): verbatim extraction from
 * ExecutiveCockpit.js. This hook is the single source of truth for which
 * stage of the turn the player is in (gate → strategy → allocation →
 * commit → results), derived purely from game state. Phase D renders the
 * Decision Canvas from it; until then the cockpit consumes it exactly as
 * it consumed the inline version — identical bindings, identical logic.
 *
 * Inputs are primitives/props only; this hook performs no fetches and owns
 * no timing beyond the original auto-advance effects.
 */
import { useState, useMemo, useCallback, useEffect, useRef } from 'react';

export default function useRoundStage({
  roundNumber,
  hasReadBriefing,
  gameOver,
  tourActive,
  roundPrerequisiteMet,
  hasDecision,
  allocations,
  commitResults,
  selfLearningMode,
  cohortWaiting = false,
  sessionId = null,
}) {
  /* PHASE 5.3 — the opt-out survives a refresh. Keyed by session so one
     cohort's preference does not follow a player into the next. Every access
     is wrapped: this runs on a client that may have storage disabled, and the
     round-stage machine is not a place to take a session down. */
  const PREF_KEY = `muressons_prefers_dashboard_${sessionId || 'demo'}`;
  const readPref = () => {
    try { return localStorage.getItem(PREF_KEY) === '1'; } catch { return false; }
  };
  const writePref = (v) => {
    try {
      if (v) localStorage.setItem(PREF_KEY, '1');
      else localStorage.removeItem(PREF_KEY);
    } catch { /* storage disabled — the ref still holds it for this session */ }
  };
  // ── Focus Mode: Stepped Decision Overlays ──
  // Optional with escape hatch — auto-opens but student can dismiss at any time
  const [focusStep, setFocusStep] = useState(null); // null | 'gate' | 'strategy' | 'allocation' | 'waiting' | 'results'
  const [focusDismissed, setFocusDismissed] = useState(false);
  /* D1: once an experienced player (round >= 3) opts out of the stepped focus
     overlay, remember it so it doesn't re-interrupt every subsequent round.
     Mandatory R1/R2 gates and first-time behaviour are untouched (the pref is
     only ever set from round 3 onward, and gates only exist in R1/R2).

     PHASE 5.3. This was a useRef, which meant the preference died on refresh —
     and a facilitator asking a room to reload, or a player whose laptop slept,
     got the overlay forced back on for the rest of the session. A ref makes it
     a suggestion; storage makes it a preference. Keyed by session so one
     cohort's opt-out does not follow a player into the next.

     Read lazily and inside try/catch: this runs during render on a client that
     may have storage disabled, and the round-stage machine is not a place to
     take a session down. */
  const prefersDashboardRef = useRef(false);
  useEffect(() => { prefersDashboardRef.current = readPref(); }, [PREF_KEY]);

  // Compute focus steps for this round — gates are mandatory in ALL modes
  const isSelfLearning = selfLearningMode === true;
  const hasGate = roundNumber === 1 || roundNumber === 2;
  // Owner request (2026-07-13): the separate 'commit' canvas stage was a
  // DUPLICATE of the always-present cockpit commit footer — two buttons for one
  // onCommit() action. The footer is the preferred surface (it validates,
  // opens the prediction prompt, and lets you scroll back to review/edit), so
  // the flow now ends its decision stages at 'allocation'; the player commits
  // from the footer and auto-advances to 'results'. The engine commit, the
  // prediction prompt, and results are all unchanged.
  const focusSteps = useMemo(() => {
    const s = [];
    if (hasGate) s.push('gate');
    s.push('strategy', 'allocation');
    return s;
  }, [hasGate]);

  // Determine the first incomplete focus step
  const getFirstIncompleteStep = useCallback(() => {
    if (hasGate && !roundPrerequisiteMet) return 'gate';
    if (!hasDecision) return 'strategy';
    // Stay on 'allocation' until the turn is committed (via the cockpit footer);
    // once commitResults lands, advance to results.
    if (!commitResults) return 'allocation';
    /* WAITING. Committing already produced this team's outcomes, so 'waiting'
       is not a loading state — it is a deliberate hold between the act and the
       reveal, for the minutes a cohort spends waiting on its slowest table.
       That gap exists today and is spent staring at numbers already known;
       this turns it into the one moment where a prediction can still be
       falsified.

       cohortWaiting is FALSE for a solo player and false the instant the last
       team commits or the facilitator releases the barrier, so nobody can be
       stranded here — the same conditions the results screen's advance button
       has always used. */
    if (cohortWaiting) return 'waiting';
    return 'results';
  }, [hasGate, roundPrerequisiteMet, hasDecision, commitResults, cohortWaiting]);

  // Auto-trigger focus mode when briefing is dismissed (entering the cockpit)
  // Suppressed while the onboarding tour is active to prevent z-index conflicts
  useEffect(() => {
    if (!hasReadBriefing || gameOver) return;
    if (focusDismissed) return;
    if (tourActive) return; // Don't auto-trigger while intro tour is running
    // Only auto-open if no focus step is active yet
    if (focusStep === null) {
      setFocusStep(getFirstIncompleteStep());
    }
  }, [hasReadBriefing, gameOver, focusDismissed, tourActive]);

  // Auto-advance: gate completed → strategy
  useEffect(() => {
    if (focusStep === 'gate' && roundPrerequisiteMet) {
      setFocusStep('strategy');
    }
  }, [focusStep, roundPrerequisiteMet]);

  // Auto-advance: turn committed while on the allocation stage → results.
  // The allocation stage's 'Review & Commit' button opens the confirm flow
  // (prediction → 'Review Your Decisions' modal) with the guided overlay still
  // open, so on commit we advance the overlay straight to its results view.
  // (Also covers committing from the cockpit footer with the overlay open.)
  useEffect(() => {
    if (commitResults && focusStep === 'allocation') {
      setFocusStep(cohortWaiting ? 'waiting' : 'results');
    }
  }, [focusStep, commitResults, cohortWaiting]);

  /* And out again the moment the cohort is whole. The poll that refreshes
     global_state drives this; nothing here waits on a timer of its own. */
  useEffect(() => {
    if (focusStep === 'waiting' && !cohortWaiting) {
      setFocusStep('results');
    }
  }, [focusStep, cohortWaiting]);

  // Reset focus mode on round change. D1: if a returning player previously
  // opted for the dashboard, keep focus dismissed instead of re-opening it.
  useEffect(() => {
    setFocusStep(null);
    setFocusDismissed(prefersDashboardRef.current);
  }, [roundNumber]);

  const isFocusActive = focusStep !== null && !focusDismissed && !tourActive;

  // Quick Resume: returning players (round 3+) can skip to decisions
  const isReturningPlayer = roundNumber >= 3;

  const handleFocusDismiss = useCallback(() => {
    setFocusDismissed(true);
    setFocusStep(null);
    // D1: remember the opt-out for experienced players (never for R1/R2 gates).
    if (roundNumber >= 3) { prefersDashboardRef.current = true; writePref(true); }
  }, [roundNumber]);

  // Quick Resume: skip briefing + focus gate, jump straight to allocation
  const handleQuickResume = useCallback(() => {
    setFocusDismissed(true);
    setFocusStep(null);
    if (roundNumber >= 3) { prefersDashboardRef.current = true; writePref(true); }
    // Scroll to decision area if available
    setTimeout(() => {
      const decisionArea = document.getElementById('tour-decisions-target');
      if (decisionArea) decisionArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 200);
  }, [roundNumber]);

  const handleFocusReenter = useCallback(() => {
    setFocusDismissed(false);
    setFocusStep(getFirstIncompleteStep());
    // D1: re-entering means they want the guided flow back — clear the opt-out.
    prefersDashboardRef.current = false;
    writePref(false);
  }, [getFirstIncompleteStep]);

  const handleFocusAdvance = useCallback((nextStep) => {
    setFocusStep(nextStep);
  }, []);

  return {
    focusStep, setFocusStep,
    focusDismissed, setFocusDismissed,
    prefersDashboardRef,
    isSelfLearning,
    hasGate, focusSteps, getFirstIncompleteStep,
    isFocusActive, isReturningPlayer,
    handleFocusDismiss, handleQuickResume, handleFocusReenter, handleFocusAdvance,
  };
}
