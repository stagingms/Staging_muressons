'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import styles from './SimulationSwitchboard.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/* ─── Static timeline data ──────────────────────────────────── */
const STD_MODULES = [
    { id: 1, label: 'Mod 1', sub: 'Materiality' },
    { id: 2, label: 'Mod 2', sub: 'Double Gate' },
    { id: 3, label: 'Mod 3', sub: 'Scope 3 Basics' },
    { id: 4, label: 'Mod 4', sub: 'ESG Contagion' },
    { id: 5, label: 'Mod 5', sub: 'Physical Risk' },
    { id: 6, label: 'Mod 6', sub: 'AI Ethics' },
    { id: 7, label: 'Mod 7', sub: 'Circular' },
    { id: 8, label: 'Mod 8', sub: 'Water Stress' },
    { id: 9, label: 'Mod 9', sub: 'Just Transition' },
    { id: 10, label: 'Mod 10', sub: 'Linear Profit ✓' },
];

const ADV_MODULES = [
    { id: 4, label: 'Mod 4', sub: 'Reg Shock' },
    { id: 5, label: 'Mod 5', sub: 'VCM Trap' },
    { id: 6, label: 'Mod 6', sub: 'Scope 3 Ultimatum' },
    { id: 7, label: 'Mod 7', sub: 'Insetting' },
    { id: 8, label: 'Mod 8', sub: 'Non-Market Strategy' },
    { id: 9, label: 'Mod 9', sub: 'Capital Markets' },
    { id: 10, label: 'Mod 10', sub: 'Circular Economy ⚡' },
];

/* ─── SVG Timeline ──────────────────────────────────────────── */
function TimelineSVG({ advanced, carbonFee, hostility, scope3 }) {
    const W = 680, H = 310;
    const pad = { x: 48, top: 36, bottom: 28 };

    /* Standard path — horizontal, evenly spaced */
    const stdY = pad.top + 40;
    const totalW = W - pad.x * 2;
    const spacing = totalW / (STD_MODULES.length - 1);
    const stdPoints = STD_MODULES.map((m, i) => ({ x: pad.x + i * spacing, y: stdY, ...m }));
    const branchIdx = 2; // split after index 2 (Mod 3)
    const branchX = stdPoints[branchIdx].x;
    const branchY = stdPoints[branchIdx].y;

    /* Advanced branch — drop down then continue */
    const advY = H - pad.bottom - 60;
    const advSpacing = (W - branchX - pad.x) / (ADV_MODULES.length - 1);
    const advPoints = ADV_MODULES.map((m, i) => ({
        x: branchX + i * advSpacing,
        y: advY,
        ...m,
    }));

    /* Build SVG path strings */
    const stdLinePath = stdPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
    const advCurvePath = `M ${branchX} ${branchY} C ${branchX + 30} ${branchY + 40}, ${advPoints[0].x - 10} ${advY - 20}, ${advPoints[0].x} ${advY}`;
    const advLinePath = advPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

    return (
        <svg
            viewBox={`0 0 ${W} ${H}`}
            className={styles.timelineSvg}
            style={{ display: 'block' }}
        >
            <defs>
                <filter id="neonGlow">
                    <feGaussianBlur stdDeviation="2.5" result="blur" />
                    <feMerge>
                        <feMergeNode in="blur" />
                        <feMergeNode in="SourceGraphic" />
                    </feMerge>
                </filter>
                <filter id="softGlow">
                    <feGaussianBlur stdDeviation="1.5" result="blur" />
                    <feMerge>
                        <feMergeNode in="blur" />
                        <feMergeNode in="SourceGraphic" />
                    </feMerge>
                </filter>
                <linearGradient id="advGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#ff4444" />
                    <stop offset="40%" stopColor="#ff8800" />
                    <stop offset="100%" stopColor="#00ff88" />
                </linearGradient>
                <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L8,3 z" fill="#00ff88" />
                </marker>
                <marker id="arrowRed" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L8,3 z" fill="#ff4444" />
                </marker>
            </defs>

            {/* Background grid */}
            {Array.from({ length: 10 }, (_, i) => (
                <line
                    key={`hg-${i}`}
                    x1={0} y1={i * (H / 9)} x2={W} y2={i * (H / 9)}
                    stroke="rgba(0,255,136,0.04)" strokeWidth="1"
                />
            ))}
            {Array.from({ length: 14 }, (_, i) => (
                <line
                    key={`vg-${i}`}
                    x1={i * (W / 13)} y1={0} x2={i * (W / 13)} y2={H}
                    stroke="rgba(0,255,136,0.04)" strokeWidth="1"
                />
            ))}

            {/* ── STANDARD PATH ── */}
            {/* Faded full standard line */}
            <path
                d={stdLinePath}
                fill="none"
                stroke={advanced ? 'rgba(180,180,180,0.18)' : 'rgba(0,255,136,0.6)'}
                strokeWidth={advanced ? 1.5 : 2.5}
                strokeDasharray={advanced ? '6 4' : 'none'}
                style={{ transition: 'stroke 0.4s, stroke-width 0.4s, opacity 0.4s' }}
                filter={advanced ? undefined : 'url(#softGlow)'}
                markerEnd={advanced ? undefined : 'url(#arrow)'}
            />

            {/* Standard module dots & labels */}
            {stdPoints.map((p, i) => {
                const isBeforeBranch = i <= branchIdx;
                const opacity = advanced ? (isBeforeBranch ? 0.9 : 0.18) : 1;
                const color = advanced ? (isBeforeBranch ? '#00ff88' : '#666') : '#00ff88';
                return (
                    <g key={`std-${p.id}`} style={{ transition: 'opacity 0.4s' }} opacity={opacity}>
                        <circle
                            cx={p.x} cy={p.y} r={isBeforeBranch ? 7 : 5}
                            fill="#000" stroke={color} strokeWidth={isBeforeBranch ? 2 : 1.5}
                            filter={!advanced ? 'url(#softGlow)' : undefined}
                        />
                        {/* Node number */}
                        <text x={p.x} y={p.y + 1} textAnchor="middle" dominantBaseline="middle"
                            fontSize="8" fill={color} fontFamily="monospace" fontWeight="700"
                        >{p.id}</text>
                        {/* Label above */}
                        <text x={p.x} y={p.y - 14} textAnchor="middle"
                            fontSize="10" fill={color} fontFamily="monospace" fontWeight="600"
                            opacity={0.9}
                        >{p.label}</text>
                        {/* Subtitle below */}
                        <text x={p.x} y={p.y + 18} textAnchor="middle"
                            fontSize="8" fill={color} fontFamily="monospace"
                            opacity={0.6}
                        >{p.sub}</text>
                    </g>
                );
            })}

            {/* "STANDARD" label */}
            {!advanced && (
                <text x={W - 6} y={stdY - 14} textAnchor="end"
                    fontSize="9" fill="#00ff88" fontFamily="monospace" opacity="0.5"
                    letterSpacing="2"
                >STANDARD PATH</text>
            )}

            {/* ── ADVANCED BRANCH (only when active) ── */}
            {advanced && (
                <>
                    {/* Branch label */}
                    <text x={branchX - 6} y={(branchY + advY) / 2} textAnchor="end"
                        fontSize="8.5" fill="#ff4444" fontFamily="monospace" opacity="0.7"
                        letterSpacing="1"
                    >BRANCH</text>
                    <text x={branchX - 6} y={(branchY + advY) / 2 + 12} textAnchor="end"
                        fontSize="8.5" fill="#ff4444" fontFamily="monospace" opacity="0.7"
                        letterSpacing="1"
                    >POINT</text>

                    {/* Vertical bifurcation marker */}
                    <line
                        x1={branchX} y1={branchY + 7} x2={branchX} y2={advY - 8}
                        stroke="rgba(255,68,68,0.4)" strokeWidth="1" strokeDasharray="4 3"
                    />

                    {/* Curved transition into advanced path */}
                    <path
                        d={advCurvePath}
                        fill="none"
                        stroke="url(#advGrad)"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        style={{ strokeDasharray: 200, strokeDashoffset: 0, animation: 'drawLine 0.6s ease-out forwards' }}
                        filter="url(#neonGlow)"
                    />

                    {/* Advanced line */}
                    <path
                        d={advLinePath}
                        fill="none"
                        stroke="url(#advGrad)"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        style={{ strokeDasharray: 800, strokeDashoffset: 0, animation: 'drawLine 0.8s ease-out 0.3s both' }}
                        filter="url(#neonGlow)"
                        markerEnd="url(#arrow)"
                    />

                    {/* Advanced module dots & labels */}
                    {advPoints.map((p, i) => {
                        const hue = i < 2 ? '#ff4444' : i < 5 ? '#ff8800' : '#00ff88';
                        return (
                            <g key={`adv-${p.id}`} style={{ animation: `fadeInBranch 0.35s ease-out ${0.3 + i * 0.07}s both` }}>
                                {/* Vertical drop line */}
                                <line
                                    x1={p.x} y1={advY - 26} x2={p.x} y2={advY - 8}
                                    stroke={hue} strokeWidth="1" opacity="0.35"
                                />
                                {/* Node */}
                                <circle cx={p.x} cy={p.y} r={7}
                                    fill="#000" stroke={hue} strokeWidth="2"
                                    filter="url(#neonGlow)"
                                />
                                <text x={p.x} y={p.y + 1} textAnchor="middle" dominantBaseline="middle"
                                    fontSize="8" fill={hue} fontFamily="monospace" fontWeight="800"
                                >{p.id}</text>
                                {/* Label above */}
                                <text x={p.x} y={advY - 30} textAnchor="middle"
                                    fontSize="10" fill={hue} fontFamily="monospace" fontWeight="600"
                                >{p.label}</text>
                                {/* Subtitle below */}
                                <text x={p.x} y={advY + 20} textAnchor="middle"
                                    fontSize="8.5" fill={hue} fontFamily="monospace"
                                    opacity="0.8"
                                >{p.sub}</text>
                            </g>
                        );
                    })}

                    {/* ADVANCED PATH label */}
                    <text x={W - 6} y={advY - 44} textAnchor="end"
                        fontSize="9" fill="#ff4444" fontFamily="monospace"
                        letterSpacing="2"
                        style={{ animation: 'neonPulse 2s ease-in-out infinite' }}
                    >⚡ ADVANCED CLIMATE ENGINE</text>

                    {/* Live readout near bottom of SVG */}
                    <rect x={pad.x} y={H - 22} width={W - pad.x * 2} height={18}
                        fill="rgba(255,68,68,0.06)" stroke="rgba(255,68,68,0.2)" strokeWidth="1"
                    />
                    <text x={pad.x + 8} y={H - 10} fontSize="8.5" fill="#ff8800" fontFamily="monospace">
                        {`CARBON: $${carbonFee}/t  |  HOSTILITY: ${hostility}/10  |  SCOPE3: ${scope3.toFixed(1)} kg CO₂e/unit`}
                    </text>
                </>
            )}
        </svg>
    );
}

/* ─── Main component ────────────────────────────────────────── */
export default function SimulationSwitchboard() {
    const [advanced, setAdvanced] = useState(false);
    const [shaking, setShaking] = useState(false);
    const [carbonFee, setCarbonFee] = useState(40);
    const [hostility, setHostility] = useState(5);
    const [scope3, setScope3] = useState(2.5);
    const [saving, setSaving] = useState(false);
    const [saveMsg, setSaveMsg] = useState('');
    const rootRef = useRef(null);

    /* Trigger glitch on toggle */
    const toggleAdvanced = useCallback(() => {
        setShaking(true);
        setTimeout(() => setShaking(false), 520);
        setAdvanced(v => !v);
    }, []);

    /* Flash save success */
    const flashSave = (msg) => {
        setSaveMsg(msg);
        setTimeout(() => setSaveMsg(''), 3500);
    };

    /* Persist to backend (if connected) */
    const handleApply = async () => {
        setSaving(true);
        try {
            const res = await fetch(`${API}/api/admin/global-settings`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    simulation_mode: advanced ? 'advanced_climate' : 'standard',
                    global_carbon_fee: carbonFee,
                    market_hostility_index: hostility,
                    scope_3_threshold: scope3,
                }),
            });
            if (res.ok) {
                flashSave('✓ SETTINGS APPLIED TO LIVE ENGINE');
            } else {
                flashSave('⚠ Backend returned ' + res.status + ' — settings saved locally');
            }
        } catch {
            flashSave('⚠ Backend offline — settings stored in UI state only');
        } finally {
            setSaving(false);
        }
    };

    /* Terminal output text */
    const terminalContent = advanced
        ? <>
            <span className={styles.terminalWarning}>
                ⚠ WARNING: Advanced Climate Physics ENGAGED.{' '}
            </span>
            <br />
            <span className={styles.terminalText}>
                Executives will now experience hard carbon taxation at{' '}
                <span className={styles.terminalHighlight}>${carbonFee}/tonne</span>,
                a Regulatory &amp; NGO Hostility Index of{' '}
                <span className={styles.terminalHighlight}>{hostility}/10</span>, and
                strict Scope 3 supply chain volatility threshold of{' '}
                <span className={styles.terminalHighlight}>{scope3.toFixed(1)} kg CO₂e/unit</span>.
                {' '}Simulation branches at Module 3.
            </span>
          </>
        : <span className={styles.terminalText}>
            System Status: Nominal. Standard linear P&amp;L operations engaged.
            Timeline: 10-module progression, no advanced physics active.
          </span>;

    return (
        <div
            ref={rootRef}
            className={`${styles.root} ${shaking ? styles.shaking : ''}`}
        >
            {/* ══════════ LEFT PANEL ══════════ */}
            <div className={styles.leftPanel}>
                <div>
                    <div className={styles.sectionLabel}>Master Control</div>

                    <div className={styles.masterBlock}>
                        <div className={styles.masterLabel}>Timeline Branch Engine</div>

                        <button
                            className={advanced ? styles.masterBtnOn : styles.masterBtnOff}
                            onClick={toggleAdvanced}
                        >
                            <span className={advanced ? styles.indicatorOn : styles.indicatorOff} />
                            {advanced ? 'DISENGAGE CLIMATE ENGINE' : 'ENGAGE ADVANCED CLIMATE ENGINE'}
                        </button>

                        <div className={advanced ? styles.statusChipOn : styles.statusChip}>
                            {advanced
                                ? '◉ ADVANCED CLIMATE MODE — LIVE'
                                : '◌ STANDARD MODE — NOMINAL'}
                        </div>
                    </div>
                </div>

                {/* ── Sliding parameters (visible only when advanced) ── */}
                <div className={advanced ? styles.slidersVisible : styles.slidersHidden}>
                    <div className={styles.sectionLabel}>Climate Engine Parameters</div>

                    {/* Carbon Fee */}
                    <div className={styles.sliderRow}>
                        <div className={styles.sliderMeta}>
                            <span className={styles.sliderName}>Internal Carbon Fee</span>
                            <span>
                                <span className={styles.sliderVal}>{carbonFee}</span>
                                <span className={styles.sliderUnit}>$/tonne</span>
                            </span>
                        </div>
                        <input
                            type="range"
                            className={styles.terminalSlider}
                            min={20} max={150} step={1}
                            value={carbonFee}
                            onChange={e => setCarbonFee(Number(e.target.value))}
                        />
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', opacity: 0.4, color: '#00ff88', marginTop: '2px' }}>
                            <span>$20</span><span>$150</span>
                        </div>
                    </div>

                    {/* Hostility */}
                    <div className={styles.sliderRow}>
                        <div className={styles.sliderMeta}>
                            <span className={styles.sliderName}>Reg &amp; NGO Hostility</span>
                            <span>
                                <span className={styles.sliderVal}>{hostility}</span>
                                <span className={styles.sliderUnit}>/10</span>
                            </span>
                        </div>
                        <input
                            type="range"
                            className={styles.terminalSlider}
                            min={1} max={10} step={1}
                            value={hostility}
                            onChange={e => setHostility(Number(e.target.value))}
                        />
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', opacity: 0.4, color: '#00ff88', marginTop: '2px' }}>
                            <span>LOW</span><span>CRITICAL</span>
                        </div>
                    </div>

                    {/* Scope 3 */}
                    <div className={styles.sliderRow}>
                        <div className={styles.sliderMeta}>
                            <span className={styles.sliderName}>Scope 3 Client Threshold</span>
                            <span>
                                <span className={styles.sliderVal}>{scope3.toFixed(1)}</span>
                                <span className={styles.sliderUnit}>kg CO₂e/u</span>
                            </span>
                        </div>
                        <input
                            type="range"
                            className={styles.terminalSlider}
                            min={1.0} max={5.0} step={0.1}
                            value={scope3}
                            onChange={e => setScope3(Number(e.target.value))}
                        />
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', opacity: 0.4, color: '#00ff88', marginTop: '2px' }}>
                            <span>1.0</span><span>5.0</span>
                        </div>
                    </div>
                </div>

                {/* ── Apply button ── */}
                <div style={{ marginTop: 'auto' }}>
                    {saveMsg && (
                        <div style={{ fontSize: '0.68rem', letterSpacing: '0.06em', color: '#00ff88', marginBottom: '0.75rem', opacity: 0.8 }}>
                            {saveMsg}
                        </div>
                    )}
                    <button
                        onClick={handleApply}
                        disabled={saving}
                        style={{
                            width: '100%',
                            padding: '0.65rem',
                            background: advanced
                                ? 'linear-gradient(135deg, rgba(255,68,68,0.15), rgba(255,136,0,0.12))'
                                : 'rgba(0,255,136,0.06)',
                            border: `1px solid ${advanced ? 'rgba(255,68,68,0.5)' : 'rgba(0,255,136,0.25)'}`,
                            color: advanced ? '#ff4444' : '#00ff88',
                            fontFamily: 'inherit',
                            fontSize: '0.68rem',
                            letterSpacing: '0.12em',
                            textTransform: 'uppercase',
                            cursor: saving ? 'not-allowed' : 'pointer',
                            opacity: saving ? 0.5 : 1,
                            borderRadius: '3px',
                            transition: 'all 0.2s',
                        }}
                    >
                        {saving ? '⟳ TRANSMITTING...' : '▶ APPLY TO LIVE ENGINE'}
                    </button>

                    {/* Data state readout */}
                    <div style={{ marginTop: '0.75rem', fontSize: '0.68rem', color: '#00ff88', opacity: 0.35, lineHeight: 1.8 }}>
                        <div>timeline_branch: {advanced ? '"ADVANCED"' : '"STANDARD"'}</div>
                        <div>global_carbon_fee: {carbonFee}</div>
                        <div>market_hostility_index: {hostility}</div>
                        <div>scope_3_threshold: {scope3.toFixed(1)}</div>
                    </div>
                </div>
            </div>

            {/* ══════════ RIGHT PANEL ══════════ */}
            <div className={styles.rightPanel}>
                <div className={styles.rightHeader}>
                    Simulation Timeline Visualiser — Module Branch Map
                    {advanced && (
                        <span style={{ marginLeft: 'auto', color: '#ff4444', fontSize: '0.68rem', letterSpacing: '0.1em' }}>
                            ⚡ ADVANCED CLIMATE ENGINE ACTIVE
                        </span>
                    )}
                </div>

                <div className={styles.timelineCard}>
                    <TimelineSVG
                        advanced={advanced}
                        carbonFee={carbonFee}
                        hostility={hostility}
                        scope3={scope3}
                    />
                </div>

                {/* Terminal output */}
                <div className={styles.terminal}>
                    {terminalContent}
                    <span className={styles.cursor} />
                </div>
            </div>
        </div>
    );
}
