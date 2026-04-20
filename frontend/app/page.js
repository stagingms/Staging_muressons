'use client';

import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import styles from './page.module.css';
import dynamic from 'next/dynamic';

import ExecutiveCockpit from './components/ExecutiveCockpit';
import BoardroomShowdown from './components/BoardroomShowdown';
import SustainabilityBalancedScorecard from './components/SustainabilityBalancedScorecard';
import GameOverSummary from './components/GameOverSummary';
import StakeholderMapModal from './components/StakeholderMapModal';
import CFOOverrideModal from './components/CFOOverrideModal';
const DoubleMaterialityMatrix = dynamic(() => import('./components/DoubleMaterialityMatrix'), { ssr: false });
const JoinCohortModal = dynamic(() => import('./components/JoinCohortModal'), { ssr: false });
const UsernamePromptModal = dynamic(() => import('./components/UsernamePromptModal'), { ssr: false });
import ResourceSidebar from './components/ResourceSidebar';
import RoundBriefing from './components/RoundBriefing';
import CrisisAlerts from './components/CrisisAlerts';
import useSimulation from './hooks/useSimulation';

// ── New Improvement Components ──────────────────────────────────
import RoundChecklist from './components/RoundChecklist';
import GlossaryPanel from './components/GlossaryPanel';
import OnboardingWalkthrough from './components/OnboardingWalkthrough';
import MarketTicker from './components/MarketTicker';
import CountdownTimer from './components/CountdownTimer';
import AchievementBadges from './components/AchievementBadges';
import AIAdvisor from './components/AIAdvisor';
import PeerComparison from './components/PeerComparison';
import PlayerAnalytics from './components/PlayerAnalytics';
import soundManager from './utils/soundManager';

// ── Advanced Climate Engine modules (lazy-loaded) ─────────────
const GreenFundBidding = dynamic(() => import('./components/GreenFundBidding'), { ssr: false });
const RegulatoryShockModule = dynamic(() => import('./components/RegulatoryShockModule'), { ssr: false });
const VCMPortfolioBuilder = dynamic(() => import('./components/VCMPortfolioBuilder'), { ssr: false });
const Scope3ProcurementOptimizer = dynamic(() => import('./components/Scope3ProcurementOptimizer'), { ssr: false });
const InsettingROICalculator = dynamic(() => import('./components/InsettingROICalculator'), { ssr: false });
const PolicyWarRoom = dynamic(() => import('./components/PolicyWarRoom'), { ssr: false });
const ESGRefinancingSimulator = dynamic(() => import('./components/ESGRefinancingSimulator'), { ssr: false });
const CircularStrategyDashboard = dynamic(() => import('./components/CircularStrategyDashboard'), { ssr: false });

// ── Seed data (mirrors backend baseline) ──────────────────────
const SEED_GLOBAL = {
  corporate_treasury: 50_000_000,
  group_reputation: 50,
  synergy_multiplier: 1.0,
  cost_of_capital: 0.05,
  active_event_flags: {},
};

const SEED_BUS = [
  {
    bu_id: 'pharma', name: 'Muressons Pharma', revenue_base: 18_000_000,
    opex_base: 11_500_000, natural_capital_debt: 0, social_license_score: 55,
    reputation_score: 52, governance_risk_score: 15, water_dependency: 82,
    carbon_intensity: 45, risk_factors: {}
  },
  {
    bu_id: 'electronics', name: 'Muressons Electronics', revenue_base: 16_500_000,
    opex_base: 10_800_000, natural_capital_debt: 0, social_license_score: 48,
    reputation_score: 50, governance_risk_score: 20, water_dependency: 58,
    carbon_intensity: 72, risk_factors: {}
  },
  {
    bu_id: 'consumer_goods', name: 'Muressons Consumer Goods', revenue_base: 10_500_000,
    opex_base: 7_800_000, natural_capital_debt: 0, social_license_score: 52,
    reputation_score: 53, governance_risk_score: 10, water_dependency: 65,
    carbon_intensity: 38, risk_factors: {}
  },
  {
    bu_id: 'software', name: 'Muressons Software', revenue_base: 8_500_000,
    opex_base: 4_200_000, natural_capital_debt: 0, social_license_score: 60,
    reputation_score: 58, governance_risk_score: 8, water_dependency: 12,
    carbon_intensity: 28, risk_factors: {}
  },
];

const SEED_BUS_HEALTHCARE = [
  {
    bu_id: 'hospitals', name: 'Muressons Hospitals', revenue_base: 22_000_000,
    opex_base: 18_500_000, natural_capital_debt: 0, social_license_score: 65,
    reputation_score: 55, governance_risk_score: 25, water_dependency: 85,
    carbon_intensity: 70, risk_factors: {}
  },
  {
    bu_id: 'clinics', name: 'Primary Care Clinics', revenue_base: 12_500_000,
    opex_base: 9_800_000, natural_capital_debt: 0, social_license_score: 70,
    reputation_score: 60, governance_risk_score: 15, water_dependency: 40,
    carbon_intensity: 35, risk_factors: {}
  },
  {
    bu_id: 'specialised_care', name: 'Specialised Care', revenue_base: 15_000_000,
    opex_base: 10_500_000, natural_capital_debt: 0, social_license_score: 55,
    reputation_score: 65, governance_risk_score: 20, water_dependency: 60,
    carbon_intensity: 50, risk_factors: {}
  },
  {
    bu_id: 'telehealth', name: 'Digital Health', revenue_base: 8_000_000,
    opex_base: 4_200_000, natural_capital_debt: 0, social_license_score: 50,
    reputation_score: 45, governance_risk_score: 10, water_dependency: 10,
    carbon_intensity: 25, risk_factors: {}
  },
];

// Round narrative titles for context
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

export default function CockpitPage() {
  const sim = useSimulation();
  const [teamName, setTeamName] = useState('');
  const [isMatrixOpen, setIsMatrixOpen] = useState(false);
  const [showDesktop, setShowDesktop] = useState(true);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);

    // Handle ?session= URL param for facilitator impersonation
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const sessionParam = params.get('session');
      if (sessionParam && !sim.sessionId) {
        sim.setSessionId && sim.setSessionId(sessionParam); // Fallback for raw setSessionId if exists
        sim.fetchDashboard(sessionParam).then(() => {
          sim.fetchRoundConfig && sim.fetchRoundConfig(sim.roundNumber || 1);
        }).catch(() => {});
      } else if (!sim.sessionId) {
        const cachedId = localStorage.getItem('muressons_session_id');
        if (cachedId) {
          sim.resumeSession(cachedId).catch(() => {
            console.error('Failed to resume session');
            localStorage.removeItem('muressons_session_id');
          });
        }
      }
    }
  }, []);

  // Live state or seed fallback
  const globalState = sim.globalState || SEED_GLOBAL;
  const _tempBus = sim.businessUnits?.length ? sim.businessUnits : null;
  const isHealthcare = _tempBus ? _tempBus.some(b => b.bu_id === 'hospitals') : (globalState?.industry === 'healthcare');
  
  const businessUnits = _tempBus || (isHealthcare ? SEED_BUS_HEALTHCARE : SEED_BUS);
  const roundNumber = sim.roundNumber || 1;

  // Synergy score for R10 gate (multiplier × 100)
  const synergyScore = Math.round((globalState.synergy_multiplier || 1.0) * 100);

  // ── Investment allocations ─────────────────────────────────
  const [allocations, setAllocations] = useState({});

  const csfPool = useMemo(
    () => {
      // Free capital allowance is strictly 20% of corporate treasury
      return (globalState?.corporate_treasury || SEED_GLOBAL.corporate_treasury) * 0.20;
    },
    [globalState?.corporate_treasury]
  );

  // ── Decision modal state ──────────────────────────────────
  const [modalOpen, setModalOpen] = useState(false);
  const [decisionChoice, setDecisionChoice] = useState(null);
  const [stakeholderDone, setStakeholderDone] = useState(false);
  const [showStakeholderMap, setShowStakeholderMap] = useState(false);

  // Reset transient minigame states when impersonating different cohorts in the same tab
  useEffect(() => {
    setStakeholderDone(false);
    setShowStakeholderMap(false);
  }, [sim.sessionId]);

  // Resource sidebar state
  const [resourceSidebarOpen, setResourceSidebarOpen] = useState(false);
  const [hasNewResources, setHasNewResources] = useState(false);

  // ── New Improvement States ──────────────────────────────────
  const [glossaryOpen, setGlossaryOpen] = useState(false);
  const [achievementsOpen, setAchievementsOpen] = useState(false);
  const [aiAdvisorOpen, setAiAdvisorOpen] = useState(false);
  const [peerComparisonOpen, setPeerComparisonOpen] = useState(false);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(true);

  // Decision paradigm state
  const [decisionParadigm, setDecisionParadigm] = useState('legacy_abc');
  const [pillarSelections, setPillarSelections] = useState({});
  const [pillarConfig, setPillarConfig] = useState(null);

  // Pre-commit review modal
  const [showReviewModal, setShowReviewModal] = useState(false);

  // R2 BU selection for Strategic Pillars mode
  const [r2BuSelection, setR2BuSelection] = useState(null); // { selected_bu, bu_label }
  const [csrdDone, setCsrdDone] = useState(false);

  // Detect paradigm from session (poll every 8s for facilitator changes)
  useEffect(() => {
    if (!sim.sessionId || sim.sessionId === 'demo') return;
    let cancelled = false;
    const fetchParadigm = () => {
      fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/simulations/${sim.sessionId}/paradigm`)
        .then(r => r.json())
        .then(data => { if (!cancelled) setDecisionParadigm(data.decision_paradigm || 'legacy_abc'); })
        .catch(() => {});
    };
    fetchParadigm(); // immediate first check
    const interval = setInterval(fetchParadigm, 8000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [sim.sessionId]);

  // Fetch pillar config for multi_toggles
  useEffect(() => {
    if (decisionParadigm !== 'multi_toggles') return;
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/simulations/pillar-config/${roundNumber}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => setPillarConfig(data))
      .catch(() => setPillarConfig(null));
  }, [decisionParadigm, roundNumber]);

  // Fetch R2 BU selection for multi_toggles
  useEffect(() => {
    if (decisionParadigm !== 'multi_toggles' || roundNumber !== 2 || !sim.sessionId || sim.sessionId === 'demo') return;
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/${sim.sessionId}/r2-bu-selection`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setR2BuSelection(data); })
      .catch(() => {});
  }, [decisionParadigm, roundNumber, sim.sessionId]);

  // Check for new resources on round change
  useEffect(() => {
    if (!sim.sessionId || sim.sessionId === 'demo') return;
    const checkResources = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/simulations/${sim.sessionId}/resources`);
        if (res.ok) {
          const data = await res.json();
          setHasNewResources((data.new_this_round || []).length > 0);
        }
      } catch (e) { /* silent */ }
    };
    checkResources();
  }, [sim.sessionId, roundNumber]);

  // CFO Override states
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [pendingDecisions, setPendingDecisions] = useState({});
  const [cfoErrorMsg, setCfoErrorMsg] = useState("");

  const [lastSavedAt, setLastSavedAt] = useState(null);

  // ── Save State Hydration ──────────────────────────────────
  // Pre-load saved allocations and decisions if they exist
  useEffect(() => {
    if (globalState?.saved_allocations && Object.keys(allocations).length === 0) {
      setAllocations(globalState.saved_allocations);
    }
    if (globalState?.saved_decision_choice && !decisionChoice) {
      setDecisionChoice(globalState.saved_decision_choice);
    }
  }, [globalState?.saved_allocations, globalState?.saved_decision_choice]);

  // Block alert state
  const [blockAlert, setBlockAlert] = useState(null);

  // Derived state ─────────────────────────────────────────
  // Open crisis modal when leaving desktop after round changes
  useEffect(() => {
    if (sim.sessionId && sim.roundChanged && !sim.gameOver) {
      setShowDesktop(true);
    }
  }, [sim.sessionId, sim.roundChanged, sim.gameOver]);

  useEffect(() => {
    // Only auto-open the decision modal after the desktop has been dismissed
    if (sim.sessionId && !showDesktop && !sim.gameOver) {
      if (sim.roundChanged || roundNumber === 1 && !decisionChoice && !modalOpen && !hasSubmittedMatrix) {
        // Optionally you can re-open it if needed, but for now we just let it open on round start
      }
    }
  }, [showDesktop]);

  const handleProceedFromDesktop = () => {
    setShowDesktop(false);
    // Nothing auto-opens — player clicks the Stakeholder Map / CSRD / Decision Tab explicitly
  };

  const handleDecision = useCallback((optionId) => {
    setDecisionChoice(optionId);
    setModalOpen(false);
  }, []);

  // ── Commit turn ───────────────────────────────────────────
  const handleCommitTurn = useCallback(async () => {
    if (!sim.sessionId) {
      await sim.startSession(teamName.trim() || 'Team Alpha');
      return;
    }

    const decisions = businessUnits.map((bu) => ({
      bu_id: bu.bu_id,
      investment_ratio: csfPool > 0 ? Math.min((allocations[bu.bu_id] || 0) / csfPool, 1.0) : 0,
      capex_allocated: Math.max(1, allocations[bu.bu_id] || 1),
      choice_selected: decisionParadigm === 'multi_toggles' ? '' : (decisionChoice || 'option_b'),
      decision_node_id: `round_${roundNumber}_${bu.bu_id}`,
      time_to_decision_seconds: 0,
      team_consensus: 'majority',
      pillar_decisions: decisionParadigm === 'multi_toggles' ? pillarSelections : null,
    }));

    try {
      await sim.commitTurn({
        dividends_paid: 0,
        crisis_severity: 0,
        imitation_decay_rate: 0.05,
        decisions,
      });
      soundManager.commit();
      setAllocations({});
      setDecisionChoice(null);
      setShowOverrideModal(false);
      setPendingDecisions(null);
    } catch (err) {
      soundManager.error();
      console.error('Commit failed:', err);
      if (err.message && err.message.includes('CFO Override')) {
        setCfoErrorMsg(err.message);
        setPendingDecisions(decisions);
        setShowOverrideModal(true);
      }
    }
  }, [sim, businessUnits, allocations, csfPool, decisionChoice, roundNumber]);

  const handleSaveDecisions = useCallback(async () => {
    if (!sim.sessionId) return;
    try {
      await sim.saveDecisions({
        allocations,
        decision_choice: decisionChoice,
      });
      setLastSavedAt(new Date());
    } catch (err) {
      console.error("Failed to save decisions:", err);
    }
  }, [sim, allocations, decisionChoice]);

  // Periodic Auto-Save
  useEffect(() => {
    if (!sim.sessionId || sim.gameOver || (!decisionChoice && !globalState?.pillar_selections) || Object.keys(allocations).length === 0) return;
    const interval = setInterval(() => {
      handleSaveDecisions();
    }, 30_000);
    return () => clearInterval(interval);
  }, [sim.sessionId, sim.gameOver, handleSaveDecisions, decisionChoice, globalState, allocations]);

  const handleForceOverride = useCallback(async () => {
    if (!pendingDecisions) return;
    try {
      await sim.commitTurn({
        dividends_paid: 0,
        crisis_severity: 0,
        imitation_decay_rate: 0.05,
        decisions: pendingDecisions,
        force_override_cfo: true, // <-- Trigger explicit override!
      });
      setShowOverrideModal(false);
      setPendingDecisions(null);
      setAllocations({});
      setDecisionChoice(null);
    } catch (err) {
      console.error("Force override still failed:", err);
    }
  }, [sim, pendingDecisions]);

  // ── Game Over → Scorecard → BoardroomShowdown → Done ─────────
  const [gameOverPhase, setGameOverPhase] = useState('scorecard'); // 'scorecard' | 'boardroom' | 'done'
  const [boardroomDone, setBoardroomDone] = useState(false);

  // Note: no effect that auto-skips phases — the flow is:
  //   game ends → scorecard shown → player clicks Proceed → boardroom → player submits → done
  // boardroomDone prevents re-entering the boardroom when reviewing the scorecard after completion.

  // ── Advanced Climate Engine — completed module tracking ───────
  // Persisted per-player per-session in localStorage so players resume where they left off.
  // Different players in the same session each have independent progress records.
  const [completedModules, setCompletedModules] = useState({});

  // Restore completed modules from localStorage when session + player identity are known
  useEffect(() => {
    const sid = sim.sessionId;
    const pid = sim.playerId || (typeof window !== 'undefined' ? localStorage.getItem('muressons_playerId') : null);
    if (!sid || !pid) return;
    const key = `ace_modules_${sid}_${pid}`;
    try {
      const saved = localStorage.getItem(key);
      if (saved) setCompletedModules(JSON.parse(saved));
      else setCompletedModules({}); // new player on this session — start fresh
    } catch { setCompletedModules({}); }
  }, [sim.sessionId, sim.playerId]);

  const markModuleDone = useCallback((round) => {
    const sid = sim.sessionId;
    const pid = sim.playerId || (typeof window !== 'undefined' ? localStorage.getItem('muressons_playerId') : null);
    setCompletedModules(prev => {
      const next = { ...prev, [round]: true };
      if (sid && pid) {
        try { localStorage.setItem(`ace_modules_${sid}_${pid}`, JSON.stringify(next)); } catch { }
      }
      return next;
    });
  }, [sim.sessionId, sim.playerId]);

  // ── Advanced Climate Engine: read mode directly from backend ──
  // Fetched independently of session globalState so it works at all rounds.
  const [isAdvancedClimate, setIsAdvancedClimate] = useState(false);
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/global-settings`);
        if (!res.ok) return;
        const d = await res.json();
        setIsAdvancedClimate(d.simulation_mode === 'advanced_climate');
      } catch { /* offline or not configured — stay false */ }
    };
    check();
    const id = setInterval(check, 15_000); // re-poll every 15s to pick up live Switchboard changes
    return () => clearInterval(id);
  }, [sim.sessionId]);

  // ── Auto-clear lock after 30s to let user retry ─────────────
  useEffect(() => {
    if (!sim.roundLocked) return;
    const timer = setTimeout(() => {
      sim.setRoundLocked(false);
    }, 30_000);
    return () => clearTimeout(timer);
  }, [sim.roundLocked]);

  const hasSubmittedMatrix = csrdDone || (globalState && (globalState.materiality_budget_allocated != null || globalState.csrd_completed));
  const hasCompletedStakeholderMap = globalState?.stakeholder_map_completed === true || stakeholderDone;
  // In multi_toggles mode, at least one pillar must be selected
  const hasDecision = decisionParadigm === 'multi_toggles'
    ? Object.keys(pillarSelections).length > 0
    : !!decisionChoice;
  const isCommitBlocked = (roundNumber === 2 && !hasSubmittedMatrix) || (roundNumber === 1 && !hasCompletedStakeholderMap) || !hasDecision || Object.keys(allocations).length === 0;

  // Mailbox messages for the new cockpit (local crisis + facilitator messages)
  // Messages ACCUMULATE across rounds so previous rounds are available in accordion
  const [mailboxMessages, setMailboxMessages] = useState([]);
  const [facilitatorMessages, setFacilitatorMessages] = useState([]);
  const addedRoundsRef = useRef(new Set());

  const CRISES_ESG = {
    1: '📋 ESG Foundation Audit: Board demands an initial ESG materiality assessment.',
    2: '⚖️ Double Materiality Gate: CFO requires all investments to pass a double materiality test.',
    3: '🏭 Scope 3 Disruption: Major Scope 3 emissions discovered in supply chains.',
    4: '⚡ ESG Contagion: Sector-wide scrutiny from competitor ESG headlines.',
    5: '🌪️ Climate Physical Risk: Severe climate event threatens facilities.',
    6: '🤖 AI Ethics Scandal: Software AI hiring tool found to exhibit bias.',
    7: '♻️ Circular Economy: New EU regulations require circular compliance.',
    8: '💧 Blue Water Stress: Primary watershed reclassified as critically stressed.',
    9: '✊ Just Transition: Automation layoffs triggering labor unrest.',
    10: '📢 Activist Ultimatum: Major activist fund demands structural change.',
  };

  const CRISES = CRISES_ESG;

  // Append crisis briefing for current + all previous rounds (accumulate, never reset)
  useEffect(() => {
    const newMsgs = [];
    for (let r = 1; r <= roundNumber; r++) {
      if (addedRoundsRef.current.has(r)) continue;
      addedRoundsRef.current.add(r);
      const crisisText = CRISES[r];
      newMsgs.push({
        id: `briefing-r${r}`, round: r, type: 'narrative', title: 'Board Briefing',
        body: `Round ${r}: ${crisisText || 'Review the module mandate and make your decisions.'}`,
        read: r < roundNumber, // Mark previous rounds as read
      });
    }
    if (newMsgs.length > 0) {
      setMailboxMessages(prev => [...prev, ...newMsgs]);
    }
  }, [roundNumber, CRISES]);

  // Append engine event messages (talent penalties etc.) for current round
  useEffect(() => {
    setMailboxMessages(prev => {
      const msgs = [...prev];
      let changed = false;

      const addMsg = (id, title, body) => {
        if (!msgs.some(m => m.id === id)) {
          msgs.push({ id, round: roundNumber, type: 'alert', title, body, read: false });
          changed = true;
        }
      };

      if (sim.events?.talent_penalty_applied > 1) {
        addMsg(`evt-talent-${roundNumber}`, '🧠 Brain-Drain Alert', `Software OPEX inflated by ${((sim.events.talent_penalty_applied - 1) * 100).toFixed(1)}%`);
      }
      
      if (sim.events?.loan_interest_payment > 0) {
        const fmtCurrency = (v) => v >= 1_000_000 ? `$${(v/1_000_000).toFixed(1)}M` : `$${(v/1000).toFixed(0)}K`;
        addMsg(`evt-loan-${roundNumber}`, '🏦 Loan Interest Charged', `Interest payment of -${fmtCurrency(sim.events.loan_interest_payment)} applied this round.`);
      }

      if (sim.events?.strike_probabilities) {
        const highs = Object.entries(sim.events.strike_probabilities).filter(([, p]) => p > 0.3);
        if (highs.length) {
          const body = highs.map(([b, p]) => `${b} ${(p * 100).toFixed(0)}%`).join(', ');
          addMsg(`evt-strike-${roundNumber}`, '⚠️ Strike Risk Warning', `Elevated strike risk detected: ${body}`);
        }
      }

      return changed ? msgs : prev;
    });
  }, [roundNumber, sim.events]);

  // Merge facilitator messages into mailbox (deduplicate by id)
  useEffect(() => {
    if (!facilitatorMessages.length) return;
    setMailboxMessages(prev => {
      const existingIds = new Set(prev.map(m => m.id));
      const newFacMsgs = facilitatorMessages.filter(m => !existingIds.has(m.id));
      if (newFacMsgs.length === 0) return prev;
      return [...prev, ...newFacMsgs];
    });
  }, [facilitatorMessages]);

  // Poll facilitator messages from backend every 8s
  useEffect(() => {
    if (!sim.sessionId || sim.sessionId === 'demo') return;
    let cancelled = false;
    const poll = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/${sim.sessionId}/messages`);
        if (res.ok && !cancelled) {
          const data = await res.json();
          setFacilitatorMessages(data.messages || []);
        }
      } catch { /* non-critical */ }
    };
    poll(); // immediate first fetch
    const interval = setInterval(poll, 8000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [sim.sessionId]);

  const handleMailMarkRead = useCallback((id) => {
    setMailboxMessages(prev => prev.map(m => m.id === id ? { ...m, read: true } : m));
  }, []);

  // Crisis alert message injection callback
  const handleCrisisInject = useCallback((msg) => {
    setMailboxMessages(prev => {
      if (prev.some(m => m.id === msg.id)) return prev;
      return [...prev, msg];
    });
  }, []);

  // ── Keyboard Shortcuts (Improvement #1.3) ──────────────────
  useEffect(() => {
    const handler = (e) => {
      // Don't capture when typing in inputs
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;

      switch (e.key) {
        case '?': setGlossaryOpen(prev => !prev); break;
        case 'r': case 'R': if (!e.ctrlKey) { setResourceSidebarOpen(prev => !prev); setHasNewResources(false); } break;
        case 'a': case 'A': if (!e.ctrlKey) setAiAdvisorOpen(prev => !prev); break;
        case 'Escape': setGlossaryOpen(false); setAchievementsOpen(false); setPeerComparisonOpen(false); break;
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);



  if (sim.gameOver) {
    if (gameOverPhase === 'scorecard') {
      return (
        <SustainabilityBalancedScorecard
          data={sim.finalReport}
          businessUnits={sim.businessUnits}
          globalState={sim.globalState}
          history={sim.history}
          onProceed={!boardroomDone ? () => setGameOverPhase('boardroom') : undefined}
          onClose={() => setGameOverPhase('done')}
          onLogout={sim.logout}
        />
      );
    }
    if (gameOverPhase === 'boardroom') {
      return (
        <BoardroomShowdown
          data={sim.finalReport}
          sessionId={sim.sessionId}
          onComplete={() => { setBoardroomDone(true); setGameOverPhase('done'); }}
        />
      );
    }
    // 'done' — simulation is complete, with option to review scorecard
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #0f172a, #1e293b)',
        color: '#e2e8f0',
        fontFamily: 'Inter, system-ui, sans-serif',
        textAlign: 'center',
        padding: '2rem',
      }}>
        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🏁</div>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem' }}>Simulation Complete</h1>
        <p style={{ fontSize: '1rem', color: '#94a3b8', maxWidth: 500, lineHeight: 1.6 }}>
          {sim.finalReport?.profile_title || 'Final Assessment'} — Your strategic journey through 10 rounds is now concluded.
        </p>
        <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '1rem', marginBottom: '2rem' }}>
          Thank you for participating in the Muressons Global Command simulation.
        </p>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          <button
            onClick={() => setGameOverPhase('scorecard')}
            style={{
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              color: '#fff',
              border: 'none',
              padding: '0.8rem 2.5rem',
              borderRadius: '10px',
              fontSize: '1rem',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 4px 16px rgba(99, 102, 241, 0.3)',
              transition: 'transform 0.15s, box-shadow 0.15s',
            }}
            onMouseOver={(e) => { e.target.style.transform = 'scale(1.03)'; }}
            onMouseOut={(e) => { e.target.style.transform = 'scale(1)'; }}
          >
            📊 Review Final Scorecard
          </button>
          
          <button
            onClick={() => sim.logout()}
            style={{
              background: 'transparent',
              color: '#94a3b8',
              border: '1px solid #475569',
              padding: '0.8rem 2.5rem',
              borderRadius: '10px',
              fontSize: '1rem',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
            onMouseOver={(e) => { e.target.style.color = '#fff'; e.target.style.borderColor = '#94a3b8'; }}
            onMouseOut={(e) => { e.target.style.color = '#94a3b8'; e.target.style.borderColor = '#475569'; }}
          >
            👋 Logout & Exit
          </button>
        </div>
      </div>
    );
  }

  const handleOpenDecisionTab = () => {
    if (roundNumber === 1 && !hasCompletedStakeholderMap) {
      setBlockAlert("You must complete the Stakeholder Power/Interest Grid before you can access the Decision Tab. Click the ⚖️ Stakeholder Map button.");
    } else if (roundNumber === 2 && !hasSubmittedMatrix) {
      setBlockAlert("You must complete and submit the CSRD Materiality Assessment before you can access the Decision Tab.");
    } else {
      setModalOpen(true);
    }
  };

  const attemptCommitTurn = () => {
    if (roundNumber === 1 && !hasCompletedStakeholderMap) {
      setBlockAlert("You must complete the Stakeholder Power/Interest Grid before advancing. Click the ⚖️ Stakeholder Map button to begin.");
    } else if (roundNumber === 2 && !hasSubmittedMatrix) {
      setBlockAlert("You must complete and submit the CSRD Materiality Assessment before advancing.");
    } else if (!hasDecision) {
      setBlockAlert(decisionParadigm === 'multi_toggles'
        ? "You must select at least one strategic pillar action before committing your turn."
        : "You must select a strategic option from the Decision section before committing your turn.");
    } else if (Object.keys(allocations).length === 0) {
      setBlockAlert("You must allocate capital to at least one business unit before committing your turn.");
    } else {
      setShowReviewModal(true);
    }
  };


  // ── Main Cockpit ──────────────────────────────────────────
  if (!isHydrated) {
    return <div style={{ height: '100vh', width: '100%', background: '#1b2a4a' }} />;
  }

  return (
    <>
      {/* ── Persistent Logout Button (always visible) ── */}
      {sim.sessionId && (
        <button
          onClick={() => sim.logout()}
          title="Logout & Exit Simulation"
          style={{
            position: 'fixed',
            top: 12,
            right: 16,
            zIndex: 19000,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 14px',
            background: 'rgba(15, 23, 42, 0.75)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(248, 113, 113, 0.25)',
            borderRadius: 8,
            color: '#fca5a5',
            fontSize: '0.72rem',
            fontWeight: 700,
            fontFamily: "'Inter', system-ui, sans-serif",
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.background = 'rgba(127, 29, 29, 0.85)';
            e.currentTarget.style.color = '#fff';
            e.currentTarget.style.borderColor = '#f87171';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = 'rgba(15, 23, 42, 0.75)';
            e.currentTarget.style.color = '#fca5a5';
            e.currentTarget.style.borderColor = 'rgba(248, 113, 113, 0.25)';
          }}
        >
          🚪 Logout
        </button>
      )}

      {/* Join/Login overlay */}
      {!sim.sessionId && <div className={styles.joinOverlay}><JoinCohortModal sim={sim} /></div>}

      {/* Choose Username Overlay */}
      {sim.sessionId && !sim.username && sim.sessionId !== 'demo' && (
        <div style={{ position: 'relative', zIndex: 16000 }}>
          <UsernamePromptModal 
            userId={sim.playerId || (typeof window !== 'undefined' ? localStorage.getItem('muressons_playerId') : null) || sim.sessionId}
            role="player"
            onComplete={sim.setUsername}
          />
        </div>
      )}

      {/* Round Locked overlay */}
      {sim.roundLocked && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(27,42,74,0.92)',
          backdropFilter: 'blur(6px)', zIndex: 15000,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1.2rem',
          fontFamily: "'Inter', sans-serif",
        }}>
          <div style={{ fontSize: '3rem' }}>🔒</div>
          <h2 style={{ color: '#f1f5f9', fontSize: '1.4rem', fontWeight: 700, letterSpacing: '-0.01em', margin: 0 }}>Waiting for Facilitator</h2>
          <p style={{ color: '#94a3b8', fontSize: '0.85rem', maxWidth: 380, textAlign: 'center', lineHeight: 1.6, margin: 0 }}>
            Round {roundNumber} is locked. Your facilitator will unlock when the cohort is ready.
          </p>
          <button onClick={() => sim.setRoundLocked(false)} style={{
            padding: '8px 20px', background: 'transparent',
            border: '1px solid rgba(241,245,249,0.2)', borderRadius: 4, color: '#94a3b8', cursor: 'pointer',
            fontSize: '0.72rem', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase',
          }}>Dismiss</button>
        </div>
      )}

      {/* ═══ ADVANCED CLIMATE ENGINE: Module Overlays (fixed, z=21000) ═══ */}
      {isAdvancedClimate && !sim.gameOver && sim.sessionId && (() => {
        const round = sim.roundNumber;
        const sid = sim.sessionId;
        if (round === 3 && !completedModules[3]) return <GreenFundBidding sessionId={sid} onComplete={() => markModuleDone(3)} />;
        if (round === 4 && !completedModules[4]) return <RegulatoryShockModule sessionId={sid} onComplete={() => markModuleDone(4)} />;
        if (round === 5 && !completedModules[5]) return <VCMPortfolioBuilder sessionId={sid} onComplete={() => markModuleDone(5)} />;
        if (round === 6 && !completedModules[6]) return <Scope3ProcurementOptimizer sessionId={sid} onComplete={() => markModuleDone(6)} />;
        if (round === 7 && !completedModules[7]) return <InsettingROICalculator sessionId={sid} onComplete={() => markModuleDone(7)} />;
        if (round === 8 && !completedModules[8]) return <PolicyWarRoom sessionId={sid} onComplete={() => markModuleDone(8)} />;
        if (round === 9 && !completedModules[9]) return <ESGRefinancingSimulator sessionId={sid} onComplete={() => markModuleDone(9)} />;
        if (round === 10 && !completedModules[10]) return <CircularStrategyDashboard sessionId={sid} onComplete={() => markModuleDone(10)} />;
        return null;
      })()}

      {/* Desktop Intro → Round Briefing */}
      {sim.sessionId && showDesktop && (
        <RoundBriefing
          roundNumber={roundNumber}
          isHealthcare={isHealthcare}
          onProceed={handleProceedFromDesktop}
        />
      )}

      {/* ═══ NEW EXECUTIVE COCKPIT ═══ */}
      <ExecutiveCockpit
        sim={sim}
        globalState={globalState}
        businessUnits={businessUnits}
        isHealthcare={isHealthcare}
        roundNumber={roundNumber}
        history={sim.history}
        roundConfig={sim.roundConfig}
        decisionParadigm={decisionParadigm}
        actionToolbar={
          sim.sessionId && !sim.gameOver ? (
            <div id="tour-player-guides-target" style={{
              display: 'flex', flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center', gap: 6,
              fontFamily: 'Inter, sans-serif', width: '100%', padding: '6px',
            }}>
              {/* Paradigm Indicator */}
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
                    'un_sdg': 'UN SDG Edition'
                  }[decisionParadigm] || 'Simulation Active'}
                </span>
              </div>
              
              {[
                { icon: '📈', label: 'Leaderboard', shortcut: null, onClick: () => setPeerComparisonOpen(true) },
                { icon: '🏅', label: 'Badges', shortcut: null, onClick: () => setAchievementsOpen(true) },
                { icon: '🧠', label: 'Advisor', shortcut: 'A', onClick: () => setAiAdvisorOpen(true) },
                { icon: '📊', label: 'Analytics', shortcut: null, onClick: () => setAnalyticsOpen(true) },
                { icon: '📖', label: 'Glossary', shortcut: '?', onClick: () => setGlossaryOpen(true) },
                { icon: soundEnabled ? '🔊' : '🔇', label: soundEnabled ? 'Sound' : 'Muted', shortcut: null, onClick: () => { const v = soundManager.toggle(); setSoundEnabled(v); } },
                { icon: '👋', label: 'Log Out', shortcut: null, onClick: () => { if(window.confirm('Log out from the simulation? Your progress is saved.')) sim.logout(); } },
              ].map(btn => (
                <button
                  key={btn.label}
                  onClick={btn.onClick}
                  title={btn.shortcut ? `${btn.label} (${btn.shortcut})` : btn.label}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4,
                    padding: '4px 8px', borderRadius: 10,
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer',
                    transition: 'transform 0.15s, background 0.15s',
                    color: '#e2e8f0',
                  }}
                  onMouseOver={e => { e.currentTarget.style.transform = 'scale(1.05)'; e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; }}
                  onMouseOut={e => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; }}
                >
                  <span style={{ fontSize: '0.85rem' }}>{btn.icon}</span>
                  <span style={{ fontSize: '0.55rem', fontWeight: 700, letterSpacing: '0.02em', textTransform: 'uppercase' }}>{btn.label}</span>
                </button>
              ))}
            </div>
          ) : null
        }
        roundChecklist={
          sim.sessionId && !showDesktop && !sim.gameOver ? (
            <RoundChecklist
              roundNumber={roundNumber}
              hasReadBriefing={!showDesktop}
              hasCompletedStakeholderMap={hasCompletedStakeholderMap}
              hasSubmittedMatrix={hasSubmittedMatrix}
              hasDecision={hasDecision}
              hasAllocated={Object.keys(allocations).length > 0}
              hasCommitted={!!sim.commitResults}
            />
          ) : null
        }
        pillarSelections={pillarSelections}
        onPillarChange={setPillarSelections}
        onDecisionChoice={setDecisionChoice}
        decisionChoice={decisionChoice}
        onCommit={attemptCommitTurn}
        onAdvance={sim.advanceToNextRound}
        commitResults={sim.commitResults}
        isCommitBlocked={isCommitBlocked}
        events={sim.events}
        messages={mailboxMessages}
        onMarkRead={handleMailMarkRead}
        pillarConfig={pillarConfig}
        onOpenStakeholderMap={() => setShowStakeholderMap(true)}
        onOpenCSRD={() => setIsMatrixOpen(true)}
        hasCompletedStakeholderMap={hasCompletedStakeholderMap}
        hasSubmittedMatrix={hasSubmittedMatrix}
        stakeholderAccuracy={globalState?.stakeholder_map_accuracy}
        csfPool={csfPool}
        allocations={allocations}
        onAllocationsChange={setAllocations}
        onResourcesOpen={() => { setResourceSidebarOpen(true); setHasNewResources(false); }}
        hasAllocated={Object.keys(allocations).length > 0}
        hasReadBriefing={!showDesktop}
        onLogout={sim.logout}
        lastSavedAt={lastSavedAt}
      />

      {/* ═══ CRISIS ALERTS (auto-trigger + manual inject) ═══ */}
      {sim.sessionId && (
        <CrisisAlerts
          globalState={globalState}
          roundNumber={roundNumber}
          onInjectMessage={handleCrisisInject}
        />
      )}

      {/* ── Auto-Advance Notification ── */}
      {sim.autoAdvanceDetected && (
        <div style={{
          position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)',
          background: 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#fff',
          borderRadius: 10, padding: '12px 24px', zIndex: 20000,
          fontFamily: "'Inter', sans-serif", fontSize: '0.85rem', fontWeight: 700,
          boxShadow: '0 8px 24px rgba(245,158,11,0.35)',
          display: 'flex', alignItems: 'center', gap: '0.6rem',
          animation: 'slideDown 0.3s ease-out',
        }}>
          <span style={{ fontSize: '1.2rem' }}>⏰</span>
          Time expired — your turn was auto-committed with default choices. Now on Round {roundNumber}.
        </div>
      )}

      {/* ── Block Alert Modal ── */}
      {blockAlert && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(27,42,74,0.5)', zIndex: 10000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: "'Inter', sans-serif",
        }}>
          <div style={{
            background: '#fff', borderRadius: 6, padding: '1.8rem 2rem', maxWidth: 420,
            textAlign: 'center', boxShadow: '0 20px 60px rgba(0,0,0,0.12)',
            border: '1px solid #dce1e8',
          }}>
            <h2 style={{ color: '#b91c1c', margin: '0 0 0.8rem', fontSize: '1.1rem', fontWeight: 700 }}>🚨 Action Blocked</h2>
            <p style={{ color: '#4a5568', margin: 0, fontSize: '0.85rem', lineHeight: 1.6 }}>{blockAlert}</p>
            <button onClick={() => setBlockAlert(null)} style={{
              marginTop: '1.2rem', padding: '8px 0', background: '#1b2a4a', color: '#fff',
              border: 'none', borderRadius: 4, fontWeight: 700, cursor: 'pointer', width: '100%',
              fontSize: '0.72rem', letterSpacing: '0.06em', textTransform: 'uppercase',
            }}>Understood</button>
          </div>
        </div>
      )}

      {/* ── Pre-Commit Review Modal ── */}
      {showReviewModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.6)', zIndex: 10001,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: "'Inter', sans-serif", backdropFilter: 'blur(4px)',
        }}>
          <div style={{
            background: '#fff', borderRadius: 12, padding: '2rem 2.2rem', maxWidth: 520, width: '90%',
            boxShadow: '0 25px 60px rgba(0,0,0,0.18)',
            border: '1px solid #e2e8f0', maxHeight: '85vh', overflow: 'auto',
          }}>
            <h2 style={{ color: '#0f172a', margin: '0 0 0.3rem', fontSize: '1.15rem', fontWeight: 800 }}>📋 Review Your Decisions</h2>
            <p style={{ color: '#64748b', margin: '0 0 1.2rem', fontSize: '0.78rem' }}>Round {roundNumber} — Confirm before submitting to the board.</p>

            {/* Strategic Decision Summary */}
            <div style={{
              background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
              padding: '1rem 1.2rem', marginBottom: '1rem',
            }}>
              <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#6b7280', marginBottom: '0.6rem' }}>
                {decisionParadigm === 'multi_toggles' ? '🎛️ Strategic Pillar Selections' : '📋 Strategic Decision'}
              </div>

              {decisionParadigm === 'multi_toggles' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {pillarConfig?.areas && Object.entries(pillarConfig.areas).map(([areaKey, area]) => {
                    const selectedOpt = pillarSelections?.[areaKey];
                    const opt = selectedOpt ? area.options?.[selectedOpt] : null;
                    const areaIcons = { energy: '⚡', operations: '🏭', supply_chain: '🔗', offsetting: '🌱' };
                    return (
                      <div key={areaKey} style={{
                        display: 'flex', alignItems: 'center', gap: '0.6rem',
                        padding: '0.5rem 0.7rem', borderRadius: 6,
                        background: selectedOpt ? '#f0fdf4' : '#fef2f2',
                        border: `1px solid ${selectedOpt ? '#bbf7d0' : '#fecaca'}`,
                      }}>
                        <span style={{ fontSize: '1.1rem' }}>{areaIcons[areaKey] || '📌'}</span>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#0f172a' }}>{area.label}</div>
                          <div style={{ fontSize: '0.7rem', color: selectedOpt ? '#15803d' : '#b91c1c' }}>
                            {opt ? `${opt.title} (${opt.cost ? `$${(opt.cost / 1_000_000).toFixed(1)}M` : 'Free'})` : '— No selection (skipped)'}
                          </div>
                        </div>
                        <span style={{ fontSize: '0.9rem' }}>{selectedOpt ? '✅' : '⏭️'}</span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{
                  padding: '0.5rem 0.7rem', borderRadius: 6,
                  background: '#f0fdf4', border: '1px solid #bbf7d0',
                  display: 'flex', alignItems: 'center', gap: '0.6rem',
                }}>
                  <span style={{ fontSize: '1.1rem' }}>📋</span>
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#0f172a' }}>
                      {decisionChoice === 'option_a' ? 'Option A' : decisionChoice === 'option_b' ? 'Option B' : 'Option C'}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: '#15803d' }}>
                      {sim.roundConfig?.options?.[decisionChoice]?.title || decisionChoice}
                    </div>
                  </div>
                  <span style={{ fontSize: '0.9rem' }}>✅</span>
                </div>
              )}
            </div>

            {/* Capital Allocation Summary */}
            {Object.keys(allocations).length > 0 && (
              <div style={{
                background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
                padding: '1rem 1.2rem', marginBottom: '1rem',
              }}>
                <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#6b7280', marginBottom: '0.5rem' }}>
                  💰 Capital Allocation
                </div>
                {businessUnits.map(bu => {
                  const amt = allocations[bu.bu_id] || 0;
                  if (amt === 0) return null;
                  return (
                    <div key={bu.bu_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', fontSize: '0.75rem', color: '#334155' }}>
                      <span>{bu.name}</span>
                      <span style={{ fontWeight: 700 }}>${(amt / 1_000_000).toFixed(2)}M</span>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '0.6rem', marginTop: '1rem' }}>
              <button
                onClick={() => setShowReviewModal(false)}
                style={{
                  flex: 1, padding: '10px 0', background: '#f1f5f9', color: '#475569',
                  border: '1px solid #d1d5db', borderRadius: 6, fontWeight: 700, cursor: 'pointer',
                  fontSize: '0.72rem', letterSpacing: '0.04em', textTransform: 'uppercase',
                }}
              >← Go Back & Edit</button>
              <button
                onClick={() => { setShowReviewModal(false); handleCommitTurn(); }}
                style={{
                  flex: 1, padding: '10px 0',
                  background: 'linear-gradient(135deg, #16a34a, #15803d)',
                  color: '#fff', border: 'none', borderRadius: 6, fontWeight: 700, cursor: 'pointer',
                  fontSize: '0.72rem', letterSpacing: '0.04em', textTransform: 'uppercase',
                  boxShadow: '0 4px 12px rgba(22,163,74,0.25)',
                }}
              >✅ Confirm & Submit</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Double Materiality Overlay ── */}
      {isMatrixOpen && (
        <DoubleMaterialityMatrix
          csfPool={csfPool}
          globalState={sim?.globalState}
          initialQ1={globalState?.materiality_budget_allocated || []}
          buId={decisionParadigm === 'multi_toggles' ? r2BuSelection?.selected_bu : null}
          buLabel={decisionParadigm === 'multi_toggles' ? r2BuSelection?.bu_label : null}
          sessionId={sim.sessionId}
          onOpenAdvisor={() => setAiAdvisorOpen(true)}
          onClose={() => setIsMatrixOpen(false)}
          onSubmit={async (payload) => {
            try {
              const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/simulations/${sim.sessionId}/materiality`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
              });
              const data = await res.json();
              if (!res.ok) return { error: data.detail };
              if (sim.fetchDashboard) {
                await sim.fetchDashboard();
              }
              setCsrdDone(true);
              return { success: true, allocated_budget: data.allocated_budget };
            } catch { return { error: 'Network error submitting matrix.' }; }
          }}
        />
      )}

      {/* ── R1 Stakeholder Map ── */}
      {showStakeholderMap && (
        <StakeholderMapModal
          sessionId={sim.sessionId}
          onComplete={(result) => {
            setShowStakeholderMap(false);
            setStakeholderDone(true);
            if (sim.sessionId) sim.fetchDashboard(sim.sessionId);
          }}
        />
      )}

      {/* ── Resource Sidebar ── */}
      <ResourceSidebar
        sessionId={sim.sessionId}
        roundNumber={roundNumber}
        isOpen={resourceSidebarOpen}
        onClose={() => setResourceSidebarOpen(false)}
      />

      {sim.error && (
        <div style={{
          position: 'fixed', bottom: 40, left: '50%', transform: 'translateX(-50%)',
          background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 4,
          padding: '6px 18px', fontSize: '0.75rem', color: '#991b1b', zIndex: 9000,
          fontFamily: "'Inter', sans-serif", fontWeight: 500,
        }}>⚠️ {sim.error}</div>
      )}

      {/* ═══ IMPROVEMENT: Round Checklist (moved to ExecutiveCockpit) ═══ */}

      {/* ═══ IMPROVEMENT: Onboarding Walkthrough (1.4) ═══ */}
      {sim.sessionId && showOnboarding && !showDesktop && !sim.gameOver && (
        <OnboardingWalkthrough roundNumber={roundNumber} onComplete={() => setShowOnboarding(false)} />
      )}

      {/* ═══ IMPROVEMENT: Action Toolbar has been moved to ExecutiveCockpit leftSidebar ═══ */}

      {/* ═══ IMPROVEMENT: Market Ticker (4.3) ═══ */}
      {sim.sessionId && !sim.gameOver && (
        <MarketTicker roundNumber={roundNumber} />
      )}

      {/* ═══ IMPROVEMENT: Glossary Panel (1.2) ═══ */}
      <GlossaryPanel isOpen={glossaryOpen} onClose={() => setGlossaryOpen(false)} />

      {/* ═══ IMPROVEMENT: Achievement Badges (5.1) ═══ */}
      <AchievementBadges
        globalState={globalState}
        roundNumber={roundNumber}
        isOpen={achievementsOpen}
        onClose={() => setAchievementsOpen(false)}
      />

      {/* ═══ IMPROVEMENT: AI Advisor (4.1) ═══ */}
      <AIAdvisor
        roundNumber={roundNumber}
        globalState={globalState}
        roundConfig={sim.roundConfig}
        isOpen={aiAdvisorOpen}
        onClose={() => setAiAdvisorOpen(false)}
      />

      {/* ═══ IMPROVEMENT: Peer Comparison (5.2) ═══ */}
      <PeerComparison
        sessionId={sim.sessionId}
        isOpen={peerComparisonOpen}
        onClose={() => setPeerComparisonOpen(false)}
      />

      {/* ═══ IMPROVEMENT: Player Analytics ═══ */}
      <PlayerAnalytics
        sessionId={sim.sessionId}
        isOpen={analyticsOpen}
        onClose={() => setAnalyticsOpen(false)}
      />
    </>
  );
}



