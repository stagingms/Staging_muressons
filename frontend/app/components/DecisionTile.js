'use client';
import React from 'react';
import styles from './ExecutiveCockpit.module.css';
import PillarSelectDropdown from './PillarSelectDropdown';

/**
 * DecisionTile — Shared decision tile component used by both
 * Focus Mode overlay and Dashboard Mode.
 *
 * Phase 1.4 Deduplication: Replaces duplicate rendering logic that
 * previously existed in ExecutiveCockpit.js (dashboard) and
 * FocusOverlay.js (focus mode).
 *
 * Props:
 *   - optId:           'option_a' | 'option_b' | 'option_c'
 *   - option:          { title, description, impacts: { treasury, reputation, carbon } }
 *   - isActive:        boolean — currently selected
 *   - onSelect:        (optId) => void
 *   - onHover:         ({ title, desc }) => void
 *   - onLeave:         () => void
 *   - detailedDesc:    string | null — from DETAILED_DESCRIPTIONS
 *   - fmtCurrency:     (v) => string
 *   - treasury:        number — current treasury for projection
 *   - reputation:      number — current reputation for projection
 *   - maxCost:         number — max cost across all options (for bar normalization)
 *   - compact:         boolean — compact mode for Focus overlay
 *   - roundNumber:     number — for round-tier styling
 */

const OPT_META = {
  option_a: { icon: '⚡', label: 'OPTION A', color: '#ef4444' },
  option_b: { icon: '⚖️', label: 'OPTION B', color: '#3b82f6' },
  option_c: { icon: '🛡️', label: 'OPTION C', color: '#16a34a' },
};

/**
 * Build a one-line "projected trade-off" from an option's impacts, so the
 * player reasons about the choice BEFORE committing (the pedagogical goal).
 * Favourable directions: treasury < 0 (frees cash), reputation > 0, carbon < 0.
 * Uses only data already passed to the tile — no new fetch, no state.
 */
function buildTradeoff(impacts) {
  if (!impacts) return null;
  const good = [], bad = [];
  const t = impacts.treasury, r = impacts.reputation, c = impacts.carbon;
  if (typeof t === 'number' && t !== 0) (t < 0 ? good : bad).push(t < 0 ? 'frees cash' : 'spends cash');
  if (typeof r === 'number' && r !== 0) (r > 0 ? good : bad).push(r > 0 ? 'lifts reputation' : 'risks reputation');
  if (typeof c === 'number' && c !== 0) (c < 0 ? good : bad).push(c < 0 ? 'cuts carbon' : 'adds carbon');
  if (!good.length && !bad.length) return null;
  return { good, bad };
}

export default function DecisionTile({
  optId,
  option,
  isActive,
  onSelect,
  onHover,
  onLeave,
  detailedDesc,
  fmtCurrency,
  treasury = 0,
  reputation = 0,
  maxCost = 1,
  compact = false,
  roundNumber = 1,
}) {
  if (!option) return null;
  const meta = OPT_META[optId] || { icon: '📌', label: optId.toUpperCase(), color: '#6366f1' };
  const costVal = option.impacts?.treasury || option.cost_impact || 0;
  const costBarPct = Math.min(100, (Math.abs(costVal) / Math.max(1, maxCost)) * 100);

  return (
    <div
      className={`${styles.decisionTile} ${isActive ? styles.decisionTileActive : ''}`}
      onClick={() => onSelect?.(optId)}
      onMouseEnter={() => onHover?.({
        title: option.title,
        desc: detailedDesc || option.description,
        regulatoryTooltip: option.regulatory_tooltip || null,
      })}
      onMouseLeave={() => onLeave?.()}
      role="button"
      tabIndex={0}
      aria-pressed={isActive}
      aria-label={`${meta.label}: ${option.title}`}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect?.(optId); } }}
    >
      {/* Header: Icon + Label */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: compact ? 2 : 4 }}>
        <span style={{ fontSize: compact ? '0.85rem' : '1rem' }}>{meta.icon}</span>
        <span className={styles.tileLabel} style={{ margin: 0 }}>
          {meta.label}
        </span>
      </div>

      {/* Title */}
      <div className={styles.tileTitle}>{option.title}</div>

      {/* Description — hidden in compact mode */}
      {!compact && (
        <p className={styles.tileDesc}>{option.description}</p>
      )}

      {/* Projected trade-off (B1) — a testable hypothesis shown BEFORE commit */}
      {!compact && (() => {
        const to = buildTradeoff(option.impacts);
        if (!to) return null;
        return (
          <div style={{
            marginTop: 4, fontSize: '0.7rem', lineHeight: 1.5,
            display: 'flex', flexWrap: 'wrap', gap: '2px 8px',
          }} title="Projected — commit and see next round whether you were right.">
            {to.good.length > 0 && (
              <span style={{ color: '#16a34a', fontWeight: 600 }}>✓ {to.good.join(', ')}</span>
            )}
            {to.bad.length > 0 && (
              <span style={{ color: '#d97706', fontWeight: 600 }}>✗ {to.bad.join(', ')}</span>
            )}
          </div>
        );
      })()}

      {/* Cost Bar */}
      {costVal ? (
        <div style={{ marginTop: compact ? 4 : 6 }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            marginBottom: 3,
          }}>
            <span style={{ fontSize: '0.75rem', color: '#8899a6', fontWeight: 600 }}>💰 Cost</span>
            <span style={{
              fontSize: '0.75rem', fontWeight: 800,
              color: costVal < 0 ? '#16a34a' : '#ef4444',
            }}>
              {fmtCurrency(costVal)}
            </span>
          </div>
          <div style={{
            height: 4, background: '#e2e8f0', borderRadius: 2,
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${costBarPct}%`, height: '100%',
              background: '#6366f1', borderRadius: 2,
              transition: 'width 0.3s ease',
            }} />
          </div>
        </div>
      ) : (
        /* Zero-cost deferred risk warning */
        <div style={{ marginTop: compact ? 4 : 6, display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f59e0b' }}>⚠️ $0 CapEx</span>
          <span style={{ fontSize: '0.72rem', color: '#92400e' }}>— deferred risk</span>
        </div>
      )}

      {/* Impact Preview (shown only when selected) */}
      {isActive && option.impacts && !compact && (
        <div style={{
          marginTop: 6, padding: '4px 6px', background: '#f8fafc',
          borderRadius: 4, fontSize: '0.72rem', lineHeight: 1.6,
        }}>
          {option.impacts.treasury && (
            <div style={{ display: 'flex', justifyContent: 'space-between', color: option.impacts.treasury < 0 ? '#16a34a' : '#ef4444' }}>
              <span>💰 Treasury</span>
              <span style={{ fontWeight: 700 }}>{fmtCurrency(treasury)} → {fmtCurrency(treasury + (option.impacts.treasury || 0))} {option.impacts.treasury < 0 ? '▼' : '▲'}</span>
            </div>
          )}
          {option.impacts.reputation !== undefined && (
            <div style={{ display: 'flex', justifyContent: 'space-between', color: option.impacts.reputation > 0 ? '#16a34a' : '#ef4444' }}>
              <span>🌍 Reputation</span>
              <span style={{ fontWeight: 700 }}>{reputation} → {reputation + (option.impacts.reputation || 0)} {option.impacts.reputation > 0 ? '▲' : '▼'}</span>
            </div>
          )}
          {option.impacts.carbon !== undefined && (
            <div style={{ display: 'flex', justifyContent: 'space-between', color: option.impacts.carbon < 0 ? '#16a34a' : '#ef4444' }}>
              <span>🏭 Carbon</span>
              <span style={{ fontWeight: 700 }}>{option.impacts.carbon > 0 ? '+' : ''}{option.impacts.carbon}t</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * PillarTile — Shared pillar tile for multi_toggles paradigm.
 * Also used by both Focus Mode and Dashboard Mode.
 * Uses PillarSelectDropdown for hover tooltip support on options.
 */
export function PillarTile({
  areaKey,
  area,
  selectedOpt,
  onSelect,
  onHover,
  onLeave,
  areaIcon,
  fmtCurrency,
  detailedDescs,
  roundNumber,
  compact = false,
}) {
  if (!area) return null;
  return (
    <div
      className={`${styles.pillarTile} ${selectedOpt ? styles.pillarTileActive : ''}`}
    >
      <div className={styles.pillarIcon}>{areaIcon || '📌'}</div>
      <div className={styles.pillarLabel}>{area.label}</div>
      <PillarSelectDropdown
        options={area.options || {}}
        value={selectedOpt || null}
        onChange={(optKey) => onSelect?.(areaKey, optKey)}
        fmtCurrency={fmtCurrency}
        detailedDescs={detailedDescs?.[areaKey] || {}}
      />
    </div>
  );
}

