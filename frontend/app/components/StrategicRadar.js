/**
 * StrategicRadar.js — Always-visible KPI bar (PHASE-3, Layer 1)
 * 6 key metrics with trend arrows, sparklines, and tipping proximity.
 * Designed for constant peripheral awareness without cognitive overload.
 */
import React, { useMemo } from 'react';
import styles from './StrategicRadar.module.css';

const METRICS = [
  { key: 'treasury', label: 'Treasury', prefix: '$', format: 'currency', goodDir: 'up', icon: '💰' },
  { key: 'reputation', label: 'Reputation', format: 'score', goodDir: 'up', icon: '⭐' },
  { key: 'slo', label: 'Social License', format: 'score', goodDir: 'up', icon: '🤝' },
  { key: 'ncd', label: 'Nat. Capital Debt', format: 'number', goodDir: 'down', icon: '🌿' },
  { key: 'wacc', label: 'WACC', suffix: '%', format: 'percent', goodDir: 'down', icon: '📊' },
  { key: 'burnout', label: 'Burnout', format: 'score', goodDir: 'down', icon: '🔥' },
];

function formatValue(val, format, prefix = '', suffix = '') {
  if (val == null) return '—';
  if (format === 'currency') {
    const abs = Math.abs(val);
    const sign = val < 0 ? '-' : '';
    if (abs >= 1e6) return `${sign}${prefix}${(abs / 1e6).toFixed(1)}M`;
    if (abs >= 1e3) return `${sign}${prefix}${(abs / 1e3).toFixed(0)}K`;
    return `${sign}${prefix}${abs.toFixed(0)}`;
  }
  if (format === 'percent') return `${(val * 100).toFixed(1)}${suffix}`;
  if (format === 'score') return `${Math.round(val)}`;
  return `${prefix}${Math.round(val)}${suffix}`;
}

function getTrend(current, previous) {
  if (previous == null || current == null) return 'stable';
  const diff = current - previous;
  if (Math.abs(diff) < 0.5) return 'stable';
  return diff > 0 ? 'up' : 'down';
}

function MiniSparkline({ history, color, goodDir }) {
  if (!history || history.length < 2) return null;
  const min = Math.min(...history);
  const max = Math.max(...history);
  const range = max - min || 1;
  const w = 60, h = 20;
  const points = history.map((v, i) =>
    `${(i / (history.length - 1)) * w},${h - ((v - min) / range) * h}`
  ).join(' ');

  return (
    <svg width={w} height={h} className={styles.sparkline}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function TippingIndicator({ tier }) {
  const colors = {
    none: '#10b981', safe: '#10b981',
    warning: '#f59e0b', stressed: '#ef4444', tipped: '#7f1d1d',
  };
  const c = colors[tier] || colors.none;
  return (
    <span className={styles.tippingDot} style={{ background: c }}
      title={`Tipping: ${tier || 'safe'}`} />
  );
}

export default function StrategicRadar({
  globalState = {},
  buStates = [],
  previousState = {},
  history = [],
  tippingState = {},
  esgWacc = null,
}) {
  const n = Math.max((buStates || []).length, 1);

  const current = useMemo(() => ({
    treasury: globalState.corporate_treasury,
    reputation: globalState.group_reputation,
    slo: (buStates || []).reduce((s, bu) => s + (bu.social_license_score || 50), 0) / n,
    ncd: (buStates || []).reduce((s, bu) => s + (bu.natural_capital_debt || 0), 0),
    wacc: esgWacc?.adjusted_wacc || globalState.cost_of_capital || 0.05,
    burnout: (buStates || []).reduce((s, bu) => s + (bu.staff_burnout_index || 0), 0) / n,
  }), [globalState, buStates, esgWacc, n]);

  const prev = useMemo(() => ({
    treasury: previousState?.corporate_treasury,
    reputation: previousState?.group_reputation,
    slo: null,
    ncd: null,
    wacc: previousState?.cost_of_capital,
    burnout: null,
  }), [previousState]);

  const sparkData = useMemo(() => {
    const data = {};
    METRICS.forEach(m => { data[m.key] = []; });
    (history || []).forEach(h => {
      const gs = h.global_state || h;
      const hBus = h.business_units || h.bu_states || [];
      const hn = Math.max(hBus.length, 1);
      data.treasury.push(gs.corporate_treasury || 0);
      data.reputation.push(gs.group_reputation || 0);
      data.slo.push(hBus.reduce((s, b) => s + (b.social_license_score || 50), 0) / hn);
      data.ncd.push(hBus.reduce((s, b) => s + (b.natural_capital_debt || 0), 0));
      data.wacc.push(gs.cost_of_capital || 0.05);
      data.burnout.push(hBus.reduce((s, b) => s + (b.staff_burnout_index || 0), 0) / hn);
    });
    // Add current
    METRICS.forEach(m => { data[m.key].push(current[m.key]); });
    return data;
  }, [history, current]);

  return (
    <div className={styles.radarBar} id="strategic-radar">
      {METRICS.map(m => {
        const val = current[m.key];
        const prevVal = prev[m.key];
        const trend = getTrend(val, prevVal);
        const isGood = (trend === m.goodDir) || trend === 'stable';
        const trendArrow = trend === 'up' ? '▲' : trend === 'down' ? '▼' : '─';
        const trendColor = isGood ? '#10b981' : '#ef4444';
        const dim = m.key === 'wacc' ? 'financial' : m.key === 'burnout' ? 'social' : 'climate';
        const tier = tippingState?.[`${dim}_tier`] || 'none';

        return (
          <div key={m.key} className={styles.metricCard}>
            <div className={styles.metricHeader}>
              <span className={styles.metricIcon}>{m.icon}</span>
              <span className={styles.metricLabel}>{m.label}</span>
              <TippingIndicator tier={tier} />
            </div>
            <div className={styles.metricValue}>
              {formatValue(val, m.format, m.prefix || '', m.suffix || '')}
              <span className={styles.trendArrow} style={{ color: trendColor }}>
                {trendArrow}
              </span>
            </div>
            <MiniSparkline
              history={sparkData[m.key]}
              color={trendColor}
              goodDir={m.goodDir}
            />
          </div>
        );
      })}
    </div>
  );
}
