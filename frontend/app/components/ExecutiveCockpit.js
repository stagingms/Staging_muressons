'use client';
import React from 'react';
import { useCurrency } from '../contexts/CurrencyContext';

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
import BenchmarksPanel from './BenchmarksPanel';
import FocusOverlay, { KPIStrip } from './FocusOverlay';
// Phase 1.4: Deduplicated decision tile components
import DecisionTile, { PillarTile } from './DecisionTile';
// Phase 3: Progressive Disclosure components
import ConsequenceDNA from './ConsequenceDNA';
import TerminalValuationCalc from './TerminalValuationCalc';
import PredictionComparison from './PredictionComparison';
import StochasticDiceRoll from './StochasticDiceRoll';
import SynergyTracker from './SynergyTracker';
import focusStyles from './FocusOverlay.module.css';
import {
  PredictionGate, BoardRoomMoment, ConfidenceCalibration,
  RoundRecap, RealWorldCard, MentalModelTracker, MidGameCheckpoint,
  R6RevelationPanel, BudgetAllocationPanel, StakeholderTribunal,
  FlagDependencyWarnings, OrientationPanel,
} from './PedagogicalScaffolding';

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
  const [hoveredOption, setHoveredOption] = useState(null); // Phase 4.6: What-If shadow

  // Pedagogical scaffolding toggles (fetched from god-mode settings)
  const [pedToggles, setPedToggles] = useState({});
  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/global-settings`)
      .then(r => r.json())
      .then(d => setPedToggles(d || {}))
      .catch(() => {});
  }, []);
  const [predictions, setPredictions] = useState([]);
  const [checkpointData, setCheckpointData] = useState(null);
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
  // Initialise EBITDA from BU revenue minus OPEX if not yet committed (avoids $0 display on R1)
  const ebitda = globalState?.historical_ebitda ||
    (businessUnits?.reduce((acc, bu) => acc + (bu.revenue_base || 0) - (bu.opex_base || 0), 0) || 0);
  // Initialise carbon from BU data when tco2e_emissions not yet set
  const rawTco2e = globalState?.tco2e_emissions;
  const tco2e = (rawTco2e != null && rawTco2e > 0)
    ? rawTco2e
    : (businessUnits?.reduce((acc, bu) => acc + (bu.carbon_intensity || 0), 0) || 0);
  const avgCarbonIntensity = businessUnits?.length
    ? (businessUnits.reduce((acc, bu) => acc + (bu.carbon_intensity || 0), 0) / businessUnits.length)
    : 0;
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
      // NEW-01/NEW-10: Derive a per-round EBITDA from BU states (revenue - opex).
      // The historical_ebitda field is cumulative and causes stock price calculation errors.
      // Fall back to a per-round estimate (cumulative / round_number) if BU data unavailable.
      const roundBUs = h.business_units || [];
      const perRoundEbitda = roundBUs.length > 0
        ? roundBUs.reduce((acc, bu) => acc + (bu.revenue_base || 0) - (bu.opex_base || 0), 0)
        : (h.global_state?.historical_ebitda
            ? Math.max(0, h.global_state.historical_ebitda / Math.max(1, h.round_number))
            : 0);
      return {
        round: h.round_number,
        year: roundToQuarter(h.round_number, BASE_YEAR).year,
        ebitda: perRoundEbitda,
        tco2e: h.global_state?.tco2e_emissions || 0,
        reputation: h.global_state?.group_reputation || 50,
        treasury: h.global_state?.corporate_treasury || 0,
        synergy: h.global_state?.synergy_multiplier || 1.0,
        previous_ebitda: prev ? (prev.business_units || []).reduce((acc, bu) => acc + (bu.revenue_base || 0) - (bu.opex_base || 0), 0) : 0,
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
  const [infraOpen, setInfraOpen] = useState(true);

  // ── Focus Mode: Advanced Metrics Drawer ──
  // Auto-collapsed for rounds 1-4, auto-expanded for rounds 5+
  const [advancedMetricsOpen, setAdvancedMetricsOpen] = useState(roundNumber >= 5);
  useEffect(() => { setAdvancedMetricsOpen(roundNumber >= 5); }, [roundNumber]);

  // ── Metacognitive Friction: Pre-Commit Prediction ──
  const [showPredictionModal, setShowPredictionModal] = useState(false);
  const [predictionText, setPredictionText] = useState('');

  // ── Consequence Traceability: tooltip index for market feed ──
  const [traceTooltipIdx, setTraceTooltipIdx] = useState(null);

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

  // ── Focus Mode: Stepped Decision Overlays ──
  // Optional with escape hatch — auto-opens but student can dismiss at any time
  const [focusStep, setFocusStep] = useState(null); // null | 'gate' | 'strategy' | 'allocation' | 'commit' | 'results'
  const [focusDismissed, setFocusDismissed] = useState(false);
  const [focusPredictionText, setFocusPredictionText] = useState('');

  // Compute focus steps for this round
  const hasGate = roundNumber === 1 || roundNumber === 2;
  const focusSteps = useMemo(() => {
    const s = [];
    if (hasGate) s.push('gate');
    s.push('strategy', 'allocation', 'commit');
    return s;
  }, [hasGate]);

  // Determine the first incomplete focus step
  const getFirstIncompleteStep = useCallback(() => {
    if (hasGate && !roundPrerequisiteMet) return 'gate';
    if (!hasDecision) return 'strategy';
    if (Object.keys(allocations).length === 0) return 'allocation';
    if (!commitResults) return 'commit';
    return 'results';
  }, [hasGate, roundPrerequisiteMet, hasDecision, allocations, commitResults]);

  // Auto-trigger focus mode when briefing is dismissed (entering the cockpit)
  useEffect(() => {
    if (!hasReadBriefing || sim?.gameOver) return;
    if (focusDismissed) return;
    // Only auto-open if no focus step is active yet
    if (focusStep === null) {
      setFocusStep(getFirstIncompleteStep());
    }
  }, [hasReadBriefing, sim?.gameOver, focusDismissed]);

  // Auto-advance: gate completed → strategy
  useEffect(() => {
    if (focusStep === 'gate' && roundPrerequisiteMet) {
      setFocusStep('strategy');
    }
  }, [focusStep, roundPrerequisiteMet]);

  // Auto-advance: commit done → results
  useEffect(() => {
    if (focusStep === 'commit' && commitResults) {
      setFocusStep('results');
    }
  }, [focusStep, commitResults]);

  // Reset focus mode on round change
  useEffect(() => {
    setFocusStep(null);
    setFocusDismissed(false);
    setFocusPredictionText('');
  }, [roundNumber]);

  const isFocusActive = focusStep !== null && !focusDismissed;

  const handleFocusDismiss = useCallback(() => {
    setFocusDismissed(true);
    setFocusStep(null);
  }, []);

  const handleFocusReenter = useCallback(() => {
    setFocusDismissed(false);
    setFocusStep(getFirstIncompleteStep());
  }, [getFirstIncompleteStep]);

  const handleFocusAdvance = useCallback((nextStep) => {
    setFocusStep(nextStep);
  }, []);


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

  // Phase 4.6: What-If shadow mode — projected deltas from hovered option
  const shadowDeltas = useMemo(() => {
    if (!hoveredOption || !options[hoveredOption]) return null;
    const opt = options[hoveredOption];
    return {
      treasury: opt.treasury_impact || opt.cost || 0,
      reputation: opt.reputation_impact || 0,
    };
  }, [hoveredOption, options]);
  // Currency symbol from cohort session (falls back to God Mode global)
  const { currency, loadSessionCurrency } = useCurrency();
  const sym = currency?.symbol || '$';

  // Load this cohort's configured currency on mount
  useEffect(() => {
    const sessionId = sim?.sessionId || sim?.session_id;
    if (sessionId) loadSessionCurrency(sessionId);
  }, [sim?.sessionId, sim?.session_id, loadSessionCurrency]);

  // Format currency — always uses the configured symbol (defaults $)
  const fmtCurrency = (v) => {
    if (v === undefined || v === null || isNaN(v)) return `${sym}0`;
    if (v === 0) return `${sym}0`;
    const abs = Math.abs(v);
    if (abs >= 1_000_000) return `${v < 0 ? '-' : ''}${sym}${(abs / 1_000_000).toFixed(1)}M`;
    if (abs >= 1_000) return `${v < 0 ? '-' : ''}${sym}${(abs / 1_000).toFixed(0)}K`;
    return `${v < 0 ? '-' : ''}${sym}${abs.toFixed(0)}`;
  };

  // NEW-01: Smart inflation formatter
  // Backend stores inflation_index as fractional rate (0.025 = 2.5%) not multiplier (1.025)
  const fmtInflation = (idx) => {
    if (!idx || isNaN(idx)) return '2.5%';
    // If value < 0.5 it's a fractional rate (e.g. 0.025), multiply by 100
    // If value >= 0.5 it's a multiplier (e.g. 1.025), subtract 1 first
    const pct = idx < 0.5 ? (idx * 100) : ((idx - 1) * 100);
    return `${pct.toFixed(1)}%`;
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
    if (flags.inflation_active || globalState?.inflation_index > 0) {
      const displayRate = fmtInflation(globalState?.inflation_index);
      items.push({ type: 'info', text: `💸 Global inflation print at ${displayRate}. OPEX scaling across all markets.` });
    }
    if (flags.greenwashing_penalty_active) {
      items.push({ type: 'alert', text: `🎭 Public backlash over corporate greenwashing. Institutional trust dropping.` });
    }
    if (flags.cogs_penalty_ratio > 1) {
      items.push({ type: 'alert', text: `⚙️ Supply chain disruptions hitting global shipping lanes.` });
    }

    // C7/C14: Dynamic Stakeholder Salience Migration (from engine events)
    const migrations = events?.salience_migrations || globalState?.active_event_flags?.salience_migrations;
    if (migrations?.length > 0) {
      migrations.forEach(m => {
        items.push({ type: 'alert', text: `${m.stakeholder_icon} SALIENCE SHIFT: ${m.stakeholder_name} moved from "${m.from_quadrant.replace('_',' ')}" → "${m.to_quadrant.replace('_',' ')}". ${m.narrative}` });
      });
    }
    if (globalState?.stakeholder_map_accuracy < 70 && roundNumber === 4) {
      items.push({ type: 'alert', text: `STAKEHOLDER MISANALYSIS: Your R1 stakeholder accuracy (${globalState.stakeholder_map_accuracy}%) increased this round's crisis severity by 25%.` });
    }
    
    // Fallback
    if (items.length < 2) {
      items.push({ type: 'info', text: '📊 Markets stable ahead of next quarter earnings reports.' });
    }

    // Foreshadowing events (R5–R8 pathway hints — players see these as news/market intel)
    const foreshadowItems = events?.foreshadowing_events || flags?.foreshadowing_events;
    if (Array.isArray(foreshadowItems) && foreshadowItems.length > 0) {
      foreshadowItems.forEach(fi => {
        const icon = fi.type === 'market_intel' ? '📈' : '📰';
        items.unshift({ type: 'alert', text: `${icon} BREAKING — ${fi.headline}: ${fi.body}`, isForeshadow: true });
      });
    }

    // Pathway-specific KPI alerts (R7+)
    if (events?.stranded_asset_exposure != null) {
      items.push({ type: 'alert', text: `🏭 Stranded Asset Exposure Index: ${events.stranded_asset_exposure.toFixed(1)} — Carbon-intensive assets face growing write-down risk.` });
    }
    if (events?.social_capital_index != null) {
      const sci = events.social_capital_index;
      items.push({ type: sci < 50 ? 'alert' : 'info', text: `🤝 Social Capital Index: ${sci.toFixed(1)}/100 — ${sci < 50 ? 'Critical stakeholder trust deficit.' : 'Stakeholder relationships stable.'}` });
    }
    if (events?.takeover_vulnerability_index != null) {
      const tvi = events.takeover_vulnerability_index;
      items.push({ type: tvi > 60 ? 'alert' : 'info', text: `🦈 Takeover Vulnerability Index: ${tvi.toFixed(1)}/100 — ${tvi > 60 ? 'HIGH RISK: Conglomerate discount makes you an attractive target.' : 'Defences holding — strategic integration discourages raiders.'}` });
    }
    if (events?.compliance_risk_index != null) {
      const cri = events.compliance_risk_index;
      items.push({ type: cri > 50 ? 'alert' : 'info', text: `⚖️ Compliance Risk Index: ${cri.toFixed(1)}/100 — ${cri > 50 ? 'ELEVATED: Regulatory exposure exceeds safe thresholds.' : 'Compliance posture within acceptable limits.'}` });
    }

    // ── HARDENING PHASE: Market Events ──
    // Macro Rate Environment
    if (events?.macro_rate_environment) {
      const macro = events.macro_rate_environment;
      const regimeIcons = { easing: '🕊️', neutral: '⚖️', tightening: '🦅', crisis: '🔥' };
      items.push({ type: macro.regime === 'tightening' || macro.regime === 'crisis' ? 'alert' : 'info', text: `${regimeIcons[macro.regime] || '🏦'} CENTRAL BANK: ${macro.label}` });
    }
    // FX Currency Shift
    if (events?.fx_risk) {
      const fx = events.fx_risk;
      const pct = (Math.abs(fx.fx_index) * 100).toFixed(1);
      items.push({ type: fx.fx_direction === 'weakening' ? 'alert' : 'info', text: `💱 FX MARKETS: Currency ${fx.fx_direction} by ${pct}% — multinational revenues ${fx.fx_direction === 'strengthening' ? 'boosted' : 'dragged'}.` });
    }
    // EU AI Act Compliance
    if (events?.eu_ai_act_compliance) {
      items.push({ type: 'alert', text: `🤖 REGULATION: EU AI Act compliance audit triggered — $${((events.eu_ai_act_compliance.cost || 0) / 1_000_000).toFixed(1)}M in governance costs.` });
    } else if (events?.eu_ai_act_pending) {
      items.push({ type: 'info', text: `🤖 REGULATORY WATCH: EU AI Act classifies your AI deployment as 'high-risk'. Compliance costs pending from Round 7.` });
    }
    // Scope 3 Data Challenge
    if (events?.scope3_data_completeness != null) {
      const c = events.scope3_data_completeness;
      items.push({ type: c < 50 ? 'alert' : 'info', text: `📊 DISCLOSURE: Scope 3 supply chain data at ${c}% completeness — ${c < 50 ? 'investor pressure mounting for transparency' : 'disclosure levels tracking industry benchmarks'}.` });
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

  // ── Dynamic UI State: Cockpit theme shifts based on game health ──
  const uiStateClass = tippingPointActive
    ? styles.cockpitCritical
    : reputation < 35
      ? styles.cockpitStressed
      : reputation > 70
        ? styles.cockpitThriving
        : '';

  // ── Phase 3.1: Round-Tier Complexity Scaling ──
  // Foundation (R1-3) → Crisis (R4-6) → Integration (R7-9) → Finale (R10)
  const roundTier = roundNumber <= 3 ? 'foundation'
    : roundNumber <= 6 ? 'crisis'
    : roundNumber <= 9 ? 'integration'
    : 'finale';
  const roundTierClass = {
    foundation: styles.roundTierFoundation,
    crisis: styles.roundTierCrisis,
    integration: styles.roundTierIntegration,
    finale: styles.roundTierFinale,
  }[roundTier] || '';

  // ── Phase 4.4: Board Mood Ambient Indicator ──
  const boardMoodClass = reputation > 70 ? styles.boardMoodThriving
    : reputation < 35 ? styles.boardMoodStressed
    : styles.boardMoodNeutral;
  // ── Phase 4.5: Keyboard Navigation ──
  // 1/2/3 for Option A/B/C, Ctrl+Enter to commit
  useEffect(() => {
    const handler = (e) => {
      // Only handle when no modal is open and decisions are accessible
      if (commitResults || !canAccessStrategy) return;
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;

      if (decisionParadigm === 'legacy_abc') {
        const keyMap = { '1': 'option_a', '2': 'option_b', '3': 'option_c' };
        if (keyMap[e.key] && options[keyMap[e.key]]) {
          e.preventDefault();
          handleLegacySelect(keyMap[e.key]);
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [decisionParadigm, options, commitResults, canAccessStrategy, handleLegacySelect]);

  // ── Consequence Traceability: map market events to causal decisions ──
  const traceConsequence = useCallback((itemText) => {
    if (!itemText || !history?.length) return null;
    const text = itemText.toLowerCase();
    for (let i = history.length - 1; i >= 0; i--) {
      const h = history[i];
      const decisions = h.global_state?.active_event_flags?.round_decisions;
      if (!decisions) continue;
      const roundNum = h.round_number;
      // Match event keywords to decision types
      if (text.includes('talent') || text.includes('brain-drain')) {
        if (decisions.includes?.('option_a') || decisions?.option_a)
          return { round: roundNum, decision: 'Option A — Aggressive cost-cutting reduced talent retention', roundTitle: ROUND_TITLES[roundNum] };
      }
      if (text.includes('greenwash') || text.includes('trust')) {
        return { round: roundNum, decision: `Round ${roundNum} ESG posture triggered reputational cascade`, roundTitle: ROUND_TITLES[roundNum] };
      }
      if (text.includes('supply chain') || text.includes('scope 3')) {
        return { round: roundNum, decision: `Round ${roundNum} supply chain strategy created downstream exposure`, roundTitle: ROUND_TITLES[roundNum] };
      }
      if (text.includes('inflation') || text.includes('opex')) {
        return { round: roundNum, decision: `Macro inflation compounding from Round ${roundNum} cost structure`, roundTitle: ROUND_TITLES[roundNum] };
      }
      if (text.includes('carbon') || text.includes('tipping point')) {
        return { round: roundNum, decision: `Cumulative emission trajectory set by Round ${roundNum} allocations`, roundTitle: ROUND_TITLES[roundNum] };
      }
      if (text.includes('stakeholder') || text.includes('salience')) {
        return { round: roundNum, decision: `Stakeholder priorities shifted due to Round ${roundNum} decisions`, roundTitle: ROUND_TITLES[roundNum] };
      }
    }
    return null;
  }, [history]);

  return (
    <div className={`${styles.cockpit} ${uiStateClass} ${roundTierClass} ${boardMoodClass}`}>
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
          <span key={`yr-${roundNumber}`} className={styles.headerYear}>{getRoundLabel(roundNumber)}</span>
          <span className={styles.headerDivider} />
          <span key={`mod-${roundNumber}`} className={styles.headerModule}>Turn {roundNumber}</span>
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
            background: decisionParadigm === 'advanced_climate' ? 'rgba(16,185,129,0.18)' : 'rgba(99,102,241,0.12)',
            border: decisionParadigm === 'advanced_climate' ? '1px solid rgba(16,185,129,0.35)' : '1px solid rgba(99,102,241,0.25)',
            fontSize: '0.62rem', fontWeight: 700, textTransform: 'uppercase',
            letterSpacing: '0.04em',
            color: decisionParadigm === 'advanced_climate' ? '#6ee7b7' : '#818cf8',
            whiteSpace: 'nowrap',
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
          {/* Projected cost moved to commit footer for better saliency */}
        </div>
      </header>

      {/* ═══ MAIN CONTENT (3 COLUMNS) ═══ */}
      <div className={`${styles.mainContent} ${isFocusActive ? focusStyles.dashboardFaded : ''}`}>

        {/* ── LEFT: KPI Dashboard ─── */}
        <aside id="tour-kpi-target" className={`${styles.leftSidebar} ${kpiFlashActive ? styles.kpiFlash : ''}`}>
          
          {/* Phase 3.2: Round Context Card — narrative context FIRST */}
          <div className={styles.roundContextCard}>
            <div className={styles.roundContextBadge}>
              <span className={styles.roundContextTier}>
                {{foundation: '🌱 FOUNDATION', crisis: '🔥 CRISIS', integration: '🔗 INTEGRATION', finale: '🏆 FINALE'}[roundTier]}
              </span>
              <span className={styles.roundContextRound}>R{roundNumber}/10</span>
            </div>
            <div className={styles.roundContextTitle}>{activeRoundTitles[roundNumber] || `Module ${roundNumber}`}</div>
            {crisisInfo?.description && (
              <div className={styles.roundContextDesc}>
                {crisisInfo.description.substring(0, 120)}{crisisInfo.description.length > 120 ? '…' : ''}
              </div>
            )}
          </div>

          {/* Resources Panel (2×2 grid) */}
          <div style={{ background: '#0a0e1a', borderBottom: '1px solid rgba(0, 229, 195, 0.2)', paddingTop: 10, paddingBottom: 10 }}>
          <div className={styles.resourcesPanel}>
            <div className={`${styles.resourceCard} ${shadowDeltas ? styles.resourceCardShadow : ''}`}>
              <div className={styles.resourceLabel}>💰 Treasury</div>
              <div className={styles.resourceValue}>{fmtCurrency(treasury)}</div>
              {shadowDeltas?.treasury !== 0 && shadowDeltas?.treasury && (
                <div style={{ fontSize: '0.6rem', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: shadowDeltas.treasury < 0 ? '#f87171' : '#4ade80', marginTop: 2 }}>
                  → {fmtCurrency(treasury + shadowDeltas.treasury)} ({shadowDeltas.treasury > 0 ? '+' : ''}{fmtCurrency(shadowDeltas.treasury)})
                </div>
              )}
            </div>
            {!isHealthcare && (() => {
              const carbonFeePerRound = (tco2e * (globalState?.internal_carbon_fee_rate || 15)) || 0;
              const greenFundTooltip = decisionParadigm === 'advanced_climate'
                ? `Balance: ${fmtCurrency(greenFund)}\nEst. fee this round: ${fmtCurrency(carbonFeePerRound)}\nThis fund auto-subsidises green CapEx and round costs. Decarbonising your BUs reduces the inflow.`
                : 'Funded by your internal carbon fee (emissions × $/tonne). Used to automatically subsidise your green CapEx investments and round costs.';
              return (
                <div className={styles.resourceCard} title={greenFundTooltip}>
                  <div className={styles.resourceLabel}>🌱 Green Fund</div>
                  <div className={styles.resourceValue} style={{ color: '#4ade80' }}>{fmtCurrency(greenFund)}</div>
                  {greenFund === 0 && decisionParadigm === 'advanced_climate' && (
                    <div style={{ fontSize: '0.52rem', color: '#6ee7b7', marginTop: 2, lineHeight: 1.3 }}>Funded by carbon fee</div>
                  )}
                  {greenFund > 0 && decisionParadigm === 'advanced_climate' && (
                    <div style={{ fontSize: '0.52rem', color: '#6ee7b7', marginTop: 2, lineHeight: 1.3 }}>+{fmtCurrency(carbonFeePerRound)}/round est.</div>
                  )}
                </div>
              );
            })()}
            <div className={`${styles.resourceCard} ${shadowDeltas ? styles.resourceCardShadow : ''}`}>
              <div className={styles.resourceLabel}>🌍 Reputation</div>
              <div className={styles.resourceValue}>{reputation.toFixed(0)}<span style={{ fontSize: '0.55rem', color: '#475569', marginLeft: 2 }}>/100</span></div>
              {shadowDeltas?.reputation !== 0 && shadowDeltas?.reputation && (
                <div style={{ fontSize: '0.6rem', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: shadowDeltas.reputation < 0 ? '#f87171' : '#4ade80', marginTop: 2 }}>
                  → {(reputation + shadowDeltas.reputation).toFixed(0)} ({shadowDeltas.reputation > 0 ? '+' : ''}{shadowDeltas.reputation})
                </div>
              )}
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
          
          {/* P1: Macro & Strategy Indicators — Advanced Metrics Drawer */}
          <div className={styles.advancedMetricsDrawer} style={{ padding: '0 12px 10px 12px', marginTop: 12 }}>
            <button
              className={`${styles.advancedMetricsToggle} ${advancedMetricsOpen ? styles.advancedMetricsToggleOpen : ''}`}
              onClick={() => setAdvancedMetricsOpen(v => !v)}
            >
              <span>📊 Advanced Metrics</span>
              <span className={`${styles.advancedMetricsChevron} ${advancedMetricsOpen ? styles.advancedMetricsChevronOpen : ''}`}>▾</span>
            </button>
            {advancedMetricsOpen && (
              <div className={styles.advancedMetricsBody}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <div style={{ flex: 1, padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: '1px solid rgba(0, 229, 195, 0.1)' }}>
                      <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: 4 }}>Synergy</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: 800, color: (globalState?.synergy_multiplier || 1) < 1 ? '#ef4444' : '#00e5c3', fontFamily: 'JetBrains Mono, monospace' }}>
                        {(globalState?.synergy_multiplier || 1).toFixed(2)}×
                      </div>
                    </div>
                    <div style={{ flex: 1, padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: '1px solid #334155' }}>
                      <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: 4 }}>Inflation</div>
                      <div style={{ fontSize: '0.8rem', fontWeight: 800, color: (globalState?.inflation_index || 0) > 0.03 ? '#f59e0b' : '#f8fafc', fontFamily: 'JetBrains Mono, monospace' }}>
                        {fmtInflation(globalState?.inflation_index)}
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
                  {/* Macro Rate Regime + FX Indicators */}
                  {(() => {
                    const macroEvt = events?.macro_rate_environment || commitResults?.events?.macro_rate_environment;
                    const fxEvt = events?.fx_risk || commitResults?.events?.fx_risk;
                    if (!macroEvt && !fxEvt) return null;
                    return (
                      <div style={{ display: 'flex', gap: 6 }}>
                        {macroEvt && (
                          <div style={{ flex: 1, padding: '6px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: `1px solid ${macroEvt.regime === 'tightening' || macroEvt.regime === 'crisis' ? 'rgba(239,68,68,0.3)' : macroEvt.regime === 'neutral' ? '#334155' : 'rgba(16,185,129,0.2)'}` }}>
                            <div style={{ fontSize: '0.55rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: 2 }}>Monetary Policy</div>
                            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: macroEvt.regime === 'tightening' || macroEvt.regime === 'crisis' ? '#f87171' : macroEvt.regime === 'neutral' ? '#e2e8f0' : '#6ee7b7', fontFamily: 'JetBrains Mono, monospace' }}>
                              {{ easing: '🕊️ Easing', neutral: '⚖️ Neutral', tightening: '🦅 Hawk', crisis: '🔥 Crisis' }[macroEvt.regime] || macroEvt.regime}
                            </div>
                          </div>
                        )}
                        {fxEvt && (
                          <div style={{ flex: 1, padding: '6px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: '1px solid #334155' }}>
                            <div style={{ fontSize: '0.55rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: 2 }}>FX Index</div>
                            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: fxEvt.fx_direction === 'strengthening' ? '#6ee7b7' : '#fbbf24', fontFamily: 'JetBrains Mono, monospace' }}>
                              {fxEvt.fx_direction === 'strengthening' ? '↑' : '↓'} {(Math.abs(fxEvt.fx_index) * 100).toFixed(1)}%
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })()}
                  {/* CE-03: Avg Carbon Intensity gauge for Advanced Climate */}
                  {decisionParadigm === 'advanced_climate' && !isHealthcare && (
                    <div style={{ padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: `1px solid ${avgCarbonIntensity > 70 ? 'rgba(239,68,68,0.4)' : avgCarbonIntensity > 50 ? 'rgba(245,158,11,0.3)' : 'rgba(16,185,129,0.2)'}` }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <span style={{ fontSize: '0.6rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700 }}>Avg Carbon Intensity</span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: avgCarbonIntensity > 70 ? '#f87171' : avgCarbonIntensity > 50 ? '#fbbf24' : '#4ade80' }}>
                          {avgCarbonIntensity.toFixed(1)}
                        </span>
                      </div>
                      <div style={{ height: 3, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${Math.min(100, (avgCarbonIntensity / 120) * 100)}%`, background: avgCarbonIntensity > 70 ? '#ef4444' : avgCarbonIntensity > 50 ? '#f59e0b' : '#10b981', borderRadius: 2, transition: 'width 0.5s' }} />
                      </div>
                      <div style={{ fontSize: '0.52rem', color: '#64748b', marginTop: 3 }}>
                        {avgCarbonIntensity > 70 ? '⚠️ Tipping point risk' : avgCarbonIntensity > 50 ? '⚡ Elevated — reduce below 70' : '✅ Managed — below threshold'}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
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
          <BenchmarksPanel sessionId={sim?.sessionId || sim?.session_id} roundNumber={roundNumber} />
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

            {/* Flag Dependency Warnings — transparency layer */}
            <FlagDependencyWarnings
              roundNumber={roundNumber}
              activeFlags={globalState?.active_event_flags || {}}
            />

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
            {/* R1a Orientation Panel (Foundation/Advanced tiers) */}
            {roundNumber === 1 && (
              <OrientationPanel
                onComplete={() => {}}
                onOpenStakeholderMap={onOpenStakeholderMap}
                hasCompletedStakeholderMap={hasCompletedStakeholderMap}
              />
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
              decisionParadigm={decisionParadigm}
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
            {!canAccessStrategy && (
              <div className={styles.freeExploreHint}>
                💡 While completing prerequisites, you can freely browse Mailbox, Market Feed &amp; Analytics in the right panel
              </div>
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
              /* ── Legacy A/B/C: 3 horizontal tiles (Phase 1.4: shared DecisionTile) ── */
              <div className={styles.decisionTiles}>
                {['option_a', 'option_b', 'option_c'].map((optId) => {
                  const opt = options[optId];
                  if (!opt) return null;
                  const maxCost = Math.max(
                    ...['option_a','option_b','option_c'].map(k => Math.abs(options[k]?.impacts?.treasury || options[k]?.cost_impact || 1))
                  );
                  return (
                    <DecisionTile
                      key={optId}
                      optId={optId}
                      option={opt}
                      isActive={decisionChoice === optId}
                      onSelect={handleLegacySelect}
                      onHover={(id) => { setHoveredOpt(id); setHoveredOption(id); }}
                      onLeave={() => { setHoveredOpt(null); setHoveredOption(null); }}
                      detailedDesc={DETAILED_DESCRIPTIONS.narrative?.[roundNumber]?.[optId]}
                      fmtCurrency={fmtCurrency}
                      treasury={treasury}
                      reputation={reputation}
                      maxCost={maxCost}
                      roundNumber={roundNumber}
                    />
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

            {/* Phase 3.3: Consequence DNA — causal chains from past decisions (R4+) */}
            <ConsequenceDNA
              history={history}
              roundNumber={roundNumber}
              globalState={globalState}
              events={events}
            />

            {/* Phase 3.7: Terminal Valuation Calculator (R9-10 Finale tier) */}
            <TerminalValuationCalc
              globalState={globalState}
              businessUnits={businessUnits}
              roundNumber={roundNumber}
              history={history}
              fmtCurrency={fmtCurrency}
            />

            {/* Active Infrastructure Projects — Collapsible */}
            {pendingProjects.length > 0 && (
              <div style={{ borderRadius: 8, overflow: 'hidden', border: '1px solid #e2e8f0', marginTop: 10 }}>
                <button
                  onClick={() => setInfraOpen(v => !v)}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                    padding: '10px 14px', border: 'none',
                    borderRadius: infraOpen ? '8px 8px 0 0' : 8,
                    background: infraOpen ? '#f8fafc' : '#f1f5f9',
                    borderLeft: '3px solid #38bdf8',
                    cursor: 'pointer', transition: 'all 0.2s',
                    fontFamily: "'Inter', 'Segoe UI', sans-serif",
                  }}
                >
                  <span style={{ fontSize: '1rem', flexShrink: 0 }}>🏗️</span>
                  <span style={{
                    flex: 1, textAlign: 'left', fontSize: '0.78rem', fontWeight: 700,
                    color: '#1e293b', letterSpacing: '0.03em',
                  }}>
                    Active Infrastructure Projects
                  </span>
                  <span style={{
                    padding: '3px 8px', borderRadius: 6, fontSize: '0.6rem', fontWeight: 700,
                    background: '#38bdf820', color: '#0284c7',
                    border: '1px solid #38bdf840', whiteSpace: 'nowrap',
                  }}>
                    {pendingProjects.length} active
                  </span>
                  <span style={{
                    fontSize: '0.65rem', color: '#94a3b8',
                    transition: 'transform 0.2s', transform: infraOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                  }}>▾</span>
                </button>
                {infraOpen && (
                  <div style={{
                    padding: '10px 14px', background: '#ffffff',
                    borderTop: '1px solid #e2e8f0',
                  }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {pendingProjects.map((proj, i) => (
                        <div key={i} style={{
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                          background: '#f8fafc', padding: '8px 10px', borderRadius: 6,
                          border: '1px solid #e2e8f0',
                        }}>
                          <span style={{ fontSize: '0.75rem', color: '#1e293b', fontWeight: 500 }}>{proj.description || 'Strategic Project'}</span>
                          <span style={{
                            fontSize: '0.65rem', color: '#475569', background: '#e2e8f0',
                            padding: '3px 8px', borderRadius: 4, fontWeight: 600, whiteSpace: 'nowrap',
                          }}>
                            ⏳ {proj.rounds_remaining} Turn{proj.rounds_remaining > 1 ? 's' : ''} Left
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

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

          <CompetitorIntelligence globalState={globalState} ebitda={ebitda} roundNumber={roundNumber} />

          {/* MP-01: Round commit status — shows how many teams have committed */}
          {sim?.sessionId && sim.sessionId !== 'demo' && (globalState?.cohort_team_count > 0) && (
            <div style={{
              padding: '6px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              background: (globalState?.team_commits_this_round || 0) >= globalState.cohort_team_count ? 'rgba(16,185,129,0.08)' : 'rgba(99,102,241,0.06)',
              borderBottom: '1px solid rgba(0,229,195,0.06)',
            }}>
              <span style={{ fontSize: '0.62rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Round {roundNumber} Status
              </span>
              <span style={{ fontSize: '0.68rem', fontWeight: 800, color: (globalState?.team_commits_this_round || 0) >= globalState.cohort_team_count ? '#10b981' : '#6366f1' }}>
                {globalState?.team_commits_this_round || 0}/{globalState.cohort_team_count} committed {(globalState?.team_commits_this_round || 0) >= globalState.cohort_team_count ? '✓' : '...'}
              </span>
            </div>
          )}

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
                📬 Mailbox {unreadCount > 0 && (
                  <span
                    className={styles.mailboxBadge}
                    style={{ animation: 'pulse 1.5s ease-in-out infinite' }}
                  >
                    {unreadCount}
                  </span>
                )}
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

          {/* Market Reality Feed — with Consequence Traceability */}
          <div className={styles.rightMarket} style={{ height: 'auto', minHeight: '20%', maxHeight: '35%' }}>
            <MarketRealityFeed
              items={marketEvents}
              activeAlert={activeAlert}
              traceConsequence={traceConsequence}
              traceTooltipIdx={traceTooltipIdx}
              onTraceHover={setTraceTooltipIdx}
            />
          </div>

          {/* What Happened / Road Not Taken / CEO Diary — Collapsible Accordions */}
          <div style={{
            flex: '1 1 auto', overflowY: 'auto', padding: '8px 10px',
            borderTop: '1px solid #1e293b',
          }}>
            <EngineEventsPanel globalState={globalState} roundEvents={events || commitResults?.events} />
          </div>

          {/* Phase 3.6: Synergy Tracker (R7+ Integration tier) */}
          <SynergyTracker
            globalState={globalState}
            roundNumber={roundNumber}
            workforceReady={globalState?.workforce_readiness}
          />

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
              {/* UX-04: Over-allocation warning */}
              {(Object.values(allocations || {}).reduce((s, v) => s + v, 0) > (csfPool || 0)) && (csfPool > 0) && !commitResults && (
                <div style={{
                  padding: '6px 10px', borderRadius: 6, background: 'rgba(239,68,68,0.12)',
                  border: '1px solid rgba(239,68,68,0.35)', fontSize: '0.62rem', color: '#fca5a5',
                  textAlign: 'center', lineHeight: 1.4, width: '100%',
                }}>
                  ⚠️ Over-allocated by {fmtCurrency(Object.values(allocations || {}).reduce((s, v) => s + v, 0) - (csfPool || 0))} — reduce CapEx to commit
                </div>
              )}
              {/* ── Projected Impact Widget (repositioned from header) ── */}
              {projectedCost !== 0 && !commitResults && (
                <div className={`${styles.projectedImpactWidget} ${projectedCost > 0 ? styles.impactNegative : styles.impactPositive}`}>
                  <span className={styles.projectedImpactLabel}>
                    {projectedCost > 0 ? '📉 Staged Cost' : '📈 Staged Gain'}
                  </span>
                  <span className={styles.projectedImpactValue} style={{ color: projectedCost > 0 ? '#f87171' : '#4ade80' }}>
                    {projectedCost > 0 ? '↓' : '↑'} {fmtCurrency(Math.abs(projectedCost))}
                  </span>
                </div>
              )}
              <motion.button
                className={`${styles.commitBtn} ${commitResults ? styles.commitBtnDone : ''}`}
                style={{ width: '100%', height: 42, fontSize: '0.85rem' }}
                disabled={!!commitResults}
                onClick={() => {
                  if (!commitResults) {
                    setShowPredictionModal(true);
                  }
                }}
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

      {/* ═══ FOCUS MODE OVERLAY ═══ */}
      <FocusOverlay
        isOpen={isFocusActive}
        step={focusStep}
        steps={focusSteps}
        onClose={handleFocusDismiss}
        onBack={handleFocusAdvance}
        onReenter={focusDismissed && !commitResults && hasReadBriefing && !sim?.gameOver ? handleFocusReenter : null}
      >
        {/* ── GATE STEP ── */}
        {focusStep === 'gate' && (
          <div className={focusStyles.gateCard}>
            {roundNumber === 1 && !hasCompletedStakeholderMap && (
              <>
                <div className={focusStyles.gateIcon}>⚖️</div>
                <h3 className={focusStyles.gateTitle}>Stakeholder Power / Interest Grid</h3>
                <p className={focusStyles.gateDescription}>
                  Before making strategic decisions, you must map your key stakeholders. This assessment will influence crisis severity in later rounds.
                </p>
                <button className={focusStyles.gateLaunchButton} onClick={onOpenStakeholderMap}>
                  🗺️ Open Stakeholder Map
                </button>
              </>
            )}
            {roundNumber === 1 && hasCompletedStakeholderMap && (
              <div className={focusStyles.gateComplete}>
                <div className={focusStyles.gateCompleteBadge}>✅</div>
                <div className={focusStyles.gateCompleteText}>
                  Stakeholder Map Complete{stakeholderAccuracy != null ? ` — ${stakeholderAccuracy.toFixed(0)}% accuracy` : ''}
                </div>
                <button className={focusStyles.actionButton} onClick={() => handleFocusAdvance('strategy')}>
                  Proceed to Strategic Decision →
                </button>
              </div>
            )}
            {roundNumber === 2 && !hasSubmittedMatrix && (
              <>
                <div className={focusStyles.gateIcon}>🚨</div>
                <h3 className={focusStyles.gateTitle}>CSRD Materiality Assessment</h3>
                <p className={focusStyles.gateDescription}>
                  The board requires a double materiality assessment before capital can be deployed. Complete the CSRD matrix to unlock strategic options.
                </p>
                <button className={focusStyles.gateLaunchButton} onClick={onOpenCSRD}>
                  📋 Open CSRD Assessment
                </button>
              </>
            )}
            {roundNumber === 2 && hasSubmittedMatrix && (
              <div className={focusStyles.gateComplete}>
                <div className={focusStyles.gateCompleteBadge}>✅</div>
                <div className={focusStyles.gateCompleteText}>CSRD Assessment Submitted</div>
                <button className={focusStyles.actionButton} onClick={() => handleFocusAdvance('strategy')}>
                  Proceed to Strategic Decision →
                </button>
              </div>
            )}
          </div>
        )}

        {/* ── STRATEGY STEP ── */}
        {focusStep === 'strategy' && (
          <div>
            <KPIStrip treasury={treasury} reputation={reputation} carbon={tco2e} ebitda={ebitda} projectedCost={projectedCost} fmtCurrency={fmtCurrency} />

            <div className={focusStyles.sectionTitle}>
              <span>{decisionParadigm === 'multi_toggles' ? '🎛️' : '📋'}</span>
              {decisionParadigm === 'multi_toggles' ? 'Strategic Pillars' : 'Strategic Options'}
              {projectedCost !== 0 && (
                <span style={{ marginLeft: 'auto', color: projectedCost > 0 ? '#f87171' : '#4ade80', fontWeight: 800, fontSize: '0.72rem' }}>
                  Impact: {fmtCurrency(projectedCost)}
                </span>
              )}
            </div>

            {decisionParadigm === 'multi_toggles' ? (
              <div className={focusStyles.focusPillarTiles}>
                {pillarConfig?.areas && Object.entries(pillarConfig.areas).map(([areaKey, area]) => {
                  const selectedOpt = pillarSelections?.[areaKey];
                  return (
                    <div key={areaKey} className={`${styles.pillarTile} ${selectedOpt ? styles.pillarTileActive : ''}`}>
                      <div className={styles.pillarIcon}>{AREA_ICONS[areaKey] || '📌'}</div>
                      <div className={styles.pillarLabel}>{area.label}</div>
                      <select
                        className={styles.pillarSelect}
                        value={selectedOpt || ''}
                        onChange={(e) => handlePillarSelect(areaKey, e.target.value || null)}
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
              <div className={focusStyles.focusDecisionTiles}>
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
                  return (
                    <div
                      key={optId}
                      className={`${styles.decisionTile} ${isActive ? styles.decisionTileActive : ''}`}
                      onClick={() => handleLegacySelect(optId)}
                      style={{ flex: '1 1 0', minWidth: 0 }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                        <span style={{ fontSize: '1rem' }}>{optMeta.icon}</span>
                        <span className={styles.tileLabel} style={{ margin: 0 }}>{optMeta.label}</span>
                      </div>
                      <div className={styles.tileTitle}>{opt.title}</div>
                      <p className={styles.tileDesc}>{opt.description}</p>
                      {costVal ? (
                        <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.6rem' }}>
                          <span style={{ color: '#64748b', fontWeight: 600 }}>💰 Cost</span>
                          <span style={{ fontSize: '0.72rem', fontWeight: 800, color: costVal < 0 ? '#16a34a' : '#ef4444' }}>{fmtCurrency(costVal)}</span>
                        </div>
                      ) : (
                        <div style={{ marginTop: 6, fontSize: '0.6rem', fontWeight: 700, color: '#f59e0b' }}>⚠️ $0 CapEx — deferred risk</div>
                      )}
                      {isActive && opt.impacts && (
                        <div style={{ marginTop: 6, padding: '4px 6px', background: 'rgba(0,229,195,0.04)', borderRadius: 4, fontSize: '0.58rem', lineHeight: 1.6, border: '1px solid rgba(0,229,195,0.08)' }}>
                          {opt.impacts.treasury && (
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: opt.impacts.treasury < 0 ? '#4ade80' : '#f87171' }}>
                              <span>💰 Treasury</span>
                              <span style={{ fontWeight: 700 }}>{fmtCurrency(treasury)} → {fmtCurrency(treasury + (opt.impacts.treasury || 0))}</span>
                            </div>
                          )}
                          {opt.impacts.reputation !== undefined && (
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: opt.impacts.reputation > 0 ? '#4ade80' : '#f87171' }}>
                              <span>🌍 Reputation</span>
                              <span style={{ fontWeight: 700 }}>{reputation} → {reputation + (opt.impacts.reputation || 0)}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Comparison Matrix for legacy A/B/C */}
            {decisionParadigm !== 'multi_toggles' && Object.keys(options).length > 0 && (
              <div style={{ marginTop: 16, padding: '12px 14px', background: isDark ? 'rgba(0,0,0,0.2)' : '#f8fafc', borderRadius: 10, border: isDark ? '1px solid rgba(0,229,195,0.06)' : '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase', color: isDark ? '#94a3b8' : '#475569', marginBottom: 8 }}>Comparison Matrix</div>
                <table style={{ width: '100%', fontSize: '0.7rem', borderCollapse: 'collapse', color: isDark ? '#d1d9e6' : '#1e293b' }}>
                  <thead>
                    <tr style={{ borderBottom: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid #e2e8f0' }}>
                      <th style={{ textAlign: 'left', paddingBottom: 4, color: isDark ? '#b0bec5' : '#475569' }}>Option</th>
                      <th style={{ textAlign: 'center', paddingBottom: 4, color: isDark ? '#b0bec5' : '#475569' }}>Treasury</th>
                      <th style={{ textAlign: 'center', paddingBottom: 4, color: isDark ? '#b0bec5' : '#475569' }}>Reputation</th>
                      <th style={{ textAlign: 'center', paddingBottom: 4, color: isDark ? '#b0bec5' : '#475569' }}>CO₂</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(options).map(([optId, opt]) => (
                      <tr key={optId} style={{ borderBottom: isDark ? '1px solid rgba(255,255,255,0.04)' : '1px solid #f1f5f9' }}>
                        <td style={{ padding: '6px 0', fontWeight: 600 }}>{optId.replace('option_', 'Option ').toUpperCase()}</td>
                        <td style={{ textAlign: 'center', color: opt.impacts?.treasury < 0 ? '#4ade80' : opt.impacts?.treasury > 0 ? '#f87171' : (isDark ? '#64748b' : '#94a3b8') }}>
                          {opt.impacts?.treasury ? fmtCurrency(opt.impacts.treasury) : '—'}
                        </td>
                        <td style={{ textAlign: 'center', color: opt.impacts?.reputation > 0 ? '#4ade80' : opt.impacts?.reputation < 0 ? '#f87171' : (isDark ? '#64748b' : '#94a3b8') }}>
                          {opt.impacts?.reputation ? (opt.impacts.reputation > 0 ? '+' : '') + opt.impacts.reputation : '—'}
                        </td>
                        <td style={{ textAlign: 'center', color: opt.impacts?.carbon < 0 ? '#4ade80' : opt.impacts?.carbon > 0 ? '#f87171' : '#64748b' }}>
                          {opt.impacts?.carbon ? (opt.impacts.carbon > 0 ? '+' : '') + opt.impacts.carbon + 't' : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <button
              className={focusStyles.actionButton}
              disabled={!hasDecision}
              onClick={() => handleFocusAdvance('allocation')}
            >
              {hasDecision ? 'Lock Decision & Continue →' : 'Select an option above to continue'}
            </button>
          </div>
        )}

        {/* ── ALLOCATION STEP ── */}
        {focusStep === 'allocation' && (
          <div>
            <KPIStrip treasury={treasury} reputation={reputation} carbon={tco2e} ebitda={ebitda} projectedCost={projectedCost} fmtCurrency={fmtCurrency} />

            {/* Locked decision summary */}
            <div className={focusStyles.decisionSummary}>
              <div className={focusStyles.decisionSummaryTitle}>📋 Locked Strategic Decision</div>
              {decisionParadigm === 'multi_toggles' ? (
                Object.entries(pillarSelections || {}).map(([areaKey, optKey]) => (
                  <div key={areaKey} className={focusStyles.decisionSummaryRow}>
                    <span>{AREA_ICONS[areaKey] || '📌'} {pillarConfig?.areas?.[areaKey]?.label || areaKey}</span>
                    <span className={focusStyles.decisionSummaryValue}>{pillarConfig?.areas?.[areaKey]?.options?.[optKey]?.title || optKey}</span>
                  </div>
                ))
              ) : (
                <div className={focusStyles.decisionSummaryRow}>
                  <span>Selected Strategy</span>
                  <span className={focusStyles.decisionSummaryValue}>
                    {decisionChoice?.replace('option_', 'Option ').toUpperCase()} — {options[decisionChoice]?.title || ''}
                  </span>
                </div>
              )}
            </div>

            <div className={focusStyles.sectionTitle}>
              <span>💰</span> Capital Allocation
              <span style={{ marginLeft: 'auto', fontSize: '0.72rem', fontWeight: 800, color: '#00e5c3' }}>
                Budget: {fmtCurrency(csfPool)}
              </span>
            </div>

            <InvestmentMatrix
              csfPool={csfPool}
              globalState={globalState}
              businessUnits={businessUnits}
              allocations={allocations}
              historyData={historyData}
              decisionParadigm={decisionParadigm}
              onAllocationsChange={onAllocationsChange}
            />

            {/* Over-allocation warning */}
            {(Object.values(allocations || {}).reduce((s, v) => s + v, 0) > (csfPool || 0)) && (csfPool > 0) && (
              <div style={{ padding: '8px 12px', borderRadius: 8, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', fontSize: '0.7rem', color: '#fca5a5', textAlign: 'center', marginTop: 10 }}>
                ⚠️ Over-allocated by {fmtCurrency(Object.values(allocations || {}).reduce((s, v) => s + v, 0) - (csfPool || 0))}
              </div>
            )}

            <button
              className={focusStyles.actionButton}
              disabled={Object.keys(allocations).length === 0}
              onClick={() => handleFocusAdvance('commit')}
            >
              {Object.keys(allocations).length > 0 ? 'Confirm Allocation & Continue →' : 'Allocate capital to at least one BU'}
            </button>
          </div>
        )}

        {/* ── COMMIT STEP ── */}
        {focusStep === 'commit' && !commitResults && (
          <div>
            {/* Prediction Section */}
            <div className={focusStyles.predictionArea}>
              <div className={focusStyles.sectionTitle}><span>🔮</span> Predict Before You Commit</div>
              <p style={{ fontSize: '0.78rem', color: '#94a3b8', lineHeight: 1.6, marginBottom: 12 }}>
                Pausing to predict outcomes strengthens strategic intuition. What do you expect will happen?
              </p>
              <div className={focusStyles.predictionPrompt}>
                💰 What will happen to your <strong style={{ color: '#e2e8f0' }}>Treasury</strong> and <strong style={{ color: '#e2e8f0' }}>Reputation</strong>?
              </div>
              <textarea
                className={focusStyles.predictionInput}
                placeholder="e.g., Treasury will drop by ~$3M due to ESG compliance costs, but reputation should rise..."
                value={focusPredictionText}
                onChange={(e) => setFocusPredictionText(e.target.value)}
                rows={3}
              />
            </div>

            {/* Full Recap */}
            <div className={focusStyles.commitRecap}>
              <div className={focusStyles.commitRecapTitle}>📋 Decision Summary</div>
              <div className={focusStyles.commitRecapRow}>
                <span>Strategy</span>
                <span className={focusStyles.commitRecapValue}>
                  {decisionParadigm === 'multi_toggles'
                    ? `${Object.keys(pillarSelections || {}).length} pillars selected`
                    : decisionChoice?.replace('option_', 'Option ').toUpperCase()}
                </span>
              </div>
              <div className={focusStyles.commitRecapRow}>
                <span>Capital Deployed</span>
                <span className={focusStyles.commitRecapValue}>
                  {fmtCurrency(Object.values(allocations || {}).reduce((s, v) => s + v, 0))}
                </span>
              </div>
              {projectedCost !== 0 && (
                <div className={focusStyles.commitRecapRow}>
                  <span>Projected Impact</span>
                  <span className={focusStyles.commitRecapValue} style={{ color: projectedCost > 0 ? '#f87171' : '#4ade80' }}>
                    {fmtCurrency(projectedCost)}
                  </span>
                </div>
              )}
            </div>

            <KPIStrip treasury={treasury} reputation={reputation} carbon={tco2e} ebitda={ebitda} projectedCost={projectedCost} fmtCurrency={fmtCurrency} />

            <div className={focusStyles.twoActions}>
              <button className={focusStyles.secondaryAction} onClick={() => {
                if (focusPredictionText.trim()) {
                  const key = `prediction_r${roundNumber}_${sim?.sessionId || 'demo'}`;
                  try { sessionStorage.setItem(key, focusPredictionText); } catch {}
                }
                setFocusPredictionText('');
                onCommit?.();
              }}>
                Skip Prediction & Submit
              </button>
              <button className={focusStyles.primaryAction} onClick={() => {
                if (focusPredictionText.trim()) {
                  const key = `prediction_r${roundNumber}_${sim?.sessionId || 'demo'}`;
                  try { sessionStorage.setItem(key, focusPredictionText); } catch {}
                }
                setFocusPredictionText('');
                onCommit?.();
              }}>
                ✓ Confirm & Submit
              </button>
            </div>
          </div>
        )}

        {/* ── RESULTS STEP ── */}
        {focusStep === 'results' && commitResults && (
          <div>
            <div style={{ textAlign: 'center', marginBottom: 16 }}>
              <div style={{ fontSize: '2rem', marginBottom: 4 }}>📊</div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#e2e8f0', margin: '0 0 4px' }}>Round {roundNumber} Results</h3>
              <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: 0 }}>Review your outcomes before advancing.</p>
            </div>

            <div className={focusStyles.focusResultsGrid}>
              {(() => {
                const newTreasury = commitResults.globalState?.corporate_treasury || 0;
                const newEbitda = commitResults.globalState?.historical_ebitda || 0;
                const newRep = commitResults.globalState?.group_reputation || 50;
                const newCarbon = commitResults.globalState?.tco2e_emissions || 0;
                const dTreasury = newTreasury - treasury;
                const dRep = newRep - reputation;
                const dCarbon = newCarbon - tco2e;
                return (
                  <>
                    <div className={focusStyles.focusResultCard}>
                      <div className={focusStyles.focusResultIcon}>💰</div>
                      <div className={focusStyles.focusResultLabel}>Treasury</div>
                      <div className={focusStyles.focusResultValue}>{fmtCurrency(newTreasury)}</div>
                      <div style={{ fontSize: '0.72rem', fontWeight: 800, color: dTreasury >= 0 ? '#4ade80' : '#f87171', marginTop: 2 }}>
                        {dTreasury >= 0 ? '▲' : '▼'} {fmtCurrency(Math.abs(dTreasury))}
                      </div>
                    </div>
                    <div className={focusStyles.focusResultCard}>
                      <div className={focusStyles.focusResultIcon}>📈</div>
                      <div className={focusStyles.focusResultLabel}>EBITDA</div>
                      <div className={focusStyles.focusResultValue}>{fmtCurrency(newEbitda)}</div>
                    </div>
                    <div className={focusStyles.focusResultCard}>
                      <div className={focusStyles.focusResultIcon}>🌍</div>
                      <div className={focusStyles.focusResultLabel}>Reputation</div>
                      <div className={focusStyles.focusResultValue}>{newRep.toFixed(0)}/100</div>
                      <div style={{ fontSize: '0.72rem', fontWeight: 800, color: dRep >= 0 ? '#4ade80' : '#f87171', marginTop: 2 }}>
                        {dRep >= 0 ? '▲' : '▼'} {Math.abs(dRep).toFixed(0)}
                      </div>
                    </div>
                    <div className={focusStyles.focusResultCard}>
                      <div className={focusStyles.focusResultIcon}>🏭</div>
                      <div className={focusStyles.focusResultLabel}>CO₂</div>
                      <div className={focusStyles.focusResultValue}>{newCarbon.toLocaleString()}t</div>
                      <div style={{ fontSize: '0.72rem', fontWeight: 800, color: dCarbon <= 0 ? '#4ade80' : '#f87171', marginTop: 2 }}>
                        {dCarbon > 0 ? '▲' : '▼'} {Math.abs(dCarbon).toLocaleString()}t
                      </div>
                    </div>
                  </>
                );
              })()}
            </div>

            {/* Events summary */}
            {commitResults.events && Object.keys(commitResults.events).length > 0 && (
              <div style={{ padding: '10px 14px', background: 'rgba(0,0,0,0.2)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)', marginBottom: 16, fontSize: '0.72rem', color: '#cbd5e1' }}>
                <div style={{ fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', marginBottom: 6, fontSize: '0.62rem' }}>⚡ Key Events</div>
                {commitResults.events.talent_penalty_applied > 1 && (
                  <div style={{ marginBottom: 3 }}>🧠 Brain-Drain: Software OPEX inflated by {((commitResults.events.talent_penalty_applied - 1) * 100).toFixed(1)}%</div>
                )}
                {commitResults.events.loan_interest_payment > 0 && (
                  <div style={{ marginBottom: 3 }}>🏦 Loan Interest: -{fmtCurrency(commitResults.events.loan_interest_payment)}</div>
                )}
              </div>
            )}

            {/* Advance button */}
            {(() => {
              const teamCount = globalState?.cohort_team_count || 0;
              const commitsCount = globalState?.team_commits_this_round || 0;
              const isMultiTeam = teamCount > 1;
              const allCommitted = commitsCount >= teamCount;
              if (isMultiTeam && !allCommitted) {
                return (
                  <div style={{ padding: '12px 16px', borderRadius: 10, textAlign: 'center', background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.25)' }}>
                    <div style={{ fontSize: '1rem', marginBottom: 4 }}>⏳</div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#818cf8', marginBottom: 2 }}>Waiting for Other Teams</div>
                    <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>{commitsCount}/{teamCount} committed</div>
                  </div>
                );
              }
              return (
                <div className={focusStyles.twoActions}>
                  <button className={focusStyles.secondaryAction} onClick={handleFocusDismiss}>
                    View Dashboard
                  </button>
                  <button className={focusStyles.primaryAction} onClick={() => { handleFocusDismiss(); onAdvance?.(); }}>
                    ⏩ Advance to Round {commitResults.newRoundNumber}
                  </button>
                </div>
              );
            })()}
          </div>
        )}
      </FocusOverlay>

      {/* ═══ PRE-COMMIT PREDICTION MODAL (Metacognitive Friction) ═══ */}
      {showPredictionModal && (
        <div className={styles.predictionOverlay} onClick={() => { setShowPredictionModal(false); }}>
          <div className={styles.predictionPanel} onClick={(e) => e.stopPropagation()}>
            <div style={{ fontSize: '2rem', textAlign: 'center', marginBottom: 8 }}>🔮</div>
            <h2 className={styles.predictionTitle}>Predict Before You Commit</h2>
            <p className={styles.predictionSubtitle}>
              Pausing to predict outcomes strengthens your strategic intuition. What do you expect will happen?
            </p>

            <div className={styles.predictionQuestion}>
              💰 What do you predict will happen to your <strong>Treasury</strong> after this round?
            </div>
            <textarea
              className={styles.predictionTextarea}
              placeholder="e.g., Treasury will drop by ~$3M due to ESG compliance costs, but reputation should rise..."
              value={predictionText}
              onChange={(e) => setPredictionText(e.target.value)}
              rows={3}
            />

            <div className={styles.predictionQuestion}>
              🌍 How will your choices affect <strong>Reputation</strong> and <strong>Carbon</strong>?
            </div>
            <textarea
              className={styles.predictionTextarea}
              placeholder="e.g., Option B is balanced — I expect a modest reputation boost with flat emissions..."
              rows={2}
            />

            {/* Summary of staged decisions */}
            <div style={{
              padding: '10px 14px', borderRadius: 8, marginBottom: 16,
              background: 'rgba(0, 229, 195, 0.04)', border: '1px solid rgba(0, 229, 195, 0.1)',
            }}>
              <div style={{ fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase', color: '#0d9488', marginBottom: 6, letterSpacing: '0.08em' }}>
                📋 Your Staged Decisions
              </div>
              <div style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: 1.6 }}>
                {decisionChoice && <div>Strategy: <strong style={{ color: '#f1f5f9' }}>{decisionChoice.replace('option_', 'Option ').toUpperCase()}</strong></div>}
                {Object.keys(pillarSelections || {}).length > 0 && (
                  <div>Pillars: <strong style={{ color: '#f1f5f9' }}>{Object.keys(pillarSelections).length} selected</strong></div>
                )}
                {projectedCost !== 0 && (
                  <div>Projected Impact: <strong style={{ color: projectedCost > 0 ? '#f87171' : '#4ade80' }}>
                    {fmtCurrency(projectedCost)}
                  </strong></div>
                )}
                <div>Capital Allocated: <strong style={{ color: '#f1f5f9' }}>
                  {fmtCurrency(Object.values(allocations || {}).reduce((s, v) => s + v, 0))}
                </strong></div>
              </div>
            </div>

            <div className={styles.predictionActions}>
              <button
                className={styles.predictionSkip}
                onClick={() => { setShowPredictionModal(false); setPredictionText(''); onCommit?.(); }}
              >
                Skip & Commit
              </button>
              <button
                className={styles.predictionSubmit}
                onClick={() => {
                  // Store prediction for post-round comparison
                  if (predictionText.trim()) {
                    const key = `prediction_r${roundNumber}_${sim?.sessionId || 'demo'}`;
                    try { sessionStorage.setItem(key, predictionText); } catch {}
                  }
                  setShowPredictionModal(false);
                  setPredictionText('');
                  onCommit?.();
                }}
              >
                ✓ Confirm & Commit
              </button>
            </div>
          </div>
        </div>
      )}

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

              {/* Phase 3.5: R5 Stochastic Dice Roll Animation */}
              {roundNumber === 5 && commitResults.events?.stochastic_damage !== undefined && (
                <StochasticDiceRoll
                  probability={0.75}
                  outcome={!!commitResults.events.stochastic_damage}
                  damageAmount={commitResults.events.stochastic_damage || 12000000}
                  fmtCurrency={fmtCurrency}
                />
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

              {/* Pedagogical: Post-Commit Scaffolding */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {pedToggles.round_recap_enabled && (
                  <RoundRecap recapData={{
                    round: roundNumber,
                    three_word_anchor: commitResults.events?.three_word_anchor,
                    causal_chains: commitResults.events?.causal_chains || [],
                    summary_sentence: commitResults.events?.round_summary,
                  }} />
                )}
                {/* Phase 3.4: Prediction vs Reality Comparison */}
                <PredictionComparison
                  predictions={predictions}
                  roundNumber={roundNumber}
                  commitResults={commitResults}
                  globalState={globalState}
                />
                {pedToggles.real_world_cards_enabled && (
                  <RealWorldCard roundNumber={roundNumber} />
                )}
                {pedToggles.board_room_moments_enabled && (
                  <BoardRoomMoment
                    roundNumber={roundNumber}
                    triggerReason={`Round ${roundNumber} results reviewed`}
                  />
                )}
                {pedToggles.mid_game_checkpoint_enabled && roundNumber === 5 && (
                  <MidGameCheckpoint checkpointData={checkpointData} />
                )}
                {/* Journey: R6 Revelation (post-decision whistleblower twist) */}
                {roundNumber === 6 && pedToggles.r6_revelation_enabled !== false && (
                  <R6RevelationPanel onMicroDecision={(data) => {
                    fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/global-settings`, {
                      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ [`journey_r6_response_${sessionId}`]: data }),
                    }).catch(() => {});
                  }} />
                )}
                {/* Journey: R7 Budget Allocation variant */}
                {roundNumber === 7 && pedToggles.r7_budget_allocation_enabled !== false && (
                  <BudgetAllocationPanel onAllocate={(allocs) => {
                    fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/global-settings`, {
                      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ [`journey_r7_allocs_${sessionId}`]: allocs }),
                    }).catch(() => {});
                  }} />
                )}
                {/* Journey: R8 Stakeholder Tribunal variant */}
                {roundNumber === 8 && pedToggles.r8_tribunal_enabled !== false && (
                  <StakeholderTribunal onResponses={(responses) => {
                    fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/global-settings`, {
                      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ [`journey_r8_responses_${sessionId}`]: responses }),
                    }).catch(() => {});
                  }} />
                )}
              </div>

              {/* MP-02: Block advance until all multiplayer teams have committed */}
              {(() => {
                const teamCount = globalState?.cohort_team_count || 0;
                const commitsCount = globalState?.team_commits_this_round || 0;
                const isMultiTeam = teamCount > 1;
                const allCommitted = commitsCount >= teamCount;

                if (isMultiTeam && !allCommitted) {
                  return (
                    <div style={{
                      padding: '12px 16px', borderRadius: 10, textAlign: 'center',
                      background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.25)',
                    }}>
                      <div style={{ fontSize: '1rem', marginBottom: 4 }}>⏳</div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#818cf8', marginBottom: 2 }}>
                        Waiting for Other Teams
                      </div>
                      <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>
                        {commitsCount}/{teamCount} teams committed — cannot advance yet
                      </div>
                    </div>
                  );
                }

                return (
                  <motion.button
                    className={styles.advanceBtnLarge}
                    onClick={onAdvance}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                  >
                    ⏩ Advance to Round {commitResults.newRoundNumber}
                  </motion.button>
                );
              })()}
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
