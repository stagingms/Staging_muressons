'use client';
import { useState, useEffect, useCallback, useRef } from 'react';
import styles from './StakeholderConfig.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const VERTICALS = [
    { id: 'agriculture', label: '🌾 Agriculture' },
    { id: 'banking_financial_services', label: '🏦 Banking & Finance' },
    { id: 'oil_gas', label: '⛽ Oil & Gas' },
    { id: 'retail_fmcg', label: '🛒 Retail / FMCG' },
    { id: 'technology', label: '💻 Technology' },
    { id: 'pharma', label: '💊 Pharma / Healthcare' },
];

const REGIONS = [
    { id: 'asean', label: '🌏 ASEAN' },
    { id: 'south_asia', label: '🇮🇳 India' },
    { id: 'europe', label: '🇪🇺 Europe' },
    { id: 'north_america', label: '🇺🇸 North America' },
    { id: 'africa', label: '🌍 Africa' },
];

const POWER_OPTS = ['high', 'low'];
const INTEREST_OPTS = ['high', 'low'];
const QUADRANT_OPTS = [
    { value: 'manage_closely', label: 'Manage Closely' },
    { value: 'keep_informed', label: 'Keep Informed' },
    { value: 'keep_satisfied', label: 'Keep Satisfied' },
    { value: 'monitor', label: 'Monitor' },
];

function makeBlankStakeholder() {
    return {
        id: `sh_${Date.now()}`,
        name: '',
        icon: '👤',
        power: 'high',
        interest: 'high',
        quadrant: 'manage_closely',
        urgency: false,
        legitimacy: false,
        description: '',
        engagement_tactics: [
            { option_text: '', rationale: '', is_correct: false },
        ],
    };
}

function Toast({ message, type }) {
    if (!message) return null;
    const bg = type === 'error' ? 'rgba(239,68,68,0.12)' : 'rgba(16,185,129,0.12)';
    const border = type === 'error' ? 'rgba(239,68,68,0.35)' : 'rgba(16,185,129,0.35)';
    const color = type === 'error' ? '#ef4444' : '#10b981';
    return (
        <div style={{
            padding: '0.65rem 1rem', borderRadius: '8px', fontSize: '0.82rem',
            fontWeight: 600, background: bg, border: `1px solid ${border}`, color,
            marginBottom: '1rem',
        }}>
            {message}
        </div>
    );
}

function TacticRow({ tactic, idx, onChange, onRemove }) {
    return (
        <div className={styles.tacticRow}>
            <input
                className={styles.input}
                placeholder="Option text"
                value={tactic.option_text}
                onChange={e => onChange(idx, 'option_text', e.target.value)}
            />
            <input
                className={styles.input}
                placeholder="Rationale"
                value={tactic.rationale}
                onChange={e => onChange(idx, 'rationale', e.target.value)}
            />
            <label className={styles.checkLabel}>
                <input
                    type="checkbox"
                    checked={tactic.is_correct}
                    onChange={e => onChange(idx, 'is_correct', e.target.checked)}
                />
                Correct
            </label>
            <button className={styles.btnDanger} onClick={() => onRemove(idx)} title="Remove tactic">✕</button>
        </div>
    );
}

function StakeholderCard({ sh, idx, onChange, onDelete, onSave, saving }) {
    const updateField = (field, value) => onChange(idx, { ...sh, [field]: value });

    const updateTactic = (tIdx, field, value) => {
        const tactics = sh.engagement_tactics.map((t, i) =>
            i === tIdx ? { ...t, [field]: value } : t
        );
        onChange(idx, { ...sh, engagement_tactics: tactics });
    };

    const addTactic = () => {
        onChange(idx, {
            ...sh,
            engagement_tactics: [...sh.engagement_tactics, { option_text: '', rationale: '', is_correct: false }],
        });
    };

    const removeTactic = (tIdx) => {
        onChange(idx, {
            ...sh,
            engagement_tactics: sh.engagement_tactics.filter((_, i) => i !== tIdx),
        });
    };

    return (
        <div className={styles.card}>
            <div className={styles.cardHeader}>
                <div className={styles.cardTitle}>
                    <input
                        className={`${styles.input} ${styles.iconInput}`}
                        value={sh.icon}
                        onChange={e => updateField('icon', e.target.value)}
                        title="Emoji icon"
                        maxLength={4}
                        style={{ width: '3rem', textAlign: 'center', fontSize: '1.3rem' }}
                    />
                    <input
                        className={styles.input}
                        placeholder="Stakeholder name"
                        value={sh.name}
                        onChange={e => updateField('name', e.target.value)}
                        style={{ flex: 1, fontWeight: 700 }}
                    />
                </div>
                <div className={styles.cardActions}>
                    <button
                        className={styles.btnPrimary}
                        onClick={() => onSave(idx)}
                        disabled={saving}
                    >
                        {saving ? '⏳' : '💾'} Save
                    </button>
                    <button
                        className={styles.btnDanger}
                        onClick={() => onDelete(idx)}
                        title="Delete stakeholder"
                    >
                        🗑️
                    </button>
                </div>
            </div>

            <div className={styles.fieldGrid}>
                <div className={styles.fieldGroup}>
                    <label className={styles.label}>Power</label>
                    <select className={styles.select} value={sh.power} onChange={e => updateField('power', e.target.value)}>
                        {POWER_OPTS.map(o => <option key={o} value={o}>{o.charAt(0).toUpperCase() + o.slice(1)}</option>)}
                    </select>
                </div>
                <div className={styles.fieldGroup}>
                    <label className={styles.label}>Interest</label>
                    <select className={styles.select} value={sh.interest} onChange={e => updateField('interest', e.target.value)}>
                        {INTEREST_OPTS.map(o => <option key={o} value={o}>{o.charAt(0).toUpperCase() + o.slice(1)}</option>)}
                    </select>
                </div>
                <div className={styles.fieldGroup}>
                    <label className={styles.label}>Quadrant</label>
                    <select className={styles.select} value={sh.quadrant} onChange={e => updateField('quadrant', e.target.value)}>
                        {QUADRANT_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                </div>
            </div>

            <div className={styles.checkboxRow}>
                <label className={styles.checkLabel}>
                    <input type="checkbox" checked={sh.urgency || false} onChange={e => updateField('urgency', e.target.checked)} />
                    <span>Urgency</span>
                </label>
                <label className={styles.checkLabel}>
                    <input type="checkbox" checked={sh.legitimacy || false} onChange={e => updateField('legitimacy', e.target.checked)} />
                    <span>Legitimacy</span>
                </label>
            </div>

            <div className={styles.fieldGroup} style={{ marginTop: '0.75rem' }}>
                <label className={styles.label}>Description</label>
                <textarea
                    className={styles.textarea}
                    rows={2}
                    placeholder="Stakeholder description"
                    value={sh.description}
                    onChange={e => updateField('description', e.target.value)}
                />
            </div>

            <div className={styles.tacticsSection}>
                <div className={styles.sectionSubheader}>
                    <span>Engagement Tactics</span>
                    <button className={styles.btnGhost} onClick={addTactic}>+ Add Tactic</button>
                </div>
                {sh.engagement_tactics.map((t, tIdx) => (
                    <TacticRow
                        key={tIdx}
                        tactic={t}
                        idx={tIdx}
                        onChange={updateTactic}
                        onRemove={removeTactic}
                    />
                ))}
            </div>
        </div>
    );
}

export default function StakeholderConfig() {
    const [vertical, setVertical] = useState('');
    const [region, setRegion] = useState('');
    const [stakeholders, setStakeholders] = useState([]);
    const [loaded, setLoaded] = useState(false);
    const [loading, setLoading] = useState(false);
    const [savingIdx, setSavingIdx] = useState(null);
    const [saving, setSaving] = useState(false);
    const [toast, setToast] = useState({ message: '', type: 'success' });

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast({ message: '', type: 'success' }), 3500);
    };

    const handleLoad = useCallback(async () => {
        if (!region) return;
        setLoading(true);
        setLoaded(false);
        try {
            const url = `${API}/api/admin/stakeholder-config/regions/${region}${vertical ? `?vertical=${vertical}` : ''}`;
            const res = await fetch(url, { credentials: 'include' });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Failed to load');
            const data = await res.json();
            setStakeholders(data.overrides || []);
            setLoaded(true);
        } catch (err) {
            showToast(`❌ ${err.message}`, 'error');
        } finally {
            setLoading(false);
        }
    }, [region, vertical]);

    const handleChange = (idx, updated) => {
        setStakeholders(prev => prev.map((s, i) => i === idx ? updated : s));
    };

    const handleSaveSingle = async (idx) => {
        setSavingIdx(idx);
        const sh = stakeholders[idx];
        try {
            const res = await fetch(`${API}/api/admin/stakeholder-config/regions/${region}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ overrides: stakeholders }),
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Save failed');
            showToast(`✅ "${sh.name || 'Stakeholder'}" saved`);
        } catch (err) {
            showToast(`❌ ${err.message}`, 'error');
        } finally {
            setSavingIdx(null);
        }
    };

    const handleSaveAll = async () => {
        if (!region) return;
        setSaving(true);
        try {
            const res = await fetch(`${API}/api/admin/stakeholder-config/regions/${region}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ overrides: stakeholders }),
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Save failed');
            showToast('✅ All stakeholders saved successfully');
        } catch (err) {
            showToast(`❌ ${err.message}`, 'error');
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = (idx) => {
        const sh = stakeholders[idx];
        if (!confirm(`Delete stakeholder "${sh.name || 'this stakeholder'}"? This cannot be undone.`)) return;
        setStakeholders(prev => prev.filter((_, i) => i !== idx));
    };

    const handleAdd = () => {
        setStakeholders(prev => [...prev, makeBlankStakeholder()]);
    };

    // ── Excel import/export state ───────────────────────────
    const [excelOpen, setExcelOpen] = useState(false);
    const [excelScope, setExcelScope] = useState('canonical');
    const [uploading, setUploading] = useState(false);
    const [downloading, setDownloading] = useState(false);
    const [excelFeedback, setExcelFeedback] = useState({ message: '', type: 'success' });
    const [dragActive, setDragActive] = useState(false);
    const fileInputRef = useRef(null);

    const EXCEL_SCOPES = [
        { value: 'canonical', label: 'Canonical (Default Set)' },
        ...REGIONS.map(r => ({ value: r.id, label: 'Region: ' + r.label })),
        ...VERTICALS.map(v => ({ value: 'vertical_' + v.id, label: 'Vertical: ' + v.label })),
    ];

    const showExcelFeedback = (message, type = 'success') => {
        setExcelFeedback({ message, type });
        setTimeout(() => setExcelFeedback({ message: '', type: 'success' }), 5000);
    };

    const handleDownloadExcel = async () => {
        setDownloading(true);
        try {
            const res = await fetch(API + '/api/admin/stakeholder-config/download/' + excelScope, { credentials: 'include' });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || 'Download failed');
            }
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'stakeholder_matrix_' + excelScope + '.xlsx';
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            showExcelFeedback('Downloaded stakeholder matrix for "' + excelScope + '"');
        } catch (err) {
            showExcelFeedback(err.message, 'error');
        } finally {
            setDownloading(false);
        }
    };

    const handleUploadExcel = async (file) => {
        if (!file) return;
        if (!file.name.toLowerCase().endsWith('.xlsx')) {
            showExcelFeedback('Only .xlsx files are accepted.', 'error');
            return;
        }
        if (file.size > 5 * 1024 * 1024) {
            showExcelFeedback('File too large. Maximum size is 5 MB.', 'error');
            return;
        }
        setUploading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch(API + '/api/admin/stakeholder-config/upload/' + excelScope, {
                method: 'POST',
                credentials: 'include',
                body: formData,
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || 'Upload failed');
            }
            const data = await res.json();
            showExcelFeedback('Uploaded ' + data.stakeholder_count + ' stakeholders for "' + excelScope + '"');
        } catch (err) {
            showExcelFeedback(err.message, 'error');
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleUploadExcel(e.dataTransfer.files[0]);
        }
    };

    const handleDragOver = (e) => { e.preventDefault(); e.stopPropagation(); setDragActive(true); };
    const handleDragLeave = (e) => { e.preventDefault(); e.stopPropagation(); setDragActive(false); };

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <div>
                    <h2 className={styles.title}>👥 Stakeholder Configurator</h2>
                    <p className={styles.subtitle}>Edit stakeholder profiles by industry vertical and region</p>
                </div>
                {loaded && (
                    <button className={styles.btnPrimary} onClick={handleSaveAll} disabled={saving}>
                        {saving ? '⏳ Saving...' : '💾 Save All'}
                    </button>
                )}
            </div>

            <Toast message={toast.message} type={toast.type} />

            {/* ── Excel Import / Export ─────────────────────── */}
            <div style={{
                background: 'var(--bg-body, #151820)',
                border: '1px solid var(--border-subtle, #2d3446)',
                borderRadius: '10px',
                overflow: 'hidden',
            }}>
                <button
                    onClick={() => setExcelOpen(v => !v)}
                    style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.85rem 1.15rem',
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-primary, #e2e8f0)',
                        cursor: 'pointer',
                        fontSize: '0.85rem',
                        fontWeight: 700,
                    }}
                >
                    <span>📊 Excel Import / Export</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted, #64748b)' }}>
                        {excelOpen ? '▲ Collapse' : '▼ Expand'}
                    </span>
                </button>
                {excelOpen && (
                    <div style={{ padding: '0 1.15rem 1.15rem', display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                        <Toast message={excelFeedback.message} type={excelFeedback.type} />

                        {/* Scope selector + buttons */}
                        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
                            <div className={styles.fieldGroup} style={{ minWidth: '220px' }}>
                                <label className={styles.label}>Config Scope</label>
                                <select
                                    className={styles.select}
                                    value={excelScope}
                                    onChange={e => setExcelScope(e.target.value)}
                                >
                                    {EXCEL_SCOPES.map(s => (
                                        <option key={s.value} value={s.value}>{s.label}</option>
                                    ))}
                                </select>
                            </div>
                            <button
                                className={styles.btnPrimary}
                                onClick={handleDownloadExcel}
                                disabled={downloading}
                                style={{ alignSelf: 'flex-end' }}
                            >
                                {downloading ? '⏳ Downloading...' : '⬇️ Download Excel'}
                            </button>
                        </div>

                        {/* Drop zone */}
                        <div
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onClick={() => fileInputRef.current && fileInputRef.current.click()}
                            style={{
                                border: '2px dashed ' + (dragActive ? '#3b82f6' : 'var(--border-subtle, #2d3446)'),
                                borderRadius: '8px',
                                padding: '1.75rem 1rem',
                                textAlign: 'center',
                                cursor: 'pointer',
                                transition: 'border-color 0.2s, background 0.2s',
                                background: dragActive ? 'rgba(59,130,246,0.06)' : 'transparent',
                            }}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".xlsx"
                                style={{ display: 'none' }}
                                onChange={e => handleUploadExcel(e.target.files && e.target.files[0])}
                            />
                            {uploading ? (
                                <p style={{ margin: 0, color: '#3b82f6', fontWeight: 600, fontSize: '0.85rem' }}>⏳ Uploading and validating…</p>
                            ) : (
                                <>
                                    <div style={{ fontSize: '2rem', marginBottom: '0.35rem' }}>📤</div>
                                    <p style={{ margin: 0, color: 'var(--text-muted, #64748b)', fontSize: '0.82rem' }}>
                                        <strong style={{ color: 'var(--text-primary, #e2e8f0)' }}>Drop .xlsx file here</strong> or click to browse
                                    </p>
                                    <p style={{ margin: '0.25rem 0 0', color: 'var(--text-muted, #64748b)', fontSize: '0.72rem' }}>Max 5 MB • .xlsx only</p>
                                </>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Selector row */}
            <div className={styles.selectorRow}>

                <div className={styles.fieldGroup}>
                    <label className={styles.label}>Industry Vertical</label>
                    <select className={styles.select} value={vertical} onChange={e => setVertical(e.target.value)}>
                        <option value="">— All Verticals —</option>
                        {VERTICALS.map(v => <option key={v.id} value={v.id}>{v.label}</option>)}
                    </select>
                </div>
                <div className={styles.fieldGroup}>
                    <label className={styles.label}>Geographic Region <span style={{ color: '#ef4444' }}>*</span></label>
                    <select className={styles.select} value={region} onChange={e => setRegion(e.target.value)}>
                        <option value="">— Select Region —</option>
                        {REGIONS.map(r => <option key={r.id} value={r.id}>{r.label}</option>)}
                    </select>
                </div>
                <button
                    className={styles.btnPrimary}
                    onClick={handleLoad}
                    disabled={!region || loading}
                    style={{ alignSelf: 'flex-end' }}
                >
                    {loading ? '⏳ Loading...' : '⬇️ Load'}
                </button>
            </div>

            {/* Grid */}
            {loaded && (
                <>
                    <div className={styles.gridHeader}>
                        <span className={styles.countBadge}>{stakeholders.length} stakeholder{stakeholders.length !== 1 ? 's' : ''}</span>
                        <button className={styles.btnGhost} onClick={handleAdd}>
                            + Add Stakeholder
                        </button>
                    </div>
                    {stakeholders.length === 0 ? (
                        <div className={styles.placeholder}>
                            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>👤</div>
                            <p>No stakeholders found. Click <strong>+ Add Stakeholder</strong> to create one.</p>
                        </div>
                    ) : (
                        <div className={styles.cardGrid}>
                            {stakeholders.map((sh, idx) => (
                                <StakeholderCard
                                    key={sh.id || idx}
                                    sh={sh}
                                    idx={idx}
                                    onChange={handleChange}
                                    onDelete={handleDelete}
                                    onSave={handleSaveSingle}
                                    saving={savingIdx === idx}
                                />
                            ))}
                        </div>
                    )}
                </>
            )}

            {!loaded && !loading && (
                <div className={styles.placeholder}>
                    <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🗂️</div>
                    <p>Select a region and click <strong>Load</strong> to view stakeholder configurations.</p>
                </div>
            )}
        </div>
    );
}
