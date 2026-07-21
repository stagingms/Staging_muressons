'use client';

/**
 * ArchetypeReveal — Capstone summary screen, Round 10 terminal state.
 *
 * ── Z-Index Contract ──────────────────────────────────────────────────────
 * This component renders as a FIXED VIEWPORT OVERLAY at z-index 9999,
 * intentionally above every other stacking context in the app (including
 * --z-briefing: 9001). It must be mounted via an early-return in page.js
 * so the entire cockpit tree never renders underneath it. See integration
 * snippet at bottom of this file.
 *
 * ── Data Contract ────────────────────────────────────────────────────────
 * @typedef {Object} TerminalStatePayload
 * @property {number} final_mr           – Regenerative Multiple (e.g. 1.34)
 * @property {number} final_treasury     – Raw treasury balance in currency units
 * @property {number} total_ncd          – Accumulated Natural Capital Debt
 * @property {"REGENERATIVE_TITAN"|"SAFE_HAVEN"|"FRAGILE_GIANT"|"PRAGMATIC_OPERATOR"|"HOLLOW_IDEALIST"|"STRANDED_RELIC"|"TURNAROUND_MANAGER"} archetype
 * @property {string[]} triggered_black_swans – IDs/labels of black swan events
 *
 * ── Math Presented ───────────────────────────────────────────────────────
 * Adjusted Value = (final_treasury × final_mr) − total_ncd
 * The UI deliberately splits the "traditional balance sheet" row from
 * the "double materiality adjustment" rows so executives see exactly how
 * a healthy treasury is reshaped by ESG performance.
 */

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useMotionValue, useTransform } from 'framer-motion';
import { REVEAL_EASE } from '../styles/reveal';
import styles from './ArchetypeReveal.module.css';

// ── Archetype Configuration Matrix ──────────────────────────────────────────

/** @type {Record<string, ArchetypeTheme>} */
const ARCHETYPE_MATRIX = {
  REGENERATIVE_TITAN: {
    label:       'Regenerative Titan',
    tagline:     'You didn\'t just survive the transition — you led it.',
    descriptor:  'Your strategy generated more social and environmental value than it consumed. The board is no longer asking whether ESG pays. You proved it does.',
    icon:        '🌱',
    grade:       'A+',
    gradeLabel:  'Exemplary',
    // Primary colours
    accentPrimary:   '#10b981',   // emerald-500
    accentSecondary: '#d97706',   // amber-600 (gold)
    accentMuted:     '#065f46',   // emerald-900
    gradientStart:   '#022c22',   // deep forest
    gradientMid:     '#0a3320',
    gradientEnd:     '#0f172a',
    glowColor:       'rgba(16,185,129,0.35)',
    borderColor:     'rgba(16,185,129,0.5)',
    chipBg:          'rgba(16,185,129,0.12)',
    chipBorder:      'rgba(16,185,129,0.3)',
    scanlineColor:   'rgba(16,185,129,0.04)',
    particleColor:   '#10b981',
    heroGradient:    'radial-gradient(ellipse 70% 50% at 50% 30%, rgba(16,185,129,0.18) 0%, transparent 70%)',
  },
  SAFE_HAVEN: {
    label:       'De-risked Safe Haven',
    tagline:     'Cautious. Resilient. Structurally sound.',
    descriptor:  'You protected balance sheet integrity while managing ESG exposure. Activist pressure won\'t find leverage here. A defensive position executed with discipline.',
    icon:        '🛡️',
    grade:       'B+',
    gradeLabel:  'Resilient',
    accentPrimary:   '#3b82f6',   // blue-500
    accentSecondary: '#64748b',   // slate-500
    accentMuted:     '#1e3a5f',
    gradientStart:   '#0a1628',
    gradientMid:     '#0f2040',
    gradientEnd:     '#0f172a',
    glowColor:       'rgba(59,130,246,0.3)',
    borderColor:     'rgba(59,130,246,0.4)',
    chipBg:          'rgba(59,130,246,0.1)',
    chipBorder:      'rgba(59,130,246,0.25)',
    scanlineColor:   'rgba(59,130,246,0.04)',
    particleColor:   '#3b82f6',
    heroGradient:    'radial-gradient(ellipse 70% 50% at 50% 30%, rgba(59,130,246,0.15) 0%, transparent 70%)',
  },
  FRAGILE_GIANT: {
    label:       'Fragile Giant',
    tagline:     'You survived. But the cracks are showing.',
    descriptor:  'Treasury looks healthy on the surface — until you price in the Natural Capital Debt your balance sheet never carried. The next climate event won\'t be as forgiving.',
    icon:        '⚠️',
    grade:       'C',
    gradeLabel:  'At Risk',
    accentPrimary:   '#f59e0b',   // amber-400
    accentSecondary: '#ea580c',   // orange-600
    accentMuted:     '#78350f',
    gradientStart:   '#1c1003',
    gradientMid:     '#231608',
    gradientEnd:     '#0f172a',
    glowColor:       'rgba(245,158,11,0.3)',
    borderColor:     'rgba(245,158,11,0.45)',
    chipBg:          'rgba(245,158,11,0.1)',
    chipBorder:      'rgba(245,158,11,0.25)',
    scanlineColor:   'rgba(245,158,11,0.04)',
    particleColor:   '#f59e0b',
    heroGradient:    'radial-gradient(ellipse 70% 50% at 50% 30%, rgba(245,158,11,0.15) 0%, transparent 70%)',
  },
  HOLLOW_IDEALIST: {
    label:       'Hollow Idealist',
    tagline:     'A regenerative story the balance sheet couldn\'t fund.',
    descriptor:  'Your ESG credentials were real — the numbers underneath them weren\'t. Enterprise value turned negative. A compelling narrative doesn\'t refinance an insolvent balance sheet.',
    icon:        '🕯️',
    grade:       'D',
    gradeLabel:  'Insolvent',
    accentPrimary:   '#a855f7',   // purple-500
    accentSecondary: '#6b21a8',   // purple-800
    accentMuted:     '#3b0764',
    gradientStart:   '#160726',
    gradientMid:     '#1e0a33',
    gradientEnd:     '#0f0a1a',
    glowColor:       'rgba(168,85,247,0.32)',
    borderColor:     'rgba(168,85,247,0.5)',
    chipBg:          'rgba(168,85,247,0.12)',
    chipBorder:      'rgba(168,85,247,0.3)',
    scanlineColor:   'rgba(168,85,247,0.04)',
    particleColor:   '#a855f7',
    heroGradient:    'radial-gradient(ellipse 70% 50% at 50% 30%, rgba(168,85,247,0.16) 0%, transparent 70%)',
  },
  STRANDED_RELIC: {
    label:       'Stranded Relic',
    tagline:     'The market repriced you before you could react.',
    descriptor:  'Natural Capital Debt consumed your enterprise value. The board has voted to restructure. This is what stranded assets look like from the inside — not a slow decline, but a sudden reckoning.',
    icon:        '💀',
    grade:       'F',
    gradeLabel:  'Bankrupt',
    accentPrimary:   '#ef4444',   // red-500
    accentSecondary: '#1a1a1a',   // near-black
    accentMuted:     '#450a0a',
    gradientStart:   '#1a0000',
    gradientMid:     '#200505',
    gradientEnd:     '#0f0a0a',
    glowColor:       'rgba(239,68,68,0.35)',
    borderColor:     'rgba(239,68,68,0.5)',
    chipBg:          'rgba(239,68,68,0.1)',
    chipBorder:      'rgba(239,68,68,0.3)',
    scanlineColor:   'rgba(239,68,68,0.04)',
    particleColor:   '#ef4444',
    heroGradient:    'radial-gradient(ellipse 70% 50% at 50% 30%, rgba(239,68,68,0.18) 0%, transparent 70%)',
  },
  PRAGMATIC_OPERATOR: {
    label:       'Pragmatic Operator',
    tagline:     'You kept the lights on.',
    descriptor:  'Solvent and steady — you protected the balance sheet without over-reaching. The strategy was unremarkable and left regenerative value on the table, but you avoided the tail risks that sank bolder players.',
    icon:        '🧭',
    grade:       'B-',
    gradeLabel:  'Solvent',
    accentPrimary:   '#64748b',   // slate-500
    accentSecondary: '#334155',   // slate-700
    accentMuted:     '#1e293b',
    gradientStart:   '#0b1220',
    gradientMid:     '#131c2b',
    gradientEnd:     '#0f172a',
    glowColor:       'rgba(100,116,139,0.28)',
    borderColor:     'rgba(100,116,139,0.42)',
    chipBg:          'rgba(100,116,139,0.1)',
    chipBorder:      'rgba(100,116,139,0.25)',
    scanlineColor:   'rgba(100,116,139,0.04)',
    particleColor:   '#64748b',
    heroGradient:    'radial-gradient(ellipse 70% 50% at 50% 30%, rgba(100,116,139,0.14) 0%, transparent 70%)',
  },
  TURNAROUND_MANAGER: {
    label:       'Turnaround Manager',
    tagline:     'Rescued from the brink.',
    descriptor:  'You inherited a crisis and fought your way back. Through disciplined crisis management you steadied the balance sheet and re-earned the market\'s confidence — a comeback built the hard way.',
    icon:        '🔧',
    grade:       'C+',
    gradeLabel:  'Rescued',
    accentPrimary:   '#8b5cf6',   // violet-500
    accentSecondary: '#6d28d9',   // violet-700
    accentMuted:     '#4c1d95',
    gradientStart:   '#140a26',
    gradientMid:     '#1c1033',
    gradientEnd:     '#0f0a1a',
    glowColor:       'rgba(139,92,246,0.3)',
    borderColor:     'rgba(139,92,246,0.46)',
    chipBg:          'rgba(139,92,246,0.1)',
    chipBorder:      'rgba(139,92,246,0.25)',
    scanlineColor:   'rgba(139,92,246,0.04)',
    particleColor:   '#8b5cf6',
    heroGradient:    'radial-gradient(ellipse 70% 50% at 50% 30%, rgba(139,92,246,0.15) 0%, transparent 70%)',
  },
};

const FALLBACK_THEME = ARCHETYPE_MATRIX.SAFE_HAVEN;

// ── Utility ─────────────────────────────────────────────────────────────────

/**
 * Formats large currency values with M/B suffix.
 * @param {number} value
 * @returns {string}
 */
function fmtCurrency(value) {
  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';
  if (abs >= 1_000_000_000) return `${sign}$${(abs / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000)     return `${sign}$${(abs / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000)         return `${sign}$${(abs / 1_000).toFixed(1)}K`;
  return `${sign}$${abs.toFixed(0)}`;
}

/**
 * Formats a multiplier value to 4 decimal places.
 * @param {number} value
 * @returns {string}
 */
function fmtMultiplier(value) {
  return `${(value || 0).toFixed(4)}×`;
}

// ── Animated Counter ─────────────────────────────────────────────────────────

/**
 * Counts from 0 to `target` over `duration`ms, formatted by `formatter`.
 */
function AnimatedNumber({ target, duration = 1400, formatter = fmtCurrency, className }) {
  const [display, setDisplay] = useState(formatter(0));
  const startRef = useRef(null);
  const rafRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    const start = performance.now();
    startRef.current = start;

    const tick = (now) => {
      if (cancelled) return;
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = target * eased;
      setDisplay(formatter(current));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        setDisplay(formatter(target));
      }
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      cancelled = true;
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration, formatter]);

  return <span className={className}>{display}</span>;
}

// ── Particle Field ─────────────────────────────────────────────────────────

/** Renders ambient floating particles tuned to the archetype colour. */
function ParticleField({ color, count = 24 }) {
  const particles = useRef(
    Array.from({ length: count }, (_, i) => ({
      id: i,
      x:    Math.random() * 100,
      y:    Math.random() * 100,
      size: 1.5 + Math.random() * 2.5,
      dur:  6 + Math.random() * 10,
      del:  Math.random() * 5,
      dx:   (Math.random() - 0.5) * 40,
      dy:   -(20 + Math.random() * 50),
    }))
  ).current;

  return (
    <div className={styles.particleField} aria-hidden="true">
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className={styles.particle}
          style={{
            left:            `${p.x}%`,
            top:             `${p.y}%`,
            width:           p.size,
            height:          p.size,
            background:      color,
            boxShadow:       `0 0 ${p.size * 2}px ${color}`,
          }}
          animate={{
            x:       [0, p.dx, 0],
            y:       [0, p.dy, 0],
            opacity: [0, 0.7, 0],
          }}
          transition={{
            duration: p.dur,
            delay:    p.del,
            repeat:   Infinity,
            ease:     'easeInOut',
          }}
        />
      ))}
    </div>
  );
}

// ── Scanline Overlay ─────────────────────────────────────────────────────────

function ScanlineOverlay({ color }) {
  return (
    <div
      className={styles.scanlines}
      style={{ backgroundImage: `repeating-linear-gradient(0deg, ${color} 0px, ${color} 1px, transparent 1px, transparent 4px)` }}
      aria-hidden="true"
    />
  );
}

// ── Math Waterfall Row ────────────────────────────────────────────────────────

function WaterfallRow({ icon, label, sublabel, value, valueDisplay, color, op, isFinal, isDeduction, delay = 0 }) {
  return (
    <motion.div
      className={`${styles.waterfallRow} ${isFinal ? styles.waterfallRowFinal : ''} ${isDeduction ? styles.waterfallRowDeduction : ''}`}
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.45, delay, ease: REVEAL_EASE }}
      style={isFinal ? { borderColor: color, boxShadow: `inset 3px 0 0 ${color}` } : {}}
    >
      <div className={styles.waterfallOp}>
        {op && <span style={{ color, fontWeight: 900, fontSize: '1.1rem' }}>{op}</span>}
      </div>
      <div className={styles.waterfallLabel}>
        <span className={styles.waterfallIcon}>{icon}</span>
        <div>
          <div className={styles.waterfallLabelText}>{label}</div>
          {sublabel && <div className={styles.waterfallSublabel}>{sublabel}</div>}
        </div>
      </div>
      <div className={styles.waterfallValue} style={{ color }}>
        {valueDisplay ?? value}
      </div>
    </motion.div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

/**
 * ArchetypeReveal
 *
 * @param {{ payload: TerminalStatePayload, onContinue?: () => void }} props
 */
export default function ArchetypeReveal({ payload, onContinue, onLogout }) {
  const [phase, setPhase] = useState('intro');   // 'intro' | 'reveal' | 'math' | 'full'
  const [mathVisible, setMathVisible] = useState(false);
  const [confirmLogout, setConfirmLogout] = useState(false);

  const {
    final_mr            = 1.0,
    final_treasury      = 0,
    total_ncd           = 0,
    archetype           = 'SAFE_HAVEN',
    profile_title       = null,
    profile_description = null,
    triggered_black_swans = [],
  } = payload || {};

  const theme = ARCHETYPE_MATRIX[archetype] || FALLBACK_THEME;
  // AR-D: prefer the backend's real name/description (pathway-renamed or custom
  // archetypes) over the generic theme label; keep the theme for visuals.
  const displayLabel      = profile_title || theme.label;
  const displayDescriptor = profile_description || theme.descriptor;

  // ── Derived math ────────────────────────────────────────────────────────
  const traditionalValue   = final_treasury;                          // What the balance sheet shows
  const mrAdjustedValue    = final_treasury * final_mr;              // After Regenerative Multiple
  const adjustedFinalValue = mrAdjustedValue - total_ncd;            // After deducting NCD

  // Is the company destroyed, and by which side of the balance sheet?
  const isValueDestroyed  = adjustedFinalValue <= 0;
  // AR-D: negative M_R-adjusted treasury means losses/insolvency drove it — NCD
  // is not the story; only when treasury is still positive does NCD "strand" it.
  const insolventBeforeNcd = mrAdjustedValue <= 0;
  const finalValueColor   = isValueDestroyed
    ? '#ef4444'
    : adjustedFinalValue > traditionalValue
    ? theme.accentPrimary
    : theme.accentSecondary;

  // ── Reveal sequence ──────────────────────────────────────────────────────
  useEffect(() => {
    // Phase 1: intro logo lockup
    const t1 = setTimeout(() => setPhase('reveal'),  800);
    // Phase 2: archetype name animates in
    const t2 = setTimeout(() => setPhase('math'),    2200);
    // Phase 3: math waterfall appears
    const t3 = setTimeout(() => setMathVisible(true), 2800);
    // Phase 4: all content visible
    const t4 = setTimeout(() => setPhase('full'),    3600);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4); };
  }, []);

  // Prevent any scroll/interaction bleed-through on the body while mounted
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = prev; };
  }, []);

  return (
    <div
      className={styles.root}
      role="dialog"
      aria-modal="true"
      aria-label={`Simulation complete. Archetype: ${theme.label}`}
      style={{
        background: `linear-gradient(160deg, ${theme.gradientStart} 0%, ${theme.gradientMid} 50%, ${theme.gradientEnd} 100%)`,
      }}
    >
      {/* ── Logout button — top-right, always visible ────────────── */}
      {onLogout && (
        <button
          onClick={() => {
            if (confirmLogout) { onLogout(); setConfirmLogout(false); }
            else setConfirmLogout(true);
          }}
          onBlur={() => setConfirmLogout(false)}
          title={confirmLogout ? 'Click again to confirm logout' : 'Logout & Exit Simulation'}
          style={{
            position: 'fixed', top: 12, right: 16, zIndex: 10001,
            display: 'flex', alignItems: 'center', gap: 6, padding: '6px 14px',
            background: confirmLogout ? 'rgba(127,29,29,0.9)' : 'rgba(15,23,42,0.75)',
            backdropFilter: 'blur(8px)',
            border: confirmLogout ? '1px solid #f87171' : '1px solid rgba(248,113,113,0.25)',
            borderRadius: 8, color: confirmLogout ? '#fff' : '#fca5a5',
            fontSize: '0.72rem', fontWeight: 700, fontFamily: "'DM Sans', system-ui, sans-serif",
            cursor: 'pointer',
            transition: 'background 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease',
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          }}
        >
          {confirmLogout ? '⚠️ Confirm Logout?' : '🚪 Logout'}
        </button>
      )}

      {/* ── Ambient layers ─────────────────────────────────────────────── */}
      <div className={styles.heroGlow} style={{ background: theme.heroGradient }} aria-hidden="true" />
      <ScanlineOverlay color={theme.scanlineColor} />
      <ParticleField color={theme.particleColor} count={20} />

      {/* ── Corner grid marks ──────────────────────────────────────────── */}
      <div className={styles.cornerTL} style={{ borderColor: theme.borderColor }} aria-hidden="true" />
      <div className={styles.cornerBR} style={{ borderColor: theme.borderColor }} aria-hidden="true" />

      {/* ── Top status bar ─────────────────────────────────────────────── */}
      <motion.div
        className={styles.statusBar}
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2, ease: REVEAL_EASE }}
      >
        <div className={styles.statusDot} style={{ background: theme.accentPrimary, boxShadow: `0 0 8px ${theme.accentPrimary}` }} />
        <span className={styles.statusLabel}>SIMULATION TERMINAL — ROUND 10 COMPLETE</span>
        <div className={styles.statusRight}>
          <span className={styles.statusPill} style={{ background: theme.chipBg, border: `1px solid ${theme.chipBorder}`, color: theme.accentPrimary }}>
            {theme.gradeLabel} · Grade {theme.grade}
          </span>
        </div>
      </motion.div>

      {/* ── Scroll container ───────────────────────────────────────────── */}
      <div className={styles.scrollContainer}>

        {/* ── Hero Section ───────────────────────────────────────────── */}
        <div className={styles.heroSection}>

          {/* Glyph */}
          <AnimatePresence>
            {phase !== 'intro' && (
              <motion.div
                className={styles.archetypeGlyph}
                initial={{ scale: 0.3, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 18, delay: 0 }}
                style={{
                  background:  theme.chipBg,
                  border:      `2px solid ${theme.borderColor}`,
                  boxShadow:   `0 0 60px ${theme.glowColor}, inset 0 0 30px ${theme.chipBg}`,
                }}
              >
                <span className={styles.archetypeEmoji}>{theme.icon}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Label + Grade chip */}
          <AnimatePresence>
            {phase !== 'intro' && (
              <motion.div
                className={styles.heroIdentity}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.15, ease: REVEAL_EASE }}
              >
                <div className={styles.archetypeChip} style={{ background: theme.chipBg, border: `1px solid ${theme.chipBorder}`, color: theme.accentPrimary }}>
                  ⬡ ARCHETYPE CLASSIFICATION
                </div>
                <h1 className={styles.archetypeName} style={{ color: theme.accentPrimary, textShadow: `0 0 40px ${theme.glowColor}` }}>
                  {displayLabel.toUpperCase()}
                </h1>
                <p className={styles.archetypeTagline}>{theme.tagline}</p>
                <p className={styles.archetypeDescriptor}>{displayDescriptor}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* ── Double Materiality Math Waterfall ───────────────────────── */}
        <AnimatePresence>
          {mathVisible && (
            <motion.section
              className={styles.mathSection}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4, ease: REVEAL_EASE }}
              aria-label="Double materiality financial breakdown"
            >
              {/* Section header */}
              <motion.div
                className={styles.mathHeader}
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: REVEAL_EASE }}
              >
                <div className={styles.mathDividerLine} style={{ background: `linear-gradient(90deg, transparent, ${theme.borderColor}, transparent)` }} />
                <div className={styles.mathHeaderContent}>
                  <span className={styles.mathHeaderIcon}>⚖️</span>
                  <div>
                    <div className={styles.mathHeaderTitle}>DOUBLE MATERIALITY VALUATION</div>
                    <div className={styles.mathHeaderSub}>How your balance sheet looks after accounting for planetary boundaries</div>
                  </div>
                </div>
                <div className={styles.mathDividerLine} style={{ background: `linear-gradient(90deg, transparent, ${theme.borderColor}, transparent)` }} />
              </motion.div>

              {/* ── BLOCK 1: Traditional Balance Sheet ───────────────────── */}
              <div className={styles.mathBlock}>
                <div className={styles.mathBlockLabel}>
                  <span className={styles.mathBlockBadge} style={{ background: 'rgba(148,163,184,0.1)', border: '1px solid rgba(148,163,184,0.2)', color: '#94a3b8' }}>
                    📒 TRADITIONAL BALANCE SHEET
                  </span>
                  <span className={styles.mathBlockNote}>What your CFO reports to the board</span>
                </div>

                <WaterfallRow
                  icon="🏦"
                  label="Final Treasury Balance"
                  sublabel="Closing corporate cash position after Round 10"
                  value={traditionalValue}
                  valueDisplay={
                    <AnimatedNumber
                      target={traditionalValue}
                      duration={1000}
                      formatter={fmtCurrency}
                    />
                  }
                  color="#94a3b8"
                  op={null}
                  delay={0.1}
                />
              </div>

              {/* Divider: "But wait..." */}
              <motion.div
                className={styles.butWait}
                initial={{ opacity: 0, scaleX: 0 }}
                animate={{ opacity: 1, scaleX: 1 }}
                transition={{ duration: 0.5, delay: 0.6, ease: REVEAL_EASE }}
                style={{ borderColor: theme.borderColor }}
              >
                <span style={{ color: theme.accentPrimary }}>
                  ╌╌╌  Now apply your ESG Performance Score  ╌╌╌
                </span>
              </motion.div>

              {/* ── BLOCK 2: Double Materiality Adjustments ──────────────── */}
              <div className={styles.mathBlock}>
                <div className={styles.mathBlockLabel}>
                  <span className={styles.mathBlockBadge} style={{ background: theme.chipBg, border: `1px solid ${theme.chipBorder}`, color: theme.accentPrimary }}>
                    🌍 DOUBLE MATERIALITY LAYER
                  </span>
                  <span className={styles.mathBlockNote}>What the market will eventually price in</span>
                </div>

                <WaterfallRow
                  icon="⚡"
                  label="Regenerative Multiple (M_R)"
                  sublabel={`ESG performance × capital efficiency × leverage quality`}
                  value={mrAdjustedValue}
                  valueDisplay={
                    <span>
                      <AnimatedNumber
                        target={final_mr}
                        duration={900}
                        formatter={fmtMultiplier}
                        className={styles.multiplierDisplay}
                      />
                      <span style={{ color: '#64748b', fontWeight: 400, fontSize: '0.7em', marginLeft: 4 }}>
                        → {fmtCurrency(mrAdjustedValue)}
                      </span>
                    </span>
                  }
                  color={final_mr >= 1.2 ? theme.accentPrimary : final_mr >= 1.0 ? '#f59e0b' : '#ef4444'}
                  op="×"
                  delay={0.5}
                />

                <WaterfallRow
                  icon="🌿"
                  label="Natural Capital Debt (NCD)"
                  sublabel="Accumulated ecological liability never on your balance sheet"
                  value={-total_ncd}
                  valueDisplay={
                    <span style={{ color: '#ef4444' }}>
                      −<AnimatedNumber
                        target={total_ncd}
                        duration={1100}
                        formatter={(v) => fmtCurrency(v).replace(/^-?\$/, '$')}
                      />
                    </span>
                  }
                  color="#ef4444"
                  op="−"
                  isDeduction
                  delay={0.85}
                />
              </div>

              {/* ── FINAL RESULT ──────────────────────────────────────────── */}
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 1.3, ease: REVEAL_EASE }}
              >
                <WaterfallRow
                  icon={isValueDestroyed ? '💥' : '✦'}
                  label="Double-Materiality Adjusted Value"
                  sublabel="(Final Treasury × M_R) − Natural Capital Debt"
                  value={adjustedFinalValue}
                  valueDisplay={
                    <AnimatedNumber
                      target={adjustedFinalValue}
                      duration={1200}
                      formatter={fmtCurrency}
                    />
                  }
                  color={finalValueColor}
                  op="="
                  isFinal
                  delay={0}
                />

                {/* Destruction callout */}
                {isValueDestroyed && (
                  <motion.div
                    className={styles.destructionCallout}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.4, delay: 0.2, ease: REVEAL_EASE }}
                  >
                    <span className={styles.destructionIcon}>⚠</span>
                    {insolventBeforeNcd ? (
                      <span>Your balance sheet finished in the red — the M_R-adjusted treasury is <strong>negative</strong> before Natural Capital Debt is even counted. This is insolvency, not just a carbon liability.</span>
                    ) : (
                      <span>Your Natural Capital Debt exceeded the M_R-adjusted treasury. Enterprise value is <strong>negative</strong> — this is what asset stranding looks like from the inside.</span>
                    )}
                  </motion.div>
                )}
              </motion.div>
            </motion.section>
          )}
        </AnimatePresence>

        {/* ── Black Swan Log ───────────────────────────────────────────── */}
        <AnimatePresence>
          {phase === 'full' && triggered_black_swans.length > 0 && (
            <motion.section
              className={styles.swanSection}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2, ease: REVEAL_EASE }}
              aria-label="Black swan events log"
            >
              <div className={styles.swanHeader}>
                <span className={styles.swanHeaderIcon}>🦢</span>
                <span className={styles.swanHeaderTitle}>BLACK SWAN EVENTS TRIGGERED</span>
                <span className={styles.swanCount}>{triggered_black_swans.length}</span>
              </div>
              <div className={styles.swanList}>
                {triggered_black_swans.map((swan, i) => (
                  <motion.div
                    key={i}
                    className={styles.swanItem}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.08 }}
                  >
                    <span className={styles.swanItemBullet} style={{ background: theme.accentPrimary }} />
                    <span className={styles.swanItemLabel}>{swan}</span>
                  </motion.div>
                ))}
              </div>
            </motion.section>
          )}
        </AnimatePresence>

        {/* ── CTA ─────────────────────────────────────────────────────── */}
        <AnimatePresence>
          {phase === 'full' && (
            <motion.div
              className={styles.ctaSection}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.4, ease: REVEAL_EASE }}
            >
              {onContinue && (
                <button
                  id="archetype-reveal-continue-btn"
                  className={styles.ctaButton}
                  style={{
                    background:   theme.chipBg,
                    border:       `1px solid ${theme.borderColor}`,
                    color:        theme.accentPrimary,
                    boxShadow:    `0 0 24px ${theme.glowColor}`,
                  }}
                  onClick={onContinue}
                >
                  <span>Continue to Debrief</span>
                  <span className={styles.ctaArrow}>→</span>
                </button>
              )}
              <p className={styles.ctaNote}>
                This valuation is now locked. Simulation Round 10 of 10 complete.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Bottom spacer */}
        <div style={{ height: '3rem' }} />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//
// INTEGRATION SNIPPET — paste into frontend/app/page.js
//
// Add the import near the top of page.js:
//
//   import ArchetypeReveal from './components/ArchetypeReveal';
//
// Then, inside the `if (sim.gameOver)` block, BEFORE the existing scorecard
// phase check, add a 'archetype' phase that renders this component:
//
//   // In page.js, inside the `if (sim.gameOver) {` block:
//
//   if (gameOverPhase === 'archetype') {
//     const terminalData = {
//       final_mr:               sim.finalReport?.regenerative_multiple ?? sim.globalState?.regenerative_multiple ?? 1.0,
//       final_treasury:         sim.globalState?.corporate_treasury ?? 0,
//       total_ncd:              (sim.businessUnits ?? []).reduce((acc, bu) => acc + (bu.natural_capital_debt ?? 0), 0),
//       archetype:              sim.finalReport?.archetype ?? 'SAFE_HAVEN',
//       triggered_black_swans:  sim.globalState?.active_event_flags?.triggered_black_swans ?? [],
//     };
//     return (
//       <ArchetypeReveal
//         payload={terminalData}
//         onContinue={() => setGameOverPhase('scorecard')}
//       />
//     );
//   }
//
// Then change the initial state of gameOverPhase from 'scorecard' to 'archetype':
//
//   const [gameOverPhase, setGameOverPhase] = useState('archetype');
//
// The ArchetypeReveal renders as a fixed-position full-screen overlay at
// z-index 9999 and calls body { overflow: hidden } while mounted, so no
// interaction with the cockpit beneath is possible.
//
// ─────────────────────────────────────────────────────────────────────────────
