'use client';
import { useState, useEffect } from 'react';
import styles from './ExecutiveCockpit.module.css';

/**
 * MarketRealityFeed — News ticker + event alert overlay.
 *
 * Props:
 *  - items: [{ type: 'info'|'alert', text: string }]
 *  - activeAlert: { icon, title, body, isBlackSwan? } — overrides feed with stark warning
 *  - onDismissAlert: () => void — callback to dismiss the active alert (player must acknowledge)
 *  - traceConsequence: (text) => { round, decision, roundTitle } | null  — consequence tracing
 *  - traceTooltipIdx: number | null — which item tooltip is showing
 *  - onTraceHover: (idx | null) => void — hover handler
 *  - roundTier: 'foundation'|'crisis'|'integration'|'finale' — for default filter
 *
 * DV-04: Items are click-to-expand for full text.
 * PED-01: Consequence traceability — hover shows causal decision link.
 * #6: Contextual Market Feed Filtering — severity filter chips.
 */

const SEVERITY_META = {
  alert: { icon: '🚨', badge: 'ALERT', badgeColor: '#ef4444', badgeBg: 'rgba(239,68,68,0.1)' },
  info: { icon: '📊', badge: 'INFO', badgeColor: '#3b82f6', badgeBg: 'rgba(59,130,246,0.08)' },
  foreshadow: { icon: '📰', badge: 'BREAKING', badgeColor: '#f59e0b', badgeBg: 'rgba(245,158,11,0.1)' },
};

const FILTER_CHIPS = [
  { id: 'all', label: 'All', icon: '📋' },
  { id: 'alerts', label: 'Alerts', icon: '⚠️' },
  { id: 'data', label: 'Data', icon: '📊' },
];

export default function MarketRealityFeed({
  items = [],
  activeAlert = null,
  onDismissAlert = null,
  traceConsequence = null,
  traceTooltipIdx = null,
  onTraceHover = null,
  roundTier = 'foundation',
}) {
  const [expandedItems, setExpandedItems] = useState({});
  const [showAll, setShowAll] = useState(false);
  // #6: Default filter — ALL for early rounds, ALERTS for late rounds
  const [feedFilter, setFeedFilter] = useState(
    roundTier === 'integration' || roundTier === 'finale' ? 'alerts' : 'all'
  );

  // Reset collapse when filter changes
  useEffect(() => {
    setShowAll(false);
  }, [feedFilter]);

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
          {/* Dismiss / Acknowledge button — alert stays until player acts */}
          {onDismissAlert && (
            <button
              onClick={onDismissAlert}
              style={{
                marginTop: 12, width: '100%', padding: '10px 16px',
                background: isBlackSwan
                  ? 'linear-gradient(135deg, #ef4444, #dc2626)'
                  : 'linear-gradient(135deg, #f59e0b, #d97706)',
                color: '#fff', border: 'none', borderRadius: 8,
                fontWeight: 800, fontSize: '0.72rem', cursor: 'pointer',
                letterSpacing: '0.06em', textTransform: 'uppercase',
                fontFamily: "'DM Sans', Inter, sans-serif",
                boxShadow: isBlackSwan
                  ? '0 4px 16px rgba(239, 68, 68, 0.35)'
                  : '0 4px 16px rgba(245, 158, 11, 0.35)',
                transition: 'transform 0.15s ease, box-shadow 0.15s ease',
              }}
              onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-1px) scale(1.02)'; }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0) scale(1)'; }}
            >
              ✓ Acknowledged — Dismiss
            </button>
          )}
        </div>
      </div>
    );
  }

  // #6: Filter items based on selected chip
  const filteredItems = feedFilter === 'all'
    ? items
    : feedFilter === 'alerts'
      ? items.filter(item => item.type === 'alert' || item.isForeshadow)
      : items.filter(item => item.type === 'info' && !item.isForeshadow);

  const alertCount = items.filter(i => i.type === 'alert' || i.isForeshadow).length;
  const dataCount = items.filter(i => i.type === 'info' && !i.isForeshadow).length;

  return (
    <div className={styles.feedContainer}>
      <div className={styles.feedTitle} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span>📰 Market Reality Feed</span>
        {/* #6: Severity Filter Chips */}
        {items.length > 2 && (
          <div style={{ display: 'flex', gap: 3 }}>
            {FILTER_CHIPS.map(chip => {
              const count = chip.id === 'all' ? items.length : chip.id === 'alerts' ? alertCount : dataCount;
              return (
                <button
                  key={chip.id}
                  onClick={() => setFeedFilter(chip.id)}
                  style={{
                    padding: '1px 6px', borderRadius: 4, fontSize: '0.48rem', fontWeight: 700,
                    border: feedFilter === chip.id ? '1px solid rgba(94,234,212,0.4)' : '1px solid rgba(148,163,184,0.12)',
                    background: feedFilter === chip.id ? 'rgba(94,234,212,0.08)' : 'transparent',
                    color: feedFilter === chip.id ? '#5eead4' : '#64748b',
                    cursor: 'pointer', fontFamily: 'inherit', textTransform: 'uppercase',
                    letterSpacing: '0.04em', transition: 'background 0.15s ease, color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease, transform 0.15s ease',
                    display: 'flex', alignItems: 'center', gap: 3,
                  }}
                >
                  {chip.icon} {chip.label} <span style={{ opacity: 0.6 }}>({count})</span>
                </button>
              );
            })}
          </div>
        )}
      </div>
      {(showAll ? filteredItems : filteredItems.slice(0, 5)).map((item, i) => {
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
              } : effectiveType === 'alert' ? {
                borderLeft: '3px solid #ef4444',
                background: 'rgba(239,68,68,0.04)',
              } : {
                borderLeft: '3px solid rgba(59,130,246,0.3)',
              }),
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
                  <span style={{
                    fontSize: '0.42rem', fontWeight: 600,
                    padding: '1px 4px', borderRadius: 3,
                    background: item.isCarryOver ? 'rgba(148,163,184,0.08)' : 'rgba(34,197,94,0.08)',
                    color: item.isCarryOver ? '#94a3b8' : '#22c55e',
                    letterSpacing: '0.03em',
                  }}>
                    {item.isCarryOver ? '↩ carry-over' : '• new'}
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
                  fontSize: effectiveType === 'alert' ? '0.74rem' : '0.7rem', lineHeight: 1.5,
                  overflow: isExpanded ? 'visible' : 'hidden',
                  display: isExpanded ? 'block' : '-webkit-box',
                  WebkitLineClamp: isExpanded ? 'unset' : 2,
                  WebkitBoxOrient: 'vertical',
                  maxHeight: isExpanded ? 'none' : '2.8em',
                  transition: 'max-height 0.25s ease',
                }}>
                  {effectiveType === 'alert' && item.text ? (
                    <>{(() => {
                      const dotIdx = item.text.indexOf('.');
                      if (dotIdx === -1) return <strong>{item.text}</strong>;
                      return <><strong>{item.text.slice(0, dotIdx + 1)}</strong>{item.text.slice(dotIdx + 1)}</>;
                    })()}</>
                  ) : item.text}
                </div>
              </div>
            </div>
          </div>
        );
      })}
      {filteredItems.length > 5 && !showAll && (
        <button
          onClick={() => setShowAll(true)}
          style={{
            display: 'block', width: '100%', padding: '6px 0',
            border: '1px solid rgba(148,163,184,0.12)', borderRadius: 4,
            background: 'rgba(148,163,184,0.04)', color: '#94a3b8',
            fontSize: '0.62rem', fontWeight: 600, cursor: 'pointer',
            fontFamily: 'inherit', textAlign: 'center',
            transition: 'background 0.15s ease, color 0.15s ease',
            marginTop: 2,
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(94,234,212,0.08)'; e.currentTarget.style.color = '#5eead4'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(148,163,184,0.04)'; e.currentTarget.style.color = '#94a3b8'; }}
        >
          Show {filteredItems.length - 5} more ▾
        </button>
      )}
      {filteredItems.length === 0 && items.length > 0 && (
        <div className={styles.feedItem} style={{ color: '#94a3b8', textAlign: 'center', fontSize: '0.65rem' }}>
          No {feedFilter === 'alerts' ? 'alerts' : 'data items'} this round
          <button
            onClick={() => setFeedFilter('all')}
            style={{ display: 'block', margin: '6px auto 0', padding: '3px 10px', borderRadius: 4, border: '1px solid rgba(148,163,184,0.15)', background: 'transparent', color: '#5eead4', fontSize: '0.68rem', fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit' }}
          >
            Show All ({items.length})
          </button>
        </div>
      )}
      {items.length === 0 && (
        <div className={styles.feedItem} style={{ color: '#94a3b8', textAlign: 'center' }}>
          <span style={{ fontSize: '1.2rem', display: 'block', marginBottom: 4 }}>📭</span>
          No market events this round
        </div>
      )}
    </div>
  );
}
