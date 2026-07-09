'use client';
import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './FocusOverlay.module.css';

/**
 * STEP_META — metadata for each focus step.
 */
const STEP_META = {
  gate:       { icon: '⚖️', label: 'Pre-Requisite Gate' },
  strategy:   { icon: '📋', label: 'Strategic Decision' },
  allocation: { icon: '💰', label: 'Capital Allocation' },
  commit:     { icon: '🔮', label: 'Confirm & Submit' },
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
      {/* ── Header ── */}
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
          <span className={styles.stepIcon}>{STEP_META[step]?.icon}</span>
          <span className={styles.stepLabel}>{STEP_META[step]?.label}</span>
          <span className={styles.stepBadge}>
            Step {currentIdx + 1} / {steps.length}
          </span>
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

      {/* ── Step Breadcrumb ── */}
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
    </>
  ) : null;

  if (variant === 'inline') {
    return (
      <>
        <AnimatePresence>
          {isOpen && step && (
            <motion.div
              className={`${styles.panel} ${styles.panelInline}`}
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
 * KPIStrip — Compact horizontal KPI reference bar for use inside focus overlays.
 */
export function KPIStrip({ treasury, reputation, carbon, ebitda, projectedCost, fmtCurrency }) {
  const fmt = fmtCurrency || ((v) => `$${(Math.abs(v) / 1_000_000).toFixed(1)}M`);
  return (
    <div className={styles.kpiStrip}>
      <div className={styles.kpiPill}>
        <span className={styles.kpiPillIcon}>💰</span>
        <span className={styles.kpiPillLabel}>Treasury</span>
        <span className={styles.kpiPillValue}>{fmt(treasury)}</span>
      </div>
      <div className={styles.kpiPill}>
        <span className={styles.kpiPillIcon}>🌍</span>
        <span className={styles.kpiPillLabel}>Reputation</span>
        <span className={styles.kpiPillValue}>{(reputation || 0).toFixed(0)}/100</span>
      </div>
      <div className={styles.kpiPill}>
        <span className={styles.kpiPillIcon}>🏭</span>
        <span className={styles.kpiPillLabel}>Carbon</span>
        <span className={styles.kpiPillValue}>{(carbon || 0).toLocaleString()}t</span>
      </div>
      <div className={styles.kpiPill}>
        <span className={styles.kpiPillIcon}>📈</span>
        <span className={styles.kpiPillLabel}>EBITDA</span>
        <span className={styles.kpiPillValue}>{fmt(ebitda)}</span>
      </div>
      {projectedCost !== 0 && projectedCost != null && (
        <div className={styles.kpiPill} style={{ borderColor: projectedCost > 0 ? 'rgba(248,113,113,0.25)' : 'rgba(74,222,128,0.25)' }}>
          <span className={styles.kpiPillIcon}>{projectedCost > 0 ? '📉' : '📈'}</span>
          <span className={styles.kpiPillLabel}>Staged</span>
          <span className={styles.kpiPillValue} style={{ color: projectedCost > 0 ? '#f87171' : '#4ade80' }}>
            {fmt(Math.abs(projectedCost))}
          </span>
        </div>
      )}
    </div>
  );
}
