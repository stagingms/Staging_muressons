'use client';
import React from 'react';
import { useCurrency } from '../contexts/CurrencyContext';
import { useAnalyticsVisibility, isPanelVisible } from '../hooks/useAnalyticsVisibility';
import { useCohortPolish } from '../hooks/useCohortPolish';

import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './ExecutiveCockpit.module.css';
import KPIDashboard from './KPIDashboard';
import TurnaroundPhaseChip from './TurnaroundPhaseChip';
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
import PillarSelectDropdown from './PillarSelectDropdown';
// Phase 3: Progressive Disclosure components
import ConsequenceDNA from './ConsequenceDNA';
import ConsequenceDNAVisualizer, { ConsequenceDNATrigger } from './ConsequenceDNAVisualizer';
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
import SystemEngineMetrics from './SystemEngineMetrics';
import StrategicRadar from './StrategicRadar';
import RiskRadar from './RiskRadar';
import ConsequenceTimeline from './ConsequenceTimeline';
import ConsequencePreview from './ConsequencePreview';
import { playDeepDiveEnter, playDeepDiveExit, playCommitSuccess, playTippingWarning } from './CockpitSounds';
import StakeholderAgentPanel from './StakeholderAgentPanel';
import EBITDAWaterfall from './EBITDAWaterfall';
import LivingPlanet from './LivingPlanet';
import DecisionPressureTimer from './DecisionPressureTimer';
import ConsequenceReplay from './ConsequenceReplay';
import PlayerAnnotations from './PlayerAnnotations';
import WhatIfSandbox from './WhatIfSandbox';
import ShadowBoardAudit from './ShadowBoardAudit';
import TCFDScenarioDashboard from './TCFDScenarioDashboard';
import BalanceSheetModal from './BalanceSheetModal';
import soundManager from '../utils/soundManager';
import dynamic from 'next/dynamic';

// Antigravity Enhancement: 3D ESG Impact Constellation (code-split)
const ESGImpactConstellation = dynamic(() => import('./ESGImpactConstellation'), {
  ssr: false,
  loading: () => null,
});

// Phase A (player redesign): module-scope pieces extracted verbatim to their
// own files — BoardPersonas, EngineWidgetsPanel, ArchiveAccordion — and the
// focus stage machine to hooks/useRoundStage. Zero behavioural change.
import useRoundStage from '../hooks/useRoundStage';
import { BOARD_PERSONAS, getPersona } from './BoardPersonas';
import MarketIntel from './MarketIntelCards';
import AnnualReport from './AnnualReport';
import EngineWidgetsPanel from './EngineWidgetsPanel';
import ArchiveAccordion from './ArchiveAccordion';

// Phase D (player redesign): CANVAS-FIRST SHELL SWITCH — the one-line
// rollback. true → the stage flow renders inline in the center column (the
// Decision Canvas) and the dense center content becomes the disclosure
// layer shown when the canvas is dismissed (D1 preference, unchanged
// semantics). false → the pre-Phase-D arrangement: fullscreen takeover
// overlay above the always-rendered dense center.
const CANVAS_FIRST = true;

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

// Pre-compute period label for a given round using the shared utility
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
  hasNewResources = false,
  hasAllocated,
  hasReadBriefing,
  onLogout,
  lastSavedAt,
  tourActive = false,
}) {
  // Sequential gating: determine if round prerequisite is met
  const hasSecondStage = roundNumber === 1 || roundNumber === 2;
  const secondStageDone = roundNumber === 1 ? hasCompletedStakeholderMap
    : roundNumber === 2 ? hasSubmittedMatrix
    : true; // R3-R10: no special prerequisite
  const roundPrerequisiteMet = hasSecondStage ? secondStageDone : true;
  // canAccessStrategy is computed below after shadowBoardCompleted state is declared

  // Logout confirmation (2-click to prevent accidents)
  const [logoutConfirm, setLogoutConfirm] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState('mailbox');
  // Rail tab → player-visibility key. Declared here so the tab bar, the
  // content switch and the fallback effect below all read ONE mapping.
  const RAIL_TAB_VIS = {
    mailbox: 'rail_mailbox',
    decisions: 'decision_history',
    engines: 'rail_engines',
    climate: 'rail_climate',
  };
  // Phase C (F-P2/F-P4): the context rail's tab CONTENT is collapsed by
  // default — the tab strip itself stays visible as badge tabs (unread
  // counts, pending markers), and nothing required to complete a turn lives
  // inside it. Content stays MOUNTED (display:none) so child fetch effects
  // and data flow are byte-identical to the always-open version.
  const [railExpanded, setRailExpanded] = useState(false);
  const [leftPanelTab, setLeftPanelTab] = useState('kpis'); // 'kpis' | 'charts' | 'metrics'
  const [hoveredOption, setHoveredOption] = useState(null); // Phase 4.6: What-If shadow
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false); // #8: Keyboard cheatsheet
  const [filterBU, setFilterBU] = useState('all'); // #6: Inline BU filter

  // ── Progressive Disclosure ──────────────────────────────
  const [viewMode, setViewMode] = useState('glance'); // 'glance' | 'deep-dive'
  const [investigatedBU, setInvestigatedBU] = useState(null); // bu.id
  const isDeepDive = viewMode === 'deep-dive' && investigatedBU;
  // V-C (player v2, V-1): after the strategic decision is made, the full
  // options section folds to a one-line summary ("change" re-expands) so the
  // allocation matrix becomes the single primary work surface. Legacy A/B/C
  // only — pillar mode is a multi-select worksheet, not a one-shot choice.
  const [optionsReopen, setOptionsReopen] = useState(false);
  // Re-fold when a (new) choice is made after "Change".
  useEffect(() => { setOptionsReopen(false); }, [decisionChoice]);

  const BU_ICONS = { pharma: '💊', electronics: '🔌', consumer_goods: '🛒', software: '💻', hospitals: '🏥', clinics: '🩺', specialised_care: '🧬', telehealth: '📱', agriculture: '🌾', fisheries: '🐟', forestry: '🌲', water: '💧', retail_banking: '🏦', investment_banking: '📊', insurance: '🛡️', fintech: '📱' };

  const enterDeepDive = useCallback((buId) => {
    setInvestigatedBU(buId);
    setViewMode('deep-dive');
    setFilterBU(buId);
    try { playDeepDiveEnter(); } catch (e) { /* audio not critical */ }
  }, []);

  const exitDeepDive = useCallback(() => {
    setInvestigatedBU(null);
    setViewMode('glance');
    setFilterBU('all');
    // Reset right panel if viewing engines (hidden in glance mode)
    setRightPanelTab(prev => prev === 'engines' ? 'mailbox' : prev);
    try { playDeepDiveExit(); } catch (e) { /* audio not critical */ }
  }, []);

  // Keyboard: Escape exits deep dive, 1-4 jump to BU
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape' && viewMode === 'deep-dive') {
        exitDeepDive();
      }
      if (e.key >= '1' && e.key <= '9' && !e.ctrlKey && !e.altKey && !e.metaKey) {
        const tag = e.target?.tagName?.toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
        const idx = parseInt(e.key, 10) - 1;
        if (businessUnits && businessUnits[idx]) {
          enterDeepDive(businessUnits[idx].id || businessUnits[idx].bu_id);
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [viewMode, businessUnits, enterDeepDive, exitDeepDive]);

  const investigatedBUData = isDeepDive ? businessUnits?.find(bu => (bu.id || bu.bu_id) === investigatedBU) : null;

  // ── Shadow Board Audit (R5) ─────────────────────────────
  const [showShadowBoardAudit, setShowShadowBoardAudit] = useState(false);
  const [shadowBoardCompleted, setShadowBoardCompleted] = useState(
    () => !!globalState?.active_event_flags?.shadow_board_completed
  );

  // ── Consequence DNA Visualizer (pop-out) ─────────────────
  const [showDNAVisualizer, setShowDNAVisualizer] = useState(false);
  const [showConstellation, setShowConstellation] = useState(false); // Antigravity Enhancement
  const dnaIgnited = shadowBoardCompleted || !!globalState?.active_event_flags?.shadow_board_completed;

  // Trigger shadow board when R5 briefing is dismissed
  useEffect(() => {
    if (roundNumber === 5 && hasReadBriefing && !shadowBoardCompleted && !sim?.gameOver) {
      // Check if already completed from globalState (session resume)
      const alreadyDone = globalState?.active_event_flags?.shadow_board_completed;
      if (alreadyDone) {
        setShadowBoardCompleted(true);
      } else {
        setShowShadowBoardAudit(true);
      }
    }
  }, [roundNumber, hasReadBriefing, shadowBoardCompleted, sim?.gameOver]);

  // Reset shadow board state on round change
  useEffect(() => {
    if (roundNumber !== 5) {
      setShowShadowBoardAudit(false);
      // Don't reset shadowBoardCompleted — it persists across round navigation
    }
  }, [roundNumber]);

  const handleShadowBoardComplete = useCallback((result) => {
    setShowShadowBoardAudit(false);
    setShadowBoardCompleted(true);
    console.log('[ShadowBoard] Audit completed:', result);
  }, []);

  // For strategic decision gating: briefing must be read, second stage (if any) must be done,
  // AND for R5 the Shadow Board Audit must be completed before strategy access
  const r5AuditGate = roundNumber === 5 ? (!!globalState?.active_event_flags?.shadow_board_completed || shadowBoardCompleted) : true;
  const canAccessStrategy = hasReadBriefing && roundPrerequisiteMet && r5AuditGate;

  // Journey pedagogy gate: track when R6/R7/R8 minigames load and are submitted
  const [r6Pending, setR6Pending] = useState(false);
  const [r6Done,    setR6Done]    = useState(false);
  const [r7Pending, setR7Pending] = useState(false);
  const [r7Done,    setR7Done]    = useState(false);
  const [r8Pending, setR8Pending] = useState(false);
  const [r8Done,    setR8Done]    = useState(false);
  // Reset on every round commit so a fresh results overlay starts clean
  useEffect(() => {
    setR6Pending(false); setR6Done(false);
    setR7Pending(false); setR7Done(false);
    setR8Pending(false); setR8Done(false);
  }, [roundNumber]);
  const journeyBlocksAdvance = (r6Pending && !r6Done) || (r7Pending && !r7Done) || (r8Pending && !r8Done);

  // B2: Per-round reflection box — stored locally per round, surfaced in debrief
  const reflectionsRef = useRef({});
  const [reflectionText, setReflectionText] = useState('');

  // ── Peer Performance: auto-fetch when commitResults arrive ──
  const [peerLeaderboard, setPeerLeaderboard] = useState([]);
  const [peerLoading, setPeerLoading] = useState(false);
  // Reveal-schedule: when the facilitator gates rankings, the endpoint returns
  // { locked:true, message } instead of data — surface that instead of a blank.
  const [peerLockMsg, setPeerLockMsg] = useState('');
  useEffect(() => {
    if (!commitResults || !sim?.sessionId || sim.sessionId === 'demo') {
      setPeerLeaderboard([]);
      setPeerLockMsg('');
      return;
    }
    let cancelled = false;
    const fetchPeers = async () => {
      setPeerLoading(true);
      try {
        const API = process.env.NEXT_PUBLIC_API_URL || '';
        const res = await fetch(`${API}/api/simulations/${sim.sessionId}/peer-leaderboard`);
        if (!res.ok) throw new Error(`Peer leaderboard: ${res.status}`);
        const data = await res.json();
        if (cancelled) return;
        if (data.locked) {
          setPeerLeaderboard([]);
          setPeerLockMsg(data.message || `Peer rankings unlock at round ${data.reveal_round ?? ''}.`);
        } else {
          setPeerLockMsg('');
          if (data.leaderboard?.length > 0) setPeerLeaderboard(data.leaderboard);
        }
      } catch { /* non-critical */ }
      if (!cancelled) setPeerLoading(false);
    };
    fetchPeers();
    return () => { cancelled = true; };
  }, [commitResults, sim?.sessionId]);

  // Pedagogical scaffolding toggles — COHORT-EFFECTIVE.
  // BUG-2026-07-20: this fetched /global-settings with no session_id, so it
  // returned PLATFORM defaults and every per-cohort pedagogy toggle
  // (Real-World Case Cards, Round Recap, Debrief Protocol, Strategy Memo…)
  // was ignored for players — the facilitator saw it saved and the card never
  // appeared. Passing the cohort id makes the response cohort-effective; the
  // deps re-fetch when the session resolves, since it is null on first render.
  const [pedToggles, setPedToggles] = useState({});
  const _pedSid = sim?.sessionId || sim?.session_id;
  useEffect(() => {
    const qs = _pedSid ? `?session_id=${encodeURIComponent(_pedSid)}` : '';
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/global-settings${qs}`)
      .then(r => r.ok ? r.json() : {})
      .then(d => setPedToggles(d || {}))
      .catch(() => {});
  }, [_pedSid]);
  const [predictions, setPredictions] = useState([]);
  const [checkpointData, setCheckpointData] = useState(null);
  useEffect(() => {
    if (!logoutConfirm) return;
    const t = setTimeout(() => setLogoutConfirm(false), 3500);
    return () => clearTimeout(t);
  }, [logoutConfirm]);
  const isPillarMode = decisionParadigm === 'multi_toggles' || decisionParadigm === 'brsr_ngrbc';
  const hasDecision = isPillarMode
    ? Object.keys(pillarSelections || {}).length > 0
    : !!decisionChoice;
  // For capital allocation gating: strategic decision must be made
  const canAccessAllocation = canAccessStrategy && hasDecision;
  const treasury = globalState?.corporate_treasury || 0;
  const reputation = globalState?.group_reputation || 50;
  // Initialise EBITDA from BU revenue minus OPEX if not yet committed (avoids $0 display on R1)
  const ebitda = globalState?.historical_ebitda ||
    (businessUnits?.reduce((acc, bu) => acc + (bu.revenue_base || 0) - (bu.opex_base || 0), 0) || 0);
  // Initialise carbon from BU data when tco2e_emissions is not yet set.
  // Clamp to >= 0: negative values indicate stale/corrupt state from a previous session snapshot.
  // Fallback formula mirrors backend: Σ(carbon_intensity × revenue_base / 1_000_000)
  const rawTco2e = globalState?.tco2e_emissions;
  const tco2e = Math.max(
    0,
    (rawTco2e != null && rawTco2e > 0)
      ? rawTco2e
      : (businessUnits?.reduce((acc, bu) => acc + ((bu.carbon_intensity || 0) * (bu.revenue_base || 0)) / 1_000_000, 0) || 0)
  );
  const avgCarbonIntensity = businessUnits?.length
    ? (businessUnits.reduce((acc, bu) => acc + (bu.carbon_intensity || 0), 0) / businessUnits.length)
    : 0;
  const vrio = globalState?.vrio_capabilities || { value: 50, rarity: 50, imitability: 100, organization: 80 };
  
  // Advanced Climate Engine Extracted State
  const greenFund = globalState?.green_transition_fund || 0;
  const costOfCapital = globalState?.cost_of_capital || 0.05;
  const tippingPointActive = globalState?.tipping_point_active || false;
  // V-A+ : pendingProjects derivation removed with the Active Infrastructure
  // Projects panel (owner request) — the data stays in the /dashboard payload.

  // W-A (W5): atmosphere tier — extends the existing health-based mood classes
  // with a subtle full-viewport backdrop. CSS-only, pointer-events none,
  // opacity-capped, killed under prefers-reduced-motion. Derivation only —
  // reads the same state the mood classes already read, writes nothing.
  const atmoTier = tippingPointActive
    ? 'tipping'
    : (reputation < 35 ? 'strain' : null);

  // EX-5: Play tipping point warning sound on activation (false → true transition)
  const prevTippingRef = useRef(false);
  useEffect(() => {
    if (tippingPointActive && !prevTippingRef.current) {
      soundManager.tippingWarning();
    }
    prevTippingRef.current = tippingPointActive;
  }, [tippingPointActive]);

  // PHASE-3: Extract ESG WACC and tipping state for Command Center components
  const esgWacc = events?.esg_adjusted_wacc || commitResults?.events?.esg_adjusted_wacc || null;
  const systemicTipping = events?.systemic_tipping || commitResults?.events?.systemic_tipping || {};
  const foreshadowingSignals = events?.foreshadowing_signals || commitResults?.events?.foreshadowing_signals || [];
  const previousGlobalState = history?.length > 0 ? history[history.length - 1]?.global_state : {};

  // Regulatory Sandbox — active instruments visible to player as "Regulatory Environment"
  const sandboxState = globalState?.regulatory_sandbox || {};
  const activeRegulations = sandboxState?.active_regulations || [];
  const regulatoryComplexity = sandboxState?.regulatory_complexity_index || 0;

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
      // Math-audit correction: historical_ebitda is NOT cumulative — the
      // engine computes it per round as Σ(revenue − opex) over the final BU
      // table (see engine._run_financial_layer + the commit route's
      // reporting-truth resync). We still prefer deriving from BU data
      // (identical definition, robust to old snapshots), but the fallback
      // uses the raw value — the old ÷ round_number divided a per-round
      // figure and understated later rounds.
      const roundBUs = h.business_units || [];
      const perRoundEbitda = roundBUs.length > 0
        ? roundBUs.reduce((acc, bu) => acc + (bu.revenue_base || 0) - (bu.opex_base || 0), 0)
        : Math.max(0, h.global_state?.historical_ebitda || 0);
      return {
        round: h.round_number,
        year: roundToQuarter(h.round_number, BASE_YEAR).year,
        yearLabel: roundToQuarter(h.round_number, BASE_YEAR).shortLabel,
        ebitda: perRoundEbitda,
        tco2e: h.global_state?.tco2e_emissions || 0,
        reputation: h.global_state?.group_reputation || 50,
        treasury: h.global_state?.corporate_treasury || 0,
        synergy: h.global_state?.synergy_multiplier || 1.0,
        // W-B (W2a): rival ghost series — engine already simulates this every round
        competitor_ebitda: h.global_state?.competitor_ebitda || null,
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
        yearLabel: roundToQuarter(roundNumber, BASE_YEAR).shortLabel,
        ebitda, tco2e, reputation, treasury,
        synergy: globalState?.synergy_multiplier || 1.0,
        competitor_ebitda: globalState?.competitor_ebitda || null,
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
          yearLabel: roundToQuarter(nextRound, BASE_YEAR).shortLabel,
          ebitda: commitResults.globalState.historical_ebitda || 0,
          tco2e: commitResults.globalState.tco2e_emissions || 0,
          reputation: commitResults.globalState.group_reputation || 50,
          treasury: commitResults.globalState.corporate_treasury || 0,
          synergy: commitResults.globalState.synergy_multiplier || 1.0,
          competitor_ebitda: commitResults.globalState.competitor_ebitda || null,
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
  // V-A (player v2): rail recap link state — the retrospect accordions render
  // in the results stage by default and here only on demand.
  const [railRecapOpen, setRailRecapOpen] = useState(false);

  // ── Focus Mode: Advanced Metrics Drawer ──
  // Auto-collapsed for rounds 1-4, auto-expanded for rounds 5+
  const [advancedMetricsOpen, setAdvancedMetricsOpen] = useState(roundNumber >= 5);
  useEffect(() => { setAdvancedMetricsOpen(roundNumber >= 5); exitDeepDive(); setOptionsReopen(false); }, [roundNumber]);

  // ── Metacognitive Friction: Pre-Commit Prediction ──
  const [showPredictionModal, setShowPredictionModal] = useState(false);
  const [predictionText, setPredictionText] = useState('');

  // ── Results-level Balance Sheet Modal ──
  const [resultsBsModalOpen, setResultsBsModalOpen] = useState(false);

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

  // #10: Sound — commit success chime
  useEffect(() => {
    if (commitResults) { try { playCommitSuccess(); } catch (e) {} }
  }, [commitResults]);

  // #10: Sound — tipping point warning
  useEffect(() => {
    if (tippingPointActive) { try { playTippingWarning(); } catch (e) {} }
  }, [tippingPointActive]);

  // ── Focus Mode: Stepped Decision Overlays ──
  // Phase A: the stage machine lives in hooks/useRoundStage.js (verbatim
  // extraction). Identical bindings are destructured so every downstream
  // reference in this file is untouched.
  const {
    focusStep, setFocusStep,
    focusDismissed, setFocusDismissed,
    prefersDashboardRef,
    hasGate, focusSteps, getFirstIncompleteStep,
    isFocusActive, isReturningPlayer,
    handleFocusDismiss, handleQuickResume, handleFocusReenter, handleFocusAdvance,
  } = useRoundStage({
    roundNumber,
    hasReadBriefing,
    gameOver: sim?.gameOver,
    tourActive,
    roundPrerequisiteMet,
    hasDecision,
    allocations,
    commitResults,
    selfLearningMode: globalState?.self_learning_mode,
  });

  // Phase B (F-P7): flag the concentration stages on <html> so ambient
  // chrome rendered outside this component (the market ticker in page.js)
  // can dim itself. Attribute-based to avoid new prop drilling through
  // page.js; removed on unmount.
  useEffect(() => {
    // V-D (player v2, V-7): the BU drill-down is a concentration state too —
    // the ticker dims while inspecting, same as during allocation/commit.
    const dim = (isFocusActive && focusStep === 'allocation') || isDeepDive;
    if (dim) document.documentElement.setAttribute('data-allocation-open', '1');
    else document.documentElement.removeAttribute('data-allocation-open');
    return () => document.documentElement.removeAttribute('data-allocation-open');
  }, [isFocusActive, focusStep, isDeepDive]);


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

  // Per-cohort player-panel visibility (fail-open): honour the facilitator's
  // analytics-visibility toggles for this cohort. Missing/loading map → visible.
  // `player` (the raw map) is destructured alongside the predicate because the
  // hook returns FRESH function identities every render — an effect depending
  // on isPlayerVisible would loop. The map is state, so it is stable.
  const { isPlayerVisible, player: playerVisibility } = useAnalyticsVisibility(sim?.sessionId || sim?.session_id);

  // Keep the OPEN rail tab valid. Hiding a tab in cohort settings must not
  // leave its content rendered underneath a tab bar that no longer offers it —
  // fall back to the first tab the cohort still permits.
  useEffect(() => {
    const visible = Object.keys(RAIL_TAB_VIS).filter(
      id => isPanelVisible(playerVisibility, RAIL_TAB_VIS[id])
    );
    if (visible.length && !visible.includes(rightPanelTab)) {
      setRightPanelTab(visible[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playerVisibility, rightPanelTab]);

  // LOW-tier polish: cohort accessibility defaults (applied at document level)
  // + white-label branding for the header. Fail-open — unconfigured cohorts
  // render exactly as before.
  const { branding } = useCohortPolish(sim?.sessionId || sim?.session_id);

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

  // W-C (W3): year-end Annual Report overlay — offered in the results step
  // after even rounds. Optional (never gates advance); resets when the
  // results snapshot clears on round advance.
  const [showAnnualReport, setShowAnnualReport] = useState(false);
  useEffect(() => { if (!commitResults) setShowAnnualReport(false); }, [commitResults]);

  // Market events from round_config + engine events
  const marketEvents = useMemo(() => {
    const items = [];
    // V-B (player v2, V-4): the round directive is no longer injected as feed
    // item 1 — it already renders in the round-narrative card and the header
    // chip (and arrives as mail when the server sends it). One fact, one
    // home; the feed keeps real market events.
    
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
      items.push({ type: 'info', text: '📊 Markets stable ahead of next period earnings reports.' });
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

    // ── REAL-WORLD SCENARIOS ──
    if (events?.cfo_austerity_active || flags?.cfo_austerity_active) {
      items.push({ type: 'alert', text: events?.cfo_austerity_message || flags?.cfo_austerity_message || `🛑 CFO AUSTERITY OVERRIDE: Heavy ESG investments drained free cash flow. The CFO has frozen all sustainability budgets for the next round.` });
    }
    if (events?.supplier_defection?.active) {
      items.push({ type: 'alert', text: events.supplier_defection.message });
    }
    if (events?.green_premium_squeeze?.active) {
      items.push({ type: 'alert', text: events.green_premium_squeeze.message });
    }
    if (events?.regulatory_ratchet?.active) {
      items.push({ type: 'alert', text: events.regulatory_ratchet.message });
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
        // No auto-dismiss — stays until player explicitly acknowledges
      }
    }
  }, [globalState, events]);

  // Dismiss callback for black swan / crisis alerts — player must manually acknowledge
  const dismissActiveAlert = useCallback(() => {
    if (blackSwanAlert) {
      const dismissedKey = `bs_dismissed_${blackSwanAlert.title}`;
      sessionStorage.setItem(dismissedKey, '1');
      setBlackSwanAlert(null);
    }
  }, [blackSwanAlert]);

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
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;

      // #8: Keyboard cheatsheet toggle
      if (e.key === '?' || (e.key === '/' && e.shiftKey)) {
        e.preventDefault();
        setShowKeyboardHelp(prev => !prev);
        return;
      }

      // Only handle decision keys when no modal is open and decisions are accessible
      if (commitResults || !canAccessStrategy) return;

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
      {/* ═══ W-A (W5): Atmosphere layer — ambient, non-blocking, capped ═══ */}
      {atmoTier && (
        <div
          aria-hidden="true"
          data-atmo={atmoTier}
          style={{
            position: 'fixed', inset: 0, zIndex: 1, pointerEvents: 'none',
            opacity: atmoTier === 'tipping' ? 0.12 : 0.08,
            background: atmoTier === 'tipping'
              ? 'radial-gradient(ellipse 80% 60% at 70% 100%, rgba(239, 68, 68, 0.55) 0%, transparent 60%), radial-gradient(ellipse 60% 50% at 20% 90%, rgba(245, 158, 11, 0.45) 0%, transparent 55%)'
              : 'radial-gradient(ellipse 90% 70% at 50% 110%, rgba(59, 130, 246, 0.4) 0%, transparent 65%)',
            animation: 'atmoDrift 26s ease-in-out infinite alternate',
          }}
        />
      )}
      <style>{`
        @keyframes atmoDrift {
          0% { transform: translate3d(0, 0, 0) scale(1); }
          100% { transform: translate3d(-2.5%, 1.5%, 0) scale(1.06); }
        }
        @keyframes stampIn {
          0% { opacity: 0; transform: rotate(-14deg) scale(1.9); }
          100% { opacity: 1; transform: rotate(-4deg) scale(1); }
        }
        @media (prefers-reduced-motion: reduce) {
          [data-atmo] { animation: none !important; opacity: 0.05 !important; }
          .stamp-ceremony { animation: none !important; }
        }
      `}</style>
      {/* ═══ W-C (W3): Year-End Integrated Annual Report — optional overlay ═══ */}
      {showAnnualReport && focusStep === 'results' && commitResults && isPlayerVisible('annual_report') && (
        <AnnualReport
          open
          onClose={() => setShowAnnualReport(false)}
          roundNumber={roundNumber}
          commitResults={commitResults}
          history={history}
          businessUnits={businessUnits}
          teamName={sim?.teamName || sim?.team_name || ''}
        />
      )}

      {/* ═══ SHADOW BOARD AUDIT — R5 Mandatory Middleware ═══ */}
      {showShadowBoardAudit && (
        <ShadowBoardAudit
          sessionId={sim?.sessionId}
          onComplete={handleShadowBoardComplete}
          globalState={globalState}
        />
      )}

      {/* ═══ CRISIS INTERSTITIAL — Full-screen overlay for Black Swan / critical events ═══ */}
      {activeAlert && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 11000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: activeAlert.isBlackSwan
            ? 'radial-gradient(ellipse at 40% 30%, rgba(127, 29, 29, 0.96) 0%, rgba(15, 10, 10, 0.98) 70%)'
            : 'radial-gradient(ellipse at 40% 30%, rgba(120, 53, 15, 0.96) 0%, rgba(20, 12, 5, 0.98) 70%)',
          fontFamily: "var(--font-sans, 'DM Sans', Inter, system-ui, sans-serif)",
          animation: 'flashIn 0.4s ease-out',
          padding: '2rem',
        }}>
          <div style={{
            width: '100%', maxWidth: 600,
            animation: 'crisisSlideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.3s both',
          }}>
            {/* Header */}
            <div style={{ textAlign: 'center', marginBottom: '1.4rem' }}>
              <span style={{
                fontSize: '3rem', display: 'block', marginBottom: '0.5rem',
                animation: 'crisisIconPulse 1.5s ease-in-out infinite',
              }}>
                {activeAlert.icon || '⚠️'}
              </span>
              <div style={{
                display: 'inline-block', fontSize: '0.68rem', fontWeight: 800,
                letterSpacing: '0.16em', textTransform: 'uppercase',
                borderRadius: 100, padding: '0.3rem 1rem', marginBottom: '0.6rem',
                color: activeAlert.isBlackSwan ? '#fca5a5' : '#fcd34d',
                background: activeAlert.isBlackSwan ? 'rgba(252, 165, 165, 0.12)' : 'rgba(252, 211, 77, 0.12)',
                border: activeAlert.isBlackSwan ? '1px solid rgba(252, 165, 165, 0.25)' : '1px solid rgba(252, 211, 77, 0.25)',
              }}>
                {activeAlert.isBlackSwan ? '🦢 BLACK SWAN EVENT — IMMEDIATE ATTENTION REQUIRED' : '⚠️ CRITICAL ALERT — ACTION REQUIRED'}
              </div>
              <h1 style={{
                fontSize: '1.5rem', fontWeight: 800, margin: 0,
                letterSpacing: '-0.02em',
                color: activeAlert.isBlackSwan ? '#fca5a5' : '#fcd34d',
              }}>
                {activeAlert.title}
              </h1>
            </div>

            {/* Body */}
            <div style={{
              borderRadius: 12, padding: '1.5rem 1.8rem', marginBottom: '1.2rem',
              boxShadow: '0 4px 24px rgba(0, 0, 0, 0.4)',
              background: activeAlert.isBlackSwan ? 'rgba(127, 29, 29, 0.5)' : 'rgba(120, 53, 15, 0.5)',
              border: activeAlert.isBlackSwan ? '1px solid rgba(252, 165, 165, 0.15)' : '1px solid rgba(252, 211, 77, 0.15)',
            }}>
              <p style={{
                fontSize: '0.88rem', lineHeight: 1.75,
                color: '#e2e8f0', margin: 0, whiteSpace: 'pre-line',
              }}>
                {activeAlert.body}
              </p>
            </div>

            {/* Dismiss */}
            <div style={{ textAlign: 'center' }}>
              <button
                onClick={dismissActiveAlert}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
                  border: 'none', borderRadius: 10,
                  padding: '0.8rem 2.2rem', fontSize: '0.8rem', fontWeight: 700,
                  cursor: 'pointer',
                  background: activeAlert.isBlackSwan
                    ? 'linear-gradient(135deg, #ef4444, #dc2626)'
                    : 'linear-gradient(135deg, #f59e0b, #d97706)',
                  color: '#fff',
                  boxShadow: activeAlert.isBlackSwan
                    ? '0 4px 16px rgba(239, 68, 68, 0.4)'
                    : '0 4px 16px rgba(245, 158, 11, 0.4)',
                  transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                  fontFamily: "var(--font-sans, 'DM Sans', Inter, sans-serif)",
                  letterSpacing: '0.04em',
                }}
                onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-1px) scale(1.02)'; }}
                onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0) scale(1)'; }}
              >
                Acknowledged — Return to Cockpit →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ GLOBAL HEADER ═══ */}
      <header className={styles.header}>
        <div className={styles.headerLogo}>
          <span className={styles.logoMark}>M</span>
          MURESSONS
          {branding?.institution && (
            <span style={{ marginLeft: 16, fontSize: '0.75rem', color: 'var(--mur-brand-primary, #94a3b8)', fontWeight: 700, letterSpacing: '0.05em', borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: 16, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              {branding.logo_url && (
                <img src={branding.logo_url} alt={`${branding.institution} logo`} style={{ height: 20, width: 'auto', borderRadius: 3 }} />
              )}
              {branding.institution.toUpperCase()}
            </span>
          )}
          {sim?.username && (
             <span style={{ marginLeft: 16, fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, letterSpacing: '0.05em', borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: 16 }}>
               WELCOME {sim.username.toUpperCase()}
             </span>
          )}
        </div>

        <div className={styles.headerCenter}>
          <div className={styles.liveStatusBadge}>
            <span className={styles.liveStatusDot} />
            <span style={{ color: '#10b981', fontWeight: 700 }}>LIVE</span>
            <span className={styles.liveStatusSep}>·</span>
            <span style={{ color: '#e2e8f0', fontWeight: 700 }}>Round {roundNumber}</span>
            <span className={styles.liveStatusSep}>·</span>
            <span>{getRoundLabel(roundNumber)}</span>
            <span className={styles.liveStatusSep}>·</span>
            <span>{activeRoundTitles[roundNumber] || ''}</span>
            {tippingPointActive && (
              <>
                <span className={styles.liveStatusSep}>·</span>
                <motion.span
                  animate={{ opacity: [1, 0.5, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  style={{ color: '#fca5a5', fontWeight: 700 }}
                >
                  ⚠️ TIPPING POINT
                </motion.span>
              </>
            )}
            {activeRegulations.length > 0 && (
              <>
                <span className={styles.liveStatusSep}>·</span>
                <span
                  title={`${activeRegulations.length} active regulation(s): ${activeRegulations.map(r => r.name).join(', ')}`}
                  style={{ color: '#a5b4fc', cursor: 'help' }}
                >
                  ⚖️ REG({activeRegulations.length})
                </span>
              </>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
            <CountdownTimer sessionId={sim?.sessionId} roundNumber={roundNumber} />
            {/* WOW-11: Enhanced timer with competitive commit counter */}
            <DecisionPressureTimer
              sessionId={sim?.sessionId}
              roundNumber={roundNumber}
              isCommitted={!!commitResults}
              globalState={globalState}
            />
            <span style={{
              padding: '2px 10px', borderRadius: 12,
              background: decisionParadigm === 'advanced_climate' ? 'rgba(16,185,129,0.18)' : 'rgba(99,102,241,0.12)',
              border: decisionParadigm === 'advanced_climate' ? '1px solid rgba(16,185,129,0.35)' : '1px solid rgba(99,102,241,0.25)',
              fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase',
              letterSpacing: '0.04em',
              color: decisionParadigm === 'advanced_climate' ? '#6ee7b7' : '#818cf8',
              whiteSpace: 'nowrap',
            }}>
              {{
                'legacy_abc': 'Narrative',
                'multi_toggles': 'Pillars',
                'advanced_climate': 'Climate',
                'healthcare': 'Healthcare',
                'un_sdg': 'UN SDG',
                'brsr_ngrbc': 'BRSR NGRBC'
              }[decisionParadigm] || 'Active'}
            </span>
            {lastSavedAt && (
               <span style={{ fontSize: '0.68rem', color: '#10b981', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 3 }}>
                 ✓ {lastSavedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
               </span>
            )}
          </div>
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
              <span className={styles.roundContextTier} title={{
                foundation: 'Rounds 1-3: Low-risk decisions. Build your data literacy and establish baseline performance.',
                crisis: 'Rounds 4-6: Systemic shocks test your resilience. Past decisions now have consequences.',
                integration: 'Rounds 7-9: Cross-BU synergies become critical. Whole-system thinking required.',
                finale: 'Round 10: The Board evaluates your 10-round legacy. Final strategic recommendation.',
              }[roundTier]}>
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

          {/* ── Left Panel Tab Bar ── */}
          <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--ck-border, rgba(148,163,184,0.08))', background: 'var(--ck-surface-1, #0e1222)', flexShrink: 0 }}>
            {[
              { id: 'kpis', label: '📊 KPIs' },
              { id: 'charts', label: '📈 Charts' },
              { id: 'metrics', label: '⚙️ Metrics' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setLeftPanelTab(tab.id)}
                style={{
                  flex: 1, padding: '7px 6px', border: 'none', cursor: 'pointer',
                  background: leftPanelTab === tab.id ? 'rgba(94, 234, 212, 0.08)' : 'transparent',
                  color: leftPanelTab === tab.id ? 'var(--ck-accent, #5eead4)' : 'var(--ck-text-3, #64748b)',
                  fontSize: 'var(--ck-fs-xs, 0.65rem)', fontWeight: 600, fontFamily: 'inherit',
                  letterSpacing: '0.04em', textTransform: 'uppercase',
                  borderBottom: leftPanelTab === tab.id ? '2px solid var(--ck-accent, #5eead4)' : '2px solid transparent',
                  transition: 'background 0.15s ease, color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease, transform 0.15s ease',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* ── TAB: KPIs (Resources + Advanced Metrics) ── */}
          {leftPanelTab === 'kpis' && (
          <div style={{ flex: 1, overflowY: 'auto' }}>
          <div style={{ background: 'var(--ck-surface-0, #0b0f1a)', borderBottom: '1px solid var(--ck-border, rgba(148,163,184,0.08))', paddingTop: 10, paddingBottom: 10 }}>
          <div className={styles.resourcesPanel} aria-live="polite" aria-label="Key Performance Indicators">
            <div className={`${styles.resourceCard} ${shadowDeltas ? styles.resourceCardShadow : ''}`}>
              <div className={styles.resourceLabel}>💰 Treasury</div>
              <div className={styles.resourceValue}>{fmtCurrency(treasury)}</div>
              {(() => { const prev = previousGlobalState?.corporate_treasury; const d = prev != null ? treasury - prev : 0; return d !== 0 ? (
                <div style={{ fontSize: '0.68rem', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: d < 0 ? '#f87171' : '#4ade80', marginTop: 1 }}>{d > 0 ? '▲' : '▼'} {d > 0 ? '+' : ''}{fmtCurrency(d)}</div>
              ) : null; })()}
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
                    <div style={{ fontSize: '0.68rem', color: '#6ee7b7', marginTop: 2, lineHeight: 1.3 }}>Funded by carbon fee</div>
                  )}
                  {greenFund > 0 && decisionParadigm === 'advanced_climate' && (
                    <div style={{ fontSize: '0.68rem', color: '#6ee7b7', marginTop: 2, lineHeight: 1.3 }}>+{fmtCurrency(carbonFeePerRound)}/round est.</div>
                  )}
                </div>
              );
            })()}
            <div className={`${styles.resourceCard} ${shadowDeltas ? styles.resourceCardShadow : ''}`}>
              <div className={styles.resourceLabel}>🌍 Reputation</div>
              <div className={styles.resourceValue}>{reputation.toFixed(0)}<span style={{ fontSize: '0.68rem', color: '#475569', marginLeft: 2 }}>/100</span></div>
              {(() => { const prev = previousGlobalState?.group_reputation; const d = prev != null ? reputation - prev : 0; return d !== 0 ? (
                <div style={{ fontSize: '0.68rem', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: d < 0 ? '#f87171' : '#4ade80', marginTop: 1 }}>{d > 0 ? '▲' : '▼'} {d > 0 ? '+' : ''}{d.toFixed(1)}</div>
              ) : null; })()}
              {shadowDeltas?.reputation !== 0 && shadowDeltas?.reputation && (
                <div style={{ fontSize: '0.6rem', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: shadowDeltas.reputation < 0 ? '#f87171' : '#4ade80', marginTop: 2 }}>
                  → {(reputation + shadowDeltas.reputation).toFixed(0)} ({shadowDeltas.reputation > 0 ? '+' : ''}{shadowDeltas.reputation})
                </div>
              )}
            </div>
            {!isHealthcare && (
              <div className={styles.resourceCard}>
                <div className={styles.resourceLabel}>🏭 Carbon</div>
                <div className={styles.resourceValue}>{tco2e.toLocaleString()}<span style={{ fontSize: '0.68rem', color: '#475569', marginLeft: 2 }}>t</span></div>
                {(() => { const prev = previousGlobalState?.tco2e_emissions; const d = prev != null ? tco2e - prev : 0; return d !== 0 ? (
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: d < 0 ? '#4ade80' : '#f87171', marginTop: 1 }}>{d < 0 ? '▼' : '▲'} {d > 0 ? '+' : ''}{d.toFixed(0)}t</div>
                ) : null; })()}
              </div>
            )}
            <div className={styles.resourceCard}>
              <div className={styles.resourceLabel}>📈 EBITDA</div>
              <div className={styles.resourceValue}>{fmtCurrency(ebitda)}</div>
              {(() => { const prevBUs = previousGlobalState?.business_units || history?.[history?.length-1]?.business_units; const prevEbitda = prevBUs?.reduce((a,b) => a + (b.revenue_base||0) - (b.opex_base||0), 0); const d = prevEbitda != null ? ebitda - prevEbitda : 0; return Math.abs(d) > 0.01 ? (
                <div style={{ fontSize: '0.68rem', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: d < 0 ? '#f87171' : '#4ade80', marginTop: 1 }}>{d > 0 ? '▲' : '▼'} {d > 0 ? '+' : ''}{fmtCurrency(d)}</div>
              ) : null; })()}
            </div>
            {isHealthcare && (
              <>
                <div className={styles.resourceCard}>
                  <div className={styles.resourceLabel}>🩺 Avg Burnout</div>
                  <div className={styles.resourceValue} style={{ color: systemBurnout > 75 ? '#ef4444' : systemBurnout > 50 ? '#f59e0b' : '#10b981' }}>
                    {systemBurnout.toFixed(1)}<span style={{ fontSize: '0.68rem', color: '#475569', marginLeft: 2 }}>/100</span>
                  </div>
                </div>
                <div className={styles.resourceCard}>
                  <div className={styles.resourceLabel}>🛏️ Bed Util.</div>
                  <div className={styles.resourceValue} style={{ color: totalBedCapacity > 85 ? '#ef4444' : totalBedCapacity > 70 ? '#f59e0b' : '#10b981' }}>
                    {totalBedCapacity.toFixed(1)}<span style={{ fontSize: '0.68rem', color: '#475569', marginLeft: 2 }}>%</span>
                  </div>
                </div>
              </>
            )}
            {isSDG && (
              <>
                <div className={styles.resourceCard}>
                  <div className={styles.resourceLabel}>🏛️ Political Capital</div>
                  <div className={styles.resourceValue} style={{ color: politicalCapital > 50 ? '#10b981' : politicalCapital > 30 ? '#f59e0b' : '#ef4444' }}>
                    {politicalCapital.toFixed(0)}<span style={{ fontSize: '0.68rem', color: '#475569', marginLeft: 2 }}>/100</span>
                  </div>
                </div>
                <div className={styles.resourceCard}>
                  <div className={styles.resourceLabel}>🤝 Community Trust</div>
                  <div className={styles.resourceValue} style={{ color: communityTrust > 50 ? '#10b981' : communityTrust > 30 ? '#f59e0b' : '#ef4444' }}>
                    {communityTrust.toFixed(0)}<span style={{ fontSize: '0.68rem', color: '#475569', marginLeft: 2 }}>/100</span>
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
            {/* Regulatory Sandbox KPI Card — visible when facilitator has activated instruments */}
            {activeRegulations.length > 0 && (
              <div
                className={styles.resourceCard}
                title={`Active regulations (${activeRegulations.length}):\n${activeRegulations.map(r => `• ${r.name}`).join('\n')}\n\nComplexity: ${regulatoryComplexity.toFixed(0)}/100`}
                style={{ cursor: 'help' }}
              >
                <div className={styles.resourceLabel}>⚖️ Reg. Active</div>
                <div className={styles.resourceValue} style={{ color: '#a5b4fc' }}>
                  {activeRegulations.length}
                  <span style={{ fontSize: '0.68rem', color: '#475569', marginLeft: 2 }}>instr.</span>
                </div>
                <div style={{ fontSize: '0.68rem', color: regulatoryComplexity > 60 ? '#fbbf24' : '#6366f1', marginTop: 2, lineHeight: 1.3 }}>
                  Complexity {regulatoryComplexity.toFixed(0)}/100
                </div>
              </div>
            )}
          </div>
          </div>
          <BenchmarksPanel sessionId={sim?.sessionId || sim?.session_id} roundNumber={roundNumber} />
          </div>
          )}

          {/* ── TAB: Charts (KPI Dashboard + Benchmarks) ── */}
          {leftPanelTab === 'charts' && isPlayerVisible('kpi_dashboard') && (
          <div style={{ flex: 1, overflowY: 'auto', paddingBottom: 10 }}>
            <KPIDashboard
            showStockPerformance={isPlayerVisible('stock_performance')}
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
          )}

          {/* ── TAB: Metrics (Advanced Metrics — previously collapsible drawer) ── */}
          {leftPanelTab === 'metrics' && (
          <div style={{ flex: 1, overflowY: 'auto', padding: '10px 12px' }}>
            {/* WOW-7: Living Planet ESG State Globe */}
            <LivingPlanet globalState={globalState} businessUnits={businessUnits} compact />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {/* #3: BU Health Leaderboard — Deep Dive only */}
              {isDeepDive && businessUnits?.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 4 }}>
                  <div style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#64748b', marginBottom: 2 }}>
                    📊 BU Health Rankings
                  </div>
                  {[...businessUnits]
                    .sort((a, b) => ((b.revenue_base || 0) - (b.opex_base || 0)) - ((a.revenue_base || 0) - (a.opex_base || 0)))
                    .map((bu, idx) => {
                      const margin = bu.revenue_base > 0 ? ((bu.revenue_base - bu.opex_base) / bu.revenue_base * 100) : 0;
                      const slo = bu.social_license_to_operate || 0;
                      const govRisk = bu.governance_risk || 0;
                      const buIcons = { pharma: '💊', electronics: '🔌', consumer_goods: '🛒', software: '💻', hospitals: '🏥', clinics: '🏥', specialised_care: '🧬', telehealth: '📱', agriculture: '🌾', fisheries: '🐟', forestry: '🌲', water: '💧', retail_banking: '🏦', investment_banking: '📊', insurance: '🛡️', fintech: '📱' };
                      const icon = buIcons[bu.id] || '🏢';
                      return (
                        <div key={bu.id || bu.bu_id || `bu-health-${idx}`} className={styles.buHealthCard}>
                          <div className={styles.buHealthIcon}>{icon}</div>
                          <div className={styles.buHealthInfo}>
                            <div className={styles.buHealthName}>{(bu.name || bu.id).replace(/_/g, ' ')}</div>
                            <div className={styles.buHealthBadges}>
                              <span className={styles.buHealthBadge} style={{ background: margin >= 25 ? 'rgba(16,185,129,0.15)' : margin >= 15 ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)', color: margin >= 25 ? '#6ee7b7' : margin >= 15 ? '#fcd34d' : '#fca5a5' }}>
                                {margin.toFixed(0)}% margin
                              </span>
                              <span className={styles.buHealthBadge} style={{ background: 'rgba(99,102,241,0.12)', color: '#a5b4fc' }}>
                                SLO {slo}
                              </span>
                              {govRisk > 10 && (
                                <span className={styles.buHealthBadge} style={{ background: 'rgba(239,68,68,0.12)', color: '#fca5a5' }}>
                                  ⚠ Gov {govRisk}%
                                </span>
                              )}
                            </div>
                          </div>
                          <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.72rem', fontWeight: 800, color: '#e2e8f0', flexShrink: 0 }}>
                            {fmtCurrency(bu.revenue_base || 0)}
                          </div>
                        </div>
                      );
                    })}
                </div>
              )}
              {/* System Metrics */}
              <div style={{ display: 'flex', gap: 6 }}>
                <div style={{ flex: 1, padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: '1px solid rgba(94, 234, 212, 0.1)' }}>
                  <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, marginBottom: 4 }}>Synergy</div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: (globalState?.synergy_multiplier || 1) < 1 ? '#f87171' : '#5eead4', fontFamily: 'JetBrains Mono, monospace' }}>
                    {(globalState?.synergy_multiplier || 1).toFixed(2)}×
                  </div>
                </div>
                <div style={{ flex: 1, padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: '1px solid #334155' }}>
                  <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, marginBottom: 4 }}>Inflation</div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: (globalState?.inflation_index || 0) > 0.03 ? '#f59e0b' : '#e2e8f0', fontFamily: 'JetBrains Mono, monospace' }}>
                    {fmtInflation(globalState?.inflation_index)}
                  </div>
                </div>
              </div>
              <div style={{ padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: '1px solid #334155' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600 }}>Cost of Capital</span>
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#e2e8f0', fontFamily: 'JetBrains Mono, monospace' }}>
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
                      <div style={{ flex: 1, padding: '6px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: '1px solid #334155' }}>
                        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, marginBottom: 2 }}>Monetary Policy</div>
                        <div style={{ fontSize: '0.73rem', fontWeight: 700, color: '#e2e8f0', fontFamily: 'JetBrains Mono, monospace' }}>
                          {{ easing: '🕊️ Easing', neutral: '⚖️ Neutral', tightening: '🦅 Hawk', crisis: '🔥 Crisis' }[macroEvt.regime] || macroEvt.regime}
                        </div>
                      </div>
                    )}
                    {fxEvt && (
                      <div style={{ flex: 1, padding: '6px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: '1px solid #334155' }}>
                        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, marginBottom: 2 }}>FX Index</div>
                        <div style={{ fontSize: '0.73rem', fontWeight: 700, color: '#e2e8f0', fontFamily: 'JetBrains Mono, monospace' }}>
                          {fxEvt.fx_direction === 'strengthening' ? '↑' : '↓'} {(Math.abs(fxEvt.fx_index) * 100).toFixed(1)}%
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}
              {/* CE-03: Avg Carbon Intensity */}
              {decisionParadigm === 'advanced_climate' && !isHealthcare && (
                <div style={{ padding: '8px 10px', background: 'rgba(14, 20, 36, 0.4)', borderRadius: 8, border: '1px solid #334155' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600 }}>Avg Carbon Intensity</span>
                    <span style={{ fontSize: '0.73rem', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: '#e2e8f0' }}>
                      {avgCarbonIntensity.toFixed(1)}
                    </span>
                  </div>
                  <div style={{ height: 3, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${Math.min(100, (avgCarbonIntensity / 120) * 100)}%`, background: '#94a3b8', borderRadius: 2, transition: 'width 0.5s' }} />
                  </div>
                </div>
              )}
              <SystemEngineMetrics globalState={globalState} pedToggles={pedToggles} isHealthcare={isHealthcare} />
            </div>
          </div>
          )}

          {/* Action Toolbar placed at the bottom of the left panel */}
          {actionToolbar && (
            <div id="tour-player-guides-target" style={{
              borderTop: '1px solid rgba(0, 229, 195, 0.2)',
              background: '#0a0e1a',
              padding: '10px 6px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              width: '100%',
              gap: 6,
              fontFamily: 'Inter, sans-serif',
              marginTop: 'auto',
              flexShrink: 0,
            }}>
              {/* Decision Paradigm Tab */}
              <div style={{
                padding: '4px 12px', borderRadius: 14, 
                background: 'rgba(99, 102, 241, 0.15)', border: '1px solid rgba(99, 102, 241, 0.3)',
                display: 'flex', alignItems: 'center', gap: 6,
                marginBottom: 6, width: '100%', justifyContent: 'center'
              }}>
                <span style={{ fontSize: '0.85rem' }}>⚙️</span>
                <span style={{ fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#818cf8', whiteSpace: 'nowrap' }}>
                  {{
                    'legacy_abc': 'Narrative Crises',
                    'multi_toggles': 'Strategic Pillars',
                    'advanced_climate': 'Advanced Climate',
                    'healthcare': 'Healthcare Edition',
                    'un_sdg': 'UN SDG Edition',
                    'brsr_ngrbc': 'BRSR NGRBC Edition'
                  }[decisionParadigm] || 'Simulation Active'}
                </span>
              </div>

              {/* Focus Mode button */}
              {!sim?.gameOver && (
                <div style={{ width: '100%', padding: '0 6px 6px', flexShrink: 0 }}>
                  <button
                    onClick={() => {
                      setLeftPanelTab('focus');
                      handleFocusReenter();
                    }}
                    style={{
                      width: '100%', padding: '8px 14px', border: 'none', cursor: 'pointer',
                      borderRadius: 8,
                      background: isFocusActive
                        ? 'linear-gradient(135deg, rgba(251, 191, 36, 0.18), rgba(245, 158, 11, 0.10))'
                        : focusDismissed
                          ? 'rgba(251, 191, 36, 0.06)'
                          : 'rgba(255, 255, 255, 0.04)',
                      border: isFocusActive
                        ? '1px solid rgba(251, 191, 36, 0.35)'
                        : focusDismissed
                          ? '1px solid rgba(245, 158, 11, 0.2)'
                          : '1px solid rgba(255, 255, 255, 0.08)',
                      color: isFocusActive ? '#fbbf24' : focusDismissed ? '#f59e0b' : '#94a3b8',
                      fontSize: '0.72rem', fontWeight: 700, fontFamily: 'inherit',
                      letterSpacing: '0.04em', textTransform: 'uppercase',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                      transition: 'background 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, transform 0.15s ease',
                      position: 'relative',
                    }}
                    onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.02)'; e.currentTarget.style.background = 'rgba(251, 191, 36, 0.12)'; }}
                    onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.background = isFocusActive ? 'linear-gradient(135deg, rgba(251, 191, 36, 0.18), rgba(245, 158, 11, 0.10))' : focusDismissed ? 'rgba(251, 191, 36, 0.06)' : 'rgba(255, 255, 255, 0.04)'; }}
                  >
                    <span style={{ fontSize: '0.9rem' }}>🎯</span>
                    <span>Focus Mode</span>
                    {focusDismissed && !isFocusActive && (
                      <span style={{
                        width: 6, height: 6, borderRadius: '50%',
                        background: '#f59e0b',
                        display: 'inline-block',
                        boxShadow: '0 0 6px rgba(245, 158, 11, 0.5)',
                      }} />
                    )}
                    {isFocusActive && (
                      <span style={{ fontSize: '0.6rem', opacity: 0.7 }}>ACTIVE</span>
                    )}
                  </button>
                </div>
              )}

              {/* Action Toolbar buttons */}
              {actionToolbar}
            </div>
          )}
        </aside>

        {/* ── CENTER: Briefing + Decisions ─── */}
        <main className={styles.centerConsole}>
          
          {/* V-C (V-6): the Round Checklist mount moved to the BOTTOM of the
              center console (docked below the scroll area) — see the end of
              <main>. The component no longer position:fixes itself out of
              its mount, so where it mounts is where it lives. */}

          {/* ═══ DECISION CANVAS (Phase D) ═══
              The stage flow (gate → strategy → allocation → commit → results)
              renders INLINE here as the primary surface when CANVAS_FIRST is
              on; with CANVAS_FIRST off it is the pre-Phase-D fullscreen
              takeover, unchanged. Children are the former focus-overlay steps,
              moved verbatim — same state, same handlers, same gating. */}
          <FocusOverlay
            variant={CANVAS_FIRST ? 'inline' : 'takeover'}
            isOpen={isFocusActive}
            step={focusStep}
            steps={focusSteps}
            onClose={handleFocusDismiss}
            onBack={handleFocusAdvance}
            onReenter={handleFocusReenter}
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
            {/* KPI-belt slot: post-completion Turnaround phase (renders only while active) */}
            <TurnaroundPhaseChip active={globalState?.turnaround_mode}
              phase={globalState?.active_event_flags?.turnaround_phase}
              round={globalState?.turnaround_round} maxRounds={4} />

            <div className={focusStyles.sectionTitle}>
              <span>{isPillarMode ? '🎛️' : '📋'}</span>
              {isPillarMode ? 'Strategic Pillars' : 'Strategic Options'}
              {projectedCost !== 0 && (
                <span style={{ marginLeft: 'auto', color: projectedCost > 0 ? '#f87171' : '#4ade80', fontWeight: 800, fontSize: '0.72rem' }}>
                  Impact: {fmtCurrency(projectedCost)}
                </span>
              )}
            </div>

            {isPillarMode ? (
              <div className={focusStyles.focusPillarTiles}>
                {pillarConfig?.areas && Object.entries(pillarConfig.areas).map(([areaKey, area]) => {
                  const selectedOpt = pillarSelections?.[areaKey];
                  return (
                    <div key={areaKey} className={`${styles.pillarTile} ${selectedOpt ? styles.pillarTileActive : ''}`}>
                      <div className={styles.pillarIcon}>{AREA_ICONS[areaKey] || '📌'}</div>
                      <div className={styles.pillarLabel}>{area.label}</div>
                      <PillarSelectDropdown
                        options={area.options || {}}
                        value={selectedOpt || null}
                        onChange={(optKey) => handlePillarSelect(areaKey, optKey)}
                        fmtCurrency={fmtCurrency}
                        detailedDescs={DETAILED_DESCRIPTIONS.pillars?.[roundNumber]?.[areaKey] || {}}
                      />
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
                          <span style={{ fontSize: '0.72rem', fontWeight: 800, color: costVal < 0 ? '#ef4444' : '#16a34a' }}>{fmtCurrency(costVal)}</span>
                        </div>
                      ) : (
                        <div style={{ marginTop: 6, fontSize: '0.6rem', fontWeight: 700, color: '#f59e0b' }}>⚠️ $0 CapEx — deferred risk</div>
                      )}
                      {isActive && opt.impacts && (
                        <div style={{ marginTop: 6, padding: '4px 6px', background: 'rgba(0,229,195,0.04)', borderRadius: 4, fontSize: '0.68rem', lineHeight: 1.6, border: '1px solid rgba(0,229,195,0.08)' }}>
                          {opt.impacts.treasury && (
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: opt.impacts.treasury < 0 ? '#f87171' : '#4ade80' }}>
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
            {!isPillarMode && Object.keys(options).length > 0 && (
              <div style={{ marginTop: 16, padding: '12px 14px', background: isDark ? 'rgba(0,0,0,0.2)' : '#f8fafc', borderRadius: 10, border: isDark ? '1px solid rgba(0,229,195,0.06)' : '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase', color: isDark ? '#94a3b8' : '#475569', marginBottom: 8 }}>Comparison Matrix</div>
                <table style={{ width: '100%', fontSize: '0.7rem', borderCollapse: 'collapse', color: isDark ? '#d1d9e6' : '#1e293b' }}>
                  <thead>
                    <tr style={{ borderBottom: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid #e2e8f0' }}>
                      <th style={{ textAlign: 'left', paddingBottom: 4, color: isDark ? '#b0bec5' : '#475569' }}>Option</th>
                      <th style={{ textAlign: 'center', paddingBottom: 4, color: isDark ? '#b0bec5' : '#475569' }}>Treasury</th>
                      <th style={{ textAlign: 'center', paddingBottom: 4, color: isDark ? '#b0bec5' : '#475569' }}>Revenue</th>
                      <th style={{ textAlign: 'center', paddingBottom: 4, color: isDark ? '#b0bec5' : '#475569' }}>Reputation</th>
                      <th style={{ textAlign: 'center', paddingBottom: 4, color: isDark ? '#b0bec5' : '#475569' }}>CO₂</th>
                      <th style={{ textAlign: 'center', paddingBottom: 4, color: isDark ? '#b0bec5' : '#475569' }}>SLO</th>
                      <th style={{ textAlign: 'center', paddingBottom: 4, color: isDark ? '#b0bec5' : '#475569' }}>Gov. Risk</th>
                      <th style={{ textAlign: 'center', paddingBottom: 4, color: isDark ? '#b0bec5' : '#475569' }}>NCD</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(options).map(([optId, opt]) => {
                      const imp = opt.impacts || {};
                      const rep = imp.reputation ?? imp.reputation_delta ?? null;
                      const ci = imp.carbon_intensity_delta ?? null;
                      const slo = imp.social_license ?? imp.social_license_delta ?? imp.social_license_boost ?? null;
                      const rev = imp.revenue_delta ?? null;
                      const gov = imp.governance_risk_delta ?? null;
                      const ncd = imp.natural_capital_debt_delta ?? null;
                      const muted = isDark ? '#64748b' : '#94a3b8';
                      return (
                      <tr key={optId} style={{ borderBottom: isDark ? '1px solid rgba(255,255,255,0.04)' : '1px solid #f1f5f9' }}>
                        <td style={{ padding: '6px 0', fontWeight: 600 }}>{optId.replace('option_', 'Option ').toUpperCase()}</td>
                        <td style={{ textAlign: 'center', color: imp.treasury < 0 ? '#f87171' : imp.treasury > 0 ? '#4ade80' : muted }}>
                          {imp.treasury != null ? fmtCurrency(imp.treasury) : '—'}
                        </td>
                        <td style={{ textAlign: 'center', color: rev > 0 ? '#4ade80' : rev < 0 ? '#f87171' : muted }}>
                          {rev != null ? (rev > 0 ? '+' : '') + fmtCurrency(rev) : '—'}
                        </td>
                        <td style={{ textAlign: 'center', color: rep > 0 ? '#4ade80' : rep < 0 ? '#f87171' : muted }}>
                          {rep != null ? (rep > 0 ? '+' : '') + rep : '—'}
                        </td>
                        <td style={{ textAlign: 'center', color: ci < 0 ? '#4ade80' : ci > 0 ? '#f87171' : muted }}>
                          {ci != null ? (ci > 0 ? '+' : '') + ci : '—'}
                        </td>
                        <td style={{ textAlign: 'center', color: slo > 0 ? '#4ade80' : slo < 0 ? '#f87171' : muted }}>
                          {slo != null ? (slo > 0 ? '+' : '') + slo : '—'}
                        </td>
                        <td style={{ textAlign: 'center', color: gov < 0 ? '#4ade80' : gov > 0 ? '#f87171' : muted }}>
                          {gov != null ? (gov > 0 ? '+' : '') + gov : '—'}
                        </td>
                        <td style={{ textAlign: 'center', color: ncd < 0 ? '#4ade80' : ncd > 0 ? '#f87171' : muted }}>
                          {ncd != null ? (ncd > 0 ? '+' : '') + ncd : '—'}
                        </td>
                      </tr>
                    );
                    })}
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
            {/* KPI-belt slot: post-completion Turnaround phase (renders only while active) */}
            <TurnaroundPhaseChip active={globalState?.turnaround_mode}
              phase={globalState?.active_event_flags?.turnaround_phase}
              round={globalState?.turnaround_round} maxRounds={4} />

            {/* Locked decision summary */}
            <div className={focusStyles.decisionSummary}>
              <div className={focusStyles.decisionSummaryTitle}>📋 Locked Strategic Decision</div>
              {isPillarMode ? (
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
              onClick={() => {
                // Go straight to the confirm flow — same trigger as the cockpit
                // footer — instead of dismissing to the dashboard first. The
                // 'Review Your Decisions' modal already provides review +
                // Go-Back-&-Edit, so the dashboard detour was a redundant step.
                if (!hasDecision) { showStageWarning('Select a Strategic Option before committing your turn.'); return; }
                const allocTotal = Object.values(allocations || {}).reduce((s, v) => s + v, 0);
                if (allocTotal <= 0) { showStageWarning('Allocate capital across your business units before committing.'); return; }
                setShowPredictionModal(true);
              }}
            >
              {Object.keys(allocations).length > 0 ? 'Review & Commit →' : 'Allocate capital to at least one BU'}
            </button>
          </div>
        )}

        {/* ── RESULTS STEP ── */}
        {focusStep === 'results' && commitResults && (
          <div>
            <div style={{ textAlign: 'center', marginBottom: 16 }}>
              <div style={{ fontSize: '2rem', marginBottom: 4 }}>📊</div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#e2e8f0', margin: '0 0 4px' }}>Round {roundNumber} Results</h3>
              <p style={{ fontSize: '0.78rem', color: '#94a3b8', margin: 0 }}>Review your outcomes before advancing.</p>
              {/* W5: ceremony stamp — pure decoration on the results card */}
              <div aria-hidden="true" className="stamp-ceremony" style={{
                display: 'inline-block', marginTop: 10, padding: '4px 14px',
                border: '2px solid rgba(74, 222, 128, 0.55)', borderRadius: 6,
                color: '#4ade80', fontSize: '0.68rem', fontWeight: 800,
                letterSpacing: '0.18em', textTransform: 'uppercase',
                fontFamily: 'var(--font-numeral, monospace)',
                animation: 'stampIn 0.45s cubic-bezier(0.2, 1.4, 0.4, 1) 0.15s both',
              }}>
                ✦ Board Resolution Passed ✦
              </div>
            </div>

            {/* W-C (W3): year-boundary artifact — optional, never gates advance.
                Shows at every year-end (even round), Year 1–5 inclusive. Year 5
                (R10) also renders the terminal FrontPage/GameOverSummary; this
                stays an independent, dismissible OverlayHost button and does not
                gate the advance path. */}
            {roundNumber % 2 === 0 && isPlayerVisible('annual_report') && (
              <div style={{ textAlign: 'center', marginBottom: 14 }}>
                <button
                  onClick={() => setShowAnnualReport(true)}
                  style={{
                    padding: '7px 16px', borderRadius: 8, cursor: 'pointer',
                    fontWeight: 700, fontSize: '0.78rem',
                    border: '1px solid rgba(13, 148, 136, 0.5)',
                    background: 'rgba(13, 148, 136, 0.12)', color: '#5eead4',
                  }}
                >📄 Year {Math.ceil(roundNumber / 2)} Integrated Report ready — view</button>
              </div>
            )}

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
                      {dTreasury !== 0 && (
                        <div style={{ fontSize: '0.72rem', fontWeight: 800, color: dTreasury >= 0 ? '#4ade80' : '#f87171', marginTop: 2 }}>
                          {dTreasury >= 0 ? '▲' : '▼'} {fmtCurrency(Math.abs(dTreasury))}
                        </div>
                      )}
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
                      {dRep !== 0 && (
                        <div style={{ fontSize: '0.72rem', fontWeight: 800, color: dRep >= 0 ? '#4ade80' : '#f87171', marginTop: 2 }}>
                          {dRep >= 0 ? '▲' : '▼'} {Math.abs(dRep).toFixed(0)}
                        </div>
                      )}
                    </div>
                    <div className={focusStyles.focusResultCard}>
                      <div className={focusStyles.focusResultIcon}>🏭</div>
                      <div className={focusStyles.focusResultLabel}>CO₂</div>
                      <div className={focusStyles.focusResultValue}>{newCarbon.toLocaleString()}t</div>
                      {dCarbon !== 0 && (
                        <div style={{ fontSize: '0.72rem', fontWeight: 800, color: dCarbon <= 0 ? '#4ade80' : '#f87171', marginTop: 2 }}>
                          {dCarbon > 0 ? '▲' : '▼'} {Math.abs(dCarbon).toLocaleString()}t
                        </div>
                      )}
                    </div>
                    {/* Balance Sheet (Focus Results) — clickable */}
                    {(() => {
                      const bsF = commitResults.globalState?.balance_sheet || commitResults.events?.balance_sheet;
                      if (!bsF || typeof bsF !== 'object' || bsF.net_assets == null) return null;
                      const cColor = { green: '#4ade80', amber: '#fbbf24', red: '#ef4444', breached: '#dc2626' };
                      const cIcon = { green: '🟢', amber: '🟡', red: '🔴', breached: '🚨' };
                      return (
                        <div className={focusStyles.focusResultCard} style={{ cursor: 'pointer' }} onClick={() => setResultsBsModalOpen(true)} title="Click to view full Balance Sheet">
                          <div className={focusStyles.focusResultIcon}>📊</div>
                          <div className={focusStyles.focusResultLabel}>Net Assets</div>
                          <div className={focusStyles.focusResultValue}>${((bsF.net_assets || 0) / 1_000_000).toFixed(0)}M</div>
                          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: cColor[bsF.covenant_status] || '#38bdf8', marginTop: 2 }}>
                            {cIcon[bsF.covenant_status] || '📊'} D/E: {(bsF.debt_to_equity || 0).toFixed(2)}×
                          </div>
                          <div style={{ fontSize: '0.55rem', color: '#64748b', marginTop: 4, fontWeight: 600 }}>🔍 Click to expand</div>
                        </div>
                      );
                    })()}
                  </>
                );
              })()}
            </div>

            {/* WOW-1: Consequence Replay — animated causal chain after commit */}
            <ConsequenceReplay
              commitResults={commitResults}
              sessionId={sim?.sessionId}
              roundNumber={roundNumber}
              globalState={globalState}
            />

            {/* Events summary */}
            {commitResults.events && Object.keys(commitResults.events).length > 0 && (
              <div style={{ padding: '10px 14px', background: 'rgba(0,0,0,0.2)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)', marginBottom: 16, fontSize: '0.72rem', color: '#cbd5e1' }}>
                <div style={{ fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', marginBottom: 6, fontSize: '0.68rem' }}>⚡ Key Events</div>
                {commitResults.events.talent_penalty_applied > 1 && (
                  <div style={{ marginBottom: 3 }}>🧠 Brain-Drain: Software OPEX inflated by {((commitResults.events.talent_penalty_applied - 1) * 100).toFixed(1)}%</div>
                )}
                {commitResults.events.loan_interest_payment > 0 && (
                  <div style={{ marginBottom: 3 }}>🏦 Loan Interest: -{fmtCurrency(commitResults.events.loan_interest_payment)}</div>
                )}
                {commitResults.events.covenant_surcharge > 0 && (
                  <div style={{ marginBottom: 3, color: '#f87171' }}>📊 Covenant Penalty: -{fmtCurrency(commitResults.events.covenant_surcharge)} interest surcharge</div>
                )}
                {commitResults.events.covenant_warning && (
                  <div style={{ marginBottom: 3, color: '#fbbf24' }}>⚠️ {typeof commitResults.events.covenant_warning === 'string' ? commitResults.events.covenant_warning : 'Debt covenant under pressure'}</div>
                )}
                {commitResults.events.esg_adjusted_wacc && commitResults.events.esg_adjusted_wacc.adjusted_wacc > 0.08 && (
                  <div style={{ marginBottom: 3, color: '#f87171' }}>📊 ESG-WACC at {(commitResults.events.esg_adjusted_wacc.adjusted_wacc * 100).toFixed(1)}% — lender covenant thresholds tightening</div>
                )}
                {commitResults.events.employer_brand_opex_penalty && (
                  <div style={{ marginBottom: 3, color: '#f87171' }}>👥 Talent Crisis: +{((commitResults.events.employer_brand_opex_penalty.multiplier || 0) * 100).toFixed(1)}% OPEX across all BUs</div>
                )}
              </div>
            )}

            {/* V-A (player v2, V-3): the retrospect lands where the learning
                does — same component, same data, moved from the ambient rail.
                Rendered against the just-committed state. */}
            <div style={{ marginBottom: 16 }}>
              <EngineEventsPanel
                globalState={commitResults.globalState || globalState}
                roundEvents={commitResults.events}
                sections="retrospect"
              />
            </div>

            {/* ── EBITDA Decomposition Waterfall (Gap 1: visual strategy storytelling) ── */}
            <EBITDAWaterfall
              businessUnits={commitResults.businessUnits || businessUnits}
              globalState={commitResults.globalState || globalState}
              events={commitResults.events || events}
              commitResults={commitResults}
              isDark={isDark}
            />

            {/* ── Reveal-schedule lock notice ── */}
            {peerLockMsg && (
              <div style={{ padding: '10px 14px', background: 'rgba(148,163,184,0.08)', borderRadius: 8, border: '1px dashed rgba(148,163,184,0.35)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8, color: '#94a3b8', fontSize: '0.72rem', fontWeight: 600 }}>
                <span>🔒</span> {peerLockMsg}
              </div>
            )}

            {/* ── Inline Peer Performance (Focus Results) ── */}
            {peerLeaderboard.length > 0 && (
              <div style={{ padding: '10px 14px', background: 'rgba(99,102,241,0.06)', borderRadius: 8, border: '1px solid rgba(99,102,241,0.2)', marginBottom: 16 }}>
                <div style={{ fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#818cf8', marginBottom: 8, fontSize: '0.68rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>📊</span> {peerLeaderboard.some(t => t.isAI) ? 'AI Benchmark Comparison' : 'Cohort Leaderboard'}
                  {peerLeaderboard.some(t => t.isAI) && <span style={{ fontSize: '0.5rem', background: 'rgba(245,158,11,0.15)', color: '#fbbf24', padding: '1px 5px', borderRadius: 3, fontWeight: 700 }}>🤖 AI</span>}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {peerLeaderboard.slice(0, 5).map(team => (
                    <div key={team.rank} style={{
                      display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', borderRadius: 6,
                      background: team.isYou ? 'rgba(99,102,241,0.12)' : 'rgba(255,255,255,0.02)',
                      border: team.isYou ? '1px solid rgba(99,102,241,0.4)' : '1px solid transparent',
                    }}>
                      <span style={{ fontSize: '0.85rem', width: 22, textAlign: 'center', flexShrink: 0 }}>
                        {team.rank <= 3 ? ['🥇', '🥈', '🥉'][team.rank - 1] : team.rank}
                      </span>
                      <span style={{ flex: 1, fontSize: '0.72rem', fontWeight: team.isYou ? 800 : 600, color: team.isYou ? '#a5b4fc' : '#cbd5e1', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {team.name}
                        {team.isYou && <span style={{ marginLeft: 6, fontSize: '0.68rem', background: 'rgba(99,102,241,0.3)', padding: '1px 6px', borderRadius: 4, fontWeight: 800, color: '#c7d2fe' }}>YOU</span>}
                      </span>
                      <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#4ade80', fontFamily: "'JetBrains Mono', monospace", flexShrink: 0 }}>
                        {fmtCurrency(team.treasury)}
                      </span>
                      <span style={{ fontSize: '0.68rem', color: '#94a3b8', flexShrink: 0, width: 28, textAlign: 'right' }}>
                        {team.reputation?.toFixed(0) ?? '—'}
                      </span>
                      <span style={{
                        fontSize: '0.72rem', flexShrink: 0,
                        color: team.trend === '↑' ? '#4ade80' : team.trend === '↓' ? '#f87171' : '#94a3b8',
                      }}>{team.trend}</span>
                    </div>
                  ))}
                </div>
                {peerLeaderboard.length > 5 && (
                  <div style={{ fontSize: '0.6rem', color: '#64748b', textAlign: 'center', marginTop: 6 }}>
                    +{peerLeaderboard.length - 5} more teams
                  </div>
                )}
              </div>
            )}

            {/* Advance button */}
            {(() => {
              const teamCount = globalState?.cohort_team_count || 0;
              const commitsCount = globalState?.team_commits_this_round || 0;
              const isMultiTeam = teamCount > 1;
              // Facilitator-paced advance: under manual/timed pacing (or after a
              // free-mode timeout/Force Advance) the wait-for-all barrier does
              // not apply — the next round's commit gate does the pacing.
              const unblocked = globalState?.cohort_advance_unblocked === true;
              const allCommitted = commitsCount >= teamCount || unblocked;
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

          {/* Phase D: the dense center content is the DISCLOSURE layer now —
              it renders when the canvas is dismissed (D1 pinned-dashboard
              preference) or when CANVAS_FIRST is rolled back. Under the old
              takeover the overlay covered it anyway, so gating it on
              isFocusActive is visually equivalent in both shells. */}
          {!(CANVAS_FIRST && isFocusActive) && (
            <>

          {/* Briefing Panel */}
          <div className={styles.briefingArea} id="tour-briefing-target">
            <div className={styles.briefingHeader} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <span className={styles.briefingRound}>Round {roundNumber}</span>
                <h2 className={styles.briefingTitle}>{activeRoundTitles[roundNumber] || `Module ${roundNumber}`}</h2>
              </div>
              {/* #6: Inline BU Filter */}
              {businessUnits?.length > 1 && (
                <select
                  value={filterBU}
                  onChange={(e) => { const v = e.target.value; if (v === 'all') { exitDeepDive(); } else { enterDeepDive(v); } }}
                  style={{
                    padding: '4px 8px', borderRadius: 6, fontSize: '0.68rem', fontWeight: 700,
                    background: 'rgba(14,20,36,0.6)', color: '#94a3b8', border: '1px solid rgba(148,163,184,0.15)',
                    cursor: 'pointer', fontFamily: "'DM Sans', sans-serif", textTransform: 'uppercase',
                    letterSpacing: '0.05em', appearance: 'auto', minWidth: 100,
                  }}
                >
                  <option key="__all__" value="all">All BUs</option>
                  {businessUnits.map(bu => {
                    const buKey = bu.id || bu.bu_id;
                    return (
                      <option key={buKey} value={buKey}>{(bu.name || buKey).replace(/_/g, ' ')}</option>
                    );
                  })}
                </select>
              )}
            </div>
            <div className={styles.briefingBody}>
              {crisisInfo?.description || crisisInfo?.narrative || (
                <>The board expects decisive action this period. Review the crisis briefing in your mailbox and select a strategic response below. Your choice will affect treasury, reputation, and long-term resilience.</>
              )}
            </div>

            {/* Quick Resume — shortcut for returning players (round 3+) */}
            {isReturningPlayer && !commitResults && isFocusActive && (
              <button
                onClick={handleQuickResume}
                style={{
                  marginTop: 8, width: '100%', padding: '8px 14px',
                  background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.06))',
                  border: '1px solid rgba(99, 102, 241, 0.25)',
                  borderRadius: 8, color: '#a5b4fc',
                  fontSize: '0.75rem', fontWeight: 700,
                  cursor: 'pointer', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', gap: '6px',
                  transition: 'background 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease, transform 0.2s ease',
                  letterSpacing: '0.03em',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.background = 'linear-gradient(135deg, rgba(99, 102, 241, 0.18), rgba(168, 85, 247, 0.12))';
                  e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.45)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = 'linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.06))';
                  e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.25)';
                }}
              >
                ⚡ Skip to Decisions
                <span style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 500 }}>(Quick Resume)</span>
              </button>
            )}

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

          {/* ── Progressive Disclosure: Deep Dive Header ── */}
          {isDeepDive && investigatedBUData && (
            <div className={`${styles.deepDiveHeader} ${styles.deepDiveEnter}`}>
              <button className={styles.deepDiveBackBtn} onClick={exitDeepDive}>
                ← Overview
              </button>
              <div className={styles.deepDiveBuTitle}>
                <span>{BU_ICONS[investigatedBU] || '🏢'}</span>
                {(investigatedBUData.name || investigatedBU).replace(/_/g, ' ')}
              </div>
              <div className={styles.deepDiveKbHint}>
                <kbd>Esc</kbd> back · <kbd>1</kbd>–<kbd>{businessUnits?.length || 4}</kbd> switch BU
              </div>
            </div>
          )}

          {/* ── Progressive Disclosure: Glance Mode — Deployment Summary ── */}
          {!isDeepDive && (
            <div className={styles.glanceEnter}>
              <div className={styles.deploymentSummary}>
                <span style={{ color: 'var(--ck-text-3, #64748b)' }}>🏦 Capital Deployed</span>
                <span style={{ color: 'var(--ck-text-1, #e2e8f0)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {fmtCurrency(Object.values(allocations || {}).reduce((s, v) => s + v, 0))} / {fmtCurrency(csfPool)}
                </span>
                <span style={{ color: 'var(--ck-accent, #5eead4)', fontSize: '0.68rem' }}>
                  Click a BU below to investigate →
                </span>
              </div>
            </div>
          )}

          {/* #2: Compact Tabular BU Summary — Deep Dive only */}
          {isDeepDive && businessUnits?.length > 0 && (
            <div className={styles.deepDiveEnter} style={{
              borderRadius: 8, overflow: 'hidden', marginTop: 8,
              border: isDark ? '1px solid rgba(148,163,184,0.08)' : '1px solid #e2e8f0',
              background: isDark ? 'rgba(14,20,36,0.4)' : '#fafbfc',
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.68rem', fontFamily: "'DM Sans', sans-serif" }}>
                <thead>
                  <tr style={{ borderBottom: isDark ? '1px solid rgba(148,163,184,0.1)' : '1px solid #e2e8f0' }}>
                    {['BU', 'Revenue', 'Margin', 'SLO', 'Gov Risk', 'NCD', 'Allocated'].map(h => (
                      <th key={h} style={{
                        padding: '6px 8px', textAlign: h === 'BU' ? 'left' : 'center',
                        fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em',
                        color: isDark ? '#64748b' : '#94a3b8', fontSize: '0.5rem',
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(filterBU === 'all' ? businessUnits : businessUnits.filter(bu => bu.id === filterBU)).map((bu, idx) => {
                    const margin = bu.revenue_base > 0 ? ((bu.revenue_base - bu.opex_base) / bu.revenue_base * 100) : 0;
                    const alloc = allocations?.[bu.id] || 0;
                    return (
                      <tr key={bu.id || bu.bu_id || `bu-row-${idx}`} style={{ borderBottom: isDark ? '1px solid rgba(148,163,184,0.05)' : '1px solid #f1f5f9' }}>
                        <td style={{ padding: '5px 8px', fontWeight: 700, color: isDark ? '#e2e8f0' : '#1e293b', whiteSpace: 'nowrap' }}>
                          {(bu.name || bu.id).replace(/_/g, ' ')}
                        </td>
                        <td style={{ padding: '5px 6px', textAlign: 'center', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600, color: isDark ? '#cbd5e1' : '#334155' }}>
                          {fmtCurrency(bu.revenue_base || 0)}
                        </td>
                        <td style={{ padding: '5px 6px', textAlign: 'center', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: margin >= 25 ? '#10b981' : margin >= 15 ? '#f59e0b' : '#ef4444' }}>
                          {margin.toFixed(1)}%
                        </td>
                        <td style={{ padding: '5px 6px', textAlign: 'center', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600, color: isDark ? '#a5b4fc' : '#6366f1' }}>
                          {bu.social_license_to_operate || 0}
                        </td>
                        <td style={{ padding: '5px 6px', textAlign: 'center', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600, color: (bu.governance_risk || 0) > 10 ? '#f87171' : isDark ? '#94a3b8' : '#64748b' }}>
                          {bu.governance_risk || 0}%
                        </td>
                        <td style={{ padding: '5px 6px', textAlign: 'center', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600, color: isDark ? '#94a3b8' : '#64748b' }}>
                          {fmtCurrency(bu.natural_capital_debt || 0)}
                        </td>
                        <td style={{ padding: '5px 6px', textAlign: 'center', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: alloc > 0 ? '#5eead4' : isDark ? '#475569' : '#94a3b8' }}>
                          {alloc > 0 ? fmtCurrency(alloc) : '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Resource Allocation Matrix — Deep Dive only.
              V-C (player v2, V-1): one primary work surface at a time. Until
              the strategic decision is made, the full matrix (pool gauge +
              four slider tiles) is a locked one-liner, not a disabled
              spectacle behind a click-intercept — same locked-truth pattern
              as V-B's options. The moment `canAccessAllocation` flips, the
              matrix renders exactly as before. */}
          {isDeepDive && !canAccessAllocation && (
            <div className={`${styles.decisionArea} ${styles.deepDiveEnter}`} style={{ flex: 'none', marginTop: 8 }}>
              <div
                id="tour-capital-target"
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
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '10px 12px', borderRadius: 8, cursor: 'not-allowed',
                  border: '1px dashed rgba(148,163,184,0.3)', background: 'rgba(148,163,184,0.04)',
                  fontSize: '0.75rem', color: '#94a3b8',
                }}
              >
                <span aria-hidden="true">🔒</span>
                <span style={{ flex: 1, fontWeight: 600 }}>
                  Capital Allocation — {fmtCurrency(csfPool)} CSF pool
                </span>
                <span style={{ fontSize: '0.7rem' }}>
                  {!hasDecision && canAccessStrategy ? 'unlocks after your strategic decision' : 'unlocks with the flow above'}
                </span>
              </div>
            </div>
          )}
          {isDeepDive && canAccessAllocation && (
          <div className={`${styles.decisionArea} ${styles.deepDiveEnter}`} style={{ flex: 'none', overflow: 'visible', borderBottom: isDark ? '1px solid rgba(0,229,195,0.06)' : '1px solid #e2e8f0', paddingBottom: 8, position: 'relative' }}>
            <div id="tour-capital-target">
            <InvestmentMatrix
              csfPool={csfPool}
              globalState={globalState}
              businessUnits={businessUnits}
              allocations={allocations}
              historyData={historyData}
              decisionParadigm={decisionParadigm}
              onAllocationsChange={onAllocationsChange}
            />
            </div>
          </div>
          )}

          {/* Decision Workspace — Minimised in Glance, Full in Deep Dive */}
          {!isDeepDive && options && Object.keys(options).length > 0 && (
            <div className={`${styles.decisionArea} ${styles.glanceEnter}`} style={{ flex: 'none', overflow: 'visible', position: 'relative', marginTop: '12px' }}>
              <div className={styles.decisionHeader}>
                <span className={styles.decisionLabel}>
                  {isPillarMode ? '🎛️ Strategic Pillars' : '📋 Strategic Options'}
                </span>
                {decisionChoice && (
                  <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#4ade80', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    ✓ {decisionChoice.replace(/_/g, ' ')}
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {Object.entries(options).map(([optId, opt]) => {
                  const cost = opt.impacts?.treasury || 0;
                  const isSelected = decisionChoice === optId;
                  return (
                    <div
                      key={optId}
                      className={styles.optionMini}
                      style={isSelected ? { borderColor: 'var(--ck-accent, #5eead4)', background: 'rgba(94,234,212,0.06)' } : {}}
                      onClick={() => {
                        // Select this option and enter deep dive for full interaction
                        if (canAccessStrategy) handleLegacySelect(optId);
                        if (businessUnits?.[0]) enterDeepDive(businessUnits[0].id || businessUnits[0].bu_id);
                      }}
                    >
                      <span className={styles.optionMiniLabel}>
                        {/* V-B: honest lock state on the glance minis too */}
                        {!canAccessStrategy ? '🔒 ' : isSelected ? '✓ ' : ''}{optId.replace('option_', '').toUpperCase()}: {opt.title || opt.name || optId}
                      </span>
                      <span className={styles.optionMiniCost} style={cost < 0 ? { color: '#ef4444' } : cost > 0 ? { color: '#4ade80' } : {}}>
                        {cost !== 0 ? fmtCurrency(cost) : '—'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          {/* V-C (V-1): decision made → the options section folds to one line;
              the matrix below becomes the primary surface. "Change" restores
              the full section (selection handlers untouched). */}
          {isDeepDive && canAccessStrategy && decisionChoice && !isPillarMode && !optionsReopen && (
            <div className={`${styles.decisionArea} ${styles.deepDiveEnter}`} style={{ flex: 'none', marginTop: '16px' }}>
              <div id="tour-strategic-target" style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '10px 12px', borderRadius: 8,
                border: '1px solid rgba(94,234,212,0.25)', background: 'rgba(94,234,212,0.05)',
                fontSize: '0.76rem',
              }}>
                <span style={{ color: '#4ade80' }}>✓</span>
                <span style={{ flex: 1, fontWeight: 700, color: isDark ? '#e2e8f0' : '#1e293b' }}>
                  Strategic Decision: {decisionChoice.replace('option_', '').toUpperCase()}
                  {options?.[decisionChoice]?.title ? ` — ${options[decisionChoice].title}` : ''}
                </span>
                {(options?.[decisionChoice]?.impacts?.treasury || 0) !== 0 && (
                  <span style={{ fontFamily: 'var(--font-numeral, monospace)', fontSize: '0.72rem', color: '#94a3b8' }}>
                    {fmtCurrency(options[decisionChoice].impacts.treasury)}
                  </span>
                )}
                <button
                  onClick={() => setOptionsReopen(true)}
                  style={{
                    padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: '0.68rem',
                    fontWeight: 700, border: '1px solid rgba(148,163,184,0.3)', background: 'transparent',
                    color: isDark ? '#94a3b8' : '#475569',
                  }}
                >Change</button>
              </div>
            </div>
          )}
          {isDeepDive && !(canAccessStrategy && decisionChoice && !isPillarMode && !optionsReopen) && (
          <div className={`${styles.decisionArea} ${styles.deepDiveEnter}`} style={{ flex: 'none', overflow: 'visible', position: 'relative', marginTop: '16px' }}>
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
                {isPillarMode ? '🎛️ Strategic Pillars' : '📋 Strategic Options'}
              </span>
              {projectedCost !== 0 && (
                <span className={`${styles.projectedDelta} ${projectedCost > 0 ? styles.projectedDown : styles.projectedUp}`}>
                  Impact: {fmtCurrency(projectedCost)}
                </span>
              )}
            </div>

            {/* Shadow Board Archetype Reminder — persistent from R5+ */}
            {roundNumber >= 5 && globalState?.active_event_flags?.shadow_board_archetype && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                padding: '0.35rem 0.65rem', marginBottom: '6px',
                borderRadius: '6px', fontSize: '0.7rem',
                background: globalState.active_event_flags.shadow_board_archetype === 'Sustainability-First'
                  ? 'rgba(16, 185, 129, 0.08)'
                  : globalState.active_event_flags.shadow_board_archetype === 'Profit-Maximiser'
                  ? 'rgba(245, 158, 11, 0.08)'
                  : 'rgba(139, 92, 246, 0.08)',
                border: `1px solid ${
                  globalState.active_event_flags.shadow_board_archetype === 'Sustainability-First'
                    ? 'rgba(16, 185, 129, 0.25)'
                    : globalState.active_event_flags.shadow_board_archetype === 'Profit-Maximiser'
                    ? 'rgba(245, 158, 11, 0.25)'
                    : 'rgba(139, 92, 246, 0.25)'
                }`,
              }}>
                <span style={{ fontSize: '0.9rem' }}>
                  {globalState.active_event_flags.shadow_board_archetype === 'Sustainability-First' ? '🌱'
                    : globalState.active_event_flags.shadow_board_archetype === 'Profit-Maximiser' ? '📈' : '⚡'}
                </span>
                <span style={{
                  fontWeight: 700,
                  color: globalState.active_event_flags.shadow_board_archetype === 'Sustainability-First'
                    ? '#10b981'
                    : globalState.active_event_flags.shadow_board_archetype === 'Profit-Maximiser'
                    ? '#f59e0b'
                    : '#8b5cf6',
                }}>
                  {globalState.active_event_flags.shadow_board_archetype}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>
                  {globalState.active_event_flags.shadow_board_archetype === 'Sustainability-First'
                    ? '— Your R5 board audit prioritised long-term planetary resilience over short-term returns'
                    : globalState.active_event_flags.shadow_board_archetype === 'Profit-Maximiser'
                    ? '— Your R5 board audit prioritised financial efficiency over ecosystem health'
                    : '— Your R5 board audit prioritised calculated agility over maximum governance protection'}
                </span>
              </div>
            )}

            {/* V-B (player v2, V-2): locked-state truth. Pre-gate, the full
                option prose used to render behind a click-intercept — 400
                words a player cannot act on, and some believed they'd
                "chosen" by reading. Locked summaries name the unlock instead;
                the full cards return unchanged the moment the gate opens
                (and always render in the canvas strategy stage). */}
            {!canAccessStrategy ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {(() => {
                  const unlockHint = !hasReadBriefing
                    ? 'Read the Briefing to unlock'
                    : (hasSecondStage && !secondStageDone)
                      ? (roundNumber === 1 ? 'Complete the Stakeholder Map to unlock' : 'Complete the CSRD Assessment to unlock')
                      : 'Complete the Shadow Board Audit to unlock';
                  const rows = isPillarMode
                    ? Object.entries(pillarConfig?.areas || {}).map(([k, a]) => ({ key: k, label: `${AREA_ICONS[k] || '📌'} ${a.label}`, cost: null }))
                    : ['option_a', 'option_b', 'option_c'].filter(id => options[id]).map(id => ({
                        key: id,
                        label: `${id.replace('option_', '').toUpperCase()}: ${options[id].title || options[id].name || id}`,
                        cost: options[id].impacts?.treasury || 0,
                      }));
                  return (
                    <>
                      {rows.map(r => (
                        <div key={r.key} style={{
                          display: 'flex', alignItems: 'center', gap: 8,
                          padding: '9px 12px', borderRadius: 8,
                          border: '1px dashed rgba(148,163,184,0.3)', background: 'rgba(148,163,184,0.04)',
                          fontSize: '0.75rem', color: '#94a3b8',
                        }}>
                          <span aria-hidden="true">🔒</span>
                          <span style={{ flex: 1, fontWeight: 600 }}>{r.label}</span>
                          {r.cost != null && r.cost !== 0 && (
                            <span style={{ fontFamily: 'var(--font-numeral, monospace)', fontSize: '0.7rem' }}>{fmtCurrency(r.cost)}</span>
                          )}
                        </div>
                      ))}
                      <div style={{ fontSize: '0.7rem', color: '#64748b', padding: '2px 2px 0' }}>
                        🔒 {unlockHint} — full details and the comparison matrix appear here once it&apos;s done.
                      </div>
                    </>
                  );
                })()}
              </div>
            ) : isPillarMode ? (
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
                      <PillarSelectDropdown
                        options={area.options || {}}
                        value={selectedOpt || null}
                        onChange={(optKey) => handlePillarSelect(areaKey, optKey)}
                        fmtCurrency={fmtCurrency}
                        detailedDescs={DETAILED_DESCRIPTIONS.pillars?.[roundNumber]?.[areaKey] || {}}
                      />
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

            {/* Strategic Breakdown Panel — V-B: withheld with the options
                pre-gate (its comparison matrix is option prose too). */}
            {canAccessStrategy && (
            <div className={styles.breakdownPanel}>
              <div className={styles.breakdownLabels}>
                <span className={styles.breakdownIcon}>🔍</span>
                <span className={styles.breakdownTitle}>STRATEGIC BREAKDOWN</span>
              </div>
              <div className={styles.breakdownContent}>
                {hoveredOpt ? (
                  <div>
                    <p><strong>{hoveredOpt.title}:</strong> {hoveredOpt.desc}</p>
                    {hoveredOpt.regulatoryTooltip && (
                      <div style={{
                        marginTop: '8px',
                        padding: '8px 10px',
                        background: 'rgba(26, 54, 93, 0.08)',
                        border: '1px solid rgba(112, 128, 144, 0.3)',
                        borderLeft: '3px solid #1a365d',
                        borderRadius: '2px',
                        fontFamily: "'Courier New', monospace",
                        fontSize: '0.65rem',
                        lineHeight: '1.5',
                        color: '#475569',
                        letterSpacing: '0.01em',
                      }}>
                        <div style={{ fontWeight: 700, fontSize: '0.6rem', color: '#1a365d', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                          NGRBC Regulatory Advisory
                        </div>
                        {hoveredOpt.regulatoryTooltip}
                      </div>
                    )}
                  </div>
                ) : decisionParadigm === 'legacy_abc' ? (
                  <div style={{ marginTop: 4 }}>
                    <div style={{ fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase', color: '#64748b', marginBottom: 6 }}>Comparison Matrix</div>
                    <table style={{ width: '100%', fontSize: '0.68rem', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
                          <th style={{ textAlign: 'left', paddingBottom: 4 }}>Option</th>
                          <th style={{ textAlign: 'center', paddingBottom: 4 }}>Treasury</th>
                          <th style={{ textAlign: 'center', paddingBottom: 4 }}>Revenue</th>
                          <th style={{ textAlign: 'center', paddingBottom: 4 }}>Reputation</th>
                          <th style={{ textAlign: 'center', paddingBottom: 4 }}>CO₂</th>
                          <th style={{ textAlign: 'center', paddingBottom: 4 }}>SLO</th>
                          <th style={{ textAlign: 'center', paddingBottom: 4 }}>Gov.</th>
                          <th style={{ textAlign: 'center', paddingBottom: 4 }}>NCD</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(options).map(([optId, opt]) => {
                          const imp = opt.impacts || {};
                          const rep = imp.reputation ?? imp.reputation_delta ?? null;
                          const ci = imp.carbon_intensity_delta ?? null;
                          const slo = imp.social_license ?? imp.social_license_delta ?? imp.social_license_boost ?? null;
                          const rev = imp.revenue_delta ?? null;
                          const gov = imp.governance_risk_delta ?? null;
                          const ncd = imp.natural_capital_debt_delta ?? null;
                          const muted = '#94a3b8';
                          return (
                          <tr key={optId} style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                            <td style={{ padding: '6px 0', fontWeight: 600 }}>{optId.replace('option_', 'Option ').toUpperCase()}</td>
                            <td style={{ textAlign: 'center', color: imp.treasury < 0 ? '#ef4444' : imp.treasury > 0 ? '#16a34a' : muted }}>
                              {imp.treasury != null ? fmtCurrency(imp.treasury) : '—'}
                            </td>
                            <td style={{ textAlign: 'center', color: rev > 0 ? '#16a34a' : rev < 0 ? '#ef4444' : muted }}>
                              {rev != null ? (rev > 0 ? '+' : '') + fmtCurrency(rev) : '—'}
                            </td>
                            <td style={{ textAlign: 'center', color: rep > 0 ? '#16a34a' : rep < 0 ? '#ef4444' : muted }}>
                              {rep != null ? (rep > 0 ? '+' : '') + rep : '—'}
                            </td>
                            <td style={{ textAlign: 'center', color: ci < 0 ? '#16a34a' : ci > 0 ? '#ef4444' : muted }}>
                              {ci != null ? (ci > 0 ? '+' : '') + ci : '—'}
                            </td>
                            <td style={{ textAlign: 'center', color: slo > 0 ? '#16a34a' : slo < 0 ? '#ef4444' : muted }}>
                              {slo != null ? (slo > 0 ? '+' : '') + slo : '—'}
                            </td>
                            <td style={{ textAlign: 'center', color: gov < 0 ? '#16a34a' : gov > 0 ? '#ef4444' : muted }}>
                              {gov != null ? (gov > 0 ? '+' : '') + gov : '—'}
                            </td>
                            <td style={{ textAlign: 'center', color: ncd < 0 ? '#16a34a' : ncd > 0 ? '#ef4444' : muted }}>
                              {ncd != null ? (ncd > 0 ? '+' : '') + ncd : '—'}
                            </td>
                          </tr>
                        );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className={styles.breakdownPlaceholder}>
                    {/* Truth fix: each pillar dropdown shows its option's cost,
                        description, and impacts in its OWN hover tooltip — this
                        panel does not duplicate that. */}
                    Open a Strategic Pillar dropdown and hover an option — its cost, description, and impacts appear beside it.
                  </p>
                )}
              </div>
            </div>
            )}

            {/* Phase 3.3: Consequence DNA — causal chains from past decisions (R4+) */}
            <ConsequenceDNA
              history={history}
              roundNumber={roundNumber}
              globalState={globalState}
              events={events}
            />

            {/* Consequence DNA Visualizer Trigger (Sankey pop-out) */}
            {roundNumber >= 4 && (
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <ConsequenceDNATrigger
                  ignited={dnaIgnited}
                  onClick={() => setShowDNAVisualizer(true)}
                />
                {/* Antigravity: 3D Constellation Trigger */}
                <button
                  onClick={() => setShowConstellation(true)}
                  style={{
                    padding: '6px 14px',
                    background: 'linear-gradient(135deg, rgba(94,234,212,0.08), rgba(129,140,248,0.08))',
                    border: '1px solid rgba(94,234,212,0.2)',
                    borderRadius: 8,
                    color: '#5eead4',
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                    letterSpacing: '0.04em',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 5,
                  }}
                  onMouseEnter={(e) => { e.target.style.borderColor = 'rgba(94,234,212,0.4)'; e.target.style.boxShadow = '0 0 12px rgba(94,234,212,0.15)'; }}
                  onMouseLeave={(e) => { e.target.style.borderColor = 'rgba(94,234,212,0.2)'; e.target.style.boxShadow = 'none'; }}
                  data-tooltip="Open 3D ESG Impact Constellation — visualize causal chains across all rounds"
                >
                  🌐 3D Constellation
                </button>
              </div>
            )}

            {/* Consequence DNA Visualizer Pop-Out */}
            <ConsequenceDNAVisualizer
              sessionId={sim?.sessionId}
              isOpen={showDNAVisualizer}
              onClose={() => setShowDNAVisualizer(false)}
              frozen={false}
            />

            {/* Antigravity Enhancement: 3D ESG Impact Constellation */}
            {showConstellation && (
              <ESGImpactConstellation
                history={history}
                currentRound={roundNumber}
                onClose={() => setShowConstellation(false)}
              />
            )}

            {/* Phase 3.7: Terminal Valuation Calculator (R9-10 Finale tier) */}
            <TerminalValuationCalc
              globalState={globalState}
              businessUnits={businessUnits}
              roundNumber={roundNumber}
              history={history}
              fmtCurrency={fmtCurrency}
            />

            {/* V-A+ (owner request, 2026-07-11): the "Active Infrastructure
                Projects" panel was removed from the player screen — the
                working-capital/synergy timers are engine internals, not a
                player decision surface (and its light palette fought the
                theme). Display-only removal: `pending_capex_projects` stays
                in the payload untouched; restore = git revert this commit. */}

            </div>
          </div>
          )}
          
          {/* #4: BU Ticker Strip — Clickable for Progressive Disclosure */}
          {businessUnits?.length > 0 && (
            <div className={styles.buTicker}>
              {businessUnits.map((bu, idx) => {
                const buId = bu.id || bu.bu_id;
                const margin = bu.revenue_base > 0 ? ((bu.revenue_base - bu.opex_base) / bu.revenue_base * 100) : 0;
                const prevBu = previousGlobalState?.business_units?.find(p => p.id === bu.id);
                const revDelta = prevBu ? ((bu.revenue_base || 0) - (prevBu.revenue_base || 0)) : 0;
                const isActive = isDeepDive && investigatedBU === buId;
                const isDimmed = isDeepDive && investigatedBU !== buId;
                return (
                  <div
                    key={buId || `bu-${idx}`}
                    className={`${styles.buTickerItem} ${isActive ? styles.buTickerItemActive : ''} ${isDimmed ? styles.buTickerItemDimmed : ''}`}
                    onClick={() => isActive ? exitDeepDive() : enterDeepDive(buId)}
                    title={`${isActive ? 'Exit' : 'Investigate'} ${(bu.name || bu.id).replace(/_/g, ' ')} · Press ${idx + 1} or Esc`}
                  >
                    <div className={styles.buTickerName}>{(bu.name || bu.id).replace(/_/g, ' ')}</div>
                    <div className={styles.buTickerMetrics}>
                      <span>Rev {fmtCurrency(bu.revenue_base || 0)}</span>
                      {revDelta !== 0 && (
                        <span style={{ color: revDelta > 0 ? '#4ade80' : '#f87171' }}>
                          {revDelta > 0 ? '▲' : '▼'}
                        </span>
                      )}
                      <span style={{ color: margin >= 25 ? '#6ee7b7' : margin >= 15 ? '#fcd34d' : '#fca5a5' }}>
                        {margin.toFixed(0)}%
                      </span>
                    </div>
                    {/* #9: Micro-Sparkline — last 5 rounds of BU revenue */}
                    {(() => {
                      const buHistory = (history || []).map(h => (h.business_units || []).find(b => b.id === buId)?.revenue_base || 0).concat([bu.revenue_base || 0]);
                      if (buHistory.length < 2) return null;
                      const pts = buHistory.slice(-5);
                      const min = Math.min(...pts); const max = Math.max(...pts);
                      const range = max - min || 1;
                      const w = 36; const h2 = 14;
                      const polyPts = pts.map((v, i) => `${(i / (pts.length - 1)) * w},${h2 - ((v - min) / range) * (h2 - 2)}`).join(' ');
                      return (
                        <svg width={w} height={h2} style={{ display: 'block', marginTop: 2 }}>
                          <polyline points={polyPts} fill="none" stroke={pts[pts.length-1] >= pts[0] ? '#4ade80' : '#f87171'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      );
                    })()}
                    {/* #4: Allocation Bar — capital deployed to this BU */}
                    {(() => {
                      const alloc = allocations?.[buId] || 0;
                      const pct = csfPool > 0 ? (alloc / csfPool) * 100 : 0;
                      return (
                        <div style={{ width: '100%', marginTop: 3 }}>
                          <div style={{ height: 3, background: 'rgba(255,255,255,0.06)', borderRadius: 2, overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${Math.min(100, pct)}%`, background: alloc > 0 ? '#5eead4' : 'transparent', borderRadius: 2, transition: 'width 0.3s ease' }} />
                          </div>
                          {alloc > 0 && (
                            <div style={{ fontSize: '0.45rem', color: '#5eead4', marginTop: 1, textAlign: 'center', fontWeight: 600, fontFamily: 'JetBrains Mono, monospace' }}>
                              {fmtCurrency(alloc)}
                            </div>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                );
              })}
            </div>
          )}

            </>
          )}

          {/* V-C (V-6): docked flow indicator — always visible at the foot of
              the center console, never overlapping content (the old 80px
              anti-overlap spacer is retired with the float). */}
          {roundChecklist && (
            <div style={{
              position: 'sticky', bottom: 0, zIndex: 20,
              padding: '6px 16px 10px', flexShrink: 0, marginTop: 'auto',
              background: 'linear-gradient(to top, var(--bg-primary, #0a0f1e) 65%, transparent)',
            }}>
              {roundChecklist}
            </div>
          )}
        </main>

        {/* ── RIGHT SIDEBAR ─── */}
        <aside id="tour-intelligence-target" className={styles.rightSidebar}>
          {/* Floating Resources Pill */}
          <button className={styles.resourcesPill} onClick={onResourcesOpen}>
            <span style={{ fontSize: '0.9rem' }}>📚</span>
            <span className={styles.resourcesPillLabel}>Resources</span>
            <span className={styles.resourcesPillArrow}>❯</span>
            {hasNewResources && <span className={styles.resourcesPillBadge} />}
          </button>

          {isPlayerVisible('competitor_intel') && (
            <CompetitorIntelligence globalState={globalState} ebitda={ebitda} roundNumber={roundNumber} />
          )}

          {/* MP-01: Round commit status — shows how many teams have committed */}
          {sim?.sessionId && sim.sessionId !== 'demo' && (globalState?.cohort_team_count > 0) && (
            <div style={{
              padding: '6px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              background: (globalState?.team_commits_this_round || 0) >= globalState.cohort_team_count ? 'rgba(16,185,129,0.08)' : 'rgba(99,102,241,0.06)',
              borderBottom: '1px solid rgba(0,229,195,0.06)',
            }}>
              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Round {roundNumber} Status
              </span>
              <span style={{ fontSize: '0.68rem', fontWeight: 800, color: (globalState?.team_commits_this_round || 0) >= globalState.cohort_team_count ? '#10b981' : '#6366f1' }}>
                {globalState?.team_commits_this_round || 0}/{globalState.cohort_team_count} committed {(globalState?.team_commits_this_round || 0) >= globalState.cohort_team_count ? '✓' : '...'}
              </span>
            </div>
          )}

          {/* Executive Mailbox / Decision History (tabbed) */}
          <div className={styles.rightMailbox} style={{ flex: railExpanded ? undefined : '0 0 auto', minHeight: railExpanded ? undefined : 0 }}>
            {/* Sticky Tab Header */}
            <div style={{
              position: 'sticky', top: 0, zIndex: 10,
              display: 'flex', gap: 0,
              background: 'var(--bg-sidebar, #ffffff)',
              borderBottom: '1px solid var(--border-subtle, #e2e8f0)',
            }}>
              {/* Rail tabs are cohort-gated (2026-07-20). Each tab maps to a
                  player-visibility key so a facilitator can strip the rail back
                  for introductory cohorts. `decisions` reuses the existing
                  decision_history key — one surface, one switch. Fail-open: an
                  unconfigured cohort shows everything, exactly as before. */}
              {[
                { id: 'mailbox', vis: 'rail_mailbox', label: '📬 Mailbox', color: '#3b82f6', badge: unreadCount > 0 ? unreadCount : null },
                { id: 'decisions', vis: 'decision_history', label: '📜 Decisions', color: '#6366f1', badge: (!commitResults && hasDecision) ? '⏳' : null },
                { id: 'engines', vis: 'rail_engines', label: '🌎 Engines', color: '#10b981', badge: (events && Object.keys(events).length > 0 && !commitResults) ? '•' : null },
                { id: 'climate', vis: 'rail_climate', label: '🌡️ Climate', color: '#38bdf8', badge: null },
              ].filter(tab => isPlayerVisible(tab.vis)).map(tab => {
                const isActive = rightPanelTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => {
                      if (!railExpanded) { setRightPanelTab(tab.id); setRailExpanded(true); }
                      else if (rightPanelTab === tab.id) setRailExpanded(false);
                      else setRightPanelTab(tab.id);
                    }}
                    title={railExpanded && rightPanelTab === tab.id ? 'Collapse panel' : `Open ${tab.id}`}
                    style={{
                      flex: 1, padding: '8px 6px', cursor: 'pointer',
                      fontSize: '0.66rem', fontWeight: isActive ? 800 : 600, textTransform: 'uppercase',
                      letterSpacing: '0.04em', border: 'none',
                      background: isActive ? `${tab.color}15` : 'transparent',
                      color: isActive ? tab.color : '#64748b',
                      borderBottom: `3px solid ${isActive ? tab.color : 'transparent'}`,
                      transition: 'all 0.15s ease',
                      position: 'relative',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 3,
                    }}
                  >
                    {tab.label}
                    {tab.badge && (
                      <span style={{
                        fontSize: typeof tab.badge === 'number' ? '0.6rem' : '0.5rem',
                        fontWeight: 800,
                        background: typeof tab.badge === 'number' ? '#f87171' : `${tab.color}25`,
                        color: typeof tab.badge === 'number' ? '#fff' : tab.color,
                        padding: typeof tab.badge === 'number' ? '1px 5px' : '0 3px',
                        borderRadius: 3,
                        minWidth: typeof tab.badge === 'number' ? 14 : 'auto',
                        textAlign: 'center',
                        animation: typeof tab.badge === 'number' ? 'pulse 1.5s ease-in-out infinite' : 'none',
                      }}>
                        {tab.badge}
                      </span>
                    )}
                  </button>
                );
              })}
              <button
                onClick={() => setRailExpanded(e => !e)}
                title={railExpanded ? 'Collapse panel' : 'Expand panel'}
                aria-expanded={railExpanded}
                style={{
                  flex: '0 0 auto', width: 26, border: 'none', cursor: 'pointer',
                  background: 'transparent', color: 'var(--neutral, #64748b)',
                  fontSize: '0.7rem', fontWeight: 800,
                }}
              >
                {railExpanded ? '▾' : '▸'}
              </button>
            </div>

            {/* Tab Content */}
            <div key={rightPanelTab} className={styles.tabContentEnter} style={{ padding: '8px 12px', overflowY: 'auto', flex: 1, display: railExpanded ? undefined : 'none' }}>
              {rightPanelTab === 'mailbox' ? (
                <>
                  <div className={styles.mailboxTitle}>
                    Round {roundNumber}
                    {unreadCount > 0 && <span className={styles.mailboxBadge}>{unreadCount}</span>}
                  </div>
                  {currentMessages.map((msg, idx) => {
                    // NF-2: Determine severity for visual differentiation
                    const persona = getPersona(msg);
                    const isCritical = persona === BOARD_PERSONAS.crisis ||
                      (msg.title || '').toLowerCase().includes('crisis') ||
                      (msg.title || '').toLowerCase().includes('removal') ||
                      (msg.title || '').toLowerCase().includes('ultimatum');
                    const isWarning = persona === BOARD_PERSONAS.legal ||
                      (msg.title || '').toLowerCase().includes('warning') ||
                      (msg.title || '').toLowerCase().includes('alert') ||
                      (msg.title || '').toLowerCase().includes('risk');
                    const severityClass = isCritical ? styles.msgSeverityCritical
                      : isWarning ? styles.msgSeverityWarning
                      : '';
                    return (
                    <div
                      key={msg.id || `msg-${idx}`}
                      className={`${styles.feedItem} ${severityClass}`}
                      onClick={() => { onMarkRead?.(msg.id); setExpandedMessage(msg); }}
                      style={{ cursor: 'pointer', opacity: msg.read ? 0.6 : 1 }}
                    >
                      {/* Improvement #4.2: AI Personas */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 2 }}>
                        <span style={{ fontSize: '0.7rem' }}>{persona.avatar}</span>
                        <span style={{ fontSize: '0.68rem', fontWeight: 600, color: persona.color }}>{persona.name}</span>
                        {isCritical && <span style={{ fontSize: '0.55rem', fontWeight: 800, color: '#ef4444', background: 'rgba(239,68,68,0.1)', padding: '1px 5px', borderRadius: 3, letterSpacing: '0.06em' }}>URGENT</span>}
                        {isWarning && !isCritical && <span style={{ fontSize: '0.55rem', fontWeight: 800, color: '#f59e0b', background: 'rgba(245,158,11,0.1)', padding: '1px 5px', borderRadius: 3, letterSpacing: '0.06em' }}>ALERT</span>}
                      </div>
                      <strong style={{ fontSize: '0.68rem', color: '#0f172a' }}>{msg.title}</strong>
                      <p style={{ margin: '2px 0 0', fontSize: '0.65rem', color: '#334155' }}>{msg.body?.substring(0, 120)}...</p>
                    </div>
                    );
                  })}
                  {currentMessages.length === 0 && (
                    <div className={styles.feedItem} style={{ color: '#94a3b8', textAlign: 'center' }}>No messages this round</div>
                  )}

                  {/* W-B: Market Intelligence — client-derived rival press +
                      rating letters (rivalIntel.js). Not messages: no read
                      state, never counted in unreadCount. */}
                  <MarketIntel history={history} roundNumber={roundNumber} />

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
              ) : rightPanelTab === 'decisions' ? (
                <DecisionHistory historyData={historyData} />
              ) : rightPanelTab === 'climate' ? (
                <TCFDScenarioDashboard sessionId={sim?.sessionId || sim?.session_id} globalState={globalState} compact />
              ) : (
                <EngineWidgetsPanel sessionId={sim?.sessionId || sim?.session_id} globalState={globalState} commitResults={commitResults} />
              )}
            </div>
          </div>

          {/* Market Reality Feed — with Consequence Traceability */}
          {/* V-C (player v2, V-1): single-open rail — while a tab panel
              (Mailbox / Decisions / Engines / Climate) is expanded, the feed
              folds to a one-line header so the rail shows ONE primary at a
              time. Active alerts still surface regardless (escalation keeps
              its rights). */}
          {!isPlayerVisible('market_reality_feed') ? null : railExpanded && !activeAlert ? (
            <div style={{ flex: '0 0 auto', padding: '4px 10px' }}>
              <button
                onClick={() => setRailExpanded(false)}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                  padding: '8px 12px', borderRadius: 8, cursor: 'pointer',
                  border: '1px solid #1e293b', background: 'transparent',
                  color: '#94a3b8', fontSize: '0.72rem', fontWeight: 700, textAlign: 'left',
                }}
                title="Collapse the open panel to bring the feed back"
              >
                <span>📡</span>
                <span style={{ flex: 1 }}>Market Reality Feed ({marketEvents.length})</span>
                <span>▸</span>
              </button>
            </div>
          ) : (
          <div className={styles.rightMarket}>
            <MarketRealityFeed
              items={marketEvents}
              activeAlert={activeAlert}
              traceConsequence={traceConsequence}
              traceTooltipIdx={traceTooltipIdx}
              onTraceHover={setTraceTooltipIdx}
              roundTier={roundTier}
              onDismissAlert={dismissActiveAlert}
            />
          </div>
          )}

          {/* V-A (player v2, V-3): the retrospect (What Happened This Round +
              Road Not Taken) moved to the RESULTS STAGE, where the learning
              lands — mid-decision it was regret-bait outranking the current
              choice. The rail keeps a one-line recap link that reveals it on
              demand (reading room, not ambient). CEO Diary stays here. */}
          <div className={styles.sectionDivider} />
          <div style={{
            flex: '1 1 auto', overflowY: 'auto', padding: '8px 10px',
          }}>
            {(roundNumber > 1 || !!commitResults) && (
              <div style={{ marginBottom: 6 }}>
                <button
                  onClick={() => setRailRecapOpen(v => !v)}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                    padding: '8px 12px', borderRadius: 8, cursor: 'pointer',
                    border: '1px solid #1e293b', background: 'transparent',
                    color: '#94a3b8', fontSize: '0.72rem', fontWeight: 700, textAlign: 'left',
                  }}
                  aria-expanded={railRecapOpen}
                >
                  <span>🔍</span>
                  <span style={{ flex: 1 }}>Round recap — what happened & the road not taken</span>
                  <span style={{ transition: 'transform 0.2s', transform: railRecapOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}>▾</span>
                </button>
                {railRecapOpen && (
                  <div style={{ marginTop: 6 }}>
                    <EngineEventsPanel globalState={globalState} roundEvents={events || commitResults?.events} sections="retrospect" />
                  </div>
                )}
              </div>
            )}
            <EngineEventsPanel globalState={globalState} roundEvents={events || commitResults?.events} sections="rest" />
            {/* SI-2+: Autonomous Stakeholder Agents Panel */}
            {(() => {
              const evs = events || commitResults?.events || {};
              // Prefer the LIVE persisted summary (globalState.agent_summary, now
              // sent through the dashboard every round with the fully-mapped fields
              // name/icon/stage/tolerance/max_tolerance) so the escalation ladder
              // reflects the accumulated state; fall back to the post-commit summary.
              const aaSummary = (Array.isArray(globalState?.agent_summary) && globalState.agent_summary.length)
                ? globalState.agent_summary
                : (evs.agent_summary || []);
              const aaDiag = evs.autonomous_agents || {};
              if (aaSummary.length > 0 || (aaDiag.agent_actions || []).length > 0) {
                return (
                  <StakeholderAgentPanel
                    agentSummary={aaSummary}
                    agentActions={aaDiag.agent_actions || []}
                    cascadesFired={aaDiag.cascades_fired || []}
                    interferenceActive={aaDiag.interference_active || []}
                    roundNumber={roundNumber}
                  />
                );
              }
              return null;
            })()}

            {/* Gap 3: Facilitator Annotations — visible to students when enabled */}
            <PlayerAnnotations
              sessionId={sim?.sessionId || sim?.session_id}
              roundNumber={roundNumber}
            />
          </div>

          {/* Phase 3.6: Synergy Tracker (R7+ Integration tier) */}
          <SynergyTracker
            globalState={globalState}
            roundNumber={roundNumber}
            workforceReady={globalState?.workforce_readiness}
          />
          {/* V-B (player v2, V-4): the rail's "Re-enter Focus Mode" button
              removed — three re-entry affordances (this, the left FOCUS MODE
              pill, the stepper) answered the same intent. The left pill and
              the stepper remain; handleFocusReenter is unchanged. */}

          {/* ── Commit Footer (compact) ── */}
          <div className={styles.rightCommit} style={{ flex: '0 0 auto', padding: '8px 12px', background: '#0f172a', borderTop: '1px solid #1e293b', display: 'flex', flexDirection: 'column', gap: 6 }}>
            {/* #1: Decision Confidence Nudge — reflective prompt card */}
            <div className={styles.reflectivePrompt}>
              <span style={{ fontSize: '0.85rem', flexShrink: 0 }}>💭</span>
              <span style={{ fontSize: '0.68rem', fontWeight: 600, color: '#94a3b8', fontStyle: 'italic', lineHeight: 1.4 }}>
                {{
                  foundation: 'Are you building a strong foundation for the next 7 rounds?',
                  crisis: 'Is this a reactive fix or a proactive strategy?',
                  integration: 'Are your BUs working together or competing for resources?',
                  finale: 'This is your final decision. The Board will ask why.',
                }[roundTier]}
              </span>
            </div>
            
            {/* Decision Quality Meter */}
            {(() => {
              const allocTotal = Object.values(allocations).reduce((a, b) => a + b, 0);
              let quality = 0;
              if (hasReadBriefing) quality += 10;
              if (isPillarMode ? Object.keys(pillarSelections || {}).length > 0 : !!decisionChoice) quality += 40;
              quality += Math.min(50, (allocTotal / (csfPool || 1)) * 50);
              return (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: '100%' }}>
                  <span style={{ fontSize: '0.68rem', textTransform: 'uppercase', color: '#94a3b8', whiteSpace: 'nowrap' }}>Ready</span>
                  <div style={{ flex: 1, height: 4, background: '#1e293b', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ width: `${quality}%`, height: '100%', background: quality > 80 ? '#10b981' : quality > 40 ? '#f59e0b' : '#ef4444', transition: 'background 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease, opacity 0.3s ease, transform 0.3s ease' }} />
                  </div>
                </div>
              );
            })()}
            
            
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, width: '100%' }}>
              {/* What-If Sandbox Mode — preview decision impacts.
                  Gated by the cohort's player-visibility toggle (what_if_simulator,
                  disabled by default); fail-open so a missing map still shows it. */}
              {!commitResults && options?.length > 0 && isPlayerVisible('what_if_simulator') && (
                <WhatIfSandbox
                  options={options}
                  businessUnits={businessUnits}
                  globalState={globalState}
                  events={events}
                  decisionChoice={decisionChoice}
                  allocations={allocations}
                  csfPool={csfPool}
                  roundNumber={roundNumber}
                  isDark={isDark}
                />
              )}
              {stageWarning && (
                <span style={{ color: '#ef4444', fontSize: '0.68rem', fontWeight: 700, textAlign: 'center' }}>🔒 {stageWarning}</span>
              )}
              {/* UX-04: Over-allocation warning */}
              {(Object.values(allocations || {}).reduce((s, v) => s + v, 0) > (csfPool || 0)) && (csfPool > 0) && !commitResults && (
                <div style={{
                  padding: '4px 8px', borderRadius: 5, background: 'rgba(239,68,68,0.12)',
                  border: '1px solid rgba(239,68,68,0.35)', fontSize: '0.68rem', color: '#fca5a5',
                  textAlign: 'center', lineHeight: 1.3, width: '100%',
                }}>
                  ⚠️ Over-allocated by {fmtCurrency(Object.values(allocations || {}).reduce((s, v) => s + v, 0) - (csfPool || 0))}
                </div>
              )}
              {/* ── Projected Impact Widget ── */}
              {projectedCost !== 0 && !commitResults && (
                <div className={`${styles.projectedImpactWidget} ${projectedCost > 0 ? styles.impactNegative : styles.impactPositive}`} style={{ padding: '3px 8px' }}>
                  <span className={styles.projectedImpactLabel} style={{ fontSize: '0.68rem' }}>
                    {projectedCost > 0 ? '📉 Cost' : '📈 Gain'}
                  </span>
                  <span className={`${styles.projectedImpactValue} ${projectedCost > 0 ? styles.lossValue : styles.gainValue}`} style={{ color: projectedCost > 0 ? '#f87171' : '#4ade80', fontSize: '0.7rem' }}>
                    {projectedCost > 0 ? '↓' : '↑'} {fmtCurrency(Math.abs(projectedCost))}
                  </span>
                </div>
              )}
              {/* #5: Smart Commit Button — reflects decision quality */}
              {(() => {
                const allocTotal = Object.values(allocations || {}).reduce((s, v) => s + v, 0);
                const overAllocated = allocTotal > (csfPool || 0) && (csfPool > 0);
                const fullyReady = hasReadBriefing && hasDecision && allocTotal > 0;
                const partialReady = hasDecision && allocTotal <= 0;
                // Facilitator-paced advance: the current round's commit is
                // locked until the facilitator's timer fires or they advance
                // the round. Decisions and allocations still save normally.
                const roundLocked = globalState?.cohort_round_locked === true;
                const nextUnlockAt = globalState?.cohort_next_unlock_at;
                let unlockLabel = null;
                if (roundLocked && nextUnlockAt) {
                  try {
                    unlockLabel = new Date(nextUnlockAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                  } catch { unlockLabel = null; }
                }
                if (roundLocked && !commitResults) {
                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      <button
                        className={styles.commitBtn}
                        style={{ width: '100%', height: 34, fontSize: '0.75rem', background: '#1e293b', border: '1px solid #475569', opacity: 0.85, cursor: 'not-allowed' }}
                        disabled
                      >
                        🔒 Round Locked{unlockLabel ? ` — opens ${unlockLabel}` : ''}
                      </button>
                      <div style={{ fontSize: '0.62rem', color: '#94a3b8', textAlign: 'center' }}>
                        Your decisions are saved. {unlockLabel
                          ? `The round opens at ${unlockLabel}.`
                          : 'The facilitator will advance the round.'}
                      </div>
                    </div>
                  );
                }
                // Mandatory-quiz gate: this round's quiz must be taken before the
                // player can commit. Server-enforced too — this is the UX mirror.
                const quizGate = globalState?.quiz_gate;
                if (quizGate?.blocked && !commitResults) {
                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      <button
                        className={styles.commitBtn}
                        style={{ width: '100%', height: 34, fontSize: '0.75rem', background: '#3730a3', border: '1px solid #4f46e5', opacity: 0.9, cursor: 'not-allowed' }}
                        disabled
                      >
                        🧩 Complete the Quiz First
                      </button>
                      <div style={{ fontSize: '0.62rem', color: '#a5b4fc', textAlign: 'center' }}>
                        This round requires the quiz{quizGate.required_title ? ` “${quizGate.required_title}”` : ''}. Open 📚 Resources to take it, then commit.
                      </div>
                    </div>
                  );
                }
                const btnStyle = commitResults
                  ? { background: '#1e293b', borderColor: '#334155' }
                  : overAllocated
                    ? { background: 'linear-gradient(135deg, #991b1b, #7f1d1d)', borderColor: '#ef4444', boxShadow: '0 0 12px rgba(239,68,68,0.25)' }
                    : fullyReady
                      ? { background: 'linear-gradient(135deg, #059669, #047857)', borderColor: '#10b981', boxShadow: '0 0 12px rgba(16,185,129,0.3)' }
                      : partialReady
                        ? { background: 'linear-gradient(135deg, #92400e, #78350f)', borderColor: '#f59e0b' }
                        : { background: '#1e293b', borderColor: '#475569' };
                const btnIcon = commitResults ? '✅' : overAllocated ? '⚠️' : fullyReady ? '▶' : partialReady ? '⏳' : '🔒';
                return (
                  <motion.button
                    className={`${styles.commitBtn} ${commitResults ? styles.commitBtnDone : ''}`}
                    style={{ width: '100%', height: 34, fontSize: '0.75rem', ...btnStyle, border: `1px solid ${btnStyle.borderColor}`, transition: 'background 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease, opacity 0.3s ease, transform 0.3s ease' }}
                    disabled={!!commitResults}
                    onClick={() => {
                      if (!commitResults) {
                        if (!hasDecision) { showStageWarning('Select a Strategic Option before committing your turn.'); return; }
                        if (allocTotal <= 0) { showStageWarning('Allocate capital across your business units before committing.'); return; }
                        setShowPredictionModal(true);
                      }
                    }}
                    whileHover={{ scale: commitResults ? 1 : 1.02 }}
                    whileTap={{ scale: commitResults ? 1 : 0.98 }}
                  >
                    {btnIcon} {commitResults ? 'Committed' : overAllocated ? 'Over-Allocated' : fullyReady ? 'Commit Decisions' : partialReady ? 'Allocate Capital' : 'Complete Steps'}
                  </motion.button>
                );
              })()}
            </div>
          </div>
        </aside>

        {/* ── #8: Keyboard Shortcut Cheatsheet (portaled to body) ── */}
        {showKeyboardHelp && typeof document !== 'undefined' && createPortal(
          <div
            onClick={() => setShowKeyboardHelp(false)}
            style={{
              position: 'fixed', inset: 0, zIndex: 99998,
              background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <div
              onClick={e => e.stopPropagation()}
              style={{
                background: 'rgba(15,23,42,0.95)', border: '1px solid rgba(94,234,212,0.2)',
                borderRadius: 16, padding: '24px 32px', minWidth: 320, maxWidth: 400,
                boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
              }}
            >
              <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#5eead4', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                ⌨ Keyboard Shortcuts
                <span onClick={() => setShowKeyboardHelp(false)} style={{ marginLeft: 'auto', cursor: 'pointer', color: '#64748b', fontSize: '1rem' }}>✕</span>
              </div>
              {[
                { keys: ['1', '2', '3'], desc: 'Select Strategic Option A / B / C' },
                { keys: ['1', '–', String(businessUnits?.length || 4)], desc: 'Investigate BU 1–' + (businessUnits?.length || 4) },
                { keys: ['Esc'], desc: 'Back to Overview (Glance mode)' },
                { keys: ['?'], desc: 'Toggle this help panel' },
              ].map(({ keys, desc }, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', borderBottom: i < 3 ? '1px solid rgba(148,163,184,0.08)' : 'none' }}>
                  <div style={{ display: 'flex', gap: 4, minWidth: 80 }}>
                    {keys.map((k, j) => (
                      <kbd key={j} style={{
                        padding: '2px 8px', borderRadius: 4, fontSize: '0.65rem', fontWeight: 700,
                        background: 'rgba(94,234,212,0.1)', border: '1px solid rgba(94,234,212,0.2)',
                        color: '#5eead4', fontFamily: 'JetBrains Mono, monospace',
                      }}>{k}</kbd>
                    ))}
                  </div>
                  <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>{desc}</span>
                </div>
              ))}
              <div style={{ marginTop: 12, fontSize: '0.68rem', color: '#475569', textAlign: 'center' }}>
                Press <kbd style={{ padding: '1px 5px', borderRadius: 3, background: 'rgba(148,163,184,0.1)', border: '1px solid rgba(148,163,184,0.15)', color: '#64748b', fontFamily: 'JetBrains Mono, monospace' }}>?</kbd> or click outside to close
              </div>
            </div>
          </div>,
          document.body
        )}

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


      {/* Balance Sheet full modal — for Focus Mode BS card clicks */}
      {resultsBsModalOpen && commitResults && (
        <BalanceSheetModal
          balanceSheet={commitResults.globalState?.balance_sheet || commitResults.events?.balance_sheet || null}
          isOpen={resultsBsModalOpen}
          onClose={() => setResultsBsModalOpen(false)}
          fmtCurrency={fmtCurrency}
        />
      )}

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
                {decisionChoice && <div>Strategy: <span className="strategy-tip-trigger" style={{ position: 'relative', cursor: 'help', borderBottom: '1px dashed rgba(241,245,249,0.3)' }}><strong style={{ color: '#f1f5f9' }}>{decisionChoice.replace('option_', 'Option ').toUpperCase()} — {options[decisionChoice]?.title || ''}</strong><span className="strategy-tip-box" style={{
                  position: 'absolute', top: 'calc(100% + 8px)', left: 0,
                  width: '280px', maxWidth: '70vw',
                  padding: '12px 16px', borderRadius: '12px',
                  background: 'linear-gradient(135deg, rgba(15,23,42,0.98), rgba(30,41,59,0.98))',
                  border: '1px solid rgba(99,102,241,0.25)',
                  boxShadow: '0 16px 40px rgba(0,0,0,0.55), 0 0 0 1px rgba(99,102,241,0.08)',
                  backdropFilter: 'blur(16px)',
                  fontSize: '0.73rem', lineHeight: 1.6, color: '#cbd5e1',
                  fontWeight: 400, pointerEvents: 'none', opacity: 0,
                  transform: 'translateY(-4px)', transition: 'opacity 0.2s ease, transform 0.2s ease', zIndex: 100,
                }}><div style={{ fontWeight: 700, color: '#a5b4fc', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{options[decisionChoice]?.title || ''}</div>{options[decisionChoice]?.description || ''}</span></span></div>}
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
                {/* Per-BU breakdown — folded in from the retired 'Review Your
                    Decisions' modal (17111b0) so this single screen carries its
                    full review content. REINSTATED 2026-07-20: the squashed
                    session commit 1ef5c98 dropped it along with Go Back & Edit,
                    leaving players unable to review or change decisions from
                    this screen — the exact regression 17111b0's message
                    promised would not happen. */}
                {Object.entries(allocations || {}).filter(([, v]) => v > 0).map(([buId, v]) => {
                  const bu = (businessUnits || []).find(b => b.bu_id === buId);
                  return (
                    <div key={buId} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#94a3b8', paddingLeft: 10 }}>
                      <span>· {bu?.name || buId}</span>
                      <span style={{ fontFamily: 'var(--font-numeral)', color: '#cbd5e1' }}>{fmtCurrency(v)}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className={styles.predictionActions}>
              {/* Go Back & Edit — closes WITHOUT committing so the player can
                  adjust allocations/strategy. This is the review escape hatch;
                  Skip & Commit is NOT a substitute (it commits immediately). */}
              <button
                className={styles.predictionSkip}
                onClick={() => { setShowPredictionModal(false); }}
              >
                ← Go Back &amp; Edit
              </button>
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
                          {dRep !== 0 && (
                            <span style={{ fontSize: '0.75rem', fontWeight: 800, marginLeft: 8, color: dRep >= 0 ? '#4ade80' : '#ef4444' }}>
                              {dRep >= 0 ? '▲' : '▼'} {Math.abs(dRep).toFixed(0)}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className={styles.resultCard}>
                        <div className={styles.resultCardIcon}>🏭</div>
                        <div className={styles.resultCardLabel}>CO₂ Emissions</div>
                        <div className={styles.resultCardValue}>
                          {newCarbon.toLocaleString()} t
                          {dCarbon !== 0 && (
                            <span style={{ fontSize: '0.75rem', fontWeight: 800, marginLeft: 8, color: dCarbon <= 0 ? '#4ade80' : '#ef4444' }}>
                              {dCarbon > 0 ? '▲' : '▼'} {Math.abs(dCarbon).toLocaleString()} t
                            </span>
                          )}
                        </div>
                      </div>
                      {/* Balance Sheet Health Card — clickable to open full IFRS balance sheet */}
                      {(() => {
                        const bsData = commitResults.globalState?.balance_sheet || commitResults.events?.balance_sheet;
                        if (!bsData) return null;
                        const bs = typeof bsData === 'object' && bsData.net_assets != null ? bsData : {};
                        const netAssets = bs.net_assets || 0;
                        const deRatio = bs.debt_to_equity || 0;
                        const cStatus = bs.covenant_status || 'green';
                        const fmtMShort = (v) => `$${((v || 0) / 1_000_000).toFixed(0)}M`;
                        const cColors = { green: '#4ade80', amber: '#fbbf24', red: '#ef4444', breached: '#dc2626' };
                        const cIcons = { green: '🟢', amber: '🟡', red: '🔴', breached: '🚨' };
                        return (
                          <div
                            className={styles.resultCard}
                            style={{ borderTop: `2px solid ${cColors[cStatus] || '#38bdf8'}`, cursor: 'pointer' }}
                            onClick={() => setResultsBsModalOpen(true)}
                            title="Click to view full Balance Sheet"
                          >
                            <div className={styles.resultCardIcon}>📊</div>
                            <div className={styles.resultCardLabel}>Balance Sheet</div>
                            <div className={styles.resultCardValue} style={{ fontSize: '0.85rem' }}>
                              {fmtMShort(netAssets)} net
                            </div>
                            <div style={{ display: 'flex', gap: 6, marginTop: 4, fontSize: '0.68rem', justifyContent: 'center' }}>
                              <span style={{ color: deRatio < 2.0 ? '#4ade80' : '#f59e0b', fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
                                D/E: {deRatio.toFixed(2)}×
                              </span>
                              <span style={{ color: cColors[cStatus] || '#38bdf8' }}>
                                {cIcons[cStatus] || '📊'} {cStatus}
                              </span>
                            </div>
                            <div style={{ fontSize: '0.58rem', color: '#64748b', marginTop: 5, fontWeight: 600, letterSpacing: '0.03em' }}>
                              🔍 Click to expand
                            </div>
                          </div>
                        );
                      })()}
                    </>
                  );
                })()}
              </div>

              {/* Trend Sparklines */}
              {historyData.length > 1 && (() => {
                const avgNCD = businessUnits.length > 0
                  ? businessUnits.reduce((s, bu) => s + (bu.natural_capital_debt || 0), 0) / businessUnits.length
                  : 0;
                const stockData = [
                  { year: 'IPO', yearLabel: 'IPO', price: IPO_PRICE },
                  ...historyData.map(h => ({
                    year: h.year,
                    yearLabel: h.yearLabel,
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
                  <div style={{
                    display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.6rem',
                    marginBottom: '1rem',
                  }}>
                    {[
                      { key: 'treasury', label: 'Treasury Trend', color: '#e2e8f0', fmt: (v) => fmtCurrency(v) },
                      { key: 'ebitda', label: 'EBITDA Trend', color: '#e2e8f0', fmt: (v) => fmtCurrency(v) },
                      { key: 'reputation', label: 'Reputation Trend', color: '#e2e8f0', fmt: (v) => v?.toFixed(0) },
                      { key: 'tco2e', label: 'CO₂ Emissions Trend', color: '#e2e8f0', fmt: (v) => `${(v || 0).toLocaleString()} t` },
                    ].map(({ key, label, color, fmt }) => {
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
                          {key === 'ebitda' && (
                            <span style={{ marginLeft: 6, fontSize: '0.56rem', fontWeight: 600, color: '#64748b', textTransform: 'none', letterSpacing: 0 }}>· ⋯ Nordhaven</span>
                          )}
                        </div>
                        <ResponsiveContainer width="100%" height={72}>
                          <AreaChart data={historyData} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                            <defs>
                              <linearGradient id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#e2e8f0" stopOpacity={0.18} />
                                <stop offset="95%" stopColor="#e2e8f0" stopOpacity={0.02} />
                              </linearGradient>
                            </defs>
                            <XAxis dataKey="yearLabel" tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                            <YAxis hide domain={yDomain} />
                            <Tooltip
                              contentStyle={{ fontSize: '0.72rem', borderRadius: 6, border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                              formatter={(v, name) => [fmt(v), name === 'competitor_ebitda' ? 'Nordhaven Group (est.)' : label.replace(' Trend', '')]}
                              labelFormatter={(l) => `${l}`}
                            />
                            <Area type="monotone" dataKey={key} stroke="#e2e8f0" strokeWidth={1.5} fill={`url(#grad-${key})`} dot={{ r: 2.5, fill: '#e2e8f0', strokeWidth: 0 }} activeDot={{ r: 4, fill: '#fff', stroke: '#94a3b8', strokeWidth: 1 }} />
                            {/* W-B (W2a): Nordhaven ghost line — dashed, no fill, display-only */}
                            {key === 'ebitda' && (
                              <Area type="monotone" dataKey="competitor_ebitda" stroke="#64748b" strokeDasharray="4 3" strokeWidth={1.2} fill="none" fillOpacity={0} dot={false} activeDot={{ r: 3, fill: '#64748b', strokeWidth: 0 }} connectNulls />
                            )}
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    );})}
                    
                    {/* Stock Price Trend Card */}
                    <div className={styles.resultCard} style={{
                      padding: '0.5rem 0.6rem 0.3rem',
                    }}>
                      <div style={{
                        display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                        fontSize: '0.68rem', fontWeight: 700,
                        textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.2rem',
                      }} className={styles.resultCardLabel}>
                        <span>📈 Stock Price</span>
                        <span style={{ fontFamily: 'JetBrains Mono, monospace' }}>
                          ${latestPrice.toFixed(2)}
                        </span>
                      </div>
                      <ResponsiveContainer width="100%" height={72}>
                        <AreaChart data={stockData} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                          <defs>
                            <linearGradient id="grad-stock-res" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#e2e8f0" stopOpacity={0.18} />
                              <stop offset="95%" stopColor="#e2e8f0" stopOpacity={0.02} />
                            </linearGradient>
                          </defs>
                          <XAxis dataKey="yearLabel" tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                          <YAxis hide domain={[Math.max(0, minP - pad), maxP + pad]} />
                          <Tooltip
                            contentStyle={{ fontSize: '0.72rem', borderRadius: 6, border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                            formatter={(v) => [`$${v.toFixed(2)}`, 'Stock Price']}
                            labelFormatter={(l) => `${l}`}
                          />
                          <ReferenceLine y={IPO_PRICE} stroke="#475569" strokeDasharray="3 3" />
                          <Area type="monotone" dataKey="price" stroke="#e2e8f0" strokeWidth={1.5} fill="url(#grad-stock-res)" dot={{ r: 2.5, fill: '#e2e8f0', strokeWidth: 0 }} activeDot={{ r: 4, fill: '#fff', stroke: '#94a3b8', strokeWidth: 1 }} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
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
                  {commitResults.events.covenant_surcharge > 0 && (
                    <div className={styles.resultsEventItem}>📊 Covenant Penalty: -{fmtCurrency(commitResults.events.covenant_surcharge)} interest surcharge on breached debt covenants</div>
                  )}
                  {commitResults.events.covenant_warning && (
                    <div className={styles.resultsEventItem}>⚠️ {typeof commitResults.events.covenant_warning === 'string' ? commitResults.events.covenant_warning : 'Debt covenant under pressure — review leverage'}</div>
                  )}
                  {commitResults.events.esg_adjusted_wacc && commitResults.events.esg_adjusted_wacc.adjusted_wacc > 0.08 && (
                    <div className={styles.resultsEventItem}>📊 ESG-WACC at {(commitResults.events.esg_adjusted_wacc.adjusted_wacc * 100).toFixed(1)}% — lender covenant triggers tightening due to ESG risk premium</div>
                  )}
                  {commitResults.events.employer_brand_opex_penalty && (
                    <div className={styles.resultsEventItem}>👥 Talent Crisis: Employer brand at {(commitResults.events.employer_brand_opex_penalty.employer_brand_score || 0).toFixed(0)}/100 — +{((commitResults.events.employer_brand_opex_penalty.multiplier || 0) * 100).toFixed(1)}% OPEX surcharge across all {commitResults.events.employer_brand_opex_penalty.affected_bus || '?'} business units</div>
                  )}
                </div>
              )}

              {/* #7: Post-Commit Delta Card — "What Changed" summary */}
              {commitResults?.globalState && (
                <div style={{
                  padding: '12px 16px', borderRadius: 10, marginBottom: '1rem',
                  background: 'linear-gradient(135deg, rgba(94,234,212,0.06), rgba(99,102,241,0.04))',
                  border: '1px solid rgba(94,234,212,0.15)',
                }}>
                  <div style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#5eead4', marginBottom: 8 }}>
                    📊 Round {roundNumber} Impact Summary
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
                    {[
                      { label: 'Treasury', prev: globalState?.corporate_treasury || treasury, post: commitResults.globalState.corporate_treasury, fmt: fmtCurrency },
                      { label: 'Reputation', prev: globalState?.group_reputation || reputation, post: commitResults.globalState.group_reputation, fmt: v => v?.toFixed(1) },
                      { label: 'Carbon', prev: globalState?.tco2e_emissions || tco2e, post: commitResults.globalState.tco2e_emissions, fmt: v => `${(v||0).toFixed(0)}t`, invert: true },
                      { label: 'EBITDA', prev: ebitda, post: commitResults.globalState.historical_ebitda, fmt: fmtCurrency },
                    ].map(({ label, prev, post, fmt, invert }) => {
                      const d = (post || 0) - (prev || 0);
                      const positive = invert ? d < 0 : d > 0;
                      return (
                        <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.65rem' }}>
                          <span style={{ color: '#94a3b8', fontWeight: 600 }}>{label}</span>
                          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: d === 0 ? '#64748b' : positive ? '#4ade80' : '#f87171' }}>
                            {d > 0 ? '+' : ''}{fmt(d)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {/* PHASE-3: Risk Intelligence Layer — post-commit analysis */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                {isPlayerVisible('risk_radar') && (
                <RiskRadar
                  buStates={commitResults.businessUnits || businessUnits}
                  allocations={allocations}
                  tippingState={commitResults.events?.systemic_tipping?.tipping_state || systemicTipping?.tipping_state || {}}
                />
                )}
                <ConsequencePreview
                  selectedOption={decisionChoice || (Object.keys(pillarSelections || {}).length > 0 ? 'multi_pillars' : null)}
                  optionConfig={decisionChoice
                    ? (options[decisionChoice] || {})
                    : (() => {
                        // Build synthetic optionConfig from multi_toggles pillar selections
                        const sels = pillarSelections || {};
                        const areas = pillarConfig?.areas || {};
                        if (Object.keys(sels).length === 0) return {};
                        const mergedImpacts = {};
                        const labels = [];
                        for (const [areaKey, optKey] of Object.entries(sels)) {
                          const opt = areas[areaKey]?.options?.[optKey];
                          if (!opt) continue;
                          labels.push(opt.title || optKey);
                          // Merge impacts from each selected pillar option
                          const imp = opt.impacts || {};
                          for (const [k, v] of Object.entries(imp)) {
                            if (typeof v === 'number') {
                              mergedImpacts[k] = (mergedImpacts[k] || 0) + v;
                            }
                          }
                          // Also fold in top-level cost as a treasury impact
                          if (opt.cost && !imp.treasury) {
                            mergedImpacts.treasury = (mergedImpacts.treasury || 0) + opt.cost;
                          }
                        }
                        return { label: labels.join(' + '), impacts: mergedImpacts };
                      })()
                  }
                  currentState={commitResults.globalState || globalState}
                  buStates={commitResults.businessUnits || businessUnits}
                  tippingState={commitResults.events?.systemic_tipping || {}}
                  whatIfResult={null}
                />
              </div>
              {pedToggles.consequence_map_enabled !== false && isPlayerVisible('consequence_timeline') && (
                <ConsequenceTimeline
                  currentRound={roundNumber}
                  activeFlags={commitResults.globalState?.active_event_flags || globalState?.active_event_flags || {}}
                  foreshadowingSignals={commitResults.events?.foreshadowing_signals || foreshadowingSignals}
                />
              )}

              {/* ── Inline Peer Performance (Results Overlay) ── */}
              {peerLeaderboard.length > 0 && (
                <div style={{
                  background: 'linear-gradient(135deg, rgba(99,102,241,0.06), rgba(168,85,247,0.04))',
                  border: '1px solid rgba(99,102,241,0.2)',
                  borderRadius: 12, padding: '1rem 1.2rem', marginBottom: '1rem',
                }}>
                  <div style={{
                    fontSize: '0.68rem', fontWeight: 800, letterSpacing: '0.1em',
                    textTransform: 'uppercase', marginBottom: '0.8rem',
                    display: 'flex', alignItems: 'center', gap: '0.4rem',
                    color: '#818cf8',
                  }}>
                    <span>📊</span> Cohort Leaderboard — How You Compare
                  </div>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                        <th style={{ textAlign: 'left', padding: '4px 6px', color: '#64748b', fontWeight: 700, fontSize: '0.6rem', textTransform: 'uppercase' }}>#</th>
                        <th style={{ textAlign: 'left', padding: '4px 6px', color: '#64748b', fontWeight: 700, fontSize: '0.6rem', textTransform: 'uppercase' }}>Team</th>
                        <th style={{ textAlign: 'right', padding: '4px 6px', color: '#64748b', fontWeight: 700, fontSize: '0.6rem', textTransform: 'uppercase' }}>Treasury</th>
                        <th style={{ textAlign: 'right', padding: '4px 6px', color: '#64748b', fontWeight: 700, fontSize: '0.6rem', textTransform: 'uppercase' }}>Rep</th>
                        <th style={{ textAlign: 'right', padding: '4px 6px', color: '#64748b', fontWeight: 700, fontSize: '0.6rem', textTransform: 'uppercase' }}>CO₂</th>
                        <th style={{ textAlign: 'center', padding: '4px 6px', color: '#64748b', fontWeight: 700, fontSize: '0.6rem', textTransform: 'uppercase' }}>Trend</th>
                      </tr>
                    </thead>
                    <tbody>
                      {peerLeaderboard.map(team => (
                        <tr key={team.rank} style={{
                          background: team.isYou ? 'rgba(99,102,241,0.1)' : 'transparent',
                          borderBottom: '1px solid rgba(255,255,255,0.04)',
                        }}>
                          <td style={{ padding: '6px', fontSize: '0.78rem' }}>
                            {team.rank <= 3 ? ['🥇', '🥈', '🥉'][team.rank - 1] : team.rank}
                          </td>
                          <td style={{
                            padding: '6px', fontWeight: team.isYou ? 800 : 600,
                            color: team.isYou ? '#a5b4fc' : '#e2e8f0',
                          }}>
                            {team.name}
                            {team.isYou && <span style={{
                              marginLeft: 6, fontSize: '0.68rem', fontWeight: 800,
                              background: 'rgba(99,102,241,0.3)', color: '#c7d2fe',
                              padding: '1px 6px', borderRadius: 4,
                            }}>YOU</span>}
                          </td>
                          <td style={{ padding: '6px', textAlign: 'right', fontWeight: 700, color: '#4ade80', fontFamily: "'JetBrains Mono', monospace" }}>
                            ${((team.treasury || 0) / 1_000_000).toFixed(1)}M
                          </td>
                          <td style={{ padding: '6px', textAlign: 'right', color: '#cbd5e1' }}>
                            {team.reputation?.toFixed(0) ?? '—'}
                          </td>
                          <td style={{ padding: '6px', textAlign: 'right', color: '#94a3b8', fontFamily: "'JetBrains Mono', monospace" }}>
                            {(team.co2 || 0).toLocaleString()}t
                          </td>
                          <td style={{
                            padding: '6px', textAlign: 'center', fontSize: '0.85rem',
                            color: team.trend === '↑' ? '#4ade80' : team.trend === '↓' ? '#f87171' : '#94a3b8',
                          }}>{team.trend}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {peerLoading && (
                <div style={{ textAlign: 'center', fontSize: '0.7rem', color: '#64748b', padding: '8px 0' }}>Loading peer data…</div>
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
                {roundNumber === 6 && pedToggles.r6_revelation_enabled !== false && (
                  <R6RevelationPanel
                    onVisible={() => setR6Pending(true)}
                    onMicroDecision={(data) => {
                      setR6Done(true);
                      fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/global-settings`, {
                        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ [`journey_r6_response_${sim?.sessionId || sim?.session_id}`]: data }),
                      }).catch(() => {});
                    }} />
                )}
                {/* Journey: R7 Budget Allocation variant */}
                {roundNumber === 7 && pedToggles.r7_budget_allocation_enabled !== false && (
                  <BudgetAllocationPanel
                    onVisible={() => setR7Pending(true)}
                    onAllocate={(allocs) => {
                      setR7Done(true);
                      fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/global-settings`, {
                        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ [`journey_r7_allocs_${sim?.sessionId || sim?.session_id}`]: allocs }),
                      }).catch(() => {});
                    }} />
                )}
                {/* Journey: R8 Stakeholder Tribunal variant */}
                {roundNumber === 8 && pedToggles.r8_tribunal_enabled !== false && (
                  <StakeholderTribunal
                    onVisible={() => setR8Pending(true)}
                    onResponses={(responses) => {
                      setR8Done(true);
                      fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/global-settings`, {
                        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ [`journey_r8_responses_${sim?.sessionId || sim?.session_id}`]: responses }),
                      }).catch(() => {});
                    }} />
                )}
              </div>

              {/* MP-02 + Journey Gate: block advance until teams committed AND minigames done */}
              {(() => {
                const teamCount = globalState?.cohort_team_count || 0;
                const commitsCount = globalState?.team_commits_this_round || 0;
                const isMultiTeam = teamCount > 1;
                // Free-advance auto-release: the barrier also lifts when the
                // facilitator's timeout lapses or Force Advance is pressed
                // (cohort_advance_unblocked), so one absent team can't deadlock
                // everyone.
                const unblocked = globalState?.cohort_advance_unblocked === true;
                const allCommitted = commitsCount >= teamCount || unblocked;
                const deadlineAt = globalState?.cohort_advance_deadline;
                let secsLeft = null;
                if (deadlineAt) {
                  const ms = new Date(deadlineAt).getTime() - Date.now();
                  secsLeft = ms > 0 ? Math.ceil(ms / 1000) : 0;
                }

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
                        {commitsCount}/{teamCount} teams committed
                        {secsLeft != null
                          ? ` — auto-advances in ~${secsLeft}s`
                          : ' — cannot advance yet'}
                      </div>
                    </div>
                  );
                }

                if (journeyBlocksAdvance) {
                  return (
                    <div style={{
                      padding: '14px 16px', borderRadius: 10, textAlign: 'center',
                      background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.35)',
                    }}>
                      <div style={{ fontSize: '1.2rem', marginBottom: 6 }}>⚠️</div>
                      <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#f59e0b', marginBottom: 4 }}>
                        Complete the Activity Above First
                      </div>
                      <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>
                        Submit your response in the panel above to unlock Round {commitResults.newRoundNumber}
                      </div>
                    </div>
                  );
                }

                return (
                  <>
                    {/* B2: Reflection box — optional, never blocks advance */}
                    <div style={{
                      padding: '10px 12px', borderRadius: 10, marginBottom: 8,
                      background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.18)',
                    }}>
                      <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#a5b4fc', marginBottom: 6, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                        💭 Quick Reflection (optional)
                      </div>
                      <textarea
                        value={reflectionText}
                        onChange={(e) => setReflectionText(e.target.value)}
                        placeholder="What did you predict vs. what actually happened — and why?"
                        rows={2}
                        style={{
                          width: '100%', resize: 'vertical', fontSize: '0.78rem', lineHeight: 1.5,
                          padding: '8px 10px', borderRadius: 8, border: '1px solid rgba(148,163,184,0.15)',
                          background: 'rgba(15,23,42,0.4)', color: 'var(--text-primary, #f1f5f9)',
                          fontFamily: 'inherit', outline: 'none',
                        }}
                        onFocus={(e) => e.target.style.borderColor = 'rgba(99,102,241,0.5)'}
                        onBlur={(e) => {
                          e.target.style.borderColor = 'rgba(148,163,184,0.15)';
                          // Persist to ref on blur
                          if (reflectionText.trim()) {
                            reflectionsRef.current[roundNumber] = reflectionText.trim();
                          }
                        }}
                      />
                    </div>
                    <motion.button
                      className={styles.advanceBtnLarge}
                      onClick={() => {
                        // Save reflection before advancing
                        if (reflectionText.trim()) {
                          reflectionsRef.current[roundNumber] = reflectionText.trim();
                        }
                        setReflectionText('');
                        onAdvance();
                      }}
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                    >
                      ⏩ Advance to Round {commitResults.newRoundNumber}
                    </motion.button>
                  </>
                );
              })()}
              {/* Balance Sheet full modal — triggered from results card */}
              <BalanceSheetModal
                balanceSheet={commitResults.globalState?.balance_sheet || commitResults.events?.balance_sheet || null}
                isOpen={resultsBsModalOpen}
                onClose={() => setResultsBsModalOpen(false)}
                fmtCurrency={fmtCurrency}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

