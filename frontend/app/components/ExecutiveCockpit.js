'use client';
import React from 'react';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './ExecutiveCockpit.module.css';
import KPIDashboard from './KPIDashboard';
import MarketRealityFeed from './MarketRealityFeed';
import InvestmentMatrix from './InvestmentMatrix';
import CountdownTimer from './CountdownTimer';
import { DETAILED_DESCRIPTIONS } from '../utils/detailedDescriptions';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine } from 'recharts';
import { calculateRoundStockPrice, IPO_PRICE } from './stockValuationEngine';
import { roundToQuarter } from '../utils/roundToQuarter';
import EngineEventsPanel from './EngineEventsPanel';
import CompetitorIntelligence from './CompetitorIntelligence';
import DecisionHistory from './DecisionHistory';

// AI Board Member Personas (Improvement #4.2)
const BOARD_PERSONAS = {
  financial: { name: 'Sarah Chen, CFO', avatar: '👩‍💼', color: '#6366f1' },
  sustainability: { name: 'Dr. Kwame Asante, CSO', avatar: '🧑‍🔬', color: '#16a34a' },
  legal: { name: 'Marcus Wong, General Counsel', avatar: '👨‍⚖️', color: '#f59e0b' },
  crisis: { name: 'Elena Vasquez, CRO', avatar: '🧑‍💻', color: '#ef4444' },
  default: { name: 'Board of Directors', avatar: '🏛️', color: '#64748b' },
};

function getPersona(msg) {
  const t = (msg.type || '').toLowerCase();
  const title = (msg.title || '').toLowerCase();
  if (t === 'crisis' || title.includes('crisis') || title.includes('alert')) return BOARD_PERSONAS.crisis;
  if (t === 'facilitator') return BOARD_PERSONAS.sustainability;
  if (title.includes('financial') || title.includes('treasury') || title.includes('ebitda')) return BOARD_PERSONAS.financial;
  if (title.includes('legal') || title.includes('regulation') || title.includes('compliance')) return BOARD_PERSONAS.legal;
  return BOARD_PERSONAS.default;
}

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

const ROUND_TITLES_SDG = {
  1: 'Mandate Selection — SDG Prioritisation',
  2: 'WASH Crisis — SDG 6',
  3: 'Education Investment — SDG 4 & 8',
  4: 'Pandemic Response — SDG 3',
  5: 'Climate Resilience — SDG 13',
  6: 'Digital Divide — SDG 9 & 17',
  7: 'Resource Extraction — SDG 12 & 15',
  8: 'Just Transition — SDG 8 & 10',
  9: 'Debt & Finance — SDG 1 & 17',
  10: 'Legacy of Leadership — All SDGs',
};

const AREA_ICONS = { energy: '⚡', operations: '🏭', supply_chain: '🔗', offsetting: '🌱' };

// Simulation starts at the current calendar year
const BASE_YEAR = new Date().getFullYear();

// Pre-compute quarter label for a given round using the shared utility
const getRoundLabel = (round) => roundToQuarter(round, BASE_YEAR).label;

export default function ExecutiveCockpit({
  sim,
  globalState,
  businessUnits,
  actionToolbar = null,
  roundChecklist = null,
  isHealthcare,
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
  hasAllocated,
  hasReadBriefing,
  onLogout,
  lastSavedAt,
}) {
  // Sequential gating: determine if round prerequisite is met
  const hasSecondStage = roundNumber === 1 || roundNumber === 2;
  const secondStageDone = roundNumber === 1 ? hasCompletedStakeholderMap
    : roundNumber === 2 ? hasSubmittedMatrix
    : true; // R3-R10: no special prerequisite
  const roundPrerequisiteMet = hasSecondStage ? secondStageDone : true;
  // For strategic decision gating: briefing must be read, and second stage (if any) must be done
  const canAccessStrategy = hasReadBriefing && roundPrerequisiteMet;

  // Logout confirmation (2-click to prevent accidents)
  const [logoutConfirm, setLogoutConfirm] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState('mailbox');
  useEffect(() => {
    if (!logoutConfirm) return;
    const t = setTimeout(() => setLogoutConfirm(false), 3500);
    return () => clearTimeout(t);
  }, [logoutConfirm]);
  const hasDecision = decisionParadigm === 'multi_toggles'
    ? Object.keys(pillarSelections || {}).length > 0
    : !!decisionChoice;
  // For capital allocation gating: strategic decision must be made
  const canAccessAllocation = canAccessStrategy && hasDecision;
  const treasury = globalState?.corporate_treasury || 0;
  const reputation = globalState?.group_reputation || 50;
  const ebitda = globalState?.historical_ebitda || 0;
  const tco2e = globalState?.tco2e_emissions || 0;
  const vrio = globalState?.vrio_capabilities || { value: 50, rarity: 50, imitability: 100, organization: 80 };
  
  // Advanced Climate Engine Extracted State
  const greenFund = globalState?.green_transition_fund || 0;
  const costOfCapital = globalState?.cost_of_capital || 0.05;
  const tippingPointActive = globalState?.tipping_point_active || false;
  const pendingProjects = globalState?.pending_capex_projects || [];

  // SDG Edition Detection
  const isSDG = decisionParadigm === 'un_sdg';
  const politicalCapital = globalState?.political_capital || 0;
  const communityTrust = globalState?.community_trust_score || 0;
  const globalEmissions = globalState?.global_emissions_intensity || 0;
  const activeRoundTitles = isSDG ? ROUND_TITLES_SDG : ROUND_TITLES;

  // Healthcare Edition Extra Metrics
  const systemBurnout = useMemo(() => {
    if (!isHealthcare || !businessUnits?.length) return 0;
    const total = businessUnits.reduce((acc, bu) => acc + (bu.staff_burnout_index || 0), 0);
    return total / businessUnits.length;
  }, [isHealthcare, businessUnits]);

  const totalBedCapacity = useMemo(() => {
    if (!isHealthcare || !businessUnits?.length) return 0;
    // bed_capacity_utilization is stored as a 0–100 utilisation %; derive absolute count for display
    return businessUnits.reduce((acc, bu) => acc + (bu.bed_capacity_utilization || 0), 0);
  }, [isHealthcare, businessUnits]);

  // Build history data for charts
  const historyData = useMemo(() => {
    const raw = (history || []);
    const arr = raw.map((h, idx) => {
      const prev = idx > 0 ? raw[idx - 1] : null;
      return {
        round: h.round_number,
        year: roundToQuarter(h.round_number, BASE_YEAR).year,
        ebitda: h.global_state?.historical_ebitda || 0,
        tco2e: h.global_state?.tco2e_emissions || 0,
        reputation: h.global_state?.group_reputation || 50,
        treasury: h.global_state?.corporate_treasury || 0,
        synergy: h.global_state?.synergy_multiplier || 1.0,
        previous_ebitda: prev?.global_state?.historical_ebitda || 0,
        previous_treasury: prev?.global_state?.corporate_treasury || 0,
        previous_reputation: prev?.global_state?.group_reputation || 50,
        previous_tco2e: prev?.global_state?.tco2e_emissions || 0,
        bu_count: h.business_units?.length || 0,
        decisions: h.global_state?.active_event_flags?.round_decisions || null,
      };
    });
    // Add current round only if not already in history
    const roundsInHistory = new Set(arr.map(d => d.round));
    if (!roundsInHistory.has(roundNumber)) {
      const lastEntry = arr[arr.length - 1];
      arr.push({
        round: roundNumber, year: roundToQuarter(roundNumber, BASE_YEAR).year,
        ebitda, tco2e, reputation, treasury,
        synergy: globalState?.synergy_multiplier || 1.0,
        previous_ebitda: lastEntry?.ebitda || 0,
        previous_treasury: lastEntry?.treasury || 0,
        previous_reputation: lastEntry?.reputation || 50,
        previous_tco2e: lastEntry?.tco2e || 0,
        bu_count: businessUnits?.length || 0,
        decisions: null,
      });
    }
    // When commitResults are available (results overlay showing), append
    // the post-commit state as the next data point so trends show the change
    if (commitResults?.globalState) {
      const nextRound = commitResults.newRoundNumber || roundNumber + 1;
      if (!roundsInHistory.has(nextRound)) {
        arr.push({
          round: nextRound,
          year: roundToQuarter(nextRound, BASE_YEAR).year,
          ebitda: commitResults.globalState.historical_ebitda || 0,
          tco2e: commitResults.globalState.tco2e_emissions || 0,
          reputation: commitResults.globalState.group_reputation || 50,
          treasury: commitResults.globalState.corporate_treasury || 0,
          synergy: commitResults.globalState.synergy_multiplier || 1.0,
          previous_ebitda: ebitda,
          previous_treasury: treasury,
          previous_reputation: reputation,
          previous_tco2e: tco2e,
          bu_count: commitResults.businessUnits?.length || 0,
          decisions: null,
        });
      }
    }
    return arr;
  }, [history, roundNumber, ebitda, tco2e, reputation, treasury, commitResults, globalState, businessUnits]);

  // Projected costs from staged decision
  const [projectedCost, setProjectedCost] = useState(0);

  // Stage-warning toast when player tries to skip a stage
  const [stageWarning, setStageWarning] = useState(null);
  const showStageWarning = useCallback((msg) => {
    setStageWarning(msg);
    setTimeout(() => setStageWarning(null), 4000);
  }, []);

  // Strategic Breakdown Hover State
  const [hoveredOpt, setHoveredOpt] = useState(null);

  // Theme detection for inline styles
  const [isDark, setIsDark] = useState(true);
  useEffect(() => {
    const check = () => setIsDark(document.documentElement.getAttribute('data-theme') !== 'light');
    check();
    const observer = new MutationObserver(check);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

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
    
    // Dynamic Engine Events
    const flags = globalState?.active_event_flags || {};
    if (flags.tech_lock_in_active) {
      items.push({ type: 'alert', text: '📉 Tech sector consolidation: non-dominant platforms facing severe integration resistance.' });
    }
    if (flags.inflation_active || globalState?.inflation_index > 1.0) {
      const rate = ((globalState?.inflation_index - 1) * 100).toFixed(1);
      items.push({ type: 'info', text: `💸 Global inflation print at ${rate !== "NaN" && rate > 0 ? rate : "2.5"}%. OPEX scaling across all markets.` });
    }
    if (flags.greenwashing_penalty_active) {
      items.push({ type: 'alert', text: `🎭 Public backlash over corporate greenwashing. Institutional trust dropping.` });
    }
    if (flags.cogs_penalty_ratio > 1) {
      items.push({ type: 'alert', text: `⚙️ Supply chain disruptions hitting global shipping lanes.` });
    }
    
    // Fallback
    if (items.length < 2) {
      items.push({ type: 'info', text: '📊 Markets stable ahead of next quarter earnings reports.' });
    }
    return items;
  }, [crisisInfo, events, roundNumber, globalState]);

  // Active event popup (traps/penalties)
  const [blackSwanAlert, setBlackSwanAlert] = useState(null);

  // Detect custom black swan events from active_event_flags
  useEffect(() => {
    const flags = globalState?.active_event_flags || events || {};
    const swans = flags.custom_black_swans;
    if (Array.isArray(swans) && swans.length > 0) {
      const latest = swans[swans.length - 1];
      // Only show if not already dismissed (stored by title)
      const dismissedKey = `bs_dismissed_${latest.title}`;
      if (!sessionStorage.getItem(dismissedKey)) {
        setBlackSwanAlert(latest);
        // Auto-dismiss after 15 seconds
        const timer = setTimeout(() => {
          setBlackSwanAlert(null);
          sessionStorage.setItem(dismissedKey, '1');
        }, 15000);
        return () => clearTimeout(timer);
      }
    }
  }, [globalState, events]);

  const activeAlert = blackSwanAlert
    ? {
        icon: '🦢',
        title: blackSwanAlert.title,
        body: blackSwanAlert.narrative,
        isBlackSwan: true,
      }
    : events?.cfo_override_used
      ? { icon: '⚠️', title: 'CFO Override Penalty', body: 'Group reputation reduced by 5 points for bypassing materiality gate.' }
      : null;

  const kpiFlashActive = !!blackSwanAlert;

  return (
    <div className={styles.cockpit}>
      {/* ═══ GLOBAL HEADER ═══ */}
      <header className={styles.header}>
        <div className={styles.headerLogo}>
          <span className={styles.logoMark}>M</span>
          MURESSONS
          {sim?.username && (
             <span style={{ marginLeft: 16, fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, letterSpacing: '0.05em', borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: 16 }}>
               WELCOME {sim.username.toUpperCase()}
             </span>
          )}
        </div>

        <div className={styles.headerCenter}>
          <span className={styles.headerYear}>{getRoundLabel(roundNumber)}</span>
          <span className={styles.headerDivider} />
          <span className={styles.headerModule}>Turn {roundNumber}</span>
          <span className={styles.headerDivider} />
          <span>{activeRoundTitles[roundNumber] || ''}</span>
          {tippingPointActive && (
            <motion.span
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              style={{
                marginLeft: 12, padding: '2px 8px', borderRadius: 4,
                backgroundColor: 'rgba(239,68,68,0.2)', color: '#fca5a5',
                fontSize: '0.65rem', fontWeight: 700, border: '1px solid rgba(239,68,68,0.4)',
                letterSpacing: '0.05em'
              }}
            >
              ⚠️ CLIMATE TIPPING POINT
            </motion.span>
          )}
          <CountdownTimer sessionId={sim?.sessionId} roundNumber={roundNumber} />
          <span style={{
            marginLeft: 10, padding: '2px 10px', borderRadius: 12,
            background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.25)',
            fontSize: '0.62rem', fontWeight: 700, textTransform: 'uppercase',
            letterSpacing: '0.04em', color: '#818cf8', whiteSpace: 'nowrap',
          }}>
            {{
              'legacy_abc': 'Narrative Crises',
              'multi_toggles': 'Strategic Pillars',
              'advanced_climate': 'Advanced Climate',
              'healthcare': 'Healthcare Edition',
              'un_sdg': 'UN SDG Edition'
            }[decisionParadigm] || 'Simulation Active'}
          </span>
          {lastSavedAt && (
             <span style={{ marginLeft: 16, fontSize: '0.65rem', color: '#10b981', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
               ✓ Saved {lastSavedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
             </span>
          )}
        </div>

        <div className={styles.headerRight}>
          {projectedCost !== 0 && (
            <span className={`${styles.projectedDelta} ${projectedCost > 0 ? styles.projectedDown : styles.projectedUp}`}>
              {projectedCost > 0 ? '↓' : '↑'} {fmtCurrency(Math.abs(projectedCost))} staged
            </span>
          )}
        </div>
      </header>

      {/* ═══ MAIN CONTENT (3 COLUMNS) ═══ */}
      <div className={styles.mainContent}>

        {/* ── LEFT: KPI Dashboard ─── */}
        <aside id="tour-kpi-target" className={`${styles.leftSidebar} ${kpiFlashActive ? styles.kpiFlash : ''}`}>
          
          {/* Resources Panel (2×2 grid) — moved ABOVE KPI charts */}
          <div style={{ background: '#0a0e1a', borderBottom: '1px solid rgba(0, 229, 195, 0.2)', paddingTop: 10, paddingBottom: 10 }}>
          <div className={styles.resourcesPanel}>
            <div className={styles.resourceCard}>
              <div className={styles.resourceLabel}>💰 Treasury</div>
              <div className={styles.resourceValue}>{fmtCurrency(treasury)}</div>
            </div>
            {!isHealthcare && (
              <div className={styles.resourceCard}>
                <div className={styles.resourceLabel}>🌱 Green Fund</div>
                <div className={styles.resourceValue} style={{ color: '#4ade80' }}>{fmtCurrency(greenFund)}</div>
              </div>
            )}
            <div className={styles.resourceCard}>
              <div className={styles.resourceLabel}>🌍 Reputation</div>
              <div className={styles.resourceValue}>{reputation.toFixed(0)}<span style={{ fontSize: '0.55rem', color: '#475569', marginLeft: 2 }}>/100</span></div>
            </div>
            {!isHealthcare && (
              <div className={styles.resourceCard}>
                <div className={styles.resourceLabel}>🏭 Carbon</div>
                <div className={styles.resourceValue}>{tco2e.toLocaleString()}<span style={{ fontSize: '0.55rem', color: '#475569', marginLeft: 2 }}>t</span></div>
              </div>
            )}
            <div className={styles.resourceCard}>
              <div className={styles.resourceLabel}>📈 EBITDA</div>
              <div className={styles.resourceValue}>{fmtCurrency(ebitda)}</div>
            </div>
            {isHealthcare && (
              <>
                <div className={styles.resourceCard}>
                  <div className={styles.resourceLabel}>🩺 Avg Burnout</div>
                  <div className={styles.resourceValue} style={{ color: systemBurnout > 75 ? '#ef4444' : systemBurnout > 50 ? '#f59e0b' : '#10b981' }}>
                    {systemBurnout.toFixed(1)}<span style={{ fontSize: '0.55rem', color: '#475569', marginLeft: 2 }}>/100</span>
                  </div>
                </div>
                <div className={styles.resourceCard}>
                  <div className={styles.resourceLabel}>🛏️ Bed Util.</div>
                  <div className={styles.resourceValue} style={{ color: totalBedCapacity > 85 ? '#ef4444' : totalBedCapacity > 70 ? '#f59e0b' : '#10b981' }}>
                    {totalBedCapacity.toFixed(1)}<span style={{ fontSize: '0.55rem', color: '#475569', marginLeft: 2 }}>%</span>
                  </div>
                </div>
              </>
            )}
            {isSDG && (
              <>
                <div className={styles.resourceCard}>
                  <div className={styles.resourceLabel}>🏛️ Political Capital</div>
                  <div className={styles.resourceValue} style={{ color: politicalCapital > 50 ? '#10b981' : politicalCapital > 30 ? '#f59e0b' : '#ef4444' }}>
                    {politicalCapital.toFixed(0)}<span style={{ fontSize: '0.55rem', color: '#475569', marginLeft: 2 }}>/100</span>
                  </div>
                </div>
                <div className={styles.resourceCard}>
                  <div className={styles.resourceLabel}>🤝 Community Trust</div>
                  <div className={styles.resourceValue} style={{ color: communityTrust > 50 ? '#10b981' : communityTrust > 30 ? '#f59e0b' : '#ef4444' }}>
                    {communityTrust.toFixed(0)}<span style={{ fontSize: '0.55rem', color: '#475569', marginLeft: 2 }}>/100</span>
                  </div>
                </div>
                <div className={styles.resourceCard}>
                  <div className={styles.resourceLabel}>🌡️ Emissions Int.</div>
                  <div className={styles.resourceValue} style={{ color: globalEmissions > 100 ? '#ef4444' : globalEmissions > 60 ? '#f59e0b' : '#10b981' }}>
                    {globalEmissions.toFixed(0)}
                  </div>
                </div>
              </>
            )}
          </div>
          
          {/* P1: Macro & Strategy Indicators */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '0 12px 10px 12px', marginTop: 12 }}>
            <div style={{ display: 'flex', gap: 6 }}>
              <div style={{ flex: 1, padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: '1px solid rgba(0, 229, 195, 0.1)' }}>
                <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: 4 }}>Synergy</div>
                <div style={{ fontSize: '0.8rem', fontWeight: 800, color: (globalState?.synergy_multiplier || 1) < 1 ? '#ef4444' : '#00e5c3', fontFamily: 'JetBrains Mono, monospace' }}>
                  {((globalState?.synergy_multiplier || 1) * 100).toFixed(0)}%
                </div>
              </div>
              <div style={{ flex: 1, padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: '1px solid #334155' }}>
                <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: 4 }}>Inflation</div>
                <div style={{ fontSize: '0.8rem', fontWeight: 800, color: (globalState?.inflation_index || 1) > 1 ? '#f59e0b' : '#f8fafc', fontFamily: 'JetBrains Mono, monospace' }}>
                  {(((globalState?.inflation_index || 1) - 1) * 100).toFixed(1)}%
                </div>
              </div>
            </div>
            <div style={{ padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: '1px solid #334155' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.6rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700 }}>Cost of Capital</span>
                <span style={{ fontSize: '0.8rem', fontWeight: 800, color: '#f8fafc', fontFamily: 'JetBrains Mono, monospace' }}>
                  {((globalState?.cost_of_capital || 0.05) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          </div>

          <div style={{ flex: 1, overflowY: 'auto', paddingBottom: 10 }}>
            <KPIDashboard
            historyData={historyData}
            ebitda={ebitda}
            tco2e={tco2e}
            vrio={vrio}
            reputation={reputation}
            projectedCost={projectedCost}
            globalState={globalState}
            businessUnits={businessUnits}
            roundNumber={roundNumber}
            events={events}
          />
          </div>

          {/* Action Toolbar placed at the bottom of the left panel */}
          {actionToolbar && (
            <div style={{ borderTop: '1px solid rgba(0, 229, 195, 0.2)', background: '#0a0e1a', paddingTop: 10, paddingBottom: 10, display: 'flex', justifyContent: 'center' }}>
              {actionToolbar}
            </div>
          )}
        </aside>

        {/* ── CENTER: Briefing + Decisions ─── */}
        <main className={styles.centerConsole}>
          
          {/* Round Checklist natively rendered rather than floating */}
          {roundChecklist && (
            <div style={{ padding: '4px 16px', flexShrink: 0, marginTop: '8px' }}>
              {roundChecklist}
            </div>
          )}

          {/* Briefing Panel */}
          <div className={styles.briefingArea} id="tour-briefing-target">
            <div className={styles.briefingHeader}>
              <span className={styles.briefingRound}>Round {roundNumber}</span>
              <h2 className={styles.briefingTitle}>{activeRoundTitles[roundNumber] || `Module ${roundNumber}`}</h2>
            </div>
            <div className={styles.briefingBody}>
              {crisisInfo?.description || crisisInfo?.narrative || (
                <>The board expects decisive action this quarter. Review the crisis briefing in your mailbox and select a strategic response below. Your choice will affect treasury, reputation, and long-term resilience.</>
              )}
            </div>
            
            <EngineEventsPanel globalState={globalState} />

            {/* ── Round Gates ── */}
            {roundNumber === 1 && !hasCompletedStakeholderMap && (
              <button
                onClick={onOpenStakeholderMap}
                style={{
                  marginTop: 10, width: '100%', padding: '10px 16px',
                  background: 'linear-gradient(135deg, #00e5c3, #0dd9b0)', color: '#0a0e1a',
                  border: 'none', borderRadius: 6, fontWeight: 800, fontSize: '0.72rem',
                  cursor: 'pointer', letterSpacing: '0.08em', textTransform: 'uppercase',
                  fontFamily: 'Inter, sans-serif',
                  boxShadow: '0 4px 16px rgba(0,229,195,0.2)',
                }}
              >
                ⚖️ Complete Stakeholder Map (Required)
              </button>
            )}
            {roundNumber === 1 && hasCompletedStakeholderMap && (
              <div style={{ marginTop: 8, fontSize: '0.72rem', color: '#4ade80', fontWeight: 600 }}>
                ✅ Stakeholder Map Complete{stakeholderAccuracy != null ? ` — ${stakeholderAccuracy.toFixed(0)}% accuracy` : ''}
              </div>
            )}
            {roundNumber === 2 && !hasSubmittedMatrix && (
              <button
                onClick={onOpenCSRD}
                style={{
                  marginTop: 10, width: '100%', padding: '10px 16px',
                  background: 'linear-gradient(135deg, #ef4444, #dc2626)', color: '#fff',
                  border: 'none', borderRadius: 6, fontWeight: 800, fontSize: '0.72rem',
                  cursor: 'pointer', letterSpacing: '0.08em', textTransform: 'uppercase',
                  fontFamily: 'Inter, sans-serif',
                  boxShadow: '0 4px 16px rgba(239,68,68,0.2)',
                }}
              >
                🚨 Complete CSRD Assessment (Required)
              </button>
            )}
            {roundNumber === 2 && hasSubmittedMatrix && (
              <div style={{ marginTop: 8, fontSize: '0.68rem', color: '#4ade80', fontWeight: 600, letterSpacing: '0.02em' }}>✅ CSRD Assessment Submitted</div>
            )}
            
            {/* Active Infrastructure Projects (CapEx Delay) */}
            {pendingProjects.length > 0 && (
              <div style={{
                marginTop: 16, padding: '12px 14px', borderRadius: 8,
                background: 'rgba(56, 189, 248, 0.08)', border: '1px solid rgba(56, 189, 248, 0.2)',
              }}>
                <div style={{ fontSize: '0.65rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>🏗️</span> Active Infrastructure Projects
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {pendingProjects.map((proj, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(15,23,42,0.4)', padding: '6px 10px', borderRadius: 6 }}>
                      <span style={{ fontSize: '0.75rem', color: '#e2e8f0', fontWeight: 500 }}>{proj.description || 'Strategic Project'}</span>
                      <span style={{ fontSize: '0.65rem', color: '#94a3b8', background: '#1e293b', padding: '2px 6px', borderRadius: 4 }}>
                        ⏳ {proj.rounds_remaining} Turn{proj.rounds_remaining > 1 ? 's' : ''} Left
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Resource Allocation Matrix */}
          <div className={styles.decisionArea} style={{ flex: 'none', overflow: 'visible', borderBottom: isDark ? '1px solid rgba(0,229,195,0.06)' : '1px solid #e2e8f0', paddingBottom: 8, position: 'relative' }}>
            <div id="tour-capital-target">
            {/* Click-intercept: requires Strategic Decision to be made */}
            {!canAccessAllocation && (
              <div
                onClick={() => {
                  if (!hasReadBriefing) {
                    showStageWarning('Read the Briefing first before proceeding.');
                  } else if (hasSecondStage && !secondStageDone) {
                    showStageWarning(roundNumber === 1 ? 'Complete the Stakeholder Map first.' : 'Complete the CSRD Assessment first.');
                  } else if (!hasDecision) {
                    showStageWarning('Make your Strategic Decision before setting Capital Allocation.');
                  }
                }}
                style={{
                  position: 'absolute', inset: 0, zIndex: 5,
                  cursor: 'not-allowed', borderRadius: 8,
                }}
              />
            )}
            <InvestmentMatrix
              csfPool={csfPool}
              globalState={globalState}
              businessUnits={businessUnits}
              allocations={allocations}
              historyData={historyData}
              onAllocationsChange={canAccessAllocation ? onAllocationsChange : () => {}}
            />
            </div>
          </div>

          {/* Decision Workspace */}
          <div className={styles.decisionArea} style={{ flex: 'none', overflow: 'visible', position: 'relative', marginTop: '16px' }}>
            <div id="tour-strategic-target">
            {/* Click-intercept: requires Briefing read + Second Stage (R1/R2) done */}
            {!canAccessStrategy && (
              <div
                onClick={() => {
                  if (!hasReadBriefing) {
                    showStageWarning('Read the Briefing first before making your Strategic Decision.');
                  } else if (hasSecondStage && !secondStageDone) {
                    showStageWarning(roundNumber === 1 ? 'Complete the Stakeholder Map before making your Strategic Decision.' : 'Complete the CSRD Assessment before making your Strategic Decision.');
                  }
                }}
                style={{
                  position: 'absolute', inset: 0, zIndex: 5,
                  cursor: 'not-allowed', borderRadius: 8,
                }}
              />
            )}
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
                  const optMeta = {
                    option_a: { icon: '⚡', label: 'OPTION A' },
                    option_b: { icon: '⚖️', label: 'OPTION B' },
                    option_c: { icon: '🛡️', label: 'OPTION C' },
                  }[optId];
                  const costVal = opt.impacts?.treasury || opt.cost_impact || 0;
                  const maxCost = Math.max(
                    ...['option_a','option_b','option_c'].map(k => Math.abs(options[k]?.impacts?.treasury || options[k]?.cost_impact || 1))
                  );
                  const costBarPct = Math.min(100, (Math.abs(costVal) / maxCost) * 100);
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
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                        <span style={{ fontSize: '1rem' }}>{optMeta.icon}</span>
                        <span className={styles.tileLabel} style={{ margin: 0 }}>
                          {optMeta.label}
                        </span>
                      </div>
                      <div className={styles.tileTitle}>{opt.title}</div>
                      <p className={styles.tileDesc}>{opt.description}</p>
                      {costVal ? (
                        <div style={{ marginTop: 6 }}>
                          <div style={{
                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                            marginBottom: 3,
                          }}>
                            <span style={{ fontSize: '0.6rem', color: '#64748b', fontWeight: 600 }}>💰 Cost</span>
                            <span style={{
                              fontSize: '0.72rem', fontWeight: 800,
                              color: costVal < 0 ? '#16a34a' : '#ef4444',
                            }}>
                              {fmtCurrency(costVal)}
                            </span>
                          </div>
                          <div style={{
                            height: 4, background: '#e2e8f0', borderRadius: 2,
                            overflow: 'hidden',
                          }}>
                            <div style={{
                              width: `${costBarPct}%`, height: '100%',
                              background: '#6366f1', borderRadius: 2,
                              transition: 'width 0.3s ease',
                            }} />
                          </div>
                        </div>
                      ) : null}
                      {/* Impact Preview when selected */}
                      {isActive && opt.impacts && (
                        <div style={{
                          marginTop: 6, padding: '4px 6px', background: '#f8fafc',
                          borderRadius: 4, fontSize: '0.58rem', lineHeight: 1.6,
                        }}>
                          {opt.impacts.treasury && (
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: opt.impacts.treasury < 0 ? '#16a34a' : '#ef4444' }}>
                              <span>💰 Treasury</span>
                              <span style={{ fontWeight: 700 }}>{fmtCurrency(treasury)} → {fmtCurrency(treasury + (opt.impacts.treasury || 0))} {opt.impacts.treasury < 0 ? '▼' : '▲'}</span>
                            </div>
                          )}
                          {opt.impacts.reputation !== undefined && (
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: opt.impacts.reputation > 0 ? '#16a34a' : '#ef4444' }}>
                              <span>🌍 Reputation</span>
                              <span style={{ fontWeight: 700 }}>{reputation} → {reputation + (opt.impacts.reputation || 0)} {opt.impacts.reputation > 0 ? '▲' : '▼'}</span>
                            </div>
                          )}
                          {opt.impacts.carbon !== undefined && (
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: opt.impacts.carbon < 0 ? '#16a34a' : '#ef4444' }}>
                              <span>🏭 Carbon</span>
                              <span style={{ fontWeight: 700 }}>{opt.impacts.carbon > 0 ? '+' : ''}{opt.impacts.carbon}t</span>
                            </div>
                          )}
                        </div>
                      )}
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
                ) : decisionParadigm === 'legacy_abc' ? (
                  <div style={{ marginTop: 4 }}>
                    <div style={{ fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase', color: '#64748b', marginBottom: 6 }}>Comparison Matrix</div>
                    <table style={{ width: '100%', fontSize: '0.68rem', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
                          <th style={{ textAlign: 'left', paddingBottom: 4 }}>Option</th>
                          <th style={{ textAlign: 'center', paddingBottom: 4 }}>Treasury Impact</th>
                          <th style={{ textAlign: 'center', paddingBottom: 4 }}>Reputation</th>
                          <th style={{ textAlign: 'center', paddingBottom: 4 }}>CO₂ / ESG</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(options).map(([optId, opt]) => (
                          <tr key={optId} style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                            <td style={{ padding: '6px 0', fontWeight: 600 }}>{optId.replace('option_', 'Option ').toUpperCase()}</td>
                            <td style={{ textAlign: 'center', color: opt.impacts?.treasury < 0 ? '#16a34a' : (opt.impacts?.treasury > 0 ? '#ef4444' : '#64748b') }}>
                              {opt.impacts?.treasury ? fmtCurrency(opt.impacts.treasury) : '—'}
                            </td>
                            <td style={{ textAlign: 'center', color: opt.impacts?.reputation > 0 ? '#16a34a' : (opt.impacts?.reputation < 0 ? '#ef4444' : '#64748b') }}>
                              {opt.impacts?.reputation ? (opt.impacts.reputation > 0 ? '+' : '') + opt.impacts.reputation : '—'}
                            </td>
                            <td style={{ textAlign: 'center', color: opt.impacts?.carbon < 0 ? '#16a34a' : (opt.impacts?.carbon > 0 ? '#ef4444' : '#64748b') }}>
                              {opt.impacts?.carbon ? (opt.impacts.carbon > 0 ? '+' : '') + opt.impacts.carbon + 't' : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className={styles.breakdownPlaceholder}>
                    Hover over an active Strategic Pillar dropdown to view its detailed implications.
                  </p>
                )}
              </div>
            </div>

            </div>
          </div>
          
          {/* Spacer to prevent Fixed RoundChecklist from overlapping bottom content */}
          <div style={{ height: '80px', flexShrink: 0 }} />
        </main>

        {/* ── RIGHT SIDEBAR ─── */}
        <aside id="tour-intelligence-target" className={styles.rightSidebar}>
          {/* Resources link */}
          <div className={styles.rightResources} style={{ padding: '8px 14px', cursor: 'pointer', background: '#f1f5f9', fontWeight: 600 }} onClick={onResourcesOpen}>
            <span className={styles.resourcesLabel}>📎 Simulation Resources</span>
            <span style={{ fontSize: '0.6rem', color: '#475569' }}>▶</span>
          </div>

          <CompetitorIntelligence globalState={globalState} ebitda={ebitda} />

          {/* Executive Mailbox / Decision History (tabbed) */}
          <div className={styles.rightMailbox}>
            {/* Sticky Tab Header */}
            <div style={{
              position: 'sticky', top: 0, zIndex: 10,
              display: 'flex', gap: 0,
              background: 'var(--bg-sidebar, #ffffff)',
              borderBottom: '1px solid var(--border-subtle, #e2e8f0)',
            }}>
              <button
                onClick={() => setRightPanelTab('mailbox')}
                style={{
                  flex: 1, padding: '8px 10px', cursor: 'pointer',
                  fontSize: '0.62rem', fontWeight: 800, textTransform: 'uppercase',
                  letterSpacing: '0.06em', border: 'none',
                  background: rightPanelTab === 'mailbox' ? 'rgba(59,130,246,0.08)' : 'transparent',
                  color: rightPanelTab === 'mailbox' ? '#3b82f6' : '#64748b',
                  borderBottom: rightPanelTab === 'mailbox' ? '2px solid #3b82f6' : '2px solid transparent',
                  transition: 'all 0.15s ease',
                }}
              >
                📬 Mailbox {unreadCount > 0 && <span className={styles.mailboxBadge}>{unreadCount}</span>}
              </button>
              <button
                onClick={() => setRightPanelTab('decisions')}
                style={{
                  flex: 1, padding: '8px 10px', cursor: 'pointer',
                  fontSize: '0.62rem', fontWeight: 800, textTransform: 'uppercase',
                  letterSpacing: '0.06em', border: 'none',
                  background: rightPanelTab === 'decisions' ? 'rgba(99,102,241,0.08)' : 'transparent',
                  color: rightPanelTab === 'decisions' ? '#6366f1' : '#64748b',
                  borderBottom: rightPanelTab === 'decisions' ? '2px solid #6366f1' : '2px solid transparent',
                  transition: 'all 0.15s ease',
                }}
              >
                📜 My Decisions
              </button>
            </div>

            {/* Tab Content */}
            <div style={{ padding: '8px 12px', overflowY: 'auto', flex: 1 }}>
              {rightPanelTab === 'mailbox' ? (
                <>
                  <div className={styles.mailboxTitle}>
                    Round {roundNumber}
                    {unreadCount > 0 && <span className={styles.mailboxBadge}>{unreadCount}</span>}
                  </div>
                  {currentMessages.map((msg) => (
                    <div
                      key={msg.id}
                      className={styles.feedItem}
                      onClick={() => { onMarkRead?.(msg.id); setExpandedMessage(msg); }}
                      style={{ cursor: 'pointer', opacity: msg.read ? 0.6 : 1 }}
                    >
                      {/* Improvement #4.2: AI Personas */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 2 }}>
                        <span style={{ fontSize: '0.7rem' }}>{getPersona(msg).avatar}</span>
                        <span style={{ fontSize: '0.55rem', fontWeight: 600, color: getPersona(msg).color }}>{getPersona(msg).name}</span>
                      </div>
                      <strong style={{ fontSize: '0.68rem', color: '#0f172a' }}>{msg.title}</strong>
                      <p style={{ margin: '2px 0 0', fontSize: '0.65rem', color: '#334155' }}>{msg.body?.substring(0, 120)}...</p>
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
                        <ArchiveAccordion key={r} round={r} roundLabel={getRoundLabel(r)} items={items} onMarkRead={onMarkRead} onExpand={setExpandedMessage} />
                      );
                    });
                  })()}
                </>
              ) : (
                <DecisionHistory historyData={historyData} />
              )}
            </div>
          </div>

          {/* Market Reality Feed (40%) */}
          <div className={styles.rightMarket} style={{ height: '50%' }}>
            <MarketRealityFeed items={marketEvents} activeAlert={activeAlert} />
          </div>

          {/* ── Commit Footer (Moved to Right Panel Bottom) ── */}
          <div className={styles.rightCommit} style={{ flex: '0 0 auto', padding: '16px 14px', background: '#0f172a', borderTop: '1px solid #1e293b', display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, fontSize: '0.7rem', fontWeight: 600, color: '#94a3b8', flexWrap: 'wrap' }}>
              <span style={{ color: hasReadBriefing ? '#10b981' : '#f59e0b' }}>Brief {hasReadBriefing ? '✓' : ''}</span> → 
              <span style={{ color: (decisionParadigm === 'multi_toggles' ? Object.keys(pillarSelections || {}).length > 0 : !!decisionChoice) ? '#10b981' : '#f59e0b' }}>Decide {(decisionParadigm === 'multi_toggles' ? Object.keys(pillarSelections || {}).length > 0 : !!decisionChoice) ? '✓' : ''}</span> → 
              <span style={{ color: Object.keys(allocations).length > 0 ? '#10b981' : '#f59e0b' }}>Allocate {Object.keys(allocations).length > 0 ? '✓' : ''}</span>
            </div>
            
            {/* Decision Quality Meter */}
            {(() => {
              const allocTotal = Object.values(allocations).reduce((a, b) => a + b, 0);
              let quality = 0;
              if (hasReadBriefing) quality += 10;
              if (decisionParadigm === 'multi_toggles' ? Object.keys(pillarSelections || {}).length > 0 : !!decisionChoice) quality += 40;
              quality += Math.min(50, (allocTotal / (csfPool || 1)) * 50);
              return (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, width: '100%' }}>
                  <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: '#cbd5e1' }}>Readiness</span>
                  <div style={{ flex: 1, height: 6, background: '#1e293b', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${quality}%`, height: '100%', background: quality > 80 ? '#10b981' : quality > 40 ? '#f59e0b' : '#ef4444', transition: 'all 0.3s ease' }} />
                  </div>
                </div>
              );
            })()}
            
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, width: '100%' }}>
              {stageWarning && (
                <span style={{ color: '#ef4444', fontSize: '0.65rem', fontWeight: 700, textAlign: 'center' }}>🔒 {stageWarning}</span>
              )}
              <motion.button
                className={`${styles.commitBtn} ${commitResults ? styles.commitBtnDone : ''}`}
                style={{ width: '100%', height: 42, fontSize: '0.85rem' }}
                disabled={!!commitResults}
                onClick={onCommit}
                whileHover={{ scale: commitResults ? 1 : 1.02 }}
                whileTap={{ scale: commitResults ? 1 : 0.98 }}
              >
                {commitResults ? '✅ Committed' : '▶ Commit Decisions'}
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
                    background: (expandedMessage.type === 'crisis' || expandedMessage.type === 'alert') ? '#fef2f2' : expandedMessage.type === 'facilitator' ? '#f0fdf4' : '#f0f4ff',
                    color: (expandedMessage.type === 'crisis' || expandedMessage.type === 'alert') ? '#dc2626' : expandedMessage.type === 'facilitator' ? '#16a34a' : '#4338ca',
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
                {(() => {
                  const newTreasury = commitResults.globalState?.corporate_treasury || 0;
                  const newEbitda = commitResults.globalState?.historical_ebitda || 0;
                  const newRep = commitResults.globalState?.group_reputation || 50;
                  const newCarbon = commitResults.globalState?.tco2e_emissions || 0;
                  
                  const dTreasury = newTreasury - treasury;
                  const dEbitda = newEbitda - ebitda;
                  const dRep = newRep - reputation;
                  const dCarbon = newCarbon - tco2e;
                  
                  const renderDelta = (v, inverseGood = false) => {
                    if (!v) return null;
                    const isGood = inverseGood ? v < 0 : v > 0;
                    return (
                      <span style={{ fontSize: '0.75rem', fontWeight: 800, marginLeft: 8, color: isGood ? '#4ade80' : '#ef4444' }}>
                        {v > 0 ? '▲' : '▼'} {fmtCurrency ? (inverseGood && v < 500 ? Math.abs(v) : fmtCurrency(Math.abs(v))) : Math.abs(v).toFixed(0)}
                      </span>
                    );
                  };

                  return (
                    <>
                      <div className={styles.resultCard}>
                        <div className={styles.resultCardIcon}>💰</div>
                        <div className={styles.resultCardLabel}>Treasury</div>
                        <div className={styles.resultCardValue}>
                          {fmtCurrency(newTreasury)}
                          {renderDelta(dTreasury)}
                        </div>
                      </div>
                      <div className={styles.resultCard}>
                        <div className={styles.resultCardIcon}>📈</div>
                        <div className={styles.resultCardLabel}>EBITDA</div>
                        <div className={styles.resultCardValue}>
                          {fmtCurrency(newEbitda)}
                          {renderDelta(dEbitda)}
                        </div>
                      </div>
                      <div className={styles.resultCard}>
                        <div className={styles.resultCardIcon}>🌍</div>
                        <div className={styles.resultCardLabel}>Reputation</div>
                        <div className={styles.resultCardValue}>
                          {newRep.toFixed(0)}
                          <span style={{ fontSize: '0.75rem', fontWeight: 800, marginLeft: 8, color: dRep >= 0 ? '#4ade80' : '#ef4444' }}>
                            {dRep >= 0 ? '▲' : '▼'} {Math.abs(dRep).toFixed(0)}
                          </span>
                        </div>
                      </div>
                      <div className={styles.resultCard}>
                        <div className={styles.resultCardIcon}>🏭</div>
                        <div className={styles.resultCardLabel}>CO₂ Emissions</div>
                        <div className={styles.resultCardValue}>
                          {newCarbon.toLocaleString()} t
                          <span style={{ fontSize: '0.75rem', fontWeight: 800, marginLeft: 8, color: dCarbon <= 0 ? '#4ade80' : '#ef4444' }}>
                            {dCarbon > 0 ? '▲' : '▼'} {Math.abs(dCarbon).toLocaleString()} t
                          </span>
                        </div>
                      </div>
                    </>
                  );
                })()}
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
                    <div key={key} className={styles.resultCard} style={{
                      padding: '0.5rem 0.6rem 0.3rem',
                    }}>
                      <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.2rem' }} className={styles.resultCardLabel}>
                        {label}
                      </div>
                      <ResponsiveContainer width="100%" height={72}>
                        <AreaChart data={historyData} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                          <defs>
                            <linearGradient id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor={color} stopOpacity={0.35} />
                              <stop offset="95%" stopColor={color} stopOpacity={0.02} />
                            </linearGradient>
                            <filter id={`glow-${key}`}>
                              <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                              <feMerge>
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="SourceGraphic" />
                              </feMerge>
                            </filter>
                          </defs>
                          <XAxis dataKey="year" tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                          <YAxis hide domain={yDomain} />
                          <Tooltip
                            contentStyle={{ fontSize: '0.72rem', borderRadius: 6, border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                            formatter={(v) => [fmt(v), label.replace(' Trend', '')]}
                            labelFormatter={(year) => `Year ${year}`}
                          />
                          <Area type="monotone" dataKey={key} stroke={color} strokeWidth={2.5} fill={`url(#grad-${key})`} filter={`url(#glow-${key})`} dot={{ r: 3, fill: color, strokeWidth: 0 }} activeDot={{ r: 5, fill: color, stroke: '#fff', strokeWidth: 2 }} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  );})}
                </div>
              )}

              {/* Stock Price Trend */}
              {historyData.length > 1 && (() => {
                const avgNCD = businessUnits.length > 0
                  ? businessUnits.reduce((s, bu) => s + (bu.natural_capital_debt || 0), 0) / businessUnits.length
                  : 0;
                const stockData = [
                  { year: 'IPO', price: IPO_PRICE },
                  ...historyData.map(h => ({
                    year: h.year,
                    price: calculateRoundStockPrice({
                      ebitda: h.ebitda,
                      synergy_multiplier: globalState?.synergy_multiplier || 1.0,
                      natural_capital_debt: avgNCD,
                      group_reputation: h.reputation,
                    }),
                  })),
                ];
                const prices = stockData.map(d => d.price);
                const minP = Math.min(...prices);
                const maxP = Math.max(...prices);
                const pad = (maxP - minP) * 0.15 || 5;
                const latestPrice = prices[prices.length - 1];
                const pctChg = ((latestPrice - IPO_PRICE) / IPO_PRICE * 100);

                return (
                  <div className={styles.resultCard} style={{
                    padding: '0.5rem 0.6rem 0.3rem', marginBottom: '1rem',
                  }}>
                    <div style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                      fontSize: '0.68rem', fontWeight: 700,
                      textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.2rem',
                    }} className={styles.resultCardLabel}>
                      <span>📈 Stock Price</span>
                      <span style={{
                        color: pctChg >= 0 ? '#16a34a' : '#ef4444', fontFamily: 'JetBrains Mono, monospace',
                      }}>
                        ${latestPrice.toFixed(2)} ({pctChg >= 0 ? '+' : ''}{pctChg.toFixed(1)}%)
                      </span>
                    </div>
                    <ResponsiveContainer width="100%" height={72}>
                      <AreaChart data={stockData} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                        <defs>
                          <linearGradient id="grad-stock-res" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.35} />
                            <stop offset="95%" stopColor="#7c3aed" stopOpacity={0.02} />
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="year" tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                        <YAxis hide domain={[Math.max(0, minP - pad), maxP + pad]} />
                        <Tooltip
                          contentStyle={{ fontSize: '0.72rem', borderRadius: 6, border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                          formatter={(v) => [`$${v.toFixed(2)}`, 'Stock Price']}
                          labelFormatter={(year) => year === 'IPO' ? 'IPO' : `Year ${year}`}
                        />
                        <ReferenceLine y={IPO_PRICE} stroke="#94a3b8" strokeDasharray="3 3" />
                        <Area type="monotone" dataKey="price" stroke="#7c3aed" strokeWidth={2.5} fill="url(#grad-stock-res)" dot={{ r: 3, fill: '#7c3aed', strokeWidth: 0 }} activeDot={{ r: 5, fill: '#7c3aed', stroke: '#fff', strokeWidth: 2 }} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                );
              })()}

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
function ArchiveAccordion({ round, roundLabel, items, onMarkRead, onExpand }) {
  const [open, setOpen] = useState(false);
  const handleToggle = (e) => {
    e.stopPropagation();
    e.preventDefault();
    setOpen(prev => !prev);
  };
  return (
    <div style={{
      marginTop: 6,
      borderTop: '1px solid #eef0f6',
    }}>
      <button
        onClick={handleToggle}
        type="button"
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 10px',
          background: open ? '#eef4ff' : '#f7f8fc',
          border: open ? '1px solid #c7d2fe' : '1px solid transparent',
          borderRadius: 5,
          cursor: 'pointer',
          fontSize: '0.65rem',
          fontWeight: 700,
          color: open ? '#3b5998' : '#6b7a8d',
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
          fontFamily: 'Inter, sans-serif',
          transition: 'all 0.15s',
        }}
      >
        <span>{open ? '▾' : '▸'} {roundLabel || `Round ${round}`}</span>
        <span style={{
          fontSize: '0.55rem',
          background: open ? '#c7d2fe' : '#e2e8f0',
          color: open ? '#3b5998' : '#475569',
          padding: '2px 6px',
          borderRadius: 4,
          fontWeight: 700,
        }}>{items.length}</span>
      </button>
      {open && (
        <div style={{ padding: '4px 0' }}>
          {items.map(msg => (
            <div
              key={msg.id}
              onClick={(e) => { e.stopPropagation(); onMarkRead?.(msg.id); onExpand?.(msg); }}
              style={{
                padding: '6px 10px 6px 18px',
                fontSize: '0.65rem',
                color: '#334155',
                lineHeight: 1.5,
                borderLeft: '2px solid #c7d2fe',
                marginLeft: 10,
                marginBottom: 3,
                cursor: 'pointer',
                opacity: msg.read ? 0.7 : 1,
                borderRadius: '0 4px 4px 0',
                background: '#fafbff',
                transition: 'all 0.15s',
              }}
            >
              <strong style={{ fontSize: '0.65rem', color: '#334155' }}>{msg.title}</strong>
              <p style={{ margin: '2px 0 0', fontSize: '0.6rem', color: '#475569' }}>
                {msg.body?.substring(0, 80)}...
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
