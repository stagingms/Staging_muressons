'use client';

import { useState, useEffect } from 'react';
import { logoutAnchorStyle } from './logoutChrome';
import styles from './RoundBriefing.module.css';
import { sanitizeHtml } from '@/app/utils/sanitize';
import { STANDARD_BRIEFINGS }   from '@/app/briefings/data/standard';
import { HEALTHCARE_BRIEFINGS } from '@/app/briefings/data/healthcare';
import { SDG_BRIEFINGS }        from '@/app/briefings/data/sdg';
import { deriveSimContext, resolveBriefing } from '@/app/briefings/resolver';
import { stripPedagogy } from '@/app/briefings/stripPedagogy';
import { currencySymbol, atRate, localiseAuthored } from '../utils/format';


/**
 * ═══════════════════════════════════════════════════════════════
 *  ROUND BRIEFING DATA — All 10 Rounds
 *  Each entry contains narrative text, objectives, key metrics.
 * ═══════════════════════════════════════════════════════════════
 */

// NOTE: BRIEFINGS, HEALTHCARE_BRIEFINGS, and SDG_BRIEFINGS have been extracted
// to briefings/data/*.js and imported above.
// These re-exports maintain backward compatibility with any other file that
// imports these constants directly from this module.
export { STANDARD_BRIEFINGS as BRIEFINGS };
export { HEALTHCARE_BRIEFINGS };
export { SDG_BRIEFINGS };

/**
 * RoundBriefing — Pre-round briefing document overlay.
 *
 * Props:
 *  - roundNumber: 1–10
 *  - isHealthcare: boolean
 *  - isSDG: boolean
 *  - decisionParadigm: string
 *  - onProceed: () => void
 *  - prevRoundData: { treasury_delta, reputation_delta, choice, events } (optional)
 *  - activeFlags: string[] — flags set by prior round decisions (optional)
 *  - globalState: object — current global state snapshot (optional)
 *  - businessUnits: BU[] — live BU array for narrative resolution
 *  - sessionMeta: { cohort_name, ... } — session metadata for personalisation
 */

// ── Butterfly Effect Hints (subtle, not explicit) ──────────────
const BUTTERFLY_HINTS = {
  electronics_blindspot: '🔍 Your earlier audit decisions left gaps that may amplify this crisis...',
  deferred_audit: '📋 Phased due diligence means some vulnerabilities remain partially hidden...',
  deep_audit_completed: '🛡️ Your thorough groundwork may provide unexpected protection here...',
  supply_chain_disruption_risk: '🏭 Supply chain restructuring has introduced new operational dynamics...',
  early_decarboniser: '🌿 Your proactive decarbonisation efforts are beginning to bear fruit...',
  green_bond_active: '💚 Green bond proceeds are gradually transforming your supply chain...',
  carbon_deferred: '⏳ Deferred carbon commitments may create mounting pressure...',
  remediation_active: '✅ Your transparency in the last crisis has altered stakeholder expectations...',
  pr_containment: '🔇 The narrative was contained, but root causes remain unaddressed...',
  deny_and_deflect: '🔥 Unresolved crisis vectors may compound with new challenges...',
  hard_engineering: '🏗️ Infrastructure projects are still under construction...',
  nature_based_resilience: '🌊 Natural buffer systems are establishing, providing growing protection...',
  insurance_only: '📄 Insurance paperwork won\'t stop physical damage...',
  ai_monetised: '🤖 The monetised algorithm continues to generate revenue — and controversy...',
  ethical_ai_overhaul: '🤝 Your ethical AI stance has strengthened stakeholder trust...',
  quiet_patch: '🔧 The quiet fix may not remain quiet forever...',
  circular_redesign: '♻️ Circular product designs are generating new efficiency gains...',
  waste_to_energy: '⚡ Waste-to-energy infrastructure is boosting cross-BU synergies...',
  desalination_built: '💧 Desalination plant is operational — water independence secured...',
  community_fund: '🏘️ Community investment is generating goodwill and workforce stability...',
  waste_compliance_gap: '⚠️ Compliance shortcuts from earlier decisions may create exposure...',
  compliance_gap: '📋 Regulatory gaps from prior choices are attracting scrutiny...',
  // CSRD materiality flags
  materiality_aligned: '📊 Your R2 materiality governance (+0.10 M_R) — institutional investors are rewarding your CSRD posture...',
  materiality_ignored: '⚠️ Your R2 materiality gaps may surface as financing friction in Green Bond pricing...',
};

// ── Theory Cards (academic frameworks per round) ───────────────
const THEORY_CARDS = {
  1: { title: 'TCFD & CSRD Frameworks', desc: 'Task Force on Climate-related Financial Disclosures (TCFD) and EU Corporate Sustainability Reporting Directive (CSRD) require companies to assess and report on climate risks and opportunities. The audit decision determines your disclosure readiness.' },
  2: { title: 'Double Materiality (EU CSRD)', desc: 'The Double Materiality concept from the EU CSRD requires assessing both how sustainability issues affect your business (financial materiality) and how your business affects society and the environment (impact materiality).' },
  3: { title: 'Scope 3 Emissions (GHG Protocol)', desc: 'The Greenhouse Gas Protocol categorises emissions into Scopes 1 (direct), 2 (energy), and 3 (value chain). Scope 3 typically represents 70-90% of a company\'s total carbon footprint.' },
  4: { title: 'Contagion Theory & Reputational Capital', desc: 'Reputational contagion occurs when a crisis in one division spreads to damage the entire organisation. Prior governance decisions determine the speed and severity of propagation.' },
  5: { title: 'TCFD Physical Risk Scenarios', desc: 'Physical climate risks include acute events (e.g., cyclones) and chronic shifts (e.g., sea level rise). The TCFD framework categorises adaptation strategies as hard engineering, nature-based solutions, or financial transfer (insurance).' },
  6: { title: 'AI Ethics & the EU AI Act', desc: 'The EU AI Act classifies AI systems by risk level. High-risk systems (like recruitment tools) require fairness audits, explainability, and human oversight. The "truth premium" reflects long-term value of ethical AI governance.' },
  7: { title: 'Circular Economy (Ellen MacArthur Foundation)', desc: 'The circular economy framework replaces linear "take-make-dispose" models with closed-loop systems. Key strategies include product redesign for disassembly, extended producer responsibility, and waste-to-energy recovery.' },
  8: { title: 'Water Stewardship (CEO Water Mandate)', desc: 'UN CEO Water Mandate principles require companies to measure water usage, reduce dependency, and invest in watershed protection. Water scarcity is a systemic risk multiplier that compounds other operational challenges.' },
  9: { title: 'Just Transition (ILO Guidelines)', desc: 'The International Labour Organization\'s Just Transition framework requires that decarbonisation pathways protect workers and communities. Failure to manage the social dimensions of transition leads to strikes, political backlash, and regulatory friction.' },
  10: { title: 'Terminal Value & Regenerative Business', desc: 'Terminal value in DCF models represents 60-80% of total enterprise value. The Regenerative Multiple (M_R) captures whether a firm creates or destroys long-term value beyond financial metrics, incorporating ecological and social capital.' },
};

// ── Stakeholder Voices ─────────────────────────────────────────
const STAKEHOLDER_VOICES = {
  1: [],
  2: [
    { avatar: '👔', role: 'CFO', text: '"Every dollar needs to justify itself against both financial return and societal impact. No exceptions."' },
    { avatar: '📊', role: 'ESG Analyst', text: '"The market is watching. Materiality alignment will define your credit rating trajectory."' },
  ],
  3: [
    { avatar: '🌍', role: 'Sustainability Director', text: '"Our Scope 3 footprint is a ticking time bomb. The question is not if regulation comes, but when."' },
    { avatar: '🏭', role: 'Supply Chain Manager', text: '"Switching suppliers overnight will cause factory downtime. But staying put is not an option either."' },
  ],
  4: [
    { avatar: '📰', role: 'Investigative Journalist', text: '"We have evidence of systematic labour violations in your tier-2 supplier factories."' },
    { avatar: '✊', role: 'Worker Representative', text: '"We are watching how you respond. Transparency now, or protests later."' },
  ],
  5: [
    { avatar: '🌪️', role: 'Climate Scientist', text: '"The cyclone trajectory models show significant uncertainty. But the damage potential is enormous."' },
    { avatar: '📊', role: 'Risk Actuary', text: '"Insurance only covers financial losses, not physical infrastructure or supply chain disruption."' },
  ],
  6: [
    { avatar: '🤖', role: 'AI Ethics Board', text: '"Monetising a biased algorithm sets a dangerous precedent across the industry."' },
    { avatar: '💼', role: 'Board Member', text: '"The revenue opportunity is substantial. But at what reputational cost?"' },
  ],
  7: [
    { avatar: '♻️', role: 'EU Regulator', text: '"Non-compliance with the 60% diversion target will incur €15M in penalties."' },
    { avatar: '🔬', role: 'Innovation Director', text: '"Waste-to-energy could transform our cost structure if we commit fully."' },
  ],
  8: [
    { avatar: '💧', role: 'Water Authority', text: '"Rationing will begin within 6 months. Industrial users will be first to face cuts."' },
    { avatar: '🏥', role: 'Pharma Operations', text: '"Our Pharma division needs 2M litres/day for sterile manufacturing. Any cut is catastrophic."' },
  ],
  9: [
    { avatar: '✊', role: 'Union Leader', text: '"We will not accept job losses without a credible retraining plan. Our patience is running out."' },
    { avatar: '🏘️', role: 'Community Mayor', text: '"These factories support 2,000 families. Close them, and you close this town."' },
  ],
  10: [
    { avatar: '📈', role: 'Activist Investor', text: '"We hold a blocking stake. Restructure now, or we force a proxy vote."' },
    { avatar: '📊', role: 'M&A Advisor', text: '"Your terminal multiple depends on the narrative you build today. Every decision matters."' },
    { avatar: '🌍', role: 'Legacy Committee', text: '"History will judge this company by what it does in this final round."' },
  ],
};

// ── Climate-Specific Theory Cards (R3+) ───────────────────────────
const CLIMATE_THEORY_CARDS = {
  1: THEORY_CARDS[1],
  2: THEORY_CARDS[2],
  3: { title: 'GHG Protocol Scope 3 + Internal Carbon Pricing', desc: 'Scope 3 emissions (value chain) represent 70-90% of corporate footprint. Internal Carbon Pricing (ICP) creates a shadow cost per tonne, funding a Green Transition Fund. The EU CBAM enforces external pricing from 2026.' },
  4: { title: 'Contagion Theory + Stranded Asset Risk', desc: 'Reputational contagion amplifies under carbon exposure. Business units with carbon intensity >120 become "stranded assets" — their value is impaired by transition risk, triggering cost of capital surcharges (TCFD Climate Transition Plan guidance).' },
  5: { title: 'TCFD Physical Risk + Climate Tipping Points', desc: 'Physical climate risks include tipping points — irreversible thresholds where small changes trigger cascading, self-reinforcing feedback loops. Once crossed, NCD costs permanently compound. The Paris Agreement\'s 1.5°C target aims to avoid these.' },
  6: { title: 'EU AI Act + Carbon Accounting Data Integrity', desc: 'The EU AI Act requires fairness audits for high-risk AI. In Advanced Climate mode, the "truth premium" also reflects carbon accounting integrity — greenwashing AI is doubly penalised.' },
  7: { title: 'Circular Economy + Green Fund Economics', desc: 'Circular economy investments are subsidised by your Green Transition Fund. The fund is self-replenishing: internal carbon fees automatically top it up. Teams that decarbonise reduce their carbon tax, but also reduce their fund inflow — a strategic tension.' },
  8: { title: 'Natural Capital Accounting + NCD Forgiveness', desc: 'The Natural Capital Protocol (NCC) quantifies ecological dependencies. In this simulation, NCD accrues compound interest. Green CapEx investment now reduces NCD (0.5 per $1M), creating a pathway out of the death spiral — the "forgiveness mechanism".' },
  9: { title: 'Just Transition + Managed Retreat', desc: 'The ILO\'s Just Transition framework meets climate retreat strategy. If tipping point is active but avg carbon intensity drops below 50, hostility is reduced by 25% — the "managed retreat" bonus. This teaches that aggressive late-stage decarbonisation still has value.' },
  10: { title: 'Terminal Value + Climate-Adjusted Multiples', desc: 'DCF terminal value is adjusted by the Regenerative Multiple, which now incorporates: cumulative carbon tax paid, NCD reduction trajectory, green fund utilisation ratio, and whether tipping point was triggered. Climate leadership directly impacts exit valuation.' },
};

// ── Climate Briefing Supplements (R1-R10) ─────────────────────
const CLIMATE_BRIEFING_SUPPLEMENTS = {
  1: '🌡️ Climate Engine Active: This session uses the Advanced Climate Engine. Starting from Round 2, Muressons will charge an internal carbon fee based on your business unit emissions. Use this round to understand your carbon intensity baseline.',
  2: '🌡️ Climate Engine: Your first internal carbon fee will be deducted at the end of this round. The fee (emissions × $/tonne) flows directly into your Green Transition Fund — a subsidy pool for future green investments.',
  3: '🌍 Climate Intelligence: The Internal Carbon Fee is now active. Each tonne of CO₂e emissions is taxed and transferred to your Green Transition Fund. High-carbon decisions now have a direct financial cost.',
  4: '🌍 Climate Intelligence: Watch your business unit carbon intensity. Units above 120 trigger stranded asset penalties (+1.5% cost of capital). Prior audit quality amplifies or dampens contagion severity.',
  5: '🌍 Climate Intelligence: The Tipping Point evaluation happens at the end of this round. If average carbon intensity exceeds 70, irreversible climate feedback loops activate — permanently doubling NCD hostility.',
  6: '🌍 Climate Intelligence: Your carbon fee continues to accumulate. Teams paying high fees should utilise their Green Fund — it subsidises all CapEx automatically. Ethical AI decisions also affect carbon accounting integrity.',
  7: '🌍 Climate Intelligence: Your Green Fund balance subsidises circular economy investments. Decarbonisation choices here can trigger the managed retreat bonus if the tipping point is already active.',
  8: '🌍 Climate Intelligence: NCD Forgiveness is active: every $1M of green CapEx reduces NCD by 0.5 per BU. Teams in NCD death spirals can invest their way out through aggressive water and nature-based infrastructure.',
  9: '🌍 Climate Intelligence: If the tipping point is active AND average carbon intensity has dropped below 50, the managed retreat mechanism activates — reducing hostility from 2× to 1.5×.',
  10: '🌍 Climate Intelligence: Your terminal valuation now includes the full climate trajectory. Cumulative carbon tax, NCD trajectory, green fund strategy, and tipping point status all factor into the Regenerative Multiple.',
};

// ── Stochastic probability labels (vague, not exact) ──────────
function getStochasticIndicator(roundNumber) {
  if (roundNumber === 5) {
    return {
      label: 'Cyclone Landfall Probability',
      level: 'HIGH',
      barPercent: 78,
      color: 'var(--danger)',
      description: 'Meteorological models indicate a high probability of direct impact on your manufacturing corridor.',
    };
  }
  if (roundNumber === 9) {
    return {
      label: 'Strike Probability (if Social License is low)',
      level: 'MODERATE–HIGH',
      barPercent: 55,
      color: 'var(--caution)',
      description: 'Labour unrest models suggest a moderate-to-high probability of industrial action if workforce morale remains low.',
    };
  }
  return null;
}

/** Turn a pasted video URL into something embeddable.
 *  YouTube / Vimeo links become their iframe-embed equivalents; anything else
 *  (mp4/webm on a CDN or the server data dir) plays in a native <video>. */
function toEmbed(url) {
  if (!url) return null;
  try {
    const u = new URL(url);
    const host = u.hostname.replace(/^www\./, '');
    if (host === 'youtube.com' || host === 'm.youtube.com') {
      const id = u.searchParams.get('v') || u.pathname.match(/\/(?:embed|shorts)\/([\w-]{6,})/)?.[1];
      if (id) return { kind: 'iframe', src: `https://www.youtube.com/embed/${id}` };
    }
    if (host === 'youtu.be') {
      const id = u.pathname.slice(1).split('/')[0];
      if (id) return { kind: 'iframe', src: `https://www.youtube.com/embed/${id}` };
    }
    if (host === 'vimeo.com') {
      const id = u.pathname.match(/\/(\d+)/)?.[1];
      if (id) return { kind: 'iframe', src: `https://player.vimeo.com/video/${id}` };
    }
    if (host === 'player.vimeo.com' || u.pathname.includes('/embed/')) {
      return { kind: 'iframe', src: url };
    }
    return { kind: 'video', src: url };
  } catch { return null; }
}

export default function RoundBriefing({
  roundNumber, isHealthcare, isSDG, decisionParadigm, onProceed,
  prevRoundData, activeFlags, globalState, businessUnits, sessionMeta,
  briefingVideoUrl,
  onLogout,
  // TIMER-2 (UX audit #15): the briefing is an early return that unmounts the
  // cockpit header, so a timed round's countdown would vanish while a player
  // reads. The page passes its pacing chip in here so the clock stays on
  // screen through the sub-flow.
  pacingChip = null,
  // Cohort player-visibility check, threaded from the page. Defaults to
  // fail-open so the briefing renders in full when mounted standalone.
  isPlayerVisible = () => true,
}) {
  // ── Derive SimContext from live session data and resolve briefing ──────────
  const tokenMap = deriveSimContext(businessUnits, sessionMeta);
  const baseDictionary = isSDG ? SDG_BRIEFINGS : isHealthcare ? HEALTHCARE_BRIEFINGS : STANDARD_BRIEFINGS;
  const b = resolveBriefing(baseDictionary[roundNumber], tokenMap);
  if (!b) return null;

  const isClimate = decisionParadigm === 'advanced_climate';

  const [recapOpen, setRecapOpen] = useState(false);
  // Read | Watch choice — Watch appears only when the facilitator configured
  // a video for this round (URL-only config; media is hosted externally).
  // Resolved ONCE, so the Read | Watch control and the video pane below can
  // never disagree. Two consequences worth stating: a cohort with the
  // briefing_video switch off is read-only even where URLs are configured, and
  // if the switch is turned off while a player is sitting in watch mode, the
  // next poll drops them back to the written briefing rather than a blank frame.
  const briefingEmbed = isPlayerVisible('briefing_video') ? toEmbed(briefingVideoUrl) : null;
  const [briefingMode, setBriefingMode] = useState('read');
  const [confirmLogout, setConfirmLogout] = useState(false);
  // Player briefing academic framing: OFF by default; facilitator can re-enable.
  const [showTheory, setShowTheory] = useState(false);
  useEffect(() => {
    let alive = true;
    fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/global-settings`)
      .then(r => (r.ok ? r.json() : {}))
      .then(d => { if (alive) setShowTheory(!!(d && d.briefing_theory_enabled)); })
      .catch(() => {});
    return () => { alive = false; };
  }, []);

  // Collect relevant butterfly hints
  const butterflyHints = (activeFlags || [])
    .filter(flag => BUTTERFLY_HINTS[flag])
    .map(flag => BUTTERFLY_HINTS[flag]);

  const theory = isClimate ? (CLIMATE_THEORY_CARDS[roundNumber] || THEORY_CARDS[roundNumber]) : THEORY_CARDS[roundNumber];
  const voices = STAKEHOLDER_VOICES[roundNumber] || [];
  const stochastic = getStochasticIndicator(roundNumber);
  const climateSupplement = isClimate ? localiseAuthored(CLIMATE_BRIEFING_SUPPLEMENTS[roundNumber]) : null;

  // ── CSRD / Industry Vertical context from globalState ──────────────────────
  const flags = globalState?.active_event_flags || {};
  const industryVerticalApplied = flags.industry_vertical_applied;
  const industryVerticalLabel = globalState?.industry_vertical_label;
  const industryVerticalIcon  = globalState?.industry_vertical_icon || '🏢';
  const materialityAligned  = flags.materiality_aligned === true;
  const materialityIgnored  = flags.materiality_ignored === true;
  const materialityStatus   = globalState?.materiality_status; // 'aligned' | 'ignored' | undefined
  const showMaterialityChip = roundNumber >= 3 && (materialityAligned || materialityIgnored);

  // Preliminary valuation estimate (after R5)
  const showValuation = roundNumber > 5 && globalState;
  let valuationEstimate = null;
  if (showValuation && globalState) {
    const treasury = globalState.corporate_treasury || 0;
    const synergy = globalState.synergy_multiplier || 1.0;
    const rep = globalState.group_reputation || 50;
    const ebitda = Math.abs(globalState.historical_ebitda || 0);
    // Use EBITDA-based valuation: ebitda × exit_multiple × M_R_proxy
    // M_R proxy = synergy × (rep / 60) × reputation premium
    const mrProxy = Math.max(0.4, synergy * (rep / 60));
    const exitMultiple = 12.0; // Matches R10 config
    // If EBITDA is available, use it; otherwise fall back to treasury-based
    const baseEbitda = ebitda > 0 ? ebitda : Math.max(treasury * 0.08, 2_000_000);
    const terminalValue = baseEbitda * exitMultiple * mrProxy;
    const low = Math.round(atRate(Math.max(terminalValue * 0.75, 0)) / 1_000_000);
    const high = Math.round(atRate(Math.max(terminalValue * 1.30, 0)) / 1_000_000);
    valuationEstimate = { low, high };
  }

  return (
    <div className={styles.overlay}>
      {/* Logout button — top-right, always visible */}
      {onLogout && (
        <button
          onClick={() => {
            if (confirmLogout) { onLogout(); setConfirmLogout(false); }
            else setConfirmLogout(true);
          }}
          onBlur={() => setConfirmLogout(false)}
          title={confirmLogout ? 'Click again to confirm logout' : 'Logout & Exit Simulation'}
          style={{
            ...logoutAnchorStyle(19100),
            display: 'flex', alignItems: 'center', gap: 6, padding: '6px 14px',
            background: confirmLogout ? 'rgba(127,29,29,0.9)' : 'rgba(15,23,42,0.75)',
            backdropFilter: 'blur(8px)',
            border: confirmLogout ? '1px solid var(--danger-text)' : '1px solid rgba(248,113,113,0.25)',
            borderRadius: 8, color: confirmLogout ? '#fff' : '#fca5a5',
            fontSize: '0.72rem', fontWeight: 700, fontFamily: "'DM Sans', system-ui, sans-serif",
            cursor: 'pointer',
            transition: 'background 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease',
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          }}
        >
          {confirmLogout ? '⚠️ Confirm Logout?' : '🚪 Logout'}
        </button>
      )}
      <div className={styles.container}>
        {/* ── Header ── */}
        <header className={styles.header}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <div className={styles.roundBadge}>ROUND {roundNumber} OF 10</div>
            {decisionParadigm === 'advanced_climate' && (
              <div style={{
                padding: '2px 8px', borderRadius: 4,
                background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.35)',
                fontSize: '0.6rem', fontWeight: 700, color: '#6ee7b7', letterSpacing: '0.06em', textTransform: 'uppercase',
              }}>
                🌡️ Advanced Climate Engine
              </div>
            )}
            {/* Industry Vertical Blueprint pill — shown on R2 when blueprint applied */}
            {roundNumber === 2 && industryVerticalApplied && (
              <div style={{
                padding: '2px 10px', borderRadius: 4,
                background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.4)',
                fontSize: '0.6rem', fontWeight: 700, color: '#a5b4fc', letterSpacing: '0.06em', textTransform: 'uppercase',
              }} title={`Industry Vertical Blueprint active: ${industryVerticalLabel}`}>
                {industryVerticalIcon} {industryVerticalLabel || industryVerticalApplied} Blueprint
              </div>
            )}
            {/* CSRD materiality status chip — shown R3 onwards */}
            {showMaterialityChip && (
              <div style={{
                padding: '2px 10px', borderRadius: 4,
                background: materialityAligned ? 'rgba(16,185,129,0.12)' : 'rgba(245,158,11,0.12)',
                border: `1px solid ${materialityAligned ? 'rgba(16,185,129,0.35)' : 'rgba(245,158,11,0.4)'}`,
                fontSize: '0.6rem', fontWeight: 700,
                color: materialityAligned ? '#6ee7b7' : '#fcd34d',
                letterSpacing: '0.06em', textTransform: 'uppercase',
              }} title={
                localiseAuthored(materialityAligned
                  ? 'R2 materiality aligned: +0.10 M_R at R10 · −$500K Green Bond (R3 Option B)'
                  : 'R2 materiality gaps: +$1M Green Bond risk premium (R3 Option B)')
              }>
                {materialityAligned ? '✅ CSRD Aligned +0.10 M_R' : '⚠️ CSRD Gap — R3 Penalty'}
              </div>
            )}
          </div>
          <div className={styles.titleRow}>
            <span className={styles.icon}>{b.icon}</span>
            <h1 className={styles.title}>{b.title}</h1>
          </div>
          <p className={styles.theme}>{b.theme}</p>
        </header>

        {/* ── Document Body ── */}
        <div className={styles.document}>
          <div className={styles.docHeader}>
            <span className={styles.docIcon}>📄</span>
            <h2 className={styles.docTitle}>Intelligence Briefing</h2>
            {briefingEmbed && (
              <div role="group" aria-label="Briefing format" style={{ display: 'inline-flex', gap: 2, padding: 2, borderRadius: 999, background: 'rgba(148,163,184,0.12)', border: '1px solid rgba(148,163,184,0.2)', marginLeft: 12 }}>
                {[['read', '📄 Read'], ['watch', '🎬 Watch']].map(([m, label]) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setBriefingMode(m)}
                    aria-pressed={briefingMode === m}
                    style={{
                      padding: '3px 12px', borderRadius: 999, border: 'none', cursor: 'pointer',
                      fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.04em',
                      background: briefingMode === m ? 'var(--accent-blue)' : 'transparent',
                      color: briefingMode === m ? '#fff' : 'inherit',
                    }}
                  >{label}</button>
                ))}
              </div>
            )}
            <span className={styles.stamp}>{b.stamp}</span>
          </div>

          {/* Previous Round Recap */}
          {prevRoundData && roundNumber > 1 && isPlayerVisible('briefing_last_round_recap') && (
            <div className={styles.recapPanel}>
              <button className={styles.recapToggle} onClick={() => setRecapOpen(!recapOpen)}>
                <span>📋 Last Round Summary</span>
                <span className={`${styles.recapChevron} ${recapOpen ? styles.recapChevronOpen : ''}`}>▸</span>
              </button>
              {recapOpen && (
                <div className={styles.recapContent}>
                  {prevRoundData.choice && (
                    <div className={styles.recapRow}>
                      <span className={styles.recapLabel}>Decision Made</span>
                      <span className={styles.recapValueNeutral}>{prevRoundData.choice}</span>
                    </div>
                  )}
                  {prevRoundData.treasury_delta !== undefined && (
                    <div className={styles.recapRow}>
                      <span className={styles.recapLabel}>Treasury Impact</span>
                      <span className={prevRoundData.treasury_delta >= 0 ? styles.recapValuePositive : styles.recapValueNegative}>
                        {prevRoundData.treasury_delta >= 0 ? '+' : ''}{(prevRoundData.treasury_delta / 1_000_000).toFixed(1)}M
                      </span>
                    </div>
                  )}
                  {prevRoundData.reputation_delta !== undefined && (
                    <div className={styles.recapRow}>
                      <span className={styles.recapLabel}>Reputation Change</span>
                      <span className={prevRoundData.reputation_delta >= 0 ? styles.recapValuePositive : styles.recapValueNegative}>
                        {prevRoundData.reputation_delta >= 0 ? '+' : ''}{prevRoundData.reputation_delta}
                      </span>
                    </div>
                  )}
                  {prevRoundData.events?.strike_triggered === true && (
                    <div className={styles.recapRow}>
                      <span className={styles.recapLabel}>⚠️ Strike</span>
                      <span className={styles.recapValueNegative}>Workers went on strike</span>
                    </div>
                  )}
                  {prevRoundData.events?.climate_event_struck === true && (
                    <div className={styles.recapRow}>
                      <span className={styles.recapLabel}>🌪️ Climate Event</span>
                      <span className={styles.recapValueNegative}>Cyclone struck — {currencySymbol()}{atRate((prevRoundData.events.actual_damage || 0) / 1_000_000).toFixed(1)}M damage</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Narrative */}
          {briefingEmbed && briefingMode === 'watch' ? (
            <div style={{ marginBottom: 16 }}>
              <div style={{ position: 'relative', width: '100%', paddingTop: '56.25%', borderRadius: 10, overflow: 'hidden', background: '#000' }}>
                {briefingEmbed.kind === 'iframe' ? (
                  <iframe
                    src={briefingEmbed.src}
                    title={`Round ${roundNumber} briefing video`}
                    style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', border: 0 }}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                ) : (
                  <video
                    src={briefingEmbed.src}
                    controls
                    playsInline
                    style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
                  />
                )}
              </div>
              <div style={{ marginTop: 6, fontSize: '0.68rem', opacity: 0.7 }}>
                Prefer text? Switch to 📄 Read above — the written briefing carries the same content.
              </div>
            </div>
          ) : (
          <div className={styles.narrative}>
            {b.narrative.map((para, i) => (
              <p key={i} dangerouslySetInnerHTML={{ __html: sanitizeHtml(showTheory ? para : stripPedagogy(para)) }} />
            ))}
          </div>
          )}

          {/* Climate Intelligence Supplement (Advanced Climate Only) */}
          {climateSupplement && (
            <div style={{
              padding: '14px 16px', borderRadius: 10, marginBottom: 16,
              background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)',
              borderLeft: '3px solid var(--kpi-good)',
            }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--kpi-good)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 6 }}>
                🌍 Climate Engine Intelligence
              </div>
              <div style={{ fontSize: '0.8rem', color: '#a7f3d0', lineHeight: 1.6 }}>
                {climateSupplement}
              </div>
              {globalState && (
                <div style={{ marginTop: 10, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ padding: '4px 10px', borderRadius: 6, background: 'rgba(15,23,42,0.5)', fontSize: '0.68rem', color: '#94a3b8' }}>
                    💰 Green Fund: <strong style={{ color: 'var(--positive-text)' }}>{currencySymbol()}{atRate((globalState.green_transition_fund || 0) / 1_000_000).toFixed(1)}M</strong>
                  </div>
                  <div style={{ padding: '4px 10px', borderRadius: 6, background: 'rgba(15,23,42,0.5)', fontSize: '0.68rem', color: '#94a3b8' }}>
                    📊 Cost of Capital: <strong style={{ color: (globalState.cost_of_capital || 0.05) > 0.06 ? 'var(--danger)' : '#f8fafc' }}>{((globalState.cost_of_capital || 0.05) * 100).toFixed(1)}%</strong>
                  </div>
                  <div style={{ padding: '4px 10px', borderRadius: 6, background: 'rgba(15,23,42,0.5)', fontSize: '0.68rem', color: '#94a3b8' }}>
                    🌡️ Tipping Point: <strong style={{ color: globalState.tipping_point_active ? 'var(--danger)' : 'var(--kpi-good)' }}>{globalState.tipping_point_active ? 'ACTIVE' : 'Stable'}</strong>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Butterfly Effect Panel */}
          {butterflyHints.length > 0 && isPlayerVisible('briefing_butterfly_hints') && (
            <div className={styles.butterflyPanel}>
              <div className={styles.butterflyHeader}>
                <span>🦋</span> Your earlier decisions shape this crisis...
              </div>
              {butterflyHints.slice(0, 3).map((hint, i) => (
                <div key={i} className={styles.butterflyHint}>{hint}</div>
              ))}
            </div>
          )}

          {/* Stochastic Probability Display */}
          {stochastic && (
            <div className={styles.stochasticPanel}>
              <div className={styles.stochasticHeader}>🎲 {stochastic.label}</div>
              <div className={styles.stochasticBar}>
                <div
                  className={styles.stochasticFill}
                  style={{ width: `${stochastic.barPercent}%`, background: stochastic.color }}
                />
              </div>
              <div className={styles.stochasticLabel}>
                Threat Level: {stochastic.level}
              </div>
              <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginTop: '0.3rem' }}>
                {stochastic.description}
              </div>
              {/* Determinism chip — makes the seeded-RNG fairness guarantee visible */}
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.35rem',
                marginTop: '0.5rem', padding: '0.25rem 0.55rem', borderRadius: '999px',
                fontSize: '0.66rem', fontWeight: 600,
                background: 'rgba(99,102,241,0.12)', color: 'var(--accent)',
                border: '1px solid rgba(99,102,241,0.35)',
              }} title="Outcomes are seeded per cohort, so this event rolls identically for every team. Results reflect strategy, not luck.">
                🎲 Shared dice — every team faces the identical roll
              </div>
            </div>
          )}

          {/* Two-column bottom grid: Left = objectives + metrics, Right = warning + theory + voices */}
          <div className={styles.docBottomGrid}>
            {/* Left Column */}
            <div>
              {/* Strategic Objectives */}
              <div className={styles.sectionTitle}>
                <span className={styles.sectionIcon}>🎯</span>
                Strategic Objectives
              </div>
              <ul className={styles.objectivesList}>
                {b.objectives.map((obj, i) => (
                  <li key={i}>{obj}</li>
                ))}
              </ul>

              {/* Key Metrics */}
              <div className={styles.sectionTitle}>
                <span className={styles.sectionIcon}>📊</span>
                Key Metrics to Watch
              </div>
              <div className={styles.metricsRow}>
                {b.metrics.map((m, i) => (
                  <div key={i} className={styles.metricChip}>
                    <span className={styles.metricIcon}>{m.icon}</span>
                    <span className={styles.metricLabel}>{m.label}</span>
                  </div>
                ))}
              </div>

              {/* Warning */}
              {b.warning && (
                <div className={styles.warningBox}>
                  <span className={styles.warningIcon}>⚠️</span>
                  <div
                    className={styles.warningText}
                    dangerouslySetInnerHTML={{ __html: sanitizeHtml(b.warning.text) }}
                  />
                </div>
              )}
            </div>

            {/* Right Column */}
            <div>
              {/* Theory Card — player-hidden unless briefing_theory_enabled;
                  the cohort switch is a further veto on top of that flag. */}
              {showTheory && theory && isPlayerVisible('briefing_theory_card') && (
                <div className={styles.theoryCard}>
                  <div className={styles.theoryHeader}>
                    <span>📚</span> Academic Framework
                  </div>
                  <div className={styles.theoryTitle}>{theory.title}</div>
                  <p className={styles.theoryDesc}>{localiseAuthored(theory.desc)}</p>
                </div>
              )}

              {/* Stakeholder Voices */}
              {voices.length > 0 && isPlayerVisible('briefing_stakeholder_voices') && (
                <div className={styles.voicesPanel}>
                  <div className={styles.voicesTitle}>💬 Stakeholder Voices</div>
                  {voices.map((v, i) => (
                    <div key={i} className={styles.voiceQuote}>
                      <span className={styles.voiceAvatar}>{v.avatar}</span>
                      <div className={styles.voiceContent}>
                        <p className={styles.voiceText}>{v.text}</p>
                        <div className={styles.voiceRole}>— {v.role}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Preliminary Valuation (after R5) */}
              {valuationEstimate && isPlayerVisible('briefing_midgame_valuation') && (
                <div className={styles.valuationCard}>
                  <div className={styles.valuationHeader}>📈 Mid-Game Valuation Estimate</div>
                  <div className={styles.valuationRange}>
                    {currencySymbol()}{valuationEstimate.low}M — {currencySymbol()}{valuationEstimate.high}M
                  </div>
                  <div className={styles.valuationNote}>
                    Estimated terminal value based on current trajectory. Subject to remaining decisions.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Proceed Button ── */}
        <div className={styles.footer}>
          {pacingChip && (
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 10 }}>
              {pacingChip}
            </div>
          )}
          {/* OBJ-1 (UX audit #10): the scored objective, stated where every
              player will read it — previously it surfaced nowhere before
              Round 10. One sentence, first briefing only. */}
          {roundNumber === 1 && (
            <p style={{
              margin: '0 0 10px', fontSize: '0.78rem', lineHeight: 1.55,
              color: 'var(--text-secondary)', textAlign: 'center', maxWidth: 560,
              marginLeft: 'auto', marginRight: 'auto',
            }}>
              <strong style={{ color: 'var(--accent)' }}>Your objective:</strong>{' '}
              finish Year 5 with the strongest Terminal Valuation and Regenerative
              Multiple (M_R) — the score that prices your profits and your impact together.
            </p>
          )}
          <button className={styles.proceedBtn} onClick={onProceed}>
            Begin Simulation →
          </button>
        </div>
      </div>
    </div>
  );
}
// tier1: determinism chip added

