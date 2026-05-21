'use client';
import { useState, useEffect } from 'react';
const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function ScenarioPresets() {
    const [presets, setPresets] = useState([]);
    const [current, setCurrent] = useState({});
    const [applying, setApplying] = useState(null);
    const [status, setStatus] = useState(null);
    const [showCreate, setShowCreate] = useState(false);
    const [newName, setNewName] = useState('');
    const [newDesc, setNewDesc] = useState('');
    const [newIcon, setNewIcon] = useState('⚙️');

    const refresh = () => {
        fetch(`${API}/api/admin/scenario-presets`)
            .then(r => r.json())
            .then(d => { setPresets(d.presets || []); setCurrent(d.current_tunables || {}); })
            .catch(() => {});
    };

    useEffect(refresh, []);

    const apply = async (id) => {
        setApplying(id);
        try {
            const res = await fetch(`${API}/api/admin/scenario-presets/apply/${id}`, { method: 'POST' });
            if (res.ok) {
                const d = await res.json();
                setCurrent(d.tunables);
                setStatus(`✅ Applied "${d.name}" — ${Object.keys(d.changed).length} parameters changed`);
                setTimeout(() => setStatus(null), 4000);
            }
        } catch { setStatus('❌ Apply failed'); }
        setApplying(null);
    };

    const saveCustom = async () => {
        if (!newName.trim()) return;
        try {
            const res = await fetch(`${API}/api/admin/scenario-presets`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName, description: newDesc, icon: newIcon, tunables: current }),
            });
            if (res.ok) { refresh(); setShowCreate(false); setNewName(''); setNewDesc(''); setStatus('✅ Custom preset saved'); setTimeout(() => setStatus(null), 3000); }
        } catch {}
    };

    const deletePreset = async (id) => {
        if (!confirm('Delete this custom preset?')) return;
        await fetch(`${API}/api/admin/scenario-presets/${id}`, { method: 'DELETE' });
        refresh();
    };

    return (
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>🎯 Scenario Presets</h2>
                    <p style={{ margin: '0.25rem 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>One-click difficulty templates for different workshop contexts</p>
                </div>
                <button onClick={() => setShowCreate(!showCreate)} style={{
                    padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-body)', color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.82rem', cursor: 'pointer',
                }}>{showCreate ? '✕ Cancel' : '+ Custom Preset'}</button>
            </div>

            {status && <div style={{ padding: '0.6rem 1rem', borderRadius: '8px', background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.3)', fontSize: '0.85rem', fontWeight: 600 }}>{status}</div>}

            {/* Preset Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
                {presets.map(p => (
                    <div key={p.id} style={{
                        padding: '1.25rem', borderRadius: '12px', background: 'var(--bg-card)',
                        border: '1px solid var(--border-subtle)', position: 'relative',
                        transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                    }}>
                        {p.is_custom && (
                            <button onClick={() => deletePreset(p.id)} style={{
                                position: 'absolute', top: '8px', right: '8px', background: 'none', border: 'none',
                                color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1rem',
                            }}>×</button>
                        )}
                        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{p.icon}</div>
                        <h3 style={{ margin: '0 0 0.25rem', fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{p.name}</h3>
                        <p style={{ margin: '0 0 0.75rem', fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>{p.description}</p>

                        {/* Preview of key params */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginBottom: '0.75rem' }}>
                            {Object.entries(p.tunables || {}).slice(0, 4).map(([k, v]) => (
                                <span key={k} style={{
                                    padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'var(--bg-body)',
                                    fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)',
                                }}>{k.split('_').pop()}: {typeof v === 'number' && v < 1 ? `${(v * 100).toFixed(0)}%` : v}</span>
                            ))}
                        </div>

                        <button onClick={() => apply(p.id)} disabled={applying === p.id} style={{
                            width: '100%', padding: '0.6rem', borderRadius: '8px', border: 'none',
                            background: applying === p.id ? 'var(--bg-body)' : 'linear-gradient(135deg, #3b82f6, #06b6d4)',
                            color: applying === p.id ? 'var(--text-muted)' : '#fff',
                            fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer',
                        }}>{applying === p.id ? '⏳ Applying...' : '⚡ Apply Preset'}</button>
                    </div>
                ))}
            </div>

            {/* Create Custom */}
            {showCreate && (
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Save Current Settings as Preset</h3>
                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                        <select value={newIcon} onChange={e => setNewIcon(e.target.value)} style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-subtle)', background: 'var(--bg-body)', fontSize: '1.2rem' }}>
                            {['⚙️', '🎯', '🏢', '🎓', '💼', '🔥', '🌍', '🧪'].map(i => <option key={i} value={i}>{i}</option>)}
                        </select>
                        <input type="text" value={newName} onChange={e => setNewName(e.target.value)} placeholder="Preset name..."
                            style={{ flex: 1, padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--border-subtle)', background: 'var(--bg-body)', color: 'var(--text-primary)', fontSize: '0.85rem' }} />
                    </div>
                    <input type="text" value={newDesc} onChange={e => setNewDesc(e.target.value)} placeholder="Description..."
                        style={{ padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--border-subtle)', background: 'var(--bg-body)', color: 'var(--text-primary)', fontSize: '0.85rem' }} />
                    <button onClick={saveCustom} style={{
                        padding: '0.6rem', borderRadius: '8px', border: 'none', background: '#22c55e', color: '#fff', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer',
                    }}>💾 Save as Custom Preset</button>
                </div>
            )}
        </div>
    );
}
