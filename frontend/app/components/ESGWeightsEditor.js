'use client';

/**
 * ESGWeightsEditor — Analytics & Assessment sub-tab on the Facilitator
 * dashboard, open to ALL facilitators (project_admin excluded server-side via
 * require_sim_manager). Tunes the weight each performance signal carries in
 * the five ESG Leadership Profile dimensions. Reads/writes the global rubric
 * via /api/admin/esg-profile-weights; the end-of-game ESG radar applies it.
 */
import { useState, useEffect, useCallback } from 'react';
import { DEFAULT_ESG_WEIGHTS, mergeEsgWeights } from './ESGLeadershipProfile';

const DIMENSIONS = [
  { id: 'climate_resilience', label: 'Climate Resilience', icon: '🌡️' },
  { id: 'governance', label: 'Governance', icon: '⚖️' },
  { id: 'social_impact', label: 'Social Impact', icon: '👥' },
  { id: 'environmental', label: 'Environmental', icon: '🌍' },
  { id: 'innovation', label: 'Innovation', icon: '💡' },
];

/** Human-friendly labels for each signal weight. */
const SIGNAL_LABELS = {
  resilience_factor: 'Climate-resilience factor (×)',
  resilience_bonus: 'Resilience investment reward',
  climate_leader: 'Climate leadership reward',
  adaptation_premium: 'Adaptation premium',
  carbon_transition: 'Carbon-transition reward',
  base: 'Baseline',
  materiality_governance: 'Materiality-governance reward',
  truth_premium: 'Transparency (truth premium)',
  materiality_aligned: 'Materiality-aligned bonus',
  instability_penalty: 'Instability penalty',
  reputation_blend: 'Reputation blend (0–1)',
  social_license_blend: 'Social-licence blend (0–1)',
  community_champion: 'Community-champion reward',
  just_transition: 'Just-transition reward',
  workforce: 'Workforce reward',
  wellbeing: 'Wellbeing reward',
  social_regeneration: 'Social-regeneration reward',
  community_trust: 'Community-trust reward',
  employee_champion: 'Employee-champion reward',
  just_transition_passed: 'Just-transition-passed bonus',
  burnout_penalty: 'Burnout penalty (per pt > 40)',
  social_collapse_penalty: 'Social-collapse penalty',
  decarbonisation: 'Decarbonisation (× carbon score)',
  stranded_asset_penalty: 'Stranded-asset penalty',
  rd_multiplier: 'R&D-intensity multiplier',
  rd_cap: 'R&D contribution cap',
  synergy: 'Synergy reward',
  brsr_pioneer: 'BRSR-pioneer reward',
  brsr_steward: 'BRSR-steward reward',
  brsr_laggard: 'BRSR-laggard penalty',
};

export default function ESGWeightsEditor() {
  const API = process.env.NEXT_PUBLIC_API_URL || '';
  const [weights, setWeights] = useState(() => mergeEsgWeights(null));
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState(null);

  const flash = (msg, ok = true) => { setStatus({ msg, ok }); setTimeout(() => setStatus(null), 4000); };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/admin/esg-profile-weights`, { credentials: 'include' });
      if (r.ok) {
        const d = await r.json();
        setWeights(mergeEsgWeights(d.esg_profile_weights));
      }
    } catch { /* offline → keep defaults */ }
    setLoading(false);
  }, [API]);

  useEffect(() => { load(); }, [load]);

  const setVal = (dim, key, v) => {
    setWeights((prev) => ({ ...prev, [dim]: { ...prev[dim], [key]: v } }));
  };

  const save = async () => {
    setSaving(true);
    // Coerce inputs to numbers (blank → default) before sending.
    const clean = {};
    for (const dim of Object.keys(DEFAULT_ESG_WEIGHTS)) {
      clean[dim] = {};
      for (const k of Object.keys(DEFAULT_ESG_WEIGHTS[dim])) {
        const n = Number(weights?.[dim]?.[k]);
        clean[dim][k] = Number.isFinite(n) ? n : DEFAULT_ESG_WEIGHTS[dim][k];
      }
    }
    try {
      const r = await fetch(`${API}/api/admin/esg-profile-weights`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ weights: clean, reason: 'Facilitator rubric update' }),
      });
      if (r.ok) { const d = await r.json(); setWeights(mergeEsgWeights(d.esg_profile_weights)); flash('✅ Weights saved'); }
      else flash(r.status === 403 ? '❌ Facilitator authentication required' : '❌ Save failed', false);
    } catch { flash('❌ Connection error', false); }
    setSaving(false);
  };

  const resetDefaults = async () => {
    if (!window.confirm('Reset all ESG signal weights to their defaults?')) return;
    setSaving(true);
    try {
      const r = await fetch(`${API}/api/admin/esg-profile-weights/reset`, { method: 'POST', credentials: 'include' });
      if (r.ok) { setWeights(mergeEsgWeights(null)); flash('✅ Reset to defaults'); }
      else flash('❌ Reset failed', false);
    } catch { flash('❌ Connection error', false); }
    setSaving(false);
  };

  const revertLocal = () => setWeights((prev) => {
    const out = {};
    for (const dim of Object.keys(DEFAULT_ESG_WEIGHTS)) out[dim] = { ...DEFAULT_ESG_WEIGHTS[dim] };
    return out;
  });

  const inputStyle = {
    width: 84, padding: '4px 8px', borderRadius: 6, border: '1px solid rgba(148,163,184,0.3)',
    background: 'rgba(15,23,42,0.6)', color: '#e2e8f0', fontFamily: "'JetBrains Mono', monospace", fontSize: '0.78rem',
  };

  return (
    <div style={{ padding: '1.5rem', color: '#e2e8f0' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10, marginBottom: 6 }}>
        <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800 }}>🎚️ ESG Profile Weights</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={revertLocal} disabled={saving} style={{ padding: '7px 14px', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: '0.78rem', border: '1px solid rgba(148,163,184,0.3)', background: 'rgba(148,163,184,0.08)', color: '#cbd5e1' }}>↺ Restore defaults (unsaved)</button>
          <button onClick={resetDefaults} disabled={saving} style={{ padding: '7px 14px', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: '0.78rem', border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.12)', color: '#fca5a5' }}>Reset saved</button>
          <button onClick={save} disabled={saving || loading} style={{ padding: '7px 16px', borderRadius: 8, cursor: 'pointer', fontWeight: 800, fontSize: '0.78rem', border: '1px solid rgba(99,102,241,0.5)', background: 'rgba(99,102,241,0.18)', color: '#c7d2fe', opacity: (saving || loading) ? 0.6 : 1 }}>{saving ? '⏳ Saving…' : '💾 Save rubric'}</button>
        </div>
      </div>
      <p style={{ color: '#94a3b8', fontSize: '0.8rem', margin: '0 0 4px' }}>
        Tune how much each performance signal contributes to the five ESG Leadership Profile dimensions shown to players at game end.
        Rewards/penalties are the M_R breakdown drivers; blends (0–1) split a dimension between its baseline metrics. Applies globally to all cohorts.
      </p>
      {status && (
        <div style={{ margin: '8px 0', fontSize: '0.8rem', fontWeight: 700, color: status.ok ? '#4ade80' : '#f87171' }}>{status.msg}</div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 14, marginTop: 12 }}>
        {DIMENSIONS.map((dim) => (
          <div key={dim.id} style={{ padding: '14px 16px', borderRadius: 12, background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.18)' }}>
            <div style={{ fontSize: '0.9rem', fontWeight: 800, marginBottom: 10 }}>{dim.icon} {dim.label}</div>
            {Object.keys(DEFAULT_ESG_WEIGHTS[dim.id]).map((k) => (
              <div key={k} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 7 }}>
                <span style={{ fontSize: '0.74rem', color: '#cbd5e1' }}>
                  {SIGNAL_LABELS[k] || k}
                  {Number(weights?.[dim.id]?.[k]) !== DEFAULT_ESG_WEIGHTS[dim.id][k] && (
                    <span title={`Default: ${DEFAULT_ESG_WEIGHTS[dim.id][k]}`} style={{ marginLeft: 6, fontSize: '0.62rem', color: '#fbbf24' }}>• edited</span>
                  )}
                </span>
                <input
                  type="number" step="any" value={weights?.[dim.id]?.[k] ?? ''}
                  // Blends are 0–1 shares; the backend clamps too, this just
                  // keeps the UI honest.
                  min={k.endsWith('_blend') ? 0 : undefined}
                  max={k.endsWith('_blend') ? 1 : undefined}
                  onChange={(e) => setVal(dim.id, k, e.target.value)}
                  style={inputStyle}
                />
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
