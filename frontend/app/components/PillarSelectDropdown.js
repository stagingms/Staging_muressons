'use client';
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import styles from './PillarSelectDropdown.module.css';

/**
 * PillarSelectDropdown — Custom dropdown replacing native <select>
 * for strategic pillar options. Shows a rich hover tooltip popup
 * beside each option with its description, cost, and impacts.
 *
 * Props:
 *   - options:        Object { optKey: { title, description, cost, impacts, ... } }
 *   - value:          string | null — currently selected optKey
 *   - onChange:       (optKey | null) => void
 *   - placeholder:    string — shown when no value selected
 *   - fmtCurrency:    (v) => string
 *   - detailedDescs:  Object { optKey: string } — detailed descriptions per option
 *   - impactLabels:   Object { impactKey: { label, icon, positive } } — optional
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
  const [hoveredOpt, setHoveredOpt] = useState(null);
  const [tooltipSide, setTooltipSide] = useState('right'); // 'right' | 'left'
  const wrapperRef = useRef(null);
  const menuRef = useRef(null);
  const hoveredRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!isOpen) return;
    const handleClick = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false);
        setHoveredOpt(null);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
        setHoveredOpt(null);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen]);

  // Determine tooltip placement based on available space
  const checkTooltipSide = useCallback((el) => {
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const spaceRight = window.innerWidth - rect.right;
    setTooltipSide(spaceRight > 320 ? 'right' : 'left');
  }, []);

  const handleToggle = useCallback(() => {
    setIsOpen((prev) => !prev);
    setHoveredOpt(null);
  }, []);

  const handleSelect = useCallback((optKey) => {
    onChange?.(optKey || null);
    setIsOpen(false);
    setHoveredOpt(null);
  }, [onChange]);

  const handleOptionHover = useCallback((optKey, el) => {
    setHoveredOpt(optKey);
    hoveredRef.current = el;
    checkTooltipSide(el);
  }, [checkTooltipSide]);

  const selectedOption = value ? options[value] : null;
  const displayText = selectedOption
    ? `${selectedOption.title} (${fmtCurrency?.(selectedOption.cost || 0) || '$0'})`
    : placeholder;

  return (
    <div className={styles.wrapper} ref={wrapperRef}>
      {/* Trigger button */}
      <button
        className={`${styles.trigger} ${isOpen ? styles.triggerOpen : ''} ${value ? styles.triggerHasValue : styles.triggerPlaceholder}`}
        onClick={handleToggle}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        {displayText}
      </button>

      {/* Dropdown menu */}
      {isOpen && (
        <>
          <div className={styles.menu} ref={menuRef} role="listbox">
            {/* Default "deselect" option */}
            <div
              className={`${styles.option} ${styles.optionDefault} ${!value ? styles.optionSelected : ''}`}
              onClick={() => handleSelect(null)}
              role="option"
              aria-selected={!value}
            >
              {placeholder}
            </div>

            {/* Options */}
            {Object.entries(options).map(([optKey, opt]) => {
              const isSelected = value === optKey;
              const isHovered = hoveredOpt === optKey;

              return (
                <div
                  key={optKey}
                  className={`${styles.option} ${isSelected ? styles.optionSelected : ''}`}
                  onClick={() => handleSelect(optKey)}
                  onMouseEnter={(e) => handleOptionHover(optKey, e.currentTarget)}
                  onMouseLeave={() => setHoveredOpt(null)}
                  role="option"
                  aria-selected={isSelected}
                >
                  {opt.title} ({fmtCurrency?.(opt.cost || 0) || '$0'})

                  {/* Tooltip popup on hover */}
                  {isHovered && (
                    <div className={`${styles.tooltip} ${tooltipSide === 'left' ? styles.tooltipLeft : ''}`}>
                      <div className={styles.tooltipTitle}>{opt.title}</div>

                      {/* Cost badge */}
                      <div className={`${styles.tooltipCost} ${
                        (opt.cost || 0) < 0 ? styles.tooltipCostPositive
                          : (opt.cost || 0) > 0 ? styles.tooltipCostNegative
                          : styles.tooltipCostZero
                      }`}>
                        💰 {fmtCurrency?.(opt.cost || 0) || '$0'}
                      </div>

                      {/* Description */}
                      <p className={styles.tooltipDesc}>
                        {detailedDescs[optKey] || opt.description || 'No description available.'}
                      </p>

                      {/* Impact badges */}
                      {opt.impacts && Object.keys(opt.impacts).length > 0 && (
                        <div className={styles.tooltipImpacts}>
                          {Object.entries(opt.impacts).map(([k, v]) => {
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
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
