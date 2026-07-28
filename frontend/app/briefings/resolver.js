import { TOKEN_DEFAULTS } from './tokens';
import { singleBuTokens } from './singleBuVariants';

// ─────────────────────────────────────────────────────────────────
//  DEFAULT BU ID SET — used to detect the unmodified 4-BU baseline
// ─────────────────────────────────────────────────────────────────
const DEFAULT_BU_IDS = new Set(['pharma', 'electronics', 'consumer_goods', 'software']);

/**
 * deriveSimContext
 *
 * Derives a complete token map from live session data.
 * This is the SINGLE place in the briefing subsystem where
 * business logic about simulation configuration lives.
 *
 * Design contract:
 *  - Pure function: same inputs always produce same output.
 *  - Returns TOKEN_DEFAULTS unchanged when the session is the standard
 *    4-BU conglomerate with no vertical substitutions — guaranteeing
 *    zero regression on the default configuration.
 *  - Derives all role-specific BU references (high-carbon, high-water,
 *    governance) from live BU data rather than hardcoded names.
 *
 * @param {Array}  businessUnits  Array of BU objects from sim.businessUnits
 *                                (already filtered for single-BU mode by page.js)
 * @param {Object} sessionMeta    { cohort_name, simulation_mode, assigned_bu, ... }
 *                                from the session-info API (via sim.sessionMeta)
 * @returns {Object}  Complete token map: { [tokenName]: resolvedString }
 */
export function deriveSimContext(businessUnits, sessionMeta) {
  const bus      = Array.isArray(businessUnits) ? businessUnits : [];
  const buCount  = bus.length;
  const cohort   = sessionMeta?.cohort_name || null;

  // ── Case 1: Standard 4-BU default, no vertical swaps ─────────────────────
  // Return base defaults unchanged — zero patching, zero regression risk.
  const isDefaultComposition =
    buCount === 4 && bus.every((bu) => DEFAULT_BU_IDS.has(bu.bu_id));

  if (isDefaultComposition && !cohort) {
    return TOKEN_DEFAULTS;
  }

  // ── Build resolved token map from live BU data ────────────────────────────

  // Sort helpers
  const byRevDesc     = [...bus].sort((a, b) => (b.revenue_base     || 0) - (a.revenue_base     || 0));
  const byCiDesc      = [...bus].sort((a, b) => (b.carbon_intensity || 0) - (a.carbon_intensity || 0));
  const byWaterDesc   = [...bus].sort((a, b) => (b.water_dependency || 0) - (a.water_dependency || 0));
  const byGovDesc     = [...bus].sort((a, b) => (b.governance_risk_score || 0) - (a.governance_risk_score || 0));

  const highCarbonBu  = byCiDesc[0]    || bus[0] || {};
  const highWaterBu   = byWaterDesc[0] || bus[0] || {};
  const lowWaterBu    = byWaterDesc[byWaterDesc.length - 1] || bus[bus.length - 1] || {};
  const highMarginBu  = byRevDesc[0]   || bus[0] || {};
  const govBu         = byGovDesc[0]   || bus[0] || {};

  // BUs with meaningful water dependency (>40) for "Pharma and Electronics" style phrasing
  const waterDependentBus = bus.filter((b) => (b.water_dependency || 0) > 40);
  const highWaterBusStr   =
    waterDependentBus.length > 0
      ? waterDependentBus.map((b) => b.name).join(' and ')
      : highWaterBu.name || TOKEN_DEFAULTS.high_water_buses;

  // BU name list: "A, B, C, and D"
  const buNamesList =
    buCount <= 1
      ? (bus[0]?.name || 'your business unit')
      : buCount === 2
        ? bus.map((b) => b.name).join(' and ')
        : bus.slice(0, -1).map((b) => b.name).join(', ') + ', and ' + bus[bus.length - 1].name;

  const buCountWord =
    ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'][buCount]
    || String(buCount);

  const orgDescription =
    buCount === 1
      ? `a focused ${bus[0]?.name || 'business'} operation`
      : `a diversified conglomerate spanning ${buNamesList}`;

  // company_name is always the fixed brand — it never varies with session
  // metadata. cohort_name is a player/cohort label (e.g. "lkj") that lives
  // in sessionMeta.cohort_name and must NOT override the company brand.
  const companyName = TOKEN_DEFAULTS.company_name; // always "Muressons Global"
  const cohortLabel = cohort || '';                 // exposed as {{cohort_name}} if templates need it


  // ── bu_intro_paragraph: R1 revenue + footprint summary ───────────────────
  const buIntroParagraph = (() => {
    if (buCount === 1) {
      const bu  = bus[0];
      const rev = bu.revenue_base ? `$${(bu.revenue_base / 1_000_000).toFixed(0)}M` : '';
      const ci  = bu.carbon_intensity ? ` with a carbon intensity of ${bu.carbon_intensity} tCO\u2082e per $1M revenue` : '';
      const wd  = bu.water_dependency ? ` and a water dependency score of ${bu.water_dependency}` : '';
      return `<strong>${bu.name}</strong>${rev ? ` generates ${rev} in revenue` : ''}${ci}${wd}.`;
    }
    // Multi-BU: generate a sentence per BU from live data, highest revenue first
    return byRevDesc.map((bu) => {
      const rev = bu.revenue_base
        ? `$${(bu.revenue_base / 1_000_000).toFixed(1)}M`
        : '';
      const ci  = bu.carbon_intensity ? ` (carbon intensity: ${bu.carbon_intensity})` : '';
      return `<strong>${bu.name}</strong>${rev ? ` generates ${rev}` : ''}${ci}`;
    }).join('. ') + '.';
  })();

  // ── water_dependency_detail: R8 paragraph ────────────────────────────────
  const waterDependencyDetail = (() => {
    if (buCount === 1) {
      const bu = bus[0];
      return `<strong>${bu.name}</strong> has a water dependency score of ${bu.water_dependency || 'N/A'}.`;
    }
    return byWaterDesc.map((bu) => {
      const score = bu.water_dependency != null ? ` (${bu.water_dependency})` : '';
      return `<strong>${bu.name}</strong>${score}`;
    }).join(', ') + '.';
  })();

  // ── factory_closure_description ──────────────────────────────────────────
  // R9 mentions specific BU closures; in a non-default session use generic phrasing.
  const factoryClosureDescription = isDefaultComposition
    ? TOKEN_DEFAULTS.factory_closure_description
    : `across your highest-emission divisions`;

  // ── capital_target ────────────────────────────────────────────────────────
  const capitalTarget =
    buCount === 1
      ? `for ${bus[0]?.name || 'your business unit'}`
      : `across all ${buCount} BUs`;

  const tokens = {
    ...TOKEN_DEFAULTS,   // safe baseline — unknown tokens fall back to defaults
    company_name:               companyName,
    cohort_name:                cohortLabel,  // player/cohort label — separate from company brand
    org_description:            orgDescription,
    bu_count_word:              buCountWord,
    bu_names_list:              buNamesList,
    bu_intro_paragraph:         buIntroParagraph,
    high_carbon_bu:             highCarbonBu.name  || TOKEN_DEFAULTS.high_carbon_bu,
    supply_chain_risk_bu:       highCarbonBu.name  || TOKEN_DEFAULTS.supply_chain_risk_bu,
    crisis_origin_bu:           highCarbonBu.name  || TOKEN_DEFAULTS.crisis_origin_bu,
    high_water_buses:           highWaterBusStr,
    high_margin_bu:             highMarginBu.name  || TOKEN_DEFAULTS.high_margin_bu,
    low_water_bu:               lowWaterBu.name    || TOKEN_DEFAULTS.low_water_bu,
    governance_bu:              govBu.name         || TOKEN_DEFAULTS.governance_bu,
    factory_closure_description: factoryClosureDescription,
    capital_target:             capitalTarget,
    water_dependency_detail:    waterDependencyDetail,

    // ── Multi-BU phrasing, derived from live BU data ─────────────────────
    audit_scope_phrase:         `all ${buCountWord} business units`,
    regulation_scope_phrase:    `all ${buCountWord} of your business units`,
    scope3_driver_sentence:
      `The ${highCarbonBu.name} division alone accounts for 40% of your total Scope 3 footprint, ` +
      'driven by energy-intensive fabrication and rare earth mineral extraction.',
    contagion_scope_sentence:
      `This is not just a ${highCarbonBu.name} problem — reputational damage will propagate across ` +
      '<strong>all your business units</strong>.',
    governance_bu_possessive:     `your ${govBu.name} division's`,
    governance_bu_possessive_cap: `Your ${govBu.name} division's`,
    governance_bu_ref:            `the ${govBu.name} division`,
    water_equity_sentence:
      `If you prioritise water allocation to your highest-margin division (${highMarginBu.name}), ` +
      'you are essentially sacrificing other operations — communities and workers who depend on ' +
      'those facilities will face devastating layoffs.',
    water_option_b_phrase:      `divert resources to ${highMarginBu.name} at $4M`,
    water_option_b_label:       `Prioritise ${highMarginBu.name}`,
    activist_case:
      `Your ${buCountWord} business units — ${buNamesList} — are too fundamentally different to be ` +
      'managed sustainably under one roof. Cross-subsidisation of high-carbon assets by green divisions ' +
      'is a form of corporate greenwashing. Each unit deserves its own sustainability mandate, its own ' +
      'carbon budget, and its own accountability structure.',
  };

  // ── Single-BU sessions: overlay variant passages so the narrative reads
  //    as one integrated business (generic + per-vertical flavour). ──────
  if (buCount === 1) {
    Object.assign(tokens, singleBuTokens(bus[0]));
  }

  return tokens;
}

/**
 * resolveBriefing
 *
 * Resolves all {{token}} placeholders in a briefing template object
 * using the provided token map.  Pure function — no side effects.
 *
 * Contract:
 *  - Processes narrative[], objectives[], and warning.text
 *  - Any {{unknown_token}} is rendered literally (visible in dev,
 *    non-crashing in production)
 *  - Returns null/undefined unchanged if template is falsy
 *
 * @param {Object|null} template  One entry from a briefings dictionary
 * @param {Object}      tokenMap  From deriveSimContext()
 * @returns {Object|null}         Resolved briefing object (same shape as template)
 */
export function resolveBriefing(template, tokenMap) {
  if (!template) return template;

  const resolve = (str) => {
    if (typeof str !== 'string') return str;
    return str.replace(/\{\{(\w+)\}\}/g, (match, key) =>
      Object.prototype.hasOwnProperty.call(tokenMap, key) ? tokenMap[key] : match
    );
  };

  return {
    ...template,
    narrative:  Array.isArray(template.narrative)  ? template.narrative.map(resolve)  : [],
    objectives: Array.isArray(template.objectives) ? template.objectives.map(resolve) : [],
    warning: template.warning
      ? { ...template.warning, text: resolve(template.warning.text) }
      : null,
  };
}
