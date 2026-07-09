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
}) {
  // ── Focus Mode: Stepped Decision Overlays ──
  // Optional with escape hatch — auto-opens but student can dismiss at any time
  const [focusStep, setFocusStep] = useState(null); // null | 'gate' | 'strategy' | 'allocation' | 'commit' | 'results'
  const [focusDismissed, setFocusDismissed] = useState(false);
  // D1: once an experienced player (round >= 3) opts out of the stepped focus
  // overlay, remember it so it doesn't re-interrupt every subsequent round.
  // Mandatory R1/R2 gates and first-time behaviour are untouched (the pref is
  // only ever set from round 3 onward, and gates only exist in R1/R2).
  const prefersDashboardRef = useRef(false);
  const [focusPredictionText, setFocusPredictionText] = useState('');
  const [skipPredictionConfirm, setSkipPredictionConfirm] = useState(false);

  // Compute focus steps for this round — gates are mandatory in ALL modes
  const isSelfLearning = selfLearningMode === true;
  const hasGate = roundNumber === 1 || roundNumber === 2;
  const focusSteps = useMemo(() => {
    const s = [];
    if (hasGate) s.push('gate');
    s.push('strategy', 'allocation', 'commit');
    return s;
  }, [hasGate]);

  // Determine the first incomplete focus step
  const getFirstIncompleteStep = useCallback(() => {
    if (hasGate && !roundPrerequisiteMet) return 'gate';
    if (!hasDecision) return 'strategy';
    if (Object.keys(allocations).length === 0) return 'allocation';
    if (!commitResults) return 'commit';
    return 'results';
  }, [hasGate, roundPrerequisiteMet, hasDecision, allocations, commitResults]);

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

  // Auto-advance: commit done → results
  useEffect(() => {
    if (focusStep === 'commit' && commitResults) {
      setFocusStep('results');
    }
  }, [focusStep, commitResults]);

  // Reset focus mode on round change. D1: if a returning player previously
  // opted for the dashboard, keep focus dismissed instead of re-opening it.
  useEffect(() => {
    setFocusStep(null);
    setFocusDismissed(prefersDashboardRef.current);
    setFocusPredictionText('');
  }, [roundNumber]);

  const isFocusActive = focusStep !== null && !focusDismissed && !tourActive;

  // Quick Resume: returning players (round 3+) can skip to decisions
  const isReturningPlayer = roundNumber >= 3;

  const handleFocusDismiss = useCallback(() => {
    setFocusDismissed(true);
    setFocusStep(null);
    // D1: remember the opt-out for experienced players (never for R1/R2 gates).
    if (roundNumber >= 3) prefersDashboardRef.current = true;
  }, [roundNumber]);

  // Quick Resume: skip briefing + focus gate, jump straight to allocation
  const handleQuickResume = useCallback(() => {
    setFocusDismissed(true);
    setFocusStep(null);
    if (roundNumber >= 3) prefersDashboardRef.current = true;
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
  }, [getFirstIncompleteStep]);

  const handleFocusAdvance = useCallback((nextStep) => {
    setFocusStep(nextStep);
  }, []);

  return {
    focusStep, setFocusStep,
    focusDismissed, setFocusDismissed,
    prefersDashboardRef,
    focusPredictionText, setFocusPredictionText,
    skipPredictionConfirm, setSkipPredictionConfirm,
    isSelfLearning,
    hasGate, focusSteps, getFirstIncompleteStep,
    isFocusActive, isReturningPlayer,
    handleFocusDismiss, handleQuickResume, handleFocusReenter, handleFocusAdvance,
  };
}
