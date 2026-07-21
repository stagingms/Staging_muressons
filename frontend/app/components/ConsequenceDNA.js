'use client';
import React, { useMemo } from 'react';
import styles from './ExecutiveCockpit.module.css';

/**
 * ConsequenceDNA — Phase 3.3
 * Visualises causal chains linking past decisions to current outcomes.
 * Shows: Decision Node → Effect Node → Future Risk Node
 *
 * Appears from Round 4+ (Crisis tier onward) to help players
 * understand cross-round dependencies and flag cascades.
 *
 * Props:
 *   - history:     round history array
 *   - roundNumber: current round
 *   - globalState: current global state (for active flags)
 *   - events:      current round events
 */

// Map known flags to their causal chains
const FLAG_CHAINS = {
  electronics_blindspot: {
    source: { round: 1, label: 'R1: Ignored Electronics BU', type: 'decision' },
    effect: { label: 'R4 Crisis severity ×2', type: 'effect' },
    future: { label: 'R10 M_R penalty', type: 'future' },
  },
  insurance_only: {
    source: { round: 5, label: 'R5: Insurance-only approach', type: 'decision' },
    effect: { label: 'Resilience Champion locked out', type: 'effect' },
    future: { label: 'Terminal M_R capped', type: 'future' },
  },
  ai_monetised: {
    source: { round: 6, label: 'R6: Monetised AI data', type: 'decision' },
    effect: { label: 'Short-term revenue boost', type: 'effect' },
    future: { label: 'R7+ compliance costs', type: 'future' },
  },
  early_decarboniser: {
    source: { round: 3, label: 'R3: Early decarbonisation', type: 'decision' },
    effect: { label: 'Carbon intensity < 35', type: 'effect' },
    future: { label: '+0.15 M_R bonus at R10', type: 'future' },
  },
  greenwash_risk: {
    source: { round: 2, label: 'R2: Weak CSRD disclosure', type: 'decision' },
    effect: { label: 'Greenwashing vulnerability', type: 'effect' },
    future: { label: 'R7 reputation penalty', type: 'future' },
  },
  civil_water_priority: {
    source: { round: 8, label: 'R8: Prioritised community water', type: 'decision' },
    effect: { label: 'Social license protected', type: 'effect' },
    future: { label: 'R10 stakeholder support', type: 'future' },
  },
  electronics_water_priority: {
    source: { round: 8, label: 'R8: Prioritised factory water', type: 'decision' },
    effect: { label: 'Production continuity', type: 'effect' },
    future: { label: 'Community trust risk', type: 'future' },
  },
  materiality_aligned: {
    source: { round: 2, label: 'R2: Materiality-aligned disclosure', type: 'decision' },
    effect: { label: 'Governance credibility +', type: 'effect' },
    future: { label: '+0.10 M_R at R10', type: 'future' },
  },
  // ── Shadow Board Audit (R5) — Value Judgment Cascades ──
  shareholder_alienated: {
    source: { round: 5, label: 'R5: Rejected Shareholder Logic', type: 'decision' },
    effect: { label: 'Investor confidence eroded', type: 'effect' },
    future: { label: 'R10 Hostile Takeover risk ↑', type: 'future' },
  },
  planet_expendable: {
    source: { round: 5, label: 'R5: Rejected Environmental Logic', type: 'decision' },
    effect: { label: 'Ecosystem resilience undermined', type: 'effect' },
    future: { label: 'R10 Climate/Revolt risk ↑', type: 'future' },
  },
  governance_fragility: {
    source: { round: 5, label: 'R5: Rejected Governance Logic', type: 'decision' },
    effect: { label: 'Regulatory scrutiny increased', type: 'effect' },
    future: { label: 'R10 Regulatory Shutdown risk ↑', type: 'future' },
  },
};

export default function ConsequenceDNA({ history, roundNumber, globalState, events }) {
  const chains = useMemo(() => {
    if (roundNumber < 4) return [];
    const activeFlags = globalState?.active_event_flags || {};
    const result = [];

    for (const [flag, chain] of Object.entries(FLAG_CHAINS)) {
      if (activeFlags[flag] && chain.source.round < roundNumber) {
        result.push({ flag, ...chain });
      }
    }

    // Sort by source round (most recent first)
    result.sort((a, b) => b.source.round - a.source.round);
    return result.slice(0, 3); // Show top 3 most relevant chains
  }, [roundNumber, globalState]);

  if (chains.length === 0) return null;

  const nodeClass = (type) => {
    switch (type) {
      case 'decision': return styles.consequenceNodeDecision;
      case 'effect': return styles.consequenceNodeEffect;
      case 'future': return styles.consequenceNodeFuture;
      default: return '';
    }
  };

  return (
    <div className={styles.consequenceDna}>
      <div className={styles.consequenceDnaTitle}>
        <span>🧬</span>
        <span>CONSEQUENCE DNA — Your Decisions, Traced</span>
      </div>
      {chains.map((chain, i) => (
        <div key={chain.flag} className={styles.consequenceChain}>
          <span className={`${styles.consequenceNode} ${nodeClass(chain.source.type)}`}>
            {chain.source.label}
          </span>
          <span className={styles.consequenceArrow}>→</span>
          <span className={`${styles.consequenceNode} ${nodeClass(chain.effect.type)}`}>
            {chain.effect.label}
          </span>
          <span className={styles.consequenceArrow}>→</span>
          <span className={`${styles.consequenceNode} ${nodeClass(chain.future.type)}`}>
            {chain.future.label}
          </span>
        </div>
      ))}
    </div>
  );
}
