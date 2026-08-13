/**
 * ConsequenceReplay — WOW-1
 *
 * An auto-playing animated causal chain that fires after each round commit,
 * visually tracing the decision through the engine's flag dependency graph.
 * Each node lights up in sequence with the impact value.
 *
 * ── UX audit #21: "Complete the consequence chain" ──────────────────────────
 * This component used to build its explanation from a hardcoded list of a few
 * event keys (talent_penalty_applied, loan_interest_payment, cyclone_loss —
 * the last of which the engine never actually emits), then fell back to "the
 * first 3 truthy flags". Every other engine effect was silently absent from
 * the player's "why did this happen" story, and a missing node is invisible:
 * it looks identical to an effect that never fired.
 *
 * The chain is now catalog-driven. It walks EVERY truthy key in the round's
 * active_event_flags:
 *   • known key   → rendered from consequenceCatalog.js (label + mechanism +
 *                   a plain-English sentence)
 *   • unknown key → still rendered, with a humanised label (and the engine's
 *                   own `*_message` / `*_because` string when one exists)
 *   • ignored key → only if it is in the documented IGNORED_KEYS set, so an
 *                   omission is always a decision on the record, never a gap.
 *
 * SAFETY: Pure presentation. Reads existing consequence data from the commit
 * results — no backend file was changed and no engine behaviour is affected.
 * Skippable via "Skip →" button. Gated by `consequence_replay_enabled`
 * facilitator toggle.
 *
 * Props (unchanged):
 *   commitResults  — the commit response object
 *   sessionId      — for settings fetch
 *   roundNumber    — current round
 *   globalState    — current global state
 *   onSkip         — callback when user skips the animation
 */
'use client';
import React, { useState, useEffect, useMemo } from 'react';
import styles from './ConsequenceReplay.module.css';
import {
  CONSEQUENCE_CATALOG,
  lookupConsequence,
  isIgnoredKey,
  humaniseKey,
  money,
} from './consequenceCatalog';
import { currencySymbol, atRate } from '../utils/format';

/** Node type per severity — reuses the existing four CSS treatments. */
const SEVERITY_NODE_TYPE = {
  bad: 'impact',
  good: 'consequence',
  neutral: 'mechanism',
};

/** Fallback icons when a catalog entry does not carry one. */
const SEVERITY_ICON = { bad: '⚠️', good: '✨', neutral: '⚙️' };

/**
 * Compact monospace figure for the node's value line. Deliberately terse —
 * the full explanation lives in the sentence underneath.
 */
function compactValue(key, value) {
  if (value === true) return 'Triggered';
  if (typeof value === 'number') {
    if (!isFinite(value)) return null;
    if (Math.abs(value) >= 10_000) return money(value);
    if (Number.isInteger(value)) return String(value);
    return value.toFixed(2);
  }
  if (typeof value === 'string') return null;      // the string IS the sentence
  if (Array.isArray(value)) return `${value.length} item${value.length === 1 ? '' : 's'}`;
  return null;
}

/**
 * The engine writes its own rationale into `*_message` / `*_because` /
 * `*_narrative` keys. When we have no catalog entry, that string is a better
 * explanation than anything we could synthesise — use it verbatim.
 */
function engineProseFor(key, value, flags) {
  if (typeof value === 'string' && value.trim() && /(_message|_because|_narrative|_desc|_reason)$/.test(key)) {
    return value.trim();
  }
  for (const suffix of ['_message', '_because', '_narrative']) {
    const prose = flags[`${key}${suffix}`];
    if (typeof prose === 'string' && prose.trim()) return prose.trim();
  }
  return null;
}

/** Safely run a catalog entry's explain() — a bad flag payload must never blank the panel. */
function safeExplain(entry, value, globalState) {
  try {
    const sentence = entry.explain(value, globalState);
    return typeof sentence === 'string' && sentence.trim() ? sentence.trim() : null;
  } catch {
    return null;
  }
}

/**
 * Build the causal chain from commit results.
 * Each node = { key, label, value, explain, mechanism, type, icon }
 */
export function buildChain(commitResults, roundNumber, globalStateProp) {
  if (!commitResults) return [];
  const chain = [];
  const gs = commitResults.globalState || globalStateProp || {};
  const events = commitResults.events || {};
  // engine.py `_assemble_global_state` writes the same dict to both, but a
  // partial commit response may only carry one — merge so neither is lost.
  const flags = { ...(gs.active_event_flags || {}), ...events };

  // ── Node 1: the decision itself ──────────────────────────────
  const choice = commitResults.choiceLabel || commitResults.choice_selected || 'Decision Made';
  chain.push({ key: '__decision__', label: choice, value: null, type: 'decision', icon: '🎯' });

  // ── Nodes 2-3: headline mechanisms (treasury + reputation) ───
  const treasuryDelta = events.treasury_delta || events.net_treasury_change || 0;
  if (treasuryDelta !== 0) {
    chain.push({
      key: '__treasury__',
      label: 'Treasury Impact',
      value: `${treasuryDelta >= 0 ? '+' : ''}${currencySymbol()}${atRate(treasuryDelta / 1_000_000).toFixed(1)}M`,
      type: 'mechanism',
      icon: treasuryDelta >= 0 ? '💰' : '💸',
    });
  }

  const repDelta = events.reputation_delta || 0;
  if (repDelta !== 0) {
    chain.push({
      key: '__reputation__',
      label: 'Reputation Change',
      value: `${repDelta >= 0 ? '+' : ''}${repDelta.toFixed(1)} pts`,
      type: 'mechanism',
      icon: repDelta >= 0 ? '📈' : '📉',
    });
  }

  // ── Every truthy engine flag, catalog-driven ─────────────────
  // No slicing, no "first 3". If the engine did it, the player sees it.
  const known = [];
  const unknown = [];

  for (const [key, value] of Object.entries(flags)) {
    if (!value) continue;                       // falsy = the effect did not fire
    if (Array.isArray(value) && value.length === 0) continue;
    if (isIgnoredKey(key)) continue;            // documented exclusion, see catalog

    const entry = lookupConsequence(key);
    if (entry) {
      known.push({
        key,
        label: entry.label,
        value: compactValue(key, value),
        explain: safeExplain(entry, value, gs) || engineProseFor(key, value, flags),
        mechanism: entry.mechanism,
        severity: entry.severity,
        type: SEVERITY_NODE_TYPE[entry.severity] || 'mechanism',
        icon: entry.icon || SEVERITY_ICON[entry.severity] || '⚙️',
      });
    } else {
      // UNKNOWN KEY — still rendered. This is the whole point of audit #21:
      // an effect the catalog has not caught up with must never vanish.
      unknown.push({
        key,
        label: humaniseKey(key),
        value: compactValue(key, value),
        explain:
          engineProseFor(key, value, flags) ||
          // a bare prose string on an uncatalogued key is still worth showing
          (typeof value === 'string' && value.trim().length > 12 ? value.trim() : null),
        mechanism: 'Engine effect recorded this round. No plain-English explanation is catalogued for it yet.',
        severity: 'neutral',
        type: 'mechanism',
        icon: '🔓',
        uncatalogued: true,
      });
    }
  }

  // Bad news first (that is what the player needs to understand), then wins,
  // then neutral state, then anything the catalog has not caught up with.
  const rank = { bad: 0, good: 1, neutral: 2 };
  known.sort((a, b) => rank[a.severity] - rank[b.severity]);

  return chain.concat(known, unknown);
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

  const chain = useMemo(
    () => buildChain(commitResults, roundNumber, globalState),
    [commitResults, roundNumber, globalState]
  );

  // Auto-play animation: reveal one node every 800ms.
  // A complete chain can now be long, so the cadence compresses to keep the
  // whole reveal inside ~8s — the short-chain feel (800ms) is unchanged.
  useEffect(() => {
    if (!enabled || skipped || chain.length === 0) return;
    setVisibleNodes(0);
    const step = chain.length <= 10 ? 800 : Math.max(120, Math.round(8000 / chain.length));
    const timers = chain.map((_, i) =>
      setTimeout(() => setVisibleNodes(i + 1), step * (i + 1))
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
          <React.Fragment key={node.key || i}>
            {i > 0 && (
              <div className={`${styles.connector} ${i < visibleNodes ? styles.connectorVisible : ''}`}>
                <div className={styles.connectorLine} />
                <div className={styles.connectorArrow}>▼</div>
              </div>
            )}
            <div
              className={`${styles.node} ${styles[`node_${node.type}`]} ${i < visibleNodes ? styles.nodeVisible : ''}`}
              style={{ animationDelay: `${i * 0.1}s` }}
              data-flag-key={node.key}
              title={node.mechanism || undefined}
            >
              <span className={styles.nodeIcon}>{node.icon}</span>
              <div className={styles.nodeContent}>
                <div className={styles.nodeLabel}>{node.label}</div>
                {node.value && <div className={styles.nodeValue}>{node.value}</div>}
                {node.explain && <div className={styles.nodeExplain}>{node.explain}</div>}
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
