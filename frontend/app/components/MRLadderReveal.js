/**
 * MRLadderReveal — WOW-10
 *
 * A sequenced, animated stacking visualization of every M_R component.
 * Each bonus/penalty animates into place one-by-one, so players watch
 * their value assemble piece-by-piece, understanding how each of their
 * decisions across 10 rounds contributed to or destroyed terminal value.
 *
 * Pure presentation — reads the same data as RegretMeter (mrJourney.js).
 * No engine, round-flow, or commit-payload changes.
 *
 * Props:
 *   mr     — actual Regenerative Multiple (number)
 *   flags  — globalState.active_event_flags (object)
 *   onComplete — optional callback when animation finishes
 */
'use client';
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { MR_OPPORTUNITIES, computeMrRegret } from '../utils/mrJourney';
import styles from './MRLadderReveal.module.css';

/** Category icons and colours for each M_R opportunity. */
const CATEGORY_THEME = {
  governance: { icon: '🏛️', color: '#8b5cf6' },
  climate:    { icon: '🌍', color: '#10b981' },
  strategic:  { icon: '🎯', color: '#3b82f6' },
  social:     { icon: '👥', color: '#f59e0b' },
};

const BASE_MR = 1.0;
const STEP_DELAY_MS = 600;   // time between each row appearing
const INITIAL_DELAY_MS = 800; // pause before first row starts

export default function MRLadderReveal({ mr = 0, flags = {}, onComplete }) {
  const { items } = useMemo(() => computeMrRegret(flags || {}), [flags]);
  const actual = Number(mr) || 0;

  // Animation state: how many rows have been revealed (-1 = base only)
  const [revealedCount, setRevealedCount] = useState(-1);
  const [animationDone, setAnimationDone] = useState(false);

  // Respect prefers-reduced-motion
  const [prefersReduced, setPrefersReduced] = useState(false);
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReduced(mq.matches);
    const handler = (e) => setPrefersReduced(e.matches);
    mq.addEventListener?.('change', handler);
    return () => mq.removeEventListener?.('change', handler);
  }, []);

  // Run the staggered reveal
  useEffect(() => {
    if (prefersReduced) {
      setRevealedCount(items.length);
      setAnimationDone(true);
      onComplete?.();
      return;
    }
    let step = -1;
    const timer = setTimeout(function tick() {
      step++;
      setRevealedCount(step);
      if (step < items.length) {
        setTimeout(tick, STEP_DELAY_MS);
      } else {
        setAnimationDone(true);
        onComplete?.();
      }
    }, INITIAL_DELAY_MS);
    return () => clearTimeout(timer);
  }, [items.length, prefersReduced]); // eslint-disable-line react-hooks/exhaustive-deps

  // Skip animation
  const handleSkip = useCallback(() => {
    setRevealedCount(items.length);
    setAnimationDone(true);
    onComplete?.();
  }, [items.length, onComplete]);

  // Build the running total as rows reveal
  const runningTotal = useMemo(() => {
    let total = BASE_MR;
    return items.map((item) => {
      if (item.captured) total += item.mr;
      return total;
    });
  }, [items]);

  const finalTotal = animationDone ? actual : (revealedCount >= 0 && revealedCount < runningTotal.length ? runningTotal[revealedCount] : BASE_MR);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerIcon}>📊</div>
        <div className={styles.headerTitle}>Regenerative Multiple Breakdown</div>
        <div className={styles.headerSubtitle}>How your decisions built (or blocked) terminal value</div>
      </div>

      {/* Base row — always visible */}
      <div className={`${styles.row} ${styles.rowBase} ${styles.rowVisible}`}>
        <div className={styles.rowLeft}>
          <span className={styles.rowIcon}>🏗️</span>
          <span className={styles.rowLabel}>Base Multiple</span>
        </div>
        <div className={styles.rowRight}>
          <span className={styles.rowValue} style={{ color: 'var(--text-primary, #f1f5f9)' }}>+{BASE_MR.toFixed(2)}</span>
          <div className={styles.rowBar}>
            <div className={styles.rowBarFill} style={{ width: `${(BASE_MR / 2.0) * 100}%`, background: 'var(--accent-blue, #3b82f6)' }} />
          </div>
        </div>
      </div>

      {/* M_R opportunity rows — revealed one-by-one */}
      {items.map((item, i) => {
        const isVisible = i <= revealedCount;
        const theme = CATEGORY_THEME[item.category] || CATEGORY_THEME.governance;
        const isCaptured = item.captured;
        const isBlocked = !isCaptured && item.blockedByFlags;

        return (
          <div
            key={item.flag}
            className={`${styles.row} ${isVisible ? styles.rowVisible : styles.rowHidden} ${!isCaptured ? styles.rowMissed : ''} ${isBlocked ? styles.rowBlocked : ''}`}
            style={{ transitionDelay: prefersReduced ? '0ms' : `${i * 50}ms` }}
          >
            <div className={styles.rowLeft}>
              <span className={styles.rowRound}>R{item.round}</span>
              <span className={styles.rowIcon}>{theme.icon}</span>
              <span className={styles.rowLabel}>
                {item.label}
                {isBlocked && <span className={styles.blockedBadge}>BLOCKED</span>}
                {!isCaptured && !isBlocked && <span className={styles.missedBadge}>MISSED</span>}
              </span>
            </div>
            <div className={styles.rowRight}>
              <span
                className={styles.rowValue}
                style={{ color: isCaptured ? theme.color : 'var(--kpi-warn, #f59e0b)' }}
              >
                {isCaptured ? '+' : '✗ +'}{item.mr.toFixed(2)}
              </span>
              <div className={styles.rowBar}>
                <div
                  className={`${styles.rowBarFill} ${!isCaptured ? styles.rowBarMissed : ''}`}
                  style={{
                    width: isVisible ? `${(item.mr / 2.0) * 100}%` : '0%',
                    background: isCaptured
                      ? `linear-gradient(90deg, ${theme.color}, ${theme.color}88)`
                      : 'repeating-linear-gradient(45deg, rgba(245,158,11,0.2) 0 4px, transparent 4px 8px)',
                  }}
                />
              </div>
            </div>
          </div>
        );
      })}

      {/* Divider */}
      <div className={`${styles.divider} ${animationDone ? styles.dividerVisible : ''}`} />

      {/* Final total */}
      <div className={`${styles.totalRow} ${animationDone ? styles.totalVisible : ''}`}>
        <div className={styles.totalLabel}>Your Regenerative Multiple</div>
        <div
          className={styles.totalValue}
          style={{
            color: actual >= 1.8 ? '#10b981'
              : actual >= 1.2 ? '#3b82f6'
              : actual >= 0.8 ? '#f59e0b'
              : '#ef4444',
          }}
        >
          {finalTotal.toFixed(2)}×
        </div>
      </div>

      {/* Skip button */}
      {!animationDone && (
        <button className={styles.skipBtn} onClick={handleSkip}>
          Skip →
        </button>
      )}
    </div>
  );
}
