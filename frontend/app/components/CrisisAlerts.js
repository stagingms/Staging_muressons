'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { logoutAnchorStyle } from './logoutChrome';
import styles from './CrisisAlerts.module.css';

import { moneyM } from '../utils/format';

/* ═════════════════════════════════════════════════════════════════
 *  CRISIS TRIGGER CONFIG — defaults, localStorage key
 * ═════════════════════════════════════════════════════════════════ */

const STORAGE_KEY = 'muressons_crisis_triggers';

const INITIAL_TREASURY = 50_000_000;

const DEFAULT_CONFIG = {
  activist_threat: {
    enabled: true,
    metric: 'group_reputation',
    operator: '<',
    threshold: 40,
    delivery: 'both',          // 'text' | 'voice' | 'both'
    title: '🔴 ACTIVIST THREAT — Investor Revolt Imminent',
    body:
      'URGENT INTELLIGENCE BRIEFING\n\n' +
      'The FutureFirst Alliance activist consortium has issued a public letter demanding an emergency shareholder vote. ' +
      'Your group reputation has fallen to critically low levels, signalling to the market that Muressons Global lacks credible ESG governance.\n\n' +
      'Key concerns raised by the activists:\n' +
      '• Persistent reputational erosion across multiple business units\n' +
      '• Failure to demonstrate measurable sustainability progress\n' +
      '• Investor confidence index at historic lows\n\n' +
      'If reputation does not recover, the activist bloc will table a motion to dissolve the conglomerate structure at the next board meeting.\n\n' +
      'Immediate action is required to stabilise stakeholder confidence.',
  },
  ceo_liquidity_panic: {
    enabled: true,
    metric: 'corporate_treasury',
    operator: '<',
    threshold: INITIAL_TREASURY * 0.5,   // $25M
    delivery: 'both',
    title: '🟠 CEO LIQUIDITY PANIC — Treasury Critical',
    body:
      'CONFIDENTIAL — CEO DIRECT LINE\n\n' +
      'This is a direct communication from the CEO. Our corporate treasury has fallen below the critical liquidity threshold. ' +
      'At current burn rates, we risk being unable to fund essential operations within the next reporting period.\n\n' +
      'The CFO has flagged the following risks:\n' +
      '• Inability to service upcoming debt obligations\n' +
      '• Credit rating downgrade watch initiated by Moody\'s\n' +
      '• Supplier payment delays triggering force majeure clauses\n' +
      '• Board members questioning capital allocation competence\n\n' +
      'Every dollar spent from this point forward must demonstrate clear ROI. ' +
      'Non-essential sustainability investments should be reviewed for deferral.\n\n' +
      'The board expects a treasury recovery plan by end of period.',
  },
};

/** Read crisis trigger config from localStorage or return defaults. */
export function loadCrisisConfig() {
  if (typeof window === 'undefined') return DEFAULT_CONFIG;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      // Merge defaults for any missing fields
      return {
        activist_threat: { ...DEFAULT_CONFIG.activist_threat, ...parsed.activist_threat },
        ceo_liquidity_panic: { ...DEFAULT_CONFIG.ceo_liquidity_panic, ...parsed.ceo_liquidity_panic },
      };
    }
  } catch { /* ignore */ }
  return DEFAULT_CONFIG;
}

/** Save crisis trigger config to localStorage. */
export function saveCrisisConfig(config) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
}

/* ═════════════════════════════════════════════════════════════════
 *  EVALUATION — check if a trigger should fire
 * ═════════════════════════════════════════════════════════════════ */

function evaluate(value, operator, threshold) {
  switch (operator) {
    case '<':  return value < threshold;
    case '<=': return value <= threshold;
    case '>':  return value > threshold;
    case '>=': return value >= threshold;
    default:   return value < threshold;
  }
}

/* ═════════════════════════════════════════════════════════════════
 *  TTS — Web Speech API voice playback
 * ═════════════════════════════════════════════════════════════════ */

/* PHASE 8 — SPEECH IS OPT-OUTABLE, AND REMEMBERS.

   A crisis alert spoke aloud, at rate 0.92 and pitch 0.85, with no way to stop
   it short of dismissing the alert. In a room of five teams on one cohort that
   is five laptops talking over the facilitator; for a screen-reader user it is
   a second voice competing with their own; and for anyone using the product in
   a shared space it is simply not acceptable to be unable to turn it off.

   Two switches, cheapest first:
     - prefers-reduced-motion is NOT the right signal and is deliberately not
       used here: someone can want motion and not want sound.
     - a stored preference, keyed globally rather than per session, because
       "do not talk to me" is a property of the person and their room, not of
       one cohort.

   Default stays ON. The facilitator's `delivery` config still decides whether
   speech is offered at all; this only decides whether the player accepts it. */
const SPEECH_PREF_KEY = 'muressons_crisis_speech';

export function speechEnabled() {
  try { return localStorage.getItem(SPEECH_PREF_KEY) !== 'off'; } catch { return true; }
}

export function setSpeechEnabled(on) {
  try {
    if (on) localStorage.removeItem(SPEECH_PREF_KEY);
    else localStorage.setItem(SPEECH_PREF_KEY, 'off');
  } catch { /* storage disabled - the session default stands */ }
}

function speak(text) {
  if (typeof window === 'undefined' || !window.speechSynthesis) return;
  if (!speechEnabled()) return;
  window.speechSynthesis.cancel();
  // Strip emoji and formatting for cleaner speech
  const clean = text.replace(/[\u{1F000}-\u{1FFFF}]/gu, '').replace(/[•●▸]/g, '').trim();
  const utt = new SpeechSynthesisUtterance(clean);
  utt.rate = 0.92;
  utt.pitch = 0.85;
  utt.volume = 1;
  // Prefer a deep, authoritative voice
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => /google.*uk.*english|daniel|samantha/i.test(v.name))
    || voices.find(v => /en.*us|en.*gb/i.test(v.lang))
    || voices[0];
  if (preferred) utt.voice = preferred;
  window.speechSynthesis.speak(utt);
}

/* ══════════════════════════════════════════════════
 *  CrisisAlerts Component
 *
 *  ARCHITECTURE: This component is headless (renders null).
 *  It owns only the trigger logic: it evaluates globalState against
 *  thresholds and fires onActivate(crisisType, cfg) when a crisis hits.
 *
 *  The parent (page.js) receives that state and renders the crisis
 *  screen as an early return — exactly like RoundBriefing — so the
 *  cockpit tree never mounts while the crisis is active.
 *
 *  Props:
 *   - globalState:      { corporate_treasury, group_reputation, ... }
 *   - roundNumber:      current round (1–10)
 *   - onInjectMessage:  (msg) => void  — injects into ExecutiveMailbox
 *   - briefingActive:   boolean — defer triggers while round briefing shows
 *   - sessionId:        string
 *   - onActivate:       (crisisType: string, cfg: object) => void
 *   - onDismiss:        () => void
 * ══════════════════════════════════════════════════ */

export default function CrisisAlerts({
  globalState, roundNumber, onInjectMessage, briefingActive, sessionId,
  onActivate, firedRef,
}) {
  // firedRef is owned by page.js and passed in — it must NOT live here.
  // Reason: when CrisisScreen shows as an early return, this component
  // unmounts. On dismiss, it remounts with a fresh local ref (firedRef={{}}).
  // That means the just-dismissed crisis immediately re-fires because the
  // component no longer knows it already fired. Stable ref in page.js fixes this.

  // Re-read config each round
  const configRef = useRef(loadCrisisConfig());
  useEffect(() => {
    configRef.current = loadCrisisConfig();
  }, [roundNumber]);

  // Listen for manual injection from God Mode (BroadcastChannel)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const bc = new BroadcastChannel('muressons_crisis_inject');
    bc.onmessage = (e) => {
      const { crisisType } = e.data || {};
      if (crisisType && configRef.current[crisisType]) {
        fireAlert(crisisType, true);
      }
    };
    return () => bc.close();
  }, []);

  // Evaluate auto-triggers when globalState changes
  useEffect(() => {
    if (!globalState) return;
    if (briefingActive) return;
    if (roundNumber <= 1) return;
    const config = configRef.current;

    for (const key of ['activist_threat', 'ceo_liquidity_panic']) {
      const cfg = config[key];
      if (!cfg?.enabled) continue;

      const firedKey = `${key}_r${roundNumber}`;
      if (firedRef.current[firedKey]) continue;

      const value = globalState[cfg.metric];
      if (value == null) continue;

      if (evaluate(value, cfg.operator, cfg.threshold)) {
        firedRef.current[firedKey] = true;
        fireAlert(key, false);
        break;
      }
    }
  }, [globalState, roundNumber, briefingActive]);

  const fireAlert = useCallback((crisisType, isManual) => {
    const cfg = configRef.current[crisisType];
    if (!cfg) return;

    const delivery = cfg.delivery || 'both';

    onInjectMessage?.({
      id: `crisis-${crisisType}-r${roundNumber}-${Date.now()}`,
      round: roundNumber,
      type: 'warning',
      title: cfg.title,
      body: cfg.body,
      read: false,
    });

    onActivate?.(crisisType, cfg, delivery);
  }, [roundNumber, onInjectMessage, onActivate]);

  return null;
}

/* ══════════════════════════════════════════════════
 *  CrisisScreen Component
 *
 *  Stateless display component — rendered by page.js as an early
 *  return (same pattern as RoundBriefing). Receives the active crisis
 *  config and calls onDismiss() when the player clicks Acknowledge.
 * ══════════════════════════════════════════════════ */

export function CrisisScreen({ crisisType, cfg, globalState, onDismiss, onLogout }) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [confirmLogout, setConfirmLogout] = useState(false);
  const isActivist = crisisType === 'activist_threat';

  // Start voice playback when screen mounts
  useEffect(() => {
    const delivery = cfg?.delivery || 'both';
    /* speechEnabled() is checked HERE as well as inside speak(): without it the
       component would sit in isSpeaking=true forever, polling a synthesiser
       that was never given anything to say. */
    if ((delivery === 'voice' || delivery === 'both') && speechEnabled()) {
      setIsSpeaking(true);
      const t = setTimeout(() => {
        speak(cfg.body);
        const check = setInterval(() => {
          if (!window.speechSynthesis.speaking) {
            setIsSpeaking(false);
            clearInterval(check);
          }
        }, 500);
      }, 600);
      return () => {
        clearTimeout(t);
        window.speechSynthesis?.cancel();
      };
    }
  }, []);

  const handleDismiss = () => {
    if (typeof window !== 'undefined') window.speechSynthesis?.cancel();
    setIsSpeaking(false);
    onDismiss?.();
  };

  const metricLabel = isActivist ? 'Group Reputation' : 'Corporate Treasury';
  const metricValue = globalState?.[cfg?.metric];
  const formattedValue = isActivist
    ? `${metricValue?.toFixed?.(1) ?? '—'} / 100`
    : moneyM(metricValue);

  return (
    <div className={`${styles.overlay} ${isActivist ? styles.overlayActivist : styles.overlayLiquidity}`}>
      {/* Logout button — top-right, always visible */}
      {onLogout && (
        <button
          onClick={() => {
            if (confirmLogout) { if (typeof window !== 'undefined') window.speechSynthesis?.cancel(); onLogout(); setConfirmLogout(false); }
            else setConfirmLogout(true);
          }}
          onBlur={() => setConfirmLogout(false)}
          title={confirmLogout ? 'Click again to confirm logout' : 'Logout & Exit Simulation'}
          style={{
            ...logoutAnchorStyle(19100),
            display: 'flex', alignItems: 'center', gap: 6, padding: '6px 14px',
            background: confirmLogout ? 'rgba(127,29,29,0.9)' : 'rgba(15,23,42,0.75)',
            backdropFilter: 'blur(8px)',
            border: confirmLogout ? '1px solid var(--danger-text)' : '1px solid rgba(248,113,113,0.25)',
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
      <div className={styles.card}>
        <div className={styles.alertHeader}>
          <span className={styles.alertIcon}>{isActivist ? '🚨' : '💸'}</span>
          <div className={`${styles.alertBadge} ${isActivist ? styles.badgeActivist : styles.badgeLiquidity}`}>
            {isActivist ? 'ACTIVIST THREAT LEVEL: CRITICAL' : 'LIQUIDITY STATUS: EMERGENCY'}
          </div>
          <h1 className={`${styles.alertTitle} ${isActivist ? styles.titleActivist : styles.titleLiquidity}`}>
            {isActivist ? 'Activist Threat' : 'CEO Liquidity Panic'}
          </h1>
        </div>

        <div className={`${styles.alertBody} ${isActivist ? styles.bodyActivist : styles.bodyLiquidity}`}>
          <p className={styles.alertText}>{cfg?.body}</p>

          <div className={`${styles.metricRibbon} ${isActivist ? styles.ribbonActivist : styles.ribbonLiquidity}`}>
            <span>{metricLabel}:</span>
            <span className={styles.metricValue}>{formattedValue}</span>
            <span>• Threshold: {isActivist ? cfg?.threshold : moneyM(cfg?.threshold)}</span>
          </div>

          {/* Voice indicator — and the way out of it.
              PHASE 8: the indicator existed and the control did not, so the
              only way to stop a voice briefing was to dismiss the crisis.
              "Stop" silences this one; "and don't speak again" stores the
              preference, because the second time you reach for this control
              you are not asking about this alert. */}
          {isSpeaking && (
            <div className={styles.voiceIndicator}>
              <span className={styles.voiceDot} />
              VOICE BRIEFING IN PROGRESS…
              <button
                type="button"
                onClick={() => { window.speechSynthesis?.cancel(); setIsSpeaking(false); }}
                style={{ marginLeft: 10, minHeight: 44, minWidth: 44, padding: '0 12px', background: 'none', border: '1px solid currentColor', borderRadius: 6, color: 'inherit', font: 'inherit', cursor: 'pointer' }}
              >
                Stop
              </button>
              <button
                type="button"
                onClick={() => { setSpeechEnabled(false); window.speechSynthesis?.cancel(); setIsSpeaking(false); }}
                style={{ marginLeft: 6, minHeight: 44, minWidth: 44, padding: '0 12px', background: 'none', border: '1px solid currentColor', borderRadius: 6, color: 'inherit', font: 'inherit', cursor: 'pointer' }}
              >
                Stop, and don&rsquo;t speak again
              </button>
            </div>
          )}
        </div>

        {/* Dismiss */}
        <div className={styles.actions}>
          <button
            className={`${styles.dismissBtn} ${isActivist ? styles.dismissActivist : styles.dismissLiquidity}`}
            onClick={handleDismiss}
          >
            Acknowledged — Return to Cockpit →
          </button>
        </div>
      </div>
    </div>
  );
}
