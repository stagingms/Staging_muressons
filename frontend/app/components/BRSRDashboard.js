'use client';
import React from 'react';
import styles from './BRSRDashboard.module.css';

/**
 * BRSR XBRL Filing Portal
 * SEBI XBRL Compliance Terminal — National Guidelines on Responsible Business Conduct
 * Reads from globalState.active_event_flags exactly as the original component.
 */

export default function BRSRDashboard({ sessionId, globalState, isOpen, onClose }) {
  if (!isOpen) return null;

  const flags = globalState?.active_event_flags || {};

  // Resilience fallback: also read from the deep BRSR track state
  // in case interim scores haven't been surfaced to active_event_flags yet.
  const trackState = globalState?._brsr_track_state || flags._brsr_track_state || {};
  const accumulatedFlags = new Set(trackState.accumulated_flags || []);

  const brsrScore = flags.brsr_performance_score
    || trackState.total_score
    || 0;

  // --- Derive validation status from score ---
  const validationStatus =
    brsrScore >= 80 ? 'Assured' :
    brsrScore >= 50 ? 'Pending' :
    'Discrepancy Found';

  const validationClass =
    brsrScore >= 80 ? styles.statusAssured :
    brsrScore >= 50 ? styles.statusPending :
    styles.statusDiscrepancy;

  // Helper: check flag from active_event_flags OR accumulated track flags
  const hasFlag = (name) => !!(flags[name] || accumulatedFlags.has(name));

  // --- NGRBC Principle rows ---
  const principleRows = [
    {
      principle: 'P1 & P7',
      domain: 'Governance & Ethics',
      tier: hasFlag('brsr_pioneer')
        ? 'LEADERSHIP_INDICATOR_SATISFIED'
        : hasFlag('governance_fragility')
          ? 'NON_COMPLIANT'
          : 'ESSENTIAL_INDICATOR',
      satisfied: hasFlag('brsr_pioneer'),
    },
    {
      principle: 'P3 & P5',
      domain: 'Workforce Well-being',
      tier: hasFlag('brsr_living_wage')
        ? 'LEADERSHIP_INDICATOR_SATISFIED'
        : 'ESSENTIAL_INDICATOR',
      satisfied: hasFlag('brsr_living_wage'),
    },
    {
      principle: 'P6 & P2',
      domain: 'Environmental Footprint',
      tier: (hasFlag('brsr_circular_symbiosis') || hasFlag('sdg_12_leadership'))
        ? 'LEADERSHIP_INDICATOR_SATISFIED'
        : 'ESSENTIAL_INDICATOR',
      satisfied: hasFlag('brsr_circular_symbiosis') || hasFlag('sdg_12_leadership'),
    },
    {
      principle: 'P4',
      domain: 'Value Chain Assurance',
      tier: hasFlag('brsr_core_assured')
        ? 'LEADERSHIP_INDICATOR_SATISFIED'
        : 'ESSENTIAL_INDICATOR',
      satisfied: hasFlag('brsr_core_assured'),
    },
    {
      principle: 'P9',
      domain: 'Integrated Reporting',
      tier: hasFlag('brsr_integrated_report')
        ? 'LEADERSHIP_INDICATOR_SATISFIED'
        : 'ESSENTIAL_INDICATOR',
      satisfied: hasFlag('brsr_integrated_report'),
    },
  ];

  const indicatorClassName = (tier) => {
    if (tier === 'LEADERSHIP_INDICATOR_SATISFIED') return styles.indicatorLeadership;
    if (tier === 'ESSENTIAL_INDICATOR') return styles.indicatorEssential;
    return styles.indicatorNonCompliant;
  };

  // --- Audit Exceptions ---
  // Check both active_event_flags and accumulated track flags
  const exceptions = [];
  if (hasFlag('governance_fragility'))    exceptions.push('GOVERNANCE_FRAGILITY_DETECTED');
  if (hasFlag('brsr_greenwash_risk'))     exceptions.push('GREENWASH_RISK_FLAGGED');
  if (hasFlag('brsr_regulatory_minimum')) exceptions.push('REGULATORY_MINIMUM_ONLY');
  if (hasFlag('brsr_statutory_minimums')) exceptions.push('STATUTORY_MINIMUMS_ONLY');
  if (hasFlag('brsr_compliance_only'))    exceptions.push('COMPLIANCE_FILING_ONLY');


  const hasExceptions = exceptions.length > 0;

  return (
    <div className={styles.overlay} onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}>
      <div className={styles.panel}>

        {/* Tricolor Strip */}
        <div className={styles.tricolorStrip}>
          <span className={styles.tricolorSaffron} />
          <span className={styles.tricolorWhite} />
          <span className={styles.tricolorGreen} />
        </div>

        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerText}>
            <div className={styles.headerTitle}>
              National Guidelines on Responsible Business Conduct — Annual Filing Gateway
            </div>
            <div className={styles.headerSub}>
              Ministry of Corporate Affairs | SEBI XBRL Compliance Terminal
            </div>
          </div>
          <button className={styles.closeLink} onClick={onClose}>
            [Close Filing Portal]
          </button>
        </div>

        {/* Content */}
        <div className={styles.content}>

          {/* Section 1: XBRL Validation Status */}
          <div>
            <div className={styles.sectionTitle}>XBRL Validation Status Summary</div>
            <div className={styles.validationPanel}>
              <table className={styles.validationTable}>
                <tbody>
                  <tr>
                    <td>Filing Entity:</td>
                    <td>Muressons Corporation Ltd.</td>
                  </tr>
                  <tr>
                    <td>CIN:</td>
                    <td>L99999MH2024PLC999999</td>
                  </tr>
                  <tr>
                    <td>Reporting Period:</td>
                    <td>FY 2025-26</td>
                  </tr>
                  <tr>
                    <td>Overall Compliance Score:</td>
                    <td>{brsrScore}/100</td>
                  </tr>
                  <tr>
                    <td>Validation Status:</td>
                    <td><span className={validationClass}>[{validationStatus.toUpperCase()}]</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 2: NGRBC Compliance Matrix */}
          <div className={styles.complianceSection}>
            <div className={styles.sectionTitle}>NGRBC Principle Compliance Matrix</div>
            <table className={styles.complianceTable}>
              <thead>
                <tr>
                  <th>Principle</th>
                  <th>Domain</th>
                  <th>Indicator Tier</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {principleRows.map((row) => (
                  <tr key={row.principle}>
                    <td><span className={styles.principleCode}>{row.principle}</span></td>
                    <td><span className={styles.domainLabel}>{row.domain}</span></td>
                    <td>
                      <span className={`${styles.indicatorTag} ${indicatorClassName(row.tier)}`}>
                        [STATUS: {row.tier}]
                      </span>
                    </td>
                    <td>
                      <span className={styles.statusIcon}>
                        {row.satisfied ? '✓' : '✗'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Section 3: Active Audit Exceptions */}
          <div>
            <div className={styles.sectionTitle}>Active Audit Exceptions &amp; Regulatory Flags</div>
            <div className={`${styles.exceptionsPanel} ${hasExceptions ? styles.hasExceptions : styles.noExceptions}`}>
              {hasExceptions ? (
                exceptions.map((exc) => (
                  <div key={exc} className={styles.exceptionLine}>
                    [EXCEPTION: {exc}]
                  </div>
                ))
              ) : (
                <div className={styles.auditClean}>
                  [AUDIT STATUS: NO MATERIAL EXCEPTIONS NOTED]
                </div>
              )}
            </div>
          </div>

          {/* Section 4: ESG Alpha Dividend */}
          {flags.brsr_net_positive_dividend && (
            <div className={styles.dividendPanel}>
              <div className={styles.dividendText}>
                [TERMINAL BONUS: ESG ALPHA DIVIDEND ACTIVATED → M_R +0.05]
              </div>
            </div>
          )}

          {/* Footer Disclaimer */}
          <div className={styles.footerDisclaimer}>
            This filing is generated for simulation purposes under the Muressons Sustainability Simulator.
            Not an official SEBI/MCA document.
          </div>

        </div>
      </div>
    </div>
  );
}
