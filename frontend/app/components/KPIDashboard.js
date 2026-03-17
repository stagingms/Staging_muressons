'use client';

import { useMemo } from 'react';
import {
  LineChart, Line, AreaChart, Area, ComposedChart, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ReferenceLine,
} from 'recharts';
import styles from './ExecutiveCockpit.module.css';

/**
 * KPIDashboard — 4 vertically stacked KPI cards with Recharts.
 *
 * 1. EBITDA Line Graph (with round-over-round delta)
 * 2. Carbon Tracker (area chart with Net Zero target)
 * 3. VRIO Radar Chart
 * 4. Stakeholder Trust Gauge
 */

const NET_ZERO_TARGET = 500; // tCO2e target line

export default function KPIDashboard({
  historyData = [],
  ebitda = 0,
  tco2e = 0,
  vrio = {},
  reputation = 50,
  projectedCost = 0,
}) {
  // VRIO radar data
  const vrioData = useMemo(() => [
    { axis: 'Avg. Social License', value: vrio.value || 0 },
    { axis: 'Avg. Carbon Intensity', value: vrio.rarity || 0 },
    { axis: 'Synergy', value: vrio.imitability || 0 },
    { axis: 'Avg. Governance Risk', value: vrio.organization || 0 },
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
  const circumference = 2 * Math.PI * 38;
  const dashOffset = circumference - (reputation / 100) * circumference;

  const fmtM = (v) => `$${(v / 1_000_000).toFixed(1)}M`;

  return (
    <>
      {/* 1. EBITDA Line Graph */}
      <div className={styles.kpiCard}>
        <div className={styles.kpiTitle}>
          📈 Financial Performance (EBITDA)
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
              <XAxis dataKey="year" tick={{ fontSize: 9, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
              <YAxis hide domain={['auto', 'auto']} />
              <Tooltip
                labelFormatter={(v) => `Year ${v}`}
                formatter={(v) => [fmtM(v), 'EBITDA']}
                contentStyle={{ fontSize: 10, borderRadius: 6, border: '1px solid #e5e7eb' }}
              />
              <Line type="monotone" dataKey="ebitda" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
              {projectedCost !== 0 && (
                <ReferenceLine y={ebitda - projectedCost} stroke="#94a3b8" strokeDasharray="4 4" label={{ value: 'Proj.', fontSize: 8, fill: '#94a3b8' }} />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 2. Carbon Tracker — Cumulative Area Chart + Per-Year Line */}
      <div className={styles.kpiCard}>
        <div className={styles.kpiTitle}>🏭 Environmental Impact (Cumulative tCO₂e)</div>
        <div className={styles.kpiValue}>
          {(() => {
            const cumTotal = historyData.reduce((s, h) => s + (h.tco2e || 0), 0);
            return cumTotal.toLocaleString();
          })()} t
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
        <div className={styles.kpiChart}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={(() => {
              let cumulative = 0;
              return historyData.map(h => {
                cumulative += (h.tco2e || 0);
                return { ...h, cumulativeTco2e: cumulative, yearlyTco2e: h.tco2e || 0 };
              });
            })()} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
              <XAxis dataKey="year" tick={{ fontSize: 9, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
              <YAxis yAxisId="left" hide domain={[0, 'auto']} />
              <YAxis yAxisId="right" hide domain={[0, 'auto']} orientation="right" />
              <Tooltip
                labelFormatter={(v) => `Year ${v}`}
                formatter={(v, name) => [
                  `${v.toLocaleString()} t`,
                  name === 'cumulativeTco2e' ? 'Cumulative tCO₂e' : 'Per-Year tCO₂e'
                ]}
                contentStyle={{ fontSize: 10, borderRadius: 6, border: '1px solid #e5e7eb' }}
              />
              <Area yAxisId="left" type="monotone" dataKey="cumulativeTco2e" stroke="#f59e0b" fill="#fef3c7" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
              <Line yAxisId="right" type="monotone" dataKey="yearlyTco2e" stroke="#3b82f6" strokeWidth={2} dot={{ r: 2, fill: '#3b82f6' }} strokeDasharray="4 3" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. VRIO Radar Chart */}
      <div className={styles.kpiCard}>
        <div className={styles.kpiTitle}>🎯 Strategic Resilience (VRIO)</div>
        <div className={styles.kpiChart}>
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={vrioData} cx="50%" cy="50%">
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="axis" tick={{ fontSize: 9, fill: '#64748b' }} />
              <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
              <Radar dataKey="value" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.15} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 4. Stakeholder Trust Gauge */}
      <div className={styles.kpiCard}>
        <div className={styles.kpiTitle}>🤝 Stakeholder Trust</div>
        <div className={styles.gauge}>
          <div className={styles.gaugeCircle}>
            <svg width="80" height="80" viewBox="0 0 80 80">
              <circle cx="40" cy="40" r="38" fill="none" stroke="#f1f5f9" strokeWidth="6" />
              <circle
                cx="40" cy="40" r="38"
                fill="none"
                stroke={trustColor}
                strokeWidth="6"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={dashOffset}
                transform="rotate(-90 40 40)"
                style={{ transition: 'stroke-dashoffset 0.5s ease' }}
              />
            </svg>
            <span className={styles.gaugeValue}>{Math.round(reputation)}</span>
          </div>
          <span className={styles.gaugeLabel}>Brand Equity Score</span>
        </div>
      </div>
    </>
  );
}
