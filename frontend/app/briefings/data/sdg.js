/**
 * ═══════════════════════════════════════════════════════════════
 *  SDG EDITION BRIEFINGS — 10 Rounds
 *
 *  SDG briefings use region names (Sub-Saharan Corridor, etc.)
 *  rather than corporate BU names, so they are not subject to
 *  vertical substitution. No {{tokens}} are needed.
 *
 *  Extracted verbatim from the original RoundBriefing.js.
 * ═══════════════════════════════════════════════════════════════
 */

export const SDG_BRIEFINGS = {
  1: {
    icon: '🎯', title: 'SDG Mandate Selection', theme: 'Choose Your Development Doctrine',
    stamp: 'PRIORITY: CRITICAL',
    narrative: [
      'The <strong>United Nations General Assembly</strong> has appointed you Special Envoy for Sustainable Development. You are responsible for 1.47 billion people across four regions: Sub-Saharan Corridor, South Asia Subcontinent, South-East Asia Hub, and Northern Transition Zone.',
      'Each region begins at different development stages. <strong>Sub-Saharan Corridor</strong> scores lowest on governance (20) and basic needs (25). The <strong>Northern Transition Zone</strong> leads with governance at 65 but faces sustainability decay.',
      'Your first mandate: choose a development doctrine that will shape your entire decade. Will you prioritise <em>poverty first</em>, <em>economic growth</em>, or a <em>balanced portfolio</em> approach? This choice sets the foundation for every subsequent round.',
    ],
    objectives: [
      'Select your development mandate: Poverty First, Growth Engine, or Balanced Portfolio',
      'Understand the SDG interlinkage matrix — investments in one cluster spill over to others',
      'Assess regional governance scores — weak governance causes institutional leakage (40% loss)',
      'Complete the Stakeholder Power/Interest Grid for global development actors',
    ],
    metrics: [
      { icon: '🏛️', label: 'Governance' },
      { icon: '🏥', label: 'Basic Needs' },
      { icon: '📊', label: 'Political Capital' },
    ],
    warning: null,
  },
  2: {
    icon: '💧', title: 'WASH Emergency', theme: 'Water, Sanitation & Hygiene Crisis (SDG 6)',
    stamp: 'HUMANITARIAN EMERGENCY',
    narrative: [
      'Contaminated water supplies have triggered a health emergency affecting <strong>200 million people</strong> across the Sub-Saharan Corridor and South Asia Subcontinent. Cholera outbreaks are spreading rapidly.',
      'The <strong>Sanitation Miracle</strong> mechanic can activate if a region pushes both Basic Needs and Human Capital above 75 — doubling the effectiveness of all future investments. But reaching that threshold requires heavy upfront commitment.',
      'Your budget is constrained by <strong>donor fatigue</strong>. If your Political Capital and Community Trust scores drop below 50, your funding multiplier shrinks to 80%.',
    ],
    objectives: [
      'Address the immediate WASH crisis across affected regions',
      'Invest in water infrastructure or emergency desalination',
      'Balance short-term relief against long-term capacity building',
      'Complete the CSRD-equivalent double materiality mapping for development aid',
    ],
    metrics: [
      { icon: '💧', label: 'Basic Needs' },
      { icon: '🏥', label: 'Human Capital' },
      { icon: '💰', label: 'Budget Multiplier' },
    ],
    warning: { text: '<strong>Donor Fatigue Warning:</strong> If Political Capital drops below 50, your budget effectiveness decreases by 20%.' },
  },
  3: {
    icon: '📚', title: 'Education Investment', theme: 'Human Capital Formation (SDG 4 & 8)',
    stamp: 'LONG-TERM INVESTMENT',
    narrative: [
      'Half a generation in the Sub-Saharan and South Asian corridors risk losing access to education. Without intervention, <strong>human capital scores will stagnate</strong> for the rest of the decade.',
      'Education investments carry a unique <strong>3-round lag</strong>: the impact of schooling programmes takes time to yield returns. Option A (Compulsory Schooling) creates an "education lag project" that matures after 3 rounds, boosting sustainable growth.',
      'Alternatively, blockchain-based supply chain traceability (Option C) can be deployed now to prevent a corruption scandal later in Round 8.',
    ],
    objectives: [
      'Decide between immediate impact vs delayed-maturation education investment',
      'Consider the 3-round education lag mechanic',
      'Explore blockchain traceability for future scandal prevention',
    ],
    metrics: [
      { icon: '📚', label: 'Human Capital' },
      { icon: '📈', label: 'Sustainable Growth' },
      { icon: '🔗', label: 'Partnerships' },
    ],
    warning: { text: '<strong>Education Lag:</strong> Schooling investments take 3 rounds before yielding returns (SDG 4 → SDG 8 multiplier).' },
  },
  4: {
    icon: '🦠', title: 'Pandemic Response', theme: 'Health System Resilience (SDG 3)',
    stamp: 'EMERGENCY RESPONSE',
    narrative: [
      'A disease outbreak has overwhelmed health systems in the poorest corridors. The <strong>Sub-Saharan Corridor</strong> faces collapse, while the <strong>Northern Transition Zone</strong> has capacity to absorb.',
      'Your response will test the <strong>migration contagion</strong> mechanic. If wealth gradients between regions exceed thresholds, populations will migrate toward wealthier regions, degrading service delivery there.',
      'A total lockdown protects health metrics but damages economic growth. Targeted shielding is moderate. Herd immunity gambling is the riskiest but cheapest.',
    ],
    objectives: [
      'Respond to the pandemic across all four regions',
      'Manage the migration contagion mechanic',
      'Balance health protection against economic damage',
    ],
    metrics: [
      { icon: '🏥', label: 'Basic Needs' },
      { icon: '🌍', label: 'Migration Pressure' },
      { icon: '🏛️', label: 'Governance' },
    ],
    warning: { text: '<strong>Migration Alert:</strong> Wealth gradients between regions trigger population migration, straining wealthier regions.' },
  },
  5: {
    icon: '🌊', title: 'Climate Resilience', theme: 'Physical Climate Risk (SDG 13)',
    stamp: 'STOCHASTIC EVENT',
    narrative: [
      'A Category 5 cyclone is bearing down on the South-East Asian coast. <strong>$12M base damage</strong> will be rolled stochastically. Your infrastructure investments determine resilience.',
      'The <strong>Carbon Retribution</strong> hook is active: if global emissions intensity exceeded 100 by Round 5, damage is <strong>tripled</strong>. This is the simulation\'s climate justice mechanic.',
      'Choose between rebuilding inland (displacing communities), coastal hardening, or accepting climate migration.',
    ],
    objectives: [
      'Prepare for the stochastic climate event',
      'Assess carbon retribution risk from accumulated emissions',
      'Choose between resilience investment, relocation, or migration acceptance',
    ],
    metrics: [
      { icon: '🌡️', label: 'Emissions' },
      { icon: '🛡️', label: 'Resilience' },
      { icon: '🌍', label: 'Planet Score' },
    ],
    warning: { text: '<strong>Carbon Retribution:</strong> If global emissions exceeded 100, cyclone damage is tripled.' },
  },
  6: {
    icon: '📡', title: 'Digital Divide', theme: 'Technology & Data Sovereignty (SDG 9 & 17)',
    stamp: 'GOVERNANCE CRISIS',
    narrative: [
      'AI-driven agricultural monitoring systems have been found to exhibit systematic bias against smallholder farmers in the Sub-Saharan Corridor. Data sovereignty debates are escalating.',
      'You must decide: full transparency and disclosure, bias correction patches, or asserting data sovereignty for affected regions.',
      'Your choice affects <strong>governance scores</strong> and <strong>partnerships</strong> — critical SDG clusters that influence the interlinkage spillover matrix.',
    ],
    objectives: [
      'Address AI bias in development technology',
      'Manage data sovereignty vs transparency trade-offs',
      'Protect governance and partnership scores',
    ],
    metrics: [
      { icon: '🏛️', label: 'Governance' },
      { icon: '🤝', label: 'Partnerships' },
      { icon: '📡', label: 'Digital Access' },
    ],
    warning: null,
  },
  7: {
    icon: '⛏️', title: 'Resource Extraction', theme: 'Responsible Mining & Biodiversity (SDG 12 & 15)',
    stamp: 'ENVIRONMENTAL CONFLICT',
    narrative: [
      'Critical mineral deposits have been discovered beneath indigenous lands in the South-East Asia Hub. The minerals are essential for renewable energy transition, but extraction threatens biodiversity corridors.',
      'Full extraction maximises economic growth but devastates planet scores. Conditional mining with environmental safeguards is moderate. Mandating recycled materials preserves biodiversity but limits growth.',
      'A potential resource conflict can be prevented if you choose carefully — this is a key <strong>interlinkage moment</strong> where planet and sustainable growth scores interact.',
    ],
    objectives: [
      'Balance resource extraction against biodiversity protection',
      'Manage indigenous community relations',
      'Consider recycled materials mandate as alternative',
    ],
    metrics: [
      { icon: '🌿', label: 'Planet' },
      { icon: '📈', label: 'Sustainable Growth' },
      { icon: '🤝', label: 'Community Trust' },
    ],
    warning: null,
  },
  8: {
    icon: '⚡', title: 'Just Transition', theme: 'Energy Transition & Labor (SDG 8 & 10)',
    stamp: 'STRIKE WARNING',
    narrative: [
      'Coal plant closures across the Northern Transition Zone and South Asia Subcontinent have displaced thousands of workers. Strike probabilities are escalating in regions with low governance.',
      'If you deployed <strong>Blockchain Traceability</strong> in Round 3, a potential corruption scandal is prevented, earning a governance bonus.',
      'Choose between crushing the strike (cheap, devastating social impact), green retraining (balanced), or abandoning the transition entirely (preserves jobs, increases emissions).',
    ],
    objectives: [
      'Manage the just transition for displaced workers',
      'Address strike risk across vulnerable regions',
      'Decide the pace of energy transition',
    ],
    metrics: [
      { icon: '⚡', label: 'Strike Probability' },
      { icon: '📊', label: 'Governance' },
      { icon: '💼', label: 'Human Capital' },
    ],
    warning: { text: '<strong>Strike Alert:</strong> Regions with governance below 40 face elevated strike probability. Institutional leakage amplifies damage.' },
  },
  9: {
    icon: '💰', title: 'Debt & Innovative Finance', theme: 'Financing the SDGs (SDG 1 & 17)',
    stamp: 'FISCAL EMERGENCY',
    narrative: [
      'Sovereign debt spirals across the Sub-Saharan and South Asian corridors threaten to undo a decade of development progress. International creditors are demanding austerity.',
      'You have three options: impose austerity (cheapest but devastates social scores), negotiate a debt jubilee (moderate), or issue innovative SDG bonds (expensive but sustainable).',
      'Your <strong>partnerships score</strong> determines bond market confidence. Higher partnerships yield better financing terms.',
    ],
    objectives: [
      'Address the sovereign debt crisis',
      'Explore innovative financing mechanisms',
      'Protect social and governance gains from austerity pressure',
    ],
    metrics: [
      { icon: '💰', label: 'Treasury' },
      { icon: '🤝', label: 'Partnerships' },
      { icon: '📊', label: 'Political Capital' },
    ],
    warning: { text: '<strong>Debt Spiral:</strong> If governance scores remain below 30, debt restructuring costs increase by 50%.' },
  },
  10: {
    icon: '🏛️', title: 'Legacy of Leadership', theme: 'Terminal HDI Assessment (All SDGs)',
    stamp: 'FINAL ASSESSMENT',
    narrative: [
      'Your decade as Special Envoy concludes. The <strong>UN General Assembly</strong> will assess your legacy based on a population-weighted <strong>Human Development Index (HDI)</strong> calculated from all six SDG clusters.',
      'The HDI formula weights: <strong>Basic Needs (25%)</strong>, <strong>Human Capital (25%)</strong>, <strong>Sustainable Growth (20%)</strong>, <strong>Planet (15%)</strong>, <strong>Governance (10%)</strong>, <strong>Partnerships (5%)</strong>.',
      'An <strong>equity penalty</strong> is applied based on inter-regional inequality. If the gap between your richest and poorest regions is large, your terminal HDI takes a significant hit. True leadership leaves no one behind.',
      'Your final choice: build institutional legacy (governance focus), launch an emergency surge in the weakest region, or quietly exit.',
    ],
    objectives: [
      'Make your final strategic allocation',
      'Maximise population-weighted HDI',
      'Minimise the inter-regional equity penalty',
      'Achieve Transformative Leader (≥80), Pragmatic Steward (≥60), or avoid Catastrophic Neglect (<40)',
    ],
    metrics: [
      { icon: '📊', label: 'Terminal HDI' },
      { icon: '⚖️', label: 'Equity Penalty' },
      { icon: '🏛️', label: 'Profile Grade' },
    ],
    warning: { text: '<strong>Equity Penalty:</strong> Inter-regional inequality (std dev) directly reduces your terminal HDI score. Balance is essential.' },
  },
};
