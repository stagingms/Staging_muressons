'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './ExecutiveCockpit.module.css';
import KPIDashboard from './KPIDashboard';
import MarketRealityFeed from './MarketRealityFeed';
import InvestmentMatrix from './InvestmentMatrix';
import { DETAILED_DESCRIPTIONS } from '../utils/detailedDescriptions';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

/**
 * ExecutiveCockpit — Premium enterprise dashboard layout.
 *
 * Strict h-screen, no-scroll, 3-column layout:
 *  Left (25%): KPI Dashboard (EBITDA, Carbon, VRIO, Trust)
 *  Center (50%): Briefing + Decision Workspace
 *  Right (25%): Resources, Mailbox, Market Feed, Commit Button
 *
 * Props:
 *  - sim:             useSimulation() hook return
 *  - globalState:     current global state
 *  - businessUnits:   current BU list
 *  - roundNumber:     current round
 *  - history:         round history array
 *  - roundConfig:     current round's config
 *  - decisionParadigm: 'legacy_abc' | 'multi_toggles'
 *  - pillarSelections: current pillar selections
 *  - onPillarChange:  (selections) => void
 *  - onDecisionChoice: (choice) => void
 *  - decisionChoice:  selected A/B/C choice
 *  - onCommit:        () => void — commit turn handler
 *  - isCommitBlocked: boolean
 *  - events:          current round events
 *  - messages:        mailbox messages array
 *  - onMarkRead:      (id) => void
 *  - pillarConfig:    pillar config for multi_toggles
 *  - onOpenStakeholderMap: () => void — R1 gate
 *  - onOpenCSRD:      () => void — R2 gate
 *  - hasCompletedStakeholderMap: boolean
 *  - hasSubmittedMatrix: boolean
 *  - stakeholderAccuracy: number | null
 *  - csfPool:         number — available CSF budget
 *  - allocations:     object — { bu_id: amount }
 *  - onAllocationsChange: (allocations) => void
 *  - onResourcesOpen: () => void
 */

const ROUND_TITLES = {
  1: 'Foundations — ESG Materiality',
  2: 'Double Materiality Gate',
  3: 'Scope 3 Supply Chain',
  4: 'ESG Contagion Crisis',
  5: 'Climate Physical Risk',
  6: 'AI Ethics & Bias',
  7: 'Circular Economy Pivot',
  8: 'Blue Water Stress',
  9: 'Just Transition & Labor',
  10: 'Grand Finale — Activist Ultimatum',
};

const AREA_ICONS = { energy: '⚡', operations: '🏭', supply_chain: '🔗', offsetting: '🌱' };

// Simulation starts at the current calendar year
const BASE_YEAR = new Date().getFullYear();

export default function ExecutiveCockpit({
  sim,
  globalState,
  businessUnits,
  roundNumber,
  history,
  roundConfig,
  decisionParadigm,
  pillarSelections,
  onPillarChange,
  onDecisionChoice,
  decisionChoice,
  onCommit,
  onAdvance,
  commitResults,
  isCommitBlocked,
  events,
  messages,
  onMarkRead,
  pillarConfig,
  onOpenStakeholderMap,
  onOpenCSRD,
  hasCompletedStakeholderMap,
  hasSubmittedMatrix,
  stakeholderAccuracy,
  csfPool,
  allocations,
  onAllocationsChange,
  onResourcesOpen,
}) {
  const treasury = globalState?.corporate_treasury || 0;
  const reputation = globalState?.group_reputation || 50;
  const ebitda = globalState?.historical_ebitda || 0;
  const tco2e = globalState?.tco2e_emissions || 0;
  const vrio = globalState?.vrio_capabilities || { value: 50, rarity: 50, imitability: 100, organization: 80 };

  // Build history data for charts
  const historyData = useMemo(() => {
    const arr = (history || []).map(h => ({
      round: h.round_number,
      year: BASE_YEAR + h.round_number,
      ebitda: h.global_state?.historical_ebitda || 0,
      tco2e: h.global_state?.tco2e_emissions || 0,
      reputation: h.global_state?.group_reputation || 50,
      treasury: h.global_state?.corporate_treasury || 0,
    }));
    // Add current round only if not already in history
    const roundsInHistory = new Set(arr.map(d => d.round));
    if (!roundsInHistory.has(roundNumber)) {
      arr.push({ round: roundNumber, year: BASE_YEAR + roundNumber, ebitda, tco2e, reputation, treasury });
    }
    // When commitResults are available (results overlay showing), append
    // the post-commit state as the next data point so trends show the change
    if (commitResults?.globalState) {
      const nextRound = commitResults.newRoundNumber || roundNumber + 1;
      if (!roundsInHistory.has(nextRound)) {
        arr.push({
          round: nextRound,
          year: BASE_YEAR + nextRound,
          ebitda: commitResults.globalState.historical_ebitda || 0,
          tco2e: commitResults.globalState.tco2e_emissions || 0,
          reputation: commitResults.globalState.group_reputation || 50,
          treasury: commitResults.globalState.corporate_treasury || 0,
        });
      }
    }
    return arr;
  }, [history, roundNumber, ebitda, tco2e, reputation, treasury, commitResults]);

  // Projected costs from staged decision
  const [projectedCost, setProjectedCost] = useState(0);

  // Strategic Breakdown Hover State
  const [hoveredOpt, setHoveredOpt] = useState(null);

  // Treasury animation
  const [treasuryFlash, setTreasuryFlash] = useState(false);
  useEffect(() => {
    if (projectedCost !== 0) {
      setTreasuryFlash(true);
      const t = setTimeout(() => setTreasuryFlash(false), 600);
      return () => clearTimeout(t);
    }
  }, [projectedCost]);

  // Legacy A/B/C tile click
  const handleLegacySelect = useCallback((optionId) => {
    onDecisionChoice?.(optionId);
    // Read cost from round config impacts
    const opt = roundConfig?.options?.[optionId];
    const cost = opt?.impacts?.treasury || opt?.cost_impact || 0;
    setProjectedCost(cost);
  }, [onDecisionChoice, roundConfig]);

  // Multi-toggles pillar select
  const handlePillarSelect = useCallback((areaKey, optionKey) => {
    const next = { ...(pillarSelections || {}) };
    if (next[areaKey] === optionKey) {
      delete next[areaKey];
    } else {
      next[areaKey] = optionKey;
    }
    onPillarChange?.(next);

    // Calculate projected cost
    if (pillarConfig?.areas) {
      let cost = 0;
      for (const [ak, ok] of Object.entries(next)) {
        const opt = pillarConfig.areas[ak]?.options?.[ok];
        if (opt?.cost) cost += opt.cost;
      }
      setProjectedCost(cost);
    }
  }, [pillarSelections, onPillarChange, pillarConfig]);

  // Crisis text for briefing
  const crisisInfo = roundConfig?.crisis;
  const options = roundConfig?.options || {};

  // Format currency
  const fmtCurrency = (v) => {
    if (v === 0) return '$0';
    const abs = Math.abs(v);
    if (abs >= 1_000_000) return `${v < 0 ? '-' : ''}$${(abs / 1_000_000).toFixed(1)}M`;
    if (abs >= 1_000) return `${v < 0 ? '-' : ''}$${(abs / 1_000).toFixed(0)}K`;
    return `$${v.toFixed(0)}`;
  };

  // Mailbox — current round messages
  const currentMessages = useMemo(() => (messages || []).filter(m => (m.round || 1) === roundNumber), [messages, roundNumber]);
  const unreadCount = currentMessages.filter(m => !m.read).length;
  const [expandedMessage, setExpandedMessage] = useState(null);

  // Market events from round_config + engine events
  const marketEvents = useMemo(() => {
    const items = [];
    if (crisisInfo) {
      items.push({ type: 'info', text: `📋 ${crisisInfo.title || `Round ${roundNumber} Crisis`}: ${crisisInfo.description || ''}` });
    }
    if (events?.talent_penalty_applied > 1) {
      items.push({ type: 'alert', text: `🧠 Brain-Drain: Software OPEX inflated ${((events.talent_penalty_applied - 1) * 100).toFixed(1)}%` });
    }
    if (events?.loan_interest_payment > 0) {
      items.push({ type: 'alert', text: `🏦 Loan Interest: -${fmtCurrency(events.loan_interest_payment)} charged` });
    }
    if (events?.strike_probabilities) {
      const highs = Object.entries(events.strike_probabilities).filter(([, p]) => p > 0.3);
      if (highs.length) {
        items.push({ type: 'alert', text: `⚠️ Strike Risk: ${highs.map(([b, p]) => `${b} ${(p * 100).toFixed(0)}%`).join(', ')}` });
      }
    }
    // Filler macro events
    if (items.length < 3) {
      items.push({ type: 'info', text: '📈 Global ESG regulations tightening — compliance costs expected to rise in emerging markets.' });
      items.push({ type: 'info', text: '🌍 COP31 summit outcomes: Net-zero commitments accelerated to 2045 for heavy industries.' });
    }
    return items;
  }, [crisisInfo, events, roundNumber]);

  // Active event popup (traps/penalties)
  const activeAlert = events?.cfo_override_used ? {
    icon: '⚠️', title: 'CFO Override Penalty', body: 'Group reputation reduced by 5 points for bypassing materiality gate.'
  } : null;

  return (
    <div className={styles.cockpit} data-theme="light">
      {/* ═══ GLOBAL HEADER ═══ */}
      <header className={styles.header}>
        <div className={styles.headerLogo}>
          <span className={styles.logoMark}>M</span>
          MURESSONS
        </div>

        <div className={styles.headerCenter}>
          <span className={styles.headerYear}>Year {BASE_YEAR + roundNumber}</span>
          <span className={styles.headerDivider} />
          <span className={styles.headerModule}>Module {roundNumber}</span>
          <span className={styles.headerDivider} />
          <span>{ROUND_TITLES[roundNumber] || ''}</span>
        </div>

        <div className={styles.headerRight}>
          {projectedCost !== 0 && (
            <span className={`${styles.projectedDelta} ${projectedCost > 0 ? styles.projectedDown : styles.projectedUp}`}>
              {projectedCost > 0 ? '↓' : '↑'} {fmtCurrency(Math.abs(projectedCost))} staged
            </span>
          )}
          <motion.div
            className={`${styles.treasuryDisplay} ${treasuryFlash ? styles.treasuryFlash : ''}`}
            animate={treasuryFlash ? { scale: [1, 1.05, 1] } : {}}
            transition={{ duration: 0.4 }}
          >
            <span style={{ fontSize: '0.7rem', opacity: 0.7 }}>USD</span>
            {fmtCurrency(treasury)}
          </motion.div>
        </div>
      </header>

      {/* ═══ MAIN CONTENT (3 COLUMNS) ═══ */}
      <div className={styles.mainContent}>

        {/* ── LEFT: KPI Dashboard ─── */}
        <aside className={styles.leftSidebar}>
          <KPIDashboard
            historyData={historyData}
            ebitda={ebitda}
            tco2e={tco2e}
            vrio={vrio}
            reputation={reputation}
            projectedCost={projectedCost}
          />
        </aside>

        {/* ── CENTER: Briefing + Decisions ─── */}
        <main className={styles.centerConsole}>
          {/* Briefing Panel */}
          <div className={styles.briefingArea}>
            <div className={styles.briefingHeader}>
              <span className={styles.briefingRound}>Round {roundNumber}</span>
              <h2 className={styles.briefingTitle}>{ROUND_TITLES[roundNumber] || `Module ${roundNumber}`}</h2>
            </div>
            <div className={styles.briefingBody}>
              {crisisInfo?.description || crisisInfo?.narrative || (
                <>The board expects decisive action this quarter. Review the crisis briefing in your mailbox and select a strategic response below. Your choice will affect treasury, reputation, and long-term resilience.</>
              )}
            </div>

            {/* ── Round Gates ── */}
            {roundNumber === 1 && !hasCompletedStakeholderMap && (
              <button
                onClick={onOpenStakeholderMap}
                style={{
                  marginTop: 10, width: '100%', padding: '10px 16px',
                  background: '#1b2a4a', color: '#fff',
                  border: 'none', borderRadius: 4, fontWeight: 700, fontSize: '0.72rem',
                  cursor: 'pointer', letterSpacing: '0.06em', textTransform: 'uppercase',
                  fontFamily: 'Inter, sans-serif',
                }}
              >
                ⚖️ Complete Stakeholder Map (Required)
              </button>
            )}
            {roundNumber === 1 && hasCompletedStakeholderMap && (
              <div style={{ marginTop: 8, fontSize: '0.72rem', color: '#16a34a', fontWeight: 600 }}>
                ✅ Stakeholder Map Complete{stakeholderAccuracy != null ? ` — ${stakeholderAccuracy.toFixed(0)}% accuracy` : ''}
              </div>
            )}
            {roundNumber === 2 && !hasSubmittedMatrix && (
              <button
                onClick={onOpenCSRD}
                style={{
                  marginTop: 10, width: '100%', padding: '10px 16px',
                  background: '#b91c1c', color: '#fff',
                  border: 'none', borderRadius: 4, fontWeight: 700, fontSize: '0.72rem',
                  cursor: 'pointer', letterSpacing: '0.06em', textTransform: 'uppercase',
                  fontFamily: 'Inter, sans-serif',
                }}
              >
                🚨 Complete CSRD Assessment (Required)
              </button>
            )}
            {roundNumber === 2 && hasSubmittedMatrix && (
              <div style={{ marginTop: 8, fontSize: '0.68rem', color: '#15803d', fontWeight: 600, letterSpacing: '0.02em' }}>✅ CSRD Assessment Submitted</div>
            )}
          </div>

          {/* Resource Allocation Matrix */}
          <div className={styles.decisionArea} style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: 8 }}>
            <InvestmentMatrix
              csfPool={csfPool}
              globalState={globalState}
              businessUnits={businessUnits}
              allocations={allocations}
              onAllocationsChange={onAllocationsChange}
            />
          </div>

          {/* Decision Workspace */}
          <div className={styles.decisionArea}>
            <div className={styles.decisionHeader}>
              <span className={styles.decisionLabel}>
                {decisionParadigm === 'multi_toggles' ? '🎛️ Strategic Pillars' : '📋 Strategic Options'}
              </span>
              {projectedCost !== 0 && (
                <span className={`${styles.projectedDelta} ${projectedCost > 0 ? styles.projectedDown : styles.projectedUp}`}>
                  Impact: {fmtCurrency(projectedCost)}
                </span>
              )}
            </div>

            {decisionParadigm === 'multi_toggles' ? (
              /* ── Multi-Toggles: 4 pillar tiles ── */
              <div className={styles.pillarTiles}>
                {pillarConfig?.areas && Object.entries(pillarConfig.areas).map(([areaKey, area]) => {
                  const selectedOpt = pillarSelections?.[areaKey];
                  return (
                    <div
                      key={areaKey}
                      className={`${styles.pillarTile} ${selectedOpt ? styles.pillarTileActive : ''}`}
                    >
                      <div className={styles.pillarIcon}>{AREA_ICONS[areaKey] || '📌'}</div>
                      <div className={styles.pillarLabel}>{area.label}</div>
                      <select
                        className={styles.pillarSelect}
                        value={selectedOpt || ''}
                        onChange={(e) => handlePillarSelect(areaKey, e.target.value || null)}
                        onMouseEnter={() => selectedOpt && setHoveredOpt({
                          title: area.options[selectedOpt]?.title,
                          desc: DETAILED_DESCRIPTIONS.pillars?.[roundNumber]?.[areaKey]?.[selectedOpt] || area.options[selectedOpt]?.description
                        })}
                        onMouseLeave={() => setHoveredOpt(null)}
                      >
                        <option value="">— Select —</option>
                        {area.options && Object.entries(area.options).map(([optKey, opt]) => (
                          <option key={optKey} value={optKey}>
                            {opt.title} ({fmtCurrency(opt.cost || 0)})
                          </option>
                        ))}
                      </select>
                    </div>
                  );
                })}
              </div>
            ) : (
              /* ── Legacy A/B/C: 3 horizontal tiles ── */
              <div className={styles.decisionTiles}>
                {['option_a', 'option_b', 'option_c'].map((optId) => {
                  const opt = options[optId];
                  if (!opt) return null;
                  const isActive = decisionChoice === optId;
                  return (
                    <div
                      key={optId}
                      className={`${styles.decisionTile} ${isActive ? styles.decisionTileActive : ''}`}
                      onClick={() => handleLegacySelect(optId)}
                      onMouseEnter={() => setHoveredOpt({
                        title: opt.title,
                        desc: DETAILED_DESCRIPTIONS.narrative?.[roundNumber]?.[optId] || opt.description
                      })}
                      onMouseLeave={() => setHoveredOpt(null)}
                    >
                      <div className={styles.tileLabel}>
                        {optId === 'option_a' ? 'Option A' : optId === 'option_b' ? 'Option B' : 'Option C'}
                      </div>
                      <div className={styles.tileTitle}>{opt.title}</div>
                      <p className={styles.tileDesc}>{opt.description}</p>
                      {(opt.impacts?.treasury || opt.cost_impact) ? (
                        <div className={`${styles.tileCost} ${(opt.impacts?.treasury || opt.cost_impact) < 0 ? styles.tileCostPositive : ''}`}>
                          {fmtCurrency(opt.impacts?.treasury || opt.cost_impact)}
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Strategic Breakdown Panel */}
            <div className={styles.breakdownPanel}>
              <div className={styles.breakdownLabels}>
                <span className={styles.breakdownIcon}>🔍</span>
                <span className={styles.breakdownTitle}>STRATEGIC BREAKDOWN</span>
              </div>
              <div className={styles.breakdownContent}>
                {hoveredOpt ? (
                  <p><strong>{hoveredOpt.title}:</strong> {hoveredOpt.desc}</p>
                ) : decisionParadigm === 'legacy_abc' && decisionChoice ? (
                  <p><strong>{options[decisionChoice]?.title}:</strong> {DETAILED_DESCRIPTIONS.narrative?.[roundNumber]?.[decisionChoice] || options[decisionChoice]?.description}</p>
                ) : (
                  <p className={styles.breakdownPlaceholder}>
                    {decisionParadigm === 'multi_toggles' 
                      ? "Hover over an active Strategic Pillar dropdown to view its detailed implications."
                      : "Hover over a strategic option above to view its detailed implications."}
                  </p>
                )}
              </div>
            </div>

          </div>
        </main>

        {/* ── RIGHT SIDEBAR ─── */}
        <aside className={styles.rightSidebar}>
          {/* Resources Tab (10%) */}
          <div className={styles.rightResources}>
            <div className={styles.resourcesTab} onClick={onResourcesOpen} style={{ cursor: 'pointer' }}>
              <span className={styles.resourcesLabel}>
                📎 Resources
              </span>
              <span style={{ fontSize: '0.6rem', color: '#94a3b8' }}>▶</span>
            </div>
          </div>

          {/* Executive Mailbox (40%) */}
          <div className={styles.rightMailbox}>
            <div className={styles.mailboxSection}>
              <div className={styles.mailboxTitle}>
                📬 Mailbox — Round {roundNumber}
                {unreadCount > 0 && <span className={styles.mailboxBadge}>{unreadCount}</span>}
              </div>
              {currentMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={styles.feedItem}
                  onClick={() => { onMarkRead?.(msg.id); setExpandedMessage(msg); }}
                  style={{ cursor: 'pointer', opacity: msg.read ? 0.6 : 1 }}
                >
                  <strong style={{ fontSize: '0.68rem', color: '#0f172a' }}>{msg.title}</strong>
                  <p style={{ margin: '2px 0 0', fontSize: '0.65rem', color: '#64748b' }}>{msg.body?.substring(0, 120)}...</p>
                </div>
              ))}
              {currentMessages.length === 0 && (
                <div className={styles.feedItem} style={{ color: '#94a3b8', textAlign: 'center' }}>No messages this round</div>
              )}

              {/* ── Previous Rounds Accordion ── */}
              {(() => {
                const archivedRounds = {};
                (messages || []).filter(m => (m.round || 1) < roundNumber).forEach(m => {
                  const r = m.round || 1;
                  if (!archivedRounds[r]) archivedRounds[r] = [];
                  archivedRounds[r].push(m);
                });
                const roundKeys = Object.keys(archivedRounds).sort((a, b) => Number(b) - Number(a));
                if (roundKeys.length === 0) return null;
                return roundKeys.map(rk => {
                  const r = Number(rk);
                  const items = archivedRounds[r];
                  return (
                    <ArchiveAccordion key={r} round={r} items={items} onMarkRead={onMarkRead} onExpand={setExpandedMessage} />
                  );
                });
              })()}
            </div>
          </div>

          {/* Market Reality Feed (40%) */}
          <div className={styles.rightMarket}>
            <MarketRealityFeed items={marketEvents} activeAlert={activeAlert} />
          </div>

          {/* Commit / Advance Footer (two buttons) */}
          <div className={styles.rightCommit}>
            <div className={styles.twoButtonRow}>
              <motion.button
                className={`${styles.commitBtnHalf} ${commitResults ? styles.commitBtnDone : ''}`}
                disabled={isCommitBlocked || !!commitResults}
                onClick={onCommit}
                whileHover={{ scale: (isCommitBlocked || commitResults) ? 1 : 1.02 }}
                whileTap={{ scale: (isCommitBlocked || commitResults) ? 1 : 0.98 }}
              >
                {commitResults ? '✅ Committed' : '▶ Commit'}
              </motion.button>
              <motion.button
                className={`${styles.advanceBtnHalf} ${!commitResults ? styles.advanceBtnLocked : ''}`}
                disabled={!commitResults}
                onClick={onAdvance}
                whileHover={{ scale: commitResults ? 1.02 : 1 }}
                whileTap={{ scale: commitResults ? 0.98 : 1 }}
              >
                {commitResults ? '⏩ Advance' : '🔒 Advance'}
              </motion.button>
            </div>
          </div>
        </aside>

        {/* ── Full Message Modal (portaled to body) ── */}
        {expandedMessage && typeof document !== 'undefined' && createPortal(
          <div
            onClick={() => setExpandedMessage(null)}
            style={{
              position: 'fixed', inset: 0, zIndex: 99999,
              background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(6px)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              padding: '2rem',
            }}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              style={{
                background: '#fff', borderRadius: '16px', maxWidth: '560px',
                width: '100%', maxHeight: '80vh', overflow: 'auto',
                boxShadow: '0 25px 60px rgba(0,0,0,0.3)',
                animation: 'fadeSlideUp 0.25s ease-out',
              }}
            >
              {/* Header */}
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '1rem 1.25rem', borderBottom: '1px solid #e2e8f0',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{
                    fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
                    padding: '3px 8px', borderRadius: '4px', letterSpacing: '0.05em',
                    background: expandedMessage.type === 'crisis' ? '#fef2f2' : expandedMessage.type === 'facilitator' ? '#f0fdf4' : '#f0f4ff',
                    color: expandedMessage.type === 'crisis' ? '#dc2626' : expandedMessage.type === 'facilitator' ? '#16a34a' : '#4338ca',
                  }}>
                    {expandedMessage.type?.toUpperCase() || 'MESSAGE'}
                  </span>
                  {expandedMessage.round && (
                    <span style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600 }}>
                      Round {expandedMessage.round}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => setExpandedMessage(null)}
                  style={{
                    background: '#f1f5f9', border: 'none', borderRadius: '50%',
                    width: 28, height: 28, cursor: 'pointer', fontSize: '0.85rem',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#64748b', fontWeight: 700,
                  }}
                >✕</button>
              </div>
              {/* Title */}
              <h3 style={{
                margin: 0, padding: '0.75rem 1.25rem 0',
                fontSize: '1rem', fontWeight: 700, color: '#0f172a',
              }}>{expandedMessage.title}</h3>
              {/* Body */}
              <div style={{
                padding: '0.75rem 1.25rem 1.25rem',
                fontSize: '0.88rem', lineHeight: 1.7, color: '#334155',
                whiteSpace: 'pre-wrap',
              }}>{expandedMessage.body}</div>
            </div>
          </div>,
          document.body
        )}
      </div>

      {/* ═══ COMMIT RESULTS OVERLAY ═══ */}
      <AnimatePresence>
        {commitResults && !sim.gameOver && (
          <motion.div
            className={styles.resultsOverlay}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <motion.div
              className={styles.resultsPanel}
              initial={{ y: 40, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -20, opacity: 0 }}
              transition={{ duration: 0.35, ease: 'easeOut' }}
            >
              <div className={styles.resultsBadge}>Round {roundNumber} Results</div>
              <h2 className={styles.resultsTitle}>📊 Turn Committed Successfully</h2>
              <p className={styles.resultsSubtitle}>Review your round outcomes before advancing to Round {commitResults.newRoundNumber}.</p>

              <div className={styles.resultsGrid}>
                <div className={styles.resultCard}>
                  <div className={styles.resultCardIcon}>💰</div>
                  <div className={styles.resultCardLabel}>Treasury</div>
                  <div className={styles.resultCardValue}>{fmtCurrency(commitResults.globalState?.corporate_treasury || 0)}</div>
                </div>
                <div className={styles.resultCard}>
                  <div className={styles.resultCardIcon}>📈</div>
                  <div className={styles.resultCardLabel}>EBITDA</div>
                  <div className={styles.resultCardValue}>{fmtCurrency(commitResults.globalState?.historical_ebitda || 0)}</div>
                </div>
                <div className={styles.resultCard}>
                  <div className={styles.resultCardIcon}>🌍</div>
                  <div className={styles.resultCardLabel}>Reputation</div>
                  <div className={styles.resultCardValue}>{commitResults.globalState?.group_reputation?.toFixed(0) || '—'}</div>
                </div>
                <div className={styles.resultCard}>
                  <div className={styles.resultCardIcon}>🏭</div>
                  <div className={styles.resultCardLabel}>CO₂ Emissions</div>
                  <div className={styles.resultCardValue}>{(commitResults.globalState?.tco2e_emissions || 0).toLocaleString()} t</div>
                </div>
              </div>

              {/* Trend Sparklines */}
              {historyData.length > 1 && (
                <div style={{
                  display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem',
                  marginBottom: '1rem',
                }}>
                  {[
                    { key: 'treasury', label: 'Treasury Trend', color: '#3b82f6', fmt: (v) => fmtCurrency(v) },
                    { key: 'ebitda', label: 'EBITDA Trend', color: '#16a34a', fmt: (v) => fmtCurrency(v) },
                    { key: 'reputation', label: 'Reputation Trend', color: '#f59e0b', fmt: (v) => v?.toFixed(0) },
                    { key: 'tco2e', label: 'CO₂ Emissions Trend', color: '#ef4444', fmt: (v) => `${(v || 0).toLocaleString()} t` },
                  ].map(({ key, label, color, fmt }) => {
                    // Compute Y-axis domain: start from 0 for reputation, otherwise use padded min/max
                    const values = historyData.map(d => d[key] || 0);
                    const minVal = Math.min(...values);
                    const maxVal = Math.max(...values);
                    const padding = (maxVal - minVal) * 0.15 || maxVal * 0.1 || 1;
                    const yDomain = key === 'reputation'
                      ? [0, 100]
                      : [Math.max(0, minVal - padding), maxVal + padding];

                    return (
                    <div key={key} style={{
                      background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
                      padding: '0.5rem 0.6rem 0.3rem',
                    }}>
                      <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.2rem' }}>
                        {label}
                      </div>
                      <ResponsiveContainer width="100%" height={72}>
                        <AreaChart data={historyData} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                          <defs>
                            <linearGradient id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                              <stop offset="95%" stopColor={color} stopOpacity={0.05} />
                            </linearGradient>
                          </defs>
                          <XAxis dataKey="year" tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                          <YAxis hide domain={yDomain} />
                          <Tooltip
                            contentStyle={{ fontSize: '0.72rem', borderRadius: 6, border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                            formatter={(v) => [fmt(v), label.replace(' Trend', '')]}
                            labelFormatter={(year) => `Year ${year}`}
                          />
                          <Area type="monotone" dataKey={key} stroke={color} strokeWidth={2} fill={`url(#grad-${key})`} dot={{ r: 3, fill: color, strokeWidth: 0 }} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  );})}
                </div>
              )}

              {/* Events summary */}
              {commitResults.events && Object.keys(commitResults.events).length > 0 && (
                <div className={styles.resultsEvents}>
                  <div className={styles.resultsEventsTitle}>⚡ Key Events</div>
                  {commitResults.events.talent_penalty_applied > 1 && (
                    <div className={styles.resultsEventItem}>🧠 Brain-Drain: Software OPEX inflated by {((commitResults.events.talent_penalty_applied - 1) * 100).toFixed(1)}%</div>
                  )}
                  {commitResults.events.loan_interest_payment > 0 && (
                    <div className={styles.resultsEventItem}>🏦 Loan Interest: -{fmtCurrency(commitResults.events.loan_interest_payment)}</div>
                  )}
                  {commitResults.events.auto_injected_messages?.length > 0 && (
                    <div className={styles.resultsEventItem}>📬 {commitResults.events.auto_injected_messages.length} new swipe file(s) delivered</div>
                  )}
                  {commitResults.events.strike_probabilities && (
                    <div className={styles.resultsEventItem}>
                      ⚠️ Strike risk: {Object.entries(commitResults.events.strike_probabilities)
                        .filter(([, p]) => p > 0.1)
                        .map(([bu, p]) => `${bu} ${(p * 100).toFixed(0)}%`)
                        .join(', ') || 'Low across all BUs'}
                    </div>
                  )}
                </div>
              )}

              <motion.button
                className={styles.advanceBtnLarge}
                onClick={onAdvance}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
              >
                ⏩ Advance to Round {commitResults.newRoundNumber}
              </motion.button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ── Sub-component: Archive Accordion for previous rounds ── */
function ArchiveAccordion({ round, items, onMarkRead, onExpand }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{
      marginTop: 4,
      borderTop: '1px solid #eef0f6',
    }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '5px 8px',
          background: open ? '#f0f4ff' : '#f7f8fc',
          border: 'none',
          borderRadius: 3,
          cursor: 'pointer',
          fontSize: '0.6rem',
          fontWeight: 700,
          color: '#6b7a8d',
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          fontFamily: 'Inter, sans-serif',
          transition: 'background 0.15s',
        }}
      >
        <span>{open ? '▾' : '▸'} Round {round}</span>
        <span style={{
          fontSize: '0.52rem',
          background: '#e2e8f0',
          color: '#475569',
          padding: '1px 5px',
          borderRadius: 3,
          fontWeight: 700,
        }}>{items.length}</span>
      </button>
      {open && items.map(msg => (
        <div
          key={msg.id}
          onClick={() => { onMarkRead?.(msg.id); onExpand?.(msg); }}
          style={{
            padding: '4px 8px 4px 16px',
            fontSize: '0.63rem',
            color: '#64748b',
            lineHeight: 1.5,
            borderLeft: '2px solid #d1d5db',
            marginLeft: 8,
            marginBottom: 2,
            cursor: 'pointer',
            opacity: msg.read ? 0.5 : 0.8,
            transition: 'opacity 0.15s',
          }}
        >
          <strong style={{ fontSize: '0.63rem', color: '#334155' }}>{msg.title}</strong>
          <p style={{ margin: '1px 0 0', fontSize: '0.6rem', color: '#94a3b8' }}>
            {msg.body?.substring(0, 80)}...
          </p>
        </div>
      ))}
    </div>
  );
}
