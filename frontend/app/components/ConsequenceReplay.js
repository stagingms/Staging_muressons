/**
 * ConsequenceReplay — WOW-1
 *
 * An auto-playing animated causal chain that fires after each round commit,
 * visually tracing the decision through the engine's flag dependency graph.
 * Each node lights up in sequence with the impact value.
 *
 * SAFETY: Pure presentation. Reads existing consequence_dna data from the
 * commit results. Falls back to a simple "Top 3 impacts" list if no
 * consequence data is available. Skippable via "Skip →" button.
 * Gated by `consequence_replay_enabled` facilitator toggle.
 *
 * Props:
 *   commitResults  — the commit response object
 *   sessionId      — for settings fetch
 *   roundNumber    — current round
 *   globalState    — current global state
 *   onSkip         — callback when user skips the animation
 */
'use client';
import React, { useState, useEffect, useMemo } from 'react';
import styles from './ConsequenceReplay.module.css';

/**
 * Build a simplified causal chain from commit results.
 * Each node = { label, value, type: 'decision'|'mechanism'|'impact'|'consequence' }
 */
function buildChain(commitResults, roundNumber) {
  if (!commitResults) return [];
  const chain = [];
  const gs = commitResults.globalState || {};
  const events = commitResults.events || {};
  const flags = gs.active_event_flags || {};

  // Node 1: The decision itself
  const choice = commitResults.choiceLabel || commitResults.choice_selected || 'Decision Made';
  chain.push({ label: choice, value: null, type: 'decision', icon: '🎯' });

  // Node 2-3: Key mechanisms (treasury + reputation changes)
  const treasuryDelta = events.treasury_delta || events.net_treasury_change || 0;
  if (treasuryDelta !== 0) {
    chain.push({
      label: 'Treasury Impact',
      value: `${treasuryDelta >= 0 ? '+' : ''}$${(treasuryDelta / 1_000_000).toFixed(1)}M`,
      type: 'mechanism',
      icon: treasuryDelta >= 0 ? '💰' : '💸',
    });
  }

  const repDelta = events.reputation_delta || 0;
  if (repDelta !== 0) {
    chain.push({
      label: 'Reputation Change',
      value: `${repDelta >= 0 ? '+' : ''}${repDelta.toFixed(1)} pts`,
      type: 'mechanism',
      icon: repDelta >= 0 ? '📈' : '📉',
    });
  }

  // Node 4: Key impacts from events
  if (events.talent_penalty_applied > 1) {
    chain.push({
      label: 'Brain-Drain Penalty',
      value: `+${((events.talent_penalty_applied - 1) * 100).toFixed(0)}% OPEX`,
      type: 'impact',
      icon: '🧠',
    });
  }
  if (events.loan_interest_payment > 0) {
    chain.push({
      label: 'Loan Interest',
      value: `-$${(events.loan_interest_payment / 1_000_000).toFixed(1)}M`,
      type: 'impact',
      icon: '🏦',
    });
  }
  if (events.cyclone_loss > 0) {
    chain.push({
      label: 'Cyclone Damage',
      value: `-$${(events.cyclone_loss / 1_000_000).toFixed(1)}M`,
      type: 'impact',
      icon: '🌪️',
    });
  }

  // Node 5: Future consequences (flag-based)
  const newFlags = Object.entries(flags).filter(([k, v]) => v === true).slice(0, 3);
  for (const [flag] of newFlags) {
    const label = flag.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    chain.push({
      label,
      value: 'Unlocked',
      type: 'consequence',
      icon: '🔓',
    });
  }

  return chain.slice(0, 6); // Max 6 nodes for readability
}

export default function ConsequenceReplay({ commitResults, sessionId, roundNumber, globalState, onSkip }) {
  const [enabled, setEnabled] = useState(true);
  const [visibleNodes, setVisibleNodes] = useState(0);
  const [skipped, setSkipped] = useState(false);

  // Check facilitator toggle
  useEffect(() => {
    if (!sessionId) return;
    const q = `?session_id=${encodeURIComponent(sessionId)}`;
    fetch(`/api/admin/global-settings${q}`)
      .then(r => r.ok ? r.json() : null)
      .then(s => { if (s && s.consequence_replay_enabled === false) setEnabled(false); })
      .catch(() => {});
  }, [sessionId]);

  const chain = useMemo(() => buildChain(commitResults, roundNumber), [commitResults, roundNumber]);

  // Auto-play animation: reveal one node every 800ms
  useEffect(() => {
    if (!enabled || skipped || chain.length === 0) return;
    setVisibleNodes(0);
    const timers = chain.map((_, i) =>
      setTimeout(() => setVisibleNodes(i + 1), 800 * (i + 1))
    );
    return () => timers.forEach(clearTimeout);
  }, [chain, enabled, skipped]);

  const handleSkip = () => {
    setSkipped(true);
    setVisibleNodes(chain.length);
    if (onSkip) onSkip();
  };

  if (!enabled || !commitResults || chain.length === 0) return null;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.title}>🧬 Consequence Replay</span>
        <button className={styles.skipBtn} onClick={handleSkip}>
          {skipped ? '✓ Complete' : 'Skip →'}
        </button>
      </div>

      <div className={styles.chain}>
        {chain.map((node, i) => (
          <React.Fragment key={i}>
            {i > 0 && (
              <div className={`${styles.connector} ${i < visibleNodes ? styles.connectorVisible : ''}`}>
                <div className={styles.connectorLine} />
                <div className={styles.connectorArrow}>▼</div>
              </div>
            )}
            <div
              className={`${styles.node} ${styles[`node_${node.type}`]} ${i < visibleNodes ? styles.nodeVisible : ''}`}
              style={{ animationDelay: `${i * 0.1}s` }}
            >
              <span className={styles.nodeIcon}>{node.icon}</span>
              <div className={styles.nodeContent}>
                <div className={styles.nodeLabel}>{node.label}</div>
                {node.value && <div className={styles.nodeValue}>{node.value}</div>}
              </div>
              <span className={`${styles.nodeTypeBadge} ${styles[`badge_${node.type}`]}`}>
                {node.type}
              </span>
            </div>
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
