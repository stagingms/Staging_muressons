'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './StakeholderAgentPanel.module.css';
import StakeholderAvatar from './StakeholderAvatar';

/* ═════════════════════════════════════════════════════════════════
 *  STAKEHOLDER AGENT PANEL
 *
 *  Displays the 5 autonomous stakeholder agents with:
 *  - Live tolerance bars with escalation zone markers
 *  - Stage badges (dormant → watching → agitated → hostile → triggered)
 *  - Trend arrows & patience counters
 *  - Agent dialogue / threat messages
 *  - Cascade chain visualization
 *  - Alert flashes on stage transitions
 *
 *  Props:
 *   - agentSummary:   array from backend get_agent_summary()
 *   - agentActions:   array from diagnostics.agent_actions
 *   - cascadesFired:  array from diagnostics.cascades_fired
 *   - roundNumber:    current round
 * ═════════════════════════════════════════════════════════════════ */

const STAGE_META = {
  dormant:   { label: 'DORMANT',   color: '#10b981', bg: 'rgba(16,185,129,0.10)', icon: '😊', order: 0 },
  watching:  { label: 'WATCHING',  color: '#f59e0b', bg: 'rgba(245,158,11,0.10)', icon: '👀', order: 1 },
  agitated:  { label: 'AGITATED',  color: '#f97316', bg: 'rgba(249,115,22,0.10)', icon: '😠', order: 2 },
  hostile:   { label: 'HOSTILE',   color: '#ef4444', bg: 'rgba(239,68,68,0.12)',  icon: '🔥', order: 3 },
  triggered: { label: 'TRIGGERED', color: '#dc2626', bg: 'rgba(220,38,38,0.15)', icon: '💥', order: 4 },
};

const TREND_ICONS = {
  improving:     { icon: '📈', label: 'Improving', color: '#10b981' },
  stable:        { icon: '➡️', label: 'Stable',    color: '#64748b' },
  deteriorating: { icon: '📉', label: 'Worsening', color: '#ef4444' },
  'n/a':         { icon: '—',  label: 'N/A',       color: '#475569' },
};

function AgentCard({ agent, action, isExpanded, onToggle }) {
  const stageMeta = STAGE_META[action?.stage || agent?.stage || 'dormant'];
  const trendMeta = TREND_ICONS[action?.trend || agent?.trend || 'stable'];
  const isTriggered = (action?.stage || agent?.stage) === 'triggered';
  const stageChanged = action?.stage_changed;

  return (
    <motion.div
      className={`${styles.agentCard} ${isTriggered ? styles.agentTriggered : ''} ${stageChanged ? styles.agentStageChanged : ''}`}
      style={{ '--agent-color': action?.color || agent?.color || '#888' }}
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header row */}
      <div className={styles.agentHeader} onClick={onToggle}>
        <div className={styles.agentIdentity}>
          {/* SA-A/SA-B: profile silhouette + state ring replaces the emoji AND
              the flat ToleranceBar. Colour = stage (STAGE_META, single source);
              ring sweep = tolerance/max; ticks = thresholds; number = tolerance. */}
          <StakeholderAvatar
            color={stageMeta.color}
            stage={action?.stage || agent?.stage || 'dormant'}
            tolerance={action?.tolerance ?? agent?.tolerance ?? 50}
            maxTolerance={agent?.max_tolerance || 100}
            thresholds={agent?.thresholds || {}}
          />
          <div className={styles.agentInfo}>
            <div className={styles.agentName}>
              {action?.icon || agent?.icon} {action?.name || agent?.name}
            </div>
            <div className={styles.agentTitle}>
              {action?.title || agent?.title || ''}
            </div>
          </div>
        </div>
        <div className={styles.agentMeta}>
          {/* Stage badge */}
          <div
            className={styles.stageBadge}
            style={{ color: stageMeta.color, background: stageMeta.bg }}
          >
            <span className={styles.stageIcon}>{stageMeta.icon}</span>
            {stageMeta.label}
          </div>
          {/* Trend */}
          <div className={styles.trendBadge} style={{ color: trendMeta.color }}>
            {trendMeta.icon}
          </div>
          {/* Expand arrow */}
          <span className={styles.expandArrow}>
            {isExpanded ? '▲' : '▼'}
          </span>
        </div>
      </div>

      {/* SA-B: tolerance now lives in the avatar ring above (sweep + ticks +
          number); the standalone ToleranceBar was retired. */}

      {/* Expanded details */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            className={styles.agentDetails}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            {/* Message / dialogue */}
            {action?.message && (
              <div className={styles.agentDialogue}>
                <div className={styles.dialogueQuote}>"{action.message}"</div>
              </div>
            )}

            {/* Violations */}
            {action?.violations?.length > 0 && (
              <div className={styles.violationsList}>
                <div className={styles.violationsHeader}>⚠ Red Line Violations</div>
                {action.violations.map((v, i) => (
                  <div key={`${v.metric}-${v.direction}`} className={styles.violationRow}>
                    <span className={styles.violationMetric}>
                      {v.metric.replace(/_/g, ' ')}
                    </span>
                    <span className={styles.violationValue}>
                      {typeof v.value === 'number' ? v.value.toFixed(1) : v.value}
                    </span>
                    <span className={styles.violationRedLine}>
                      ({v.direction} {v.red_line})
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Stats row */}
            <div className={styles.statsRow}>
              <div className={styles.statPill}>
                <span className={styles.statLabel}>Patience</span>
                <span className={styles.statValue}>
                  {action?.patience_counter ?? agent?.patience_counter ?? 0} rounds
                </span>
              </div>
              <div className={styles.statPill}>
                <span className={styles.statLabel}>Tolerance Δ</span>
                <span
                  className={styles.statValue}
                  style={{ color: (action?.tolerance_delta || 0) >= 0 ? '#10b981' : '#ef4444' }}
                >
                  {(action?.tolerance_delta || 0) >= 0 ? '+' : ''}
                  {(action?.tolerance_delta || 0).toFixed(1)}
                </span>
              </div>
              <div className={styles.statPill}>
                <span className={styles.statLabel}>Trend</span>
                <span className={styles.statValue} style={{ color: trendMeta.color }}>
                  {trendMeta.label}
                </span>
              </div>
            </div>

            {/* Triggered event details */}
            {action?.triggered_event && (
              <div className={styles.triggeredEvent}>
                <div className={styles.triggeredTitle}>{action.triggered_event.title}</div>
                <div className={styles.triggeredNarrative}>{action.triggered_event.narrative}</div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function StakeholderAgentPanel({
  agentSummary = [],
  agentActions = [],
  cascadesFired = [],
  interferenceActive = [],
  roundNumber,
}) {
  const [expandedAgents, setExpandedAgents] = useState({});
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleAgent = (id) => {
    setExpandedAgents((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Merge summary + actions for display
  const mergedAgents = useMemo(() => {
    return agentSummary.map((agent) => {
      const action = agentActions.find((a) => a.agent_id === agent.agent_id) || {};
      return { ...agent, action };
    });
  }, [agentSummary, agentActions]);

  // Sort by escalation severity (most critical first)
  const sortedAgents = useMemo(() => {
    return [...mergedAgents].sort((a, b) => {
      const stageA = STAGE_META[a.action?.stage || a.stage]?.order || 0;
      const stageB = STAGE_META[b.action?.stage || b.stage]?.order || 0;
      return stageB - stageA;
    });
  }, [mergedAgents]);

  // Counts
  const triggeredCount = mergedAgents.filter(
    (a) => (a.action?.stage || a.stage) === 'triggered'
  ).length;
  const hostileCount = mergedAgents.filter(
    (a) => (a.action?.stage || a.stage) === 'hostile'
  ).length;
  const watchCount = mergedAgents.filter(
    (a) => ['watching', 'agitated'].includes(a.action?.stage || a.stage)
  ).length;

  if (mergedAgents.length === 0) return null;

  return (
    <div className={styles.panel}>
      {/* Panel Header */}
      <div className={styles.panelHeader} onClick={() => setIsCollapsed(!isCollapsed)}>
        <div className={styles.panelTitle}>
          <span className={styles.panelIcon}>🎭</span>
          <span>AUTONOMOUS STAKEHOLDERS</span>
        </div>
        <div className={styles.panelBadges}>
          {triggeredCount > 0 && (
            <span className={`${styles.countBadge} ${styles.badgeCritical}`}>
              {triggeredCount} 💥
            </span>
          )}
          {hostileCount > 0 && (
            <span className={`${styles.countBadge} ${styles.badgeHostile}`}>
              {hostileCount} 🔥
            </span>
          )}
          {watchCount > 0 && (
            <span className={`${styles.countBadge} ${styles.badgeWatch}`}>
              {watchCount} 👀
            </span>
          )}
          {interferenceActive.length > 0 && (
            <span className={`${styles.countBadge} ${styles.badgeWatch}`}
              style={{ background: 'rgba(139,92,246,0.12)', color: '#c4b5fd', borderColor: 'rgba(139,92,246,0.25)' }}>
              {interferenceActive.length} 📡
            </span>
          )}
          <span className={styles.collapseArrow}>
            {isCollapsed ? '▼' : '▲'}
          </span>
        </div>
      </div>

      <AnimatePresence>
        {!isCollapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className={styles.panelBody}
          >
            {/* Agent cards */}
            {sortedAgents.map((agent) => (
              <AgentCard
                key={agent.agent_id}
                agent={agent}
                action={agent.action}
                isExpanded={!!expandedAgents[agent.agent_id]}
                onToggle={() => toggleAgent(agent.agent_id)}
              />
            ))}

            {/* Inter-Agent Interference alerts */}
            {interferenceActive.length > 0 && (
              <div className={styles.interferenceSection}>
                <div className={styles.interferenceTitle}>
                  <span>📡</span> Feedback Loops Active
                </div>
                {interferenceActive.map((ie, i) => {
                  const agentA = ie.agents?.[0]?.replace(/the_/g, '').replace(/_/g, ' ') || '?';
                  const agentB = ie.agents?.[1]?.replace(/the_/g, '').replace(/_/g, ' ') || '?';
                  const pct = Math.round((ie.multiplier - 1) * 100);
                  return (
                    <div key={`${ie.agents?.[0] || 'a'}-${ie.agents?.[1] || 'b'}-${i}`} className={styles.interferenceCard}>
                      <div className={styles.interferenceAgents}>
                        <span style={{ textTransform: 'capitalize' }}>{agentA}</span>
                        <span className={styles.interferenceLink}>⇄</span>
                        <span style={{ textTransform: 'capitalize' }}>{agentB}</span>
                        <span className={styles.interferenceMultiplier}>
                          ×{ie.multiplier} ({pct}% faster)
                        </span>
                      </div>
                      {ie.narrative && (
                        <div className={styles.interferenceNarrative}>{ie.narrative}</div>
                      )}
                      {ie.theory && (
                        <div className={styles.interferenceTheory}>🎓 {ie.theory}</div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Cascade chain log */}
            {cascadesFired.length > 0 && (
              <div className={styles.cascadeSection}>
                <div className={styles.cascadeTitle}>⚡ Cascade Chain</div>
                {cascadesFired.map((c, i) => (
                  <div key={`${c.source || 'src'}->${c.target || 'tgt'}-${i}`} className={styles.cascadeRow}>
                    <span className={styles.cascadeSource}>
                      {c.source?.replace(/the_/g, '').replace(/_/g, ' ')}
                    </span>
                    <span className={styles.cascadeArrow}>→</span>
                    <span className={styles.cascadeTarget}>
                      {c.target?.replace(/the_/g, '').replace(/_/g, ' ')}
                    </span>
                    <span className={styles.cascadeHit}>
                      −{c.tolerance_hit} tolerance
                    </span>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
