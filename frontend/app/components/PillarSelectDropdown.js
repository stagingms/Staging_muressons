'use client';
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import styles from './PillarSelectDropdown.module.css';
import { currencySymbol } from '../utils/format';

/**
 * PillarSelectDropdown — custom dropdown for strategic-pillar options with a
 * rich hover card (description, cost, impact badges) beside each option.
 *
 * July 2026 fixes:
 *
 *  1. CLIPPING. The menu and hover card were absolutely positioned inside the
 *     tile, but the decision surface scrolls (.content has overflow-y:auto and
 *     .panel has overflow:hidden), so both were clipped by the scroll
 *     container — the hover card was rendered but invisible, and long menus
 *     were cut off at the card edge. Both layers are now PORTALLED to
 *     document.body with fixed positioning anchored to the trigger, which is
 *     what the previously-unused createPortal import was there for.
 *
 *  2. DESCRIPTION KEY MISMATCH. detailedDescriptions stores pillar copy under
 *     positional keys (option_1, option_2, option_3) while the engine's option
 *     keys are semantic (renewable_ppa, blockchain_trace, …), so every lookup
 *     missed and players only ever saw the short one-line description. The
 *     lookup now tries the semantic key first, then falls back to the
 *     positional key for that option's index.
 *
 * Props:
 *   - options:        Object { optKey: { title, description, cost, impacts } }
 *   - value:          string | null — currently selected optKey
 *   - onChange:       (optKey | null) => void
 *   - placeholder:    string — shown when no value selected
 *   - fmtCurrency:    (v) => string
 *   - detailedDescs:  Object { optKey | option_N: string }
 *   - impactLabels:   Object { impactKey: { label, icon, positive } }
 */

const DEFAULT_IMPACT_LABELS = {
  reputation: { label: 'Reputation', icon: '📊', positive: true },
  carbon_intensity_delta: { label: 'Carbon', icon: '🏭', positive: false },
  natural_capital_debt_delta: { label: 'NCD', icon: '🌍', positive: false },
  social_license_delta: { label: 'Social License', icon: '🤝', positive: true },
  governance_risk_delta: { label: 'Gov Risk', icon: '⚖️', positive: false },
  water_dependency_delta: { label: 'Water', icon: '💧', positive: false },
  burnout_delta: { label: 'Burnout', icon: '🔥', positive: false },
  treasury: { label: 'Treasury', icon: '💰', positive: false },
  carbon: { label: 'Carbon', icon: '🏭', positive: false },
};

const MENU_MAX_W = 340;
const CARD_W = 300;
const GAP = 10;

export default function PillarSelectDropdown({
  options = {},
  value,
  onChange,
  placeholder = '— Select —',
  fmtCurrency,
  detailedDescs = {},
  impactLabels = DEFAULT_IMPACT_LABELS,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [hovered, setHovered] = useState(null);      // { key, rect }
  const [menuRect, setMenuRect] = useState(null);    // fixed coords for the menu
  const wrapperRef = useRef(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);

  const optionKeys = useMemo(() => Object.keys(options), [options]);

  /** Description lookup: semantic key first, then the positional option_N key
   *  the detailed-description file actually uses. */
  const describe = useCallback((optKey) => {
    const idx = optionKeys.indexOf(optKey);
    return (
      detailedDescs[optKey] ||
      (idx >= 0 ? detailedDescs[`option_${idx + 1}`] : undefined) ||
      options[optKey]?.description ||
      'No description available.'
    );
  }, [detailedDescs, options, optionKeys]);

  /** Anchor the portalled menu to the trigger, flipping up when short of room. */
  const positionMenu = useCallback(() => {
    const el = triggerRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const vh = window.innerHeight;
    const estH = Math.min(320, 44 + optionKeys.length * 36);
    const below = vh - r.bottom;
    const openUp = below < estH + 16 && r.top > below;
    setMenuRect({
      left: Math.max(8, Math.min(r.left, window.innerWidth - MENU_MAX_W - 8)),
      top: openUp ? undefined : r.bottom + 4,
      bottom: openUp ? vh - r.top + 4 : undefined,
      minWidth: r.width,
      maxHeight: Math.max(160, (openUp ? r.top : below) - 16),
    });
  }, [optionKeys.length]);

  useEffect(() => {
    if (!isOpen) { setMenuRect(null); setHovered(null); return undefined; }
    positionMenu();
    const onScrollOrResize = () => { positionMenu(); setHovered(null); };
    window.addEventListener('resize', onScrollOrResize);
    window.addEventListener('scroll', onScrollOrResize, true);
    return () => {
      window.removeEventListener('resize', onScrollOrResize);
      window.removeEventListener('scroll', onScrollOrResize, true);
    };
  }, [isOpen, positionMenu]);

  // Close on outside click — the menu now lives outside the wrapper, so both
  // subtrees must be consulted.
  useEffect(() => {
    if (!isOpen) return undefined;
    const handleClick = (e) => {
      const inWrapper = wrapperRef.current?.contains(e.target);
      const inMenu = menuRef.current?.contains(e.target);
      if (!inWrapper && !inMenu) { setIsOpen(false); setHovered(null); }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return undefined;
    const handler = (e) => {
      if (e.key === 'Escape') { setIsOpen(false); setHovered(null); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen]);

  const handleToggle = useCallback(() => {
    setIsOpen((prev) => !prev);
    setHovered(null);
  }, []);

  const handleSelect = useCallback((optKey) => {
    onChange?.(optKey || null);
    setIsOpen(false);
    setHovered(null);
  }, [onChange]);

  const selectedOption = value ? options[value] : null;
  const displayText = selectedOption
    ? `${selectedOption.title} (${fmtCurrency?.(selectedOption.cost || 0) || `${currencySymbol()}0`})`
    : placeholder;

  /** Hover card placement: right of the menu, flipping left when tight. */
  const cardStyle = useMemo(() => {
    if (!hovered?.rect) return null;
    const r = hovered.rect;
    const vw = typeof window !== 'undefined' ? window.innerWidth : 1440;
    const vh = typeof window !== 'undefined' ? window.innerHeight : 900;
    const spaceRight = vw - r.right;
    const left = spaceRight > CARD_W + GAP ? r.right + GAP : Math.max(8, r.left - CARD_W - GAP);
    return {
      position: 'fixed',
      left,
      top: Math.max(8, Math.min(r.top - 4, vh - 260)),
      width: CARD_W,
      zIndex: 20050,
      pointerEvents: 'none',
    };
  }, [hovered]);

  const hoveredOpt = hovered ? options[hovered.key] : null;

  return (
    <div className={styles.wrapper} ref={wrapperRef}>
      <button
        ref={triggerRef}
        className={`${styles.trigger} ${isOpen ? styles.triggerOpen : ''} ${value ? styles.triggerHasValue : styles.triggerPlaceholder}`}
        onClick={handleToggle}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        {displayText}
      </button>

      {/* Menu + hover card are portalled to <body> so no scrolling ancestor
          can clip them (the original defect). */}
      {isOpen && menuRect && typeof document !== 'undefined' && createPortal(
        <>
          <div
            className={styles.menu}
            ref={menuRef}
            role="listbox"
            style={{
              position: 'fixed',
              left: menuRect.left,
              ...(menuRect.top !== undefined ? { top: menuRect.top } : { bottom: menuRect.bottom }),
              minWidth: menuRect.minWidth,
              maxWidth: MENU_MAX_W,
              maxHeight: menuRect.maxHeight,
              overflowY: 'auto',
              zIndex: 20040,
            }}
          >
            <div
              className={`${styles.option} ${styles.optionDefault} ${!value ? styles.optionSelected : ''}`}
              onClick={() => handleSelect(null)}
              onMouseEnter={() => setHovered(null)}
              role="option"
              aria-selected={!value}
            >
              {placeholder}
            </div>

            {optionKeys.map((optKey) => {
              const opt = options[optKey];
              const isSelected = value === optKey;
              return (
                <div
                  key={optKey}
                  className={`${styles.option} ${isSelected ? styles.optionSelected : ''}`}
                  onClick={() => handleSelect(optKey)}
                  onMouseEnter={(e) => setHovered({ key: optKey, rect: e.currentTarget.getBoundingClientRect() })}
                  onMouseLeave={() => setHovered((h) => (h?.key === optKey ? null : h))}
                  role="option"
                  aria-selected={isSelected}
                  title={describe(optKey)}   /* native fallback for touch/no-hover */
                >
                  {opt.title} ({fmtCurrency?.(opt.cost || 0) || `${currencySymbol()}0`})
                </div>
              );
            })}
          </div>

          {hoveredOpt && cardStyle && (
            <div className={styles.tooltip} style={cardStyle}>
              <div className={styles.tooltipTitle}>{hoveredOpt.title}</div>

              <div className={`${styles.tooltipCost} ${
                (hoveredOpt.cost || 0) < 0 ? styles.tooltipCostPositive
                  : (hoveredOpt.cost || 0) > 0 ? styles.tooltipCostNegative
                  : styles.tooltipCostZero
              }`}>
                💰 {fmtCurrency?.(hoveredOpt.cost || 0) || `${currencySymbol()}0`}
              </div>

              <p className={styles.tooltipDesc}>{describe(hovered.key)}</p>

              {hoveredOpt.impacts && Object.keys(hoveredOpt.impacts).length > 0 && (
                <div className={styles.tooltipImpacts}>
                  {Object.entries(hoveredOpt.impacts).map(([k, v]) => {
                    if (v === 0) return null;
                    const meta = impactLabels[k] || { label: k, icon: '📋', positive: true };
                    const isGood = meta.positive ? v > 0 : v < 0;
                    return (
                      <span
                        key={k}
                        className={`${styles.tooltipImpactBadge} ${isGood ? styles.tooltipImpactGood : styles.tooltipImpactBad}`}
                      >
                        {meta.icon} {v > 0 ? '+' : ''}{v} {meta.label}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </>,
        document.body
      )}
    </div>
  );
}
