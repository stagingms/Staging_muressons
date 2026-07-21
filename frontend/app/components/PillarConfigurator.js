'use client';
import { useState, useEffect, useCallback } from 'react';
import styles from './PillarConfigurator.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const VERTICALS = [
    { id: 'agriculture', label: '🌾 Agriculture' },
    { id: 'banking_financial_services', label: '🏦 Banking & Finance' },
    { id: 'oil_gas', label: '⛽ Oil & Gas' },
    { id: 'retail_fmcg', label: '🛒 Retail / FMCG' },
    { id: 'technology', label: '💻 Technology' },
    { id: 'pharma', label: '💊 Pharma / Healthcare' },
];

const STANDARD_AREAS = [
    { id: 'energy', label: 'Energy', icon: '⚡' },
    { id: 'operations', label: 'Operations', icon: '⚙️' },
    { id: 'supply_chain', label: 'Supply Chain', icon: '🔗' },
    { id: 'carbon_offsetting', label: 'Carbon Offsetting / Vertical Override', icon: '🌿' },
    { id: 'human_resources', label: 'Human Resources', icon: '👥' },
];

function makeBlankArea() {
    return {
        id: `custom_${Date.now()}`,
        label: '',
        icon: '🏛️',
        order: 99,
        options: [
            makeBlankOption('A'),
            makeBlankOption('B'),
        ],
    };
}

function makeBlankOption(key = '') {
    return {
        option_key: key,
        title: '',
        description: '',
        cost: 0,
        carbon_intensity_delta: 0,
        reputation: 0,
        social_license_delta: 0,
        governance_risk_delta: 0,
        flags_set: '',
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

function OptionCard({ opt, idx, onChange, onRemove, canRemove }) {
    const update = (field, value) => onChange(idx, { ...opt, [field]: value });
    return (
        <div className={styles.optionCard}>
            <div className={styles.optionHeader}>
                <span className={styles.optionKeyBadge}>{opt.option_key || `Option ${idx + 1}`}</span>
                {canRemove && (
                    <button className={styles.btnDanger} onClick={() => onRemove(idx)} title="Remove option">✕</button>
                )}
            </div>
            <div className={styles.optionGrid}>
                <div className={styles.fieldGroup}>
                    <label className={styles.label}>Option Key</label>
                    <input className={styles.input} value={opt.option_key} onChange={e => update('option_key', e.target.value)} placeholder="e.g. A" />
                </div>
                <div className={styles.fieldGroup}>
                    <label className={styles.label}>Title</label>
                    <input className={styles.input} value={opt.title} onChange={e => update('title', e.target.value)} placeholder="Option title" />
                </div>
                <div className={styles.fieldGroup}>
                    <label className={styles.label}>Cost (USD, can be negative)</label>
                    <input className={styles.input} type="number" value={opt.cost} onChange={e => update('cost', Number(e.target.value))} />
                </div>
            </div>
            <div className={styles.fieldGroup} style={{ marginTop: '0.5rem' }}>
                <label className={styles.label}>Description</label>
                <textarea className={styles.textarea} rows={2} value={opt.description} onChange={e => update('description', e.target.value)} placeholder="Option description" />
            </div>
            <div className={styles.impactGrid}>
                {[
                    { key: 'carbon_intensity_delta', label: 'Carbon Δ' },
                    { key: 'reputation', label: 'Reputation Δ' },
                    { key: 'social_license_delta', label: 'Social License Δ' },
                    { key: 'governance_risk_delta', label: 'Gov. Risk Δ' },
                ].map(f => (
                    <div key={f.key} className={styles.fieldGroup}>
                        <label className={styles.label}>{f.label}</label>
                        <input
                            className={styles.input}
                            type="number"
                            step="0.01"
                            value={opt[f.key]}
                            onChange={e => update(f.key, Number(e.target.value))}
                        />
                    </div>
                ))}
                <div className={styles.fieldGroup}>
                    <label className={styles.label}>Flags Set (comma-separated)</label>
                    <input className={styles.input} value={opt.flags_set} onChange={e => update('flags_set', e.target.value)} placeholder="e.g. green_certified,iso_compliant" />
                </div>
            </div>
        </div>
    );
}

function CustomAreaCard({ area, idx, onChange, onDelete }) {
    const update = (field, value) => onChange(idx, { ...area, [field]: value });

    const updateOption = (oIdx, updated) => {
        onChange(idx, { ...area, options: area.options.map((o, i) => i === oIdx ? updated : o) });
    };

    const addOption = () => {
        if (area.options.length >= 4) return;
        onChange(idx, { ...area, options: [...area.options, makeBlankOption(String.fromCharCode(65 + area.options.length))] });
    };

    const removeOption = (oIdx) => {
        if (area.options.length <= 2) return;
        onChange(idx, { ...area, options: area.options.filter((_, i) => i !== oIdx) });
    };

    return (
        <div className={styles.areaCard}>
            <div className={styles.areaCardHeader}>
                <div className={styles.areaCardTitle}>
                    <input
                        className={`${styles.input} ${styles.iconInput}`}
                        value={area.icon}
                        onChange={e => update('icon', e.target.value)}
                        style={{ width: '3rem', textAlign: 'center', fontSize: '1.3rem' }}
                        maxLength={4}
                        title="Icon (emoji)"
                    />
                    <input
                        className={styles.input}
                        placeholder="Area label"
                        value={area.label}
                        onChange={e => update('label', e.target.value)}
                        style={{ flex: 1, fontWeight: 700 }}
                    />
                    <div className={styles.fieldGroup} style={{ minWidth: 80, maxWidth: 100 }}>
                        <label className={styles.label}>Order</label>
                        <input className={styles.input} type="number" value={area.order} onChange={e => update('order', Number(e.target.value))} />
                    </div>
                </div>
                <button
                    className={styles.btnDanger}
                    onClick={() => {
                        if (confirm(`Delete custom area "${area.label || 'this area'}"?`)) onDelete(idx);
                    }}
                >
                    🗑️ Delete Area
                </button>
            </div>

            <div className={styles.optionsHeader}>
                <span className={styles.optionsLabel}>Options ({area.options.length}/4)</span>
                {area.options.length < 4 && (
                    <button className={styles.btnGhost} onClick={addOption}>+ Add Option</button>
                )}
            </div>

            <div className={styles.optionsList}>
                {area.options.map((opt, oIdx) => (
                    <OptionCard
                        key={oIdx}
                        opt={opt}
                        idx={oIdx}
                        onChange={updateOption}
                        onRemove={removeOption}
                        canRemove={area.options.length > 2}
                    />
                ))}
            </div>
        </div>
    );
}

export default function PillarConfigurator() {
    const [vertical, setVertical] = useState('');
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [toast, setToast] = useState({ message: '', type: 'success' });

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast({ message: '', type: 'success' }), 3500);
    };

    const handleLoad = useCallback(async () => {
        if (!vertical) return;
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/pillar-config/${vertical}`);
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Failed to load');
            const data = await res.json();
            setConfig(data);
        } catch (err) {
            showToast(`❌ ${err.message}`, 'error');
            setConfig({ custom_areas: [] });
        } finally {
            setLoading(false);
        }
    }, [vertical]);

    useEffect(() => {
        if (vertical) handleLoad();
    }, [vertical]);

    const handleAreaChange = (idx, updated) => {
        setConfig(prev => ({
            ...prev,
            custom_areas: prev.custom_areas.map((a, i) => i === idx ? updated : a),
        }));
    };

    const handleAreaDelete = (idx) => {
        setConfig(prev => ({
            ...prev,
            custom_areas: prev.custom_areas.filter((_, i) => i !== idx),
        }));
    };

    const handleAddArea = () => {
        setConfig(prev => ({
            ...prev,
            custom_areas: [...(prev?.custom_areas || []), makeBlankArea()],
        }));
    };

    const handleSaveAll = async () => {
        if (!vertical || !config) return;
        setSaving(true);
        try {
            const res = await fetch(`${API}/api/admin/pillar-config/${vertical}/order`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ custom_areas: config.custom_areas }),
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Save failed');
            showToast('✅ Pillar configuration saved successfully');
        } catch (err) {
            showToast(`❌ ${err.message}`, 'error');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div>
                    <h2 className={styles.title}>🏛️ Pillar Configurator</h2>
                    <p className={styles.subtitle}>Manage strategic decision areas per industry vertical</p>
                </div>
                {config && (
                    <button className={styles.btnPrimary} onClick={handleSaveAll} disabled={saving}>
                        {saving ? '⏳ Saving...' : '💾 Save All'}
                    </button>
                )}
            </div>

            <Toast message={toast.message} type={toast.type} />

            {/* Vertical selector */}
            <div className={styles.selectorRow}>
                <div className={styles.fieldGroup} style={{ maxWidth: 300 }}>
                    <label className={styles.label}>Industry Vertical</label>
                    <select className={styles.select} value={vertical} onChange={e => setVertical(e.target.value)}>
                        <option value="">— Select Vertical —</option>
                        {VERTICALS.map(v => <option key={v.id} value={v.id}>{v.label}</option>)}
                    </select>
                </div>
                {loading && <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', alignSelf: 'flex-end', paddingBottom: '0.4rem' }}>⏳ Loading...</span>}
            </div>

            {/* Standard areas */}
            <div className={styles.section}>
                <div className={styles.sectionHeader}>
                    <span>🔒 Standard Areas (Read-only)</span>
                    <span className={styles.sectionBadge}>5 areas</span>
                </div>
                <div className={styles.standardGrid}>
                    {STANDARD_AREAS.map(area => (
                        <div key={area.id} className={styles.standardCard}>
                            <span className={styles.standardIcon}>{area.icon}</span>
                            <span className={styles.standardLabel}>{area.label}</span>
                            <span className={styles.lockBadge}>🔒</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Custom areas */}
            {config && (
                <div className={styles.section}>
                    <div className={styles.sectionHeader}>
                        <span>✨ Custom Areas</span>
                        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                            <span className={styles.sectionBadge}>{config.custom_areas?.length || 0} custom</span>
                            <button className={styles.btnGhost} onClick={handleAddArea}>+ Add Custom Area</button>
                        </div>
                    </div>

                    {(!config.custom_areas || config.custom_areas.length === 0) ? (
                        <div className={styles.placeholder}>
                            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🏛️</div>
                            <p>No custom areas configured. Click <strong>+ Add Custom Area</strong> to create one.</p>
                        </div>
                    ) : (
                        <div className={styles.customAreasList}>
                            {config.custom_areas.map((area, idx) => (
                                <CustomAreaCard
                                    key={area.id || idx}
                                    area={area}
                                    idx={idx}
                                    onChange={handleAreaChange}
                                    onDelete={handleAreaDelete}
                                />
                            ))}
                        </div>
                    )}
                </div>
            )}

            {!vertical && !config && (
                <div className={styles.placeholder}>
                    <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🏛️</div>
                    <p>Select an <strong>Industry Vertical</strong> to view and configure pillar areas.</p>
                </div>
            )}
        </div>
    );
}
