/**
 * ═══════════════════════════════════════════════════════════════
 *  SINGLE-BU BRIEFING VARIANTS
 *
 *  When a session runs with exactly one business unit, several
 *  briefing passages that presuppose a multi-BU conglomerate
 *  (cross-BU contagion, "prioritise one division over the others",
 *  the R10 break-up-the-conglomerate ultimatum) stop making
 *  narrative sense. This module supplies replacement token values:
 *
 *   - genericSingleBu(bu): structural/grammar phrasing that works
 *     for ANY one-unit session (unknown/custom BUs included).
 *   - SINGLE_BU_VARIANTS[bu_id]: flavour overrides for the four
 *     standard verticals (supply chains, market reactions, and the
 *     activist's Round 10 argument).
 *
 *  Consumed by deriveSimContext() in briefings/resolver.js — merged
 *  over the derived token map when buCount === 1. Token names match
 *  the registry in briefings/tokens.js.
 * ═══════════════════════════════════════════════════════════════
 */

function genericSingleBu(bu) {
  const name = (bu && bu.name) || 'your business unit';
  return {
    audit_scope_phrase:      'your business unit',
    regulation_scope_phrase: 'your business unit',
    bu_initiatives_phrase:   'your business unit\'s',
    bu_waste_intro:          'Your business unit generates waste streams of varying complexity. It faces',
    symbiosis_scope:         'cross-site',
    ai_contagion_scope:      'across the entire company',

    scope3_supply_chain:
      'raw material extraction, tiered processing, and distribution networks across three continents',
    scope3_driver_sentence:
      'Upstream production and logistics alone account for 40% of your total Scope 3 footprint, ' +
      'driven by energy-intensive manufacturing and transport.',

    contagion_scope_sentence:
      'This is not just a procurement problem — reputational damage will propagate across ' +
      '<strong>your entire product portfolio</strong> and every market you serve.',
    contagion_market_reaction:
      'Key customers are reviewing their vendor ethics clauses. Boycott campaigns are spreading ' +
      'across your major sales channels.',
    contagion_objective:      'Manage reputational contagion across your product portfolio',
    social_license_objective: 'Protect your Social License to Operate across every market you serve',

    governance_bu_possessive:     `${name}'s`,
    governance_bu_possessive_cap: `${name}'s`,
    governance_bu_ref:            name,

    water_equity_sentence:
      'If you prioritise water allocation to your flagship high-margin production sites, you are ' +
      'essentially sacrificing your remaining facilities — communities and workers who depend on ' +
      'them will face devastating layoffs.',
    water_option_b_phrase:  'divert water to your flagship sites at $4M',
    water_option_b_label:   'Prioritise Flagship Sites',
    water_penalty_scope:    'on your remaining facilities',
    water_equity_objective: 'Be aware that prioritising flagship sites devastates other facilities\' Social License',

    factory_closure_description: 'your highest-emission production sites',

    activist_motion: `break up ${name}'s integrated structure`,
    activist_case:
      `${name}'s integrated structure obscures the true environmental cost of each operation. ` +
      'Cross-subsidisation of high-impact operations by high-margin lines is a form of corporate ' +
      'greenwashing. Each operating segment deserves its own sustainability mandate, its own ' +
      'carbon budget, and its own accountability structure.',
    synergy_question:
      'Did you build genuine synergies across your operating segments that justify the integrated structure?',
  };
}

export const SINGLE_BU_VARIANTS = {
  pharma: {
    scope3_supply_chain:
      'raw material extraction in Southeast Asia, active pharmaceutical ingredient production in India, ' +
      'and packaging and distribution networks across three continents',
    scope3_driver_sentence:
      'Upstream API synthesis and cold-chain logistics alone account for 40% of your total Scope 3 ' +
      'footprint, driven by energy-intensive manufacturing and temperature-controlled distribution.',
    contagion_market_reaction:
      'Hospital networks and insurers are reviewing their vendor ethics clauses. Boycott campaigns ' +
      'are spreading at major pharmacy chains.',
    activist_case:
      'Muressons Pharma\'s integrated structure — R&D, manufacturing, and distribution under one roof — ' +
      'obscures the true environmental cost of each operation. Cross-subsidisation of high-carbon ' +
      'manufacturing by high-margin R&D is a form of corporate greenwashing. Each operating segment ' +
      'deserves its own sustainability mandate, its own carbon budget, and its own accountability structure.',
  },

  electronics: {
    scope3_supply_chain:
      'rare earth mineral extraction in Southeast Asia, chip fabrication in Taiwan, and assembly ' +
      'and distribution networks across three continents',
    scope3_driver_sentence:
      'Upstream fabrication and rare earth mineral extraction alone account for 40% of your total ' +
      'Scope 3 footprint, driven by energy-intensive wafer production and mining.',
    contagion_market_reaction:
      'Enterprise clients are reviewing their vendor ethics clauses. Boycott campaigns are spreading ' +
      'at major electronics retailers.',
    activist_case:
      'Muressons Electronics\' integrated structure — component fabrication, assembly, and distribution ' +
      'under one roof — obscures the true environmental cost of each operation. Cross-subsidisation of ' +
      'high-carbon fabrication by high-margin device lines is a form of corporate greenwashing. Each ' +
      'operating segment deserves its own sustainability mandate, its own carbon budget, and its own ' +
      'accountability structure.',
  },

  consumer_goods: {
    scope3_supply_chain:
      'agricultural commodity sourcing in Southeast Asia, ingredient processing in India, and ' +
      'manufacturing and distribution networks across three continents',
    scope3_driver_sentence:
      'Upstream agricultural sourcing and packaging alone account for 40% of your total Scope 3 ' +
      'footprint, driven by land-use change and single-use plastics.',
    contagion_market_reaction:
      'Retail partners are reviewing their vendor ethics clauses. Boycott campaigns are spreading ' +
      'at major supermarket chains.',
    activist_case:
      'Muressons Consumer Goods\' integrated structure — sourcing, manufacturing, and brand distribution ' +
      'under one roof — obscures the true environmental cost of each operation. Cross-subsidisation of ' +
      'high-impact agricultural sourcing by high-margin brands is a form of corporate greenwashing. Each ' +
      'operating segment deserves its own sustainability mandate, its own carbon budget, and its own ' +
      'accountability structure.',
  },

  software: {
    scope3_supply_chain:
      'data centre hardware manufactured in East Asia, cloud infrastructure spanning three continents, ' +
      'and a global network of outsourced development partners',
    scope3_driver_sentence:
      'Purchased hardware and cloud infrastructure alone account for 40% of your total Scope 3 ' +
      'footprint, driven by embodied carbon in servers and data centre electricity.',
    contagion_market_reaction:
      'Enterprise clients are reviewing their vendor ethics clauses. Cancellation campaigns are ' +
      'spreading among major cloud customers.',
    activist_case:
      'Muressons Software\'s integrated structure — product development, cloud operations, and ' +
      'professional services under one roof — obscures the true environmental cost of each operation. ' +
      'Cross-subsidisation of energy-intensive cloud operations by high-margin software licences is a ' +
      'form of corporate greenwashing. Each operating segment deserves its own sustainability mandate, ' +
      'its own carbon budget, and its own accountability structure.',
  },
};

/**
 * singleBuTokens — token overrides for a one-unit session.
 * Generic phrasing first, then per-vertical flavour if the bu_id
 * matches a standard vertical.
 */
export function singleBuTokens(bu) {
  return {
    ...genericSingleBu(bu),
    ...(SINGLE_BU_VARIANTS[bu && bu.bu_id] || {}),
  };
}
