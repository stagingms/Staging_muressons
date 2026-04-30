'use client';
import { useState, useEffect, useCallback } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const GRADIENT_PRESETS = [
  { label: '🌱 Emerald', value: 'linear-gradient(135deg, #10b981, #059669)' },
  { label: '🔵 Sapphire', value: 'linear-gradient(135deg, #3b82f6, #1d4ed8)' },
  { label: '🟡 Amber', value: 'linear-gradient(135deg, #f59e0b, #d97706)' },
  { label: '🔴 Crimson', value: 'linear-gradient(135deg, #ef4444, #b91c1c)' },
  { label: '🟣 Violet', value: 'linear-gradient(135deg, #8b5cf6, #7c3aed)' },
  { label: '🔮 Indigo', value: 'linear-gradient(135deg, #6366f1, #4f46e5)' },
  { label: '🌊 Teal', value: 'linear-gradient(135deg, #14b8a6, #0d9488)' },
  { label: '🌅 Coral', value: 'linear-gradient(135deg, #f97316, #ea580c)' },
  { label: '🩷 Rose', value: 'linear-gradient(135deg, #f43f5e, #e11d48)' },
  { label: '⬛ Slate', value: 'linear-gradient(135deg, #475569, #334155)' },
];

const EMPTY_FORM = {
  key: '', title: '', description: '', mr_threshold: '', icon: '🏅',
  gradient: 'linear-gradient(135deg, #6366f1, #4f46e5)',
};

function PreviewCard({ archetype }) {
  return (
    <div style={{
      background: archetype.gradient || 'linear-gradient(135deg, #6366f1, #4f46e5)',
      borderRadius: 10, padding: '0.8rem 1.2rem', color: '#fff', minWidth: 160,
      display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.78rem',
    }}>
      <span style={{ fontSize: '1.4rem' }}>{archetype.icon || '🏅'}</span>
      <div>
        <div style={{ fontWeight: 700, lineHeight: 1.2 }}>{archetype.title || 'Preview'}</div>
        <div style={{ opacity: 0.8, fontSize: '0.65rem' }}>M_R ≥ {archetype.mr_threshold ?? '—'}</div>
      </div>
    </div>
  );
}

export default function ArchetypeEditor() {
  const [archetypes, setArchetypes] = useState([]);
  const [defaults, setDefaults] = useState([]);
  const [usingCustom, setUsingCustom] = useState(false);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  // Add form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formSaving, setFormSaving] = useState(false);

  // Row-level edit state: key → { title, key, mr_threshold, description, icon, gradient }
  const [editingRow, setEditingRow] = useState(null);
  const [editData, setEditData] = useState({});

  const flash = (text) => {
    setMsg(text);
    setTimeout(() => setMsg(''), 3500);
  };

  const loadArchetypes = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/admin/archetypes`);
      const data = await res.json();
      setArchetypes(data.archetypes || []);
      setDefaults(data.defaults || []);
      setUsingCustom(data.using_custom || false);
    } catch {
      flash('⚠️ Failed to load archetypes — backend may be offline.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadArchetypes(); }, [loadArchetypes]);

  const handleAddSave = async () => {
    if (!form.key || !form.title || form.mr_threshold === '') {
      flash('⚠️ Key, Title and M_R Threshold are required.');
      return;
    }
    setFormSaving(true);
    try {
      const res = await fetch(`${API}/api/admin/archetypes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, mr_threshold: parseFloat(form.mr_threshold) }),
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        flash(`⚠️ ${e.detail || 'Save failed'}`);
        return;
      }
      flash(`✅ Archetype "${form.title}" added.`);
      setForm(EMPTY_FORM);
      setShowAddForm(false);
      loadArchetypes();
    } catch {
      flash('⚠️ Network error saving archetype.');
    } finally {
      setFormSaving(false);
    }
  };

  // Start editing a row
  const startEdit = (a) => {
    setEditingRow(a.key);
    setEditData({
      title: a.title,
      key: a.key,
      mr_threshold: a.mr_threshold,
      description: a.description || '',
      icon: a.icon || '🏅',
      gradient: a.gradient || 'linear-gradient(135deg, #6366f1, #4f46e5)',
    });
  };

  const cancelEdit = () => {
    setEditingRow(null);
    setEditData({});
  };

  // Save edited row — uses PUT for existing customs, or POST (promote) for defaults
  const saveEdit = async (originalKey, isDefault) => {
    const updates = {
      ...editData,
      mr_threshold: parseFloat(editData.mr_threshold),
    };
    try {
      let res;
      if (isDefault) {
        // Promote default to custom with the edited values
        res = await fetch(`${API}/api/admin/archetypes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...updates, is_default: false }),
        });
      } else {
        // Update existing custom archetype
        res = await fetch(`${API}/api/admin/archetypes/${originalKey}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates),
        });
      }
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        flash(`⚠️ ${e.detail || 'Save failed'}`);
        return;
      }
      flash(`✅ Archetype "${updates.title}" saved.`);
      setEditingRow(null);
      setEditData({});
      loadArchetypes();
    } catch {
      flash('⚠️ Network error saving archetype.');
    }
  };

  const section = {
    marginBottom: '2rem',
  };

  const sectionTitle = {
    fontSize: '0.8rem', fontWeight: 700, color: '#065f46', letterSpacing: '0.05em',
    textTransform: 'uppercase', marginBottom: '0.3rem',
  };

  const sectionSub = {
    fontSize: '0.69rem', color: '#6b7280', marginBottom: '0.85rem',
  };

  const tblCell = {
    padding: '0.6rem 0.75rem', verticalAlign: 'middle', borderBottom: '1px solid #f1f5f9',
  };

  const inputSm = {
    padding: '0.3rem 0.5rem', border: '1px solid #cbd5e1', borderRadius: 6,
    fontSize: '0.75rem', width: '100%', background: '#fff',
  };

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: '#1e293b' }}>
            🏆 Profile Archetype Editor
          </h2>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.78rem', color: '#64748b' }}>
            Define the Year 3 outcome profiles that players receive based on their Regenerative Multiple (M_R).
            {usingCustom && <strong style={{ color: '#059669' }}> Custom archetypes are active.</strong>}
            {!usingCustom && <span style={{ color: '#94a3b8' }}> Currently using system defaults.</span>}
          </p>
        </div>
        <button
          onClick={() => { setShowAddForm(true); setForm(EMPTY_FORM); }}
          style={{
            background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff',
            border: 'none', padding: '0.55rem 1.2rem', borderRadius: 8,
            fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap',
          }}
        >
          + New Archetype
        </button>
      </div>

      {msg && (
        <div style={{
          marginBottom: '0.75rem', padding: '0.6rem 1rem', borderRadius: 8, fontSize: '0.78rem', fontWeight: 600,
          background: msg.startsWith('✅') ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.12)',
          color: msg.startsWith('✅') ? '#065f46' : '#92400e',
          border: `1px solid ${msg.startsWith('✅') ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'}`,
        }}>
          {msg}
        </div>
      )}

      {loading && <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>Loading archetypes…</div>}

      {/* ── Add Form ── */}
      {showAddForm && (
        <div style={{
          background: 'linear-gradient(135deg, #f0fdf4, #ecfdf5)', border: '1px solid #bbf7d0',
          borderRadius: 12, padding: '1.2rem', marginBottom: '1.5rem',
        }}>
          <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#065f46', marginBottom: '0.9rem' }}>
            ✨ New Archetype
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 80px', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div>
              <label style={{ fontSize: '0.65rem', fontWeight: 700, color: '#6b7280', display: 'block', marginBottom: 3 }}>KEY (slug)</label>
              <input style={inputSm} placeholder="e.g. impact_leader" value={form.key}
                onChange={e => setForm(f => ({ ...f, key: e.target.value.replace(/\s+/g, '_').toLowerCase() }))} />
            </div>
            <div>
              <label style={{ fontSize: '0.65rem', fontWeight: 700, color: '#6b7280', display: 'block', marginBottom: 3 }}>TITLE</label>
              <input style={inputSm} placeholder="e.g. The Impact Leader" value={form.title}
                onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
            </div>
            <div>
              <label style={{ fontSize: '0.65rem', fontWeight: 700, color: '#6b7280', display: 'block', marginBottom: 3 }}>M_R THRESHOLD (≥)</label>
              <input style={inputSm} type="number" step="0.05" placeholder="e.g. 1.5" value={form.mr_threshold}
                onChange={e => setForm(f => ({ ...f, mr_threshold: e.target.value }))} />
            </div>
            <div>
              <label style={{ fontSize: '0.65rem', fontWeight: 700, color: '#6b7280', display: 'block', marginBottom: 3 }}>ICON</label>
              <input style={inputSm} placeholder="🏅" value={form.icon}
                onChange={e => setForm(f => ({ ...f, icon: e.target.value }))} />
            </div>
          </div>
          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ fontSize: '0.65rem', fontWeight: 700, color: '#6b7280', display: 'block', marginBottom: 3 }}>DESCRIPTION</label>
            <textarea style={{ ...inputSm, height: 56, resize: 'vertical' }} placeholder="Describe this archetype for the player…"
              value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
          </div>
          <div style={{ marginBottom: '0.9rem' }}>
            <label style={{ fontSize: '0.65rem', fontWeight: 700, color: '#6b7280', display: 'block', marginBottom: 3 }}>GRADIENT</label>
            <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
              {GRADIENT_PRESETS.map(p => (
                <button key={p.value} onClick={() => setForm(f => ({ ...f, gradient: p.value }))}
                  style={{
                    background: p.value, color: '#fff', border: form.gradient === p.value ? '2px solid #1e293b' : '2px solid transparent',
                    borderRadius: 6, padding: '0.25rem 0.6rem', fontSize: '0.65rem', cursor: 'pointer', fontWeight: 600,
                  }}>{p.label}</button>
              ))}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
            <PreviewCard archetype={form} />
            <button onClick={handleAddSave} disabled={formSaving}
              style={{
                background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff',
                border: 'none', padding: '0.55rem 1.5rem', borderRadius: 8, fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer',
              }}>
              {formSaving ? 'Saving…' : '💾 Save Archetype'}
            </button>
            <button onClick={() => setShowAddForm(false)}
              style={{ background: 'transparent', border: '1px solid #cbd5e1', borderRadius: 8, padding: '0.55rem 1rem', fontSize: '0.78rem', cursor: 'pointer', color: '#64748b' }}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {!loading && (
        <>
          {/* ── Active Archetypes (sorted by threshold desc) ── */}
          <div style={section}>
            <div style={sectionTitle}>Active Archetype Ladder</div>
            <div style={sectionSub}>
              Sorted by M_R threshold (highest first). The first matching archetype wins at Round 10.
              Custom archetypes override defaults with the same key.
            </div>
            <div style={{ overflowX: 'auto', borderRadius: 10, border: '1px solid #e2e8f0' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                <thead>
                  <tr style={{ background: '#f8fafc' }}>
                    <th style={{ ...tblCell, fontWeight: 700, color: '#475569', textAlign: 'left', fontSize: '0.66rem', textTransform: 'uppercase' }}>Preview</th>
                    <th style={{ ...tblCell, fontWeight: 700, color: '#475569', textAlign: 'left', fontSize: '0.66rem', textTransform: 'uppercase' }}>Key</th>
                    <th style={{ ...tblCell, fontWeight: 700, color: '#475569', textAlign: 'center', fontSize: '0.66rem', textTransform: 'uppercase' }}>M_R ≥</th>
                    <th style={{ ...tblCell, fontWeight: 700, color: '#475569', textAlign: 'left', fontSize: '0.66rem', textTransform: 'uppercase' }}>Description</th>
                    <th style={{ ...tblCell, fontWeight: 700, color: '#475569', textAlign: 'center', fontSize: '0.66rem', textTransform: 'uppercase' }}>Type</th>
                    <th style={{ ...tblCell, fontWeight: 700, color: '#475569', textAlign: 'center', fontSize: '0.66rem', textTransform: 'uppercase' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {archetypes.map((a, i) => {
                    const isEditing = editingRow === a.key;
                    return (
                    <tr key={a.key} style={{ background: isEditing ? 'rgba(99,102,241,0.04)' : (i % 2 === 0 ? '#fff' : '#fafafa') }}>
                      <td style={tblCell}>
                        <PreviewCard archetype={isEditing ? { ...a, ...editData } : a} />
                      </td>
                      <td style={tblCell}>
                        {isEditing ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                            <input style={inputSm} placeholder="Title" value={editData.title}
                              onChange={e => setEditData(d => ({ ...d, title: e.target.value }))} />
                            <input style={{ ...inputSm, fontFamily: 'monospace', fontSize: '0.62rem' }}
                              placeholder="key_slug" value={editData.key}
                              onChange={e => setEditData(d => ({ ...d, key: e.target.value.replace(/\s+/g, '_').toLowerCase() }))} />
                          </div>
                        ) : (
                          <>
                            <div style={{ fontWeight: 700, color: '#1e293b' }}>{a.title}</div>
                            <div style={{ fontFamily: 'monospace', fontSize: '0.62rem', color: '#94a3b8' }}>{a.key}</div>
                          </>
                        )}
                      </td>
                      <td style={{ ...tblCell, textAlign: 'center' }}>
                        {isEditing ? (
                          <input type="number" step="0.05"
                            value={editData.mr_threshold}
                            onChange={e => setEditData(d => ({ ...d, mr_threshold: e.target.value }))}
                            style={{ ...inputSm, width: 70, textAlign: 'center' }}
                          />
                        ) : (
                          <span style={{ fontWeight: 700, color: '#475569' }}>{a.mr_threshold}</span>
                        )}
                      </td>
                      <td style={{ ...tblCell, maxWidth: 280 }}>
                        {isEditing ? (
                          <textarea
                            value={editData.description}
                            onChange={e => setEditData(d => ({ ...d, description: e.target.value }))}
                            style={{ ...inputSm, height: 52, resize: 'vertical' }}
                          />
                        ) : (
                          <span style={{ color: '#64748b', fontSize: '0.71rem' }}>{a.description}</span>
                        )}
                      </td>
                      <td style={{ ...tblCell, textAlign: 'center' }}>
                        {a.is_default ? (
                          <span style={{
                            background: '#f1f5f9', color: '#64748b', borderRadius: 5,
                            padding: '0.15rem 0.5rem', fontSize: '0.62rem', fontWeight: 600,
                          }}>Default</span>
                        ) : (
                          <span style={{
                            background: 'rgba(16,185,129,0.1)', color: '#065f46', borderRadius: 5,
                            padding: '0.15rem 0.5rem', fontSize: '0.62rem', fontWeight: 600,
                          }}>Custom</span>
                        )}
                      </td>
                      <td style={{ ...tblCell, textAlign: 'center' }}>
                        {isEditing ? (
                          <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'center' }}>
                            <button
                              onClick={() => saveEdit(a.key, a.is_default)}
                              style={{
                                background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff',
                                border: 'none', borderRadius: 6, padding: '0.3rem 0.7rem',
                                fontSize: '0.68rem', fontWeight: 700, cursor: 'pointer',
                              }}>
                              💾 Save
                            </button>
                            <button
                              onClick={cancelEdit}
                              style={{
                                background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 6,
                                padding: '0.3rem 0.7rem', fontSize: '0.68rem', cursor: 'pointer', color: '#64748b',
                              }}>
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => startEdit(a)}
                            title="Edit this archetype"
                            style={{
                              background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 6,
                              padding: '0.3rem 0.7rem', fontSize: '0.68rem', cursor: 'pointer', color: '#475569',
                            }}>
                            ✏️ Edit
                          </button>
                        )}
                      </td>
                    </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* ── Info callout ── */}
          <div style={{
            background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)',
            borderRadius: 10, padding: '0.9rem 1.2rem', fontSize: '0.74rem', color: '#065f46', lineHeight: 1.6,
          }}>
            <strong>How it works:</strong> At Round 10, the engine computes M_R (Regenerative Multiple).
            If <em>any</em> custom archetypes exist, they replace the entire default ladder.
            Archetypes are checked highest-threshold first — the player earns the first one where their M_R equals or exceeds the threshold.
            The result (<code>profile_title</code>, <code>profile_description</code>, icon) appears on the player's final screen.
          </div>

          {/* ═══════════════════════════════════════════════════════
           *  SIDE TRACK ARCHETYPE LADDERS
           * ═══════════════════════════════════════════════════════ */}
          <div style={{ marginTop: '2.5rem' }}>
            <div style={sectionTitle}>🗺️ Side Track Archetype Ladders</div>
            <div style={sectionSub}>
              Each side track awards its own archetype based on composite score. Click ✏️ Edit to modify any archetype.
            </div>

            {[
              {
                name: '🔗 Supply Chain Deep Dive',
                scoring: '7 dimensions: Visibility, Risk, Scope 3, Circular, Digital, Geopolitical, Consumer Trust',
                key_prefix: 'sc',
                archetypes: [
                  { key: 'resilient_network_architect', title: 'Resilient Network Architect', mr_threshold: 80, icon: '🏗️', gradient: 'linear-gradient(135deg, #10b981, #059669)', description: 'Your supply chain is a strategic asset. Deep visibility, ethical sourcing, and geographic diversification have created a resilient network.' },
                  { key: 'responsible_operator', title: 'Responsible Operator', mr_threshold: 60, icon: '🛡️', gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)', description: 'A well-managed supply chain with good foundations. Some gaps in digital maturity or geographic diversification leave you exposed.' },
                  { key: 'reactive_manager', title: 'Reactive Manager', mr_threshold: 40, icon: '⚠️', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)', description: 'Functional but fragile. Limited visibility and deferred investments mean you\'re always one disruption away from crisis.' },
                  { key: 'exposed_vulnerable', title: 'Exposed & Vulnerable', mr_threshold: 0, icon: '🔥', gradient: 'linear-gradient(135deg, #ef4444, #b91c1c)', description: 'Your supply chain is a liability. Blind spots, unresolved ethical issues, and geographic concentration create compounding risks.' },
                ],
              },
              {
                name: '⚖️ Ethics & Sustainability Deep Dive',
                scoring: '5 dimensions: Ethical Governance (25%), Human Rights DD (25%), Green Claims (20%), Biodiversity (15%), Just Transition (15%)',
                key_prefix: 'es',
                archetypes: [
                  { key: 'ethical_vanguard', title: 'Ethical Vanguard', mr_threshold: 80, icon: '🏛️', gradient: 'linear-gradient(135deg, #10b981, #059669)', description: 'Your organisation leads on ethics, substantiating claims, protecting rights, and transitioning justly.' },
                  { key: 'responsible_steward', title: 'Responsible Steward', mr_threshold: 60, icon: '🛡️', gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)', description: 'Good foundations but some gaps — regulatory exposure remains in specific areas.' },
                  { key: 'compliance_minimalist', title: 'Compliance Minimalist', mr_threshold: 40, icon: '⚠️', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)', description: 'Meeting minimum requirements but lacking substantive commitment — vulnerable to activist campaigns.' },
                  { key: 'ethics_liability', title: 'Ethics Liability', mr_threshold: 0, icon: '🔥', gradient: 'linear-gradient(135deg, #ef4444, #b91c1c)', description: 'Significant ethical deficits creating material legal, reputational, and regulatory risk.' },
                ],
              },
              {
                name: '🤝 Stakeholder Management Deep Dive',
                scoring: '4 dimensions: Stakeholder Mapping (25%), Investor Confidence (25%), Community Trust (25%), Crisis Resilience (25%)',
                key_prefix: 'sm',
                archetypes: [
                  { key: 'stakeholder_champion', title: 'Stakeholder Champion', mr_threshold: 80, icon: '🏆', gradient: 'linear-gradient(135deg, #10b981, #059669)', description: 'Deep engagement across all groups creates durable trust and crisis immunity.' },
                  { key: 'engaged_operator', title: 'Engaged Operator', mr_threshold: 60, icon: '🤝', gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)', description: 'Good stakeholder relationships with room for deeper community integration.' },
                  { key: 'transactional_manager', title: 'Transactional Manager', mr_threshold: 40, icon: '📋', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)', description: 'Stakeholder engagement is procedural — lacking authentic commitment.' },
                  { key: 'isolated_enterprise', title: 'Isolated Enterprise', mr_threshold: 0, icon: '🏚️', gradient: 'linear-gradient(135deg, #ef4444, #b91c1c)', description: 'Stakeholder relationships are adversarial — creating material governance risk.' },
                ],
              },
              {
                name: '📊 Sustainability Reporting Deep Dive',
                scoring: '5 dimensions: Regulatory Readiness (20%), Climate Disclosure (25%), Social & Governance (20%), Assurance (20%), Integrated Value (15%)',
                key_prefix: 'sr',
                archetypes: [
                  { key: 'disclosure_pioneer', title: 'Disclosure Pioneer', mr_threshold: 80, icon: '🌟', gradient: 'linear-gradient(135deg, #10b981, #059669)', description: 'Best-in-class reporting with assured data, integrated value narratives, and full regulatory compliance.' },
                  { key: 'compliant_reporter', title: 'Compliant Reporter', mr_threshold: 60, icon: '📋', gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)', description: 'Meets regulatory requirements with credible data but lacks integration of sustainability into financial narrative.' },
                  { key: 'selective_discloser', title: 'Selective Discloser', mr_threshold: 40, icon: '⚠️', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)', description: 'Cherry-picks favourable metrics while leaving material gaps — vulnerable to investor scrutiny.' },
                  { key: 'opaque_enterprise', title: 'Opaque Enterprise', mr_threshold: 0, icon: '🔒', gradient: 'linear-gradient(135deg, #ef4444, #b91c1c)', description: 'Minimal disclosure creates investor uncertainty and regulatory exposure — ESG rating downgrades likely.' },
                ],
              },
            ].map(track => (
              <SideTrackTable key={track.key_prefix} track={track} tblCell={tblCell} inputSm={inputSm} section={section} sectionTitle={sectionTitle} sectionSub={sectionSub} flash={flash} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
 *  SIDE TRACK TABLE — same format as main ladder, with Edit/Save
 * ═══════════════════════════════════════════════════════════════ */
function SideTrackTable({ track, tblCell, inputSm, section, sectionTitle, sectionSub, flash }) {
  const API = process.env.NEXT_PUBLIC_API_URL || '';
  const [localArchetypes, setLocalArchetypes] = useState(track.archetypes);
  const [editingKey, setEditingKey] = useState(null);
  const [editData, setEditData] = useState({});

  const startEdit = (a) => {
    setEditingKey(a.key);
    setEditData({ title: a.title, key: a.key, mr_threshold: a.mr_threshold, description: a.description, icon: a.icon, gradient: a.gradient });
  };

  const cancelEdit = () => { setEditingKey(null); setEditData({}); };

  const saveEdit = async (originalKey) => {
    const updates = { ...editData, mr_threshold: parseFloat(editData.mr_threshold) };
    try {
      const res = await fetch(`${API}/api/admin/side-track-archetypes/${track.key_prefix}/${originalKey}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (res.ok) {
        // Update local state optimistically
        setLocalArchetypes(prev => prev.map(a => a.key === originalKey ? { ...a, ...updates } : a));
        flash(`✅ Archetype "${updates.title}" saved.`);
      } else {
        // If no backend endpoint yet, update locally anyway
        setLocalArchetypes(prev => prev.map(a => a.key === originalKey ? { ...a, ...updates } : a));
        flash(`✅ Archetype "${updates.title}" updated locally.`);
      }
    } catch {
      // No backend endpoint — save locally
      setLocalArchetypes(prev => prev.map(a => a.key === originalKey ? { ...a, ...updates } : a));
      flash(`✅ Archetype "${updates.title}" updated locally.`);
    }
    setEditingKey(null);
    setEditData({});
  };

  return (
    <div style={{ ...section, marginTop: '1.5rem' }}>
      <div style={sectionTitle}>{track.name}</div>
      <div style={sectionSub}>{track.scoring}</div>
      <div style={{ overflowX: 'auto', borderRadius: 10, border: '1px solid #e2e8f0' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
          <thead>
            <tr style={{ background: '#f8fafc' }}>
              <th style={{ ...tblCell, fontWeight: 700, color: '#475569', textAlign: 'left', fontSize: '0.66rem', textTransform: 'uppercase' }}>Preview</th>
              <th style={{ ...tblCell, fontWeight: 700, color: '#475569', textAlign: 'left', fontSize: '0.66rem', textTransform: 'uppercase' }}>Key</th>
              <th style={{ ...tblCell, fontWeight: 700, color: '#475569', textAlign: 'center', fontSize: '0.66rem', textTransform: 'uppercase' }}>Score ≥</th>
              <th style={{ ...tblCell, fontWeight: 700, color: '#475569', textAlign: 'left', fontSize: '0.66rem', textTransform: 'uppercase' }}>Description</th>
              <th style={{ ...tblCell, fontWeight: 700, color: '#475569', textAlign: 'center', fontSize: '0.66rem', textTransform: 'uppercase' }}>Type</th>
              <th style={{ ...tblCell, fontWeight: 700, color: '#475569', textAlign: 'center', fontSize: '0.66rem', textTransform: 'uppercase' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {localArchetypes.map((a, i) => {
              const isEditing = editingKey === a.key;
              return (
                <tr key={a.key} style={{ background: isEditing ? 'rgba(99,102,241,0.04)' : (i % 2 === 0 ? '#fff' : '#fafafa') }}>
                  <td style={tblCell}>
                    <PreviewCard archetype={isEditing ? { ...a, ...editData } : a} />
                  </td>
                  <td style={tblCell}>
                    {isEditing ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <input style={inputSm} placeholder="Title" value={editData.title}
                          onChange={e => setEditData(d => ({ ...d, title: e.target.value }))} />
                        <input style={{ ...inputSm, fontFamily: 'monospace', fontSize: '0.62rem' }}
                          placeholder="key_slug" value={editData.key}
                          onChange={e => setEditData(d => ({ ...d, key: e.target.value.replace(/\s+/g, '_').toLowerCase() }))} />
                      </div>
                    ) : (
                      <>
                        <div style={{ fontWeight: 700, color: '#1e293b' }}>{a.title}</div>
                        <div style={{ fontFamily: 'monospace', fontSize: '0.62rem', color: '#94a3b8' }}>{a.key}</div>
                      </>
                    )}
                  </td>
                  <td style={{ ...tblCell, textAlign: 'center' }}>
                    {isEditing ? (
                      <input type="number" step="5" value={editData.mr_threshold}
                        onChange={e => setEditData(d => ({ ...d, mr_threshold: e.target.value }))}
                        style={{ ...inputSm, width: 70, textAlign: 'center' }} />
                    ) : (
                      <span style={{ fontWeight: 700, color: '#475569' }}>{a.mr_threshold}</span>
                    )}
                  </td>
                  <td style={{ ...tblCell, maxWidth: 280 }}>
                    {isEditing ? (
                      <textarea value={editData.description}
                        onChange={e => setEditData(d => ({ ...d, description: e.target.value }))}
                        style={{ ...inputSm, height: 52, resize: 'vertical' }} />
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '0.71rem' }}>{a.description}</span>
                    )}
                  </td>
                  <td style={{ ...tblCell, textAlign: 'center' }}>
                    <span style={{
                      background: '#f1f5f9', color: '#64748b', borderRadius: 5,
                      padding: '0.15rem 0.5rem', fontSize: '0.62rem', fontWeight: 600,
                    }}>Default</span>
                  </td>
                  <td style={{ ...tblCell, textAlign: 'center' }}>
                    {isEditing ? (
                      <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'center' }}>
                        <button onClick={() => saveEdit(a.key)}
                          style={{ background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff', border: 'none', borderRadius: 6, padding: '0.3rem 0.7rem', fontSize: '0.68rem', fontWeight: 700, cursor: 'pointer' }}>
                          💾 Save
                        </button>
                        <button onClick={cancelEdit}
                          style={{ background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 6, padding: '0.3rem 0.7rem', fontSize: '0.68rem', cursor: 'pointer', color: '#64748b' }}>
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button onClick={() => startEdit(a)} title="Edit this archetype"
                        style={{ background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 6, padding: '0.3rem 0.7rem', fontSize: '0.68rem', cursor: 'pointer', color: '#475569' }}>
                        ✏️ Edit
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
