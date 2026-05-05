/**
 * ConsequencePreview.js — Pre-commit analysis panel (PHASE-3)
 * Shows projected impacts of the current decision before committing.
 * Integrates with the What-If terminal valuation engine.
 */
import React, { useMemo } from 'react';
import styles from './ConsequencePreview.module.css';

const IMPACT_ICONS = {
  treasury: '💰', reputation: '⭐', social_license: '🤝', carbon_intensity: '🏭',
  governance_risk: '🏛️', natural_capital_debt: '🌿', burnout: '🔥', wacc: '📊',
  mr_projection: '🎯', strike_risk: '✊', tipping_proximity: '⚠️',
};

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
          Math.abs(value) >= 1_000_000 ? `$${(value / 1_000_000).toFixed(1)}M` :
          Math.abs(value) >= 1_000 ? `$${(value / 1_000).toFixed(0)}K` :
          value.toFixed(1)
        ) : value}
      </span>
    </div>
  );
}

function TippingProximity({ dimension, tier, distance }) {
  const colors = {
    none: '#10b981', safe: '#10b981',
    warning: '#f59e0b', stressed: '#ef4444', tipped: '#7f1d1d',
  };
  return (
    <div className={styles.tippingRow}>
      <span className={styles.tippingLabel}>{dimension}</span>
      <div className={styles.tippingTrack}>
        <div className={styles.tippingFill} style={{
          width: `${Math.min(100, Math.max(0, 100 - (distance || 50)))}%`,
          background: colors[tier] || colors.none,
        }} />
      </div>
      <span className={styles.tippingTier} style={{ color: colors[tier] || colors.none }}>
        {tier || 'safe'}
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
      .filter(([k, v]) => typeof v === 'number' && v !== 0 && !k.includes('factor') && !k.includes('risk') && !k.includes('flag'))
      .map(([k, v]) => ({
        key: k,
        value: v,
        isPositive: k.includes('reputation') || k.includes('social_license') ?
          v > 0 : k.includes('risk') || k.includes('debt') || k.includes('intensity') ?
          v < 0 : v > 0,
      }))
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
  }, [optionConfig]);

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
            maxValue={Math.max(...impacts.map(i => Math.abs(i.value)), 1)}
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
        {['climate', 'social', 'financial'].map(dim => (
          <TippingProximity key={dim} dimension={dim}
            tier={tippingState?.[`${dim}_tier`] || 'none'}
            distance={tippingState?.dimensions?.[dim]?.distance} />
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
                ${((whatIfResult.delta?.tv_change || 0) / 1_000_000).toFixed(1)}M
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
