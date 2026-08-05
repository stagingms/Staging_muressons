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

export default function RegulatorySandboxControl({ sessionId, isGodMode = false }) {
    const [instruments, setInstruments]   = useState({});
    const [customParams, setCustomParams] = useState({});
    const [loading, setLoading]           = useState(true);
    const [activating, setActivating]     = useState(null);
    const [actionStatus, setActionStatus] = useState('');
    const [statusType, setStatusType]     = useState('info');
    const [complexityIndex, setComplexityIndex] = useState(0);
    const [captureRisk, setCaptureRisk]   = useState(0);
    const [activeCount, setActiveCount]   = useState(0);
    const [exoEvents, setExoEvents]       = useState([]);
    const [triggeringEvent, setTriggeringEvent] = useState(null);

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

    const fetchExoEvents = useCallback(() => {
        if (!sessionId) return;
        fetch(`${API}/api/simulations/${sessionId}/regulatory-sandbox/exogenous-events`)
            .then(res => res.ok ? res.json() : null)
            .then(data => { if (data?.exogenous_events) setExoEvents(data.exogenous_events); })
            .catch(() => {});
    }, [sessionId]);

    useEffect(() => { fetchInstruments(); fetchExoEvents(); }, [fetchInstruments, fetchExoEvents]);

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
            fetchExoEvents();
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
                    <p>{isGodMode ? 'Select a cohort from the Target Cohort dropdown above to configure its regulatory environment.' : 'Select a session from the Leaderboard to configure its regulatory environment.'}</p>
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

            {/* ── Exogenous Crisis Events ── */}
            {exoEvents.length > 0 && (
                <div className={styles.exoSection}>
                    <div className={styles.exoHeader}>
                        <span className={styles.exoIcon}>💥</span>
                        <div>
                            <h3 className={styles.exoTitle}>Exogenous Crisis Events</h3>
                            <p className={styles.exoSubtitle}>Force-trigger policy shocks (R7–R9). Bypasses natural trigger conditions.</p>
                        </div>
                    </div>
                    <div className={styles.exoGrid}>
                        {exoEvents.map(evt => {
                            const fired = !!evt.already_fired;
                            const severityColor = evt.severity === 'critical' ? '#ef4444' : '#f59e0b';
                            return (
                                <div key={evt.event_id} className={`${styles.exoCard} ${fired ? styles.exoFired : ''}`}>
                                    <div className={styles.exoCardHeader}>
                                        <span className={styles.exoCardIcon}>{evt.icon}</span>
                                        <div style={{ flex: 1 }}>
                                            <h4 className={styles.exoCardName}>{evt.name}</h4>
                                            <p className={styles.exoCardDesc}>{evt.description}</p>
                                        </div>
                                        <span className={styles.exoSeverity} style={{ color: severityColor, borderColor: `${severityColor}40`, background: `${severityColor}12` }}>
                                            {evt.severity}
                                        </span>
                                    </div>
                                    <div className={styles.exoMeta}>
                                        <span>Rounds: {evt.trigger_rounds.join(', ')}</span>
                                        <span>•</span>
                                        <span style={{ fontSize: 'var(--type-caption)', fontStyle: 'italic', color: '#64748b' }}>{(evt.theory || '').split('—')[0].trim()}</span>
                                    </div>
                                    <div className={styles.exoEffects}>
                                        {Object.entries(evt.effects || {}).map(([k, v]) => (
                                            <span key={k} className={styles.exoEffectPill}>
                                                {k.replace(/_/g, ' ')}: {typeof v === 'number' ? (v >= 1000000 ? `$${(v/1e6).toFixed(0)}M` : v > 0 ? `+${v}` : v) : String(v)}
                                            </span>
                                        ))}
                                    </div>
                                    <button
                                        className={styles.exoTriggerBtn}
                                        disabled={fired || !!triggeringEvent}
                                        onClick={async () => {
                                            if (!confirm(`⚠️ FORCE TRIGGER: "${evt.name}"?\n\nThis will immediately apply all effects to the session. This action cannot be undone.`)) return;
                                            setTriggeringEvent(evt.event_id);
                                            setActionStatus(`Triggering ${evt.name}...`);
                                            setStatusType('info');
                                            try {
                                                const res = await fetch(`${API}/api/simulations/${sessionId}/regulatory-sandbox/trigger-event`, {
                                                    method: 'POST',
                                                    headers: { 'Content-Type': 'application/json' },
                                                    body: JSON.stringify({ event_id: evt.event_id }),
                                                });
                                                if (res.ok) {
                                                    const data = await res.json();
                                                    setActionStatus(`${evt.icon} ${evt.name} triggered successfully`);
                                                    setStatusType('success');
                                                    fetchExoEvents();
                                                } else {
                                                    const err = await res.json().catch(() => ({}));
                                                    setActionStatus(`Failed: ${err.detail || 'Trigger error'}`);
                                                    setStatusType('error');
                                                }
                                            } catch {
                                                setActionStatus('Network error');
                                                setStatusType('error');
                                            } finally {
                                                setTriggeringEvent(null);
                                                setTimeout(() => setActionStatus(''), 7000);
                                            }
                                        }}
                                    >
                                        {fired ? `✓ Fired in R${evt.already_fired}` : triggeringEvent === evt.event_id ? '⏳ Triggering…' : `${evt.icon} Force Trigger`}
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </section>
    );
}
