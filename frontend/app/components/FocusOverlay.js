'use client';
import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './FocusOverlay.module.css';
import { moneyM } from '../utils/format';

/**
 * STEP_META — metadata for each focus step.
 */
const STEP_META = {
  gate:       { icon: '⚖️', label: 'Pre-Requisite Gate' },
  strategy:   { icon: '📋', label: 'Strategic Decision' },
  allocation: { icon: '💰', label: 'Capital Allocation' },
  commit:     { icon: '🔮', label: 'Confirm & Submit' },
  waiting:    { icon: '⏳', label: 'Committed' },
  results:    { icon: '📊', label: 'Round Results' },
};

/**
 * FocusOverlay — Stepped decision focus mode wrapper.
 *
 * @param {boolean}  isOpen     - Whether the overlay is visible
 * @param {string}   step       - Current step key ('gate'|'strategy'|'allocation'|'commit'|'results')
 * @param {string[]} steps      - Ordered array of step keys for this round
 * @param {Function} onClose    - Called when the user wants to view the full dashboard
 * @param {Function} onReenter  - Called when the user re-enters focus mode (renders floating button)
 * @param {React.ReactNode} children - Step-specific content
 */
/**
 * Phase D: `variant` — 'takeover' (pre-Phase-D fullscreen overlay) or
 * 'inline' (the Decision Canvas: same header/content/breadcrumb rendered
 * in-flow inside the center column; no backdrop, no fixed positioning).
 * Header, Esc-to-dismiss, back navigation, and the re-enter button behave
 * identically in both variants.
 */
export default function FocusOverlay({ isOpen, step, steps, onClose, onBack, onReenter, children, variant = 'takeover' }) {
  const currentIdx = steps.indexOf(step);
  const canGoBack = currentIdx > 0 && step !== 'results';

  // Phase E (a11y): when the stage changes, move keyboard/screen-reader
  // focus so the flow is navigable without a mouse and each step announces
  // itself. The target used to be a heading in this header that repeated the
  // stage name; the stage now names itself in its own h2, so focus goes to
  // the panel region instead. Its aria-label already carries the step, so a
  // screen-reader user hears the step once and then the question — rather
  // than the same words twice at the same heading level.
  const panelRef = useRef(null);
  useEffect(() => {
    if (isOpen && step) panelRef.current?.focus();
  }, [isOpen, step]);

  // Escape key to dismiss
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  const inner = isOpen && step ? (
    <>
      {/* ── Header ──
          Navigation only. It used to also announce "📋 Strategic Decision ·
          Step 2 / 3" — which, once each stage grew a headline of its own,
          named the screen twice in fourteen vertical pixels of each other.
          Step POSITION is not lost with the badge: the round checklist under
          the canvas already names all five steps and marks the current one,
          at a granularity the 1-of-3 badge never had. */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          {canGoBack && (
            <button
              className={styles.backButton}
              onClick={() => onBack?.(steps[currentIdx - 1])}
              title={`Back to ${STEP_META[steps[currentIdx - 1]]?.label}`}
            >
              ← Back
            </button>
          )}
        </div>
        <button
          className={styles.closeButton}
          onClick={onClose}
          title="View Full Dashboard (Esc)"
        >
          📊 Dashboard
        </button>
      </div>

      {/* ── Content ── */}
      <div className={styles.content}>
        {children}
      </div>

      {/* ── Step Breadcrumb ──
          INLINE ONLY DROPS IT. In the canvas the action bar's step row sits
          directly beneath this — "Briefing · Materiality assessment · Decision
          · Capital · Commit", named and marked — so three emoji dots above it
          were the third statement of where you are on one screen, after the
          header (now gone) and the bar. Named steps beat dotted ones anyway:
          a dot tells you there are five things and you are on the third; the
          words tell you the third is Decision.

          TAKEOVER KEEPS IT. That variant is the CANVAS_FIRST rollback — a
          fullscreen overlay covering the cockpit, and therefore covering the
          action bar. Removing the breadcrumb there would leave a player with
          no position indicator at all, which is a worse screen than the one
          this change improves. */}
      {variant !== 'inline' && (
      <div className={styles.breadcrumb}>
        {steps.flatMap((s, i) => {
          const els = [
            <div
              key={s}
              className={[
                styles.breadcrumbDot,
                i < currentIdx ? styles.breadcrumbComplete : '',
                i === currentIdx ? styles.breadcrumbActive : '',
              ].filter(Boolean).join(' ')}
            >
              <span>{STEP_META[s]?.icon}</span>
            </div>,
          ];
          if (i < steps.length - 1) {
            els.push(
              <div
                key={`line-${i}`}
                className={[
                  styles.breadcrumbLine,
                  i < currentIdx ? styles.breadcrumbLineComplete : '',
                ].filter(Boolean).join(' ')}
              />
            );
          }
          return els;
        })}
      </div>
      )}
    </>
  ) : null;

  if (variant === 'inline') {
    return (
      <>
        <AnimatePresence>
          {isOpen && step && (
            <motion.div
              ref={panelRef}
              tabIndex={-1}
              className={`${styles.panel} ${styles.panelInline}`}
              role="region"
              aria-label={`Decision canvas — ${STEP_META[step]?.label || 'round flow'}`}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
            >
              {inner}
            </motion.div>
          )}
        </AnimatePresence>
        {!isOpen && onReenter && (
          <motion.button
            className={styles.reenterButton}
            onClick={onReenter}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            title="Re-enter guided flow"
          >
            🎯 Focus Mode
          </motion.button>
        )}
      </>
    );
  }

  return (
    <>
      <AnimatePresence>
        {isOpen && step && (
          <motion.div
            className={styles.backdrop}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            onClick={onClose}
          >
            <motion.div
              ref={panelRef}
              tabIndex={-1}
              role="region"
              aria-label={`Decision stage — ${STEP_META[step]?.label || 'round flow'}`}
              className={styles.panel}
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.97, opacity: 0, y: -10 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
              onClick={(e) => e.stopPropagation()}
            >
              {inner}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Re-enter Focus Mode floating button (visible when dismissed) */}
      {!isOpen && onReenter && (
        <motion.button
          className={styles.reenterButton}
          onClick={onReenter}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          title="Re-enter Focus Mode"
        >
          🎯 Focus Mode
        </motion.button>
      )}
    </>
  );
}

/**
 * KPIStrip — the belt. What the round has done to you, above what you are
 * about to do about it.
 *
 * WHAT IT REPLACED. Five bordered pills, each an emoji then a 12px label then
 * a 12px value, all on one line. Three problems. The values were the same size
 * as their labels, so the number a team argues about had no more presence than
 * the word next to it. The emoji were the loudest thing in each pill and carry
 * no information a reader does not already have from the label. And not one
 * pill said whether the figure had MOVED — a treasury of 11.0M means nothing
 * without last round's, and the delta was available all along in
 * previousGlobalState, three lines away in the same component.
 *
 * Now: label above, value at display size in tabular figures, movement beneath
 * in words and a sign glyph. Colour is never the only encoding — the sign
 * travels with the number, and "vs R2" says what it is measured against
 * instead of leaving the reader to assume.
 */
export function KPIStrip({
  treasury, reputation, carbon, ebitda, projectedCost, fmtCurrency,
  previous, roundNumber, cohortCommits, cohortTeamCount,
}) {
  const fmt = fmtCurrency || ((v) => moneyM(Math.abs(v)));
  const prevRound = roundNumber > 1 ? `vs R${roundNumber - 1}` : 'first round';

  /* A delta is rendered ONLY when there is a previous value to subtract. A
     round-1 player has no history, and inventing a zero would state that
     nothing changed rather than that nothing is known yet. */
  const move = (now, then, format, higherIsBetter = true) => {
    /* No prior snapshot — round 1, or a session whose history has not yet
       accumulated one. An empty line is honest; "vs R1" alone reads as a
       comparison that was made and came back blank. */
    if (then == null || now == null) return { text: '', dir: null };
    const d = now - then;
    if (d === 0) return { text: `unchanged ${prevRound}`, dir: null };
    return {
      text: `${d > 0 ? '+' : '−'}${format(Math.abs(d))} ${prevRound}`,
      dir: (d > 0) === higherIsBetter ? 'up' : 'down',
    };
  };

  const num = (v) => Math.round(v).toLocaleString();
  const tiles = [
    { label: 'Treasury',   value: fmt(treasury),                    ...move(treasury, previous?.corporate_treasury, fmt) },
    { label: 'EBITDA',     value: fmt(ebitda),                      ...move(ebitda, previous?.historical_ebitda, fmt) },
    { label: 'Reputation', value: (reputation || 0).toFixed(0),     ...move(reputation, previous?.group_reputation, (v) => v.toFixed(0)) },
    { label: 'Carbon',     value: num(carbon || 0),                 ...move(carbon, previous?.tco2e_emissions, num, false) },
  ];
  if (cohortTeamCount > 1) {
    tiles.push({
      label: 'Committed',
      value: `${cohortCommits || 0} of ${cohortTeamCount}`,
      text: 'teams', dir: null,
    });
  }
  /* SIGN. projectedCost is opt.impacts.treasury, and the engine writes a
     COST as a NEGATIVE treasury delta — Option A's -2.5M means 2.5M leaves.
     I had this inverted, so a decision that spent 2.5M announced itself as
     "freed this round" in the positive colour. */
  if (projectedCost !== 0 && projectedCost != null) {
    tiles.push({
      label: 'Staged',
      value: fmt(Math.abs(projectedCost)),
      text: projectedCost < 0 ? 'to spend this round' : 'freed this round',
      dir: projectedCost < 0 ? 'down' : 'up',
    });
  }

  return (
    <div className={styles.belt}>
      {tiles.map((t) => (
        <div key={t.label} className={styles.beltTile}>
          <div className={styles.beltLabel}>{t.label}</div>
          <div className={styles.beltValue}>{t.value}</div>
          <div className={styles.beltDelta} data-dir={t.dir || undefined}>{t.text}</div>
        </div>
      ))}
    </div>
  );
}
