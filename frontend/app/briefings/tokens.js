/**
 * ═══════════════════════════════════════════════════════════════
 *  BRIEFING TOKEN REGISTRY
 *
 *  Tokens are {{double-brace}} placeholders in briefing prose that
 *  get replaced at render time by the resolver using live session data.
 *
 *  TOKEN_DEFAULTS represent the standard 4-BU Muressons conglomerate.
 *  Any session matching that baseline returns these values unchanged,
 *  guaranteeing zero regression for the default configuration.
 *
 *  Naming convention: {{snake_case_noun}}
 *  All tokens must have a default value.
 * ═══════════════════════════════════════════════════════════════
 */

export const TOKEN_DEFAULTS = {
  // ── Organisation identity ──────────────────────────────────────
  company_name:     'Muressons Global',
  org_description:  'a diversified conglomerate spanning Pharmaceuticals, Electronics, Consumer Goods, and Software',
  cso_title:        'Chief Sustainability Officer',

  // ── BU roster descriptors ──────────────────────────────────────
  bu_count_word:    'four',
  bu_names_list:    'Pharmaceuticals, Electronics, Consumer Goods, and Software',

  // ── Dynamic paragraph (R1): revenue + footprint detail ────────
  // Resolved by deriveSimContext from live businessUnits[]; default
  // matches the original hardcoded narrative exactly.
  bu_intro_paragraph:
    'Your conglomerate is a complex beast. <strong>Muressons Pharma</strong> generates $18M in revenue with high water dependency. ' +
    '<strong>Electronics</strong> pulls in $16.5M but carries the highest carbon intensity at 72 units. ' +
    '<strong>Consumer Goods</strong> is the steady middle child at $10.5M, and <strong>Software</strong> — ' +
    'the leanest unit at $8.5M — has the lowest environmental footprint but the highest governance sensitivity.',

  // ── Role-specific BU references ───────────────────────────────
  // Resolved to the live highest-carbon, highest-water, governance BU names.
  // Defaults match the standard conglomerate composition.
  high_carbon_bu:       'Electronics',
  supply_chain_risk_bu: 'Electronics',
  crisis_origin_bu:     'Electronics',
  high_water_bus:       'Pharma and Electronics',
  high_margin_bu:       'Electronics',
  low_water_bu:         'Software',
  governance_bu:        'Software',
  factory_closure_description: 'two in the Consumer Goods division and one in Electronics',

  // ── Capital allocation target phrasing ────────────────────────
  // 'across all 4 BUs' in default; 'for [BU name]' in single-BU mode.
  capital_target: 'across all 4 BUs',

  // ── R4 water stress detail paragraph ──────────────────────────
  // Resolved from live water_dependency scores in single/swapped sessions.
  water_dependency_detail:
    '<strong>Pharma</strong> has the highest water dependency score (82) — ultra-pure water is essential for ' +
    'drug formulation and sterile manufacturing. <strong>Electronics</strong> (58) requires massive volumes for ' +
    'semiconductor wafer fabrication and cooling systems. <strong>Consumer Goods</strong> (65) depends on water ' +
    'for food and beverage processing lines. Only <strong>Software</strong> (12) has minimal direct water exposure.',
};
