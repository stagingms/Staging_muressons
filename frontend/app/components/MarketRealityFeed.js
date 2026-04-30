'use client';
import { useState } from 'react';
import styles from './ExecutiveCockpit.module.css';

/**
 * MarketRealityFeed — News ticker + event alert overlay.
 *
 * Props:
 *  - items: [{ type: 'info'|'alert', text: string }]
 *  - activeAlert: { icon, title, body, isBlackSwan? } — overrides feed with stark warning
 *  - traceConsequence: (text) => { round, decision, roundTitle } | null  — consequence tracing
 *  - traceTooltipIdx: number | null — which item tooltip is showing
 *  - onTraceHover: (idx | null) => void — hover handler
 *
 * DV-04: Items are click-to-expand for full text.
 * PED-01: Consequence traceability — hover shows causal decision link.
 */

const SEVERITY_META = {
  alert: { icon: '🚨', badge: 'ALERT', badgeColor: '#ef4444', badgeBg: 'rgba(239,68,68,0.1)' },
  info: { icon: '📊', badge: 'INFO', badgeColor: '#3b82f6', badgeBg: 'rgba(59,130,246,0.08)' },
  foreshadow: { icon: '📰', badge: 'BREAKING', badgeColor: '#f59e0b', badgeBg: 'rgba(245,158,11,0.1)' },
};

export default function MarketRealityFeed({
  items = [],
  activeAlert = null,
  traceConsequence = null,
  traceTooltipIdx = null,
  onTraceHover = null,
}) {
  const [expandedItems, setExpandedItems] = useState({});

  const toggleExpand = (idx) => {
    setExpandedItems(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  if (activeAlert) {
    const isBlackSwan = activeAlert.isBlackSwan;
    return (
      <div className={styles.feedContainer}>
        <div className={styles.feedTitle}>
          {isBlackSwan ? '🦢 BLACK SWAN EVENT' : '📰 Market Reality'}
        </div>
        <div
          className={`${styles.eventPopup} ${isBlackSwan ? styles.eventPopupBlackSwan : ''}`}
          style={isBlackSwan ? {
            background: 'linear-gradient(135deg, #1a0000, #2d0000)',
            border: '2px solid #ef4444',
            boxShadow: '0 0 30px rgba(239, 68, 68, 0.3)',
            animation: 'none',
          } : undefined}
        >
          <div className={styles.eventPopupIcon}>
            {activeAlert.icon || '⚠️'}
          </div>
          <div
            className={styles.eventPopupTitle}
            style={isBlackSwan ? { color: '#ef4444', fontWeight: 800, fontSize: '1rem' } : undefined}
          >
            {activeAlert.title}
          </div>
          <div
            className={styles.eventPopupBody}
            style={isBlackSwan ? { color: '#fecaca', fontSize: '0.82rem', lineHeight: 1.5 } : undefined}
          >
            {activeAlert.body}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.feedContainer}>
      <div className={styles.feedTitle}>📰 Market Reality Feed</div>
      {items.map((item, i) => {
        const effectiveType = item.isForeshadow ? 'foreshadow' : item.type;
        const meta = SEVERITY_META[effectiveType] || SEVERITY_META.info;
        const isExpanded = !!expandedItems[i];
        const isLong = item.text && item.text.length > 80;

        // Consequence traceability
        const trace = traceConsequence ? traceConsequence(item.text) : null;
        const showTrace = traceTooltipIdx === i && trace;

        return (
          <div
            key={i}
            className={`${styles.feedItem} ${item.type === 'alert' ? styles.feedItemAlert : styles.feedItemInfo} ${trace ? styles.traceableItem : ''}`}
            style={{
              animationDelay: `${i * 80}ms`,
              cursor: isLong || trace ? 'pointer' : 'default',
              transition: 'background 0.2s ease',
              ...(item.isForeshadow ? {
                borderLeft: '3px solid #f59e0b',
                background: 'rgba(245,158,11,0.04)',
              } : {}),
            }}
            onClick={() => isLong && toggleExpand(i)}
            onMouseEnter={() => trace && onTraceHover?.(i)}
            onMouseLeave={() => onTraceHover?.(null)}
            title={trace ? 'Hover for causal decision trace' : (isLong ? (isExpanded ? 'Click to collapse' : 'Click to expand') : undefined)}
          >
            {/* Consequence Traceability Tooltip */}
            {showTrace && (
              <div className={styles.traceTooltip}>
                <div className={styles.traceRound}>
                  🔗 Traced to Round {trace.round}
                </div>
                <div style={{ fontSize: '0.65rem', color: '#64748b', marginBottom: 4 }}>
                  {trace.roundTitle}
                </div>
                <div className={styles.traceDecision}>
                  {trace.decision}
                </div>
              </div>
            )}

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6 }}>
              <span style={{ fontSize: '0.82rem', flexShrink: 0, lineHeight: 1.5 }}>{meta.icon}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 2 }}>
                  <span style={{
                    fontSize: '0.48rem', fontWeight: 800,
                    padding: '1px 4px', borderRadius: 3,
                    background: meta.badgeBg, color: meta.badgeColor,
                    letterSpacing: '0.06em',
                    textTransform: 'uppercase',
                  }}>
                    {meta.badge}
                  </span>
                  {trace && (
                    <span style={{
                      fontSize: '0.45rem', fontWeight: 700,
                      padding: '1px 4px', borderRadius: 3,
                      background: 'rgba(0, 229, 195, 0.08)', color: '#0d9488',
                      letterSpacing: '0.04em', textTransform: 'uppercase',
                    }}>
                      🔗 R{trace.round}
                    </span>
                  )}
                  {isLong && (
                    <span style={{
                      fontSize: '0.5rem', color: 'rgba(148,163,184,0.7)',
                      marginLeft: 'auto', flexShrink: 0, transition: 'transform 0.2s ease',
                      transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                      display: 'inline-block',
                    }}>▼</span>
                  )}
                </div>
                <div style={{
                  fontSize: '0.7rem', lineHeight: 1.5,
                  overflow: isExpanded ? 'visible' : 'hidden',
                  display: isExpanded ? 'block' : '-webkit-box',
                  WebkitLineClamp: isExpanded ? 'unset' : 2,
                  WebkitBoxOrient: 'vertical',
                  maxHeight: isExpanded ? 'none' : '2.8em',
                  transition: 'max-height 0.25s ease',
                }}>
                  {item.text}
                </div>
              </div>
            </div>
          </div>
        );
      })}
      {items.length === 0 && (
        <div className={styles.feedItem} style={{ color: '#94a3b8', textAlign: 'center' }}>
          <span style={{ fontSize: '1.2rem', display: 'block', marginBottom: 4 }}>📭</span>
          No market events this round
        </div>
      )}
    </div>
  );
}

