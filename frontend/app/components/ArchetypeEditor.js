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

  // Inline-edit state: { key: string, field: string }
  const [inlineEdit, setInlineEdit] = useState({});

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

  const handleEdit = async (key, updates) => {
    try {
      const res = await fetch(`${API}/api/admin/archetypes/${key}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        flash(`⚠️ ${e.detail || 'Update failed'}`);
        return;
      }
      flash(`✅ Archetype "${key}" updated.`);
      loadArchetypes();
    } catch {
      flash('⚠️ Network error updating archetype.');
    }
  };

  const handleDelete = async (key, title) => {
    if (!confirm(`Delete custom archetype "${title}"? This cannot be undone.`)) return;
    try {
      const res = await fetch(`${API}/api/admin/archetypes/${key}`, { method: 'DELETE' });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        flash(`⚠️ ${e.detail || 'Delete failed'}`);
        return;
      }
      flash(`🗑️ Archetype "${title}" deleted.`);
      loadArchetypes();
    } catch {
      flash('⚠️ Network error deleting archetype.');
    }
  };

  const handlePromote = async (defaultArchetype) => {
    // Clone a default to customs so it's editable
    try {
      const res = await fetch(`${API}/api/admin/archetypes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...defaultArchetype, is_default: false }),
      });
      if (!res.ok) throw new Error('promote failed');
      flash(`✅ "${defaultArchetype.title}" is now editable as a custom archetype.`);
      loadArchetypes();
    } catch {
      flash('⚠️ Could not promote default archetype.');
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
                  {archetypes.map((a, i) => (
                    <tr key={a.key} style={{ background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                      <td style={tblCell}><PreviewCard archetype={a} /></td>
                      <td style={tblCell}>
                        <div style={{ fontWeight: 700, color: '#1e293b' }}>{a.title}</div>
                        <div style={{ fontFamily: 'monospace', fontSize: '0.62rem', color: '#94a3b8' }}>{a.key}</div>
                      </td>
                      <td style={{ ...tblCell, textAlign: 'center' }}>
                        {a.is_default ? (
                          <span style={{ fontWeight: 700, color: '#475569' }}>{a.mr_threshold}</span>
                        ) : (
                          <input type="number" step="0.05"
                            defaultValue={a.mr_threshold}
                            onBlur={e => handleEdit(a.key, { mr_threshold: parseFloat(e.target.value) })}
                            style={{ ...inputSm, width: 70, textAlign: 'center' }}
                          />
                        )}
                      </td>
                      <td style={{ ...tblCell, maxWidth: 280 }}>
                        {a.is_default ? (
                          <span style={{ color: '#64748b', fontSize: '0.71rem' }}>{a.description}</span>
                        ) : (
                          <textarea
                            defaultValue={a.description}
                            onBlur={e => handleEdit(a.key, { description: e.target.value })}
                            style={{ ...inputSm, height: 52, resize: 'vertical' }}
                          />
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
                        {a.is_default ? (
                          <button
                            onClick={() => handlePromote(a)}
                            title="Clone to custom so it can be edited"
                            style={{
                              background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 6,
                              padding: '0.3rem 0.7rem', fontSize: '0.68rem', cursor: 'pointer', color: '#475569',
                            }}>
                            ✏️ Override
                          </button>
                        ) : (
                          <button
                            onClick={() => handleDelete(a.key, a.title)}
                            title="Delete this custom archetype (reverts to default if same key exists)"
                            style={{
                              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
                              borderRadius: 6, padding: '0.3rem 0.7rem', fontSize: '0.68rem', cursor: 'pointer', color: '#dc2626',
                            }}>
                            🗑️ Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
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
        </>
      )}
    </div>
  );
}
