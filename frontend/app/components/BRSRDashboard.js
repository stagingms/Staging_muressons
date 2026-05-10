'use client';
import React, { useMemo } from 'react';
import styles from './BRSRDashboard.module.css';

/**
 * BRSR Dashboard
 * Visualizes the 5-round NGRBC BRSR deep dive progress.
 */

export default function BRSRDashboard({ sessionId, globalState, isOpen, onClose }) {
  if (!isOpen) return null;

  const flags = globalState?.active_event_flags || {};
  const brsrScore = flags.brsr_performance_score || 0;
  
  const metrics = [
    { id: 'gov', title: 'Governance & Ethics', icon: '⚖️', score: flags.brsr_pioneer ? 100 : (flags.governance_fragility ? 20 : 60) },
    { id: 'workforce', title: 'Workforce Well-being', icon: '👷', score: flags.brsr_living_wage ? 100 : 50 },
    { id: 'env', title: 'Environmental Footprint', icon: '🌿', score: flags.brsr_circular_symbiosis ? 100 : (flags.sdg_12_leadership ? 80 : 40) },
    { id: 'value_chain', title: 'Value Chain Assurance', icon: '🔗', score: flags.brsr_core_assured ? 100 : (flags.brsr_greenwash_risk ? 20 : 50) },
    { id: 'reporting', title: 'Integrated Reporting', icon: '📊', score: flags.brsr_integrated_report ? 100 : 40 },
  ];

  const getColor = (score) => {
    if (score >= 80) return '#10b981'; // Green
    if (score >= 50) return '#f59e0b'; // Amber
    return '#ef4444'; // Red
  };

  return (
    <div className={styles.overlay} onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}>
      <div className={styles.panel}>
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <span className={styles.headerIcon}>🇮🇳</span>
            <div>
              <div className={styles.headerTitle}>BRSR NGRBC DASHBOARD</div>
              <div className={styles.headerSub}>SEBI Compliance & Leadership Tracker</div>
            </div>
          </div>
          <div className={styles.headerRight}>
            <button className={styles.closeBtn} onClick={onClose}>✕</button>
          </div>
        </div>

        <div className={styles.content}>
          <div className={styles.metricsGrid}>
            <div className={styles.metricCard} style={{ borderLeft: '4px solid #818cf8' }}>
              <div className={styles.metricHeader}>
                <span className={styles.metricTitle}>Overall Performance</span>
                <span className={styles.metricIcon}>🏆</span>
              </div>
              <div className={styles.metricValue} style={{ color: getColor(brsrScore) }}>
                {brsrScore}<span style={{ fontSize: '1rem', color: '#64748b' }}>/100</span>
              </div>
              <div className={styles.progressBar}>
                <div className={styles.progressFill} style={{ width: `${brsrScore}%`, background: getColor(brsrScore) }} />
              </div>
            </div>
            
            {flags.brsr_net_positive_dividend && (
              <div className={styles.metricCard} style={{ background: 'rgba(16,185,129,0.08)' }}>
                <div className={styles.metricHeader}>
                  <span className={styles.metricTitle}>ESG Alpha Dividend</span>
                  <span className={styles.metricIcon}>💰</span>
                </div>
                <div className={styles.metricValue} style={{ color: '#10b981' }}>+0.05</div>
                <div style={{ fontSize: '0.75rem', color: '#10b981' }}>Terminal Valuation Multiplier</div>
              </div>
            )}
          </div>

          <div className={styles.flagsSection}>
            <div className={styles.flagsTitle}>NGRBC Principle Alignment</div>
            <div className={styles.metricsGrid}>
              {metrics.map(m => (
                <div key={m.id} className={styles.metricCard}>
                  <div className={styles.metricHeader}>
                    <span className={styles.metricTitle}>{m.title}</span>
                    <span className={styles.metricIcon}>{m.icon}</span>
                  </div>
                  <div className={styles.progressBar}>
                    <div className={styles.progressFill} style={{ width: `${m.score}%`, background: getColor(m.score) }} />
                  </div>
                  <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: getColor(m.score), fontWeight: 'bold' }}>
                    {m.score >= 80 ? 'Leadership' : m.score >= 50 ? 'Essential' : 'Laggard'}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className={styles.flagsSection}>
             <div className={styles.flagsTitle}>Active Indicators</div>
             <div className={styles.flagsGrid}>
                {[
                  { id: 'brsr_pioneer', label: 'Governance Pioneer' },
                  { id: 'brsr_living_wage', label: 'Living Wage Adopted' },
                  { id: 'brsr_circular_symbiosis', label: 'Circular Symbiosis' },
                  { id: 'brsr_core_assured', label: 'BRSR Core Assured' },
                  { id: 'brsr_integrated_report', label: 'Integrated Reporting' }
                ].map(flag => {
                  const isActive = flags[flag.id];
                  return (
                    <div key={flag.id} className={`${styles.flagBadge} ${isActive ? styles.flagBadgeActive : ''}`}>
                      <span>{isActive ? '✅' : '○'}</span>
                      <span>{flag.label}</span>
                    </div>
                  );
                })}
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
