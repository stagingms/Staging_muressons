'use client';

import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import styles from './InvestmentMatrix.module.css';
import { Abbr } from './Glossary';
import { useCurrency } from '../contexts/CurrencyContext';

/* ── SVG Icon Components ──────────────────────────────────── */
const SvgPharma = () => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><rect x="7" y="3" width="10" height="18" rx="5"/><line x1="7" y1="12" x2="17" y2="12"/></svg>);
const SvgElectronics = () => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><rect x="6" y="6" width="12" height="12" rx="2"/><line x1="9" y1="6" x2="9" y2="3"/><line x1="15" y1="6" x2="15" y2="3"/><line x1="9" y1="18" x2="9" y2="21"/><line x1="15" y1="18" x2="15" y2="21"/><line x1="6" y1="9" x2="3" y2="9"/><line x1="6" y1="15" x2="3" y2="15"/><line x1="18" y1="9" x2="21" y2="9"/><line x1="18" y1="15" x2="21" y2="15"/></svg>);
const SvgConsumer = () => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M6 7h12l1.5 14H4.5L6 7z"/><path d="M9 7V5a3 3 0 0 1 6 0v2"/></svg>);
const SvgSoftware = () => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="8,4 3,12 8,20"/><polyline points="16,4 21,12 16,20"/><line x1="14" y1="4" x2="10" y2="20"/></svg>);
const SvgHospital = () => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><rect x="4" y="4" width="16" height="16" rx="2"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>);
const SvgClinic = () => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><circle cx="12" cy="10" r="4"/><path d="M8 18c0-2.2 1.8-4 4-4s4 1.8 4 4"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="10" y1="10" x2="14" y2="10"/></svg>);
const SvgSpecCare = () => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><circle cx="12" cy="9" r="3"/><line x1="12" y1="12" x2="12" y2="21"/><line x1="9" y1="6" x2="7" y2="3"/><line x1="15" y1="6" x2="17" y2="3"/></svg>);
const SvgTelehealth = () => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><rect x="5" y="3" width="14" height="18" rx="2"/><polyline points="9,13 11,11 13,15 15,12"/></svg>);

const BU_META = {
    pharma: { label: 'Pharma', Icon: SvgPharma, accent: 'var(--bu-pharma)' },
    electronics: { label: 'Electronics', Icon: SvgElectronics, accent: 'var(--bu-electronics)' },
    consumer_goods: { label: 'Consumer Goods', Icon: SvgConsumer, accent: 'var(--bu-consumer)' },
    software: { label: 'Software', Icon: SvgSoftware, accent: 'var(--bu-software)' },
    hospitals: { label: 'Hospitals', Icon: SvgHospital, accent: 'var(--bu-hospital)' },
    clinics: { label: 'Primary Care Clinics', Icon: SvgClinic, accent: 'var(--bu-clinics)' },
    specialised_care: { label: 'Specialised Care', Icon: SvgSpecCare, accent: 'var(--bu-specialised)' },
    telehealth: { label: 'Digital Health', Icon: SvgTelehealth, accent: 'var(--bu-telehealth)' },
};

/* ── Animated Number (odometer effect) ────────────────────── */
function AnimatedNumber({ value, decimals = 1, prefix = '', suffix = '' }) {
    const [display, setDisplay] = useState(value);
    const prev = useRef(value);
    const raf = useRef(null);
    useEffect(() => {
        const start = prev.current, diff = value - start;
        if (Math.abs(diff) < 0.001) { setDisplay(value); prev.current = value; return; }
        const t0 = performance.now();
        const run = (now) => {
            const p = Math.min((now - t0) / 400, 1);
            const e = 1 - Math.pow(1 - p, 3);
            setDisplay(start + diff * e);
            if (p < 1) raf.current = requestAnimationFrame(run);
            else { setDisplay(value); prev.current = value; }
        };
        raf.current = requestAnimationFrame(run);
        return () => { if (raf.current) cancelAnimationFrame(raf.current); };
    }, [value]);
    return <>{prefix}{(display / 1_000_000).toFixed(decimals)}{suffix}</>;
}

/* ── Pool Donut Gauge ─────────────────────────────────────── */
function PoolDonut({ pctUsed }) {
    const size = 60, sw = 6, r = (size - sw) / 2, circ = 2 * Math.PI * r;
    const fill = Math.min(pctUsed, 120);
    const offset = circ * (1 - fill / 120);
    const color = pctUsed > 100 ? 'var(--danger)' : pctUsed > 80 ? 'var(--caution)' : '#00e5c3';
    return (
        <div className={styles.donutWrap}>
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
                <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(20,27,45,0.8)" strokeWidth={sw}/>
                <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={sw}
                    strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
                    transform={`rotate(-90 ${size/2} ${size/2})`}
                    style={{ transition: 'stroke-dashoffset 0.6s ease, stroke 0.4s ease' }}/>
            </svg>
            <span className={styles.donutLabel}>{Math.round(pctUsed)}%</span>
        </div>
    );
}

/* ── BU Health Calculator ─────────────────────────────────── */
function getSliderColor(pct, accent) {
    if (pct > 100) return 'var(--danger)';
    if (pct > 80) return 'var(--caution)';
    if (pct > 50) return 'var(--caution-deep)';
    return accent;
}

/* ── Sort options ─────────────────────────────────────────── */
const SORT_OPTIONS = [
    { key: 'default', label: 'Default' },
    { key: 'revenue', label: 'Revenue' },
    { key: 'margin', label: 'Margin' },
    { key: 'risk', label: 'Risk' },
];

/**
 * InvestmentMatrix — Centre console with 4 mutually exclusive sliders.
 * Allocations deduct from the Corporate Strategic Fund (CSF) pool.
 *
 * Props:
 *  - csfPool:       total available funds (CSF from global treasury)
 *  - businessUnits: array of BU objects
 *  - allocations:   { [bu_id]: number } controlled externally
 *  - onAllocationsChange: (newAllocations) => void
 */
export default function InvestmentMatrix({
    csfPool = 0,
    globalState = {},
    businessUnits = [],
    allocations = {},
    onAllocationsChange,
    historyData = [],
    decisionParadigm = 'legacy_abc',
    /* CHROME. The capital stage now states the fund and what is left of it in
       its own stage head, at display size, above this component. With chrome
       off, the pool header (donut, CSF Pool, Allocated, Remaining), the pool
       bar and the sort row are suppressed so the same three numbers are not
       announced twice on one screen. The rows, the slider behaviour, the 120%
       ceiling and every warning stay exactly as they are.

       Default TRUE so the dashboard path and any other caller are untouched. */
    chrome = true,
}) {
    const { currency } = useCurrency();
    const sym = currency?.symbol || '$';
    const [csrdIssues, setCsrdIssues] = useState([]);
    const [sortBy, setSortBy] = useState('default');
    const [draggingBu, setDraggingBu] = useState(null);
    const [shakeId, setShakeId] = useState(null);

    // Fetch materiality issues so we can display funded ones
    useEffect(() => {
        const fetchIssues = async () => {
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/materiality-config`);
                if (res.ok) {
                    const data = await res.json();
                    setCsrdIssues(data.issues || []);
                }
            } catch {
                // Silently degrade — materiality config is optional enhancement data
            }
        };
        fetchIssues();
    }, []);

    const fundedIssueIds = globalState?.materiality_budget_allocated || [];
    const fundedIssues = csrdIssues.filter(i => fundedIssueIds.includes(i.id));

    const totalAllocated = useMemo(
        () => Object.values(allocations).reduce((s, v) => s + v, 0),
        [allocations]
    );

    const remaining = useMemo(
        () => Math.max(0, csfPool - totalAllocated),
        [csfPool, totalAllocated]
    );

    const handleSlider = useCallback(
        (buId, rawValue) => {
            const value = parseFloat(rawValue);
            const otherTotal = totalAllocated - (allocations[buId] || 0);

            // Cap total allocation at 120% of CSF pool (allows 20% over-allocation via loan).
            const maxTotal = csfPool * 1.20;
            const maxAvailable = maxTotal - otherTotal;

            const clamped = Math.min(value, Math.max(0, maxAvailable));

            // Trigger shake if over-allocation attempted
            if (value > clamped + 50000) {
                setShakeId(buId);
                setTimeout(() => setShakeId(null), 500);
            }

            onAllocationsChange?.({
                ...allocations,
                [buId]: Math.round(clamped * 100) / 100,
            });
        },
        [allocations, totalAllocated, csfPool, onAllocationsChange]
    );

    const pctUsed = csfPool > 0 ? ((totalAllocated / csfPool) * 100) : 0;
    const poolWarmth = csfPool > 0 ? Math.max(0, 1 - remaining / csfPool) : 0;

    // Sorted BU list
    const sortedUnits = useMemo(() => {
        const arr = [...businessUnits];
        if (sortBy === 'revenue') arr.sort((a, b) => b.revenue_base - a.revenue_base);
        else if (sortBy === 'margin') arr.sort((a, b) => {
            const mA = a.revenue_base > 0 ? (a.revenue_base - a.opex_base) / a.revenue_base : 0;
            const mB = b.revenue_base > 0 ? (b.revenue_base - b.opex_base) / b.revenue_base : 0;
            return mB - mA;
        });
        else if (sortBy === 'risk') arr.sort((a, b) => (b.governance_risk_score || 0) - (a.governance_risk_score || 0));
        return arr;
    }, [businessUnits, sortBy]);

    // NEW-05: Native input listener map so programmatic slider changes update counters
    // React's synthetic onChange won't fire when external JS calls:
    //   slider.value = X; slider.dispatchEvent(new Event('input', { bubbles: true }));
    // The native listener below bridges that gap.
    const sliderRefs = useRef({});

    useEffect(() => {
        const handlers = {};
        businessUnits.forEach(bu => {
            const el = sliderRefs.current[bu.bu_id];
            if (!el) return;
            const handler = (e) => {
                // Only handle programmatic dispatches — real user events are
                // already handled by React's onChange to avoid double-firing
                // which causes stale-closure overwrites of other BU allocations.
                if (e.isTrusted) return;
                handleSlider(bu.bu_id, e.target.value);
            };
            handlers[bu.bu_id] = handler;
            el.addEventListener('input', handler);
        });
        return () => {
            businessUnits.forEach(bu => {
                const el = sliderRefs.current[bu.bu_id];
                if (el && handlers[bu.bu_id]) {
                    el.removeEventListener('input', handlers[bu.bu_id]);
                }
            });
        };
    }, [businessUnits, handleSlider]);

    return (
        <section className={`${styles.matrix} ${chrome ? '' : styles.matrixBare}`}>
            {/* Pool summary */}
            {chrome && (
            <div className={styles.poolHeader} style={{ '--pool-warmth': poolWarmth }}>
                <div className={styles.poolTitleRow}>
                    <div className={styles.poolTitle}>
                        <span className={styles.poolIcon}>🏦</span>
                        <h2>Investment Matrix</h2>
                    </div>
                </div>
                <div className={styles.poolBody}>
                    <PoolDonut pctUsed={pctUsed} />
                    <div className={styles.poolStats}>
                        <div className={styles.statBlock}>
                            <span className={styles.statLabel}><Abbr term="CSF">CSF Pool</Abbr></span>
                            <span className={styles.statValue}>
                                <AnimatedNumber value={csfPool} prefix={sym} suffix="M" />
                            </span>
                        </div>
                        <div className={styles.statBlock}>
                            <span className={styles.statLabel}>Allocated</span>
                            <span className={`${styles.statValue} ${styles.allocated}`}>
                                <AnimatedNumber value={totalAllocated} prefix={sym} suffix="M" />
                            </span>
                        </div>
                        {/* CA-B: REMAINING is the constraint the whole stage is
                            about — make it the hero, colour it as it drains and
                            turns negative (over-allocated). Pool math unchanged. */}
                        <div className={`${styles.statBlock} ${styles.statBlockHero}`}>
                            <span className={styles.statLabel}>Remaining</span>
                            <span className={`${styles.statValue} ${styles.remainingHero} ${remaining < 0 ? styles.over : remaining < csfPool * 0.1 ? styles.low : ''}`}>
                                <AnimatedNumber value={remaining} prefix={sym} suffix="M" />
                            </span>
                        </div>
                    </div>
                </div>

                {/* CA-B: pool-spent bar — the budget tension in one glance.
                    Fill = allocated/pool; colour shifts calm→amber→red and shows
                    an explicit over-allocation state (same thresholds as the
                    slider fill). Presentation only — reads pctUsed/remaining. */}
                <div className={styles.poolSpentTrack} aria-hidden="true">
                    <div
                        className={`${styles.poolSpentFill} ${pctUsed > 100 ? styles.poolSpentOver : pctUsed > 80 ? styles.poolSpentWarn : ''}`}
                        style={{ width: `${Math.min(100, pctUsed)}%` }}
                    />
                </div>

                {/* Warning for Over-allocation or Negative Treasury (Loan Required) */}
                {(totalAllocated > csfPool || (globalState?.corporate_treasury ?? 0) < 0) && (
                    <div className={styles.loanWarning}>
                        <span className={styles.loanIcon}>⚠️</span>
                        <span>
                            {(globalState?.corporate_treasury ?? 0) < 0
                                ? <>Emergency Credit Line: <span className={styles.loanAmount}>{sym}{(Math.abs(globalState?.corporate_treasury ?? 0) / 1_000_000).toFixed(2)}M</span> in debt</>
                                : <>Loan Required: <span className={styles.loanAmount}>{sym}{((totalAllocated - csfPool) / 1_000_000).toFixed(2)}M</span></>
                            }
                            <span style={{ color: "var(--text-muted)", marginLeft: "0.5rem" }}>
                                at {(globalState?.active_event_flags?.loan_interest_rate * 100 || 12).toFixed(1)}% interest per round
                            </span>
                        </span>
                    </div>
                )}
                {/* Emergency credit line (FIN-05, Wave 3): a real facility. Drawn
                    automatically ($1M into cash) when treasury × 20% falls below
                    $1M — the same trigger the server derives — interest on the
                    outstanding balance at prevailing + 2%, repaid once the
                    treasury recovers or at round 10. Outstanding → say so. */}
                {globalState?.corporate_treasury != null
                  && ((globalState.corporate_treasury * 0.20 < 1_000_000) || (globalState?.active_event_flags?.emergency_credit_balance > 0)) && (
                    <div className={styles.loanWarning} style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.06)' }} data-testid="emergency-credit-banner">
                        <span className={styles.loanIcon}>🚨</span>
                        <span style={{ fontSize: 'var(--type-caption)' }}>
                            {globalState?.active_event_flags?.emergency_credit_balance > 0 ? (
                                <>Emergency credit line <strong>drawn</strong>: <strong>{sym}{(globalState.active_event_flags.emergency_credit_balance / 1_000_000).toFixed(1)}M</strong> outstanding at{' '}</>
                            ) : (
                                <>Emergency Credit Facility: <strong>{sym}1.0M</strong> will be drawn this round at{' '}</>
                            )}
                            <span className={styles.loanAmount}>
                                {((globalState?.active_event_flags?.loan_interest_rate || 0.12) * 100 + 2).toFixed(1)}%
                            </span>{' '}
                            <span style={{ color: "var(--text-muted)" }}>
                                (prevailing rate + 2%; repaid automatically once treasury clears {sym}5M, or at round 10)
                            </span>
                        </span>
                    </div>
                )}
                {/* MB-01: Green Fund coverage indicator for Advanced Climate */}
                {decisionParadigm === 'advanced_climate' && (globalState?.green_transition_fund || 0) > 0 && (
                    <div style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        padding: '4px 0', fontSize: 'var(--type-caption)',
                    }}>
                        <span style={{ color: 'var(--positive-text)', display: 'flex', alignItems: 'center', gap: 4 }}>
                            🌱 Green Fund Coverage
                        </span>
                        <span style={{ color: 'var(--positive-text)', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
                            up to {sym}{((globalState?.green_transition_fund || 0) / 1_000_000).toFixed(1)}M available
                        </span>
                    </div>
                )}
            </div>

            )}

            {/* Sort toggle — hidden in the single-BU (single-SBU) simulation:
                there is nothing to sort with one unit. */}
            {chrome && (businessUnits?.length || 0) > 1 && (
                <div className={styles.sortBar}>
                    <span className={styles.sortLabel}>Sort:</span>
                    {SORT_OPTIONS.map(opt => (
                        <button key={opt.key}
                            className={`${styles.sortBtn} ${sortBy === opt.key ? styles.sortBtnActive : ''}`}
                            onClick={() => setSortBy(opt.key)}>{opt.label}</button>
                    ))}
                </div>
            )}

            {/* BU Sliders */}
            <div className={`${styles.sliders} ${sortedUnits.length === 1 ? styles.slidersSingle : ''}`}>
                {sortedUnits.map((bu, i) => {
                    const meta = BU_META[bu.bu_id] || { label: bu.bu_id, Icon: () => <span>📊</span>, accent: '#6366f1' };
                    const alloc = allocations[bu.bu_id] || 0;
                    const sliderMax = csfPool * 1.20;
                    const pct = csfPool > 0 ? (alloc / csfPool) * 100 : 0;
                    const thumbPct = sliderMax > 0 ? (alloc / sliderMax) * 100 : 0;
                    const sliderColor = getSliderColor(pct, meta.accent);
                    const isDimmed = remaining <= 0 && alloc === 0;
                    const isDragging = draggingBu === bu.bu_id;
                    const isShaking = shakeId === bu.bu_id;

                    // Metric helpers
                    const margin = bu.revenue_base > 0 ? (bu.revenue_base - bu.opex_base) / bu.revenue_base * 100 : 0;
                    const slo = bu.social_license_score || 0;



                    // Find issues that target this BU
                    const buFundedIssues = fundedIssues.filter(issue =>
                        issue.affected_bu_1 === bu.bu_id || issue.affected_bu_2 === bu.bu_id
                    );

                    const cardClasses = [
                        styles.sliderCard,
                        isDimmed ? styles.sliderCardDimmed : '',
                        isDragging ? styles.sliderCardDragging : '',
                        isShaking ? styles.sliderCardShake : '',
                    ].filter(Boolean).join(' ');

                    return (
                        <div key={bu.bu_id} className={cardClasses}
                            style={{ '--bu-accent': meta.accent, animationDelay: `${i * 100}ms` }}>

                            {/* Header — five things, and the owner named all five:
                                name, revenue and margin, social licence, the
                                slider, the amount.

                                WHAT LEFT, so it is on the record rather than in a
                                diff: the BU glyph (decoration — the name is the
                                identifier), the health verdict chip, the thesis
                                line ("fund here because…"), and the revenue
                                sparkline. Governance risk and natural-capital
                                debt left with the metrics drawer. All of those
                                still exist elsewhere: the comparison matrix on
                                the decision stage carries gov risk and natural
                                capital per OPTION, and the round retrospect
                                carries the engine's own account. What is gone
                                from THIS screen is the per-BU derivation of
                                them. If the thesis line is missed, it is the one
                                worth arguing back for — it was the only sentence
                                on the stage that said why a unit deserved money.

                                Social licence earns its place: it is the metric
                                the funding decision most directly moves, and it
                                gates the green premium. It reads as a score with
                                its scale, never a bare number. */}
                            {/* NO THESIS LINE. It was a first-match cascade over
                                margin, social licence and governance risk, in that
                                fixed order, reporting ONE of them. Three problems,
                                and the third is the one that settled it.

                                It was a complaint, not a case for funding: six of
                                its seven outputs named a fault, and only the
                                all-healthy fallback was positive. Its own docblock
                                claimed it said "fund here because" — it never did.

                                It hid worse news than it reported. A unit at margin
                                10, licence 20, governance risk 45 — all three in
                                danger — said only "Thin 10% margin", because margin
                                is tested first. A team funds the margin and never
                                learns about the licence.

                                And once the row above carried all three inputs, it
                                restated a number sitting directly over it on every
                                one of the four business units. "margin 23%" then
                                "Modest 23% margin". It had stopped adding anything.

                                If a sentence returns here it should say what a number
                                cannot — whether capital compounds or plugs a hole —
                                rather than re-reading the row. */}
                            <div className={styles.sliderHeader}>
                                <div className={styles.buInfo}>
                                    <span className={styles.buNameRow}>
                                        <span className={styles.buLabel}>{meta.label}</span>
                                    </span>
                                    <span className={styles.buRevenue} title="Revenue, operating margin, and the social licence this unit holds — the three figures that decide whether capital here compounds">
                                        Rev {sym}{(bu.revenue_base / 1_000_000).toFixed(1)}M
                                        <span aria-hidden="true"> · </span>
                                        margin {margin.toFixed(0)}%
                                        <span aria-hidden="true"> · </span>
                                        social licence {Math.round(slo)}/100
                                    </span>
                                </div>

                                <span className={styles.allocAmount}>
                                    {sym}{(alloc / 1_000_000).toFixed(2)}M
                                </span>
                            </div>

                            {/* Slider with tooltip and tick marks */}
                            <div className={styles.sliderRow} style={{ '--thumb-pos': `${thumbPct}%` }}>
                                <div className={styles.sliderTooltip}>
                                    {sym}{(alloc / 1_000_000).toFixed(2)}M
                                </div>
                                <input type="range" id={`slider-${bu.bu_id}`}
                                    ref={el => { sliderRefs.current[bu.bu_id] = el; }}
                                    min={0} max={sliderMax} step={100_000} value={alloc}
                                    onChange={(e) => handleSlider(bu.bu_id, e.target.value)}
                                    onMouseDown={() => setDraggingBu(bu.bu_id)}
                                    onMouseUp={() => setDraggingBu(null)}
                                    onTouchStart={() => setDraggingBu(bu.bu_id)}
                                    onTouchEnd={() => setDraggingBu(null)}
                                    className={styles.slider}
                                    style={{ '--pct': `${thumbPct}%`, '--accent': meta.accent, '--slider-color': sliderColor }}
                                />
                                {chrome && (
                                <div className={styles.sliderTicks}>
                                    {[0, 25, 50, 75, 100].map(t => (
                                        <span key={t} className={styles.sliderTickLabel}>
                                            <span className={styles.sliderTick} />
                                            {t === 0 ? '0' : t === 100 ? 'Max' : ''}
                                        </span>
                                    ))}
                                </div>
                                )}
                            </div>

                            {/* Footer — how much of the pool this unit is taking.
                                The metrics drawer went with the four gauges it
                                held; see the header note. */}
                            {chrome && (
                            <div className={styles.sliderFooter}>
                                <span className={styles.footerLabel}>{pct.toFixed(1)}% of pool</span>
                            </div>
                            )}

                            {/* Render Funded Mitigations for this BU */}
                            {buFundedIssues.length > 0 && (
                                <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'var(--bg-elevated)', borderTop: `2px solid ${meta.accent}`, borderRadius: '0.375rem' }}>
                                    <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                        🎯 Funded ESG Mitigations
                                    </div>
                                    <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                        {buFundedIssues.map(issue => {
                                            const sandboxConfig = globalState?.materiality_dictionary_override;
                                            const sandboxIssue = sandboxConfig?.issues?.find(i => i.id === issue.id);
                                            const displayCost = sandboxIssue ? sandboxIssue.mitigation_cost_usd : issue.mitigation_cost_usd;
                                            return (
                                                <li key={issue.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                                                    <span style={{ color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '140px' }} title={issue.title}>
                                                        • {issue.title}
                                                    </span>
                                                    <span style={{ color: 'var(--accent-green, var(--kpi-good))', fontWeight: 'bold' }}>
                                                        {sym}{(displayCost / 1_000_000).toFixed(1)}M
                                                    </span>
                                                </li>
                                            );
                                        })}
                                    </ul>
                                </div>
                            )}

                        </div>
                    );
                })}
            </div>
        </section>
    );
}
