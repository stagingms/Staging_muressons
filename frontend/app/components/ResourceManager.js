'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './ResourceManager.module.css';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

const TYPE_ICONS = { PDF: '📄', Video: '🎬', Weblink: '🔗', Memo: '📝' };
const TYPE_CLASS = { PDF: styles.typePDF, Video: styles.typeVideo, Weblink: styles.typeWeblink, Memo: styles.typeMemo };

export default function ResourceManager() {
    const [activeTab, setActiveTab] = useState('library');
    const [library, setLibrary] = useState([]);
    const [sessions, setSessions] = useState([]);
    const [selectedSession, setSelectedSession] = useState('');
    const [sessionResources, setSessionResources] = useState([]);
    const [deploymentGuide, setDeploymentGuide] = useState(null);
    const [status, setStatus] = useState(null);

    // Add Individual Resource State
    const [showAddForm, setShowAddForm] = useState(false);
    const [formData, setFormData] = useState({
        id: '', title: '', type: 'PDF', url: '', category: 'General', 
        facilitator_default_round: 1, visibility: 'Standard', tags: '', facilitator_strategy: ''
    });

    // ── Fetch master library ────────────────────────────────
    const fetchLibrary = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/admin/resources/library`);
            if (res.ok) { const d = await res.json(); setLibrary(d.resources || []); }
        } catch (e) { console.error('Failed to fetch library', e); }
    }, []);

    // ── Fetch sessions ──────────────────────────────────────
    const fetchSessions = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/admin/sessions`);
            if (res.ok) { const d = await res.json(); setSessions(d.sessions || []); }
        } catch (e) { console.error('Failed to fetch sessions', e); }
    }, []);

    // ── Fetch session resources ─────────────────────────────
    const fetchSessionResources = useCallback(async (sid) => {
        if (!sid) return;
        try {
            const res = await fetch(`${API_BASE}/api/admin/sessions/${sid}/resources`);
            if (res.ok) { const d = await res.json(); setSessionResources(d.resources || []); }
        } catch (e) { console.error('Failed to fetch session resources', e); }
    }, []);

    // ── Fetch deployment guide ──────────────────────────────
    const fetchGuide = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/admin/resources/deployment-guide`);
            if (res.ok) { const d = await res.json(); setDeploymentGuide(d); }
        } catch (e) { console.error('Failed to fetch guide', e); }
    }, []);

    useEffect(() => {
        fetchLibrary();
        fetchSessions();
        fetchGuide();
    }, [fetchLibrary, fetchSessions, fetchGuide]);

    useEffect(() => {
        if (selectedSession) fetchSessionResources(selectedSession);
    }, [selectedSession, fetchSessionResources]);

    // ── Upload JSON ─────────────────────────────────────────
    const handleUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        try {
            const text = await file.text();
            const data = JSON.parse(text);
            const res = await fetch(`${API_BASE}/api/admin/resources/library`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (res.ok) {
                const d = await res.json();
                setStatus({ type: 'success', msg: `✅ Uploaded ${d.count} resources` });
                fetchLibrary();
                fetchGuide();
            } else {
                setStatus({ type: 'error', msg: '❌ Upload failed — check JSON format' });
            }
        } catch (err) {
            setStatus({ type: 'error', msg: `❌ Parse error: ${err.message}` });
        }
        e.target.value = '';
    };

    // ── Add Individual Resource ─────────────────────────────
    const handleAddSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...formData,
                facilitator_default_round: parseInt(formData.facilitator_default_round, 10),
                tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean)
            };
            const res = await fetch(`${API_BASE}/api/admin/resources/library/item`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (res.ok) {
                setStatus({ type: 'success', msg: `✅ Resource ${formData.id} added successfully.` });
                fetchLibrary();
                fetchGuide();
                setShowAddForm(false);
                setFormData({ id: '', title: '', type: 'PDF', url: '', category: 'General', facilitator_default_round: 1, visibility: 'Standard', tags: '', facilitator_strategy: '' });
            } else {
                let errMsg = 'Unknown error';
                try {
                    const err = await res.json();
                    errMsg = err.detail || 'Unknown error';
                } catch {
                    errMsg = `Server error ${res.status}`;
                }
                setStatus({ type: 'error', msg: `❌ Failed to add: ${errMsg}` });
            }
        } catch (err) {
            setStatus({ type: 'error', msg: `❌ Network error: ${err.message}` });
        }
    };

    // ── Upload Physical File ────────────────────────────────
    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        setStatus({ type: 'info', msg: 'Uploading file...' });
        const formDataUpload = new FormData();
        formDataUpload.append('file', file);

        try {
            // Bypass Next.js proxy for file uploads to preserve multipart boundaries
            const uploadUrl = API_BASE ? `${API_BASE}/api/admin/resources/upload` : 'http://localhost:8000/api/admin/resources/upload';
            const res = await fetch(uploadUrl, {
                method: 'POST',
                body: formDataUpload,
            });
            if (res.ok) {
                const d = await res.json();
                setFormData(prev => ({ ...prev, url: d.url }));
                setStatus({ type: 'success', msg: `✅ File uploaded: ${file.name}` });
            } else {
                let errMsg = 'Unknown error';
                try {
                    const err = await res.json();
                    errMsg = err.detail || 'Unknown error';
                } catch {
                    errMsg = `Server error ${res.status}`;
                }
                setStatus({ type: 'error', msg: `❌ File upload failed: ${errMsg}` });
            }
        } catch (err) {
            setStatus({ type: 'error', msg: `❌ Network error: ${err.message}` });
        }
        e.target.value = ''; // Reset input
    };

    // ── Delete resource ─────────────────────────────────────
    const handleDelete = async (id) => {
        try {
            await fetch(`${API_BASE}/api/admin/resources/library/item/${id}`, { method: 'DELETE' });
            fetchLibrary();
        } catch (e) { console.error(e); }
    };

    // ── Toggle unlock ───────────────────────────────────────
    const handleToggle = async (resourceId, currentlyUnlocked) => {
        if (!selectedSession) return;
        try {
            if (currentlyUnlocked) {
                await fetch(`${API_BASE}/api/admin/sessions/${selectedSession}/resources/lock`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ resource_id: resourceId }),
                });
            } else {
                const sess = sessions.find(s => s.session_id === selectedSession);
                const round = sess?.round_number || 1;
                await fetch(`${API_BASE}/api/admin/sessions/${selectedSession}/resources/unlock`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ resource_ids: [resourceId], round_number: round }),
                });
            }
            fetchSessionResources(selectedSession);
        } catch (e) { console.error(e); }
    };

    // ── Strategic Drop ──────────────────────────────────────
    const handleDrop = async (resourceId) => {
        if (!selectedSession) return;
        const sess = sessions.find(s => s.session_id === selectedSession);
        const round = sess?.round_number || 1;
        try {
            await fetch(`${API_BASE}/api/admin/sessions/${selectedSession}/resources/drop`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ resource_ids: [resourceId], round_number: round }),
            });
            setStatus({ type: 'success', msg: `🚨 Strategic drop sent!` });
            fetchSessionResources(selectedSession);
        } catch (e) { console.error(e); }
    };

    // ── Render: Master Library Tab ──────────────────────────
    const renderLibrary = () => (
        <>
            {/* Upload */}
            <div className={styles.uploadSection}>
                <h3>📦 Upload Master Library (JSON)</h3>
                <label className={styles.uploadArea}>
                    <input type="file" accept=".json" onChange={handleUpload} />
                    <div className={styles.fileInfo}>
                        <span style={{ fontSize: '1.5rem' }}>📁</span>
                        <span>Click to upload <strong>Resource_Library.json</strong></span>
                    </div>
                </label>
            </div>

            {status && (
                <div className={`${styles.statusMsg} ${status.type === 'success' ? styles.statusSuccess : styles.statusError}`}>
                    {status.msg}
                </div>
            )}

            {/* Actions Bar */}
            <div className={styles.libraryActions}>
                <button 
                    className={`${styles.addBtn} ${showAddForm ? styles.addBtnActive : ''}`} 
                    onClick={() => setShowAddForm(!showAddForm)}
                >
                    {showAddForm ? '⨯ Cancel Adding' : '➕ Add Individual Resource'}
                </button>
            </div>

            {/* Add Individual Resource Form */}
            {showAddForm && (
                <form onSubmit={handleAddSubmit} className={styles.addForm}>
                    <h4>Create New Resource</h4>
                    <div className={styles.formGrid}>
                        <div className={styles.inputGroup}>
                            <label>Resource ID *</label>
                            <input required placeholder="e.g. RES_105" value={formData.id} onChange={e => setFormData({...formData, id: e.target.value})} />
                        </div>
                        <div className={styles.inputGroup}>
                            <label>Title *</label>
                            <input required placeholder="Resource Title" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} />
                        </div>
                        <div className={styles.inputGroup}>
                            <label>Type</label>
                            <select value={formData.type} onChange={e => setFormData({...formData, type: e.target.value})}>
                                <option value="PDF">📄 PDF</option>
                                <option value="Video">🎬 Video</option>
                                <option value="Weblink">🔗 Weblink</option>
                                <option value="Memo">📝 Memo</option>
                            </select>
                        </div>
                        <div className={styles.inputGroup}>
                            <label>Category</label>
                            <select value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})}>
                                <option value="General">General</option>
                                <option value="Ecological">Ecological</option>
                                <option value="Social">Social</option>
                                <option value="Economic">Economic</option>
                            </select>
                        </div>
                        <div className={styles.inputGroup}>
                            <label>URL / Link</label>
                            <input placeholder="https://..." value={formData.url} onChange={e => setFormData({...formData, url: e.target.value})} />
                        </div>
                        <div className={styles.inputGroup}>
                            <label>Or Upload Local File</label>
                            <input 
                                type="file" 
                                onChange={handleFileUpload} 
                                className={styles.fileInput} 
                                title="Upload a file instead of providing a URL"
                            />
                        </div>
                        <div className={styles.inputGroup}>
                            <label>Target Round</label>
                            <input type="number" min="1" max="10" required value={formData.facilitator_default_round} onChange={e => setFormData({...formData, facilitator_default_round: e.target.value})} />
                        </div>
                        <div className={styles.inputGroup}>
                            <label>Visibility</label>
                            <select value={formData.visibility} onChange={e => setFormData({...formData, visibility: e.target.value})}>
                                <option value="Standard">Standard (Manual Unlock)</option>
                                <option value="Hidden">Hidden (Auto-Unlock via trigger)</option>
                            </select>
                        </div>
                        <div className={styles.inputGroup}>
                            <label>Tags (comma separated)</label>
                            <input placeholder="e.g. ESG, General" value={formData.tags} onChange={e => setFormData({...formData, tags: e.target.value})} />
                        </div>
                        <div className={`${styles.inputGroup} ${styles.fullWidth}`}>
                            <label>Facilitator Strategy (Guide text)</label>
                            <textarea placeholder="Strategy hint for the deployment guide..." value={formData.facilitator_strategy} onChange={e => setFormData({...formData, facilitator_strategy: e.target.value})} rows="2" />
                        </div>
                    </div>
                    <button type="submit" className={styles.submitBtn}>Save Resource</button>
                </form>
            )}

            {/* Table */}
            <table className={styles.resourceTable}>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Category</th>
                        <th>Round</th>
                        <th>Visibility</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    {library.map(r => (
                        <tr key={r.id}>
                            <td style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>{r.id}</td>
                            <td>
                                {r.title}
                                {r.visibility === 'Hidden' && <span className={styles.hiddenBadge}>🔒 HIDDEN</span>}
                            </td>
                            <td>
                                <span className={`${styles.typeBadge} ${TYPE_CLASS[r.type] || ''}`}>
                                    {TYPE_ICONS[r.type] || '📌'} {r.type}
                                </span>
                            </td>
                            <td>{r.category}</td>
                            <td>{r.facilitator_default_round || '—'}</td>
                            <td>{r.visibility || 'Standard'}</td>
                            <td>
                                <button className={styles.deleteBtn} onClick={() => handleDelete(r.id)} title="Delete">
                                    🗑️
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            {library.length === 0 && (
                <p style={{ textAlign: 'center', color: '#64748b', padding: '2rem' }}>
                    No resources loaded. Upload a JSON file to get started.
                </p>
            )}
        </>
    );

    // ── Render: Session Control Tab ─────────────────────────
    const renderSessionControl = () => (
        <>
            <div className={styles.sessionSelector}>
                <label>🎯 Session:</label>
                <select value={selectedSession} onChange={e => setSelectedSession(e.target.value)}>
                    <option value="">— Select a session —</option>
                    {sessions.map(s => (
                        <option key={s.session_id} value={s.session_id}>
                            {s.cohort_name} (R{s.round_number || '?'})
                        </option>
                    ))}
                </select>
            </div>

            {!selectedSession && (
                <p style={{ textAlign: 'center', color: '#64748b', padding: '2rem' }}>
                    Select a session to manage resources.
                </p>
            )}

            {selectedSession && sessionResources.map(r => (
                <div key={r.id} className={styles.toggleRow}>
                    <div className={styles.toggleInfo}>
                        <span className={styles.toggleTitle}>
                            {TYPE_ICONS[r.type] || '📌'} {r.title}
                            {r.visibility === 'Hidden' && <span className={styles.hiddenBadge}>🔒 HIDDEN</span>}
                        </span>
                        <span className={styles.toggleMeta}>
                            {r.category} · {r.type} · Suggested R{r.facilitator_default_round}
                            {r.unlocked_at_round ? ` · Unlocked R${r.unlocked_at_round}` : ''}
                            {r.is_strategic_drop ? ' · 🚨 DROPPED' : ''}
                        </span>
                    </div>
                    <div className={styles.toggleActions}>
                        {!r.unlocked && r.visibility !== 'Hidden' && (
                            <button className={styles.dropBtn} onClick={() => handleDrop(r.id)}>
                                🚨 Drop
                            </button>
                        )}
                        <label className={styles.toggleSwitch}>
                            <input
                                type="checkbox"
                                checked={r.unlocked}
                                onChange={() => handleToggle(r.id, r.unlocked)}
                            />
                            <span className={styles.slider}></span>
                        </label>
                    </div>
                </div>
            ))}
        </>
    );

    // ── Render: Deployment Guide Tab ────────────────────────
    const renderGuide = () => {
        if (!deploymentGuide) return <p style={{ color: '#64748b' }}>Loading guide...</p>;

        // Group by round
        const byRound = {};
        (deploymentGuide.round_deployment || []).forEach(entry => {
            if (!byRound[entry.round]) byRound[entry.round] = [];
            byRound[entry.round].push(entry);
        });

        return (
            <div className={styles.guideSection}>
                <h3>📋 Facilitator Deployment Strategy</h3>
                {Object.entries(byRound)
                    .sort(([a], [b]) => Number(a) - Number(b))
                    .map(([round, entries]) => (
                        <div key={round} className={styles.guideRound}>
                            <div className={styles.guideRoundHeader}>
                                <span className={styles.roundBadge}>R{round}</span>
                                <span>Round {round}</span>
                            </div>
                            {entries.map(entry => (
                                <div key={entry.resource_id} className={styles.guideItem}>
                                    <span className={`${styles.typeBadge} ${TYPE_CLASS[entry.type] || ''}`} style={{ marginRight: '0.5rem' }}>
                                        {TYPE_ICONS[entry.type] || '📌'} {entry.type}
                                    </span>
                                    <strong>{entry.title}</strong>
                                    <div className={styles.guideStrategy}>💡 {entry.strategy}</div>
                                </div>
                            ))}
                        </div>
                    ))}

                {/* Hidden Resources */}
                {deploymentGuide.hidden_resources?.length > 0 && (
                    <div className={styles.hiddenGuide}>
                        <h4>🔒 Hidden Resource Triggers (Alpha Levers)</h4>
                        {deploymentGuide.hidden_resources.map(h => (
                            <div key={h.resource_id} className={styles.hiddenCard}>
                                <h5>{h.title}</h5>
                                <p className={styles.conditionText}>
                                    🎯 Unlock: <code>{h.unlock_condition?.metric}</code> {h.unlock_condition?.operator} {h.unlock_condition?.value?.toLocaleString()}
                                    {h.unlock_condition?.min_round > 1 ? ` (from Round ${h.unlock_condition.min_round})` : ''}
                                </p>
                                {h.effect && (
                                    <p className={styles.effectText}>
                                        ⚡ Effect: {h.effect.target} → {h.effect.modifier > 0 ? '+' : ''}{h.effect.modifier < 1 && h.effect.modifier > -1
                                            ? `${(h.effect.modifier * 100).toFixed(0)}%`
                                            : `$${h.effect.modifier.toLocaleString()}`}
                                    </p>
                                )}
                                {h.strategy && <p className={styles.guideStrategy}>💡 {h.strategy}</p>}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className={styles.resourceManager}>
            <div className={styles.tabBar}>
                <button className={`${styles.tabBtn} ${activeTab === 'library' ? styles.active : ''}`}
                    onClick={() => setActiveTab('library')}>
                    📦 Master Library
                </button>
                <button className={`${styles.tabBtn} ${activeTab === 'sessions' ? styles.active : ''}`}
                    onClick={() => setActiveTab('sessions')}>
                    🎯 Session Control
                </button>
                <button className={`${styles.tabBtn} ${activeTab === 'guide' ? styles.active : ''}`}
                    onClick={() => setActiveTab('guide')}>
                    📋 Deployment Guide
                </button>
            </div>

            {activeTab === 'library' && renderLibrary()}
            {activeTab === 'sessions' && renderSessionControl()}
            {activeTab === 'guide' && renderGuide()}
        </div>
    );
}
