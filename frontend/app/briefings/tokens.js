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
  high_water_buses:     'Pharma and Electronics',
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

  // ── Multi-BU phrasing (tokenised so single-BU sessions read naturally) ──
  // Defaults reproduce the original 4-BU narrative exactly.
  audit_scope_phrase:      'all four business units',
  regulation_scope_phrase: 'all four of your business units',
  bu_initiatives_phrase:   'each business unit\'s',
  bu_waste_intro:          'Your four business units generate waste streams of varying complexity. Each division faces',
  symbiosis_scope:         'cross-BU',
  ai_contagion_scope:      'across all BUs',

  // ── Scope 3 supply chain description (R3) ─────────────────────
  scope3_supply_chain:
    'raw material extraction in Southeast Asia, chip fabrication in Taiwan, pharmaceutical ingredients from India, ' +
    'and consumer goods manufacturing across three continents',
  scope3_driver_sentence:
    'The Electronics division alone accounts for 40% of your total Scope 3 footprint, driven by energy-intensive ' +
    'fabrication and rare earth mineral extraction.',

  // ── Contagion crisis phrasing (R4) ────────────────────────────
  contagion_scope_sentence:
    'This is not just a Electronics problem — reputational damage will propagate across <strong>all your business units</strong>.',
  contagion_market_reaction:
    'Enterprise clients are reviewing their vendor ethics clauses. Boycott campaigns are spreading at major retailers.',
  contagion_objective:      'Manage cross-BU reputational contagion',
  social_license_objective: 'Protect Social License to Operate across all business units',

  // ── AI ethics phrasing (R6) ───────────────────────────────────
  governance_bu_possessive:     'your Software division\'s',
  governance_bu_possessive_cap: 'Your Software division\'s',
  governance_bu_ref:            'the Software division',

  // ── Water crisis phrasing (R8) ────────────────────────────────
  water_equity_sentence:
    'If you prioritise water allocation to your highest-margin division (Electronics), you are essentially ' +
    'sacrificing other operations — communities and workers who depend on those facilities will face devastating layoffs.',
  water_option_b_phrase: 'divert resources to Electronics at $4M',
  water_option_b_label:  'Prioritise Electronics',
  water_penalty_scope:   'on other BUs',
  water_equity_objective: 'Be aware that prioritising one BU devastates others\' Social License',

  // ── Grand Finale phrasing (R10) ───────────────────────────────
  activist_motion: 'dissolve the conglomerate structure',
  activist_case:
    'Your four business units — Pharmaceuticals, Electronics, Consumer Goods, and Software — are too fundamentally ' +
    'different to be managed sustainably under one roof. Cross-subsidisation of high-carbon assets by green divisions ' +
    'is a form of corporate greenwashing. Each unit deserves its own sustainability mandate, its own carbon budget, ' +
    'and its own accountability structure.',
  synergy_question: 'Did you build genuine cross-BU synergies that justify the structure?',
};
