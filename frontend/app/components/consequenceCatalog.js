/**
 * consequenceCatalog.js — UX audit #21 ("Complete the consequence chain")
 *
 * WHY THIS FILE EXISTS
 * --------------------
 * ConsequenceReplay used to explain a round from a hardcoded list of three or
 * four event keys, then fell back to "the first 3 truthy flags". Every other
 * effect the engine produced was silently absent from the player's
 * "why did this happen" story — and the gap was invisible, because a missing
 * node looks exactly like a node that never fired.
 *
 * This catalog is the single vocabulary of engine effects. It maps a key that
 * the backend writes into `global_state.active_event_flags` (same dict the
 * commit response exposes as `events` — see backend/engine.py
 * `_assemble_global_state`) to the four things a student needs:
 *
 *   label      — what to call it in plain English
 *   mechanism  — the engine rule that produced it (the "how")
 *   severity   — 'good' | 'bad' | 'neutral'  (drives node colour/order)
 *   explain    — (value, globalState) => one sentence a student can read
 *
 * `icon` is optional and purely decorative.
 *
 * READ-ONLY CONTRACT: this file describes engine output. It must never be used
 * to change engine behaviour, and no backend file was modified to add it.
 * If the engine grows a new flag, ConsequenceReplay still renders it via the
 * humanised fallback (`humaniseKey`) — nothing is ever silently dropped —
 * and adding an entry here just upgrades that row from a bare label to a
 * real explanation.
 *
 * Sources surveyed for the vocabulary (read-only):
 *   backend/engine.py, backend/round_logic.py, backend/impact_engine.py,
 *   backend/systemic_risk_engine.py, backend/black_swan_registry.py,
 *   backend/npc_stakeholders.py, backend/balance_sheet.py,
 *   backend/ending_pathways.py, backend/stakeholder_map.py
 */

/* ═══════════════════════════════════════════════════════════════
   Formatting helpers (shared by the explain() sentences)
   ═══════════════════════════════════════════════════════════════ */

const num = (v, fallback = 0) => (typeof v === 'number' && isFinite(v) ? v : fallback);

/** $2.4M / $840K / $0 — always absolute, the sentence supplies the direction. */
export function money(v) {
  const n = Math.abs(num(v));
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

/** 0.045 → "4.5%" (for rates already expressed as a fraction). */
export function rate(v, dp = 1) {
  return `${(num(v) * 100).toFixed(dp)}%`;
}

/** 12.4 → "12.4%" (for values already expressed in percentage points). */
export function pct(v, dp = 1) {
  return `${num(v).toFixed(dp)}%`;
}

/**
 * Safe display of a small scalar flag value ("stabilise", "A+", 3).
 * The engine occasionally hands a dict or a bare `true` where a label is
 * expected; `fallback` keeps the sentence readable instead of printing
 * "[object Object]" at a student.
 */
export function token(v, fallback) {
  if (typeof v === 'string' && v.trim()) return v.trim().replace(/_/g, ' ');
  if (typeof v === 'number' && isFinite(v)) return String(v);
  return fallback;
}

/** "hospitals" / "consumer_goods" → "Hospitals" / "Consumer Goods". */
export function buName(id) {
  if (!id || typeof id !== 'string') return 'a business unit';
  return id.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Generic humaniser for keys with no catalog entry.
 * `cfo_austerity_active` → "CFO Austerity Active".
 * This is what guarantees the no-silent-drop property.
 */
const ACRONYMS = new Set([
  'ai', 'brsr', 'cbam', 'ceo', 'cfo', 'ci', 'coc', 'csrd', 'dso', 'ebitda',
  'epr', 'esg', 'eu', 'fx', 'hr', 'mr', 'msme', 'ncd', 'npc', 'opex', 'capex',
  'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9', 'r10', 'rd', 'sbti',
  'sdg', 'sec', 'slo', 'tnfd', 'un', 'var', 'vrio', 'wacc',
]);

export function humaniseKey(key) {
  return String(key)
    .replace(/^_+/, '')
    .split('_')
    .filter(Boolean)
    .map((w) => (ACRONYMS.has(w.toLowerCase()) ? w.toUpperCase() : w.charAt(0).toUpperCase() + w.slice(1)))
    .join(' ');
}

/**
 * Several engines stamp the round number onto the key
 * (`reputation_applied_r4`, `midgame_carbon_cost_r7`, …). Strip that suffix so
 * one catalog entry covers the whole family instead of ten near-duplicates.
 */
export function normaliseKey(key) {
  return String(key).replace(/_r\d{1,2}$/, '');
}

/* ═══════════════════════════════════════════════════════════════
   PER-BU / PER-NPC FLAG FAMILIES (UX audit #21, follow-through)

   Several engines stamp the ENTITY onto the key rather than the value:
   `talent_penalty_applied_pharma`, `braindrain_opex_impact_software`,
   `npc_cascade_treasury_activist_fund`, … The set is unbounded by design —
   verticals and NPC ids are configurable per cohort — so these cannot be
   enumerated in the catalog.

   Previously they fell through to the generic humaniser, which produced
   "Talent Penalty Applied Pharma" — technically no-silent-drop, but it read
   like a variable name and told the student nothing.

   This suffix matcher recovers the intent: the family supplies the sentence,
   the suffix supplies the subject. `PER_ENTITY_FAMILIES` is ordered
   longest-prefix-first at match time so `technical_debt_streak_x` never
   resolves against `technical_debt_penalty`.

   Verified against the backend on 2026-08-02 — every prefix below is a real
   `ctx.events[f"..._{bu_id}"]` write site in engine.py.
   ═══════════════════════════════════════════════════════════════ */

export const PER_ENTITY_FAMILIES = {
  talent_penalty_applied: {
    label: 'Talent Penalty', mechanism: 'Talent & Burnout engine', severity: 'bad',
    explain: (who, v) => `${who} carried a talent penalty of ${rate(v, 2)}× on its operating costs — people left faster than they were replaced.`,
  },
  braindrain_opex_impact: {
    label: 'Brain Drain Cost', mechanism: 'Talent & Burnout engine', severity: 'bad',
    explain: (who, v) => `Losing experienced staff pushed ${who}'s operating costs up${v && v.opex_delta ? ` by ${money(v.opex_delta)}` : ''}.`,
  },
  talent_neglect_surcharge: {
    label: 'Talent Neglect Surcharge', mechanism: 'Talent & Burnout engine', severity: 'bad',
    explain: (who, v) => `${who} paid ${money(v)} extra to cover work its own team could no longer do.`,
  },
  burnout_passive_decay: {
    label: 'Burnout Recovery', mechanism: 'Talent & Burnout engine', severity: 'neutral',
    explain: (who, v) => `${who}'s burnout eased by ${rate(v, 1)} points simply from time passing — no action of yours caused this.`,
  },
  utilization_overload_fatigue: {
    label: 'Overload Fatigue', mechanism: 'Capacity engine', severity: 'bad',
    explain: (who) => `${who} ran above safe utilisation long enough that fatigue started compounding.`,
  },
  bed_utilization_drift: {
    label: 'Capacity Drift', mechanism: 'Capacity engine (healthcare)', severity: 'neutral',
    explain: (who, v) => `${who}'s bed utilisation moved by ${rate(v, 1)} points.`,
  },
  patient_outcomes_billing_multiplier: {
    label: 'Outcomes-Linked Billing', mechanism: 'Capacity engine (healthcare)', severity: 'neutral',
    explain: (who, v) => `${who}'s revenue was multiplied by ${rate(v, 3)}× because payers priced on patient outcomes.`,
  },
  cash_conversion_drag: {
    label: 'Cash Conversion Drag', mechanism: 'Working-capital engine', severity: 'bad',
    explain: (who, v) => `${money(v)} of ${who}'s revenue was recognised but not collected this round.`,
  },
  revenue_cannibalized: {
    label: 'Revenue Cannibalised', mechanism: 'Portfolio engine', severity: 'bad',
    explain: (who, v) => `${who} lost ${money(v)} of revenue to your own competing product.`,
  },
  supply_chain_contagion: {
    label: 'Supply-Chain Contagion', mechanism: 'Supply-chain network', severity: 'bad',
    explain: (who, v) => `A supplier failure reached ${who} as a ${money(v)} surcharge.`,
  },
  lockin_synergy_penalty: {
    label: 'Lock-In Penalty', mechanism: 'Supply-chain network', severity: 'bad',
    explain: (who, v) => `${who}'s synergy was cut to ${rate(v, 2)}× because it is locked into a single supplier.`,
  },
  technical_debt_penalty: {
    label: 'Technical Debt', mechanism: 'Capability engine', severity: 'bad',
    explain: (who) => `${who} is paying for deferred maintenance — the bill arrives whether or not you look at it.`,
  },
  technical_debt_streak: {
    label: 'Technical Debt Streak', mechanism: 'Capability engine', severity: 'bad',
    explain: (who, v) => `${who} has now under-invested for ${v} consecutive round${Number(v) === 1 ? '' : 's'}.`,
  },
  implementation_lag_deferred: {
    label: 'Implementation Lag', mechanism: 'Capability engine', severity: 'neutral',
    explain: (who, v) => `${money(v)} of ${who}'s intended spend lands next round instead — change takes time to bite.`,
  },
  ncd_credit_downgrade: {
    label: 'Natural-Capital Downgrade', mechanism: 'Natural Capital Debt engine', severity: 'bad',
    explain: (who) => `${who}'s environmental liabilities grew large enough for lenders to reprice its credit.`,
  },
  institutional_leakage: {
    label: 'Institutional Leakage', mechanism: 'SDG engine', severity: 'bad',
    explain: (who) => `Weak local institutions absorbed part of ${who}'s investment before it reached the ground.`,
  },
  sanitation_miracle: {
    label: 'Sanitation Breakthrough', mechanism: 'SDG engine', severity: 'good',
    explain: (who) => `${who}'s water and sanitation work compounded into an outsized health gain.`,
  },
  interlinkage_applied: {
    label: 'SDG Interlinkage', mechanism: 'SDG engine', severity: 'good',
    explain: (who) => `Progress at ${who} pulled a second, linked goal forward with it.`,
  },
  npc_cascade_treasury: {
    label: 'Stakeholder Cascade', mechanism: 'NPC stakeholder engine', severity: 'bad',
    explain: (who, v) => `${who} reacting cost the group ${money(v)} as other stakeholders followed.`,
  },
};

const _FAMILY_PREFIXES = Object.keys(PER_ENTITY_FAMILIES).sort((a, b) => b.length - a.length);

/**
 * Resolve a per-entity key to `{ entry, subject }`, or null.
 * Longest prefix wins, so `technical_debt_streak_pharma` never matches
 * `technical_debt_penalty`.
 */
export function matchPerEntity(key) {
  const k = String(key || '');
  for (const prefix of _FAMILY_PREFIXES) {
    if (k.length > prefix.length + 1 && k.startsWith(`${prefix}_`)) {
      const suffix = k.slice(prefix.length + 1);
      if (!suffix) return null;
      const fam = PER_ENTITY_FAMILIES[prefix];
      const subject = buName(suffix);
      return {
        entry: {
          label: `${fam.label} — ${subject}`,
          mechanism: fam.mechanism,
          severity: fam.severity,
          explain: (v) => fam.explain(subject, v),
        },
        subject,
        family: prefix,
      };
    }
  }
  return null;
}

/** Catalog lookup: exact → round-suffix family → per-entity family. Null if unknown. */
export function lookupConsequence(key) {
  if (CONSEQUENCE_CATALOG[key]) return CONSEQUENCE_CATALOG[key];
  const base = normaliseKey(key);
  if (base !== key && CONSEQUENCE_CATALOG[base]) return CONSEQUENCE_CATALOG[base];
  // UX audit #21 follow-through: per-BU / per-NPC families.
  const perEntity = matchPerEntity(base);
  return perEntity ? perEntity.entry : null;
}

/* ═══════════════════════════════════════════════════════════════
   THE CATALOG
   Grouped by the engine that writes the flag.
   ═══════════════════════════════════════════════════════════════ */

export const CONSEQUENCE_CATALOG = {
  /* ───────────────────────────────────────────────────────────────
     1. TALENT, BURNOUT & WORKFORCE  (engine.py brain-drain / burnout,
        employer brand, strikes, retraining, HR ROI)
     ─────────────────────────────────────────────────────────────── */

  talent_penalty_applied: {
    label: 'Brain-Drain Penalty',
    mechanism: 'Group reputation fell below the brain-drain threshold, so recruitment and retention costs were loaded onto OPEX.',
    severity: 'bad',
    icon: '🧠',
    explain: (v) =>
      `Your best people started leaving, so operating costs rose ${pct((num(v, 1) - 1) * 100)} to replace them.`,
  },
  employer_brand: {
    label: 'Employer Brand Score',
    mechanism: 'Reputation, staff burnout and workforce readiness combine into a single hiring-market score.',
    severity: 'neutral',
    icon: '🪪',
    explain: (v) =>
      `Your standing as an employer is now ${num(v).toFixed(0)}/100 — that is what candidates see before they see your salary offer.`,
  },
  employer_brand_opex_penalty: {
    label: 'Recruitment Cost Surge',
    mechanism: 'A weak employer brand forces a recruitment premium onto every business unit\'s OPEX.',
    severity: 'bad',
    icon: '💼',
    explain: (v) =>
      `A poor employer brand added ${money(v && v.total_penalty)} of extra hiring cost across ${num(v && v.affected_bus, 0) || 'all'} divisions this round.`,
  },
  burnout_diagnostics: {
    label: 'Staff Burnout',
    mechanism: 'Burnout accumulates from workload and under-investment in people, and decays slowly when you invest.',
    severity: 'bad',
    icon: '🕯️',
    explain: () => 'Staff burnout moved this round — tired teams are slower and more expensive to run.',
  },
  burnout_strike_boost: {
    label: 'Burnout Raised Strike Risk',
    mechanism: 'Burnout above the tolerance band is added directly to strike probability.',
    severity: 'bad',
    icon: '⚠️',
    explain: (v) => `Exhausted staff pushed the chance of industrial action up by ${pct(num(v) * 100)}.`,
  },
  strike_triggered: {
    label: 'Strike',
    mechanism: 'A strike roll succeeded against the accumulated strike probability for that business unit.',
    severity: 'bad',
    icon: '✊',
    explain: () => 'Workers walked out — production stopped and revenue was lost while the dispute ran.',
  },
  strike_revenue_lost: {
    label: 'Strike Revenue Lost',
    mechanism: 'Strike days are converted into lost production and removed from revenue.',
    severity: 'bad',
    icon: '📉',
    explain: (v) => `The stoppage cost you ${money(v)} of revenue you will not get back.`,
  },
  strike_probability: {
    label: 'Strike Probability',
    mechanism: 'Social licence, burnout and pay decisions set the odds of industrial action each round.',
    severity: 'neutral',
    icon: '🎲',
    explain: (v) => `The odds of a walkout next round stand at ${pct(num(v) * 100)}.`,
  },
  micro_strike_applied: {
    label: 'Localised Disruption',
    mechanism: 'Macro noise triggers a short, local stoppage at one randomly selected business unit.',
    severity: 'bad',
    icon: '⚡',
    explain: (v) =>
      `A short local stoppage at ${buName(v && v.bu_id)} added ${money(v && v.opex_penalty)} to operating costs.`,
  },
  strike_floor_applied: {
    label: 'Strike Risk Floor',
    mechanism: 'A minimum strike probability applies once social licence is critically low, regardless of other spending.',
    severity: 'bad',
    icon: '🚧',
    explain: () => 'Social licence is so low that a baseline strike risk now applies no matter what else you do.',
  },
  workforce_readiness: {
    label: 'Workforce Readiness',
    mechanism: 'Training investment raises readiness; neglect and churn erode it. Readiness gates synergy capture.',
    severity: 'neutral',
    icon: '🎓',
    explain: (v) => `Your people are ${num(v).toFixed(0)}/100 ready for the strategy you are asking them to deliver.`,
  },
  low_readiness_penalty_active: {
    label: 'Readiness Too Low',
    mechanism: 'Below the readiness floor, promised efficiency gains are not realised.',
    severity: 'bad',
    icon: '🚫',
    explain: () => 'Your workforce was not skilled up enough to actually deliver the efficiencies you paid for.',
  },
  education_lag_matured: {
    label: 'Training Investment Matured',
    mechanism: 'Education and training projects pay back on a multi-round lag, not in the round you fund them.',
    severity: 'good',
    icon: '📚',
    explain: (v) => `Training you funded rounds ago finally landed, worth ${money(v)} this round.`,
  },
  education_lag_mature: {
    label: 'Training Payback Scheduled',
    mechanism: 'Education projects are queued with a fixed maturation delay before they pay back.',
    severity: 'neutral',
    icon: '⏳',
    explain: () => 'Your training spend is in the pipeline — it pays back in a later round, not this one.',
  },
  education_lag_project_started: {
    label: 'Training Programme Started',
    mechanism: 'A workforce education project was opened this round with a deferred benefit.',
    severity: 'neutral',
    icon: '🏫',
    explain: () => 'You started a workforce education programme; the benefit arrives after the lag, not now.',
  },
  retraining_clawback: {
    label: 'Retraining Clawback',
    mechanism: 'Retraining outcomes are probabilistic against social licence — low trust means people leave anyway.',
    severity: 'bad',
    icon: '↩️',
    explain: (v) => `${money(v)} of your retraining spend was wasted because staff left before it paid back.`,
  },
  retraining_assessment: {
    label: 'Retraining Outcome',
    mechanism: 'Retraining success is rolled against social licence: trusted employers keep the people they retrain.',
    severity: 'neutral',
    icon: '🧾',
    explain: () => 'Your retraining programme was assessed — whether it sticks depends on how much staff trust you.',
  },
  sdg_8_work_multiplier: {
    label: 'Decent Work Multiplier',
    mechanism: 'SDG 8 (decent work) performance scales labour productivity across the group.',
    severity: 'neutral',
    icon: '👷',
    explain: (v) => `Your decent-work record is scaling labour productivity by ${num(v, 1).toFixed(2)}×.`,
  },
  hr_roi_this_round: {
    label: 'People Investment Return',
    mechanism: 'HR spend returns value through OPEX savings plus pillar effectiveness, measured each round.',
    severity: 'good',
    icon: '💡',
    explain: (v) => `Money you put into people returned ${money(v)} of value this round.`,
  },
  hr_roi_cumulative: {
    label: 'People Investment (Cumulative)',
    mechanism: 'Cumulative return on every round of HR investment since Round 1.',
    severity: 'good',
    icon: '📈',
    explain: (v) => `Across the whole game, investing in people has returned ${money(v)} so far.`,
  },
  hr_quality_tier: {
    label: 'People Investment Tier',
    mechanism: 'Cumulative HR spend is banded into quality tiers that gate workforce bonuses.',
    severity: 'neutral',
    icon: '🏅',
    explain: (v) => `Your sustained investment in people rates as "${token(v, 'improving')}".`,
  },
  mr_workforce_bonus: {
    label: 'Workforce Bonus to M_R',
    mechanism: 'Sustained workforce readiness adds a bonus to the terminal Regenerative Multiple.',
    severity: 'good',
    icon: '⭐',
    explain: () => 'Your investment in readiness earned a bonus on the final Regenerative Multiple.',
  },
  mr_wellbeing_bonus: {
    label: 'Wellbeing Bonus to M_R',
    mechanism: 'Keeping average burnout low across the game adds a terminal M_R bonus.',
    severity: 'good',
    icon: '🌿',
    explain: () => 'You kept burnout low all game, and the final valuation multiple rewards that.',
  },

  /* ───────────────────────────────────────────────────────────────
     2. CLIMATE & CARBON  (engine.py carbon fee, CBAM, SBTi, tipping
        points, natural capital debt, EU taxonomy, climate VaR)
     ─────────────────────────────────────────────────────────────── */

  internal_carbon_fee_deducted: {
    label: 'Internal Carbon Fee',
    mechanism: 'Your own shadow carbon price is charged on group emissions and swept into the Green Transition Fund.',
    severity: 'bad',
    icon: '🏷️',
    explain: (v) => `You charged yourself ${money(v)} for the carbon you emitted — that money went into your Green Transition Fund.`,
  },
  internal_carbon_fee_per_ton: {
    label: 'Internal Carbon Price',
    mechanism: 'The per-tonne shadow price you set determines how hard emissions bite your own P&L.',
    severity: 'neutral',
    icon: '⚖️',
    explain: (v) => `You are pricing your own carbon at ${money(v)} per tonne.`,
  },
  peak_internal_carbon_fee: {
    label: 'Carbon Price Ratchet',
    mechanism: 'The internal carbon price never falls below its historic peak — you cannot quietly walk a commitment back.',
    severity: 'neutral',
    icon: '🔒',
    explain: (v) => `Your highest-ever internal carbon price (${money(v)}/tonne) is now a floor you cannot go below.`,
  },
  carbon_retribution_triggered: {
    label: 'Emergency Climate Levy',
    mechanism: 'Group carbon intensity above the early-game ceiling triggers a punitive multiple on the carbon charge.',
    severity: 'bad',
    icon: '🔥',
    explain: () => 'Your emissions were high enough early on to trigger an emergency climate levy at penalty rates.',
  },
  carbon_retribution_penalty: {
    label: 'Climate Levy Charged',
    mechanism: 'The retribution levy is charged directly against treasury in the round it fires.',
    severity: 'bad',
    icon: '💸',
    explain: (v) => `The emergency climate levy took ${money(v)} straight out of your treasury.`,
  },
  carbon_retribution_multiplier: {
    label: 'Levy Multiplier',
    mechanism: 'The penalty multiple applied to the standard carbon charge when the levy fires.',
    severity: 'bad',
    icon: '✖️',
    explain: (v) => `The levy charged you ${num(v, 1).toFixed(1)}× the normal carbon rate.`,
  },
  carbon_forward_used: {
    label: 'Carbon Forward Exercised',
    mechanism: 'A carbon forward bought earlier locks in a price below the current spot market.',
    severity: 'good',
    icon: '📜',
    explain: () => 'A carbon contract you bought earlier kicked in, so you paid the locked-in price instead of today\'s.',
  },
  carbon_forward_savings: {
    label: 'Carbon Hedge Saving',
    mechanism: 'The difference between spot offset price and your forward price is banked as saving.',
    severity: 'good',
    icon: '💰',
    explain: (v) => `Hedging your carbon price early saved you ${money(v)} against the spot market.`,
  },
  carbon_offset_market: {
    label: 'Carbon Offset Purchase',
    mechanism: 'Residual emissions are offset at the prevailing spot price unless a forward covers them.',
    severity: 'neutral',
    icon: '🌍',
    explain: () => 'You bought offsets on the open market for emissions you did not eliminate.',
  },
  cbam_surcharge_applied: {
    label: 'EU Border Carbon Tax',
    mechanism: 'EU CBAM charges an import surcharge when Scope 1+2 carbon intensity exceeds the border threshold.',
    severity: 'bad',
    icon: '🛃',
    explain: (v) => `Because your carbon intensity is above the EU border threshold, exports cost you an extra ${money(v)}.`,
  },
  cbam_effective_fee: {
    label: 'CBAM Rate',
    mechanism: 'The effective per-tonne border adjustment rate applied to your exports.',
    severity: 'neutral',
    icon: '📐',
    explain: (v) => `The EU border adjustment is charging you ${money(v)} per tonne on exported carbon.`,
  },
  loss_damage_levy_applied: {
    label: 'Loss & Damage Levy',
    mechanism: 'Once the climate tier reaches stressed or tipped, a mandatory adaptation contribution is charged.',
    severity: 'bad',
    icon: '🌊',
    explain: (v) => `You paid ${money(v)} into the international loss-and-damage fund — the bill for climate inaction.`,
  },
  tipping_point_reached: {
    label: 'Climate Tipping Point',
    mechanism: 'Average carbon intensity crossed the irreversible threshold; natural capital costs now compound.',
    severity: 'bad',
    icon: '🌡️',
    explain: () => 'You crossed the climate tipping point. This is irreversible — from here the ecological bill compounds.',
  },
  tipping_tier_escalated: {
    label: 'Climate Threshold Crossed',
    mechanism: 'Carbon intensity bands escalate warning → stressed → tipped, each with heavier penalties.',
    severity: 'bad',
    icon: '📛',
    explain: (v) => `Your climate risk band escalated to "${token(v, 'a worse tier')}" — the penalties get heavier at each step.`,
  },
  tipping_tier_active: {
    label: 'Climate Risk Band',
    mechanism: 'The active climate tier scales natural capital interest and carbon tax multipliers.',
    severity: 'neutral',
    icon: '🌤️',
    explain: (v) => `You are currently sitting in the "${token(v, 'elevated')}" climate risk band.`,
  },
  tipping_point_managed_retreat: {
    label: 'Managed Retreat',
    mechanism: 'A large carbon intensity drop after tipping partially mitigates — but does not undo — the damage.',
    severity: 'good',
    icon: '🪃',
    explain: () => 'You cut carbon hard enough to soften the tipping-point damage, though you cannot reverse it.',
  },
  climate_var: {
    label: 'Climate Value at Risk',
    mechanism: 'Physical and transition risk are priced into a single value-at-risk figure each round.',
    severity: 'neutral',
    icon: '📊',
    explain: (v) => `Climate exposure now puts ${money(v && v.total_var)} of value at risk.`,
  },
  climate_event_struck: {
    label: 'Physical Climate Event',
    mechanism: 'A physical climate event rolls against cyclone probability, reduced by your resilience factor.',
    severity: 'bad',
    icon: '🌪️',
    explain: () => 'A physical climate event hit your assets — the resilience you did (or did not) build decided how hard.',
  },
  actual_damage: {
    label: 'Climate Damage',
    mechanism: 'Base event damage is reduced by the active resilience factor to give actual damage.',
    severity: 'bad',
    icon: '🏚️',
    explain: (v) => `The event did ${money(v)} of real damage after your defences were counted.`,
  },
  climate_resilience_factor: {
    label: 'Resilience Factor',
    mechanism: 'Resilience investment reduces physical climate damage as a straight percentage.',
    severity: 'good',
    icon: '🛡️',
    explain: (v) => `Your resilience investment absorbed ${pct(num(v) * 100)} of the physical damage.`,
  },
  active_resilience_factor: {
    label: 'Active Resilience',
    mechanism: 'Completed resilience projects contribute a standing damage-reduction factor.',
    severity: 'good',
    icon: '🧱',
    explain: (v) => `Defences you have already built are cutting climate damage by ${pct(num(v) * 100)}.`,
  },
  resilience_project_started: {
    label: 'Resilience Project Started',
    mechanism: 'Resilience projects take rounds to build; they protect you only once complete.',
    severity: 'neutral',
    icon: '🏗️',
    explain: () => 'You started building physical defences — they protect you from next round, not this one.',
  },
  resilience_deferred_amount: {
    label: 'Resilience Deferred',
    mechanism: 'Resilience spend that has not yet matured provides no protection in the current round.',
    severity: 'neutral',
    icon: '⏱️',
    explain: (v) => `${money(v)} of resilience spend is still under construction and protecting nothing yet.`,
  },
  global_emissions_intensity: {
    label: 'Group Carbon Intensity',
    mechanism: 'Revenue-weighted average carbon intensity across every business unit.',
    severity: 'neutral',
    icon: '🏭',
    explain: (v) => `Across the whole group you are running at a carbon intensity of ${num(v).toFixed(0)}.`,
  },
  emissions_limit_breached: {
    label: 'Emissions Limit Breached',
    mechanism: 'Absolute group tonnage above the hard cap triggers a regulatory crisis event.',
    severity: 'bad',
    icon: '🚨',
    explain: () => 'Your total emissions blew through the hard cap, which triggered a public regulatory crisis.',
  },
  emissions_rep_penalty: {
    label: 'Emissions Reputation Hit',
    mechanism: 'Breaching the emissions ceiling costs reputation on top of the financial penalty.',
    severity: 'bad',
    icon: '📉',
    explain: (v) => `Being seen to breach your emissions limit cost you ${num(v).toFixed(1)} reputation points.`,
  },
  stranded_asset_penalty_applied: {
    label: 'Stranded Assets',
    mechanism: 'Business units above the carbon intensity ceiling are reclassified as stranded, adding a cost-of-capital surcharge.',
    severity: 'bad',
    icon: '⛽',
    explain: () => 'Investors reclassified your dirtiest units as stranded assets, so your cost of capital went up.',
  },
  stranded_asset_bu_ids: {
    label: 'Stranded Business Units',
    mechanism: 'The specific units whose carbon intensity crossed the stranding threshold.',
    severity: 'bad',
    icon: '📍',
    explain: (v) =>
      `${Array.isArray(v) ? v.map(buName).join(', ') : buName(v)} ${Array.isArray(v) && v.length > 1 ? 'are' : 'is'} now considered a stranded asset by climate-aware investors.`,
  },
  stranded_asset_exposure: {
    label: 'Stranded Asset Exposure',
    mechanism: 'The share of group value sitting in assets at risk of stranding.',
    severity: 'bad',
    icon: '🧨',
    explain: (v) => `${pct(v)} of your asset base is exposed to being written off in a fast transition.`,
  },
  divestment_pressure_active: {
    label: 'Divestment Pressure',
    mechanism: 'Stranded assets bring institutional shareholders demanding a credible decarbonisation pathway.',
    severity: 'bad',
    icon: '🏛️',
    explain: () => 'Institutional shareholders are now openly threatening to sell out unless you show a decarbonisation plan.',
  },
  ncd_forgiveness_applied: {
    label: 'Natural Capital Debt Repaid',
    mechanism: 'Green CapEx forgives natural capital debt on a logarithmic curve — early spend is worth most.',
    severity: 'good',
    icon: '🌱',
    explain: (v) => `Green capital spending wrote off ${money(v)} of the ecological debt you had built up.`,
  },
  ncd_halved: {
    label: 'Natural Capital Debt Halved',
    mechanism: 'A qualifying restoration decision halves outstanding natural capital debt.',
    severity: 'good',
    icon: '✂️',
    explain: () => 'Your restoration choice cut your outstanding natural capital debt in half.',
  },
  ncd_doubled: {
    label: 'Natural Capital Debt Doubled',
    mechanism: 'Extractive choices double the outstanding natural capital debt and the interest it accrues.',
    severity: 'bad',
    icon: '⛏️',
    explain: () => 'That extractive choice doubled your natural capital debt — and the interest that compounds on it.',
  },
  ncd_project_started: {
    label: 'Restoration Project Started',
    mechanism: 'Nature restoration projects are queued and pay down natural capital debt on completion.',
    severity: 'neutral',
    icon: '🌳',
    explain: () => 'You began a nature restoration project; it pays down ecological debt once it completes.',
  },
  nbs_uncertainty: {
    label: 'Nature-Based Solution Risk',
    mechanism: 'Nature-based solutions succeed probabilistically — ecosystems do not follow a project plan.',
    severity: 'neutral',
    icon: '🍃',
    explain: () => 'Your nature-based solution was rolled against ecological uncertainty — nature does not guarantee delivery.',
  },
  sbti_coc_surcharge_applied: {
    label: 'SBTi Misalignment Surcharge',
    mechanism: 'Consecutive rounds off the science-based target pathway attract an investor cost-of-capital surcharge.',
    severity: 'bad',
    icon: '🔬',
    explain: (v) => `Missing your science-based target for several rounds running added ${rate(v)} to your cost of capital.`,
  },
  sbti_pathway: {
    label: 'Science-Based Target Pathway',
    mechanism: 'Your emissions trajectory is compared each round against the 1.5°C-aligned reduction pathway.',
    severity: 'neutral',
    icon: '📉',
    explain: (v) =>
      v && v.aligned === false
        ? 'You are off the science-based emissions pathway; investors are watching the gap.'
        : 'Your emissions are tracking the science-based reduction pathway.',
  },
  eu_taxonomy_alignment_pct: {
    label: 'EU Taxonomy Alignment',
    mechanism: 'The share of turnover that qualifies as taxonomy-aligned green activity.',
    severity: 'neutral',
    icon: '🇪🇺',
    explain: (v) => `${pct(v)} of your revenue counts as green under the EU taxonomy.`,
  },
  taxonomy_green_finance_discount: {
    label: 'Green Finance Discount',
    mechanism: 'High taxonomy alignment unlocks cheaper debt from sustainability-linked lenders.',
    severity: 'good',
    icon: '🏦',
    explain: (v) => `Being genuinely green earned you ${rate(v)} off your borrowing cost.`,
  },
  taxonomy_coc_benefit: {
    label: 'Taxonomy Cost-of-Capital Benefit',
    mechanism: 'Taxonomy-aligned revenue reduces the group cost of capital.',
    severity: 'good',
    icon: '⬇️',
    explain: (v) => `Taxonomy-aligned revenue reduced your cost of capital by ${rate(v)}.`,
  },
  taxonomy_coc_surcharge: {
    label: 'Taxonomy Cost-of-Capital Surcharge',
    mechanism: 'Predominantly brown revenue raises the group cost of capital.',
    severity: 'bad',
    icon: '⬆️',
    explain: (v) => `Too little of your revenue is taxonomy-aligned, so lenders added ${rate(v)} to your cost of capital.`,
  },
  taxonomy_brown_penalty: {
    label: 'Brown Revenue Penalty',
    mechanism: 'Revenue from excluded activities is penalised under the taxonomy screen.',
    severity: 'bad',
    icon: '🟤',
    explain: () => 'Too much of your revenue comes from activities the taxonomy screens out, and you were penalised for it.',
  },
  carbon_intensity_applied: {
    label: 'Carbon Intensity Change',
    mechanism: 'The chosen option moves carbon intensity across the business units it touches.',
    severity: 'neutral',
    icon: '🌡️',
    explain: (v) => `Your decision moved carbon intensity by ${num(v) >= 0 ? '+' : ''}${num(v).toFixed(1)} points.`,
  },
  carbon_intensity_halved: {
    label: 'Carbon Intensity Halved',
    mechanism: 'A deep decarbonisation option cuts carbon intensity by half in the affected units.',
    severity: 'good',
    icon: '🎯',
    explain: () => 'That decision halved carbon intensity where it applied — the single biggest lever in the model.',
  },
  carbon_tax_tripled: {
    label: 'Carbon Tax Tripled',
    mechanism: 'A regulatory escalation event multiplies the prevailing carbon tax rate.',
    severity: 'bad',
    icon: '💥',
    explain: () => 'Regulators tripled the carbon tax rate — every tonne you still emit now costs three times as much.',
  },
  midgame_carbon_cost: {
    label: 'Carbon Cost Charged',
    mechanism: 'Mid-game rounds charge the prevailing carbon rate against group tonnage.',
    severity: 'bad',
    icon: '🧾',
    explain: (v) => `Carbon you emitted this round cost you ${money(v)}.`,
  },
  early_decarboniser_synergy_bonus: {
    label: 'Early Decarboniser Bonus',
    mechanism: 'Cutting carbon before the regulatory ratchet unlocks a lasting synergy bonus.',
    severity: 'good',
    icon: '🥇',
    explain: () => 'You decarbonised before you were forced to, and that early move unlocked a permanent synergy bonus.',
  },
  green_fund_used: {
    label: 'Green Fund Drawn',
    mechanism: 'The Green Transition Fund (built from your internal carbon fee) subsidises qualifying CapEx.',
    severity: 'good',
    icon: '🪙',
    explain: (v) => `Your Green Transition Fund covered ${money(v)} of this round's capital spend, so treasury took less of a hit.`,
  },
  green_fund_terminal_bonus: {
    label: 'Green Fund Terminal Bonus',
    mechanism: 'An unspent Green Transition Fund converts into terminal value at the end of the game.',
    severity: 'good',
    icon: '🎁',
    explain: (v) => `Money left in your Green Transition Fund converted into ${money(v)} of terminal value.`,
  },
  scope_transparency: {
    label: 'Scope 1/2/3 Disclosure',
    mechanism: 'Emissions are split across Scope 1, 2 and 3 so the disclosed footprint matches the real one.',
    severity: 'neutral',
    icon: '🔍',
    explain: () => 'Your emissions were broken out across Scopes 1, 2 and 3 — Scope 3 is usually the uncomfortable one.',
  },
  scope3_data_completeness: {
    label: 'Scope 3 Data Quality',
    mechanism: 'Supply chain transparency determines how much Scope 3 data you can actually evidence.',
    severity: 'neutral',
    icon: '🧮',
    explain: (v) => `You can evidence ${pct(v)} of your Scope 3 emissions — the rest is estimate, and auditors know it.`,
  },
  water_project_started: {
    label: 'Water Project Started',
    mechanism: 'Water infrastructure projects mature over several rounds before delivering benefits.',
    severity: 'neutral',
    icon: '💧',
    explain: () => 'You commissioned water infrastructure; the payback comes in later rounds.',
  },
  desalination_payback_started: {
    label: 'Desalination Payback',
    mechanism: 'A completed desalination plant returns a fixed sum per round against its build cost.',
    severity: 'good',
    icon: '🌊',
    explain: () => 'Your desalination plant came online and has started paying back its build cost each round.',
  },

  /* ───────────────────────────────────────────────────────────────
     3. FINANCE, TREASURY & COVENANT  (engine.py financial layer,
        balance_sheet.py covenants, turnaround_engine.py distress)
     ─────────────────────────────────────────────────────────────── */

  loan_interest_payment: {
    label: 'Loan Interest',
    mechanism: 'Outstanding loan principal accrues interest at the prevailing loan rate every round.',
    severity: 'bad',
    icon: '🏦',
    explain: (v) => `Servicing your debt cost you ${money(v)} in interest this round.`,
  },
  loan_principal: {
    label: 'Debt Outstanding',
    mechanism: 'Loan principal carries forward until repaid and drives both interest and covenant ratios.',
    severity: 'neutral',
    icon: '📗',
    explain: (v) => `You are still carrying ${money(v)} of borrowed money.`,
  },
  loan_interest_rate: {
    label: 'Borrowing Rate',
    mechanism: 'The interest rate on your debt, tightened by macro conditions and ESG risk.',
    severity: 'neutral',
    icon: '％',
    explain: (v) => `Lenders are charging you ${rate(v)} on borrowed money.`,
  },
  emergency_credit_used: {
    label: 'Emergency Credit Drawn',
    mechanism: 'When treasury cannot cover committed spend, an automatic emergency facility is drawn at a punitive rate.',
    severity: 'bad',
    icon: '🆘',
    explain: () => 'You ran out of cash, so an emergency credit line was drawn automatically — at a rate you did not negotiate.',
  },
  emergency_credit_amount: {
    label: 'Emergency Credit Amount',
    mechanism: 'The size of the automatic emergency drawdown, added to loan principal.',
    severity: 'bad',
    icon: '💳',
    explain: (v) => `You were forced to borrow ${money(v)} at short notice to stay solvent.`,
  },
  emergency_credit_rate: {
    label: 'Emergency Credit Rate',
    mechanism: 'Emergency facilities price well above the standard loan rate.',
    severity: 'bad',
    icon: '🔺',
    explain: (v) => `That emergency money is costing you ${rate(v)} — far above your normal borrowing rate.`,
  },
  emergency_credit_interest: {
    label: 'Emergency Credit Interest',
    mechanism: 'Interest charged on the emergency facility in the round it is drawn.',
    severity: 'bad',
    icon: '💸',
    explain: (v) => `Running out of cash cost you ${money(v)} in penalty interest.`,
  },
  negative_treasury_interest_applied: {
    label: 'Overdraft Interest',
    mechanism: 'A negative treasury balance accrues interest at the corporate cost of capital.',
    severity: 'bad',
    icon: '🔻',
    explain: (v) => `Your treasury went negative, so creditors charged you ${money(v)} on the overdraft.`,
  },
  insolvency_active: {
    label: 'Insolvency / Credit Downgrade',
    mechanism: 'Breaching the insolvency threshold forces mandatory austerity: CapEx capped, dividends suspended.',
    severity: 'bad',
    icon: '☠️',
    explain: () => 'Treasury breached the insolvency line. Austerity is now mandatory: capital spending is capped and dividends are stopped.',
  },
  survival_mode: {
    label: 'Survival Mode',
    mechanism: 'Sustained distress puts the company into survival mode, restricting strategic options.',
    severity: 'bad',
    icon: '🩹',
    explain: () => 'The company is in survival mode — you are managing to stay alive, not to grow.',
  },
  bailout_applied: {
    label: 'Bailout',
    mechanism: 'Distress detection triggers a one-off external bailout with strings attached.',
    severity: 'neutral',
    icon: '🪂',
    explain: (v) => `An outside rescue put ${money(v)} into the business — bought time, at the cost of your independence.`,
  },
  distress_detection: {
    label: 'Financial Distress',
    mechanism: 'Treasury, covenant and EBITDA signals combine into a distress classification each round.',
    severity: 'bad',
    icon: '🚑',
    explain: (v) =>
      v && v.distress_detected
        ? 'The engine has formally classified you as financially distressed.'
        : 'Your distress indicators were checked and you are still in the clear.',
  },
  turnaround_phase: {
    label: 'Turnaround Phase',
    mechanism: 'Distressed companies move through staged turnaround phases with different constraints in each.',
    severity: 'neutral',
    icon: '🔄',
    explain: (v) => `You are in the "${token(v, 'recovery')}" phase of the turnaround, which limits what you are allowed to do.`,
  },
  turnaround_graduated: {
    label: 'Turnaround Complete',
    mechanism: 'Meeting the recovery criteria graduates the company out of turnaround constraints.',
    severity: 'good',
    icon: '🎓',
    explain: () => 'You pulled the company out of distress and graduated from the turnaround programme.',
  },
  capex_capped: {
    label: 'Capital Spending Capped',
    mechanism: 'CapEx is hard-capped at a multiple of treasury, and halved again under insolvency austerity.',
    severity: 'bad',
    icon: '🧢',
    explain: () => 'You asked to spend more than your balance sheet allows, so your capital spend was cut back to the cap.',
  },
  capex_cap_limit: {
    label: 'Capital Spending Ceiling',
    mechanism: 'The hard ceiling on capital spend derived from your current treasury.',
    severity: 'neutral',
    icon: '📏',
    explain: (v) => `Your balance sheet only supports ${money(v)} of capital spending right now.`,
  },
  capex_overrun_triggered: {
    label: 'Execution Overrun',
    mechanism: 'Every capital programme rolls against an overrun probability — scope creep is modelled, not assumed away.',
    severity: 'bad',
    icon: '🔨',
    explain: () => 'Your capital project overran. Scope creep is real, and the engine rolls for it every time you build.',
  },
  capex_overrun_amount: {
    label: 'Overrun Cost',
    mechanism: 'The overrun is added to the capital request before treasury is debited.',
    severity: 'bad',
    icon: '➕',
    explain: (v) => `The overrun added ${money(v)} to what you actually paid.`,
  },
  capex_project_completed: {
    label: 'Capital Project Completed',
    mechanism: 'Multi-round capital projects deliver their benefit only on completion.',
    severity: 'good',
    icon: '✅',
    explain: () => 'A capital project you funded earlier finished, and its benefits start flowing now.',
  },
  dividends_paid: {
    label: 'Dividends Paid',
    mechanism: 'Dividends are paid from free cash after committed spend and clamped to what treasury allows.',
    severity: 'neutral',
    icon: '💵',
    explain: (v) => `You returned ${money(v)} to shareholders this round.`,
  },
  dividends_clamped: {
    label: 'Dividend Cut Back',
    mechanism: 'Requested dividends above available free cash are clamped down to what the balance sheet supports.',
    severity: 'bad',
    icon: '✂️',
    explain: () => 'You promised shareholders more than you could afford, so the payout was cut back to what the cash allowed.',
  },
  dividends_requested: {
    label: 'Dividend Requested',
    mechanism: 'The dividend you asked for, before any clamp or suspension.',
    severity: 'neutral',
    icon: '🙋',
    explain: (v) => `You asked to pay out ${money(v)}.`,
  },
  dividend_suspended: {
    label: 'Dividend Suspended',
    mechanism: 'Insolvency austerity suspends dividends entirely until treasury recovers.',
    severity: 'bad',
    icon: '⛔',
    explain: () => 'Dividends were suspended altogether — the balance sheet simply cannot support a payout.',
  },
  dividend_ratchet_triggered: {
    label: 'Dividend Ratchet',
    mechanism: 'Cutting a dividend after a run of stable payouts is punished far harder than never having paid one.',
    severity: 'bad',
    icon: '🪤',
    explain: () => 'Cutting a dividend after years of paying one damaged board confidence badly — the market punishes reversals, not low payouts.',
  },
  dividend_ratchet_penalty: {
    label: 'Ratchet Penalty',
    mechanism: 'The reputation and confidence cost of breaking a dividend track record.',
    severity: 'bad',
    icon: '📉',
    explain: (v) => `Breaking your dividend record cost you ${num(v).toFixed(1)} points of board and investor confidence.`,
  },
  covenant_warning: {
    label: 'Covenant Warning',
    mechanism: 'Net debt to EBITDA above the trigger ratio moves covenant status from green to amber.',
    severity: 'bad',
    icon: '🟠',
    explain: (v) => (typeof v === 'string' && v ? v : 'Your lenders have put you on covenant watch — debt is high relative to earnings.'),
  },
  covenant_surcharge: {
    label: 'Covenant Breach Surcharge',
    mechanism: 'Red or breached covenant status triggers a lender surcharge charged straight to treasury.',
    severity: 'bad',
    icon: '🔴',
    explain: (v) => `Breaching your debt covenants cost you ${money(v)} in lender penalties.`,
  },
  covenant_surcharge_rate: {
    label: 'Covenant Penalty Rate',
    mechanism: 'The surcharge rate steps up as covenant status worsens from red to breached.',
    severity: 'bad',
    icon: '📈',
    explain: (v) => `Your lenders are charging a ${rate(v)} penalty while you stay in breach.`,
  },
  esg_adjusted_wacc: {
    label: 'ESG-Adjusted Cost of Capital',
    mechanism: 'Carbon, governance, social licence and nature risk each add or subtract basis points from your WACC.',
    severity: 'neutral',
    icon: '🧭',
    explain: (v) =>
      `Your ESG risk profile puts your cost of capital at ${rate(v && v.adjusted_wacc, 2)} — sustainability is priced into your debt, not separate from it.`,
  },
  coc_macro_rate_applied: {
    label: 'Central Bank Rate Move',
    mechanism: 'The macro rate cycle moves the corporate cost of capital independently of anything you do.',
    severity: 'neutral',
    icon: '🏛️',
    explain: (v) =>
      num(v) === 0
        ? 'Central bank policy was neutral this round, so your cost of capital was unchanged.'
        : `Monetary policy moved your cost of capital by ${num(v) >= 0 ? '+' : ''}${rate(v, 2)} — nothing you did caused this.`,
  },
  macro_rate_environment: {
    label: 'Rate Environment',
    mechanism: 'The rate cycle rotates through easing, neutral and tightening on a fixed cadence.',
    severity: 'neutral',
    icon: '🌐',
    explain: (v) => `Central banks are in a "${String((v && v.phase) || 'shifting')}" phase right now.`,
  },
  inflation_index_applied: {
    label: 'Inflation',
    mechanism: 'Cost inflation is applied to every business unit\'s OPEX each round.',
    severity: 'bad',
    icon: '📈',
    explain: (v) => `Inflation added ${pct(num(v) * 100)} to your operating costs before you did anything.`,
  },
  inflation_drift_hostile: {
    label: 'Hostile Inflation Drift',
    mechanism: 'A hostile regulatory and market environment pushes system-wide inflation above baseline and compounds it.',
    severity: 'bad',
    icon: '🔥',
    explain: () => 'A hostile operating environment is driving inflation above baseline, and it compounds every round.',
  },
  macro_noise: {
    label: 'Macro Volatility',
    mechanism: 'Seeded random macro noise perturbs inflation and can trigger localised disruption.',
    severity: 'neutral',
    icon: '🎲',
    explain: () => 'The wider economy moved on its own this round — some of what happened was not your doing.',
  },
  fx_risk: {
    label: 'Currency Movement',
    mechanism: 'FX moves scale international revenue by each unit\'s overseas exposure.',
    severity: 'neutral',
    icon: '💱',
    explain: (v) => (v && v.fx_message ? String(v.fx_message) : 'Currency moves changed the value of your overseas revenue.'),
  },
  dso_working_capital: {
    label: 'Cash Collection Lag',
    mechanism: 'Days Sales Outstanding defers revenue into the next round; weak governance lengthens the lag.',
    severity: 'bad',
    icon: '⏳',
    explain: (v) => `${money(v && v.total_deferred)} of revenue you earned will not be collected until next round.`,
  },
  cfo_austerity_active: {
    label: 'CFO Austerity',
    mechanism: 'The CFO imposes a spending freeze when investment outruns what the balance sheet supports.',
    severity: 'bad',
    icon: '🧊',
    explain: () => 'Your CFO has imposed austerity — discretionary spending is frozen until the numbers recover.',
  },
  caroic: {
    label: 'Return on Invested Capital',
    mechanism: 'Carbon-adjusted return on invested capital measures whether your spending actually creates value.',
    severity: 'neutral',
    icon: '🧮',
    explain: (v) =>
      `Your carbon-adjusted return on invested capital is ${rate((v && v.caroic) ?? v, 1)} — this is whether the money you spend actually creates value.`,
  },
  momentum: {
    label: 'Strategic Momentum',
    mechanism: 'Momentum tracks whether your key metrics are improving or deteriorating round on round.',
    severity: 'neutral',
    icon: '🏃',
    explain: (v) => `Your strategic momentum score is ${num(v && v.momentum_score).toFixed(0)} — direction of travel matters more than any single round.`,
  },
  green_bond_r2_risk_premium: {
    label: 'Green Bond Risk Premium',
    mechanism: 'Issuing a green bond without credible alignment attracts a risk premium instead of a discount.',
    severity: 'bad',
    icon: '📕',
    explain: (v) => `Your green bond was priced with a ${rate(v)} risk premium because the underlying story was not credible.`,
  },
  green_bond_r2_alignment_discount: {
    label: 'Green Bond Discount',
    mechanism: 'A credibly aligned green bond prices below conventional debt.',
    severity: 'good',
    icon: '📘',
    explain: (v) => `A credible green bond earned you ${rate(v)} off your cost of debt.`,
  },
  green_premium_squeeze: {
    label: 'Green Premium Squeeze',
    mechanism: 'When competitors catch up on green credentials, the price premium you were charging erodes.',
    severity: 'bad',
    icon: '🪗',
    explain: (v) => `Rivals caught up on green credentials, squeezing ${money(v && v.penalty)} out of the premium you were charging.`,
  },
  equity_wiped_out: {
    label: 'Equity Wiped Out',
    mechanism: 'Net debt exceeding enterprise value leaves nothing for shareholders in the equity bridge.',
    severity: 'bad',
    icon: '🕳️',
    explain: () => 'Debt now exceeds what the business is worth — the shareholders\' stake is gone.',
  },
  opex_slash_applied: {
    label: 'Cost Cutting',
    mechanism: 'Slashing OPEX buys treasury now and pays for it in outcomes and staff capacity later.',
    severity: 'neutral',
    icon: '🪓',
    explain: () => 'You cut operating costs hard. The cash shows up now; the damage to outcomes shows up later.',
  },
  opex_slash_treasury_bonus: {
    label: 'Cost Cutting Cash',
    mechanism: 'The immediate treasury benefit of the OPEX cut.',
    severity: 'good',
    icon: '💰',
    explain: (v) => `Cutting costs freed up ${money(v)} of cash this round.`,
  },
  opex_slash_outcomes_penalty: {
    label: 'Cost Cutting Damage',
    mechanism: 'OPEX cuts degrade service and outcome quality proportionally to the depth of the cut.',
    severity: 'bad',
    icon: '💔',
    explain: (v) => `Those cuts cost you ${num(v).toFixed(1)} points of service and outcome quality.`,
  },

  /* ───────────────────────────────────────────────────────────────
     4. STAKEHOLDER & SOCIAL LICENCE  (npc_stakeholders.py,
        stakeholder_map.py salience migration, engine.py fatigue,
        greenwashing / truth premium)
     ─────────────────────────────────────────────────────────────── */

  stakeholder_fatigue_applied: {
    label: 'Stakeholder Fatigue',
    mechanism: 'Each crisis you survive makes the next reputation recovery slower — trust rebuilds more slowly than it breaks.',
    severity: 'bad',
    icon: '😮‍💨',
    explain: () => 'Stakeholders have seen too many crises from you. Your reputation recovers more slowly now than it used to.',
  },
  stakeholder_fatigue_efficiency: {
    label: 'Recovery Efficiency',
    mechanism: 'Recovery efficiency decays with the lifetime crisis count.',
    severity: 'bad',
    icon: '🔋',
    explain: (v) => `You are only recovering reputation at ${pct(num(v, 1) * 100)} of the normal rate.`,
  },
  crisis_count_lifetime: {
    label: 'Crises Survived',
    mechanism: 'The running count of crises drives stakeholder fatigue and the recovery penalty.',
    severity: 'neutral',
    icon: '🔢',
    explain: (v) => `You have now been through ${num(v).toFixed(0)} crisis rounds, and stakeholders remember every one.`,
  },
  npc_stakeholders: {
    label: 'Stakeholder Reactions',
    mechanism: 'Each NPC stakeholder scores your round against their own priorities and escalates or de-escalates accordingly.',
    severity: 'neutral',
    icon: '👥',
    explain: (v) => {
      const n = (v && Array.isArray(v.npc_actions) && v.npc_actions.length) || 0;
      return n
        ? `${n} stakeholder group${n === 1 ? '' : 's'} reacted to your decision, each judging it against their own priorities.`
        : 'Your stakeholders assessed this round against their own priorities.';
    },
  },
  npc_cascade_events: {
    label: 'Stakeholder Cascade',
    mechanism: 'A hostile stakeholder can pull others with them — anger propagates through the network.',
    severity: 'bad',
    icon: '🌊',
    explain: (v) => {
      const n = Array.isArray(v) ? v.length : 0;
      return n
        ? `One angry stakeholder dragged ${n} other${n === 1 ? '' : 's'} with them — opposition spreads through the network.`
        : 'Anger from one stakeholder group began spreading to others.';
    },
  },
  active_npc_cascades: {
    label: 'Active Cascades',
    mechanism: 'Cascades stay live for several rounds until trust is deliberately rebuilt.',
    severity: 'bad',
    icon: '♾️',
    explain: () => 'Stakeholder opposition is still cascading and will keep costing you until you rebuild trust deliberately.',
  },
  npc_slo_feedback: {
    label: 'Stakeholder Social Licence Feedback',
    mechanism: 'Stakeholder satisfaction feeds back directly into each business unit\'s social licence to operate.',
    severity: 'neutral',
    icon: '🔁',
    explain: () => 'How stakeholders feel about you was fed back into your social licence to operate on the ground.',
  },
  stakeholder_coalition: {
    label: 'Stakeholder Coalition',
    mechanism: 'Aligned stakeholders can form a coalition, combining their power and urgency against you.',
    severity: 'bad',
    icon: '🤝',
    explain: () => 'Separate stakeholder groups joined forces. A coalition is much harder to negotiate with than individuals.',
  },
  salience_migrations: {
    label: 'Stakeholder Salience Shift',
    mechanism: 'Stakeholders move between salience quadrants (power / legitimacy / urgency) as events change their standing.',
    severity: 'neutral',
    icon: '🧭',
    explain: (v) => {
      const n = Array.isArray(v) ? v.length : 0;
      return n
        ? `${n} stakeholder${n === 1 ? '' : 's'} changed how much they matter to you — yesterday's minor voice can become today's decisive one.`
        : 'The map of who matters to you shifted this round.';
    },
  },
  salience_migration_count: {
    label: 'Salience Shifts',
    mechanism: 'The count of stakeholders whose quadrant changed this round.',
    severity: 'neutral',
    icon: '🔀',
    explain: (v) => `${num(v).toFixed(0)} stakeholder group(s) changed quadrant on your salience map.`,
  },
  salience_migration_message: {
    label: 'Salience Shift Detail',
    mechanism: 'A plain-language summary of which stakeholders moved and why.',
    severity: 'neutral',
    icon: '💬',
    explain: (v) => (typeof v === 'string' && v ? v : 'Stakeholder salience shifted as a result of this round.'),
  },
  social_license_boosted: {
    label: 'Social Licence Improved',
    mechanism: 'Community-facing decisions raise the social licence to operate in the affected units.',
    severity: 'good',
    icon: '🤲',
    explain: () => 'Communities gave you more room to operate because of what you chose here.',
  },
  social_license_severe_drop_applied: {
    label: 'Social Licence Collapse',
    mechanism: 'A severe breach of community trust drops social licence sharply and raises strike risk.',
    severity: 'bad',
    icon: '🧨',
    explain: () => 'Your social licence collapsed. Communities that stop consenting can stop you operating entirely.',
  },
  avg_social_license: {
    label: 'Average Social Licence',
    mechanism: 'The mean social licence across business units, gating strike risk and terminal multiple bonuses.',
    severity: 'neutral',
    icon: '📊',
    explain: (v) => `Across the group your social licence to operate averages ${num(v).toFixed(0)}/100.`,
  },
  community_trust_score: {
    label: 'Community Trust',
    mechanism: 'Governance quality and partnership investment combine into a community trust score.',
    severity: 'neutral',
    icon: '🏘️',
    explain: (v) => `Communities rate their trust in you at ${num(v).toFixed(0)}/100.`,
  },
  political_capital_score: {
    label: 'Political Capital',
    mechanism: 'Political capital is earned by delivering on public commitments and spent when you need regulatory latitude.',
    severity: 'neutral',
    icon: '🎩',
    explain: (v) => `You are holding ${num(v).toFixed(0)}/100 of political capital — the goodwill you can spend when regulators come knocking.`,
  },
  social_capital_index: {
    label: 'Social Capital',
    mechanism: 'Accumulated social capital determines how much benefit of the doubt you get in a crisis.',
    severity: 'neutral',
    icon: '💞',
    explain: (v) => `Your social capital stands at ${num(v).toFixed(0)} — this is the credit you can draw on when something goes wrong.`,
  },
  social_media_velocity: {
    label: 'Social Media Amplification',
    mechanism: 'Digital scrutiny intensifies each round, multiplying how fast reputational damage spreads.',
    severity: 'bad',
    icon: '📱',
    explain: (v) => `Bad news now travels ${num(v, 1).toFixed(1)}× faster than it did at the start of the game.`,
  },
  donor_fatigue_budget_multiplier: {
    label: 'Donor Fatigue',
    mechanism: 'Repeated appeals to the same funders shrink the budget they are willing to give.',
    severity: 'bad',
    icon: '🥱',
    explain: (v) => `Going back to the same funders again has cut what they will give to ${pct(num(v, 1) * 100)} of the original budget.`,
  },
  migration_service_penalty: {
    label: 'Service Migration Penalty',
    mechanism: 'Stakeholders shifting away from a business unit reduce the service revenue it can hold.',
    severity: 'bad',
    icon: '🚶',
    explain: (v) => `Stakeholders moving away from you cost ${money(v)} of service revenue.`,
  },
  migration_target_affected: {
    label: 'Unit Losing Stakeholders',
    mechanism: 'The business unit with the highest stakeholder gap absorbs the migration penalty.',
    severity: 'bad',
    icon: '🎯',
    explain: (v) => `${buName(v)} took the brunt of stakeholders walking away.`,
  },
  greenwashing_scandal: {
    label: 'Greenwashing Scandal',
    mechanism: 'The engine compares your green rhetoric to your actual green investment ratio. A gap becomes a scandal.',
    severity: 'bad',
    icon: '🎭',
    explain: () => 'Your green claims did not match your green spending, and it became a public scandal.',
  },
  greenwashing_penalty: {
    label: 'Greenwashing Penalty',
    mechanism: 'A greenwashing scandal costs reputation points on top of any financial impact.',
    severity: 'bad',
    icon: '📉',
    explain: (v) => `Being caught overclaiming on sustainability cost you ${num(v).toFixed(1)} reputation points.`,
  },
  greenwashing_risk_active: {
    label: 'Greenwashing Risk',
    mechanism: 'A gap between disclosure and investment puts you on the watchlist before any scandal fires.',
    severity: 'bad',
    icon: '⚠️',
    explain: () => 'You are saying more than you are spending. That gap is what a greenwashing scandal is made of.',
  },
  greenwashing_checked: {
    label: 'Greenwashing Check',
    mechanism: 'Every round your investment ratio is tested against your disclosure claims.',
    severity: 'neutral',
    icon: '🔎',
    explain: () => 'Your green claims were checked against your actual spending this round.',
  },
  truth_premium_active: {
    label: 'Truth Premium',
    mechanism: 'Disclosing uncomfortable facts costs short-term reputation but buys durable credibility.',
    severity: 'good',
    icon: '🗝️',
    explain: () => 'You told the uncomfortable truth. It cost you in the short term and bought you credibility that lasts.',
  },
  promise_resolutions: {
    label: 'Promises Resolved',
    mechanism: 'Commitments made in earlier rounds are checked against what you actually delivered.',
    severity: 'neutral',
    icon: '🤞',
    explain: () => 'Promises you made in earlier rounds came due, and stakeholders checked whether you kept them.',
  },
  engagement_action_result: {
    label: 'Stakeholder Engagement Outcome',
    mechanism: 'Direct engagement actions succeed or fail against the target stakeholder\'s current trust level.',
    severity: 'neutral',
    icon: '☎️',
    explain: () => 'Your direct engagement with a stakeholder group played out — trust already banked decided how it landed.',
  },
  stakeholder_revenue_boost: {
    label: 'Stakeholder Revenue Boost',
    mechanism: 'Strong stakeholder relationships convert into commercial access and revenue.',
    severity: 'good',
    icon: '📈',
    explain: (v) => `Good stakeholder relationships turned into ${money(v)} of extra revenue.`,
  },

  /* ───────────────────────────────────────────────────────────────
     5. SUPPLY CHAIN  (engine.py supply chain contagion / transparency,
        supplier defection, technology lock-in, synergy)
     ─────────────────────────────────────────────────────────────── */

  supply_chain_transparency: {
    label: 'Supply Chain Transparency',
    mechanism: 'Transparency builds slowly through supplier auditing and traceability investment.',
    severity: 'neutral',
    icon: '🔗',
    explain: (v) => `You can see ${pct(v)} of the way down your own supply chain.`,
  },
  supply_chain_contagion: {
    label: 'Supply Chain Contagion',
    mechanism: 'A crisis in one business unit spreads cost pressure to every unit sharing suppliers.',
    severity: 'bad',
    icon: '🕸️',
    explain: () => 'Trouble in one part of the business spread through shared suppliers and raised costs everywhere.',
  },
  supply_chain_disruption_applied: {
    label: 'Supply Chain Disruption',
    mechanism: 'A supply shock interrupts input flows and forces costlier substitutes.',
    severity: 'bad',
    icon: '🚢',
    explain: () => 'Your supply chain was disrupted, and you paid more for inputs you could no longer source normally.',
  },
  supplier_defection: {
    label: 'Supplier Defection',
    mechanism: 'Suppliers squeezed too hard on price or ethics defect to competitors.',
    severity: 'bad',
    icon: '🚪',
    explain: (v) =>
      v && v.active === false
        ? 'Your suppliers were tested for defection risk and stayed with you.'
        : 'A supplier walked away. Squeezing the people who supply you eventually costs more than it saves.',
  },
  supply_chain_fragile: {
    label: 'Fragile Supply Chain',
    mechanism: 'Low transparency and single-sourcing classify the chain as fragile, amplifying shocks.',
    severity: 'bad',
    icon: '🪟',
    explain: () => 'Your supply chain is classified as fragile — one shock anywhere in it lands on you at full force.',
  },
  supply_chain_adequate: {
    label: 'Adequate Supply Chain',
    mechanism: 'Middling transparency and diversification give partial shock absorption.',
    severity: 'neutral',
    icon: '🧷',
    explain: () => 'Your supply chain is adequate — it absorbs small shocks but not large ones.',
  },
  supply_chain_resilient: {
    label: 'Resilient Supply Chain',
    mechanism: 'High transparency and diversified sourcing damp incoming supply shocks.',
    severity: 'good',
    icon: '🛡️',
    explain: () => 'Your supply chain is resilient, so shocks that would hurt rivals barely register for you.',
  },
  blockchain_traceability_dividend: {
    label: 'Traceability Dividend',
    mechanism: 'End-to-end traceability investment returns value through premium pricing and avoided incidents.',
    severity: 'good',
    icon: '🔐',
    explain: (v) => `Being able to trace your supply chain end to end was worth ${money(v)} this round.`,
  },
  sc_cobalt_findings: {
    label: 'Supply Chain Audit Findings',
    mechanism: 'Deep supplier audits surface issues that were always there but previously invisible.',
    severity: 'neutral',
    icon: '🧪',
    explain: () => 'Your supplier audit found things. They were always there — you just could not see them before.',
  },
  sc_digital_maturity: {
    label: 'Supply Chain Digital Maturity',
    mechanism: 'Digital maturity determines how quickly you can detect and respond to supply shocks.',
    severity: 'neutral',
    icon: '🖥️',
    explain: (v) => `Your supply chain digital maturity is ${num(v).toFixed(0)}/100 — this decides how fast you spot a problem.`,
  },
  circular_efficiency_bonus_applied: {
    label: 'Circular Economy Bonus',
    mechanism: 'Closing material loops reduces input cost and waste charges simultaneously.',
    severity: 'good',
    icon: '♻️',
    explain: () => 'Designing waste out of the loop cut both your input costs and your disposal costs at once.',
  },
  technology_lockin_penalty: {
    label: 'Technology Lock-In',
    mechanism: 'Repeated investment in one technology path raises switching costs and suppresses synergy elsewhere.',
    severity: 'bad',
    icon: '🔒',
    explain: () => 'You kept investing down one technology path, and now switching away from it is expensive.',
  },
  technology_lockin_bu: {
    label: 'Locked-In Unit',
    mechanism: 'The business unit whose repeated investment streak triggered lock-in.',
    severity: 'bad',
    icon: '📍',
    explain: (v) => `${buName(v)} is now locked into its technology path.`,
  },
  synergy_boost_applied: {
    label: 'Synergy Unlocked',
    mechanism: 'Complementary investments across units multiply group performance beyond the sum of the parts.',
    severity: 'good',
    icon: '🔗',
    explain: (v) => `Investments that reinforce each other lifted your group synergy by ${num(v).toFixed(2)}.`,
  },
  synergy_boost_pending: {
    label: 'Synergy Pending',
    mechanism: 'Some synergy benefits are queued and only land once the enabling project completes.',
    severity: 'neutral',
    icon: '⏳',
    explain: (v) => `${num(v).toFixed(2)} of synergy is queued and will land once the enabling work finishes.`,
  },
  synergy_decayed_from: {
    label: 'Synergy Decay',
    mechanism: 'Synergy decays every round unless actively maintained — coordination is not free.',
    severity: 'bad',
    icon: '🍂',
    explain: (v) => `Your synergy multiplier decayed from ${num(v, 1).toFixed(2)} — coordination has to be maintained or it erodes.`,
  },
  synergy_wiped: {
    label: 'Synergy Wiped Out',
    mechanism: 'A structural decision (divestment, spin-off, restructure) destroys accumulated synergy outright.',
    severity: 'bad',
    icon: '💥',
    explain: () => 'That structural decision destroyed the synergy you had spent rounds building.',
  },
  synergy_gate_blocked: {
    label: 'Synergy Gate Failed',
    mechanism: 'Synergy only unlocks if readiness and coordination prerequisites are met first.',
    severity: 'bad',
    icon: '🚧',
    explain: () => 'You did not meet the prerequisites, so the synergy you paid for did not unlock.',
  },
  synergy_gate_passed: {
    label: 'Synergy Gate Passed',
    mechanism: 'Meeting the readiness prerequisites releases the queued synergy benefit.',
    severity: 'good',
    icon: '🔓',
    explain: () => 'You met the prerequisites, so the queued synergy benefit was released.',
  },
  synergy_readiness_penalty: {
    label: 'Readiness Cut Synergy',
    mechanism: 'Low workforce readiness scales down the synergy actually captured.',
    severity: 'bad',
    icon: '📉',
    explain: (v) => `Your people were not ready, so you only captured part of the synergy — ${num(v).toFixed(2)} was lost.`,
  },

  /* ───────────────────────────────────────────────────────────────
     6. BLACK SWAN & SYSTEMIC RISK  (black_swan_registry.py,
        systemic_risk_engine.py tipping states, competitor pressure)
     ─────────────────────────────────────────────────────────────── */

  black_swan_events: {
    label: 'Black Swan Event',
    mechanism: 'Low-probability, high-impact events fire against a seeded roll modified by your own risk posture.',
    severity: 'bad',
    icon: '🦢',
    explain: (v) => {
      const n = Array.isArray(v) ? v.length : 0;
      return n
        ? `${n} rare, high-impact event${n === 1 ? '' : 's'} hit you this round — your exposure decided how much damage got through.`
        : 'A rare, high-impact event fired this round.';
    },
  },
  black_swan_narratives: {
    label: 'Black Swan Narrative',
    mechanism: 'Each black swan carries a narrative explaining what happened in the world, not just to your numbers.',
    severity: 'bad',
    icon: '📰',
    explain: () => 'The world outside your company moved, and you were exposed to it.',
  },
  active_black_swans: {
    label: 'Ongoing Black Swans',
    mechanism: 'Black swans persist for a set number of rounds, so the damage is not confined to the round they fire.',
    severity: 'bad',
    icon: '⏳',
    explain: (v) => {
      const n = Array.isArray(v) ? v.length : 0;
      return n
        ? `${n} shock${n === 1 ? ' is' : 's are'} still running — the damage does not stop in the round it starts.`
        : 'A shock from an earlier round is still running.';
    },
  },
  systemic_tipping: {
    label: 'Systemic Tipping',
    mechanism: 'Climate, social and financial subsystems each track warning → stressed → tipped independently.',
    severity: 'bad',
    icon: '🌐',
    explain: () => 'One of the systems you depend on — climate, social or financial — crossed a threshold. These do not reset.',
  },
  systemic_tipping_state: {
    label: 'Systemic Risk State',
    mechanism: 'The current tier of each systemic subsystem and the multipliers each tier applies.',
    severity: 'neutral',
    icon: '🧭',
    explain: () => 'Your climate, social and financial risk tiers were reassessed this round.',
  },
  climate_tipping_penalties_applied: {
    label: 'Climate System Penalties',
    mechanism: 'A tipped climate subsystem multiplies natural capital interest and carbon tax and caps reputation.',
    severity: 'bad',
    icon: '🔥',
    explain: () => 'The climate subsystem has tipped, so ecological costs now compound and your reputation is capped.',
  },
  social_tipping_penalties_applied: {
    label: 'Social System Penalties',
    mechanism: 'A tipped social subsystem raises strike risk and suppresses productivity across the group.',
    severity: 'bad',
    icon: '✊',
    explain: () => 'The social subsystem has tipped — strike risk is elevated and productivity is suppressed everywhere.',
  },
  financial_tipping_penalties_applied: {
    label: 'Financial System Penalties',
    mechanism: 'A tipped financial subsystem hardens covenants and raises the cost of every future pound you borrow.',
    severity: 'bad',
    icon: '🏦',
    explain: () => 'The financial subsystem has tipped, so covenants hardened and every future pound you borrow costs more.',
  },
  contagion_spike_triggered: {
    label: 'Reputation Contagion',
    mechanism: 'A reputation collapse in one unit drags the group average down faster than the arithmetic mean.',
    severity: 'bad',
    icon: '🦠',
    explain: () => 'A reputation hit in one unit spread across the group — reputation is shared, even when the failure is not.',
  },
  adaptive_crisis_severity: {
    label: 'Crisis Severity Adapted',
    mechanism: 'Crisis severity scales to your current position so the simulation stays challenging without being unwinnable.',
    severity: 'neutral',
    icon: '🎚️',
    explain: () => 'The severity of this crisis was scaled to where you actually are, not to a fixed script.',
  },
  crisis_multiplier: {
    label: 'Crisis Multiplier',
    mechanism: 'Prior blind spots and unresolved risks multiply the impact of the current crisis.',
    severity: 'bad',
    icon: '✖️',
    explain: (v) => `Earlier unresolved risks multiplied this crisis by ${num(v, 1).toFixed(1)}×.`,
  },
  crisis_severity_effective: {
    label: 'Effective Crisis Severity',
    mechanism: 'The final crisis severity after every multiplier and mitigation is applied.',
    severity: 'bad',
    icon: '🌡️',
    explain: (v) => `After everything was counted, this crisis landed at severity ${num(v).toFixed(1)}.`,
  },
  materiality_shocks: {
    label: 'Materiality Shock',
    mechanism: 'Issues you declared immaterial can fire back as shocks — the materiality assessment is a bet, not a description.',
    severity: 'bad',
    icon: '🎯',
    explain: () => 'An issue you had judged immaterial came back and hit you. Materiality assessment is a bet you can lose.',
  },
  fog_of_war_active: {
    label: 'Fog of War',
    mechanism: 'Early rounds hide competitor data unless you paid for a deep audit.',
    severity: 'bad',
    icon: '🌫️',
    explain: () => 'You are deciding with incomplete market visibility. A deep audit would have lifted the fog.',
  },
  foreshadowing_signals: {
    label: 'Early Warning Signals',
    mechanism: 'The engine plants signals about the ending pathway your decisions are steering towards.',
    severity: 'neutral',
    icon: '🔮',
    explain: () => 'There are signals in the news about where your decisions are taking you. They are easy to miss on purpose.',
  },
  foreshadowing_events: {
    label: 'Foreshadowing Events',
    mechanism: 'News releases and market intelligence hint indirectly at the ending pathway you have seeded.',
    severity: 'neutral',
    icon: '📻',
    explain: () => 'News items appeared that point, indirectly, at the endgame your choices are building.',
  },
  competitor_warning: {
    label: 'Competitor Overtaking You',
    mechanism: 'The NPC competitor grows steadily; relative advantage below 1.0 means they are ahead.',
    severity: 'bad',
    icon: '🏁',
    explain: (v) => (typeof v === 'string' && v ? v : 'Your competitor is now out-earning you — standing still is falling behind.'),
  },
  relative_market_advantage: {
    label: 'Relative Market Advantage',
    mechanism: 'Your EBITDA divided by the competitor\'s — above 1.0 you are ahead, below it you are not.',
    severity: 'neutral',
    icon: '⚔️',
    explain: (v) =>
      num(v, 1) >= 1
        ? `You are earning ${num(v, 1).toFixed(2)}× what your main competitor earns.`
        : `Your competitor is ahead — you are at ${num(v, 1).toFixed(2)}× their earnings.`,
  },
  competitor_ebitda: {
    label: 'Competitor Earnings',
    mechanism: 'The NPC competitor compounds its earnings every round whether you act or not.',
    severity: 'neutral',
    icon: '🏢',
    explain: (v) => `Your main competitor earned ${money(v)} this round.`,
  },
  poison_pill_deployed: {
    label: 'Poison Pill Deployed',
    mechanism: 'A takeover defence that dilutes a hostile acquirer at the cost of your own shareholders.',
    severity: 'neutral',
    icon: '☠️',
    explain: () => 'You deployed a takeover defence. It keeps you independent and dilutes your own shareholders to do it.',
  },
  white_knight_revenue_drag: {
    label: 'White Knight Cost',
    mechanism: 'A friendly acquirer keeps you out of hostile hands but takes a share of your revenue.',
    severity: 'bad',
    icon: '🐴',
    explain: (v) => `Bringing in a friendly investor cost you ${money(v)} of revenue as the price of staying independent.`,
  },
  takeover_vulnerability_index: {
    label: 'Takeover Vulnerability',
    mechanism: 'A depressed share price and weak defences raise the odds of a hostile approach.',
    severity: 'bad',
    icon: '🎯',
    explain: (v) => `You are ${num(v).toFixed(0)}/100 vulnerable to a hostile takeover right now.`,
  },

  /* ───────────────────────────────────────────────────────────────
     7. REGULATORY & COMPLIANCE  (engine.py regulatory ratchet,
        legal challenges, EU AI Act, materiality, BRSR track)
     ─────────────────────────────────────────────────────────────── */

  regulatory_ratchet_active: {
    label: 'Regulatory Ratchet',
    mechanism: 'Your cost of capital can never fall below its historic regulatory floor — compliance costs are sticky downwards.',
    severity: 'bad',
    icon: '🔩',
    explain: () => 'Your cost of capital is being held up by a regulatory floor. Compliance costs, once incurred, do not simply go away.',
  },
  regulatory_floor_coc: {
    label: 'Regulatory Floor',
    mechanism: 'The historic maximum cost of capital becomes a floor that erodes only very slowly.',
    severity: 'neutral',
    icon: '📉',
    explain: (v) => `Regulation is holding your cost of capital at a floor of ${rate(v, 2)}.`,
  },
  regulatory_floor_eroded: {
    label: 'Regulatory Floor Eased',
    mechanism: 'Sustained good behaviour slowly erodes the regulatory floor downwards.',
    severity: 'good',
    icon: '⬇️',
    explain: () => 'Consistent good behaviour eased the regulatory floor on your cost of capital slightly.',
  },
  regulatory_friction: {
    label: 'Regulatory Friction',
    mechanism: 'A hostile regulatory relationship adds ongoing OPEX and slows approvals.',
    severity: 'bad',
    icon: '🧱',
    explain: () => 'Your relationship with regulators is costing you — approvals are slower and compliance work is heavier.',
  },
  regulatory_friction_opex_applied: {
    label: 'Regulatory Friction Cost',
    mechanism: 'Regulatory friction is charged as an OPEX rate across the group.',
    severity: 'bad',
    icon: '💸',
    explain: (v) => `Regulatory friction added ${money(v)} to your operating costs.`,
  },
  regulatory_ratchet: {
    label: 'Compliance Cost Ratchet',
    mechanism: 'Escalating compliance requirements permanently raise the cost base.',
    severity: 'bad',
    icon: '⚙️',
    explain: () => 'Compliance requirements escalated again, and that raises your cost base permanently.',
  },
  consent_decree_active: {
    label: 'Consent Decree',
    mechanism: 'A regulator-imposed consent decree constrains your choices until you demonstrate compliance.',
    severity: 'bad',
    icon: '⚖️',
    explain: () => 'You are operating under a consent decree — a regulator now has a say in decisions that used to be yours alone.',
  },
  legal_challenge_outcome: {
    label: 'Legal Challenge',
    mechanism: 'Legal challenges resolve against your ethical score — a clean record is a legal asset.',
    severity: 'neutral',
    icon: '🏛️',
    explain: (v) => `Your legal challenge resolved as "${token(v, 'decided')}" — your prior conduct was part of the evidence.`,
  },
  legal_challenge_fine: {
    label: 'Legal Fine',
    mechanism: 'An adverse legal outcome is charged as a fine against treasury.',
    severity: 'bad',
    icon: '💰',
    explain: (v) => `Losing that legal challenge cost you ${money(v)} in fines.`,
  },
  legal_challenge_suspended_bu: {
    label: 'Operations Suspended',
    mechanism: 'A severe adverse ruling suspends operations at the affected business unit.',
    severity: 'bad',
    icon: '🛑',
    explain: (v) => `${buName(v)} had its operations suspended by the ruling — no revenue while it stays shut.`,
  },
  eu_ai_act_compliance: {
    label: 'EU AI Act Compliance',
    mechanism: 'High-risk AI deployment triggers governance surcharges and mandatory audit requirements.',
    severity: 'bad',
    icon: '🤖',
    explain: () => 'Deploying high-risk AI brought EU AI Act obligations: governance surcharges and mandatory audits.',
  },
  eu_ai_act_pending: {
    label: 'EU AI Act Exposure Building',
    mechanism: 'AI deployment accrues future compliance obligations before they become chargeable.',
    severity: 'bad',
    icon: '⏰',
    explain: () => 'Your AI deployment is building a compliance obligation that has not been billed to you yet.',
  },
  compliance_cost_total: {
    label: 'Compliance Cost',
    mechanism: 'Regulatory obligations are charged per business unit and summed to a group total.',
    severity: 'bad',
    icon: '📋',
    explain: (v) => `Meeting your regulatory obligations cost ${money(v)} this round.`,
  },
  compliance_risk_index: {
    label: 'Compliance Risk',
    mechanism: 'Accumulated regulatory exposure across disclosure, emissions and labour obligations.',
    severity: 'bad',
    icon: '📛',
    explain: (v) => `Your compliance risk sits at ${num(v).toFixed(0)}/100 — this is the pathway to a regulatory shutdown ending.`,
  },
  materiality_aligned: {
    label: 'Materiality-Aligned Disclosure',
    mechanism: 'Disclosing against a genuine double-materiality assessment earns lasting governance credibility.',
    severity: 'good',
    icon: '🎯',
    explain: () => 'You disclosed against what actually matters, and that credibility pays back at the end of the game.',
  },
  materiality_ignored: {
    label: 'Materiality Ignored',
    mechanism: 'Disclosure that skips the material issues leaves you exposed when those issues fire.',
    severity: 'bad',
    icon: '🙈',
    explain: () => 'You disclosed around the issues that actually matter. That gap is exactly where the next shock arrives.',
  },
  scope3_data_challenge: {
    label: 'Scope 3 Data Challenge',
    mechanism: 'Auditors challenge Scope 3 figures that supply chain transparency cannot support.',
    severity: 'bad',
    icon: '❓',
    explain: () => 'Auditors challenged your Scope 3 numbers because your supply chain visibility cannot back them up.',
  },
  deep_audit_completed: {
    label: 'Deep Audit Completed',
    mechanism: 'A deep audit lifts the fog of war and unlocks accurate competitor and internal data.',
    severity: 'good',
    icon: '🔬',
    explain: () => 'You paid for a deep audit, and it bought you something rare: an accurate picture of your own business.',
  },
  brsr_grade: {
    label: 'BRSR Reporting Grade',
    mechanism: 'BRSR filing quality is graded across the nine NGRBC principles.',
    severity: 'neutral',
    icon: '🇮🇳',
    explain: (v) => `Your sustainability reporting was graded "${token(v, 'this round')}".`,
  },
  brsr_performance_score: {
    label: 'BRSR Score',
    mechanism: 'Your cumulative BRSR performance score across disclosure rounds.',
    severity: 'neutral',
    icon: '📑',
    explain: (v) => `Your BRSR performance score is ${num(v).toFixed(0)}.`,
  },
  brsr_truth_premium_blocked: {
    label: 'Truth Premium Blocked',
    mechanism: 'A weak disclosure record blocks the credibility premium honest reporting would otherwise earn.',
    severity: 'bad',
    icon: '🚫',
    explain: () => 'Your disclosure record was too weak for honest reporting to earn you any credibility premium.',
  },
  brsr_cpcb_penalty_active: {
    label: 'Pollution Board Penalty',
    mechanism: 'Pollution control board findings attract a standing penalty until remediated.',
    severity: 'bad',
    icon: '🏭',
    explain: () => 'The pollution control board has you under penalty, and it stands until you remediate.',
  },
  brsr_labor_unrest_risk: {
    label: 'Labour Unrest Risk',
    mechanism: 'Labour practice failures across the value chain raise unrest risk under NGRBC Principle 3.',
    severity: 'bad',
    icon: '⚡',
    explain: () => 'Labour practices in your value chain have raised the risk of unrest.',
  },

  /* ───────────────────────────────────────────────────────────────
     8. GOVERNANCE, BOARD & SESSION  (board_governance.py,
        org_politics.py, shadow_board_audit.py, pedagogical_engine.py)
     ─────────────────────────────────────────────────────────────── */

  board_governance: {
    label: 'Board Reaction',
    mechanism: 'The board scores your round against its own mandate and can escalate to resolutions.',
    severity: 'neutral',
    icon: '🪑',
    explain: () => 'Your board assessed this round against the mandate it gave you.',
  },
  board_pressure: {
    label: 'Board Pressure',
    mechanism: 'Accumulated performance signals build board pressure for a change of direction.',
    severity: 'bad',
    icon: '🔥',
    explain: (v) => `Board pressure is at ${num(v).toFixed(0)}/100 — they are running out of patience with the current direction.`,
  },
  pending_shareholder_resolutions: {
    label: 'Shareholder Resolutions',
    mechanism: 'Unaddressed investor concerns become formal resolutions tabled against management.',
    severity: 'bad',
    icon: '🗳️',
    explain: (v) => {
      const n = Array.isArray(v) ? v.length : 0;
      return n
        ? `${n} shareholder resolution${n === 1 ? ' has' : 's have'} been tabled against you.`
        : 'A shareholder resolution has been tabled against management.';
    },
  },
  org_politics: {
    label: 'Internal Politics',
    mechanism: 'Business unit heads compete for budget, and losers slow-walk delivery.',
    severity: 'neutral',
    icon: '🏛️',
    explain: () => 'Internal politics moved this round. Strategy does not execute itself — people who lose budget fights push back.',
  },
  shadow_board_rejection: {
    label: 'Shadow Board Rejection',
    mechanism: 'Rejecting a value logic in the shadow board audit permanently closes some endgame paths.',
    severity: 'bad',
    icon: '🎭',
    explain: (v) => `You rejected the "${typeof v === 'string' ? humaniseKey(v) : 'dissenting'}" logic, and that choice closes doors later in the game.`,
  },
  shadow_board_completed: {
    label: 'Shadow Board Audit Done',
    mechanism: 'The shadow board audit records which value logics you accepted and which you dismissed.',
    severity: 'neutral',
    icon: '📝',
    explain: () => 'You completed the shadow board audit. What you rejected there is now on the record.',
  },
  archetype_classification: {
    label: 'Leadership Archetype',
    mechanism: 'Your decision pattern across rounds is classified into a leadership archetype.',
    severity: 'neutral',
    icon: '🧬',
    explain: () => 'Your pattern of decisions has been classified into a leadership archetype — it is built from what you did, not what you said.',
  },
  system_archetypes_detected: {
    label: 'System Archetype Detected',
    mechanism: 'Recurring system dynamics (fixes that fail, shifting the burden, limits to growth) are named when detected.',
    severity: 'neutral',
    icon: '🔁',
    explain: (v) => {
      const n = Array.isArray(v) ? v.length : 0;
      return n
        ? `${n} classic system trap${n === 1 ? '' : 's'} showed up in your decision pattern — the same shape recurs across very different industries.`
        : 'A classic system trap showed up in your decision pattern.';
    },
  },
  decision_regret: {
    label: 'Decision Regret',
    mechanism: 'The gap between what you chose and what the best available option would have delivered.',
    severity: 'neutral',
    icon: '🪞',
    explain: () => 'The engine measured the gap between what you chose and the best option that was on the table.',
  },
  reflection_required: {
    label: 'Reflection Prompt',
    mechanism: 'Significant swings trigger a mandatory reflection before the next round unlocks.',
    severity: 'neutral',
    icon: '💭',
    explain: () => 'Something significant happened, so the simulation is asking you to stop and account for it before moving on.',
  },
  collaboration_gap: {
    label: 'Collaboration Gap',
    mechanism: 'Divergence between team members\' stated priorities is surfaced as a collaboration gap.',
    severity: 'neutral',
    icon: '🧩',
    explain: () => 'Your team is not aligned on priorities, and the gap is now visible.',
  },
  auto_committed: {
    label: 'Round Auto-Committed',
    mechanism: 'An unsubmitted round is committed automatically when the timer expires, using saved or default allocations.',
    severity: 'bad',
    icon: '⏰',
    explain: () => 'Time ran out and the round was committed for you. Not deciding is still a decision, and it was scored like one.',
  },
  ai_monetised: {
    label: 'AI Data Monetised',
    mechanism: 'Monetising data gives immediate revenue and accrues future compliance and trust costs.',
    severity: 'neutral',
    icon: '💽',
    explain: () => 'You monetised your data. The revenue lands now; the compliance and trust cost lands later.',
  },
  hidden_resources_unlocked: {
    label: 'Hidden Resources Unlocked',
    mechanism: 'Certain decision paths reveal capabilities and resources that were not visible before.',
    severity: 'good',
    icon: '🗝️',
    explain: () => 'That path revealed capabilities you did not know you had access to.',
  },
  side_track_completed: {
    label: 'Specialist Track Completed',
    mechanism: 'Completing a specialist side track contributes a bonus or penalty to the terminal multiple.',
    severity: 'neutral',
    icon: '🛤️',
    explain: () => 'You finished a specialist track, and it now feeds into your final score.',
  },
  side_track_score: {
    label: 'Specialist Track Score',
    mechanism: 'The score earned on the specialist track, converted into a terminal multiple adjustment.',
    severity: 'neutral',
    icon: '🎯',
    explain: (v) => `You scored ${num(v).toFixed(0)} on the specialist track.`,
  },
  pathway_discovery: {
    label: 'Ending Pathway Seeded',
    mechanism: 'Your decisions quietly select which endgame you will face; the foreshadowing chain follows from it.',
    severity: 'neutral',
    icon: '🧭',
    explain: () => 'Your decisions have quietly selected the ending you are heading towards. You will see the signals before you see the ending.',
  },
  mr_breakdown: {
    label: 'Regenerative Multiple Breakdown',
    mechanism: 'Every bonus and penalty contributing to the terminal Regenerative Multiple is itemised.',
    severity: 'neutral',
    icon: '🧾',
    explain: () => 'Your final Regenerative Multiple was itemised — every bonus and penalty is traceable to a decision.',
  },
  mr_capped_at: {
    label: 'Regenerative Multiple Capped',
    mechanism: 'Some earlier choices place a hard ceiling on the terminal multiple regardless of later performance.',
    severity: 'bad',
    icon: '🧢',
    explain: (v) => `An earlier decision capped your final multiple at ${num(v).toFixed(2)} — later rounds could not undo it.`,
  },
  mr_resilience_bonus: {
    label: 'Resilience Bonus to M_R',
    mechanism: 'Demonstrated resilience through shocks adds to the terminal multiple.',
    severity: 'good',
    icon: '🛡️',
    explain: (v) => `Coming through shocks intact added ${num(v).toFixed(2)} to your final multiple.`,
  },
  mr_just_transition_bonus: {
    label: 'Just Transition Bonus',
    mechanism: 'Decarbonising without abandoning workers and communities earns a terminal bonus.',
    severity: 'good',
    icon: '🤝',
    explain: (v) => `You decarbonised without abandoning your workforce, and that added ${num(v).toFixed(2)} to your final multiple.`,
  },
  mr_instability_discount: {
    label: 'Instability Discount',
    mechanism: 'Low average social licence discounts the terminal multiple — unstable earnings are worth less.',
    severity: 'bad',
    icon: '📉',
    explain: () => 'Chronically low social licence discounted your final valuation. Unstable earnings are worth less than stable ones.',
  },
  mr_truth_premium: {
    label: 'Truth Premium to M_R',
    mechanism: 'A record of honest disclosure adds a credibility premium at terminal valuation.',
    severity: 'good',
    icon: '🗝️',
    explain: (v) => `Your record of honest disclosure added ${num(v).toFixed(2)} to your final multiple.`,
  },
};

/* ═══════════════════════════════════════════════════════════════
   IGNORED KEYS — deliberate exclusions, not accidents.

   Everything not in this set is rendered by ConsequenceReplay, whether or
   not it has a catalog entry. Each key below is excluded because it is
   bookkeeping, configuration, or a carrier for state that the player is
   shown elsewhere — not because we ran out of copy for it.
   ═══════════════════════════════════════════════════════════════ */

export const IGNORED_KEYS = new Set([
  // ── Determinism & session configuration (facilitator-set, not caused by
  //    the player; showing them would imply the player did something) ──
  'stochastic_seed',          // RNG seed for cohort-identical rolls
  'difficulty_tier',          // facilitator difficulty band
  'decision_paradigm',        // which option set the round is drawn from
  'climate_paradigm',         // climate model variant selected for the cohort
  'region_id',                // geography, chosen at session setup
  'industry_vertical_applied', // vertical selected at session setup
  'ending_pathway',           // the endgame is *revealed* later by design
  'forced_black_swan',        // facilitator override, not a player consequence
  'custom_black_swans',       // narrative payloads rendered by the crisis feed
  'allowed_overrides',        // facilitator permission switch
  'allowed_swipes',           // facilitator permission switch
  'swipe_rounds',             // facilitator permission switch
  'override_rounds',          // facilitator permission switch
  'brain_drain_threshold',    // tunable constant, not an event
  'audit_tolerance',          // tunable constant, not an event
  'ceo_interview_enabled',    // feature toggle
  'ceo_interview_voice_gender', // presentation setting
  'carbon_tax_override_active', // facilitator override switch
  'global_carbon_fee',        // scenario-level rate, not a player action
  'shadow_carbon_price',      // scenario-level rate, not a player action
  'saved_allocations',        // in-progress form state carried between visits
  'saved_decision_choice',    // in-progress form state carried between visits
  'write_back_flags',         // plumbing for the side-track bridge
  'pathway_config_loaded',    // loader housekeeping
  'pathway_discovery_error',  // internal error channel, not player-facing

  // ── Identity / archetype carriers (revealed in their own dedicated
  //    reveal components; duplicating them here would spoil the reveal) ──
  'archetype',
  'brsr_archetype',
  'shadow_board_archetype',
  'profile',
  'profile_title',
  'profile_description',
  'profile_icon',
  'profile_gradient',

  // ── Terminal valuation carriers (the scorecard and Annual Report own
  //    these; the replay explains the round, not the final scoreboard) ──
  'terminal_value',
  'terminal_ebitda',
  'regenerative_multiple',
  'equity_value',
  'equity_bridge',
  'price_per_share',
  'shares_outstanding',
  'net_debt',
  'total_financial_debt',
  'exit_multiple',
  'exit_multiple_applied',
  'exit_multiple_wacc_used',
  'exit_multiple_dynamic',
  'exit_multiple_detail',
  'dynamic_exit_multiple_detail',
  'ev_over_revenue',
  'price_to_book',
  'ev_revenue_signal',
  'pb_signal',
  'final_treasury',
  'total_revenue',
  'total_opex',
  'group_reputation',

  // ── Raw diagnostic blobs (per-BU dumps and audit trails; they exist for
  //    the facilitator analytics views, and would be noise as a chain node) ──
  'consequence_waterfall',
  'black_swan_diagnostics',
  'esg_wacc_diagnostics',
  'workforce_readiness_diagnostics',
  'supply_chain_transparency_diag',
  'ncd_transparency',
  'sentiment_history',
  'sentiment_stakeholders',
  'brsr_round_history',
  'momentum_history',
  'decisions_raw',
  'forecast',
  'interest_rates',
  'strike_probabilities',
  'greenwashing_counterfactual',
  'greenwashing_threshold',
  'greenwashing_avg_investment_ratio',
  'fog_noise',
  'stochastic_roll',
  'stochastic_threshold',
  'strike_roll',
  'fired_materiality_shocks',
  'auto_injected_messages',
  'negotiation_log',
  'ceo_diary',

  // ── Decision bookkeeping (the chosen option is already the first node of
  //    the chain, so re-rendering it as a consequence would double-count) ──
  'choice_selected',
  'choice_label',
  'choice_title',
  'choice_description',
  'pillar_selections',
  'pillar_flags',
  'last_dividends_paid',      // carried forward purely to compute the ratchet
  'crisis_title',
  'crisis_icon',
  'crisis_description',
  'round_number',
  'auto_committed_source',    // 'auto_committed' itself IS shown; this is plumbing
  'auto_committed_reason',
]);

/**
 * Keys the engine uses purely as internal carry-over between layers within a
 * tick. They are prefixed with `_` by convention in backend/engine.py
 * (`_base_treasury_internal`, `_loan_principal_internal`, …) and are never
 * meant to reach a player. Handled as a prefix rule rather than an
 * enumeration so new internals are excluded automatically.
 */
export const IGNORED_KEY_PREFIXES = ['_'];

/**
 * Suffix families that are bookkeeping rather than events:
 *   `r3_flags`, `flags_set_r3`  — the flag list the chosen option set
 *   `r3_choice`                 — the option id, already node 1
 *   `r3_pillar_bypass`          — form-level bypass record
 */
const IGNORED_KEY_PATTERNS = [
  /^r\d{1,2}_flags$/,
  /^flags_set_r\d{1,2}$/,
  /^r\d{1,2}_choice$/,
  /^r\d{1,2}_pillar_bypass$/,
];
// NOTE: `*_message` and `*_because` keys are deliberately NOT ignored. They
// carry the engine's own plain-English rationale, which ConsequenceReplay uses
// verbatim as the explanation for keys with no catalog entry — which is exactly
// the "explain everything" behaviour this audit item asks for.

/** True when a flag key is deliberately excluded from the consequence chain. */
export function isIgnoredKey(key) {
  if (IGNORED_KEYS.has(key)) return true;
  if (IGNORED_KEY_PREFIXES.some((p) => String(key).startsWith(p))) return true;
  return IGNORED_KEY_PATTERNS.some((re) => re.test(String(key)));
}

export default CONSEQUENCE_CATALOG;
