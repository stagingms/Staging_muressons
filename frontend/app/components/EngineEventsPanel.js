import React from 'react';
import { currencySymbol, money, atRate } from '../utils/format';

/**
 * EngineEventsPanel — Expanded simulation engine event display.
 * Surfaces 20+ engine events with plain-language tooltips.
 */

const EVENT_TOOLTIPS = {
  inflation: 'Year-over-year cost inflation applied to OPEX. Erodes margins if not managed.',
  tech_lock_in: 'Repeated investment in legacy systems triggers switching costs and reduced agility.',
  greenwashing: 'Cosmetic ESG spending without substance detected. Reputation takes a hidden penalty.',
  cogs_penalty: 'Supply chain drag has increased your cost of goods sold.',
  cannibalization: 'One dominant BU is eating into market share of your other BUs.',
  dividend_ratchet: 'Cutting dividends after stable payouts severely damages board confidence.',
  stakeholder_fatigue: 'Repeated crises have degraded stakeholder trust. Recovery costs increase.',
  brain_drain: 'Top talent is fleeing due to poor working conditions or governance.',
  technical_debt: 'Deferred infrastructure upgrades have triggered unavoidable capital costs.',
  supply_chain_contagion: 'A crisis in one BU is spilling over, amplifying costs across the group.',
  fog_of_war: 'Competitor data is hidden. You are making decisions with incomplete market visibility.',
  npc_competitor: 'The NPC competitor is growing steadily. Falling behind means losing market share.',
  ncd_interest: 'Natural Capital Debt is accruing interest. High debt leads to runaway ecological costs.',
  insolvency: 'Treasury has breached critical levels. Austerity measures are now mandatory.',
  burnout: 'Staff burnout is affecting operational efficiency and increasing OPEX.',
  strike_warning: 'Worker discontent is rising. Strike probability is elevated in low-SLO BUs.',
  revenue_generation: 'A previous infrastructure investment is now generating recurring revenue.',
  implementation_lag: 'Benefits from recent investments have not yet been realized.',
  regulatory_ratchet: 'Escalating compliance costs are permanently elevating cost of capital.',
  climate_tipping: 'Environmental thresholds crossed — irreversible acceleration of NCD costs.',
  desalination_payback: 'Desalination plant is generating revenue to offset initial investment.',
  early_decarboniser: 'Early supply chain decarbonisation has unlocked a strategic synergy bonus.',
  insolvency_capex_cap: 'CapEx spending is capped at 50% due to insolvency austerity measures.',
  internal_carbon_fee: 'Your emissions generate an internal carbon fee that funds the Green Transition Fund. Higher emissions = higher tax.',
  green_fund_used: 'Your Green Transition Fund subsidised part of your capital expenditure, reducing the treasury impact.',
  stranded_asset: 'Business units with carbon intensity above 120 are classified as stranded assets, triggering a cost of capital surcharge.',
  inflation_drift: 'Hostile regulatory environment is driving system-wide inflation above baseline, compounding OPEX costs each round.',
  managed_retreat: 'Carbon intensity has dropped significantly, partially mitigating tipping point damage — but the tipping point remains irreversible.',
  ncd_forgiveness: 'Green CapEx investment is actively reducing your Natural Capital Debt, slowing the penalty escalation.',
  // ── HARDENING PHASE ──
  macro_rate: 'Central bank monetary policy cycle affecting your cost of capital. Rates cycle through easing → neutral → tightening every 3 rounds.',
  fx_risk: 'Foreign exchange movements have impacted your multinational revenue streams. BUs with higher international exposure are more affected.',
  dso_working_capital: 'Days Sales Outstanding (DSO) timing has deferred revenue collection. Higher governance risk increases DSO.',
  scope3_data: 'Scope 3 emissions data availability varies based on your supply chain transparency strategy.',
  social_media_velocity: 'Social media amplification is accelerating reputational damage. Digital scrutiny intensifies each round.',
  nbs_uncertainty: 'Nature-based solutions face ecological uncertainty. Mangrove restoration has a 75% success rate.',
  eu_ai_act: 'EU AI Act compliance costs are now active. High-risk AI deployment triggers governance surcharges and audit requirements.',
  workforce_retraining: 'Workforce retraining program outcomes depend on your social licence. Lower trust = higher failure rate.',
  pathway_discovery: 'Your decisions have seeded a hidden ending pathway. The full foreshadowing chain will be revealed at the end.',
  board_pressure: 'The board is exerting pressure based on accumulated performance signals and strategic direction.',
  stakeholder_salience: 'Stakeholder power, legitimacy, and urgency have shifted based on your decisions (Mitchell/Agle/Wood framework).',
};

// V-A (player v2): `sections` controls which accordion groups render so the
// retrospect (What Happened This Round + Road Not Taken) can live in the
// results stage while the rail keeps the rest. 'all' preserves the original
// behaviour for any untouched caller.
//   'all'        → everything (default, pre-V-A behaviour)
//   'retrospect' → What Happened This Round + Road Not Taken only
//   'rest'       → everything else (CEO Diary)
export default function EngineEventsPanel({ globalState, roundEvents, sections = 'all' }) {
  const showRetrospect = sections === 'all' || sections === 'retrospect';
  const showRest = sections === 'all' || sections === 'rest';
  const flags = globalState?.active_event_flags || {};
  const events = [];

  // 1. Inflation
  if (flags.inflation_active || globalState?.inflation_index > 1.0) {
    const rate = ((globalState?.inflation_index - 1) * 100).toFixed(1);
    const displayRate = rate !== "NaN" && rate > 0 ? rate : "2.5";
    events.push({ icon: '📈', color: 'var(--caution)', text: `Inflation increased OPEX by ${displayRate}%.`, tooltip: EVENT_TOOLTIPS.inflation });
  }

  // 2. Tech Lock-in
  if (flags.tech_lock_in_active) {
    events.push({ icon: '🔒', color: 'var(--danger)', text: 'Technology Lock-In active — synergy penalty on non-dominant BUs.', tooltip: EVENT_TOOLTIPS.tech_lock_in });
  }

  // 3. Greenwashing
  if (flags.greenwashing_penalty_active) {
    events.push({ icon: '🎭', color: 'var(--danger)', text: 'Greenwashing detected! Severe reputation penalty applied.', tooltip: EVENT_TOOLTIPS.greenwashing });
  }

  // 4. COGS Penalty
  if (flags.cogs_penalty_ratio > 1) {
    events.push({ icon: '⚙️', color: 'var(--caution)', text: `Supply chain drag increased COGS by ${((flags.cogs_penalty_ratio - 1) * 100).toFixed(1)}%.`, tooltip: EVENT_TOOLTIPS.cogs_penalty });
  }

  // 5. Revenue Cannibalization
  if (flags.cannibalization_active) {
    events.push({ icon: '🔄', color: 'var(--caution)', text: 'Product cannibalization reduced revenue efficiency.', tooltip: EVENT_TOOLTIPS.cannibalization });
  }

  // 6. Dividend Ratchet
  if (flags.dividend_ratchet_triggered || roundEvents?.dividend_ratchet_triggered) {
    events.push({ icon: '📉', color: 'var(--danger)', text: 'Dividend ratchet triggered — board confidence has dropped.', tooltip: EVENT_TOOLTIPS.dividend_ratchet });
  }

  // 7. Stakeholder Fatigue
  if (flags.stakeholder_fatigue_applied || roundEvents?.stakeholder_fatigue_applied) {
    events.push({ icon: '😓', color: 'var(--caution)', text: 'Stakeholder fatigue — recovering reputation is now more expensive.', tooltip: EVENT_TOOLTIPS.stakeholder_fatigue });
  }

  // 8. Brain Drain / Talent Flight
  if (flags.talent_flight_triggered || roundEvents?.talent_penalty_applied) {
    const penalty = roundEvents?.talent_penalty_applied;
    events.push({ icon: '🧠', color: 'var(--danger)', text: `Talent brain-drain risk${penalty ? ` — OPEX surcharge applied` : ' detected'}.`, tooltip: EVENT_TOOLTIPS.brain_drain });
  }

  // 9. Technical Debt
  const techDebtKeys = Object.keys(roundEvents || {}).filter(k => k.startsWith('technical_debt_penalty_'));
  if (techDebtKeys.length > 0) {
    const buNames = techDebtKeys.map(k => k.replace('technical_debt_penalty_', '')).join(', ');
    events.push({ icon: '🏗️', color: 'var(--caution)', text: `Technical debt penalty applied to: ${buNames}.`, tooltip: EVENT_TOOLTIPS.technical_debt });
  }

  // 10. Supply Chain Contagion
  if (roundEvents?.contagion_spike_triggered || flags.supply_chain_contagion) {
    events.push({ icon: '🦠', color: 'var(--danger)', text: 'Contagion spreading — crisis damage amplified across all BUs.', tooltip: EVENT_TOOLTIPS.supply_chain_contagion });
  }

  // 11. Fog of War
  if (flags.fog_of_war_active) {
    events.push({ icon: '🌫️', color: 'var(--accent)', text: 'Fog of War active — competitor data hidden from view.', tooltip: EVENT_TOOLTIPS.fog_of_war });
  }

  // 12. NPC Competitor Growth
  if (roundEvents?.competitor_warning || flags.competitor_warning) {
    events.push({ icon: '🏢', color: 'var(--accent)', text: 'NPC competitor is growing at 3%/round — monitor your market position.', tooltip: EVENT_TOOLTIPS.npc_competitor });
  }

  // 13. NCD Interest
  if (roundEvents?.interest_rates) {
    const rates = roundEvents.interest_rates;
    const highDebtBUs = Object.entries(rates).filter(([, r]) => r > 0.06);
    if (highDebtBUs.length > 0) {
      const names = highDebtBUs.map(([name]) => name).join(', ');
      events.push({ icon: '🌿', color: 'var(--caution)', text: `High NCD interest accruing on: ${names}.`, tooltip: EVENT_TOOLTIPS.ncd_interest });
    }
  }

  // 14. Insolvency
  if (roundEvents?.insolvency_active) {
    events.push({ icon: '🚨', color: 'var(--danger)', text: roundEvents.insolvency_message || 'CREDIT DOWNGRADE — austerity measures active.', tooltip: EVENT_TOOLTIPS.insolvency });
  }

  // 15. Insolvency CapEx Cap
  if (roundEvents?.capex_cap_multiplier && roundEvents.capex_cap_multiplier < 1.0) {
    events.push({ icon: '🔻', color: 'var(--danger)', text: `CapEx capped at ${Math.round(roundEvents.capex_cap_multiplier * 100)}% due to insolvency.`, tooltip: EVENT_TOOLTIPS.insolvency_capex_cap });
  }

  // 16. Staff Burnout (Healthcare)
  const burnoutKeys = Object.keys(roundEvents || {}).filter(k => k.startsWith('utilization_overload_fatigue_'));
  if (burnoutKeys.length > 0) {
    events.push({ icon: '🩺', color: 'var(--caution)', text: 'Staff burnout increasing due to bed utilization overload.', tooltip: EVENT_TOOLTIPS.burnout });
  }

  // 17. Strike Warning
  if (roundEvents?.strike_probabilities) {
    const highRisk = Object.entries(roundEvents.strike_probabilities).filter(([, p]) => p > 0.3);
    if (highRisk.length > 0) {
      const names = highRisk.map(([name]) => name).join(', ');
      events.push({ icon: '✊', color: 'var(--danger)', text: `Elevated strike risk in: ${names}.`, tooltip: EVENT_TOOLTIPS.strike_warning });
    }
  }

  // 18. Revenue Generation (Desalination payback)
  if (roundEvents?.revenue_generation_completed) {
    const amt = (atRate(roundEvents.revenue_generation_completed) / 1_000_000).toFixed(1);
    events.push({ icon: '💧', color: '#10b981', text: `Infrastructure investment generated ${currencySymbol()}${amt}M revenue.`, tooltip: EVENT_TOOLTIPS.revenue_generation });
  }

  // 19. Implementation Lag
  if (flags.implementation_lag || roundEvents?.resilience_project_started || roundEvents?.ncd_project_started) {
    events.push({ icon: '⏳', color: 'var(--accent)', text: 'Infrastructure project underway — benefits pending maturation.', tooltip: EVENT_TOOLTIPS.implementation_lag });
  }

  // 20. Early Decarboniser Bonus
  if (roundEvents?.early_decarboniser_synergy_bonus) {
    events.push({ icon: '🌱', color: '#10b981', text: 'Early decarbonisation rewarded — synergy bonus (+0.10) applied.', tooltip: EVENT_TOOLTIPS.early_decarboniser });
  }

  // 21. Negative Treasury Interest
  if (roundEvents?.negative_treasury_interest_applied) {
    const interest = (atRate(roundEvents.negative_treasury_interest_applied) / 1_000_000).toFixed(2);
    events.push({ icon: '🏦', color: 'var(--danger)', text: `Debt service: ${currencySymbol()}${interest}M interest charged on negative treasury.`, tooltip: 'Negative treasury balance incurs interest at the cost of capital rate.' });
  }

  // 22. Climate Event
  if (roundEvents?.climate_event_struck) {
    const damage = (atRate((roundEvents.actual_damage || 0)) / 1_000_000).toFixed(1);
    events.push({ icon: '🌪️', color: 'var(--danger)', text: `Cyclone struck! Actual damage: ${currencySymbol()}${damage}M (mitigated by resilience).`, tooltip: 'Physical climate event caused infrastructure damage, reduced by your resilience factor.' });
  } else if (roundEvents?.climate_event_struck === false) {
    events.push({ icon: '🌤️', color: '#10b981', text: 'The cyclone changed course — no damage this round.', tooltip: 'The stochastic climate event did not trigger this time.' });
  }

  // 23. Strike Result
  if (roundEvents?.strike_triggered === true) {
    events.push({ icon: '🚫', color: 'var(--danger)', text: roundEvents.strike_message || 'Worker strike triggered — revenue lost.', tooltip: 'Worker strike caused by low social license and factory closure decisions.' });
  } else if (roundEvents?.strike_triggered === false && roundEvents?.strike_message) {
    events.push({ icon: '🤝', color: '#10b981', text: roundEvents.strike_message, tooltip: 'Strike was narrowly averted.' });
  }

  // ── CLIMATE ENGINE EVENTS (24-31) ──

  // 24. Internal Carbon Fee
  if (roundEvents?.internal_carbon_fee_deducted) {
    const fee = (atRate(roundEvents.internal_carbon_fee_deducted) / 1_000_000).toFixed(2);
    events.push({ icon: '💨', color: '#10b981', text: `Internal carbon fee: ${currencySymbol()}${fee}M deducted → Green Transition Fund.`, tooltip: EVENT_TOOLTIPS.internal_carbon_fee });
  }

  // 25. Green Fund Used
  if (roundEvents?.green_fund_used) {
    const amt = (atRate(roundEvents.green_fund_used) / 1_000_000).toFixed(1);
    events.push({ icon: '🌱', color: '#10b981', text: `Green Fund subsidised ${currencySymbol()}${amt}M of your spending.`, tooltip: EVENT_TOOLTIPS.green_fund_used });
  }

  // 26. Stranded Asset Penalty
  if (roundEvents?.stranded_asset_penalty_applied) {
    const buNames = (roundEvents.stranded_asset_bu_ids || []).join(', ');
    events.push({ icon: '🏚️', color: 'var(--danger)', text: `Stranded asset penalty — Cost of Capital +1.5% [BUs: ${buNames || 'high-carbon units'}].`, tooltip: EVENT_TOOLTIPS.stranded_asset });
  }

  // 27. Inflation Drift (Hostile)
  if (roundEvents?.inflation_drift_hostile) {
    events.push({ icon: '🔥', color: 'var(--caution)', text: roundEvents.inflation_drift_message || 'Hostile regulation driving inflation above baseline.', tooltip: EVENT_TOOLTIPS.inflation_drift });
  }

  // 28. Tipping Point Activation
  if (roundEvents?.tipping_point_reached) {
    events.push({ icon: '🌡️', color: 'var(--danger)', text: 'CLIMATE TIPPING POINT — Irreversible environmental threshold breached. NCD costs doubled.', tooltip: EVENT_TOOLTIPS.climate_tipping });
  }

  // 29. Managed Retreat
  if (roundEvents?.tipping_point_managed_retreat) {
    events.push({ icon: '🌿', color: '#38bdf8', text: 'Managed retreat — Aggressive decarbonisation has reduced tipping point severity by 25%.', tooltip: EVENT_TOOLTIPS.managed_retreat });
  }

  // 30. NCD Forgiveness
  if (roundEvents?.ncd_forgiveness_applied) {
    events.push({ icon: '♻️', color: '#10b981', text: `Green CapEx reduced Natural Capital Debt by ${roundEvents.ncd_forgiveness_applied} per BU.`, tooltip: EVENT_TOOLTIPS.ncd_forgiveness });
  }

  // ── HARDENING PHASE: New Engine Events ──────────────────────

  // 31. Macro Interest Rate Environment
  if (roundEvents?.macro_rate_environment) {
    const macro = roundEvents.macro_rate_environment;
    const regimeIcons = { easing: '🕊️', neutral: '⚖️', tightening: '🦅', crisis: '🔥' };
    const icon = regimeIcons[macro.regime] || '🏦';
    const modPct = macro.modifier_pct;
    events.push({
      icon, color: macro.regime === 'tightening' || macro.regime === 'crisis' ? 'var(--danger)' : macro.regime === 'neutral' ? 'var(--accent)' : '#10b981',
      text: `${macro.label || `${macro.regime} monetary policy`}${modPct ? ` (CoC ${modPct > 0 ? '+' : ''}${modPct}%)` : ''}`,
      tooltip: EVENT_TOOLTIPS.macro_rate,
    });
  }

  // 32. FX Risk
  if (roundEvents?.fx_risk) {
    const fx = roundEvents.fx_risk;
    const dir = fx.fx_direction === 'strengthening' ? '💪' : '📉';
    const pct = Math.abs(fx.fx_index * 100).toFixed(1);
    events.push({
      icon: dir, color: fx.fx_direction === 'strengthening' ? '#10b981' : 'var(--caution)',
      text: `FX ${fx.fx_direction}: ${pct}% currency shift affecting multinational revenue.`,
      tooltip: EVENT_TOOLTIPS.fx_risk,
    });
  }

  // 33. DSO / Working Capital Lag
  if (roundEvents?.dso_working_capital) {
    const dso = roundEvents.dso_working_capital;
    if (dso.total_deferred > 0) {
      const deferred = (atRate(dso.total_deferred) / 1_000_000).toFixed(1);
      events.push({
        icon: '⏰', color: 'var(--accent)',
        text: `Working capital timing: ${currencySymbol()}${deferred}M revenue deferred (DSO drag across BUs).`,
        tooltip: EVENT_TOOLTIPS.dso_working_capital,
      });
    }
  }

  // 34. Scope 3 Data Availability (R3+)
  if (roundEvents?.scope3_data_completeness != null || flags.scope3_data_completeness != null) {
    const completeness = roundEvents?.scope3_data_completeness ?? flags.scope3_data_completeness;
    const icon = completeness >= 70 ? '📊' : completeness >= 50 ? '📋' : '🔍';
    const color = completeness >= 70 ? '#10b981' : completeness >= 50 ? 'var(--caution)' : 'var(--danger)';
    events.push({
      icon, color,
      text: `Scope 3 data completeness: ${completeness}% — ${completeness >= 70 ? 'deep audit provides reliable supply chain emissions data' : completeness >= 50 ? 'partial visibility into supply chain emissions' : 'limited Scope 3 data — high reporting uncertainty'}.`,
      tooltip: EVENT_TOOLTIPS.scope3_data,
    });
  }

  // 35. Social Media Velocity Amplifier (R4+)
  if (roundEvents?.social_media_velocity) {
    const smv = roundEvents.social_media_velocity;
    events.push({
      icon: '📱', color: 'var(--danger)',
      text: smv.message || `Social media velocity amplifier active (${smv.multiplier?.toFixed(1) || ''}×) — reputation penalty: ${smv.reputation_penalty?.toFixed(1) || '?'} pts.`,
      tooltip: EVENT_TOOLTIPS.social_media_velocity,
    });
  }

  // 36. Nature-Based Solution Uncertainty (R5)
  if (roundEvents?.nbs_uncertainty) {
    const nbs = roundEvents.nbs_uncertainty;
    events.push({
      icon: nbs.succeeded ? '🌴' : '🌿',
      color: nbs.succeeded ? '#10b981' : 'var(--danger)',
      text: nbs.message || (nbs.succeeded
        ? 'Mangrove restoration SUCCEEDED — nature-based resilience buffer established.'
        : 'Mangrove restoration FAILED — ecological conditions prevented establishment. Resilience reduced.'),
      tooltip: EVENT_TOOLTIPS.nbs_uncertainty,
    });
  }

  // 37. EU AI Act Compliance (R6→R7+)
  if (roundEvents?.eu_ai_act_compliance) {
    const euAi = roundEvents.eu_ai_act_compliance;
    const cost = (atRate((euAi.cost || 0)) / 1_000_000).toFixed(1);
    events.push({
      icon: '🤖', color: 'var(--danger)',
      text: euAi.message || `EU AI Act compliance: ${currencySymbol()}${cost}M audit and governance costs incurred for AI deployment.`,
      tooltip: EVENT_TOOLTIPS.eu_ai_act,
    });
  } else if (roundEvents?.eu_ai_act_pending) {
    events.push({
      icon: '⚠️', color: 'var(--caution)',
      text: roundEvents.eu_ai_act_pending.message || 'EU AI Act: Your AI deployment is classified as high-risk. Compliance costs will apply from Round 7.',
      tooltip: EVENT_TOOLTIPS.eu_ai_act,
    });
  }

  // 38. Workforce Retraining (R9)
  if (roundEvents?.retraining_assessment) {
    const ra = roundEvents.retraining_assessment;
    events.push({
      icon: ra.succeeded ? '🎓' : '👷',
      color: ra.succeeded ? '#10b981' : 'var(--danger)',
      text: roundEvents.retraining_message || (ra.succeeded
        ? `Workforce retraining program SUCCEEDED (${ra.success_rate}% completion rate) — just transition benefits fully realised.`
        : `Workforce retraining program FAILED — 30% of transition benefits clawed back (social licence: ${ra.social_license_factor}).`),
      tooltip: EVENT_TOOLTIPS.workforce_retraining,
    });
  }

  // 39. Pathway Discovery (R10 debrief)
  if (roundEvents?.pathway_discovery) {
    const pd = roundEvents.pathway_discovery;
    events.push({
      icon: '🗺️', color: '#818cf8',
      text: `Pathway revealed: "${pd.pathway_name}" — Your decisions from R5–R8 seeded this outcome.`,
      tooltip: EVENT_TOOLTIPS.pathway_discovery,
    });
  }

  // 40. Board Pressure Events
  if (roundEvents?.board_pressure_event) {
    const bp = roundEvents.board_pressure_event;
    events.push({
      icon: '🏛️', color: 'var(--caution)',
      text: bp.message || 'Board of Directors is exerting strategic pressure this period.',
      tooltip: EVENT_TOOLTIPS.board_pressure,
    });
  }

  // 41. Stakeholder Salience Migration (Mitchell/Agle/Wood)
  if (roundEvents?.stakeholder_salience) {
    const salience = roundEvents.stakeholder_salience;
    const definitive = Object.entries(salience.stakeholders || {}).filter(([,s]) => s.classification === 'Definitive');
    if (definitive.length > 0) {
      const names = definitive.map(([name]) => name.replace(/_/g, ' ')).join(', ');
      events.push({
        icon: '⚡', color: 'var(--danger)',
        text: `DEFINITIVE stakeholders (high power + legitimacy + urgency): ${names}. Immediate engagement required.`,
        tooltip: EVENT_TOOLTIPS.stakeholder_salience,
      });
    }
  }

  // ── BALANCE SHEET ENGINE EVENTS (42-44) ──────────────────────

  // 42. Covenant Status Warning
  if (roundEvents?.covenant_warning || flags.covenant_warning) {
    const warning = roundEvents?.covenant_warning || flags.covenant_warning;
    const bs = globalState?.balance_sheet || {};
    const cStatus = bs.covenant_status || 'green';
    const ndEbitda = bs.net_debt_to_ebitda;
    if (cStatus === 'amber') {
      events.push({
        icon: '📊', color: 'var(--caution)',
        text: `Debt covenant WATCH LIST — Net Debt/EBITDA at ${ndEbitda?.toFixed(2) || '?'}× (threshold: 3.5×). ${typeof warning === 'string' ? warning : 'Review leverage before committing further.'}`,
        tooltip: 'Your Net Debt / EBITDA ratio is approaching the lender covenant ceiling. If breached, your cost of capital will increase and the revolving credit facility may be restricted.',
      });
    } else if (cStatus === 'red') {
      events.push({
        icon: '🔴', color: 'var(--danger)',
        text: `Debt covenant BREACH — 30-day cure period. Net Debt/EBITDA at ${ndEbitda?.toFixed(2) || '?'}× (limit: 4.5×). Interest surcharge applied.`,
        tooltip: 'Your debt covenants are breached. Lenders have activated a 30-day cure period with a +2% interest surcharge. Reduce leverage by selling assets, cutting dividends, or paying down debt.',
      });
    } else if (cStatus === 'breached') {
      events.push({
        icon: '🚨', color: '#dc2626',
        text: `COVENANT ACCELERATION — Lenders may demand full repayment. Net Debt/EBITDA: ${ndEbitda?.toFixed(2) || '?'}× (>4.5×). Severe treasury penalty.`,
        tooltip: 'Your debt covenants are severely breached. Under standard LMA terms, lenders can accelerate the full revolving credit facility, demanding immediate repayment. This is a solvency crisis.',
      });
    }
  }

  // 43. Goodwill Impairment
  // FIX-D: goodwill_impairment is now a dict { amount, pct, trigger } not a raw number.
  // BS-HIST: diagnostics moved to balance_sheet_diagnostics (balance_sheet now
  // carries the full statement); fall back to the old key for pre-fix sessions.
  const _bsDiag = roundEvents?.balance_sheet_diagnostics || roundEvents?.balance_sheet;
  if ((_bsDiag?.goodwill_impairment?.amount || 0) > 0) {
    const impairment = (atRate(_bsDiag.goodwill_impairment.amount) / 1_000_000).toFixed(1);
    const trigger = _bsDiag.goodwill_impairment.trigger || 'reputation';
    const triggerLabel = trigger === 'ebitda_margin' ? 'Low EBITDA margin' : trigger === 'survival' ? 'Survival mode' : 'Low reputation';
    events.push({
      icon: '📉', color: 'var(--danger)',
      text: `Goodwill impairment: ${currencySymbol()}${impairment}M written off. Trigger: ${triggerLabel}. IAS 36 annual test failed.`,
      tooltip: 'IAS 36 requires annual goodwill impairment testing. Impairment is triggered when group reputation drops below 40 or EBITDA margin falls below 10%. The write-off is smoothly calculated — not a hard cliff — reducing goodwill proportionally.',
    });
  }

  // 44. Stranded Asset Exposure (from BS engine)
  if (globalState?.balance_sheet?.stranded_asset_exposure > 0) {
    const bs = globalState.balance_sheet;
    const exposurePct = ((bs.stranded_asset_exposure / (bs.total_assets || 1)) * 100).toFixed(1);
    if (parseFloat(exposurePct) > 5) {
      events.push({
        icon: '🏚️', color: 'var(--caution)',
        text: `Stranded asset exposure: ${exposurePct}% of total assets at climate transition risk.`,
        tooltip: 'Based on Carbon Tracker methodology, assets with high carbon intensity face write-down risk as the economy transitions. Reduce carbon intensity to lower exposure.',
      });
    }
  }

  // 45. Covenant Surcharge (treasury penalty)
  if (roundEvents?.covenant_surcharge > 0) {
    const surcharge = (atRate(roundEvents.covenant_surcharge) / 1_000_000).toFixed(2);
    const rate = ((roundEvents.covenant_surcharge_rate || 0) * 100).toFixed(0);
    events.push({
      icon: '🏦', color: 'var(--danger)',
      text: `Covenant penalty: ${currencySymbol()}${surcharge}M interest surcharge (+${rate}% annualised on net debt).`,
      tooltip: 'When debt covenants are breached, lenders impose a penalty interest rate surcharge. This directly reduces your treasury. Reduce leverage to avoid ongoing penalties.',
    });
  }

  // ── SYSTEMIC RISK ENGINE EVENTS (46-50) ──────────────────────

  // 46. ESG-Adjusted WACC
  const waccDiag = flags.esg_adjusted_wacc;
  if (waccDiag && typeof waccDiag === 'object' && waccDiag.adjusted_wacc) {
    const adjusted = (waccDiag.adjusted_wacc * 100).toFixed(2);
    const base = (waccDiag.base_wacc * 100).toFixed(2);
    const carbonPrem = waccDiag.carbon_premium ? (waccDiag.carbon_premium * 100).toFixed(2) : '0.00';
    const govPrem = waccDiag.gov_premium ? (waccDiag.gov_premium * 100).toFixed(2) : '0.00';
    const sloDiscount = waccDiag.slo_discount ? (waccDiag.slo_discount * 100).toFixed(2) : '0.00';
    const isStressed = waccDiag.adjusted_wacc > 0.08;
    events.push({
      icon: isStressed ? '📊' : '📈',
      color: isStressed ? 'var(--danger)' : waccDiag.adjusted_wacc > 0.06 ? 'var(--caution)' : '#10b981',
      text: `ESG-Adjusted WACC: ${adjusted}% (base ${base}% + carbon ${carbonPrem}% + governance ${govPrem}% − SLO discount ${sloDiscount}%).${isStressed ? ' ⚠️ WACC above 8% — lender covenant triggers tightening.' : ''}`,
      tooltip: 'Your cost of capital is dynamically adjusted based on ESG performance (El Ghoul et al., 2011). High carbon intensity and governance risk increase WACC; strong social license reduces it. When WACC exceeds 8%, lenders automatically tighten covenant triggers.',
    });
  }

  // 47. Employer Brand OPEX Penalty
  const ebPenalty = roundEvents?.employer_brand_opex_penalty || flags.employer_brand_opex_penalty;
  if (ebPenalty && typeof ebPenalty === 'object') {
    const totalPenalty = (atRate(ebPenalty.total_penalty) / 1_000_000).toFixed(1);
    const ebScore = ebPenalty.employer_brand_score?.toFixed(0) || '?';
    const multPct = ((ebPenalty.multiplier || 0) * 100).toFixed(1);
    events.push({
      icon: '👥', color: 'var(--danger)',
      text: ebPenalty.narrative || `Talent crisis — employer brand at ${ebScore}/100. Recruitment cost surcharge of ${currencySymbol()}${totalPenalty}M (+${multPct}% OPEX across all ${ebPenalty.affected_bus || '?'} BUs).`,
      tooltip: 'When your employer brand score drops below 40 (driven by reputation, burnout, and workforce readiness), ALL business units face escalating recruitment and retention costs. This models the real-world "talent flight spiral" where poor conditions compound into organisation-wide OPEX inflation.',
    });
  }

  // 48. Systemic Tipping Point Transitions
  const tipping = roundEvents?.systemic_tipping || flags.systemic_tipping;
  if (tipping && tipping.transitions && tipping.transitions.length > 0) {
    for (const trans of tipping.transitions) {
      events.push({
        icon: '⚠️', color: '#dc2626',
        text: `SYSTEMIC TIPPING — ${(trans.dimension || '').toUpperCase()}: ${trans.message || 'Irreversible threshold crossed.'}`,
        tooltip: 'Systemic tipping points are irreversible. Once crossed, permanent penalty multipliers apply for the remainder of the simulation. This models real systemic collapse where trust and ecosystem services, once lost, cannot be fully rebuilt within business-relevant timescales (Rockström et al., 2009).',
      });
    }
  }

  // 49. NPC Cascading Reactions
  const cascades = roundEvents?.npc_cascades || flags.npc_cascades;
  if (cascades && Array.isArray(cascades) && cascades.length > 0) {
    for (const cascade of cascades) {
      const actionLabel = (cascade.action || '').replace(/_/g, ' ');
      events.push({
        icon: '🔗', color: '#f97316',
        text: `NPC CASCADE — ${cascade.npc?.replace(/_/g, ' ') || 'Stakeholder'}: ${actionLabel}. ${cascade.narrative || ''}`,
        tooltip: 'Stakeholder reactions trigger other stakeholders — a journalist exposé can embolden activist investors, who then trigger regulator investigations. This "stakeholder spiral" models the interconnected nature of real stakeholder ecosystems.',
      });
    }
  }

  // 50. Foreshadowing Signals
  const foreshadowing = roundEvents?.foreshadowing_signals || flags.foreshadowing_signals;
  if (foreshadowing && Array.isArray(foreshadowing) && foreshadowing.length > 0) {
    for (const signal of foreshadowing) {
      const isPositive = signal.category === 'positive';
      events.push({
        icon: isPositive ? '🔮' : '⚡',
        color: isPositive ? '#10b981' : 'var(--caution)',
        text: signal.message || `${signal.signal_id}: ${signal.category} signal detected.`,
        tooltip: 'Foreshadowing signals indicate that a decision you made in an earlier round will have consequences in a later round. Positive signals indicate protective measures; warning signals suggest emerging vulnerabilities.',
      });
    }
  }

  // ── CEO Diary entry (narrative engagement) ──
  const diary = roundEvents?.ceo_diary;

  // ── Decision Regret (shadow tick alternatives) ──
  const regret = roundEvents?.decision_regret;

  // ── Category grouping ──
  const categorizeEvent = (evt) => {
    if (['var(--danger)'].includes(evt.color) || evt.text?.toLowerCase().includes('risk') || evt.text?.toLowerCase().includes('penalty') || evt.text?.toLowerCase().includes('strike') || evt.text?.toLowerCase().includes('breach') || evt.text?.toLowerCase().includes('tipping')) return 'risks';
    if (evt.text?.toLowerCase().includes('revenue') || evt.text?.toLowerCase().includes('$') || evt.text?.toLowerCase().includes('ebitda') || evt.text?.toLowerCase().includes('wacc') || evt.text?.toLowerCase().includes('treasury') || evt.text?.toLowerCase().includes('cost') || evt.text?.toLowerCase().includes('fee') || evt.text?.toLowerCase().includes('interest') || evt.text?.toLowerCase().includes('covenant')) return 'financial';
    return 'market';
  };

  const grouped = { risks: [], financial: [], market: [] };
  events.forEach(evt => grouped[categorizeEvent(evt)].push(evt));

  const categoryMeta = {
    risks: { icon: '⚠️', label: 'RISKS', color: 'var(--danger)' },
    financial: { icon: '📈', label: 'FINANCIAL IMPACTS', color: 'var(--caution)' },
    market: { icon: '🌍', label: 'MARKET & ESG', color: 'var(--accent)' },
  };

  // V-A: null out when the VISIBLE sections have no content (original check,
  // scoped per `sections` so an empty wrapper never renders).
  const retrospectHasContent = events.length > 0 || !!regret;
  const restHasContent = !!diary;
  if ((!showRetrospect || !retrospectHasContent) && (!showRest || !restHasContent)) return null;

  const moodStyles = {
    confident: { bg: 'rgba(16,185,129,0.06)', border: 'rgba(16,185,129,0.2)', label: '#10b981', emoji: '😤' },
    contemplative: { bg: 'rgba(99,102,241,0.06)', border: 'rgba(99,102,241,0.2)', label: '#818cf8', emoji: '🤔' },
    anxious: { bg: 'rgba(245,158,11,0.06)', border: 'rgba(245,158,11,0.2)', label: 'var(--caution)', emoji: '😰' },
    distressed: { bg: 'rgba(239,68,68,0.06)', border: 'rgba(239,68,68,0.2)', label: 'var(--danger)', emoji: '😨' },
    desperate: { bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.3)', label: 'var(--danger-text)', emoji: '😱' },
  };

  const [eventsOpen, setEventsOpen] = React.useState(true);
  const [regretOpen, setRegretOpen] = React.useState(true);
  const [diaryOpen, setDiaryOpen] = React.useState(false);
  const [expandedEvent, setExpandedEvent] = React.useState(null);

  const hasRegret = regret && Object.keys(regret.alternatives || {}).length > 0;

  const AccordionHeader = ({ icon, title, badge, accentColor, isOpen, onClick }) => (
    <button
      onClick={onClick}
      style={{
        width: '100%', display: 'flex', alignItems: 'center', gap: 10,
        padding: '11px 14px', border: 'none',
        borderRadius: isOpen ? '8px 8px 0 0' : 8,
        background: isOpen ? '#111827' : '#0f1729',
        borderLeft: `3px solid ${accentColor}`,
        cursor: 'pointer', transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
        fontFamily: "'DM Sans', 'Segoe UI', sans-serif",
      }}
    >
      <span style={{ fontSize: '1rem', flexShrink: 0 }}>{icon}</span>
      <span style={{
        flex: 1, textAlign: 'left', fontSize: '0.78rem', fontWeight: 700,
        color: '#f1f5f9', letterSpacing: '0.03em',
      }}>
        {title}
      </span>
      {badge && (
        <span style={{
          padding: '3px 8px', borderRadius: 6, fontSize: 'var(--type-caption)', fontWeight: 700,
          background: `${accentColor}20`, color: accentColor,
          border: `1px solid ${accentColor}40`, whiteSpace: 'nowrap',
        }}>
          {badge}
        </span>
      )}
      <span style={{
        fontSize: 'var(--type-caption)', color: '#64748b',
        transition: 'transform 0.2s', transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
      }}>▾</span>
    </button>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontFamily: "'DM Sans', 'Segoe UI', sans-serif" }}>
      {/* ═══ What Happened This Round ═══ */}
      {showRetrospect && events.length > 0 && (
        <div style={{ borderRadius: 8, overflow: 'hidden', border: '1px solid #1e293b' }}>
          <AccordionHeader
            icon="🔍" title="What Happened This Round"
            badge={`${events.length} event${events.length !== 1 ? 's' : ''}`}
            accentColor="var(--caution)"
            isOpen={eventsOpen} onClick={() => setEventsOpen(v => !v)}
          />
          {eventsOpen && (
            <div style={{
              padding: '10px 14px', background: '#0c1322',
              borderTop: '1px solid #1e293b',
              maxHeight: 340, overflowY: 'auto',
            }}>
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '6px 10px', marginBottom: 8, borderRadius: 6,
                background: 'rgba(94,234,212,0.06)', border: '1px solid rgba(94,234,212,0.1)',
                fontSize: 'var(--type-caption)', color: 'var(--neutral)', fontWeight: 600,
              }}>
                <span>{events.length} events</span>
                <span>{grouped.risks.length} risks</span>
                <span>{grouped.financial.length} financial</span>
                <span>{grouped.market.length} market</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {Object.entries(grouped).filter(([, evts]) => evts.length > 0).map(([cat, catEvents]) => {
                  const meta = categoryMeta[cat];
                  return (
                    <div key={cat} style={{ marginBottom: 8 }}>
                      <div style={{
                        fontSize: 'var(--type-caption)', fontWeight: 800, textTransform: 'uppercase',
                        letterSpacing: '0.08em', color: meta.color, padding: '4px 0',
                        borderBottom: `1px solid ${meta.color}20`, marginBottom: 5,
                        display: 'flex', alignItems: 'center', gap: 5,
                      }}>
                        {meta.icon} {meta.label} ({catEvents.length})
                      </div>
                      {catEvents.map((evt, i) => (
                        <div
                          key={`${cat}-${evt.tooltip?.slice(0, 40) || evt.text?.slice(0, 40) || i}`}
                          style={{ display: 'flex', alignItems: 'flex-start', gap: 8, cursor: evt.tooltip ? 'pointer' : 'default', padding: '3px 0' }}
                          onClick={() => evt.tooltip && setExpandedEvent(expandedEvent === `${cat}-${i}` ? null : `${cat}-${i}`)}
                          data-tooltip={evt.tooltip}
                        >
                          <span style={{ flexShrink: 0, fontSize: '0.85rem' }}>{evt.icon}</span>
                          <div style={{ flex: 1 }}>
                            <span style={{ fontSize: 'var(--type-caption)', color: '#cbd5e1', lineHeight: 1.5 }}>{evt.text}</span>
                            {expandedEvent === `${cat}-${i}` && evt.tooltip && (
                              <div style={{
                                marginTop: 4, padding: '6px 8px', borderRadius: 4,
                                background: 'rgba(94,234,212,0.04)', border: '1px solid rgba(94,234,212,0.1)',
                                fontSize: 'var(--type-caption)', color: 'var(--neutral)', lineHeight: 1.6, fontStyle: 'italic',
                              }}>
                                💡 {evt.tooltip}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══ Road Not Taken ═══ */}
      {showRetrospect && hasRegret && (() => {
        const optionLabels = { option_a: 'Option A', option_b: 'Option B', option_c: 'Option C' };
        const fmtDelta = (v) => {
          if (!v && v !== 0) return '—';
          const sign = v >= 0 ? '+' : '−';
          return `${sign}${money(Math.abs(v))}`;
        };
        return (
          <div style={{ borderRadius: 8, overflow: 'hidden', border: '1px solid #1e293b', background: 'linear-gradient(135deg, rgba(167,139,250,0.03), transparent)' }}>
            <AccordionHeader
              icon="🔮" title="Road Not Taken"
              badge={regret.note || 'Alternatives'}
              accentColor="#a78bfa"
              isOpen={regretOpen} onClick={() => setRegretOpen(v => !v)}
            />
            {regretOpen && (
              <div style={{
                padding: '10px 14px', background: 'linear-gradient(135deg, rgba(167,139,250,0.04), #0c1322)',
                borderTop: '1px solid #1e293b',
              }}>
                <div style={{ fontSize: '0.76rem', color: 'var(--neutral)', marginBottom: 8 }}>
                  <span style={{
                    background: 'linear-gradient(90deg, #c4b5fd, #818cf8, #c4b5fd)',
                    backgroundSize: '200% auto',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    animation: 'shimmer 3s linear infinite',
                  }}>
                    You chose <strong>{optionLabels[regret.your_choice] || regret.your_choice}</strong>
                  </span>. Here's what the alternatives would have yielded:
                </div>
                <style>{`@keyframes shimmer { to { background-position: 200% center; } }`}</style>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {Object.entries(regret.alternatives).map(([opt, data]) => {
                    const tBetter = data.treasury_delta > 0;
                    const rBetter = data.reputation_delta > 0;
                    return (
                      <div key={opt} style={{
                        flex: '1 1 80px', padding: '8px 10px', borderRadius: 6,
                        background: '#111827', border: '1px solid #1e293b',
                      }}>
                        <div style={{
                          fontSize: 'var(--type-caption)', fontWeight: 700, color: '#c4b5fd',
                          marginBottom: 4, textTransform: 'capitalize',
                        }}>
                          {optionLabels[opt] || opt}
                        </div>
                        <div style={{ fontSize: 'var(--type-caption)', color: tBetter ? 'var(--positive-text)' : 'var(--danger-text)', fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
                          💰 {fmtDelta(data.treasury_delta)}
                        </div>
                        <div style={{ fontSize: 'var(--type-caption)', color: rBetter ? 'var(--positive-text)' : 'var(--danger-text)', fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
                          ⭐ {data.reputation_delta >= 0 ? '+' : ''}{data.reputation_delta?.toFixed(1) || '0'} rep
                        </div>
                        {data.ebitda_delta != null && (
                          <div style={{ fontSize: 'var(--type-caption)', color: 'var(--neutral)', marginTop: 2 }}>
                            📊 EBITDA: {fmtDelta(data.ebitda_delta)}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        );
      })()}

      {/* ═══ CEO Diary ═══ */}
      {showRest && diary && (() => {
        const ms = moodStyles[diary.mood] || moodStyles.contemplative;
        return (
          <div style={{ borderRadius: 8, overflow: 'hidden', border: '1px solid #1e293b' }}>
            <AccordionHeader
              icon="📓" title={`CEO Diary — ${diary.round_label || 'This Round'}`}
              badge={`${ms.emoji} ${diary.mood}`}
              accentColor={ms.label}
              isOpen={diaryOpen} onClick={() => setDiaryOpen(v => !v)}
            />
            {diaryOpen && (
              <div style={{
                padding: '12px 16px', background: '#0c1322',
                borderTop: '1px solid #1e293b',
              }}>
                <div style={{
                  fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.65,
                  fontStyle: 'italic',
                }}>
                  "{diary.entry}"
                </div>
              </div>
            )}
          </div>
        );
      })()}
    </div>
  );
}
