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
import ResourceSidebar from './components/ResourceSidebar';
import useSimulation from './hooks/useSimulation';

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
        sim.fetchDashboard(sessionParam).then(() => {
          sim.fetchRoundConfig && sim.fetchRoundConfig(sim.roundNumber || 1);
        }).catch(() => {});
      }
    }
  }, []);

  // Live state or seed fallback
  const globalState = sim.globalState || SEED_GLOBAL;
  const businessUnits = sim.businessUnits?.length ? sim.businessUnits : SEED_BUS;
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

  // Resource sidebar state
  const [resourceSidebarOpen, setResourceSidebarOpen] = useState(false);
  const [hasNewResources, setHasNewResources] = useState(false);

  // Decision paradigm state
  const [decisionParadigm, setDecisionParadigm] = useState('legacy_abc');
  const [pillarSelections, setPillarSelections] = useState({});
  const [pillarConfig, setPillarConfig] = useState(null);

  // Pre-commit review modal
  const [showReviewModal, setShowReviewModal] = useState(false);

  // R2 BU selection for Strategic Pillars mode
  const [r2BuSelection, setR2BuSelection] = useState(null); // { selected_bu, bu_label }

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
      setAllocations({});
      setDecisionChoice(null);
      setShowOverrideModal(false);
      setPendingDecisions(null);
    } catch (err) {
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
      // Optionally flash a success message or rely on button UI feedback
    } catch (err) {
      console.error("Failed to save decisions:", err);
    }
  }, [sim, allocations, decisionChoice]);

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

  // When re-joining a completed session, skip to done phase
  useEffect(() => {
    if (sim.gameOver && sim.roundNumber > 10 && !boardroomDone) {
      setBoardroomDone(true);
      setGameOverPhase('done');
    }
  }, [sim.gameOver, sim.roundNumber, boardroomDone]);

  // ── Auto-clear lock after 30s to let user retry ─────────────
  useEffect(() => {
    if (!sim.roundLocked) return;
    const timer = setTimeout(() => {
      sim.setRoundLocked(false);
    }, 30_000);
    return () => clearTimeout(timer);
  }, [sim.roundLocked]);

  const hasSubmittedMatrix = globalState && globalState.materiality_budget_allocated !== undefined;
  const hasCompletedStakeholderMap = globalState?.stakeholder_map_completed === true || stakeholderDone;
  // In multi_toggles mode, at least one pillar must be selected
  const hasDecision = decisionParadigm === 'multi_toggles'
    ? Object.keys(pillarSelections).length > 0
    : !!decisionChoice;
  const isCommitBlocked = (roundNumber === 2 && !hasSubmittedMatrix) || (roundNumber === 1 && !hasCompletedStakeholderMap) || !hasDecision;

  // Mailbox messages for the new cockpit (local crisis + facilitator messages)
  // Messages ACCUMULATE across rounds so previous rounds are available in accordion
  const [mailboxMessages, setMailboxMessages] = useState([]);
  const [facilitatorMessages, setFacilitatorMessages] = useState([]);
  const addedRoundsRef = useRef(new Set());

  const CRISES = useMemo(() => ({
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
  }), []);

  // Append crisis briefing once per round (accumulate, never reset)
  useEffect(() => {
    if (addedRoundsRef.current.has(roundNumber)) return;
    addedRoundsRef.current.add(roundNumber);
    const crisisText = CRISES[roundNumber];
    const newMsgs = [
      { id: `briefing-r${roundNumber}`, round: roundNumber, type: 'narrative', title: 'Board Briefing', body: `Round ${roundNumber}: ${crisisText || 'Review the module mandate and make your decisions.'}`, read: false },
    ];
    setMailboxMessages(prev => [...prev, ...newMsgs]);
  }, [roundNumber, CRISES]);

  // Append engine event messages (talent penalties etc.) for current round
  useEffect(() => {
    if (sim.events?.talent_penalty_applied > 1) {
      const evtId = `evt-talent-${roundNumber}`;
      setMailboxMessages(prev => {
        if (prev.some(m => m.id === evtId)) return prev;
        return [...prev, { id: evtId, round: roundNumber, type: 'warning', title: '🧠 Brain-Drain Alert', body: `Software OPEX inflated by ${((sim.events.talent_penalty_applied - 1) * 100).toFixed(1)}%`, read: false }];
      });
    }
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
      setBlockAlert("You must complete the Stakeholder Power/Interest Grid before advancing to Round 2. Click the ⚖️ Stakeholder Map button to begin.");
    } else if (roundNumber === 2 && !hasSubmittedMatrix) {
      setBlockAlert("You must complete and submit the CSRD Materiality Assessment before advancing to Round 3.");
    } else if (!hasDecision) {
      setBlockAlert(decisionParadigm === 'multi_toggles'
        ? "You must select at least one strategic pillar action before committing your turn."
        : "You must select a strategic option from the Decision Tab before committing your turn.");
    } else {
      // Show review modal instead of committing directly
      setShowReviewModal(true);
    }
  };

  // ── Main Cockpit ──────────────────────────────────────────
  if (!isHydrated) {
    return <div style={{ height: '100vh', width: '100%', background: '#1b2a4a' }} />;
  }

  return (
    <>
      {/* Join/Login overlay */}
      {!sim.sessionId && <div className={styles.joinOverlay}><JoinCohortModal sim={sim} /></div>}

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

      {/* Desktop Intro */}
      {sim.sessionId && showDesktop && (
        <div style={{
          position: 'fixed', inset: 0,
          backgroundImage: 'url(/desktop-bg.JPG)', backgroundSize: 'cover', backgroundPosition: 'center',
          zIndex: 10000, display: 'flex', justifyContent: 'flex-end', alignItems: 'flex-end', padding: '2rem',
          fontFamily: "'Inter', sans-serif",
        }}>
          <div style={{
            background: 'rgba(27,42,74,0.96)',
            border: '1px solid rgba(241,245,249,0.12)', borderRadius: 6, padding: '1rem 1.6rem',
            boxShadow: '0 12px 40px rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', gap: '1rem',
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
              <span style={{ fontSize: '0.58rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#94a3b8' }}>Round {roundNumber} of 10</span>
              <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f1f5f9' }}>{ROUND_TITLES[roundNumber]}</span>
            </div>
            <button onClick={handleProceedFromDesktop} style={{
              background: '#3b82f6', color: '#fff', border: 'none',
              borderRadius: 4, padding: '8px 18px', fontSize: '0.72rem', fontWeight: 700, cursor: 'pointer',
              letterSpacing: '0.04em', textTransform: 'uppercase',
            }}>Enter Cockpit →</button>
          </div>
        </div>
      )}

      {/* ═══ NEW EXECUTIVE COCKPIT ═══ */}
      <ExecutiveCockpit
        sim={sim}
        globalState={globalState}
        businessUnits={businessUnits}
        roundNumber={roundNumber}
        history={sim.history}
        roundConfig={sim.roundConfig}
        decisionParadigm={decisionParadigm}
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
      />

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
          onClose={() => setIsMatrixOpen(false)}
          onSubmit={async (payload) => {
            try {
              const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/simulations/${sim.sessionId}/materiality`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
              });
              const data = await res.json();
              if (!res.ok) return { error: data.detail };
              if (sim.globalState) {
                sim.globalState.corporate_treasury += data.allocated_budget;
                sim.globalState.materiality_budget_allocated = payload.matrix_submission.quadrant_1_top_right;
              }
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
          position: 'fixed', bottom: 16, left: '50%', transform: 'translateX(-50%)',
          background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 4,
          padding: '6px 18px', fontSize: '0.75rem', color: '#991b1b', zIndex: 9000,
          fontFamily: "'Inter', sans-serif", fontWeight: 500,
        }}>⚠️ {sim.error}</div>
      )}
    </>
  );
}



