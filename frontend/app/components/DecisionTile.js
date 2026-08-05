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

/* `color` was carried on each entry and read by nothing — four raw hues held
   alive by a field no JSX in this file references. Removed rather than
   tokenised: the cheapest way to pay a debt is to delete its cause. */
const OPT_META = {
  option_a: { icon: '⚡', label: 'OPTION A' },
  option_b: { icon: '⚖️', label: 'OPTION B' },
  option_c: { icon: '🛡️', label: 'OPTION C' },
};

/**
 * Build a one-line "projected trade-off" from an option's impacts, so the
 * player reasons about the choice BEFORE committing (the pedagogical goal).
 * Favourable directions: treasury > 0 (frees cash), reputation > 0, carbon < 0.
 * Uses only data already passed to the tile — no new fetch, no state.
 *
 * THE SIGN. `round_configs.py` writes an option's cost as a NEGATIVE treasury
 * impact — of the 26 treasury impacts in that file, 22 are negative and none
 * are positive, because every priced option in the game is an expense.
 * `round_logic.py:1586` then converts it (`abs(t) if t < 0 else -t`) before
 * subtracting. So negative means SPEND, and this file had it backwards in
 * three places: here, the screen-reader description, and the cost colour.
 * Every priced option announced its cost as a gain.
 *
 * The same inversion was found and fixed in the projected-impact chip and the
 * KPI belt; it survived here because nothing was looking at this file.
 */
function buildTradeoff(impacts) {
  if (!impacts) return null;
  const good = [], bad = [];
  const t = impacts.treasury, r = impacts.reputation, c = impacts.carbon;
  if (typeof t === 'number' && t !== 0) (t > 0 ? good : bad).push(t > 0 ? 'frees cash' : 'spends cash');
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
  const meta = OPT_META[optId] || { icon: '📌', label: optId.toUpperCase() };
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
      /* A11Y-F4 (WCAG 1.3.1, 4.1.2): role="button" is children-presentational
         per WAI-ARIA, so EVERYTHING inside this tile — the description, the
         projected trade-off, the cost, the $0-CapEx warning — was stripped from
         the accessibility tree. A screen-reader user made the central decision
         of the product hearing only "Option A: Retrofit the Lyon plant".
         aria-describedby is computed from the referenced node's text content and
         is NOT suppressed by children-presentational, so it restores exactly the
         reasoning material a sighted player gets. */
      aria-describedby={`tile-desc-${optId}`}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect?.(optId); } }}
    >
      {/* A11Y-F4: the same content a sighted player reads, flattened into one
          describable node. Visually hidden — this is a parallel channel, not a
          duplicate on screen. */}
      <span
        id={`tile-desc-${optId}`}
        style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap' }}
      >
        {(() => {
          const parts = [detailedDesc || option.description];
          const to = buildTradeoff(option.impacts);
          if (to) {
            if (to.good.length) parts.push(`Projected upside: ${to.good.join(', ')}.`);
            if (to.bad.length) parts.push(`Projected downside: ${to.bad.join(', ')}.`);
          }
          if (typeof costVal === 'number' && costVal !== 0 && fmtCurrency) {
            /* SIGN: negative = spend. This said "Frees ₹30M" for a ₹30M
               expense — the inversion above, in the screen-reader channel,
               where nobody could see it was wrong. */
            parts.push(`${costVal > 0 ? 'Frees' : 'Costs'} ${fmtCurrency(Math.abs(costVal))}.`);
          } else if (costVal === 0) {
            parts.push('No capital expenditure.');
          }
          parts.push(isActive ? 'Currently selected.' : 'Not selected.');
          return parts.filter(Boolean).join(' ');
        })()}
      </span>
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
            marginTop: 4, fontSize: 'var(--type-caption)', lineHeight: 1.5,
            display: 'flex', flexWrap: 'wrap', gap: '2px 8px',
          }} title="Projected — commit and see next round whether you were right.">
            {to.good.length > 0 && (
              <span style={{ color: 'var(--positive-text)', fontWeight: 600 }}>✓ {to.good.join(', ')}</span>
            )}
            {to.bad.length > 0 && (
              <span style={{ color: 'var(--caution-text)', fontWeight: 600 }}>✗ {to.bad.join(', ')}</span>
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
            <span style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)', fontWeight: 600 }}>💰 Cost</span>
            <span style={{
              fontSize: 'var(--type-caption)', fontWeight: 800,
              /* SIGN: negative = spend, so negative is the RED one. This was
                 the visible half of the inversion — 22 of the 25 priced
                 options rendered their cost in green. */
              color: costVal > 0 ? 'var(--positive-text)' : 'var(--danger-text)',
            }}>
              {fmtCurrency(costVal)}
            </span>
          </div>
          <div style={{
            height: 4, background: 'var(--neutral-soft)', borderRadius: 2,
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${costBarPct}%`, height: '100%',
              background: 'var(--accent)', borderRadius: 2,
              transition: 'width 0.3s ease',
            }} />
          </div>
        </div>
      ) : (
        /* Zero-cost deferred risk warning */
        <div style={{ marginTop: compact ? 4 : 6, display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: 'var(--caution-text)' }}>⚠️ $0 CapEx</span>
          <span style={{ fontSize: 'var(--type-caption)', color: 'var(--caution-text)' }}>— deferred risk</span>
        </div>
      )}

      {/* Impact Preview (shown only when selected) */}
      {isActive && option.impacts && !compact && (
        <div style={{
          marginTop: 6, padding: '4px 6px', background: 'var(--neutral-faint)',
          borderRadius: 4, fontSize: 'var(--type-caption)', lineHeight: 1.6,
        }}>
          {option.impacts.treasury && (
            <div style={{ display: 'flex', justifyContent: 'space-between', color: option.impacts.treasury > 0 ? 'var(--positive-text)' : 'var(--danger-text)' }}>
              <span>💰 Treasury</span>
              <span style={{ fontWeight: 700 }}>{fmtCurrency(treasury)} → {fmtCurrency(treasury + (option.impacts.treasury || 0))} {option.impacts.treasury < 0 ? '▼' : '▲'}</span>
            </div>
          )}
          {option.impacts.reputation !== undefined && (
            <div style={{ display: 'flex', justifyContent: 'space-between', color: option.impacts.reputation > 0 ? 'var(--positive-text)' : 'var(--danger-text)' }}>
              <span>🌍 Reputation</span>
              <span style={{ fontWeight: 700 }}>{reputation} → {reputation + (option.impacts.reputation || 0)} {option.impacts.reputation > 0 ? '▲' : '▼'}</span>
            </div>
          )}
          {option.impacts.carbon !== undefined && (
            <div style={{ display: 'flex', justifyContent: 'space-between', color: option.impacts.carbon < 0 ? 'var(--positive-text)' : 'var(--danger-text)' }}>
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

