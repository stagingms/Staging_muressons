'use client';
import { useState, useMemo, useCallback } from 'react';

/**
 * WhatIfSandbox — Player-facing "mock up decisions" mode.
 * Allows students to preview the estimated impact of decisions
 * BEFORE committing them. Shows projected deltas for Treasury,
 * Reputation, CO2, and EBITDA based on the current decision state.
 *
 * Props:
 *   options:          Available decision options (A/B/C or pillar config)
 *   businessUnits:    Current BU array
 *   globalState:      Current global state
 *   events:           Round events with impact data
 *   decisionChoice:   Currently selected choice
 *   allocations:      Capital allocations { bu_id: amount }
 *   csfPool:          Total capital available
 *   roundNumber:      Current round number
 *   isDark:           Theme mode
 */

const fmt$ = (v) => {
  const abs = Math.abs(v || 0);
  if (abs >= 1e6) return `$${((v || 0) / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `$${((v || 0) / 1e3).toFixed(0)}K`;
  return `$${(v || 0).toFixed(0)}`;
};

export default function WhatIfSandbox({
  options = [],
  businessUnits = [],
  globalState = {},
  events = {},
  decisionChoice,
  allocations = {},
  csfPool = 0,
  roundNumber = 1,
  isDark = true,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [sandboxChoice, setSandboxChoice] = useState(null);

  const treasury = globalState?.corporate_treasury || 0;
  const reputation = globalState?.group_reputation || 50;
  const tco2e = globalState?.tco2e_emissions || 0;
  const ebitda = businessUnits.reduce((a, bu) => a + (bu.revenue_base || 0) - (bu.opex_base || 0), 0);

  // Estimate impact of a given option choice
  const estimateImpact = useCallback((opt) => {
    if (!opt) return null;

    // Use impact data from options if available
    const impacts = opt.impacts || opt.effects || {};
    const treasuryDelta = impacts.treasury || impacts.treasury_delta || -(csfPool * 0.3);
    const repDelta = impacts.reputation || impacts.reputation_delta || 0;
    const carbonDelta = impacts.carbon || impacts.tco2e_delta || 0;
    const ebitdaDelta = impacts.ebitda || impacts.ebitda_delta || 0;

    // Factor in capital allocation costs
    const totalAllocated = Object.values(allocations).reduce((s, v) => s + v, 0);

    return {
      treasury: treasuryDelta - totalAllocated,
      reputation: repDelta,
      carbon: carbonDelta,
      ebitda: ebitdaDelta,
      projected: {
        treasury: treasury + treasuryDelta - totalAllocated,
        reputation: Math.max(0, Math.min(100, reputation + repDelta)),
        carbon: Math.max(0, tco2e + carbonDelta),
        ebitda: ebitda + ebitdaDelta,
      },
    };
  }, [treasury, reputation, tco2e, ebitda, csfPool, allocations]);

  const activeEstimate = useMemo(() => {
    const target = sandboxChoice || decisionChoice;
    if (!target || !options.length) return null;
    const opt = options.find(o => o.key === target || o.id === target);
    return estimateImpact(opt);
  }, [sandboxChoice, decisionChoice, options, estimateImpact]);

  const colors = {
    accent: '#00e5c3',
    bg: isDark ? 'rgba(0, 229, 195, 0.04)' : 'rgba(0, 229, 195, 0.06)',
    border: isDark ? 'rgba(0, 229, 195, 0.15)' : 'rgba(0, 229, 195, 0.25)',
    text: isDark ? '#e2e8f0' : '#1e293b',
    muted: isDark ? '#64748b' : '#94a3b8',
    positive: '#4ade80',
    negative: '#f87171',
  };

  if (!options.length) return null;

  return (
    <div style={{
      border: `1px solid ${isOpen ? colors.border : 'rgba(0,229,195,0.08)'}`,
      borderRadius: '10px',
      background: isOpen ? colors.bg : 'transparent',
      transition: 'background 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease, opacity 0.3s ease, transform 0.3s ease',
      marginBottom: '8px',
      overflow: 'hidden',
    }}>
      {/* Toggle Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '8px 12px',
          background: 'none', border: 'none',
          color: colors.accent,
          fontSize: '0.72rem', fontWeight: 700,
          cursor: 'pointer',
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          🧪 What-If Sandbox
          {isOpen && <span style={{
            fontSize: '0.68rem', fontWeight: 600,
            background: 'rgba(0,229,195,0.15)',
            padding: '1px 6px', borderRadius: '3px',
            color: colors.accent, textTransform: 'none',
            letterSpacing: 'normal',
          }}>Preview Mode</span>}
        </span>
        <span style={{
          transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.2s',
          fontSize: '0.6rem',
        }}>▼</span>
      </button>

      {/* Sandbox Content */}
      {isOpen && (
        <div style={{ padding: '0 12px 12px' }}>
          {/* Option Selector */}
          <div style={{
            display: 'flex', gap: '6px', marginBottom: '10px',
            flexWrap: 'wrap',
          }}>
            {options.map((opt, i) => {
              const key = opt.key || opt.id || `opt_${i}`;
              const isActive = (sandboxChoice || decisionChoice) === key;
              return (
                <button
                  key={key}
                  onClick={() => setSandboxChoice(key)}
                  style={{
                    padding: '5px 10px',
                    borderRadius: '6px',
                    border: `1px solid ${isActive ? colors.accent : 'rgba(255,255,255,0.08)'}`,
                    background: isActive ? 'rgba(0,229,195,0.12)' : 'rgba(255,255,255,0.03)',
                    color: isActive ? colors.accent : colors.text,
                    fontSize: '0.72rem',
                    fontWeight: isActive ? 700 : 500,
                    cursor: 'pointer',
                    transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                    maxWidth: '180px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {opt.label || opt.title || `Option ${String.fromCharCode(65 + i)}`}
                </button>
              );
            })}
          </div>

          {/* Impact Preview Grid */}
          {activeEstimate ? (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '6px',
            }}>
              {[
                {
                  label: '💰 Treasury',
                  current: fmt$(treasury),
                  delta: activeEstimate.treasury,
                  projected: fmt$(activeEstimate.projected.treasury),
                  color: activeEstimate.treasury >= 0 ? colors.positive : colors.negative,
                },
                {
                  label: '🌍 Reputation',
                  current: reputation.toFixed(0),
                  delta: activeEstimate.reputation,
                  projected: activeEstimate.projected.reputation.toFixed(0),
                  color: activeEstimate.reputation >= 0 ? colors.positive : colors.negative,
                },
                {
                  label: '🏭 CO₂',
                  current: tco2e.toLocaleString(),
                  delta: activeEstimate.carbon,
                  projected: activeEstimate.projected.carbon.toLocaleString(),
                  color: activeEstimate.carbon <= 0 ? colors.positive : colors.negative,
                },
                {
                  label: '📈 EBITDA',
                  current: fmt$(ebitda),
                  delta: activeEstimate.ebitda,
                  projected: fmt$(activeEstimate.projected.ebitda),
                  color: activeEstimate.ebitda >= 0 ? colors.positive : colors.negative,
                },
              ].map((metric, i) => (
                <div key={i} style={{
                  padding: '8px',
                  borderRadius: '8px',
                  background: isDark ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.6)',
                  border: `1px solid ${isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)'}`,
                  textAlign: 'center',
                }}>
                  <div style={{
                    fontSize: '0.68rem', color: colors.muted,
                    fontWeight: 700, textTransform: 'uppercase',
                    letterSpacing: '0.06em', marginBottom: '3px',
                  }}>{metric.label}</div>
                  <div style={{
                    fontSize: '0.72rem', fontWeight: 800,
                    color: colors.text,
                    fontFamily: "'JetBrains Mono', monospace",
                  }}>{metric.current}</div>
                  <div style={{
                    fontSize: '0.68rem', fontWeight: 700,
                    color: metric.color,
                    marginTop: '2px',
                  }}>
                    {metric.delta > 0 ? '▲' : metric.delta < 0 ? '▼' : '—'}{' '}
                    {metric.delta !== 0 ? (metric.delta > 0 ? '+' : '') + (typeof metric.delta === 'number' && Math.abs(metric.delta) >= 1000 ? fmt$(metric.delta) : metric.delta.toFixed(1)) : '0'}
                  </div>
                  <div style={{
                    fontSize: '0.68rem', color: colors.accent,
                    marginTop: '2px', fontWeight: 600,
                  }}>→ {metric.projected}</div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{
              textAlign: 'center', padding: '12px',
              fontSize: '0.72rem', color: colors.muted,
            }}>
              Select an option above to preview estimated outcomes
            </div>
          )}

          {/* Disclaimer */}
          <div style={{
            marginTop: '8px',
            fontSize: '0.68rem', color: colors.muted,
            textAlign: 'center', fontStyle: 'italic',
            lineHeight: 1.4,
          }}>
            ⚡ Projections are estimates. Actual outcomes depend on market dynamics, competitor actions, and systemic risk events.
          </div>
        </div>
      )}
    </div>
  );
}
