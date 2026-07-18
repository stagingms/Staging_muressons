'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './CustomBlackSwanBuilder.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const SCOPE_OPTIONS = [
  { value: 'Global', label: '🌍 Global (All BUs)' },
  { value: 'pharma', label: '💊 Muressons Pharma' },
  { value: 'electronics', label: '🔌 Muressons Electronics' },
  { value: 'consumer_goods', label: '🛍️ Muressons Consumer Goods' },
  { value: 'software', label: '💻 Muressons Software' },
  { value: 'hospitals', label: '🏥 Muressons Hospitals' },
  { value: 'clinics', label: '🩺 Primary Care Clinics' },
  { value: 'specialised_care', label: '🔬 Specialised Care' },
  { value: 'telehealth', label: '📱 Digital Health' },
];

/**
 * Facilitator-dashboard tool (tab: custom_black_swan, lead facilitator+).
 * Per-cohort unlock: a super admin enables `custom_black_swan_enabled` for a
 * cohort (cohort-settings override); only enabled cohorts appear in the
 * dropdown for non-admin facilitators, and the inject endpoint enforces the
 * same flag plus session ownership server-side. Admin roles see all cohorts.
 *
 * Props: facilitatorId (scopes the cohort list), isAdmin (bypasses the
 * per-cohort unlock filter).
 */
export default function CustomBlackSwanBuilder({ facilitatorId = null, isAdmin = false }) {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState('');
  const [title, setTitle] = useState('');
  const [narrative, setNarrative] = useState('');
  const [targetScope, setTargetScope] = useState('Global');
  const [financialImpact, setFinancialImpact] = useState(0);
  const [reputationImpact, setReputationImpact] = useState(0);
  const [socialLicenseImpact, setSocialLicenseImpact] = useState(0);
  const [naturalDebtImpact, setNaturalDebtImpact] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [showConfirm, setShowConfirm] = useState(false);

  // Load sessions — non-admins get only their own cohorts, and only the ones
  // a super admin unlocked for the injector (custom_black_swan_enabled is
  // enriched onto each session by /api/admin/sessions).
  useEffect(() => {
    (async () => {
      try {
        const qs = !isAdmin && facilitatorId ? `?facilitator_id=${encodeURIComponent(facilitatorId)}` : '';
        const res = await fetch(`${API}/api/admin/sessions${qs}`, { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          const sessionList = (data.sessions || [])
            .filter(s => !s.player_id) // Only cohort sessions
            .filter(s => isAdmin || s.custom_black_swan_enabled === true);
          setSessions(sessionList);
          if (sessionList.length > 0 && !selectedSession) {
            setSelectedSession(sessionList[0].session_id);
          }
        }
      } catch { /* ignore */ }
    })();
  }, [facilitatorId, isAdmin]);

  // Load history
  const loadHistory = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/admin/custom-black-swan-log`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setHistory(data.events || []);
      }
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const handleInject = async () => {
    if (!selectedSession || !title.trim() || !narrative.trim()) {
      setError('Session, title, and narrative are required.');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    setShowConfirm(false);

    try {
      const res = await fetch(`${API}/api/admin/${selectedSession}/inject-custom-event`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          narrative: narrative.trim(),
          target_scope: targetScope,
          financial_impact: parseFloat(financialImpact) || 0,
          reputation_impact: parseFloat(reputationImpact) || 0,
          social_license_impact: parseFloat(socialLicenseImpact) || 0,
          natural_debt_impact: parseFloat(naturalDebtImpact) || 0,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Injection failed (${res.status})`);
      }

      const data = await res.json();
      setResult(data);
      // reset form
      setTitle('');
      setNarrative('');
      setFinancialImpact(0);
      setReputationImpact(0);
      setSocialLicenseImpact(0);
      setNaturalDebtImpact(0);
      setTargetScope('Global');
      loadHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const impactPreview = [
    financialImpact !== 0 && `Treasury ${financialImpact > 0 ? '+' : ''}$${(financialImpact / 1_000_000).toFixed(1)}M`,
    reputationImpact !== 0 && `Reputation ${reputationImpact > 0 ? '+' : ''}${reputationImpact}`,
    socialLicenseImpact !== 0 && `Social License ${socialLicenseImpact > 0 ? '+' : ''}${socialLicenseImpact}`,
    naturalDebtImpact !== 0 && `Natural Debt ${naturalDebtImpact > 0 ? '+' : ''}${naturalDebtImpact}`,
  ].filter(Boolean);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.icon}>🦢</span>
        <div>
          <h2>Custom Black Swan Injector</h2>
          <p className={styles.subtitle}>
            Create and inject custom crises that are not part of the standard 10-round narrative
          </p>
        </div>
      </div>

      {/* No unlocked cohorts: explain the gate instead of an empty dropdown */}
      {!isAdmin && sessions.length === 0 && (
        <div className={styles.errorBanner} style={{ marginBottom: 12 }}>
          🔒 No cohorts are enabled for the injector. A super admin can unlock it
          per cohort (Analytics &amp; Cohort Controls → Facilitator Tools).
        </div>
      )}

      {/* ── Form ── */}
      <div className={styles.formGrid}>
        {/* Session Selector */}
        <div className={styles.fieldFull}>
          <label className={styles.label}>Target Session / Cohort</label>
          <select
            className={styles.select}
            value={selectedSession}
            onChange={(e) => setSelectedSession(e.target.value)}
          >
            <option value="">— Select a session —</option>
            {sessions.map((s) => (
              <option key={s.session_id} value={s.session_id}>
                {s.cohort_name || s.session_id} (R{s.current_round || '?'})
              </option>
            ))}
          </select>
        </div>

        {/* Event Title */}
        <div className={styles.fieldFull}>
          <label className={styles.label}>Event Title</label>
          <input
            className={styles.input}
            type="text"
            placeholder="e.g. Global Shipping Canal Blocked"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        {/* Narrative */}
        <div className={styles.fieldFull}>
          <label className={styles.label}>Narrative Text</label>
          <textarea
            className={styles.textarea}
            rows={4}
            placeholder="The news story presented to the executives..."
            value={narrative}
            onChange={(e) => setNarrative(e.target.value)}
          />
        </div>

        {/* Target Scope */}
        <div className={styles.field}>
          <label className={styles.label}>Target Scope</label>
          <select
            className={styles.select}
            value={targetScope}
            onChange={(e) => setTargetScope(e.target.value)}
          >
            {SCOPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Financial Impact */}
        <div className={styles.field}>
          <label className={styles.label}>
            💰 Financial Impact ($)
            <span className={styles.hint}>Negative = deduction</span>
          </label>
          <input
            className={styles.input}
            type="number"
            step="100000"
            value={financialImpact}
            onChange={(e) => setFinancialImpact(parseFloat(e.target.value) || 0)}
          />
        </div>

        {/* Reputation Impact */}
        <div className={styles.field}>
          <label className={styles.label}>
            ⭐ Reputation Impact
            <span className={styles.hint}>Range: -100 to +100</span>
          </label>
          <input
            className={styles.input}
            type="number"
            step="1"
            min="-100"
            max="100"
            value={reputationImpact}
            onChange={(e) => setReputationImpact(parseFloat(e.target.value) || 0)}
          />
        </div>

        {/* Social License Impact */}
        <div className={styles.field}>
          <label className={styles.label}>
            🤝 Social License Impact
            <span className={styles.hint}>Per-BU or Global</span>
          </label>
          <input
            className={styles.input}
            type="number"
            step="1"
            min="-100"
            max="100"
            value={socialLicenseImpact}
            onChange={(e) => setSocialLicenseImpact(parseFloat(e.target.value) || 0)}
          />
        </div>

        {/* Natural Debt Impact */}
        <div className={styles.field}>
          <label className={styles.label}>
            🏭 Natural Capital Debt
            <span className={styles.hint}>Positive = increase debt</span>
          </label>
          <input
            className={styles.input}
            type="number"
            step="1"
            value={naturalDebtImpact}
            onChange={(e) => setNaturalDebtImpact(parseFloat(e.target.value) || 0)}
          />
        </div>
      </div>

      {/* Impact Preview */}
      {impactPreview.length > 0 && (
        <div className={styles.preview}>
          <div className={styles.previewTitle}>⚡ Impact Preview</div>
          <div className={styles.previewTags}>
            {impactPreview.map((tag, i) => (
              <span key={i} className={styles.previewTag}>{tag}</span>
            ))}
          </div>
        </div>
      )}

      {/* Error / Success */}
      {error && <div className={styles.errorBanner}>{error}</div>}
      {result && (
        <div className={styles.successBanner}>
          ✅ Black Swan &quot;{result.event?.title}&quot; injected successfully!
        </div>
      )}

      {/* Inject Button */}
      {!showConfirm ? (
        <button
          className={styles.injectBtn}
          disabled={loading || !selectedSession || !title.trim() || !narrative.trim()}
          onClick={() => setShowConfirm(true)}
        >
          🦢 Inject Custom Event Now
        </button>
      ) : (
        <div className={styles.confirmRow}>
          <span className={styles.confirmText}>⚠️ This will immediately mutate the player&apos;s game state. Proceed?</span>
          <button className={styles.confirmYes} onClick={handleInject} disabled={loading}>
            {loading ? '⏳ Injecting...' : '✅ Confirm Injection'}
          </button>
          <button className={styles.confirmNo} onClick={() => setShowConfirm(false)} disabled={loading}>
            Cancel
          </button>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className={styles.historySection}>
          <h3 className={styles.historyTitle}>📜 Injection History</h3>
          <div className={styles.historyList}>
            {history.slice().reverse().map((evt, i) => (
              <div key={i} className={styles.historyItem}>
                <div className={styles.historyHeader}>
                  <span className={styles.historyName}>🦢 {evt.title}</span>
                  <span className={styles.historyTime}>
                    {new Date(evt.injected_at).toLocaleString()}
                  </span>
                </div>
                <div className={styles.historyMeta}>
                  <span>Scope: {evt.target_scope}</span>
                  {evt.financial_impact !== 0 && <span>💰 ${(evt.financial_impact / 1_000_000).toFixed(1)}M</span>}
                  {evt.reputation_impact !== 0 && <span>⭐ {evt.reputation_impact > 0 ? '+' : ''}{evt.reputation_impact}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
