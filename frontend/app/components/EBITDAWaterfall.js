'use client';
import { useMemo } from 'react';

/**
 * EBITDAWaterfall — Visual waterfall decomposition of round P&L.
 *
 * Gap 1 from UX Audit: Harvard Business Publishing uses full-width waterfall
 * charts to show exactly how each factor flows to EBITDA. This replaces
 * text-heavy event feeds with a visual "strategic storytelling" element.
 *
 * Props:
 *   businessUnits:  Current BU array (revenue_base, opex_base)
 *   globalState:    Current global state (tco2e, green_fund, etc.)
 *   events:         Round events from commit results
 *   commitResults:  Full commit results object
 *   isDark:         Theme mode (default true)
 */

const fmt$ = (v) => {
  const abs = Math.abs(v);
  if (abs >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
};

export default function EBITDAWaterfall({ businessUnits = [], globalState = {}, events = {}, commitResults = {}, isDark = true }) {
  const steps = useMemo(() => {
    const bus = businessUnits.length > 0 ? businessUnits : (commitResults?.businessUnits || []);
    const totalRevenue = bus.reduce((acc, bu) => acc + (bu.revenue_base || 0), 0);
    const totalOpex = bus.reduce((acc, bu) => acc + (bu.opex_base || 0), 0);
    const grossMargin = totalRevenue - totalOpex;

    // Extract costs from events/globalState
    const flags = globalState?.active_event_flags || events || {};
    const crisisResponse = events?.cost_impact || events?.crisis_cost || flags.crisis_cost || 0;
    const carbonTax = flags.internal_carbon_fee_deducted || globalState?.carbon_tax_cost || 0;
    const dividends = globalState?.dividends_paid || flags.dividends_paid || 0;
    const inflationDrag = flags.inflation_opex_increase || 0;
    const reputationBonus = flags.reputation_revenue_bonus || 0;
    const investmentCost = globalState?.capex_spent || flags.capex_spent || 0;

    // Compute net EBITDA
    const netEBITDA = grossMargin
      - Math.abs(crisisResponse)
      - Math.abs(carbonTax)
      - Math.abs(dividends)
      - Math.abs(inflationDrag)
      + Math.abs(reputationBonus)
      - Math.abs(investmentCost);

    const raw = [
      { label: 'Revenue', value: totalRevenue, type: 'positive', icon: '💰' },
      { label: 'OPEX', value: -totalOpex, type: 'negative', icon: '🏭' },
    ];

    if (crisisResponse > 0) {
      raw.push({ label: 'Crisis Cost', value: -crisisResponse, type: 'negative', icon: '🚨' });
    }
    if (carbonTax > 0) {
      raw.push({ label: 'Carbon Tax', value: -carbonTax, type: 'negative', icon: '🌡️' });
    }
    if (inflationDrag > 0) {
      raw.push({ label: 'Inflation', value: -inflationDrag, type: 'negative', icon: '📈' });
    }
    if (reputationBonus > 0) {
      raw.push({ label: 'Rep. Bonus', value: reputationBonus, type: 'positive', icon: '⭐' });
    }
    if (investmentCost > 0) {
      raw.push({ label: 'CapEx', value: -investmentCost, type: 'negative', icon: '🔧' });
    }
    if (dividends > 0) {
      raw.push({ label: 'Dividends', value: -dividends, type: 'negative', icon: '💸' });
    }

    raw.push({ label: 'EBITDA', value: netEBITDA, type: 'total', icon: '📊' });

    return raw;
  }, [businessUnits, globalState, events, commitResults]);

  // Compute waterfall geometry
  const maxAbsValue = Math.max(...steps.map(s => Math.abs(s.value)), 1);
  const barMaxWidth = 200; // px

  // Running total for waterfall positioning
  let runningTotal = 0;
  const bars = steps.map((step, i) => {
    const isTotal = step.type === 'total';
    const absWidth = Math.max(8, (Math.abs(step.value) / maxAbsValue) * barMaxWidth);

    if (isTotal) {
      const totalWidth = Math.max(8, (Math.abs(step.value) / maxAbsValue) * barMaxWidth);
      return { ...step, barWidth: totalWidth, isPositive: step.value >= 0 };
    }

    runningTotal += step.value;
    return { ...step, barWidth: absWidth, isPositive: step.value >= 0 };
  });

  const colors = {
    positive: isDark ? '#4ade80' : '#16a34a',
    negative: isDark ? '#f87171' : '#dc2626',
    total: isDark ? '#60a5fa' : '#2563eb',
    totalNeg: isDark ? '#f97316' : '#ea580c',
    labelColor: isDark ? '#e2e8f0' : '#0f172a',
    mutedColor: isDark ? '#94a3b8' : '#64748b',
    bgColor: isDark ? 'rgba(14, 20, 36, 0.5)' : 'rgba(241, 245, 249, 0.8)',
    borderColor: isDark ? 'rgba(0, 229, 195, 0.08)' : 'rgba(0, 0, 0, 0.08)',
    rowHover: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
  };

  if (steps.length <= 2) return null; // Skip if only Revenue+OPEX (no meaningful decomposition)

  return (
    <div style={{
      background: colors.bgColor,
      border: `1px solid ${colors.borderColor}`,
      borderRadius: '10px',
      padding: '14px 16px',
      marginTop: '14px',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '6px',
        marginBottom: '12px', paddingBottom: '8px',
        borderBottom: `1px solid ${colors.borderColor}`,
      }}>
        <span style={{ fontSize: '0.85rem' }}>📊</span>
        <span style={{
          fontSize: '0.72rem', fontWeight: 800,
          textTransform: 'uppercase', letterSpacing: '0.1em',
          color: colors.total,
        }}>
          EBITDA Decomposition
        </span>
      </div>

      {/* Waterfall Bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
        {bars.map((bar, i) => {
          const isTotal = bar.type === 'total';
          const barColor = isTotal
            ? (bar.isPositive ? colors.total : colors.totalNeg)
            : (bar.isPositive ? colors.positive : colors.negative);

          return (
            <div key={i} style={{
              display: 'grid',
              gridTemplateColumns: '24px 80px 1fr 72px',
              alignItems: 'center',
              gap: '8px',
              padding: '4px 8px',
              borderRadius: '6px',
              background: isTotal ? `${barColor}12` : 'transparent',
              borderTop: isTotal ? `1px dashed ${barColor}40` : 'none',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = isTotal ? `${barColor}18` : colors.rowHover}
            onMouseLeave={e => e.currentTarget.style.background = isTotal ? `${barColor}12` : 'transparent'}
            >
              {/* Icon */}
              <span style={{ fontSize: '0.82rem', textAlign: 'center' }}>{bar.icon}</span>

              {/* Label */}
              <span style={{
                fontSize: isTotal ? '0.75rem' : '0.72rem',
                fontWeight: isTotal ? 800 : 600,
                color: isTotal ? barColor : colors.labelColor,
                textTransform: isTotal ? 'uppercase' : 'none',
                letterSpacing: isTotal ? '0.06em' : 'normal',
              }}>
                {bar.label}
              </span>

              {/* Bar */}
              <div style={{ display: 'flex', alignItems: 'center', height: '14px' }}>
                <div style={{
                  width: `${bar.barWidth}px`,
                  height: isTotal ? '12px' : '10px',
                  borderRadius: '3px',
                  background: `linear-gradient(90deg, ${barColor}, ${barColor}cc)`,
                  boxShadow: isTotal ? `0 2px 8px ${barColor}30` : 'none',
                  transition: 'width 0.6s cubic-bezier(0.22, 1, 0.36, 1)',
                }} />
              </div>

              {/* Value */}
              <span style={{
                fontSize: isTotal ? '0.78rem' : '0.72rem',
                fontWeight: isTotal ? 900 : 700,
                fontFamily: "'JetBrains Mono', monospace",
                fontVariantNumeric: 'tabular-nums',
                color: barColor,
                textAlign: 'right',
              }}>
                {bar.value >= 0 ? '' : '−'}{fmt$(Math.abs(bar.value))}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
