'use client';

import { useState, useMemo } from 'react';
import {
  LineChart, Line, AreaChart, Area, ComposedChart, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ReferenceLine,
} from 'recharts';
import StockPerformanceChart from './StockPerformanceChart';
import { roundToQuarter } from '../utils/roundToQuarter';
import styles from './ExecutiveCockpit.module.css';

/**
 * KPIDashboard — Tabbed KPI panel with Financial / ESG toggle.
 *
 * Financial tab: Stock Performance + EBITDA line
 * ESG tab: Carbon Tracker + VRIO Radar + Stakeholder Trust
 *
 * Bottom: Compact KPI summary strip (Treasury, Reputation, Carbon, EBITDA)
 */

const NET_ZERO_TARGET = 500;

const TAB_CONFIG = [
  { id: 'financial', label: '💰 Financial', icon: '📈' },
  { id: 'esg', label: '🌱 ESG', icon: '🌍' },
];

export default function KPIDashboard({
  historyData = [],
  ebitda = 0,
  tco2e = 0,
  vrio = {},
  reputation = 50,
  projectedCost = 0,
  globalState,
  businessUnits = [],
  roundNumber = 1,
  events,
}) {
  const [activeTab, setActiveTab] = useState('financial');

  // VRIO radar data
  const vrioData = useMemo(() => [
    { axis: 'Social License', value: vrio.value || 0 },
    { axis: 'Carbon Risk', value: vrio.rarity || 0 },
    { axis: 'Synergy', value: vrio.imitability || 0 },
    { axis: 'Governance', value: vrio.organization || 0 },
  ], [vrio]);

  // Round-over-round delta for EBITDA
  const ebitdaDelta = useMemo(() => {
    if (historyData.length < 2) return null;
    const prev = historyData[historyData.length - 2]?.ebitda || 0;
    const curr = historyData[historyData.length - 1]?.ebitda || 0;
    return curr - prev;
  }, [historyData]);

  // Trust gauge
  const trustColor = reputation >= 60 ? '#22c55e' : reputation >= 40 ? '#f59e0b' : '#ef4444';

  const fmtM = (v) => `$${(v / 1_000_000).toFixed(1)}M`;

  return (
    <>
      {/* ── Tab Toggle ── */}
      <div style={{
        display: 'flex', gap: 4, marginBottom: 8,
        background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: 4,
        border: '1px solid rgba(255,255,255,0.05)',
      }}>
        {TAB_CONFIG.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              flex: 1, padding: '6px 8px',
              borderRadius: 6, border: 'none',
              background: activeTab === tab.id
                ? 'rgba(0, 229, 195, 0.15)'
                : 'transparent',
              color: activeTab === tab.id ? '#00e5c3' : '#64748b',
              fontSize: '0.65rem', fontWeight: 800,
              cursor: 'pointer',
              boxShadow: activeTab === tab.id ? '0 0 12px rgba(0, 229, 195, 0.2)' : 'none',
              transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
              letterSpacing: '0.05em',
              textTransform: 'uppercase',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── FINANCIAL TAB ── */}
      {activeTab === 'financial' && (
        <>
          {/* Stock Performance */}
          <StockPerformanceChart
            historyData={historyData}
            globalState={globalState}
            businessUnits={businessUnits}
            roundNumber={roundNumber}
            events={events}
            projectedCost={projectedCost}
          />

          {/* EBITDA Line Graph */}
          <div className={styles.kpiCard}>
            <div className={styles.kpiTitle}>
              💰 Group EBITDA
              {projectedCost !== 0 && (
                <span className={`${styles.projectedDelta} ${projectedCost > 0 ? styles.projectedDown : styles.projectedUp}`}>
                  {projectedCost > 0 ? '↓' : '↑'} {fmtM(Math.abs(projectedCost))}
                </span>
              )}
            </div>
            <div className={styles.kpiValue}>
              {fmtM(ebitda)}
              {ebitdaDelta != null && (
                <span style={{
                  marginLeft: 8, fontSize: '0.6rem', fontWeight: 600,
                  color: ebitdaDelta >= 0 ? '#22c55e' : '#ef4444',
                }}>
                  {ebitdaDelta >= 0 ? '▲' : '▼'} {fmtM(Math.abs(ebitdaDelta))}
                </span>
              )}
            </div>
            <div className={styles.kpiChart}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historyData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                  <XAxis dataKey="round" tick={{ fontSize: 9, fill: '#94a3b8' }} tickLine={false} axisLine={false} tickFormatter={(v) => roundToQuarter(v).shortLabel} />
                  <YAxis 
                    domain={['auto', 'auto']} 
                    tick={{ fontSize: 9, fill: '#94a3b8' }} 
                    tickLine={false} 
                    axisLine={false}
                    tickFormatter={(v) => `$${(v / 1_000_000).toFixed(0)}M`}
                    width={40}
                  />
                  <Tooltip
                    labelFormatter={(v) => roundToQuarter(v).label}
                    formatter={(v) => [fmtM(v), 'EBITDA']}
                    contentStyle={{ fontSize: 10, borderRadius: 6, border: '1px solid rgba(0,229,195,0.15)', background: '#0f1524', color: '#e2e8f0' }}
                  />
                  <Line type="monotone" dataKey="ebitda" stroke="#00e5c3" strokeWidth={2} dot={{ r: 3, fill: '#00e5c3' }} activeDot={{ r: 5 }} />
                  {projectedCost !== 0 && (
                    <ReferenceLine y={ebitda - projectedCost} stroke="#94a3b8" strokeDasharray="4 4" label={{ value: 'Proj.', fontSize: 8, fill: '#94a3b8' }} />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* CAROIC Card — Carbon-Adjusted Return on Invested Capital */}
          {events?.caroic && (
            <div className={styles.kpiCard}>
              <div className={styles.kpiTitle}>🌿 CAROIC — Carbon-Adjusted Return</div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
                <div className={styles.kpiValue} style={{
                  color: events.caroic.grade === 'A+' || events.caroic.grade === 'A'
                    ? '#22c55e'
                    : events.caroic.grade === 'B' || events.caroic.grade === 'C'
                      ? '#f59e0b'
                      : '#ef4444',
                }}>
                  {events.caroic.caroic_pct}%
                </div>
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  padding: '2px 8px',
                  borderRadius: 4,
                  background: events.caroic.grade === 'A+' || events.caroic.grade === 'A'
                    ? 'rgba(34,197,94,0.15)'
                    : events.caroic.grade === 'B' || events.caroic.grade === 'C'
                      ? 'rgba(245,158,11,0.15)'
                      : 'rgba(239,68,68,0.15)',
                  color: events.caroic.grade === 'A+' || events.caroic.grade === 'A'
                    ? '#4ade80'
                    : events.caroic.grade === 'B' || events.caroic.grade === 'C'
                      ? '#fcd34d'
                      : '#fca5a5',
                  letterSpacing: '0.05em',
                }}>
                  Grade {events.caroic.grade}
                </span>
              </div>
              <div style={{ fontSize: '0.65rem', color: '#94a3b8', marginTop: 4, lineHeight: 1.4 }}>
                {events.caroic.interpretation}
              </div>
              <div style={{
                display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, marginTop: 8,
                fontSize: '0.6rem', color: '#64748b',
              }}>
                <div style={{ textAlign: 'center', padding: '4px 0', background: 'rgba(255,255,255,0.03)', borderRadius: 4 }}>
                  <div style={{ color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>NOPAT</div>
                  <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{fmtM(events.caroic.nopat)}</div>
                </div>
                <div style={{ textAlign: 'center', padding: '4px 0', background: 'rgba(255,255,255,0.03)', borderRadius: 4 }}>
                  <div style={{ color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>Carbon Charge</div>
                  <div style={{ color: '#fbbf24', fontWeight: 600 }}>{fmtM(events.caroic.carbon_capital_charge)}</div>
                </div>
                <div style={{ textAlign: 'center', padding: '4px 0', background: 'rgba(255,255,255,0.03)', borderRadius: 4 }}>
                  <div style={{ color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>Adj. Capital</div>
                  <div style={{ color: '#e2e8f0', fontWeight: 600 }}>{fmtM(events.caroic.adjusted_capital)}</div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── ESG TAB ── */}
      {activeTab === 'esg' && (
        <>
          {/* Carbon Tracker */}
            <div className={styles.kpiCard}>
            <div className={styles.kpiTitle}>🏭 Carbon Footprint (Current Year tCO₂e)</div>
            <div className={styles.kpiValue}>
              {tco2e.toLocaleString()} t
              {historyData.length >= 2 && (() => {
                const curr = historyData[historyData.length - 1]?.tco2e || 0;
                const prev = historyData[historyData.length - 2]?.tco2e || 0;
                const delta = curr - prev;
                return delta !== 0 ? (
                  <span style={{
                    marginLeft: 8, fontSize: '0.6rem', fontWeight: 600,
                    color: delta <= 0 ? '#22c55e' : '#ef4444',
                  }}>
                    {delta <= 0 ? '▼' : '▲'} {Math.abs(delta).toLocaleString()} t/yr
                  </span>
                ) : null;
              })()}
            </div>
            <div className={styles.kpiChart} style={{ height: '110px', minHeight: '110px', marginTop: '8px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={(() => {
                  let cumulative = 0;
                  return historyData.map(h => {
                    cumulative += (h.tco2e || 0);
                    return { ...h, cumulativeTco2e: cumulative, yearlyTco2e: h.tco2e || 0 };
                  });
                })()} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                  <XAxis dataKey="round" tick={{ fontSize: 9, fill: '#94a3b8' }} tickLine={false} axisLine={false} tickFormatter={(v) => roundToQuarter(v).shortLabel} />
                  <YAxis yAxisId="left" hide domain={[0, 'auto']} />
                  <YAxis yAxisId="right" hide domain={[0, 'auto']} orientation="right" />
                  <Tooltip
                    labelFormatter={(v) => roundToQuarter(v).label}
                    formatter={(v, name) => [
                      `${v.toLocaleString()} t`,
                      name === 'cumulativeTco2e' ? 'Cumulative tCO₂e' : 'Per-Year tCO₂e'
                    ]}
                    contentStyle={{ fontSize: 10, borderRadius: 6, border: '1px solid rgba(0,229,195,0.15)', background: '#0f1524', color: '#e2e8f0' }}
                  />
                  <Area yAxisId="left" type="monotone" dataKey="cumulativeTco2e" stroke="#f59e0b" fill="rgba(245,158,11,0.1)" strokeWidth={2} dot={{ r: 3, fill: '#f59e0b' }} activeDot={{ r: 5 }} />
                  <Line yAxisId="right" type="monotone" dataKey="yearlyTco2e" stroke="#3b82f6" strokeWidth={2} dot={{ r: 2, fill: '#3b82f6' }} strokeDasharray="4 3" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Carbon Intensity Tracker */}
          <div className={styles.kpiCard}>
            <div className={styles.kpiTitle}>📏 Carbon Intensity (tCO₂e per $1M Revenue)</div>
            <div className={styles.kpiValue}>
              {(() => {
                const rev = globalState?.revenue || (ebitda * 4.5);
                return rev ? (tco2e / (rev / 1_000_000)).toFixed(2) : '0.00';
              })()}
              <span style={{ fontSize: '0.6rem', color: '#94a3b8', marginLeft: '4px', fontWeight: 600 }}>t/$1M</span>
              {historyData.length >= 2 && (() => {
                const getInt = (h) => {
                  const r = h.globalState?.revenue || ((h.ebitda || 1) * 4.5);
                  return r ? (h.tco2e || 0) / (r / 1_000_000) : 0;
                };
                const curr = getInt(historyData[historyData.length - 1]);
                const prev = getInt(historyData[historyData.length - 2]);
                const delta = curr - prev;
                return delta !== 0 ? (
                  <span style={{
                    marginLeft: 8, fontSize: '0.6rem', fontWeight: 600,
                    color: delta <= 0 ? '#22c55e' : '#ef4444',
                  }}>
                    {delta <= 0 ? '▼' : '▲'} {Math.abs(delta).toFixed(2)}
                  </span>
                ) : null;
              })()}
            </div>
            <div className={styles.kpiChart} style={{ height: '110px', minHeight: '110px', marginTop: '8px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={(() => {
                  return historyData.map(h => {
                    const r = h.globalState?.revenue || ((h.ebitda || 1) * 4.5);
                    const intensity = r ? (h.tco2e || 0) / (r / 1_000_000) : 0;
                    return { ...h, intensity: parseFloat(intensity.toFixed(2)) };
                  });
                })()} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                  <XAxis dataKey="round" tick={{ fontSize: 9, fill: '#94a3b8' }} tickLine={false} axisLine={false} tickFormatter={(v) => roundToQuarter(v).shortLabel} />
                  <YAxis hide domain={['auto', 'auto']} />
                  <Tooltip
                    labelFormatter={(v) => roundToQuarter(v).label}
                    formatter={(v) => [`${v} t/$1M`, 'Intensity']}
                    contentStyle={{ fontSize: 10, borderRadius: 6, border: '1px solid rgba(0,229,195,0.15)', background: '#0f1524', color: '#e2e8f0' }}
                  />
                  <Line type="monotone" dataKey="intensity" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3, fill: '#8b5cf6' }} activeDot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          {/* Risk & Reputation Dual Display */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          {/* Risk Exposure & Resilience Radar */}
          <div className={styles.kpiCard}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div className={styles.kpiTitle}>🛡️ Risk & Resilience</div>
              {vrio.value !== undefined && (() => {
                const riskScore = ((vrio.organization || 0) + (100 - (vrio.value || 0)) + (vrio.rarity || 0)) / 3;
                return (
                  <div style={{ fontSize: '0.65rem', fontWeight: 800, padding: '2px 6px', borderRadius: 4, background: riskScore > 50 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)', color: riskScore > 50 ? '#fca5a5' : '#6ee7b7' }}>
                    Risk: {riskScore.toFixed(0)}/100
                  </div>
                );
              })()}
            </div>
            <div className={styles.kpiChart}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={vrioData} cx="50%" cy="50%" outerRadius="55%">
                  <PolarGrid stroke="rgba(0,229,195,0.12)" />
                  <PolarAngleAxis dataKey="axis" tick={{ fontSize: 8, fill: '#64748b' }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar dataKey="value" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.15} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Stakeholder Trust Gauge */}
          <div className={styles.kpiCard}>
            <div className={styles.kpiTitle}>🌍 Corporate Reputation</div>
            <div className={styles.gauge}>
              <div className={styles.gaugeCircle}>
                <svg width="100%" height="80px" viewBox="-15 -15 130 130" preserveAspectRatio="xMidYMid meet">
                  <defs>
                    <linearGradient id="trustGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor={reputation >= 80 ? '#15803d' : reputation >= 60 ? '#3b82f6' : reputation >= 40 ? '#f59e0b' : '#ef4444'} />
                      <stop offset="100%" stopColor={reputation >= 80 ? '#166534' : reputation >= 60 ? '#2563eb' : reputation >= 40 ? '#d97706' : '#dc2626'} />
                    </linearGradient>
                    <filter id="trustGlow">
                      <feGaussianBlur stdDeviation="3" result="blur" />
                      <feMerge>
                        <feMergeNode in="blur" />
                        <feMergeNode in="SourceGraphic" />
                      </feMerge>
                    </filter>
                  </defs>
                  <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="7" />
                  <circle
                    cx="50" cy="50" r="42"
                    fill="none"
                    stroke="url(#trustGrad)"
                    strokeWidth="7"
                    strokeLinecap="round"
                    strokeDasharray={2 * Math.PI * 42}
                    strokeDashoffset={2 * Math.PI * 42 - (reputation / 100) * 2 * Math.PI * 42}
                    transform="rotate(-90 50 50)"
                    filter="url(#trustGlow)"
                    style={{ transition: 'stroke-dashoffset 0.6s ease' }}
                  />
                  {[25, 50, 75].map(v => {
                    const angle = (v / 100) * 360 - 90;
                    const rad = (angle * Math.PI) / 180;
                    const x1 = 50 + 36 * Math.cos(rad);
                    const y1 = 50 + 36 * Math.sin(rad);
                    const x2 = 50 + 38 * Math.cos(rad);
                    const y2 = 50 + 38 * Math.sin(rad);
                    return <line key={v} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#94a3b8" strokeWidth="1.5" />;
                  })}
                </svg>
                <span className={styles.gaugeValue} style={{ color: '#f8fafc', textShadow: '0 0 10px rgba(255,255,255,0.2)' }}>{Math.round(reputation)}</span>
              </div>
              <span className={styles.gaugeLabel} style={{ color: reputation >= 80 ? '#4ade80' : reputation >= 60 ? '#60a5fa' : reputation >= 40 ? '#fcd34d' : '#fca5a5' }}>
                {reputation >= 80 ? 'Excellent' : reputation >= 60 ? 'Strong' : reputation >= 40 ? 'Moderate' : reputation >= 20 ? 'Low' : 'Critical'}
              </span>
            </div>
          </div>
          </div>
        </>
      )}
    </>
  );
}
