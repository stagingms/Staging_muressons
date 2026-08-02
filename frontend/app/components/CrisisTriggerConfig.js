'use client';

import { useState, useEffect } from 'react';
import { loadCrisisConfig, saveCrisisConfig } from './CrisisAlerts';
import styles from './CrisisTriggerConfig.module.css';

/* ═════════════════════════════════════════════════════════════════
 *  CrisisTriggerConfig — God Mode panel for editing crisis trigger
 *  conditions, message content, and delivery mode.
 * ═════════════════════════════════════════════════════════════════ */

const METRICS = [
  { value: 'group_reputation', label: 'Group Reputation' },
  { value: 'corporate_treasury', label: 'Corporate Treasury ($)' },
];

const OPERATORS = [
  { value: '<', label: '< (less than)' },
  { value: '<=', label: '≤ (less than or equal)' },
  { value: '>', label: '> (greater than)' },
  { value: '>=', label: '≥ (greater than or equal)' },
];

const DELIVERY_MODES = [
  { value: 'text', label: '📝 Text Only' },
  { value: 'voice', label: '🔊 Voice Only' },
  { value: 'both', label: '📝🔊 Both' },
];

const CRISIS_TYPES = [
  {
    key: 'activist_threat',
    icon: '🚨',
    label: 'Activist Threat',
    subtitle: 'Triggered when investor confidence collapses due to poor reputation',
    injectClass: 'injectActivist',
  },
  {
    key: 'ceo_liquidity_panic',
    icon: '💸',
    label: 'CEO Liquidity Panic',
    subtitle: 'Triggered when corporate treasury falls below critical levels',
    injectClass: 'injectLiquidity',
  },
];

export default function CrisisTriggerConfig() {
  const [config, setConfig] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setConfig(loadCrisisConfig());
  }, []);

  if (!config) return null;

  const update = (crisisKey, field, value) => {
    setConfig((prev) => ({
      ...prev,
      [crisisKey]: { ...prev[crisisKey], [field]: value },
    }));
    setSaved(false);
  };

  const handleSave = () => {
    saveCrisisConfig(config);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const handleManualInject = (crisisKey) => {
    if (typeof window === 'undefined') return;
    if (!confirm(`Fire "${crisisKey === 'activist_threat' ? 'Activist Threat' : 'CEO Liquidity Panic'}" to ALL active player sessions?`)) return;
    const bc = new BroadcastChannel('muressons_crisis_inject');
    bc.postMessage({ crisisType: crisisKey });
    bc.close();
    alert('✅ Crisis alert injected. Active sessions will display the alert.');
  };

  return (
    <div className={styles.container}>
      <div className={styles.topHeader}>
        <h2>🚨 Crisis Trigger Configuration</h2>
        <p>
          Define auto-trigger conditions for Activist Threat and CEO Liquidity Panic alerts.
          These fire as text messages, voice briefings, or both — delivered directly to the Executive Cockpit.
        </p>
      </div>

      {CRISIS_TYPES.map(({ key, icon, label, subtitle, injectClass }) => {
        const cfg = config[key];
        return (
          <div key={key} className={styles.triggerCard}>
            {/* Card Header */}
            <div className={styles.cardHeader}>
              <span className={styles.cardIcon}>{icon}</span>
              <div className={styles.cardTitleWrap}>
                <h3 className={styles.cardTitle}>{label}</h3>
                <p className={styles.cardSubtitle}>{subtitle}</p>
              </div>
              <div className={styles.toggleWrap}>
                <span className={`${styles.toggleLabel} ${cfg.enabled ? styles.toggleOn : styles.toggleOff}`}>
                  {cfg.enabled ? 'ON' : 'OFF'}
                </span>
                <button
                  className={`${styles.toggle} ${cfg.enabled ? styles.active : ''}`}
                  onClick={() => update(key, 'enabled', !cfg.enabled)}
                  type="button"
                >
                  <span className={styles.toggleDot} />
                </button>
              </div>
            </div>

            {/* Configuration Fields */}
            <div className={styles.formGrid}>
              {/* Metric */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Monitored Metric</label>
                <select
                  className={styles.formSelect}
                  value={cfg.metric}
                  onChange={(e) => update(key, 'metric', e.target.value)}
                >
                  {METRICS.map((m) => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </div>

              {/* Operator */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Comparison</label>
                <select
                  className={styles.formSelect}
                  value={cfg.operator}
                  onChange={(e) => update(key, 'operator', e.target.value)}
                >
                  {OPERATORS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>

              {/* Threshold */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>
                  Threshold {cfg.metric === 'corporate_treasury' ? '($)' : '(0–100)'}
                </label>
                <input
                  className={styles.formInput}
                  type="number"
                  value={cfg.threshold}
                  onChange={(e) => update(key, 'threshold', Number(e.target.value))}
                  min={0}
                  step={cfg.metric === 'corporate_treasury' ? 1000000 : 1}
                />
              </div>

              {/* Delivery Mode */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Delivery Mode</label>
                <div className={styles.deliveryRow}>
                  {DELIVERY_MODES.map((dm) => (
                    <button
                      key={dm.value}
                      type="button"
                      className={`${styles.deliveryBtn} ${cfg.delivery === dm.value ? styles.active : ''}`}
                      onClick={() => update(key, 'delivery', dm.value)}
                    >
                      {dm.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Title */}
              <div className={`${styles.formGroup} ${styles.formGroupFull}`}>
                <label className={styles.formLabel}>Alert Title</label>
                <input
                  className={styles.formInput}
                  type="text"
                  value={cfg.title}
                  onChange={(e) => update(key, 'title', e.target.value)}
                />
              </div>

              {/* Body */}
              <div className={`${styles.formGroup} ${styles.formGroupFull}`}>
                <label className={styles.formLabel}>Alert Message Body</label>
                <textarea
                  className={styles.formTextarea}
                  value={cfg.body}
                  onChange={(e) => update(key, 'body', e.target.value)}
                  rows={6}
                />
              </div>
            </div>

            {/* Manual Inject */}
            <div className={styles.injectRow}>
              <button
                className={`${styles.injectBtn} ${styles[injectClass]}`}
                onClick={() => handleManualInject(key)}
                type="button"
              >
                ⚡ Fire Now — Manual Inject
              </button>
            </div>
          </div>
        );
      })}

      {/* Save */}
      <div className={styles.saveBar}>
        {saved && <span className={styles.savedToast}>✅ Saved to local configuration</span>}
        <button className={styles.saveBtn} onClick={handleSave}>
          💾 Save Configuration
        </button>
      </div>
    </div>
  );
}
