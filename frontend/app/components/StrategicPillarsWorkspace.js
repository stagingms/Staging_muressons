'use client';
import { useState, useEffect, useMemo, useCallback } from 'react';
import { createPortal } from 'react-dom';
import styles from './StrategicPillarsWorkspace.module.css';
import { DETAILED_DESCRIPTIONS } from '../utils/detailedDescriptions';

const AREA_ICONS = {
  energy: '⚡',
  operations: '🏭',
  supply_chain: '🔗',
  offsetting: '🌱',
};

export default function StrategicPillarsWorkspace({
  sessionId,
  roundNumber,
  onSelectionsChange,
  apiBase,
  treasury,
}) {
  const [config, setConfig] = useState(null);
  const [selections, setSelections] = useState({});
  const [loading, setLoading] = useState(true);
  const [expandedArea, setExpandedArea] = useState(null);
  const [hoveredOpt, setHoveredOpt] = useState(null);

  // Fetch pillar config for current round
  useEffect(() => {
    if (!roundNumber) return;
    setLoading(true);
    fetch(`${apiBase}/api/simulations/pillar-config/${roundNumber}`)
      .then((r) => r.json())
      .then((data) => {
        setConfig(data);
        setLoading(false);
        // Reset selections when round changes
        setSelections({});
      })
      .catch((err) => {
        console.error('Failed to fetch pillar config:', err);
        setLoading(false);
      });
  }, [roundNumber, apiBase]);

  // Notify parent of selection changes
  useEffect(() => {
    if (onSelectionsChange) {
      onSelectionsChange(selections);
    }
  }, [selections, onSelectionsChange]);

  const handleSelect = useCallback((areaKey, optionKey) => {
    setSelections((prev) => {
      const next = { ...prev };
      if (next[areaKey] === optionKey) {
        delete next[areaKey];
      } else {
        next[areaKey] = optionKey;
      }
      return next;
    });
  }, []);

  // Calculate aggregated cost
  const aggregation = useMemo(() => {
    if (!config || !config.areas) return { totalCost: 0, impacts: {} };

    let totalCost = 0;
    const impacts = {};

    for (const [areaKey, optionKey] of Object.entries(selections)) {
      const area = config.areas[areaKey];
      if (!area) continue;
      const option = area.options[optionKey];
      if (!option) continue;

      totalCost += option.cost || 0;
      for (const [k, v] of Object.entries(option.impacts || {})) {
        impacts[k] = (impacts[k] || 0) + v;
      }
    }

    return { totalCost, impacts };
  }, [config, selections]);

  const selectedCount = Object.keys(selections).length;
  const areaCount = config?.areas ? Object.keys(config.areas).length : 4;

  if (loading) {
    return (
      <div className={styles.workspace}>
        <div className={styles.loadingPulse}>
          <div className={styles.loadingIcon}>🎛️</div>
          <p>Loading strategic options...</p>
        </div>
      </div>
    );
  }

  if (!config || !config.areas) {
    return (
      <div className={styles.workspace}>
        <div className={styles.errorState}>
          <span>⚠️</span>
          <p>No pillar configuration available for this round.</p>
        </div>
      </div>
    );
  }

  const formatCurrency = (v) => {
    if (v === 0) return '$0';
    const sign = v > 0 ? '+' : '';
    return `${sign}$${Math.abs(v / 1_000_000).toFixed(1)}M`;
  };

  const impactLabels = {
    reputation: { label: 'Reputation', icon: '📊', positive: true },
    carbon_intensity_delta: { label: 'Carbon', icon: '🏭', positive: false },
    natural_capital_debt_delta: { label: 'NCD', icon: '🌍', positive: false },
    social_license_delta: { label: 'Social License', icon: '🤝', positive: true },
    governance_risk_delta: { label: 'Gov Risk', icon: '⚖️', positive: false },
    water_dependency_delta: { label: 'Water', icon: '💧', positive: false },
  };

  return (
    <div className={styles.workspace}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerTitle}>
          <span className={styles.headerIcon}>🎛️</span>
          <div>
            <h2>{config.title}</h2>
            <p>{config.description}</p>
          </div>
        </div>
        <div className={styles.headerBadge}>
          {selectedCount}/{areaCount} Areas
        </div>
      </div>

      {/* Pillar Tiles */}
      <div className={styles.pillarsGrid}>
        {Object.entries(config.areas).map(([areaKey, area]) => {
          const isExpanded = expandedArea === areaKey;
          const selectedOption = selections[areaKey];

          return (
            <div
              key={areaKey}
              className={`${styles.pillarTile} ${selectedOption ? styles.pillarSelected : ''} ${isExpanded ? styles.pillarExpanded : ''}`}
            >
              {/* Tile Header */}
              <div
                className={styles.pillarHeader}
                onClick={() => setExpandedArea(isExpanded ? null : areaKey)}
              >
                <div className={styles.pillarIcon}>
                  {AREA_ICONS[areaKey] || area.icon || '📌'}
                </div>
                <div className={styles.pillarLabel}>
                  <h3>{area.label}</h3>
                  {selectedOption && (
                    <span className={styles.selectedTag}>
                      ✓ {area.options[selectedOption]?.title}
                    </span>
                  )}
                </div>
                <div className={styles.expandChevron}>
                  {isExpanded ? '▲' : '▼'}
                </div>
              </div>

              {/* Options Panel */}
              {isExpanded && (
                <div className={styles.optionsPanel}>
                  {Object.entries(area.options).map(([optKey, opt]) => {
                    const isSelected = selectedOption === optKey;

                    return (
                      <div
                        key={optKey}
                        className={`${styles.optionCard} ${isSelected ? styles.optionSelected : ''}`}
                        onClick={() => handleSelect(areaKey, optKey)}
                        onMouseEnter={() => setHoveredOpt({
                          title: opt.title,
                          description: opt.description,
                          detailedDescription: DETAILED_DESCRIPTIONS.pillars?.[roundNumber]?.[areaKey]?.[optKey] || opt.detailed_description || opt.description
                        })}
                        onMouseLeave={() => setHoveredOpt(null)}
                      >
                        <div className={styles.optionHeader}>
                          <span className={styles.optionTitle}>{opt.title}</span>
                          <span
                            className={`${styles.optionCost} ${opt.cost > 0 ? styles.costPositive : opt.cost < 0 ? styles.costNegative : ''}`}
                          >
                            {formatCurrency(opt.cost)}
                          </span>
                        </div>
                        <p className={styles.optionDesc}>{opt.description}</p>
                        {opt.impacts && Object.keys(opt.impacts).length > 0 && (
                          <div className={styles.optionImpacts}>
                            {Object.entries(opt.impacts).map(([k, v]) => {
                              const meta = impactLabels[k] || { label: k, icon: '📋', positive: true };
                              const isGood = meta.positive ? v > 0 : v < 0;

                              return (
                                <span
                                  key={k}
                                  className={`${styles.impactBadge} ${isGood ? styles.impactGood : styles.impactBad}`}
                                >
                                  {meta.icon} {v > 0 ? '+' : ''}{v} {meta.label}
                                </span>
                              );
                            })}
                          </div>
                        )}
                        {isSelected && <div className={styles.selectedIndicator}>✓ SELECTED</div>}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Cost Summary Bar */}
      <div className={styles.summaryBar}>
        <div className={styles.summaryLeft}>
          <span className={styles.summaryLabel}>Total Round Cost</span>
          <span
            className={`${styles.summaryValue} ${aggregation.totalCost > 0 ? styles.costPositive : styles.costNegative}`}
          >
            {formatCurrency(aggregation.totalCost)}
          </span>
        </div>

        <div className={styles.summaryImpacts}>
          {Object.entries(aggregation.impacts).map(([k, v]) => {
            if (v === 0) return null;
            const meta = impactLabels[k] || { label: k, icon: '📋', positive: true };
            const isGood = meta.positive ? v > 0 : v < 0;

            return (
              <span
                key={k}
                className={`${styles.summaryImpact} ${isGood ? styles.impactGood : styles.impactBad}`}
              >
                {meta.icon} {v > 0 ? '+' : ''}{v}
              </span>
            );
          })}
        </div>

        <div className={styles.summaryRight}>
          {treasury !== undefined && (
            <span className={styles.treasuryAfter}>
              Treasury After: {formatCurrency(treasury + aggregation.totalCost)}
            </span>
          )}
        </div>
      </div>

      {/* Strategic Breakdown Panel */}
      <div className={styles.breakdownPanel}>
        <div className={styles.breakdownLabels}>
          <span className={styles.breakdownIcon}>🔍</span>
          <span className={styles.breakdownTitle}>STRATEGIC BREAKDOWN</span>
        </div>
        <div className={styles.breakdownContent}>
          {hoveredOpt ? (
            <p><strong>{hoveredOpt.title}:</strong> {hoveredOpt.detailedDescription || hoveredOpt.description}</p>
          ) : (
            <p className={styles.breakdownPlaceholder}>Hover over a strategic option above to preview its detailed implications.</p>
          )}
        </div>
      </div>
    </div>
  );
}
