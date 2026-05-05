'use client';
import { useState, useEffect } from 'react';
const API = process.env.NEXT_PUBLIC_API_URL || '';

const TAG_COLORS = {
    general: { bg: 'rgba(100,116,139,0.1)', border: 'rgba(100,116,139,0.3)', color: '#64748b', icon: '📝' },
    teaching_moment: { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.3)', color: '#3b82f6', icon: '💡' },
    warning: { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)', color: '#ef4444', icon: '⚠️' },
    insight: { bg: 'rgba(34,197,94,0.1)', border: 'rgba(34,197,94,0.3)', color: '#22c55e', icon: '🔍' },
};

export default function FacilitatorAnnotations({ sessionId, leaderboard = [] }) {
    const [annotations, setAnnotations] = useState([]);
    const [sid, setSid] = useState(sessionId || '');
    const [newText, setNewText] = useState('');
    const [newTag, setNewTag] = useState('general');
    const [newRound, setNewRound] = useState(1);
    const [newVisibleToStudents, setNewVisibleToStudents] = useState(true);
    const [saving, setSaving] = useState(false);
    const [playerVisible, setPlayerVisible] = useState(false);

    const sessions = leaderboard.filter(s => !s.player_id);

    useEffect(() => {
        const target = sid || sessionId;
        if (!target) return;
        fetch(`${API}/api/admin/annotations/${target}`)
            .then(r => r.json())
            .then(d => setAnnotations(d.annotations || []))
            .catch(() => {});
    }, [sid, sessionId]);

    // Fetch visibility state
    useEffect(() => {
        const target = sid || sessionId;
        if (!target) return;
        // Check the session's annotations_player_visible flag
        fetch(`${API}/api/admin/sessions`)
            .then(r => r.json())
            .then(d => {
                const sess = (d.sessions || []).find(s => s.session_id === target);
                if (sess) setPlayerVisible(!!sess.annotations_player_visible);
            })
            .catch(() => {});
    }, [sid, sessionId]);

    const toggleVisibility = async () => {
        const target = sid || sessionId;
        if (!target) return;
        const newVal = !playerVisible;
        try {
            await fetch(`${API}/api/admin/annotations/${target}/visibility`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player_visible: newVal }),
            });
            setPlayerVisible(newVal);
        } catch {}
    };

    const addAnnotation = async () => {
        if (!newText.trim()) return;
        const target = sid || sessionId;
        if (!target) return;
        setSaving(true);
        try {
            const res = await fetch(`${API}/api/admin/annotations/${target}`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: newText, tag: newTag, round: newRound, visible_to_students: newVisibleToStudents }),
            });
            if (res.ok) {
                const ann = await res.json();
                setAnnotations(prev => [...prev, ann]);
                setNewText('');
            }
        } catch {}
        setSaving(false);
    };

    const deleteAnnotation = async (annId) => {
        const target = sid || sessionId;
        await fetch(`${API}/api/admin/annotations/${target}/${annId}`, { method: 'DELETE' });
        setAnnotations(prev => prev.filter(a => a.id !== annId));
    };

    return (
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>📌 Session Annotations</h2>
                {/* Student Visibility Toggle */}
                <label style={{
                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                    cursor: 'pointer', userSelect: 'none',
                    fontSize: '0.78rem', fontWeight: 600,
                    color: playerVisible ? '#10b981' : 'var(--text-muted)',
                    padding: '4px 10px', borderRadius: '6px',
                    background: playerVisible ? 'rgba(16,185,129,0.08)' : 'transparent',
                    border: `1px solid ${playerVisible ? 'rgba(16,185,129,0.3)' : 'var(--border-subtle)'}`,
                    transition: 'all 0.2s',
                }}>
                    <input type="checkbox" checked={playerVisible} onChange={toggleVisibility}
                        style={{ accentColor: '#10b981', width: 16, height: 16, cursor: 'pointer' }} />
                    {playerVisible ? '👁️ Visible to Students' : '🔒 Hidden from Students'}
                </label>
            </div>

            {sessions.length > 0 && (
                <select value={sid} onChange={e => setSid(e.target.value)} style={{
                    padding: '0.5rem 1rem', borderRadius: '6px', border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-body)', color: 'var(--text-primary)', fontSize: '0.85rem', maxWidth: '400px',
                }}>
                    <option value="">Select a cohort...</option>
                    {sessions.map(s => <option key={s.session_id} value={s.session_id}>{s.cohort_name || s.session_id}</option>)}
                </select>
            )}

            {/* New Annotation Form */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '1rem' }}>
                <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                    <select value={newTag} onChange={e => setNewTag(e.target.value)} style={{
                        padding: '0.4rem 0.75rem', borderRadius: '6px', border: '1px solid var(--border-subtle)',
                        background: 'var(--bg-body)', color: 'var(--text-primary)', fontSize: '0.82rem',
                    }}>
                        {Object.keys(TAG_COLORS).map(t => <option key={t} value={t}>{TAG_COLORS[t].icon} {t.replace('_', ' ')}</option>)}
                    </select>
                    <select value={newRound} onChange={e => setNewRound(parseInt(e.target.value))} style={{
                        padding: '0.4rem 0.75rem', borderRadius: '6px', border: '1px solid var(--border-subtle)',
                        background: 'var(--bg-body)', color: 'var(--text-primary)', fontSize: '0.82rem',
                    }}>
                        {Array.from({ length: 10 }, (_, i) => i + 1).map(r => <option key={r} value={r}>Round {r}</option>)}
                    </select>
                    <label style={{
                        display: 'flex', alignItems: 'center', gap: '0.3rem',
                        fontSize: '0.75rem', color: 'var(--text-muted)', cursor: 'pointer',
                    }}>
                        <input type="checkbox" checked={newVisibleToStudents}
                            onChange={e => setNewVisibleToStudents(e.target.checked)}
                            style={{ accentColor: '#10b981', cursor: 'pointer' }} />
                        Show to students
                    </label>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <input type="text" value={newText} onChange={e => setNewText(e.target.value)}
                        placeholder="Add an annotation..." onKeyDown={e => e.key === 'Enter' && addAnnotation()}
                        style={{ flex: 1, padding: '0.6rem 0.75rem', borderRadius: '6px', border: '1px solid var(--border-subtle)', background: 'var(--bg-body)', color: 'var(--text-primary)', fontSize: '0.85rem' }} />
                    <button onClick={addAnnotation} disabled={saving || !newText.trim()} style={{
                        padding: '0.5rem 1rem', borderRadius: '6px', border: 'none',
                        background: '#3b82f6', color: '#fff', fontWeight: 600, fontSize: '0.82rem', cursor: 'pointer',
                        opacity: saving || !newText.trim() ? 0.5 : 1,
                    }}>{saving ? '⏳' : '+ Add'}</button>
                </div>
            </div>

            {/* Annotations List */}
            {annotations.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No annotations yet</div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {annotations.map(ann => {
                        const tc = TAG_COLORS[ann.tag] || TAG_COLORS.general;
                        return (
                            <div key={ann.id} style={{
                                padding: '0.75rem 1rem', borderRadius: '8px',
                                background: tc.bg, border: `1px solid ${tc.border}`,
                                display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
                            }}>
                                <span style={{ fontSize: '1.1rem' }}>{tc.icon}</span>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{ann.text}</div>
                                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                                        R{ann.round} · {ann.tag.replace('_', ' ')} · {ann.created_at?.slice(0, 16)}
                                    </div>
                                </div>
                                <button onClick={() => deleteAnnotation(ann.id)} style={{
                                    background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1rem',
                                }}>×</button>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
