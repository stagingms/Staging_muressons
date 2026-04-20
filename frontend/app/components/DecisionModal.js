'use client';

import { useState, useMemo, useEffect } from 'react';
import { createPortal } from 'react-dom';
import styles from './DecisionModal.module.css';
import { DETAILED_DESCRIPTIONS } from '../utils/detailedDescriptions';

/**
 * DecisionModal — Crisis decision popup with 3 strategic options.
 *
 * Props:
 *  - isOpen:        boolean
 *  - roundConfig:   backend round config (crisis + options) or null
 *  - roundNumber:   current round
 *  - synergyScore:  current synergy score (for R10 gate)
 *  - onSelect:      (optionId) => void
 *  - onClose:       () => void
 */

// ── Color mapping for option labels ───────────────────────
const OPTION_ACCENTS = {
    option_a: '#10b981',
    option_b: '#f59e0b',
    option_c: '#ef4444',
};

// ── Fallback crisis per round (when backend offline) ──────
const FALLBACK_CRISES = {
    1: {
        id: 'foundation', title: 'ESG Foundation Audit', icon: '📋',
        description: 'Your board demands an initial ESG materiality assessment across all business units. Choose how deeply to investigate your supply chain risks.'
    },
    2: {
        id: 'double_materiality', title: 'Double Materiality Gate', icon: '⚖️',
        description: 'Chief Financial Officer requires all sustainability investments to pass a double materiality test before allocation.'
    },
    3: {
        id: 'scope3', title: 'Scope 3 Supply Chain Disruption', icon: '🏭',
        description: 'Major Scope 3 emissions discovered in your crucial supply chains. Regulators are watching closely.'
    },
    4: {
        id: 'contagion', title: 'ESG Contagion Crisis', icon: '⚡',
        description: 'Negative ESG headlines from a competitor have triggered sector-wide scrutiny. Your reputation is under pressure.'
    },
    5: {
        id: 'climate', title: 'Climate Physical Risk Event', icon: '🌪️',
        description: 'A severe climate event threatens your coastal manufacturing facilities. Engineering and insurance decisions must be made immediately.'
    },
    6: {
        id: 'ai_bias', title: 'AI Ethics & Bias Scandal', icon: '🤖',
        description: 'Your software division\'s AI hiring tool has been found to exhibit racial bias. Media attention is escalating.'
    },
    7: {
        id: 'circularity', title: 'Circular Economy Pivot', icon: '♻️',
        description: 'New EU regulations require circular economy compliance by 2035. This is your chance to gain first-mover advantage through cross-BU synergy.'
    },
    8: {
        id: 'water_stress', title: 'Blue Water Stress', icon: '💧',
        description: 'Your primary watershed has been reclassified as critically stressed. All water-dependent BUs face imminent operational disruption.'
    },
    9: {
        id: 'just_transition', title: 'Just Transition & Labor', icon: '✊',
        description: 'Automation and green-transition layoffs have triggered labor unrest. Social license is eroding across communities.'
    },
    10: {
        id: 'activist_ultimatum', title: 'Activist Ultimatum', icon: '📢',
        description: 'A major activist fund has acquired 8% of Muressons shares and is demanding structural change. You must choose your corporate destiny.'
    },
};

const FALLBACK_OPTIONS = {
    option_a: {
        id: 'option_a', label: 'A', title: 'Option A — Bold Action', description: 'Take aggressive, high-cost action to address the crisis head-on.',
        impacts: { treasury: 'High cost', risk: 'Reduced' }, accent: '#10b981'
    },
    option_b: {
        id: 'option_b', label: 'B', title: 'Option B — Balanced', description: 'Moderate investment with balanced risk-reward profile.',
        impacts: { treasury: 'Medium cost', risk: 'Partial' }, accent: '#f59e0b'
    },
    option_c: {
        id: 'option_c', label: 'C', title: 'Option C — Conservative', description: 'Minimize cost now, but accept higher long-term risks.',
        impacts: { treasury: 'Low cost', risk: 'Deferred' }, accent: '#ef4444'
    },
};

function transformConfig(roundConfig, roundNumber) {
    if (!roundConfig) {
        return {
            crisis: FALLBACK_CRISES[roundNumber] || FALLBACK_CRISES[1],
            options: Object.values(FALLBACK_OPTIONS),
        };
    }

    const crisis = roundConfig.crisis || {
        id: roundConfig.id || `r${roundNumber}`,
        title: roundConfig.title || `Round ${roundNumber} Crisis`,
        description: roundConfig.description || '',
        icon: roundConfig.icon || '⚡',
    };

    const options = [];
    const rawOpts = roundConfig.options || {};
    for (const [key, opt] of Object.entries(rawOpts)) {
        options.push({
            id: key,
            label: key.replace('option_', '').toUpperCase(),
            title: opt.title || opt.label || key,
            description: opt.description || '',
            detailedDescription: DETAILED_DESCRIPTIONS.narrative?.[roundNumber]?.[key] || opt.detailed_description || opt.description || '',
            impacts: opt.impacts || {},
            accent: OPTION_ACCENTS[key] || '#6366f1',
            disabled: opt.disabled || false,
            disabledReason: opt.disabled_reason || null,
        });
    }

    return { crisis, options: options.length > 0 ? options : Object.values(FALLBACK_OPTIONS) };
}

export default function DecisionModal({
    isOpen = false,
    roundConfig = null,
    roundNumber = 1,
    synergyScore = 100,
    onSelect,
    onClose,
}) {
    const [selected, setSelected] = useState(null);
    const [confirming, setConfirming] = useState(false);
    const [hoveredOpt, setHoveredOpt] = useState(null);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    // Transform backend config to display format
    const { crisis, options } = useMemo(
        () => transformConfig(roundConfig, roundNumber),
        [roundConfig, roundNumber]
    );

    // R10 synergy gate: disable Option A if synergy <= 80
    const processedOptions = useMemo(() => {
        if (roundNumber !== 10) return options;
        return options.map((opt) => {
            if (opt.id === 'option_a' && synergyScore <= 80) {
                return {
                    ...opt,
                    disabled: true,
                    disabledReason: `Requires Synergy Score > 80 (current: ${synergyScore})`,
                };
            }
            return opt;
        });
    }, [options, roundNumber, synergyScore]);

    // Reset selection when round changes
    useEffect(() => {
        setSelected(null);
        setConfirming(false);
    }, [roundNumber]);

    if (!isOpen) return null;

    const handleSelect = (optionId) => {
        const opt = processedOptions.find((o) => o.id === optionId);
        if (opt?.disabled) return;
        setSelected(optionId);
        setConfirming(false);
    };

    const handleConfirm = () => {
        if (!selected) return;
        onSelect?.(selected);
        setSelected(null);
        setConfirming(false);
    };

    return (
        <div className={styles.overlay} onClick={onClose}>
            <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                {/* Header */}
                <div className={styles.modalHeader}>
                    <div className={styles.crisisTag}>
                        <span className={styles.crisisIcon}>{crisis.icon}</span>
                        <span className={styles.crisisLabel}>ROUND {roundNumber} CRISIS</span>
                    </div>
                    <button className={styles.closeBtn} onClick={onClose}>
                        ✕
                    </button>
                </div>

                {/* Crisis description */}
                <div className={styles.crisisBlock}>
                    <h2 className={styles.crisisTitle}>{crisis.title}</h2>
                    <p className={styles.crisisDesc}>{crisis.description}</p>
                </div>

                {/* Divider */}
                <div className={styles.divider}>
                    <span>SELECT YOUR STRATEGY</span>
                </div>

                {/* Options */}
                <div className={styles.optionsGrid}>
                    {processedOptions.map((opt) => {
                        const isActive = selected === opt.id;
                        const isDisabled = opt.disabled;
                        return (
                            <button
                                key={opt.id}
                                className={`${styles.optionCard} ${isActive ? styles.active : ''} ${isDisabled ? styles.disabled : ''}`}
                                style={{ '--opt-accent': opt.accent || '#6366f1' }}
                                onClick={() => handleSelect(opt.id)}
                                disabled={isDisabled}
                                onMouseEnter={() => !isDisabled && setHoveredOpt(opt)}
                                onMouseLeave={() => setHoveredOpt(null)}
                            >
                                <div className={styles.optLabel}>{opt.label}</div>
                                <h3 className={styles.optTitle}>{opt.title}</h3>
                                <p className={styles.optDesc}>{opt.description}</p>

                                <div className={styles.impactGrid}>
                                    {Object.entries(opt.impacts || {}).map(([key, val]) => (
                                        <div key={key} className={styles.impactItem}>
                                            <span className={styles.impactKey}>
                                                {key.replace(/_/g, ' ')}
                                            </span>
                                            <span
                                                className={`${styles.impactVal} ${String(val).startsWith('-')
                                                    ? styles.negative
                                                    : styles.positive
                                                    }`}
                                            >
                                                {val}
                                            </span>
                                        </div>
                                    ))}
                                </div>

                                {isDisabled && opt.disabledReason && (
                                    <div className={styles.disabledBadge}>
                                        🔒 {opt.disabledReason}
                                    </div>
                                )}

                                {isActive && (
                                    <div className={styles.selectedBadge}>✓ SELECTED</div>
                                )}
                            </button>
                        );
                    })}
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
                        ) : selected ? (
                            <p><strong>{processedOptions.find(o => o.id === selected)?.title}:</strong> {processedOptions.find(o => o.id === selected)?.detailedDescription || processedOptions.find(o => o.id === selected)?.description}</p>
                        ) : (
                            <p className={styles.breakdownPlaceholder}>Hover over a strategic option above to preview its detailed implications.</p>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className={styles.modalFooter}>
                    {!confirming ? (
                        <button
                            className={`${styles.confirmBtn} ${!selected ? styles.disabled : ''}`}
                            disabled={!selected}
                            onClick={() => setConfirming(true)}
                        >
                            Review & Confirm
                        </button>
                    ) : (
                        <div className={styles.confirmBlock}>
                            <span className={styles.confirmText}>
                                Commit to{' '}
                                <strong>
                                    {processedOptions.find((o) => o.id === selected)?.title}
                                </strong>
                                ? This cannot be undone.
                            </span>
                            <div className={styles.confirmActions}>
                                <button
                                    className={styles.cancelBtn}
                                    onClick={() => setConfirming(false)}
                                >
                                    Back
                                </button>
                                <button className={styles.commitBtn} onClick={handleConfirm}>
                                    🔒 Confirm Decision
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
