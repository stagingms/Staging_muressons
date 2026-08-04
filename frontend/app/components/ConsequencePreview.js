/**
 * ConsequencePreview.js — Pre-commit analysis panel (PHASE-3)
 * Shows projected impacts of the current decision before committing.
 * Integrates with the What-If terminal valuation engine.
 */
import React, { useMemo } from 'react';
import styles from './ConsequencePreview.module.css';
import { currencySymbol, money } from '../utils/format';

const IMPACT_ICONS = {
  treasury: '💰', reputation: '⭐', social_license: '🤝', carbon_intensity: '🏭',
  governance_risk: '🏛️', natural_capital_debt: '🌿', burnout: '🔥', wacc: '📊',
  mr_projection: '🎯', strike_risk: '✊', tipping_proximity: '⚠️',
};

/** Detect whether a key represents a monetary value (large absolute scale) */
const isMonetaryKey = (k) =>
  k.includes('treasury') || k.includes('revenue') || k.includes('cost');

function ImpactBar({ label, value, maxValue = 20, isPositive }) {
  const width = Math.min(Math.abs(value) / maxValue * 100, 100);
  const color = isPositive ? '#10b981' : '#ef4444';
  return (
    <div className={styles.impactRow}>
      <span className={styles.impactLabel}>{IMPACT_ICONS[label] || '•'} {label.replace(/_/g, ' ')}</span>
      <div className={styles.impactBarTrack}>
        <div className={styles.impactBarFill} style={{
          width: `${width}%`,
          background: `linear-gradient(90deg, ${color}80, ${color})`,
          marginLeft: isPositive ? '50%' : `${50 - width}%`,
        }} />
        <div className={styles.impactBarCenter} />
      </div>
      <span className={styles.impactValue} style={{ color }}>
        {value > 0 ? '+' : ''}{typeof value === 'number' ? (
          Math.abs(value) >= 1_000 ? money(value) :
          value.toFixed(1)
        ) : value}
      </span>
    </div>
  );
}

/** Map tier to proximity percentage (how close to tipping, 0 = safe, 100 = tipped) */
const TIER_PROXIMITY = { none: 10, safe: 10, warning: 50, stressed: 80, tipped: 100 };

function TippingProximity({ dimension, tier, metrics }) {
  const colors = {
    none: '#10b981', safe: '#10b981',
    warning: '#f59e0b', stressed: '#ef4444', tipped: '#7f1d1d',
  };
  const proximity = TIER_PROXIMITY[tier] || 10;
  const tierLabel = tier === 'none' ? 'safe' : tier;

  // Build a compact metrics tooltip string
  let metricsHint = '';
  if (metrics) {
    if (dimension === 'climate') metricsHint = `CI: ${metrics.ci ?? '—'} · EHI: ${metrics.ehi ?? '—'}`;
    if (dimension === 'social') metricsHint = `SLO: ${metrics.slo ?? '—'} · Burn: ${metrics.burnout ?? '—'}`;
    if (dimension === 'financial') metricsHint = `Covenant: ${metrics.covenant ?? '—'}`;
  }

  return (
    <div className={styles.tippingRow}>
      <span className={styles.tippingLabel}>{dimension}</span>
      <div className={styles.tippingTrack} title={metricsHint}>
        <div className={styles.tippingFill} style={{
          width: `${proximity}%`,
          background: colors[tier] || colors.none,
          transition: 'width 0.6s ease-out, background 0.3s ease',
        }} />
      </div>
      <span className={styles.tippingTier} style={{ color: colors[tier] || colors.none }}>
        {tierLabel}
      </span>
    </div>
  );
}

export default function ConsequencePreview({
  selectedOption = null,
  optionConfig = {},
  currentState = {},
  buStates = [],
  tippingState = {},
  whatIfResult = null,
}) {
  const impacts = useMemo(() => {
    if (!optionConfig?.impacts) return [];
    const imp = optionConfig.impacts;
    return Object.entries(imp)
      .filter(([k, v]) => typeof v === 'number' && v !== 0 && !k.includes('factor') && !k.includes('flag'))
      .map(([k, v]) => ({
        key: k,
        value: v,
        isPositive: k.includes('reputation') || k.includes('social_license') ?
          v > 0 : k.includes('risk') || k.includes('debt') || k.includes('intensity') ?
          v < 0 : v > 0,
        isMoney: isMonetaryKey(k),
      }))
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
  }, [optionConfig]);

  // Compute separate maxValues for monetary and score-based impacts
  // so that small-magnitude score deltas are visible alongside large monetary values
  const { maxMoney, maxScore } = useMemo(() => {
    const moneyVals = impacts.filter(i => i.isMoney).map(i => Math.abs(i.value));
    const scoreVals = impacts.filter(i => !i.isMoney).map(i => Math.abs(i.value));
    return {
      maxMoney: Math.max(...moneyVals, 1),
      maxScore: Math.max(...scoreVals, 1),
    };
  }, [impacts]);

  const stakeholderReactions = useMemo(() => {
    if (!optionConfig?.impacts) return [];
    const reactions = [];
    const imp = optionConfig.impacts;
    if (imp.reputation_delta && imp.reputation_delta < -10) {
      reactions.push({ npc: 'Activist Investor', reaction: 'Hostile', icon: '🦅', severity: 'high' });
    }
    if (imp.governance_risk_delta && imp.governance_risk_delta > 5) {
      reactions.push({ npc: 'Regulator', reaction: 'Monitoring', icon: '🏛️', severity: 'medium' });
    }
    if (imp.social_license_delta && imp.social_license_delta < -10) {
      reactions.push({ npc: 'Community', reaction: 'Concerned', icon: '👥', severity: 'high' });
    }
    if (imp.strike_risk) {
      reactions.push({ npc: 'Workforce', reaction: 'Strike Risk', icon: '✊', severity: 'critical' });
    }
    return reactions;
  }, [optionConfig]);

  // Extract tipping dimensions — handle both flattened (tipping_state only)
  // and full systemic_tipping result objects
  const tippingDimensions = useMemo(() => {
    // Full object: { tipping_state: {...}, dimensions: {...} }
    const dims = tippingState?.dimensions || {};
    const state = tippingState?.tipping_state || tippingState || {};
    return ['climate', 'social', 'financial'].map(dim => ({
      dim,
      tier: state[`${dim}_tier`] || 'none',
      metrics: dims[dim] || null,
    }));
  }, [tippingState]);

  if (!selectedOption) {
    return (
      <div className={styles.previewContainer} id="consequence-preview">
        <div className={styles.emptyState}>
          <span className={styles.emptyIcon}>🔮</span>
          <p>Select a decision option to preview its consequences</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.previewContainer} id="consequence-preview">
      <div className={styles.previewHeader}>
        <h3 className={styles.previewTitle}>🔮 Consequence Preview</h3>
        <span className={styles.optionBadge}>{optionConfig?.label || selectedOption}</span>
      </div>

      {/* Impact Bars */}
      <div className={styles.section}>
        <h4 className={styles.sectionTitle}>Projected Impacts</h4>
        {impacts.map(imp => (
          <ImpactBar key={imp.key} label={imp.key} value={imp.value}
            maxValue={imp.isMoney ? maxMoney : maxScore}
            isPositive={imp.isPositive} />
        ))}
      </div>

      {/* Stakeholder Reactions */}
      {stakeholderReactions.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Stakeholder Reactions</h4>
          {stakeholderReactions.map((r, i) => (
            <div key={i} className={`${styles.reactionRow} ${styles[`severity_${r.severity}`]}`}>
              <span>{r.icon}</span>
              <span className={styles.reactionNpc}>{r.npc}</span>
              <span className={styles.reactionAction}>{r.reaction}</span>
            </div>
          ))}
        </div>
      )}

      {/* Tipping Point Proximity */}
      <div className={styles.section}>
        <h4 className={styles.sectionTitle}>Tipping Point Proximity</h4>
        {tippingDimensions.map(({ dim, tier, metrics }) => (
          <TippingProximity key={dim} dimension={dim}
            tier={tier}
            metrics={metrics} />
        ))}
      </div>

      {/* M_R Projection */}
      {whatIfResult && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Terminal Valuation Impact</h4>
          <div className={styles.mrProjection}>
            <div className={styles.mrRow}>
              <span>Current M_R:</span>
              <span className={styles.mrValue}>{whatIfResult.baseline?.mr?.toFixed(2) || '—'}</span>
            </div>
            <div className={styles.mrRow}>
              <span>Projected M_R:</span>
              <span className={styles.mrValue}>{whatIfResult.what_if?.mr?.toFixed(2) || '—'}</span>
            </div>
            <div className={styles.mrRow}>
              <span>TV Delta:</span>
              <span className={styles.mrDelta} style={{
                color: (whatIfResult.delta?.tv_change || 0) >= 0 ? '#10b981' : '#ef4444'
              }}>
                {whatIfResult.delta?.tv_change >= 0 ? '+' : ''}
               {currencySymbol()}{((whatIfResult.delta?.tv_change || 0) / 1_000_000).toFixed(1)}M
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Climate Framing Badge */}
      {optionConfig?.climate_framing && (
        <div className={styles.framingBadge}>
          🌡️ {optionConfig.climate_framing}
        </div>
      )}
    </div>
  );
}
