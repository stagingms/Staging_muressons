/**
 * ConsequenceReplay — WOW-1
 *
 * An auto-playing animated sequence that visually traces the causal chain
 * of the player's round decision through the engine's flag dependency graph.
 * Fires after each round commit (in the results step), making the engine's
 * extraordinary depth *visible* to the player.
 *
 * SAFETY: Pure presentation layer. Reads existing data from:
 *   - commitResults.events (engine events from the round tick)
 *   - globalState.active_event_flags (flag dependency graph state)
 *   - The per-round causal chain definitions below (static data)
 * No changes to engine.py, round_logic.py, terminal_valuation.py, or any
 * commit payload. No changes to round flow or gating logic.
 *
 * FACILITATOR TOGGLE: Controlled by `consequence_replay_enabled` setting.
 * When disabled, renders nothing. Skippable by player via "Skip" button.
 *
 * Props:
 *   roundNumber   — current round (1-10)
 *   choiceKey     — the crisis decision made (e.g. 'option_a')
 *   commitResults — full commit results object
 *   globalState   — current global state (post-commit)
 *   prevGlobalState — previous global state (pre-commit, for delta computation)
 *   sessionId     — for fetching facilitator settings
 *   onComplete    — callback when animation finishes or is skipped
 */
'use client';
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import styles from './ConsequenceReplay.module.css';

/**
 * Causal chain definitions per round × choice.
 * Each chain is an ordered array of { label, icon, type, detail? }.
 * Type: 'decision' | 'mechanism' | 'impact' | 'future' (for flag effects).
 *
 * These are static, pedagogical descriptions mirroring the flag dependency
 * graph in SIMULATION_CONTEXT.md §11. They do NOT compute anything — the
 * engine has already computed the real effects. This is narration, not math.
 */
const CAUSAL_CHAINS = {
  1: {
    option_a: [
      { label: 'Surface-Level ESG Scan', icon: '📋', type: 'decision' },
      { label: 'Electronics risks remain hidden', icon: '🔍', type: 'mechanism' },
      { label: 'electronics_blindspot flag set', icon: '⚠️', type: 'impact', flag: 'electronics_blindspot' },
      { label: 'Round 4 crisis severity will DOUBLE (40→80)', icon: '💣', type: 'future' },
    ],
    option_b: [
      { label: 'Deep Forensic Audit', icon: '🔬', type: 'decision' },
      { label: 'Hidden supply chain risks uncovered', icon: '🔍', type: 'mechanism' },
      { label: 'Carbon intensity reduced, SLO improved', icon: '📈', type: 'impact' },
      { label: 'Round 4 crisis severity halved — you are protected', icon: '🛡️', type: 'future' },
    ],
    option_c: [
      { label: 'Phased Audit Rollout', icon: '📅', type: 'decision' },
      { label: 'Partial blind spots remain in Electronics BU', icon: '🔍', type: 'mechanism' },
      { label: 'Moderate cost, partial protection', icon: '⚖️', type: 'impact' },
      { label: 'Some Round 4 exposure persists', icon: '⚠️', type: 'future' },
    ],
  },
  2: {
    option_a: [
      { label: 'Full Materiality Alignment', icon: '📊', type: 'decision' },
      { label: 'ESRS 1 compliance achieved', icon: '✅', type: 'mechanism' },
      { label: 'materiality_aligned flag set → +0.10 M_R at terminal', icon: '🎯', type: 'impact', flag: 'materiality_aligned' },
      { label: 'Governance credibility established for institutional investors', icon: '🏛️', type: 'future' },
    ],
    option_b: [
      { label: 'Strategic Exceptions', icon: '📋', type: 'decision' },
      { label: 'Partial CSRD compliance', icon: '⚖️', type: 'mechanism' },
      { label: 'No materiality M_R bonus at terminal valuation', icon: '❌', type: 'impact' },
    ],
    option_c: [
      { label: 'CEO-Only Sign-Off', icon: '👤', type: 'decision' },
      { label: 'ESRS 1 §1.51 violation triggered', icon: '⚖️', type: 'mechanism' },
      { label: '40% budget clawback, Governance Risk +10', icon: '💸', type: 'impact' },
      { label: 'Investor risk premium applied to cost of capital', icon: '📉', type: 'future' },
    ],
  },
  3: {
    option_a: [
      { label: 'Rapid Supplier Switch', icon: '🏭', type: 'decision' },
      { label: 'Scope 3 carbon intensity reduced by 15', icon: '🌍', type: 'mechanism' },
      { label: 'early_decarboniser flag set → +0.10 synergy bonus at R7', icon: '⚡', type: 'impact', flag: 'early_decarboniser' },
      { label: 'Supply disruption risk in short term', icon: '⚠️', type: 'future' },
    ],
    option_b: [
      { label: 'Green Bond Investment', icon: '💚', type: 'decision' },
      { label: 'NCD reduced by 15, CI reduced by 8', icon: '📉', type: 'mechanism' },
      { label: 'Green bond active, balanced decarbonisation', icon: '🎯', type: 'impact' },
    ],
    option_c: [
      { label: 'Offset & Defer', icon: '⏳', type: 'decision' },
      { label: 'Real decarbonisation deferred', icon: '🔄', type: 'mechanism' },
      { label: 'NCD increases by 5, Reputation drops', icon: '📉', type: 'impact' },
      { label: 'Greenwash risk if investment ratio < 15%', icon: '⚠️', type: 'future' },
    ],
  },
  4: {
    option_a: [
      { label: 'Full Transparency & Remediation', icon: '🔆', type: 'decision' },
      { label: 'Root cause addressed, stakeholder trust rebuilt', icon: '🤝', type: 'mechanism' },
      { label: 'SLO +8, Governance Risk -5', icon: '📈', type: 'impact' },
      { label: 'Contagion contained — reputation stabilizes', icon: '🛡️', type: 'future' },
    ],
    option_b: [
      { label: 'Damage Control PR', icon: '📰', type: 'decision' },
      { label: 'Root cause unaddressed', icon: '🔄', type: 'mechanism' },
      { label: 'SLO drops by 3, surface-level containment', icon: '⚖️', type: 'impact' },
    ],
    option_c: [
      { label: 'Deny & Deflect', icon: '🙈', type: 'decision' },
      { label: 'Contagion engine amplifies crisis via S-curve', icon: '📈', type: 'mechanism' },
      { label: 'Reputation -15, SLO -10, Governance Risk +8', icon: '💥', type: 'impact' },
      { label: 'Natural Capital Debt increases; brain-drain accelerates', icon: '⚠️', type: 'future' },
    ],
  },
  5: {
    option_a: [
      { label: 'Hard Engineering Defence', icon: '🏗️', type: 'decision' },
      { label: 'Resilience factor 0.85 — protection active from R7', icon: '🛡️', type: 'mechanism' },
      { label: 'NCD +10, CI +3 (construction impact)', icon: '⚖️', type: 'impact' },
      { label: 'Climate resilience bonus (+0.20 M_R) preserved at terminal', icon: '🎯', type: 'future' },
    ],
    option_b: [
      { label: 'Nature-Based Solutions', icon: '🌿', type: 'decision' },
      { label: 'Resilience factor 0.60, NCD reduced', icon: '🌍', type: 'mechanism' },
      { label: 'NCD -8, CI -6, nature-based resilience set', icon: '📈', type: 'impact', flag: 'nature_based_resilience' },
      { label: 'Climate resilience bonus (+0.20 M_R) preserved at terminal', icon: '🎯', type: 'future' },
    ],
    option_c: [
      { label: 'Insurance Only', icon: '📜', type: 'decision' },
      { label: 'Resilience factor = 0.0 — NO physical protection', icon: '❌', type: 'mechanism' },
      { label: 'insurance_only flag set', icon: '🔒', type: 'impact', flag: 'insurance_only' },
      { label: 'PERMANENTLY BLOCKS +0.20 Resilience M_R bonus at terminal valuation', icon: '🚫', type: 'future' },
    ],
  },
  6: {
    option_a: [
      { label: 'Monetise the Algorithm', icon: '💰', type: 'decision' },
      { label: 'Software revenue +$10M but ethical violation exposed', icon: '📰', type: 'mechanism' },
      { label: 'Reputation -20, SLO -15', icon: '💥', type: 'impact' },
      { label: 'EU AI Act compliance costs from Round 7+', icon: '⚖️', type: 'future' },
    ],
    option_b: [
      { label: 'Ethical AI Overhaul', icon: '🤖', type: 'decision' },
      { label: 'Full algorithmic bias remediation', icon: '🔧', type: 'mechanism' },
      { label: 'ethical_ai_overhaul flag set → +0.15 Truth Premium M_R', icon: '🎯', type: 'impact', flag: 'ethical_ai_overhaul' },
      { label: 'SLO +15, long-term governance credibility', icon: '📈', type: 'future' },
    ],
    option_c: [
      { label: 'Quiet Patch', icon: '🔇', type: 'decision' },
      { label: 'Surface fix, governance risk persists', icon: '⚠️', type: 'mechanism' },
      { label: 'Governance Risk +10, future leak risk', icon: '📉', type: 'impact' },
    ],
  },
  7: {
    option_a: [
      { label: 'Full Circular Redesign', icon: '♻️', type: 'decision' },
      { label: 'Product lifecycle transformed, NCD -12', icon: '🌍', type: 'mechanism' },
      { label: 'CI -8 (scope3-weighted), Reputation +8', icon: '📈', type: 'impact' },
    ],
    option_b: [
      { label: 'Extended Producer Responsibility', icon: '📦', type: 'decision' },
      { label: 'Moderate waste diversion, compliance met', icon: '✅', type: 'mechanism' },
      { label: 'NCD -6, CI -5', icon: '⚖️', type: 'impact' },
    ],
    option_c: [
      { label: 'Waste-to-Energy Partnership', icon: '⚡', type: 'decision' },
      { label: 'Cross-BU synergy unlocked', icon: '🔗', type: 'mechanism' },
      { label: 'synergy_unlock flag set → +0.15 Strategic M_R + OPEX savings', icon: '🎯', type: 'impact', flag: 'synergy_unlock' },
      { label: 'Enables Round 10 "Resist & Integrate" option', icon: '🔓', type: 'future' },
    ],
  },
  8: {
    option_a: [
      { label: 'Water Efficiency for All BUs', icon: '💧', type: 'decision' },
      { label: 'All BUs benefit equally, SLO preserved', icon: '⚖️', type: 'mechanism' },
      { label: 'Water dependency -20, CI -3, SLO +5', icon: '📈', type: 'impact' },
      { label: 'Resilience M_R bonus preserved at terminal valuation', icon: '🎯', type: 'future' },
    ],
    option_b: [
      { label: 'Prioritise Electronics', icon: '⚡', type: 'decision' },
      { label: 'Electronics protected, Pharma/CG abandoned', icon: '⚠️', type: 'mechanism' },
      { label: 'electronics_water_priority flag set, SLO -25 for Pharma/CG', icon: '💥', type: 'impact', flag: 'electronics_water_priority' },
      { label: 'PERMANENTLY BLOCKS +0.20 Resilience M_R bonus', icon: '🚫', type: 'future' },
    ],
    option_c: [
      { label: 'Desalination Mega-Project', icon: '🏗️', type: 'decision' },
      { label: 'Massive infrastructure investment (-$30M)', icon: '💸', type: 'mechanism' },
      { label: 'NCD -30, Water -40, generates $5M/round from R10', icon: '📈', type: 'impact' },
      { label: '3-round payback; long-term water independence', icon: '⏰', type: 'future' },
    ],
  },
  9: {
    option_a: [
      { label: 'Immediate Closure', icon: '🏚️', type: 'decision' },
      { label: 'Short-term cash gain, community devastation', icon: '💰', type: 'mechanism' },
      { label: 'SLO -20, Reputation -15', icon: '💥', type: 'impact' },
      { label: '75% strike chance if SLO is low — could zero revenue', icon: '🚨', type: 'future' },
    ],
    option_b: [
      { label: 'Managed Transition', icon: '🤝', type: 'decision' },
      { label: 'Phased factory transition with worker support', icon: '👥', type: 'mechanism' },
      { label: 'managed_transition → +0.12 Just Transition M_R (×JT scaling)', icon: '🎯', type: 'impact', flag: 'managed_transition' },
      { label: 'HR investment history amplifies this bonus up to 1.5×', icon: '📈', type: 'future' },
    ],
    option_c: [
      { label: 'Community Investment Fund', icon: '🏘️', type: 'decision' },
      { label: 'Deep community partnership, $20M investment', icon: '💚', type: 'mechanism' },
      { label: 'community_fund → +0.18 Community Champion M_R (×JT scaling)', icon: '🎯', type: 'impact', flag: 'community_fund' },
      { label: 'SLO +18, Reputation +12 — strongest social outcome', icon: '🌟', type: 'future' },
    ],
  },
  10: {
    option_a: [
      { label: 'Resist & Integrate', icon: '🏛️', type: 'decision' },
      { label: 'Leverage synergy to defend against restructuring', icon: '🔗', type: 'mechanism' },
      { label: 'Synergy bonus applied to terminal valuation', icon: '📈', type: 'impact' },
    ],
    option_b: [
      { label: 'Spin-off', icon: '📤', type: 'decision' },
      { label: 'Weakest BU divested, partial value unlock', icon: '⚖️', type: 'mechanism' },
      { label: '+$10M treasury, SLO -5', icon: '💰', type: 'impact' },
    ],
    option_c: [
      { label: 'Divest All', icon: '💵', type: 'decision' },
      { label: 'Full divestiture for maximum cash extraction', icon: '💸', type: 'mechanism' },
      { label: 'synergy_wipe — all synergy destroyed, +$25M cash', icon: '💥', type: 'impact' },
      { label: 'Short-term cash maximized, long-run value destroyed', icon: '⚠️', type: 'future' },
    ],
  },
};

/** Compute KPI deltas from pre vs post global state. */
function computeDeltas(prev, next) {
  if (!prev || !next) return [];
  const deltas = [];
  const treasury = (next.corporate_treasury || 0) - (prev.corporate_treasury || 0);
  if (Math.abs(treasury) > 100) {
    deltas.push({
      label: 'Treasury',
      value: `${treasury >= 0 ? '+' : '-'}$${(Math.abs(treasury) / 1e6).toFixed(1)}M`,
      positive: treasury >= 0,
    });
  }
  const rep = (next.group_reputation || 50) - (prev.group_reputation || 50);
  if (Math.abs(rep) > 0.5) {
    deltas.push({
      label: 'Reputation',
      value: `${rep >= 0 ? '+' : ''}${rep.toFixed(0)}`,
      positive: rep >= 0,
    });
  }
  return deltas;
}

const NODE_DELAY_MS = 800;
const INITIAL_DELAY = 600;

export default function ConsequenceReplay({
  roundNumber,
  choiceKey,
  commitResults,
  globalState,
  prevGlobalState,
  sessionId,
  onComplete,
}) {
  const [enabled, setEnabled] = useState(true);
  const [revealedStep, setRevealedStep] = useState(-1);
  const [done, setDone] = useState(false);

  // Respect prefers-reduced-motion
  const [prefersReduced, setPrefersReduced] = useState(false);
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReduced(mq.matches);
    const h = (e) => setPrefersReduced(e.matches);
    mq.addEventListener?.('change', h);
    return () => mq.removeEventListener?.('change', h);
  }, []);

  // Check facilitator toggle
  useEffect(() => {
    const q = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    fetch(`/api/admin/global-settings${q}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((s) => {
        if (s && s.consequence_replay_enabled === false) setEnabled(false);
      })
      .catch(() => {}); // fail-open: show by default
  }, [sessionId]);

  // Get the causal chain for this round+choice
  const chain = useMemo(() => {
    const roundChains = CAUSAL_CHAINS[roundNumber];
    if (!roundChains) return null;
    return roundChains[choiceKey] || null;
  }, [roundNumber, choiceKey]);

  // KPI deltas
  const deltas = useMemo(
    () => computeDeltas(prevGlobalState, commitResults?.globalState || globalState),
    [prevGlobalState, commitResults, globalState]
  );

  // Run the sequenced reveal
  useEffect(() => {
    if (!chain || !enabled) return;
    if (prefersReduced) {
      setRevealedStep(chain.length);
      setDone(true);
      return;
    }
    let step = -1;
    const timer = setTimeout(function tick() {
      step++;
      setRevealedStep(step);
      if (step < chain.length) {
        setTimeout(tick, NODE_DELAY_MS);
      } else {
        setDone(true);
      }
    }, INITIAL_DELAY);
    return () => clearTimeout(timer);
  }, [chain, enabled, prefersReduced]);

  const handleSkip = useCallback(() => {
    if (chain) setRevealedStep(chain.length);
    setDone(true);
    onComplete?.();
  }, [chain, onComplete]);

  const handleDismiss = useCallback(() => {
    onComplete?.();
  }, [onComplete]);

  // Don't render if disabled or no chain
  if (!enabled || !chain) return null;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.headerIcon}>🧬</span>
        <span className={styles.headerTitle}>Consequence Chain — Round {roundNumber}</span>
      </div>

      {/* The causal chain */}
      <div className={styles.chain}>
        {chain.map((node, i) => {
          const isVisible = i <= revealedStep;
          const typeClass =
            node.type === 'decision' ? styles.nodeDecision :
            node.type === 'mechanism' ? styles.nodeMechanism :
            node.type === 'future' ? styles.nodeFuture :
            styles.nodeImpact;

          return (
            <React.Fragment key={i}>
              {i > 0 && (
                <div className={`${styles.connector} ${isVisible ? styles.connectorVisible : ''}`}>
                  <div className={styles.connectorLine} />
                  <div className={styles.connectorArrow}>↓</div>
                </div>
              )}
              <div className={`${styles.node} ${typeClass} ${isVisible ? styles.nodeVisible : styles.nodeHidden}`}>
                <span className={styles.nodeIcon}>{node.icon}</span>
                <span className={styles.nodeLabel}>{node.label}</span>
              </div>
            </React.Fragment>
          );
        })}
      </div>

      {/* KPI deltas (shown when animation is done) */}
      {done && deltas.length > 0 && (
        <div className={styles.deltas}>
          {deltas.map((d) => (
            <div key={d.label} className={`${styles.delta} ${d.positive ? styles.deltaPositive : styles.deltaNegative}`}>
              <span className={styles.deltaLabel}>{d.label}</span>
              <span className={styles.deltaValue}>{d.value}</span>
            </div>
          ))}
        </div>
      )}

      {/* Controls */}
      <div className={styles.controls}>
        {!done && (
          <button className={styles.skipBtn} onClick={handleSkip}>Skip →</button>
        )}
        {done && (
          <button className={styles.dismissBtn} onClick={handleDismiss}>Continue ↓</button>
        )}
      </div>
    </div>
  );
}
