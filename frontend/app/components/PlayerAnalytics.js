'use client';
import { useState, useEffect, useMemo } from 'react';
import styles from './PlayerAnalytics.module.css';
import { playerIdHeader } from '../hooks/useSimulation';
import { currencySymbol, atRate } from '../utils/format';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const TABS = [
    { id: 'benchmarking', label: '🏆 Peer Benchmarking', key: 'peer_benchmarking', title: 'Shows your anonymous percentile ranking vs. the cohort for Treasury, Reputation, and Synergy. Includes bar visualizations with your value compared against the cohort average. Answers: "How do I rank among my peers?"' },
    { id: 'impact', label: '🧠 Decision Impact', key: 'decision_impact', title: 'Per-round KPI attribution — shows how each of your choices affected Treasury, Reputation, and Synergy with colour-coded delta badges (+/-) and a narrative explanation of the outcome. Answers: "What impact did my decisions actually have?"' },
    { id: 'whatif', label: '📈 What-If', key: 'what_if_simulator', title: 'Counterfactual analysis — shows what would have happened if you had chosen the most popular alternative option. Displays projected Treasury and Reputation diffs. Only appears when your choices differ from the majority. Disabled by default.' },
];

export default function PlayerAnalytics({ sessionId, isOpen, onClose }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState('benchmarking');

    useEffect(() => {
        if (!isOpen || !sessionId) return;
        setLoading(true);
        // X-Player-Id: the endpoint is now SEC-3-guarded (owned sessions admit
        // only their owner; facilitators always pass).
        fetch(`${API}/api/admin/analytics/player/${sessionId}`, { headers: playerIdHeader(), credentials: 'include' })
            .then(r => r.ok ? r.json() : null)
            .then(d => { setData(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, [isOpen, sessionId]);

    const visibleTabs = useMemo(() => {
        if (!data?.visibility) return TABS;
        return TABS.filter(t => data.visibility[t.key] !== false);
    }, [data]);

    // Keep the OPEN tab one the cohort actually permits.
    //
    // This was a VISIBILITY LEAK, not merely an empty pane: `tab` initialises to
    // 'benchmarking' and was never reconciled with visibleTabs, so a cohort with
    // Peer Benchmarking switched off still rendered <PeerBenchmarking> in the
    // body — the tab bar hid the tab while the panel underneath kept drawing
    // peer data. The rail carries the same guard for the same reason.
    useEffect(() => {
        if (!visibleTabs.length) return;
        if (!visibleTabs.some(t => t.id === tab)) setTab(visibleTabs[0].id);
    }, [visibleTabs, tab]);

    const shown = (id) => tab === id && visibleTabs.some(t => t.id === id);

    if (!isOpen) return null;

    return (
        <div className={styles.overlay} onClick={onClose}>
            <div className={styles.modal} onClick={e => e.stopPropagation()}>
                <div className={styles.header}>
                    <span className={styles.icon}>📊</span>
                    <h2>My Analytics</h2>
                    <button className={styles.closeBtn} onClick={onClose}>✕</button>
                </div>

                {loading ? (
                    <div className={styles.loading}>Loading your analytics…</div>
                ) : !data ? (
                    <div className={styles.loading}>Analytics unavailable. Play more rounds to generate data.</div>
                ) : !visibleTabs.length ? (
                    // Every tab switched off for this cohort. Say so plainly
                    // rather than presenting an empty chrome the player will
                    // read as a broken screen.
                    <div className={styles.loading}>
                        Your facilitator has turned personal analytics off for this cohort.
                    </div>
                ) : (
                    <>
                        <div className={styles.tabBar}>
                            {visibleTabs.map(t => (
                                <button key={t.id}
                                    className={`${styles.tab} ${tab === t.id ? styles.tabActive : ''}`}
                                    onClick={() => setTab(t.id)}
                                    data-tooltip={t.title}
                                    data-tooltip-pos="below">
                                    {t.label}
                                </button>
                            ))}
                        </div>
                        <div className={styles.body}>
                            {/* Guarded on visibleTabs, not just on `tab`: the
                                reconciling effect runs AFTER render, so the first
                                paint following a settings change would otherwise
                                still draw the hidden panel for one frame. */}
                            {shown('benchmarking') && <PeerBenchmarking data={data.peer_benchmarking} />}
                            {shown('impact') && <DecisionImpact data={data.decision_impact} />}
                            {shown('whatif') && <WhatIfSimulator data={data.what_if} />}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   PEER BENCHMARKING
   ═══════════════════════════════════════ */
function PeerBenchmarking({ data }) {
    if (!data) return <Empty />;

    const metrics = [
        {
            label: 'Treasury', percentile: data.treasury_percentile,
            value: `${currencySymbol()}${atRate(data.player?.treasury / 1_000_000).toFixed(1)}M`,
            avg: `${currencySymbol()}${atRate(data.cohort_avg?.treasury / 1_000_000).toFixed(1)}M`,
            color: '#3b82f6'
        },
        {
            label: 'Reputation', percentile: data.reputation_percentile,
            value: data.player?.reputation?.toFixed(1),
            avg: data.cohort_avg?.reputation?.toFixed(1),
            color: '#10b981'
        },
        {
            label: 'Synergy', percentile: data.synergy_percentile,
            value: `${data.player?.synergy?.toFixed(2)}×`,
            avg: '—',
            color: '#8b5cf6'
        },
    ];

    return (
        <div className={styles.section}>
            <p className={styles.sectionDesc}>
                {/* SEAM-12 (Wave 3): the peer set is this cohort's teams — say so, and say when there are none */}
                {data.peer_scope === 'solo' || (data.player_count || 0) <= 1
                    ? 'Solo session — no cohort peers at this round; percentiles are against yourself.'
                    : `Your percentile ranking vs the ${data.player_count} teams in your cohort at the same round`}
            </p>
            <div className={styles.benchGrid}>
                {metrics.map(m => (
                    <div key={m.label} className={styles.benchCard}>
                        <div className={styles.benchHeader}>
                            <span className={styles.benchLabel}>{m.label}</span>
                            <span className={styles.benchPct} style={{ color: m.color }}>
                                {m.percentile}th
                            </span>
                        </div>
                        <div className={styles.benchBar}>
                            <div className={styles.benchFill} style={{
                                width: `${m.percentile}%`,
                                background: m.color,
                            }} />
                            <div className={styles.benchMarker} style={{ left: `${m.percentile}%` }} />
                        </div>
                        <div className={styles.benchStats}>
                            <span>You: <strong>{m.value}</strong></span>
                            <span>Avg: <strong>{m.avg}</strong></span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   DECISION IMPACT ATTRIBUTION
   ═══════════════════════════════════════ */
function DecisionImpact({ data }) {
    if (!data || !data.length) return <Empty msg="No decisions tracked yet" />;

    return (
        <div className={styles.section}>
            <p className={styles.sectionDesc}>
                How each round's decisions affected your KPIs
            </p>
            <div className={styles.impactList}>
                {data.map(d => (
                    <div key={d.round} className={styles.impactCard}>
                        <div className={styles.impactHeader}>
                            <span className={styles.impactRound}>Year {d.round}</span>
                            <span className={styles.impactChoice}>
                                {d.choice?.replace('option_', 'Option ').toUpperCase()}
                            </span>
                        </div>
                        <div className={styles.impactDeltas}>
                            <DeltaBadge label="Treasury" value={d.treasury_delta} isCurrency />
                            <DeltaBadge label="Reputation" value={d.reputation_delta} />
                            <DeltaBadge label="Synergy" value={d.synergy_delta} precision={3} />
                        </div>
                        <p className={styles.impactNarrative}>{d.narrative}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}

function DeltaBadge({ label, value, isCurrency = false, precision = 1 }) {
    const positive = value > 0;
    const formatted = isCurrency
        ? `${positive ? '+' : ''}${currencySymbol()}${atRate(Math.abs(value) / 1_000_000).toFixed(precision)}M`
        : `${positive ? '+' : ''}${value?.toFixed(precision)}`;

    return (
        <div className={`${styles.delta} ${positive ? styles.deltaPos : value < 0 ? styles.deltaNeg : styles.deltaNeutral}`}>
            <span className={styles.deltaLabel}>{label}</span>
            <span className={styles.deltaVal}>{formatted}</span>
        </div>
    );
}


/* ═══════════════════════════════════════
   WHAT-IF SIMULATOR
   ═══════════════════════════════════════ */
function WhatIfSimulator({ data }) {
    if (!data || !data.length) {
        return (
            <div className={styles.section}>
                <p className={styles.sectionDesc}>
                    No counterfactual data available yet. This shows up when your choices differ from the majority.
                </p>
                <Empty msg="Make some choices that differ from the crowd" />
            </div>
        );
    }

    return (
        <div className={styles.section}>
            <p className={styles.sectionDesc}>
                What would have happened if you chose the most popular alternative?
            </p>
            <div className={styles.whatIfList}>
                {data.map(d => (
                    <div key={d.round} className={styles.whatIfCard}>
                        <div className={styles.whatIfHeader}>
                            <span className={styles.whatIfRound}>Year {d.round}</span>
                            <div className={styles.whatIfChoices}>
                                <span className={styles.whatIfYou}>
                                    You: {d.actual_choice?.replace('option_', '').toUpperCase()}
                                </span>
                                <span className={styles.whatIfArrow}>→</span>
                                <span className={styles.whatIfAlt}>
                                    Popular: {d.alternative?.replace('option_', '').toUpperCase()}
                                    <small> ({d.alternative_popularity})</small>
                                </span>
                            </div>
                        </div>
                        <div className={styles.whatIfDeltas}>
                            <div className={`${styles.whatIfDelta} ${d.projected_treasury_diff > 0 ? styles.deltaPos : styles.deltaNeg}`}>
                                <span>💰 Treasury</span>
                                <strong>{d.projected_treasury_diff > 0 ? '+' : ''}{currencySymbol()}{atRate(d.projected_treasury_diff / 1_000_000).toFixed(1)}M</strong>
                            </div>
                            <div className={`${styles.whatIfDelta} ${d.projected_reputation_diff > 0 ? styles.deltaPos : styles.deltaNeg}`}>
                                <span>⭐ Reputation</span>
                                <strong>{d.projected_reputation_diff > 0 ? '+' : ''}{d.projected_reputation_diff?.toFixed(1)}</strong>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}


function Empty({ msg = 'No data available yet' }) {
    return (
        <div className={styles.empty}>
            <span>📭</span>
            <p>{msg}</p>
        </div>
    );
}
