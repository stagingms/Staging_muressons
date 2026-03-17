'use client';

import { useMemo } from 'react';
import styles from './CapitalGauges.module.css';

/**
 * CapitalGauges — Top header with 4 persistent progress bars.
 * Color-coded Red / Yellow / Green based on critical thresholds.
 *
 * Props:
 *  - globalState:  { corporate_treasury, group_reputation, synergy_multiplier, ... }
 *  - businessUnits: array of BU objects
 *  - roundNumber:   current round
 */
export default function CapitalGauges({ globalState, businessUnits, roundNumber }) {
    const gauges = useMemo(() => {
        if (!globalState || !businessUnits?.length) return [];

        const treasury = globalState.corporate_treasury || 0;
        const reputation = globalState.group_reputation || 0;

        // Aggregate natural capital debt
        const totalNCD = businessUnits.reduce(
            (sum, bu) => sum + (bu.natural_capital_debt || 0),
            0
        );
        // Average social license
        const avgSocialLicense =
            businessUnits.reduce((sum, bu) => sum + (bu.social_license_score || 0), 0) /
            businessUnits.length;
        // Average governance risk
        const avgGovRisk =
            businessUnits.reduce((sum, bu) => sum + (bu.governance_risk_score || 0), 0) /
            businessUnits.length;

        return [
            {
                id: 'financial',
                label: 'Financial Capital',
                tooltip: 'Corporate treasury — total available cash reserves',
                value: Math.min(100, (treasury / 50_000_000) * 100), // Normalised to baseline
                display: `$${(treasury / 1_000_000).toFixed(1)}M`,
                icon: '💰',
                thresholds: { red: 30, yellow: 60 },
            },
            {
                id: 'natural',
                label: 'Natural Capital',
                tooltip: 'Natural Capital Debt (NCD) — accumulated environmental damage across all BUs',
                // Inverse: high debt = low score
                value: Math.max(0, 100 - totalNCD * 0.001),
                display: totalNCD === 0 ? 'Healthy' : `-$${(totalNCD / 1_000).toFixed(0)}K debt`,
                icon: '🌿',
                thresholds: { red: 25, yellow: 55 },
            },
            {
                id: 'social',
                label: 'Social Capital',
                tooltip: 'Social License (SL) — average community and stakeholder trust across all BUs (0–100)',
                value: avgSocialLicense,
                display: `${avgSocialLicense.toFixed(1)} / 100`,
                icon: '🤝',
                thresholds: { red: 30, yellow: 50 },
            },
            {
                id: 'governance',
                label: 'Governance',
                tooltip: 'Governance Risk — average regulatory and compliance risk score across all BUs',
                // Inverse: high risk = low score
                value: Math.max(0, 100 - avgGovRisk * 2),
                display: `Risk: ${avgGovRisk.toFixed(1)}`,
                icon: '⚖️',
                thresholds: { red: 30, yellow: 55 },
            },
        ];
    }, [globalState, businessUnits]);

    const getColor = (value, thresholds) => {
        if (value <= thresholds.red) return 'red';
        if (value <= thresholds.yellow) return 'yellow';
        return 'green';
    };

    return (
        <header className={styles.header}>
            <div className={styles.titleBlock}>
                <h1 className={styles.title}>MURESSONS CORPORATION</h1>
                <span className={styles.roundBadge}>Round {roundNumber || 1} / 10</span>
            </div>

            <div className={styles.gaugesRow}>
                {gauges.map((g, i) => {
                    const color = getColor(g.value, g.thresholds);
                    return (
                        <div
                            key={g.id}
                            className={styles.gaugeCard}
                            style={{ animationDelay: `${i * 80}ms` }}
                            title={g.tooltip}
                        >
                            <div className={styles.gaugeTop}>
                                <span className={styles.gaugeIcon}>{g.icon}</span>
                                <span className={styles.gaugeLabel}>{g.label}</span>
                            </div>
                            <div className={styles.barTrack}>
                                <div
                                    className={`${styles.barFill} ${styles[`bar_${color}`]}`}
                                    style={{ width: `${Math.max(2, g.value)}%` }}
                                />
                            </div>
                            <div className={styles.gaugeBottom}>
                                <span className={`${styles.gaugeValue} ${styles[`text_${color}`]}`}>
                                    {g.display}
                                </span>
                                <span className={`${styles.statusDot} ${styles[`dot_${color}`]}`} />
                            </div>
                        </div>
                    );
                })}
            </div>
        </header>
    );
}
