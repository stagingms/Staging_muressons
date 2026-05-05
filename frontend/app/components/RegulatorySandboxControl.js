'use client';

import React, { useState, useEffect, useCallback } from 'react';
import styles from './RegulatorySandboxControl.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const THEORY_COLORS = {
    'Pigou':   '#f59e0b',
    'Coase':   '#3b82f6',
    'Akerlof': '#8b5cf6',
    'Ruggie':  '#10b981',
    'Dasgupta':'#06b6d4',
    'ILO':     '#ef4444',
    'Ostrom':  '#6366f1',
};

function getTheoryColor(theory = '') {
    for (const [key, color] of Object.entries(THEORY_COLORS)) {
        if (theory.includes(key)) return color;
    }
    return '#64748b';
}

export default function RegulatorySandboxControl({ sessionId }) {
    const [instruments, setInstruments]   = useState({});
    const [customParams, setCustomParams] = useState({});
    const [loading, setLoading]           = useState(true);
    const [activating, setActivating]     = useState(null);
    const [actionStatus, setActionStatus] = useState('');
    const [statusType, setStatusType]     = useState('info');
    const [complexityIndex, setComplexityIndex] = useState(0);
    const [captureRisk, setCaptureRisk]   = useState(0);
    const [activeCount, setActiveCount]   = useState(0);

    const fetchInstruments = useCallback(() => {
        if (!sessionId) return;
        setLoading(true);
        fetch(`${API}/api/simulations/${sessionId}/regulatory-sandbox/instruments`)
            .then(res => res.ok ? res.json() : null)
            .then(data => {
                if (data?.instruments) {
                    setInstruments(data.instruments);
                    const defaults = {};
                    for (const [id, inst] of Object.entries(data.instruments)) {
                        defaults[id] = {};
                        for (const [pName, pConfig] of Object.entries(inst.parameters || {})) {
                            defaults[id][pName] = pConfig.default;
                        }
                    }
                    setCustomParams(defaults);
                }
            })
            .catch(() => {})
            .finally(() => setLoading(false));
    }, [sessionId]);

    useEffect(() => { fetchInstruments(); }, [fetchInstruments]);

    const handleParamChange = (instId, paramName, value, type) => {
        let val = value;
        if (type === 'number') { val = parseFloat(value); if (isNaN(val)) val = 0; }
        else if (type === 'bool') { val = value === 'true'; }
        setCustomParams(prev => ({ ...prev, [instId]: { ...prev[instId], [paramName]: val } }));
    };

    const activateInstrument = async (instId) => {
        setActivating(instId);
        setActionStatus(`Activating ${instruments[instId]?.name || instId}...`);
        setStatusType('info');
        try {
            const res = await fetch(`${API}/api/simulations/${sessionId}/regulatory-sandbox/activate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ instrument_id: instId, parameters: customParams[instId] || {} }),
            });
            if (res.ok) {
                const data = await res.json();
                setComplexityIndex(data.complexity_index || 0);
                setCaptureRisk(data.capture_risk || 0);
                setActiveCount(prev => prev + 1);
                setActionStatus(data.message || `Activated: ${instruments[instId]?.name}`);
                setStatusType(data.capture_warning ? 'warn' : 'success');
                if (data.capture_warning) {
                    setTimeout(() => { setActionStatus(data.capture_warning); setStatusType('warn'); }, 3500);
                }
                setTimeout(() => setActionStatus(''), 7000);
            } else {
                const err = await res.json().catch(() => ({}));
                setActionStatus(`Failed: ${err.detail || 'Activation error'}`);
                setStatusType('error');
                setTimeout(() => setActionStatus(''), 5000);
            }
        } catch {
            setActionStatus('Network error — check backend connection');
            setStatusType('error');
            setTimeout(() => setActionStatus(''), 5000);
        } finally {
            setActivating(null);
        }
    };

    if (!sessionId) {
        return (
            <section className={styles.panel}>
                <div className={styles.headerRow}>
                    <span className={styles.headerIcon}>⚖️</span>
                    <div>
                        <h2 className={styles.title}>Regulatory Sandbox</h2>
                        <p className={styles.subtitle}>Expert-tier ESG Regulatory Design</p>
                    </div>
                </div>
                <div className={styles.emptyState}>
                    <div className={styles.emptyIcon}>🏛️</div>
                    <p>Select a session from the Leaderboard to configure its regulatory environment.</p>
                </div>
            </section>
        );
    }

    if (loading) {
        return (
            <section className={styles.panel}>
                <div className={styles.loadingPulse}>Loading regulatory instruments…</div>
            </section>
        );
    }

    const complexityColor = complexityIndex > 70 ? '#ef4444' : complexityIndex > 40 ? '#f59e0b' : '#10b981';
    const captureColor    = captureRisk > 60    ? '#ef4444' : captureRisk > 30    ? '#f59e0b' : '#64748b';

    return (
        <section className={styles.panel}>
            {/* ── Header ── */}
            <div className={styles.headerRow}>
                <span className={styles.headerIcon}>⚖️</span>
                <div className={styles.headerText}>
                    <h2 className={styles.title}>Regulatory Sandbox</h2>
                    <p className={styles.subtitle}>
                        Inject regulatory instruments to test systemic resilience.
                        Theory base: Pigou · Coase · Ostrom · Ruggie · Akerlof.
                    </p>
                </div>
                <div className={styles.sessionTag}>{sessionId.slice(0, 12)}…</div>
            </div>

            {/* ── Complexity Gauges ── */}
            {activeCount > 0 && (
                <div className={styles.gaugeRow}>
                    <div className={styles.gauge}>
                        <span className={styles.gaugeLabel}>Regulatory Complexity</span>
                        <div className={styles.gaugeBar}>
                            <div className={styles.gaugeFill} style={{ width: `${complexityIndex}%`, background: complexityColor }} />
                        </div>
                        <span className={styles.gaugeVal} style={{ color: complexityColor }}>{complexityIndex.toFixed(0)}/100</span>
                    </div>
                    <div className={styles.gauge}>
                        <span className={styles.gaugeLabel}>Capture Risk (Stigler 1971)</span>
                        <div className={styles.gaugeBar}>
                            <div className={styles.gaugeFill} style={{ width: `${captureRisk}%`, background: captureColor }} />
                        </div>
                        <span className={styles.gaugeVal} style={{ color: captureColor }}>{captureRisk.toFixed(0)}%</span>
                    </div>
                </div>
            )}

            {/* ── Status Banner ── */}
            {actionStatus && (
                <div className={`${styles.statusBanner} ${styles[`status_${statusType}`]}`}>
                    {actionStatus}
                </div>
            )}

            {/* ── Polycentric Governance Hint ── */}
            {activeCount >= 3 && (
                <div className={styles.ostromHint}>
                    <strong>📚 Ostrom (2009) — Polycentric Governance:</strong> You are now operating multiple
                    overlapping instruments. Polycentric systems can be resilient but require coordination
                    to prevent complexity spirals and regulatory capture.
                </div>
            )}

            {/* ── Instrument Grid ── */}
            <div className={styles.instrumentGrid}>
                {Object.entries(instruments).map(([id, inst]) => {
                    const tc = getTheoryColor(inst.theory || '');
                    return (
                        <div key={id} className={styles.instrumentCard} style={{ '--accent': tc }}>
                            <div className={styles.cardAccentBar} style={{ background: tc }} />
                            <div className={styles.cardBody}>
                                <div className={styles.cardHeader}>
                                    <div>
                                        <h3 className={styles.instName}>{inst.name}</h3>
                                        <p className={styles.instDesc}>{inst.description}</p>
                                    </div>
                                    <span className={styles.theoryPill} style={{
                                        background: `${tc}18`, color: tc, borderColor: `${tc}40`
                                    }}>
                                        {(inst.theory || '').split('(')[0].trim().split(':')[0]}
                                    </span>
                                </div>

                                <div className={styles.paramsList}>
                                    {Object.entries(inst.parameters || {}).map(([pName, pConfig]) => (
                                        <div key={pName} className={styles.paramRow}>
                                            <label className={styles.paramLabel}>
                                                {pName.replace(/_/g, ' ')}
                                            </label>
                                            {pConfig.options ? (
                                                <select
                                                    className={styles.paramSelect}
                                                    value={customParams[id]?.[pName] ?? pConfig.default}
                                                    onChange={e => handleParamChange(id, pName, e.target.value, 'string')}
                                                >
                                                    {pConfig.options.map(opt => (
                                                        <option key={opt} value={opt}>{opt}</option>
                                                    ))}
                                                </select>
                                            ) : pConfig.type === 'bool' ? (
                                                <select
                                                    className={styles.paramSelect}
                                                    value={String(customParams[id]?.[pName] ?? pConfig.default)}
                                                    onChange={e => handleParamChange(id, pName, e.target.value, 'bool')}
                                                >
                                                    <option value="true">Yes</option>
                                                    <option value="false">No</option>
                                                </select>
                                            ) : (
                                                <div className={styles.numInput}>
                                                    <input
                                                        type="number"
                                                        min={pConfig.min} max={pConfig.max}
                                                        className={styles.paramNumber}
                                                        value={customParams[id]?.[pName] ?? pConfig.default}
                                                        onChange={e => handleParamChange(id, pName, e.target.value, 'number')}
                                                    />
                                                    {pConfig.unit && (
                                                        <span className={styles.paramUnit}>{pConfig.unit}</span>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>

                                <div className={styles.cardFooter}>
                                    <p className={styles.theoryNote}>{inst.theory}</p>
                                    <button
                                        className={styles.activateBtn}
                                        onClick={() => activateInstrument(id)}
                                        disabled={!!activating}
                                        style={{ '--btn-color': tc }}
                                    >
                                        {activating === id ? '⏳ Activating…' : '⚡ Activate Instrument'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </section>
    );
}
