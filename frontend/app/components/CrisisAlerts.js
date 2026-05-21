'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import styles from './CrisisAlerts.module.css';

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

function speak(text) {
  if (typeof window === 'undefined' || !window.speechSynthesis) return;
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

/* ═════════════════════════════════════════════════════════════════
 *  CrisisAlerts Component
 *
 *  Props:
 *   - globalState:  { corporate_treasury, group_reputation, ... }
 *   - roundNumber:  current round (1–10)
 *   - onInjectMessage: (msg: {id, round, type, title, body}) => void
 *      callback to inject a message into the ExecutiveMailbox
 *   - briefingActive: boolean — when true, delay auto-triggers until
 *      the round briefing overlay is dismissed so the crisis overlay
 *      appears on top of the cockpit / Shadow Board Audit screen.
 * ═════════════════════════════════════════════════════════════════ */

export default function CrisisAlerts({ globalState, roundNumber, onInjectMessage, briefingActive }) {
  const [activeAlert, setActiveAlert] = useState(null);   // 'activist_threat' | 'ceo_liquidity_panic' | null
  const [isSpeaking, setIsSpeaking] = useState(false);
  const firedRef = useRef({});  // track which alerts already fired per round

  // Re-read config each round change
  const configRef = useRef(loadCrisisConfig());
  useEffect(() => {
    configRef.current = loadCrisisConfig();
  }, [roundNumber]);

  // Listen for manual injection events from God Mode (via BroadcastChannel)
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

  // Evaluate auto-triggers whenever globalState changes.
  // If the round briefing overlay is still showing (briefingActive), defer
  // evaluation so the crisis overlay fires AFTER the briefing is dismissed —
  // this ensures the Activist Threat / CEO Liquidity Panic full-screen
  // overlay is visible on top of the cockpit or Shadow Board Audit.
  useEffect(() => {
    if (!globalState) return;
    if (briefingActive) return;  // wait until briefing is dismissed
    const config = configRef.current;

    for (const key of ['activist_threat', 'ceo_liquidity_panic']) {
      const cfg = config[key];
      if (!cfg?.enabled) continue;

      const firedKey = `${key}_r${roundNumber}`;
      if (firedRef.current[firedKey]) continue;  // already fired this round

      const value = globalState[cfg.metric];
      if (value == null) continue;

      if (evaluate(value, cfg.operator, cfg.threshold)) {
        firedRef.current[firedKey] = true;
        fireAlert(key, false);
        break;  // one alert at a time
      }
    }
  }, [globalState, roundNumber, briefingActive]);

  const fireAlert = useCallback((crisisType, isManual) => {
    const config = configRef.current;
    const cfg = config[crisisType];
    if (!cfg) return;

    const delivery = cfg.delivery || 'both';

    // Inject message into mailbox
    if (delivery === 'text' || delivery === 'both') {
      onInjectMessage?.({
        id: `crisis-${crisisType}-r${roundNumber}-${Date.now()}`,
        round: roundNumber,
        type: 'warning',
        title: cfg.title,
        body: cfg.body,
        read: false,
      });
    }

    // Show full-screen overlay
    setActiveAlert(crisisType);

    // Voice playback
    if (delivery === 'voice' || delivery === 'both') {
      setIsSpeaking(true);
      // Small delay so the overlay is visible first
      setTimeout(() => {
        speak(cfg.body);
        // Track speaking status
        const checkSpeaking = setInterval(() => {
          if (!window.speechSynthesis.speaking) {
            setIsSpeaking(false);
            clearInterval(checkSpeaking);
          }
        }, 500);
      }, 600);
    }
  }, [roundNumber, onInjectMessage]);

  const handleDismiss = () => {
    if (typeof window !== 'undefined') window.speechSynthesis?.cancel();
    setIsSpeaking(false);
    setActiveAlert(null);
  };

  if (!activeAlert) return null;

  const config = configRef.current;
  const cfg = config[activeAlert];
  const isActivist = activeAlert === 'activist_threat';

  const metricLabel = isActivist ? 'Group Reputation' : 'Corporate Treasury';
  const metricValue = globalState?.[cfg?.metric];
  const formattedValue = isActivist
    ? `${metricValue?.toFixed?.(1) ?? '—'} / 100`
    : `$${(metricValue / 1_000_000)?.toFixed?.(1) ?? '—'}M`;

  return (
    <div className={`${styles.overlay} ${isActivist ? styles.overlayActivist : styles.overlayLiquidity}`}>
      <div className={styles.card}>
        {/* Header */}
        <div className={styles.alertHeader}>
          <span className={styles.alertIcon}>{isActivist ? '🚨' : '💸'}</span>
          <div className={`${styles.alertBadge} ${isActivist ? styles.badgeActivist : styles.badgeLiquidity}`}>
            {isActivist ? 'ACTIVIST THREAT LEVEL: CRITICAL' : 'LIQUIDITY STATUS: EMERGENCY'}
          </div>
          <h1 className={`${styles.alertTitle} ${isActivist ? styles.titleActivist : styles.titleLiquidity}`}>
            {isActivist ? 'Activist Threat' : 'CEO Liquidity Panic'}
          </h1>
        </div>

        {/* Body */}
        <div className={`${styles.alertBody} ${isActivist ? styles.bodyActivist : styles.bodyLiquidity}`}>
          <p className={styles.alertText}>{cfg?.body}</p>

          {/* Metric ribbon */}
          <div className={`${styles.metricRibbon} ${isActivist ? styles.ribbonActivist : styles.ribbonLiquidity}`}>
            <span>{metricLabel}:</span>
            <span className={styles.metricValue}>{formattedValue}</span>
            <span>• Threshold: {isActivist ? cfg?.threshold : `$${(cfg?.threshold / 1_000_000)?.toFixed?.(1)}M`}</span>
          </div>

          {/* Voice indicator */}
          {isSpeaking && (
            <div className={styles.voiceIndicator}>
              <span className={styles.voiceDot} />
              VOICE BRIEFING IN PROGRESS…
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
