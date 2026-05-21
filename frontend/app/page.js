'use client';

import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import styles from './page.module.css';
import cockpitStyles from './components/ExecutiveCockpit.module.css';
import dynamic from 'next/dynamic';

import ExecutiveCockpit from './components/ExecutiveCockpit';
import BoardroomShowdown from './components/BoardroomShowdown';
import SustainabilityBalancedScorecard from './components/SustainabilityBalancedScorecard';
import GameOverSummary from './components/GameOverSummary';
import StakeholderMapModal from './components/StakeholderMapModal';
import CFOOverrideModal from './components/CFOOverrideModal';
const FullScreenLoader = () => <div style={{position: 'fixed', inset: 0, background: '#080c18', zIndex: 20000}}></div>;
const DoubleMaterialityMatrix = dynamic(() => import('./components/DoubleMaterialityMatrix'), { ssr: false });
const JoinCohortModal = dynamic(() => import('./components/JoinCohortModal'), { ssr: false, loading: FullScreenLoader });
const UsernamePromptModal = dynamic(() => import('./components/UsernamePromptModal'), { ssr: false, loading: FullScreenLoader });
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
const SideTrackPanel = dynamic(() => import('./components/SideTrackPanel'), { ssr: false });
const SDGAlignmentRadar = dynamic(() => import('./components/SDGAlignmentRadar'), { ssr: false });
const BRSRDashboard = dynamic(() => import('./components/BRSRDashboard'), { ssr: false });
const InlinePodcastPlayer = dynamic(() => import('./components/InlinePodcastPlayer'), { ssr: false });

// ── Per-round AI Podcast transcripts (Dr. Priya Sharma + Prof. James Walker) ─
const PODCAST_TRANSCRIPTS = {
  1: [
    { speaker: 'Dr. Priya Sharma', text: 'Welcome to the Muressons Boardroom Briefing. Round 1 puts you in the seat of a CEO whose board has just mandated an ESG materiality assessment. The stakes are immediate — stakeholder trust is your first currency.' },
    { speaker: 'Prof. James Walker', text: 'Exactly, Priya. The Mendelow matrix you complete this round isn\'t busywork — it directly calibrates the crisis severity you face in Round 4. Underweight a high-power, high-interest stakeholder and you\'ll feel it during the contagion event.' },
    { speaker: 'Dr. Priya Sharma', text: 'The capital allocation this round sets your EBITDA baseline. Early under-investment in operations locks you into a higher OPEX structure that compounds for all 10 rounds. Think long-term payback, not short-term cashflow.' },
    { speaker: 'Prof. James Walker', text: 'One key insight: reputation above 60 at end of Round 1 unlocks a 0.05 synergy bonus next period. That\'s a meaningful edge — and it\'s entirely within your control through transparent stakeholder engagement.' },
  ],
  2: [
    { speaker: 'Prof. James Walker', text: 'Round 2 introduces the CSRD Double Materiality Gate — the EU\'s disclosure regime that forces companies to assess both their impact on society AND society\'s financial impact on them. It\'s a two-way lens.' },
    { speaker: 'Dr. Priya Sharma', text: 'The budget you allocate through the materiality matrix flows directly into your Scope 1 and 2 baseline. Skew too heavily toward financial materiality and you risk a greenwashing penalty event in Round 6 when the AI ethics crisis hits.' },
    { speaker: 'Prof. James Walker', text: 'Think of the CFO override as a last resort, not a strategy. Using it triggers a 5-point reputation deduction — which sounds small until you realise reputation is the denominator in your Social License to Operate calculation.' },
    { speaker: 'Dr. Priya Sharma', text: 'The real lesson here: integrated reporting isn\'t compliance theatre. Companies that score above 70 on materiality alignment face a statistically lower probability of activist intervention in the final round.' },
  ],
  3: [
    { speaker: 'Dr. Priya Sharma', text: 'Scope 3 is where most ESG strategies collapse. Today\'s Green Fund Bidding exercise mirrors the exact MAC curve analysis used by Unilever and Interface when they redesigned their supply chains post-Paris Agreement.' },
    { speaker: 'Prof. James Walker', text: 'Notice the trap in Round 3: the LED and HVAC retrofit has a negative MAC — it actually saves money. The Green Fund should only be used for projects that face a genuine green premium hurdle, not financially optimal ones.' },
    { speaker: 'Dr. Priya Sharma', text: 'Your Scope 3 completeness score at end of this round becomes the investor disclosure pressure variable. Below 50% and you\'ll see that data-completeness warning appear in your Market Reality Feed from Round 4 onwards.' },
    { speaker: 'Prof. James Walker', text: 'The supply chain disruption probability also rises if you under-invest here. The cogs_penalty_ratio in the engine is a direct function of your Round 3 supply chain capital decisions. Cause and effect — with a 2-round lag.' },
  ],
  4: [
    { speaker: 'Prof. James Walker', text: 'ESG Contagion is Muressons\' interpretation of the systemic risk literature from Battiston et al. — the idea that ESG failures propagate through financial networks like a virus. Your Round 1 stakeholder accuracy now becomes weaponised.' },
    { speaker: 'Dr. Priya Sharma', text: 'If you mapped stakeholders accurately in Round 1, your contagion resistance index is higher. That\'s mechanically encoded in the simulation engine — every percentage point of stakeholder accuracy translates to 0.25% lower crisis severity here.' },
    { speaker: 'Prof. James Walker', text: 'This round also tests whether you\'ve maintained your Social License to Operate. The SLO metric gates which recovery options are available to you. Below 40, the "industry coalition" option disappears — you\'re on your own.' },
    { speaker: 'Dr. Priya Sharma', text: 'Watch your treasury. Contagion crises in the real world demand immediate capital deployment. Companies with sub-20% treasury cushions lose agency entirely — which is why the emergency credit facility exists as a last resort.' },
  ],
  5: [
    { speaker: 'Dr. Priya Sharma', text: 'Round 5 operationalises the TCFD framework. The Voluntary Carbon Market portfolio you\'re building isn\'t just an offset exercise — it\'s a stress-test of your understanding of carbon credit integrity tiers.' },
    { speaker: 'Prof. James Walker', text: 'Tier 3 avoidance credits cost $4 per tonne but carry 15% integrity. Tier 1 engineered removal costs $275 but carries 100% integrity. The market is repricing this risk — VCMI\'s claims code now makes integrity non-negotiable for institutional investors.' },
    { speaker: 'Dr. Priya Sharma', text: 'Climate physical risk in this round maps to the NGFS orderly transition scenario. If you\'ve been tracking carbon intensity, you\'ll know whether you\'re on a 1.5°C pathway. Deviation compounds the physical risk event severity.' },
    { speaker: 'Prof. James Walker', text: 'One of the most powerful leverage points in Meadows\' framework is changing the goal of the system. Round 5 is where your long-term decarbonisation goal either crystalises or fractures under short-term financial pressure.' },
  ],
  6: [
    { speaker: 'Prof. James Walker', text: 'The EU AI Act classifies high-risk AI systems with significant compliance obligations. In Round 6, the bias scandal tests whether your AI governance spend in previous rounds built institutional resilience or left you exposed.' },
    { speaker: 'Dr. Priya Sharma', text: 'Board Governance metrics become critical here. Companies with a board ESG alignment score above 60 can invoke board-level crisis containment. Below that threshold, the reputational cascade is automatic and severe.' },
    { speaker: 'Prof. James Walker', text: 'The EU AI Act compliance cost is a fixed $1.2M on average, but the reputational damage multiplier depends on your prior Social License score. Same regulation, radically different impact — that\'s systemic complexity in action.' },
    { speaker: 'Dr. Priya Sharma', text: 'From a Meadows perspective, you\'re now encountering delays in a system with negative feedback loops. The bias scandal is a consequence of decisions made 3-4 rounds ago. That\'s the most important lesson: sustainability leadership requires prospective thinking.' },
  ],
  7: [
    { speaker: 'Dr. Priya Sharma', text: 'The Circular Economy pivot is grounded in the Ellen MacArthur Foundation\'s ReSOLVE framework. Round 7 shifts the question from "how do we reduce harm?" to "how do we design value that loops?"' },
    { speaker: 'Prof. James Walker', text: 'The CircularStrategyDashboard models a product-as-a-service transition. The NPV of the lease model outperforms linear sales by Year 8, but the transition period requires patient capital — exactly the test of your treasury management.' },
    { speaker: 'Dr. Priya Sharma', text: 'EU regulation on circular compliance is real — the Ecodesign for Sustainable Products Regulation is already in force. Companies that front-run regulation capture market share; those that react lose it to early movers.' },
    { speaker: 'Prof. James Walker', text: 'Synergy Tracker is most powerful in Round 7. Your circular investments interact with prior supply chain and biodiversity decisions to produce compounding returns. This is the Meadows "reinforcing loop" — either it\'s working for you or against you.' },
  ],
  8: [
    { speaker: 'Prof. James Walker', text: 'Water stress is one of the most underpriced systemic risks in corporate finance. Round 8 uses the WRI Aqueduct 4.0 methodology — when a watershed is reclassified as critically stressed, physical water costs can triple overnight.' },
    { speaker: 'Dr. Priya Sharma', text: 'The Policy War Room exercise models regulatory lobbying through a game-theoretic lens. Offensive lobbying to strengthen carbon standards can weaponise regulation against lower-performing competitors — a genuine strategic play used by DSM and Ørsted.' },
    { speaker: 'Prof. James Walker', text: 'Your biodiversity engine state is visible to students this round via the Engines tab. The TNFD LEAP framework flags your watershed dependencies — if EHI has been declining, water stress severity is amplified at the engine level.' },
    { speaker: 'Dr. Priya Sharma', text: 'There\'s a powerful insight in the Coase theorem: when property rights are well-defined, market actors can negotiate efficient environmental outcomes. The lobbying stances in the War Room test whether you understand which regulatory design creates the most value for you.' },
  ],
  9: [
    { speaker: 'Dr. Priya Sharma', text: 'Just Transition is the ethical frontier of sustainability. The ILO defines it as a pathway that maximises social benefits while minimising hardship for workers displaced by the shift to a low-carbon economy. Round 9 tests whether your strategy honours this.' },
    { speaker: 'Prof. James Walker', text: 'The ESG Refinancing Simulator is based on real green bond and sustainability-linked loan mechanics. The 75 basis point greenium for sustainability leaders is empirically grounded in Bloomberg data from 2022-2024 issuances.' },
    { speaker: 'Dr. Priya Sharma', text: 'If your ESG score is below 40 at this point, you face a 150bp penalty — the Brown Penalty. That\'s $15M extra in interest cost on a billion-dollar refinancing. The financial system is pricing transition risk, whether companies are ready or not.' },
    { speaker: 'Prof. James Walker', text: 'The strike probability variable is highest this round for companies that under-invested in workforce transition. Check your Engines tab — if the org_politics engine fired, you\'ll see coalition fragmentation data that predicts labour unrest severity.' },
  ],
  10: [
    { speaker: 'Prof. James Walker', text: 'The Activist Ultimatum in Round 10 is based on Engine No. 1\'s campaign against ExxonMobil and Follow This\' shareholder resolutions at Shell. Activists now have the financial sophistication to enforce transition plans — not just demand them.' },
    { speaker: 'Dr. Priya Sharma', text: 'The Regenerative Multiple is your terminal valuation metric. M_R above 1.2 puts you in the Regenerative Titan archetype — companies whose ESG strategy generated more social and environmental value than they consumed. That\'s the new benchmark for corporate leadership.' },
    { speaker: 'Prof. James Walker', text: 'As you head into the CEO Interview, remember the 50/50 scoring split: half from your in-game decisions, half from how articulately you can explain your reasoning. The debrief isn\'t a formality — it\'s where leaders are separated from managers.' },
    { speaker: 'Dr. Priya Sharma', text: 'Ten rounds. Five years of corporate history compressed into a few hours. Whatever your archetype, the most important outcome is this: you now understand that sustainability isn\'t a constraint on financial performance — it\'s the system within which financial performance is possible.' },
  ],
};


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
  // NEW-04: track which round briefings have already been seen — prevents re-showing on re-render
  const seenBriefingRoundsRef = useRef(new Set());

  useEffect(() => {
    setIsHydrated(true);

    // Handle ?session= URL param for facilitator impersonation
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const sessionParam = params.get('session');
      if (sessionParam && !sim.sessionId) {
        // NEW-12: Only honour the url ?session= param if it matches the locally stored session
        // (prevents cross-auth session leak when sharing links)
        const localSession = localStorage.getItem('muressons_session_id');
        if (!localSession || localSession === sessionParam) {
          sim.fetchDashboard(sessionParam).then(() => {
            sim.fetchRoundConfig && sim.fetchRoundConfig(sim.roundNumber || 1);
          }).catch(() => {});
        } else {
          // The url references a different session — ignore it silently
          console.warn('[Security] Ignoring ?session= param that does not match stored session.');
        }
      } else if (!sim.sessionId) {
        const cachedId = localStorage.getItem('muressons_session_id');
        if (cachedId) {
          // NEW-07: Keep localStorage ID even on failure — don't wipe it, so the player can retry
          sim.resumeSession(cachedId).catch((err) => {
            console.error('Failed to resume session — will retry on next load:', err);
            // Do NOT removeItem here — preserve the session pointer for reconnection
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
      const treasury = globalState?.corporate_treasury ?? SEED_GLOBAL.corporate_treasury;
      const pool = treasury * 0.20;
      // Emergency floor: even bankrupt teams can make $1M in strategic
      // investments (via emergency credit line). Without this, negative
      // treasury permanently deadlocks the investment matrix.
      return Math.max(pool, 1_000_000);
    },
    [globalState?.corporate_treasury]
  );

  // Auto-detect when emergency credit line is active (treasury × 20% < $1M)
  const emergencyCreditActive = useMemo(() => {
    const treasury = globalState?.corporate_treasury ?? SEED_GLOBAL.corporate_treasury;
    return treasury * 0.20 < 1_000_000;
  }, [globalState?.corporate_treasury]);

  // ── Decision modal state ──────────────────────────────────
  const [modalOpen, setModalOpen] = useState(false);
  const [decisionChoice, setDecisionChoice] = useState(null);
  const [stakeholderDone, setStakeholderDone] = useState(false);
  const [showStakeholderMap, setShowStakeholderMap] = useState(false);

  // Reset transient minigame states when impersonating different cohorts in the same tab
  useEffect(() => {
    setStakeholderDone(false);
    setShowStakeholderMap(false);
    // Clear briefing-seen tracker so the briefing page shows on re-login
    seenBriefingRoundsRef.current = new Set();
    setShowDesktop(true);
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
  const [sideTracksOpen, setSideTracksOpen] = useState(false);
  const [sdgRadarOpen, setSdgRadarOpen] = useState(false);
  const [brsrDashboardOpen, setBrsrDashboardOpen] = useState(false);
  const [sideTrackInfo, setSideTrackInfo] = useState(null); // { count, unlocked, blocking_track_id }
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false); // Phase 2.1: delayed until after glimpse
  const [cockpitGlimpse, setCockpitGlimpse] = useState(false); // Phase 2.1: 5s preview state
  const [confirmLogout, setConfirmLogout] = useState(false);
  useEffect(() => {
    if (!confirmLogout) return;
    const t = setTimeout(() => setConfirmLogout(false), 3500);
    return () => clearTimeout(t);
  }, [confirmLogout]);

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

  // ── Side Track availability check ──────────────────────────
  useEffect(() => {
    if (!sim.sessionId || sim.sessionId === 'demo') return;
    let cancelled = false;
    const checkSideTracks = () => {
      fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/simulations/${sim.sessionId}/side-tracks`)
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (cancelled || !data) return;
          const tracks = data.side_tracks || [];
          const unlocked = tracks.filter(t => t.is_unlocked);
          setSideTrackInfo({
            count: tracks.length,
            unlocked: unlocked.length,
            blocking_track_id: data.blocking_track_id || null,
            mainBlocked: data.main_sim_blocked || false,
          });
          // Auto-open side tracks panel when a blocking track requires attention
          if (data.blocking_track_id && !sideTracksOpen) {
            setSideTracksOpen(true);
          }
        })
        .catch(() => {});
    };
    checkSideTracks();
    // Re-check after round changes (polling every 15s is sufficient)
    const interval = setInterval(checkSideTracks, 15000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [sim.sessionId, roundNumber]);

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

  // Universal Broadcast — receives God Mode announcements over WebSocket
  const [broadcast, setBroadcast] = useState(null); // { title, message, priority }

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
  // NEW-04: Only re-open round briefing for rounds the player hasn't acknowledged yet
  useEffect(() => {
    if (sim.sessionId && sim.roundChanged && !sim.gameOver) {
      if (!seenBriefingRoundsRef.current.has(roundNumber)) {
        setShowDesktop(true);
      }
    }
  }, [sim.sessionId, sim.roundChanged, sim.gameOver, roundNumber]);

  // Clear transient decision state when the round actually advances.
  // This is deferred from handleCommitTurn so the post-commit results
  // overlay (ConsequencePreview, etc.) can still reference the player's
  // committed choices while reviewing round outcomes.
  const prevRoundForClear = useRef(roundNumber);
  useEffect(() => {
    if (roundNumber !== prevRoundForClear.current) {
      prevRoundForClear.current = roundNumber;
      setAllocations({});
      setDecisionChoice(null);
      setPillarSelections({});
    }
  }, [roundNumber]);

  const handleProceedFromDesktop = () => {
    // Mark this round's briefing as seen so it doesn't re-open
    seenBriefingRoundsRef.current.add(roundNumber);
    setShowDesktop(false);
    // Phase 2.1: Go directly to onboarding tour (ROUND 1 ONLY)
    if (roundNumber === 1) {
      setShowOnboarding(true);
    }
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
        emergency_credit_used: emergencyCreditActive,
      });
      soundManager.commit();
      // NOTE: allocations, decisionChoice, and pillarSelections are now
      // cleared by the roundNumber-change useEffect above (not here), so
      // the post-commit results overlay can still reference them.
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
  }, [sim, businessUnits, allocations, csfPool, decisionChoice, roundNumber, emergencyCreditActive]);

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

  // Universal Broadcast WebSocket — connects to /api/admin/ws/session/{id} for God Mode pushes
  useEffect(() => {
    if (!sim.sessionId || sim.sessionId === 'demo' || typeof window === 'undefined') return;
    const wsBase = (process.env.NEXT_PUBLIC_API_URL || '').replace(/^http/, 'ws');
    const wsUrl = `${wsBase}/api/admin/ws/session/${sim.sessionId}`;
    let ws;
    let retryTimeout;
    const connect = () => {
      try {
        ws = new WebSocket(wsUrl);
        ws.onmessage = (evt) => {
          try {
            const msg = JSON.parse(evt.data);
            if (msg.type === 'universal_broadcast') {
              setBroadcast({ title: msg.title, message: msg.message, priority: msg.priority });
            }
            // Forward round_unlocked / advance events to simulation hook
            if (msg.type === 'round_unlocked' || msg.type === 'game_advanced') {
              sim.fetchDashboard?.(sim.sessionId);
            }
          } catch { /* ignore malformed WS messages */ }
        };
        ws.onerror = () => {};
        ws.onclose = () => {
          // Reconnect after 5s (handles server restarts)
          retryTimeout = setTimeout(connect, 5000);
        };
      } catch { /* WebSocket not available */ }
    };
    connect();
    return () => {
      clearTimeout(retryTimeout);
      ws?.close();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sim.sessionId]);

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
    } catch (err) {
      console.error("Force override still failed:", err);
    }
  }, [sim, pendingDecisions]);

  // ── Game Over → Scorecard → BoardroomShowdown → Done ─────────
  const [gameOverPhase, setGameOverPhase] = useState('scorecard'); // 'scorecard' | 'boardroom' | 'done'
  const [showPodcast, setShowPodcast] = useState(false);
  const [boardroomDone, setBoardroomDone] = useState(false);
  // EX-2/NF-4: Commit Ceremony state (must be before any early return)
  const [showCommitCeremony, setShowCommitCeremony] = useState(false);

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

  const isSelfLearning = globalState?.self_learning_mode === true;
  const hasSubmittedMatrix = csrdDone || globalState?.csrd_completed === true ||
    (Array.isArray(globalState?.materiality_budget_allocated) && globalState.materiality_budget_allocated.length > 0);
  const hasCompletedStakeholderMap = globalState?.stakeholder_map_completed === true || stakeholderDone;
  // In multi_toggles mode, at least one pillar must be selected
  const hasDecision = decisionParadigm === 'multi_toggles'
    ? Object.keys(pillarSelections).length > 0
    : !!decisionChoice;
  // Gate enforcement: R1 stakeholder map and R2 materiality matrix are mandatory in ALL modes
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

      if (sim.events?.brsr_greenwash_crisis) {
        addMsg(`evt-brsr-gw-${roundNumber}`, '💧 SEBI Show-Cause Notice', sim.events.brsr_greenwash_crisis);
      }

      if (sim.events?.brsr_governance_crisis) {
        addMsg(`evt-brsr-gov-${roundNumber}`, '⛔ Governance Leak', sim.events.brsr_governance_crisis);
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
          sessionId={sim.sessionId}
        />
      );
    }
    if (gameOverPhase === 'boardroom') {
      return (
        <BoardroomShowdown
          data={sim.finalReport}
          sessionId={sim.sessionId}
          onComplete={() => { setBoardroomDone(true); setGameOverPhase('done'); }}
          onLogout={sim.logout}
        />
      );
    }
    // 'done' — simulation is complete, with option to review scorecard
    return (
      <GameOverSummary
        data={sim.finalReport}
        businessUnits={sim.businessUnits}
        globalState={sim.globalState}
        history={sim.history}
        decisionParadigm={decisionParadigm}
        sessionId={sim.sessionId}
        onReviewScorecard={() => setGameOverPhase('scorecard')}
        onLogout={sim.logout}
      />
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
    // Side track blocking gate
    if (sideTrackInfo?.mainBlocked) {
      setBlockAlert("A Side Track requires your attention before you can advance to the next round. Complete the active side track first.");
      setSideTracksOpen(true);
      return;
    }
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
      {/* UX-10: Logout — 2 click confirmation to prevent accidental exits */}
      {sim.sessionId && (
        <button
          onClick={() => {
            if (confirmLogout) { sim.logout(); setConfirmLogout(false); }
            else setConfirmLogout(true);
          }}
          title={confirmLogout ? 'Click again to confirm logout' : 'Logout & Exit Simulation'}
          style={{
            position: 'fixed', top: 12, right: 16, zIndex: 19000,
            display: 'flex', alignItems: 'center', gap: 6, padding: '6px 14px',
            background: confirmLogout ? 'rgba(127,29,29,0.9)' : 'rgba(15,23,42,0.75)',
            backdropFilter: 'blur(8px)',
            border: confirmLogout ? '1px solid #f87171' : '1px solid rgba(248,113,113,0.25)',
            borderRadius: 8, color: confirmLogout ? '#fff' : '#fca5a5',
            fontSize: '0.72rem', fontWeight: 700, fontFamily: "'DM Sans', system-ui, sans-serif",
            cursor: 'pointer', transition: 'background 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease, transform 0.2s ease', boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          }}
        >
          {confirmLogout ? '⚠️ Confirm Logout?' : '🚪 Logout'}
        </button>
      )}

      {/* CB-01 / MP-05: Error banners for join-required and session-expired */}
      {sim.error && !sim.sessionId && (sim.error.startsWith('JOIN_REQUIRED') || sim.error.startsWith('SESSION_EXPIRED')) && (
        <div style={{
          position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)', zIndex: 20000,
          padding: '14px 24px', borderRadius: 12, maxWidth: 480, textAlign: 'center',
          background: 'rgba(30,15,15,0.96)', border: '1px solid rgba(239,68,68,0.5)',
          backdropFilter: 'blur(12px)', boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          fontFamily: "'DM Sans', system-ui, sans-serif",
        }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fca5a5', marginBottom: 6 }}>
            {sim.error.startsWith('JOIN_REQUIRED') ? '🚫 Direct Session Start Not Permitted' : '⏱️ Session Expired'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', lineHeight: 1.5 }}>
            {sim.error.startsWith('JOIN_REQUIRED')
              ? 'Please enter your cohort session code to join the live simulation.'
              : 'Your previous session could not be restored. Please use your session code to rejoin.'}
          </div>
        </div>
      )}


      {/* MP-03: Auto-advance notification */}
      {sim.autoAdvanceDetected && (
        <div style={{
          position: 'fixed', top: 60, left: '50%', transform: 'translateX(-50%)', zIndex: 18000,
          padding: '10px 20px', borderRadius: 10, background: 'rgba(16,185,129,0.15)',
          border: '1px solid rgba(16,185,129,0.4)', backdropFilter: 'blur(8px)',
          fontFamily: "'DM Sans', system-ui, sans-serif", fontSize: '0.8rem',
          color: '#6ee7b7', fontWeight: 600, letterSpacing: '0.02em',
        }}>
          ⚡ Facilitator has advanced the round — cockpit updating...
        </div>
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
          fontFamily: "'DM Sans', sans-serif",
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

      {/* ── CFO Override Modal ── */}
      {showOverrideModal && (
        <CFOOverrideModal
          errorText={cfoErrorMsg}
          onConfirm={handleForceOverride}
          onCancel={() => { setShowOverrideModal(false); setPendingDecisions(null); setCfoErrorMsg(''); }}
        />
      )}

      {/* ── Universal Broadcast Banner (God Mode → Students) ── */}
      {broadcast && (
        <div style={{
          position: 'fixed', top: 60, left: '50%', transform: 'translateX(-50%)',
          zIndex: 20500, maxWidth: 560, width: '90%',
          background: broadcast.priority === 'critical'
            ? 'rgba(127,29,29,0.96)' : broadcast.priority === 'warning'
            ? 'rgba(120,53,15,0.96)' : 'rgba(14,20,36,0.96)',
          border: broadcast.priority === 'critical'
            ? '1px solid rgba(239,68,68,0.6)' : broadcast.priority === 'warning'
            ? '1px solid rgba(245,158,11,0.6)' : '1px solid rgba(59,130,246,0.5)',
          borderRadius: 12, backdropFilter: 'blur(12px)',
          boxShadow: '0 12px 40px rgba(0,0,0,0.4)',
          fontFamily: "'DM Sans', sans-serif",
          animation: 'slideDown 0.3s ease-out',
        }}>
          <div style={{ padding: '14px 18px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
            <span style={{ fontSize: '1.4rem', flexShrink: 0 }}>
              {broadcast.priority === 'critical' ? '🚨' : broadcast.priority === 'warning' ? '⚠️' : '📢'}
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '0.88rem', fontWeight: 800, color: '#f1f5f9', marginBottom: 4 }}>
                {broadcast.title}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                {broadcast.message}
              </div>
            </div>
            <button
              onClick={() => setBroadcast(null)}
              style={{
                background: 'transparent', border: 'none', color: '#64748b',
                fontSize: '1rem', cursor: 'pointer', padding: 4, borderRadius: 4,
                lineHeight: 1, flexShrink: 0,
              }}
              title="Dismiss"
            >✕</button>
          </div>
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
          isSDG={decisionParadigm === 'un_sdg'}
          decisionParadigm={decisionParadigm}
          globalState={globalState}
          onProceed={handleProceedFromDesktop}
          prevRoundData={sim.history?.[sim.history.length - 1]}
          activeFlags={Object.keys(globalState?.active_event_flags || {})}
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
                { icon: '🎧', label: 'Podcast', shortcut: null, onClick: () => setShowPodcast(true) },
                { icon: '📈', label: 'Leaderboard', shortcut: null, onClick: () => setPeerComparisonOpen(true) },
                ...(sideTrackInfo && sideTrackInfo.count > 0 ? [{
                  icon: '🛤️', label: sideTrackInfo.unlocked > 0 ? `Tracks (${sideTrackInfo.unlocked})` : 'Tracks', shortcut: null,
                  onClick: () => setSideTracksOpen(true),
                  highlight: sideTrackInfo.mainBlocked,
                }] : []),
                { icon: '🏅', label: 'Badges', shortcut: null, onClick: () => setAchievementsOpen(true) },
                { icon: '🧠', label: 'Advisor', shortcut: 'A', onClick: () => setAiAdvisorOpen(true) },
                { icon: '📊', label: 'Analytics', shortcut: null, onClick: () => setAnalyticsOpen(true) },
                { icon: '🌐', label: 'SDG Radar', shortcut: null, onClick: () => setSdgRadarOpen(true) },
                { icon: '🇮🇳', label: 'BRSR', shortcut: null, onClick: () => setBrsrDashboardOpen(true) },
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
                    background: btn.highlight ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.05)',
                    border: btn.highlight ? '1px solid rgba(245,158,11,0.5)' : '1px solid rgba(255,255,255,0.1)',
                    cursor: 'pointer',
                    transition: 'transform 0.15s, background 0.15s',
                    color: btn.highlight ? '#f59e0b' : '#e2e8f0',
                    animation: btn.highlight ? 'pulse 2s infinite' : 'none',
                  }}
                  onMouseOver={e => { e.currentTarget.style.transform = 'scale(1.05)'; e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; }}
                  onMouseOut={e => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; }}
                >
                  <span style={{ fontSize: '0.85rem' }}>{btn.icon}</span>
                  <span style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.02em', textTransform: 'uppercase' }}>{btn.label}</span>
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
        hasNewResources={hasNewResources}
        hasAllocated={Object.keys(allocations).length > 0}
        hasReadBriefing={!showDesktop}
        onLogout={sim.logout}
        lastSavedAt={lastSavedAt}
        tourActive={showOnboarding}
      />

      {/* ═══ INLINE PODCAST PLAYER ═══ */}
      {showPodcast && sim.sessionId && (
        <InlinePodcastPlayer
          isOpen={showPodcast}
          onClose={() => setShowPodcast(false)}
          title={`Round ${roundNumber} — Boardroom Briefing Podcast`}
          transcript={PODCAST_TRANSCRIPTS[roundNumber] || PODCAST_TRANSCRIPTS[1]}
          sessionId={sim.sessionId}
          notebookId={`round_${roundNumber}_podcast`}
        />
      )}

      {/* ═══ SIDE TRACK PANEL ═══ */}
      {sideTracksOpen && sim.sessionId && (
        <SideTrackPanel sessionId={sim.sessionId} onClose={() => setSideTracksOpen(false)} />
      )}

      {/* ═══ SDG ALIGNMENT RADAR ═══ */}
      {sdgRadarOpen && sim.sessionId && (
        <SDGAlignmentRadar
          sessionId={sim.sessionId}
          globalState={globalState}
          buStates={businessUnits}
          isOpen={sdgRadarOpen}
          onClose={() => setSdgRadarOpen(false)}
        />
      )}

      {/* ═══ BRSR DASHBOARD ═══ */}
      {brsrDashboardOpen && sim.sessionId && (
        <BRSRDashboard
          sessionId={sim.sessionId}
          globalState={globalState}
          isOpen={brsrDashboardOpen}
          onClose={() => setBrsrDashboardOpen(false)}
        />
      )}

      {/* ═══ CRISIS ALERTS (auto-trigger + manual inject) ═══ */}
      {sim.sessionId && (
        <CrisisAlerts
          globalState={globalState}
          roundNumber={roundNumber}
          onInjectMessage={handleCrisisInject}
          briefingActive={showDesktop}
        />
      )}

      {/* ── Auto-Advance Notification ── */}
      {sim.autoAdvanceDetected && (
        <div
          onClick={() => sim.setAutoAdvanceDetected?.(false)}
          style={{
          position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)',
          background: 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#fff',
          borderRadius: 10, padding: '12px 24px', zIndex: 20000,
          fontFamily: "'DM Sans', sans-serif", fontSize: '0.85rem', fontWeight: 700,
          boxShadow: '0 8px 24px rgba(245,158,11,0.35)',
          display: 'flex', alignItems: 'center', gap: '0.6rem',
          animation: 'slideDown 0.3s ease-out', cursor: 'pointer',
        }}>
          <span style={{ fontSize: '1.2rem' }}>⏰</span>
          Time expired — your turn was auto-committed with default choices. Now on Round {roundNumber}.
          <span style={{ marginLeft: '0.5rem', opacity: 0.7, fontSize: '0.7rem' }}>✕</span>
        </div>
      )}

      {/* ── Block Alert Modal ── */}
      {blockAlert && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(27,42,74,0.5)', zIndex: 10000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: "'DM Sans', sans-serif",
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
          fontFamily: "'DM Sans', sans-serif", backdropFilter: 'blur(4px)',
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
                      {decisionChoice === 'option_a' ? 'Option A' : decisionChoice === 'option_b' ? 'Option B' : 'Option C'} — {sim.roundConfig?.options?.[decisionChoice]?.title || ''}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: '#15803d', borderBottom: '1px dashed #bbf7d0' }}>
                      {sim.roundConfig?.options?.[decisionChoice]?.description || decisionChoice}
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
                onClick={() => {
                  setShowReviewModal(false);
                  // EX-2/NF-4: Show commit ceremony overlay
                  setShowCommitCeremony(true);
                  setTimeout(() => {
                    setShowCommitCeremony(false);
                    handleCommitTurn();
                  }, 800);
                }}
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

      {/* EX-2/NF-4: Commit Ceremony Overlay */}
      {showCommitCeremony && (
        <div className={cockpitStyles.commitCeremony}>
          <div className={cockpitStyles.commitPulseRing}>
            <span style={{ fontSize: '1.6rem' }}>✅</span>
          </div>
          <span className={cockpitStyles.commitProcessingText}>Processing Decision...</span>
        </div>
      )}

      {/* ── R2 Double Materiality (Phase 2.3: slide-in panel) ── */}
      {isMatrixOpen && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 7500,
          display: 'flex', justifyContent: 'flex-end',
          background: 'rgba(10, 14, 26, 0.4)',
          animation: 'slideInFromRight 0.3s ease-out',
        }}>
          <div style={{
            width: '85%', maxWidth: 1100, height: '100%',
            background: '#0a0e1a',
            borderLeft: '2px solid rgba(0, 229, 195, 0.15)',
            boxShadow: '-8px 0 32px rgba(0,0,0,0.4)',
            overflow: 'auto',
          }}>
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
          </div>
        </div>
      )}

      {/* ── R1 Stakeholder Map (Phase 2.3: slide-in panel) ── */}
      {showStakeholderMap && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 7500,
          display: 'flex', justifyContent: 'flex-end',
          background: 'rgba(10, 14, 26, 0.4)',
          animation: 'slideInFromRight 0.3s ease-out',
        }}>
          <div style={{
            width: '85%', maxWidth: 1100, height: '100%',
            background: '#0a0e1a',
            borderLeft: '2px solid rgba(0, 229, 195, 0.15)',
            boxShadow: '-8px 0 32px rgba(0,0,0,0.4)',
            overflow: 'auto',
          }}>
            <StakeholderMapModal
              sessionId={sim.sessionId}
              onComplete={(result) => {
                setShowStakeholderMap(false);
                setStakeholderDone(true);
                if (sim.sessionId) sim.fetchDashboard(sim.sessionId);
              }}
            />
          </div>
        </div>
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
          fontFamily: "'DM Sans', sans-serif", fontWeight: 500,
        }}>⚠️ {sim.error}</div>
      )}

      {/* ═══ IMPROVEMENT: Round Checklist (moved to ExecutiveCockpit) ═══ */}

      {/* ═══ Phase 2.2: Onboarding Walkthrough (contextual, dismissible) ═══ */}
      {sim.sessionId && showOnboarding && !showDesktop && !sim.gameOver && (
        <OnboardingWalkthrough roundNumber={roundNumber} decisionParadigm={decisionParadigm} onComplete={() => setShowOnboarding(false)} />
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
        roundNumber={roundNumber}
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



