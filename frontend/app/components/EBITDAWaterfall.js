'use client';
import { useMemo } from 'react';
import { buildWaterfall } from './ebitdaWaterfallModel';
import { currencySymbol, atRate } from '../utils/format';

/**
 * EBITDAWaterfall — Visual waterfall decomposition of the round.
 *
 * Slot: results stage (rendered after commit, inside the Focus Results block).
 *
 * Gap 1 from UX Audit: Harvard Business Publishing uses full-width waterfall
 * charts to show exactly how each factor flows to EBITDA. This replaces
 * text-heavy event feeds with a visual "strategic storytelling" element.
 *
 * BUG-2026-07-29: this panel never rendered. It read six fields, five of which
 * the backend never writes, so it always fell through `steps.length <= 2` and
 * returned null. The step builder now lives in ebitdaWaterfallModel.js, keyed
 * to fields the engine actually emits — see that file for the full account,
 * including why carbon and crisis costs sit BELOW the EBITDA line rather than
 * inside it (engine: historical_ebitda = revenue - opex, nothing else).
 *
 * Props:
 *   businessUnits:  Current BU array (revenue_base, opex_base)
 *   globalState:    Current global state (round_number, historical_ebitda, flags)
 *   events:         Round events from commit results
 *   commitResults:  Full commit results object
 *   isDark:         Theme mode (default true)
 */

const fmt$ = (v) => {
  const abs = Math.abs(v);
  if (abs >= 1e6) return `${currencySymbol()}${atRate(v / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `${currencySymbol()}${atRate(v / 1e3).toFixed(0)}K`;
  return `${currencySymbol()}${atRate(v).toFixed(0)}`;
};

export default function EBITDAWaterfall({ businessUnits = [], globalState = {}, events = {}, commitResults = {}, isDark = true }) {
  const { steps, reconciles } = useMemo(
    () => buildWaterfall({ businessUnits, globalState, events, commitResults }),
    [businessUnits, globalState, events, commitResults],
  );

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

  // Revenue + OPEX + EBITDA is already a real (if minimal) bridge, so 3 steps
  // is legitimately renderable. The old threshold of >2 combined with the
  // dead field names is what made this panel invisible for its whole life.
  if (steps.length < 3) return null;

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
          fontSize: 'var(--type-caption)', fontWeight: 800,
          textTransform: 'uppercase', letterSpacing: '0.1em',
          color: colors.total,
        }}>
          EBITDA Bridge & Cash Impact
        </span>
      </div>

      {/* Waterfall Bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
        {bars.map((bar, i) => {
          const isTotal = bar.type === 'total';
          // The line that carries the lesson: everything below it moved CASH,
          // not EBITDA. Without this the chart would imply carbon and crisis
          // costs reduce EBITDA, which in this engine they do not.
          const startsCashSection = bar.section === 'cash' && bars[i - 1]?.section !== 'cash';
          const barColor = isTotal
            ? (bar.isPositive ? colors.total : colors.totalNeg)
            : (bar.isPositive ? colors.positive : colors.negative);

          return (
            <div key={i}>
            {startsCashSection && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                margin: '10px 0 6px', paddingTop: 8,
                borderTop: `1px dashed ${colors.borderColor}`,
              }}>
                <span style={{ fontSize: 'var(--type-caption)', fontWeight: 800, letterSpacing: '0.09em',
                               textTransform: 'uppercase', color: colors.mutedColor }}>
                  Below EBITDA — cash movements this round
                </span>
              </div>
            )}
            <div style={{
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
            </div>
          );
        })}
      </div>

      {/* If the engine's own historical_ebitda stops matching revenue - opex,
          this chart is no longer telling the truth. Say so rather than draw a
          confident bar over a broken assumption. */}
      {!reconciles && (
        <div style={{
          marginTop: 10, padding: '6px 10px', borderRadius: 6,
          background: 'rgba(249,115,22,0.10)', border: '1px dashed rgba(249,115,22,0.45)',
          color: colors.mutedColor, fontSize: 'var(--type-caption)', fontWeight: 600,
        }}>
          ⚠ Revenue − OPEX no longer equals the engine's reported EBITDA. The
          bridge above may be incomplete.
        </div>
      )}
    </div>
  );
}
