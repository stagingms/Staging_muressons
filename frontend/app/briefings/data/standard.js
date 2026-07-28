/**
 * ═══════════════════════════════════════════════════════════════
 *  STANDARD BRIEFINGS — 10 Rounds (Conglomerate / ESG mode)
 *
 *  All BU-specific values that vary by session configuration are
 *  expressed as {{token}} placeholders resolved at render time by
 *  resolveBriefing() in briefings/resolver.js.
 *
 *  Token reference: see briefings/tokens.js
 *
 *  Sessions using the default 4-BU composition receive the base
 *  TOKEN_DEFAULTS which reproduce the original hardcoded narrative
 *  exactly — zero regression for existing sessions.
 * ═══════════════════════════════════════════════════════════════
 */

export const STANDARD_BRIEFINGS = {
  1: {
    icon: '📋',
    title: 'Foundations',
    theme: 'ESG Baseline Assessment',
    stamp: 'PRIORITY: HIGH',
    narrative: [
      'The Board of Directors has convened an emergency session. Global regulators are tightening ESG disclosure requirements, and <strong>{{company_name}}</strong> — {{org_description}} — has never conducted a comprehensive ESG materiality assessment.',
      'As the newly appointed <em>{{cso_title}}</em>, your first mandate is clear: determine the depth and scope of an initial ESG audit across {{audit_scope_phrase}}. The audit results will shape every strategic decision you make for the next decade.',
      '{{bu_intro_paragraph}}',
      'Before making your audit decision, you must also complete the <strong>Stakeholder Power/Interest Grid</strong><span class="ped-academic"> (Mendelow\'s Matrix)</span> to map the political landscape. Understanding who holds power over your ESG agenda — regulators, investors, employees, communities — is essential groundwork for every crisis ahead.',
      'Choose carefully. A superficial scan may save money now, but <strong>blind spots in the {{supply_chain_risk_bu}} supply chain</strong> could come back to haunt you when scrutiny intensifies in later rounds. The consequences of this first decision cascade forward through all ten rounds.',
    ],
    objectives: [
      'Decide audit depth: Surface scan, deep forensic audit, or phased rollout',
      'Balance upfront cost against long-term risk visibility',
      'Complete the Stakeholder Power/Interest Grid (Mendelow\'s Matrix)',
      'Set your initial capital allocation strategy {{capital_target}}',
    ],
    metrics: [
      { icon: '💰', label: 'Treasury' },
      { icon: '⭐', label: 'Reputation' },
      { icon: '🔍', label: 'Risk Visibility' },
    ],
    warning: null,
  },

  2: {
    icon: '📊',
    title: 'Double Materiality',
    theme: 'Materiality-Based Budget Allocation',
    stamp: 'CFO GATE ACTIVE',
    narrative: [
      'The CFO has imposed a new investment governance framework: the <strong>Double Materiality Matrix</strong>. Every capital allocation must now demonstrate alignment with both <em>high financial impact</em> and <em>high ESG impact</em> criteria.<span class="ped-academic"> This aligns with the EU\'s Corporate Sustainability Reporting Directive (CSRD), which requires companies to assess and report on both how sustainability issues affect the business (financial materiality) and how the business affects society and the environment (impact materiality).</span>',
      'This is not optional. Proposals that fall outside the top-right quadrant of the materiality matrix will be <strong>rejected by the CFO</strong> unless you invoke an executive override — at the cost of your reputation. The CFO has made clear: "Every dollar we invest must serve both our shareholders and our stakeholders. If it doesn\'t pass the double materiality test, it doesn\'t get funded."',
      'You must complete the CSRD Materiality Assessment before making any strategic decisions this round. You will map {{bu_initiatives_phrase}} initiatives onto a 2×2 matrix of Financial Impact vs ESG Impact. Only initiatives landing in <strong>Quadrant 1 (High/High)</strong> will receive automatic approval. Everything else requires justification or override.',
      'This is your first taste of regulatory friction — the tension between what is profitable and what is sustainable. How you navigate this framework will set the tone for your governance credibility throughout the simulation.',
    ],
    objectives: [
      'Complete and submit the CSRD Double Materiality Assessment',
      'Allocate your budget to initiatives in the High Impact quadrant',
      'Decide whether to fully align, allow exceptions, or ignore the framework',
      'Consider the governance risk implications of each approach',
    ],
    metrics: [
      { icon: '⭐', label: 'Reputation' },
      { icon: '⚖️', label: 'Governance Risk' },
      { icon: '📈', label: 'Strategic Alignment' },
    ],
    warning: {
      text: '<strong>📊 CSRD Governance Premium:</strong> Achieving ≥80% Q1 accuracy AND choosing Option A/B governance unlocks <strong>+0.10 M_R</strong> at Round 10 (ESRS 1 §1.51). It also <strong>reduces your R3 Green Bond cost by $500K</strong>. Option C or poor accuracy triggers a $1M Green Bond risk premium.',
    },
  },

  3: {
    icon: '🏭',
    title: 'Scope 3 Emissions',
    theme: 'Supply Chain Decarbonisation',
    stamp: 'REGULATORY SIGNAL',
    narrative: [
      'Breaking news from Brussels: <strong>mandatory Scope 3 disclosure</strong> is now on the regulatory horizon.<span class="ped-academic"> The International Sustainability Standards Board (ISSB) has finalised standards requiring full value-chain emissions reporting.</span> Preliminary analysis shows that your supply chain carbon footprint is <em>four times</em> your direct emissions — and investors are watching.',
      'Your supply chain spans {{scope3_supply_chain}}. Each link in this chain carries embedded carbon that will soon appear on your balance sheet. {{scope3_driver_sentence}}',
      'The financial stakes are real. Scope 3 emissions will eventually feed into your <strong>Natural Capital Debt (NCD)</strong> — a running tally of your environmental liability that compounds over rounds and directly affects your Year 5 Terminal Valuation. Ignoring it now means paying more later.',
      'The clock is ticking. You can switch suppliers immediately (fast but disruptive, with risk of operational downtime in {{high_water_buses}}), issue a green bond for gradual transition (moderate cost, lower NCD), or buy carbon offsets and defer the hard decisions. Each path has very different consequences for your carbon intensity trajectory and treasury.',
    ],
    objectives: [
      'Address Scope 3 emissions exposure across the supply chain',
      'Choose between rapid disruption, structured transition, or deferral',
      'Manage Natural Capital Debt — it accumulates across rounds',
      'Consider how supply chain disruption might affect {{high_water_buses}}',
    ],
    metrics: [
      { icon: '🌡️', label: 'Carbon Intensity' },
      { icon: '🌿', label: 'NCD (Natural Capital)' },
      { icon: '💰', label: 'Treasury' },
    ],
    warning: null,
  },

  4: {
    icon: '🔥',
    title: 'Contagion',
    theme: 'Reputation Crisis Cascade',
    stamp: 'CRISIS ALERT',
    narrative: [
      'A whistleblower exposé has gone viral: <strong>child labour allegations</strong> in your {{crisis_origin_bu}} supply chain. An investigative journalist has published footage from a tier-2 supplier facility in Southeast Asia showing underage workers. The story was broken by a major news outlet and is trending globally within hours. Hashtags calling for a {{company_name}} boycott are dominating social media.',
      'The <em>Contagion Engine</em> is now active. {{contagion_scope_sentence}} Customers are questioning whether your operations follow the same ethical shortcuts. {{contagion_market_reaction}}',
      'The base crisis severity is <strong>40 points</strong>, but if you failed to conduct a deep audit in Round 1, the {{crisis_origin_bu}} blind spot means this crisis hits at <strong>80 points</strong> — double the impact. The forensic audit you could have done would have caught these supplier issues before they became front-page news.',
      'Your response will define whether this crisis becomes a defining moment of transparency — earning long-term stakeholder trust — or the beginning of a death spiral. Full remediation costs $6M but repairs reputation. PR containment is cheaper but does not fix the root cause. Denial risks catastrophic long-term consequences. The board is watching. The market is watching. The world is watching.',
    ],
    objectives: [
      'Respond to the {{crisis_origin_bu}} supply chain scandal',
      '{{contagion_objective}}',
      'Choose between transparency, PR containment, or denial',
      '{{social_license_objective}}',
    ],
    metrics: [
      { icon: '⭐', label: 'Reputation' },
      { icon: '🤝', label: 'Social License' },
      { icon: '📊', label: 'Contagion Spread' },
    ],
    warning: {
      text: '<strong>⚡ Blindspot Check:</strong> If you chose a Surface-Level Scan or Phased Audit in Round 1, the {{crisis_origin_bu}} blind spot is active — <strong>crisis severity is DOUBLED</strong> (40 → 80). A Deep Forensic Audit would have protected you.',
    },
  },

  5: {
    icon: '🌪️',
    title: 'Climate',
    theme: 'Physical Climate Risk Event',
    stamp: 'STOCHASTIC EVENT',
    narrative: [
      'Meteorological services have issued a <strong>Category 4 cyclone warning</strong> for the coastal corridor housing your primary manufacturing facilities. Satellite imagery shows a massive storm system forming in the Indian Ocean, projected to make landfall within 72 hours. Projected base damage: <em>$12 million</em>.',
      'This is not a strategic choice — it\'s a force of nature. A <strong>stochastic dice roll</strong> (75% probability of landfall) will determine whether the cyclone strikes your facilities. You cannot prevent the storm, but you can choose how to prepare: build hard engineering defences (flood walls, reinforced infrastructure), invest in nature-based solutions (mangrove restoration, natural buffers), or rely solely on insurance coverage.',
      'Each option carries a different <strong>Resilience Factor</strong> — the percentage of damage you can mitigate if the storm hits. Hard engineering offers 85% mitigation but adds to your Natural Capital Debt through concrete and steel. Nature-based solutions offer 60% mitigation while actually <em>reducing</em> your NCD. Insurance provides zero mitigation but is the cheapest upfront option.',
      'The implications extend beyond this round. Your resilience strategy here feeds into your <strong>Year 5 Regenerative Multiple</strong>. Choosing the insurance-only path signals to investors that you are not building genuine climate resilience — and it will block a critical +0.20 bonus in your final valuation.',
    ],
    objectives: [
      'Prepare for a physical climate event with real financial consequences',
      'Choose your resilience strategy: Hard engineering, nature-based, or insurance',
      'Understand the trade-off between upfront cost and damage mitigation',
      'Consider the Natural Capital Debt implications of each approach',
      '⚖️ Complete the mandatory Shadow Board Audit — your board will review your ESG governance posture before allowing strategy access',
    ],
    metrics: [
      { icon: '🛡️', label: 'Resilience Factor' },
      { icon: '💰', label: 'Potential Damage ($12M)' },
      { icon: '🌿', label: 'NCD Impact' },
    ],
    warning: {
      text: '<strong>🎲 Stochastic Event:</strong> A random dice roll (threshold: 75%) determines if the cyclone strikes. Your resilience factor mitigates damage — Insurance Only (0% mitigation) will <strong>block your R10 resilience bonus</strong>.',
    },
  },

  6: {
    icon: '🤖',
    title: 'AI Bias',
    theme: 'Algorithmic Ethics & Brand Risk',
    stamp: 'ETHICS REVIEW',
    narrative: [
      'An internal audit of {{governance_bu_possessive}} AI-powered recruitment tool has revealed <strong>systematic discrimination</strong> against minority applicants. The algorithm, trained on a decade of historical hiring data, has been rejecting qualified minority candidates at 3× the rate of non-minority applicants. The bias is embedded in the training data itself — reflecting decades of structural inequality that the AI has learned to perpetuate.',
      'The story has reached mainstream media. Civil rights organisations are mobilising class-action lawsuits. {{governance_bu_possessive_cap}} lucrative government contracts — worth $3M annually — are now under formal review. The EU AI Act compliance team is demanding an immediate impact assessment, and the European Data Protection Board has opened a preliminary investigation.',
      'Ironically, the biased algorithm is also commercially valuable. Several Fortune 500 companies have expressed interest in licensing it as a "workforce optimisation tool." Monetising it would generate $5M in immediate revenue for {{governance_bu_ref}} but could trigger a contagion spike {{ai_contagion_scope}} if the story gains further traction.',
      'You face a profound ethical crossroads. A full <strong>Ethical AI Overhaul</strong> costs $8M but builds genuine social capital and unlocks the coveted <em>Truth Premium</em> at Round 10 — a +0.15 bonus to your Regenerative Multiple. A quiet patch costs only $1M but increases governance risk by 10 points. Your choice here will echo through your Year 5 Terminal Valuation and define what kind of company {{company_name}} truly is.',
    ],
    objectives: [
      'Respond to the AI bias scandal in {{governance_bu}}',
      'Weigh the financial temptation of monetisation against reputational risk',
      'Consider the "Truth Premium" — ethical choices unlock R10 bonuses',
      'Manage Social License and Governance Risk {{ai_contagion_scope}}',
    ],
    metrics: [
      { icon: '⭐', label: 'Reputation' },
      { icon: '🤝', label: 'Social License' },
      { icon: '⚖️', label: 'Governance Risk' },
    ],
    warning: {
      text: '<strong>🏆 Truth Premium:</strong> Choosing the Ethical AI Overhaul (Option B) unlocks a <strong>+0.15 bonus</strong> to your Regenerative Multiple at Round 10. This could be the difference between "Fragile Giant" and "De-risked Safe-Haven".',
    },
  },

  7: {
    icon: '♻️',
    title: 'Circularity',
    theme: 'Circular Economy Transition',
    stamp: 'EU REGULATION',
    narrative: [
      'The European Commission has published its <strong>Circular Economy Action Plan</strong> with binding targets: all companies operating in the EU must achieve <em>60% waste diversion</em> by next fiscal year. Non-compliance fines: <strong>$15 million</strong>. This regulation applies across {{regulation_scope_phrase}}, and the deadline is non-negotiable.',
      '{{bu_waste_intro}} distinct circular economy challenges — from hazardous process waste to electronic waste, single-use packaging, and data centre thermal output.',
      'This round introduces the concept of <strong>industrial symbiosis</strong> — the potential for {{symbiosis_scope}} waste-to-resource exchanges. Thermal waste can power cold chain logistics. Organic waste can feed bio-energy systems. Decommissioned hardware contains recoverable rare metals. The question is whether you invest in making these connections real.',
      'A <strong>Waste-to-Energy partnership</strong> — while not the cheapest option — could unlock a critical <em>Synergy Multiplier boost (+0.35)</em> that amplifies your final Terminal Valuation. More importantly, it enables the "Resist & Integrate" option in Round 10, which is only available if your Synergy Score exceeds 80. This is a pivotal strategic fork.',
    ],
    objectives: [
      'Achieve regulatory compliance with EU circular economy mandates',
      'Choose between full circular redesign, producer responsibility, or waste-to-energy',
      'Consider the Synergy Multiplier — it gates your options in Round 10',
      'Manage the balance between NCD reduction and treasury costs',
    ],
    metrics: [
      { icon: '🌿', label: 'NCD Reduction' },
      { icon: '🔄', label: 'Synergy Multiplier' },
      { icon: '⭐', label: 'Reputation' },
    ],
    warning: {
      text: '<strong>🔗 Synergy Gate:</strong> Choosing Waste-to-Energy (Option C) adds <strong>+0.35</strong> to your Synergy Multiplier and <strong>unlocks "Resist & Integrate"</strong> in Round 10. Without sufficient synergy (>80), your best R10 option will be locked.',
    },
  },

  8: {
    icon: '💧',
    title: 'Blue Stress',
    theme: 'Water Scarcity Emergency',
    stamp: 'EMERGENCY',
    narrative: [
      'A multi-year drought has reached critical levels. The primary watershed serving your <strong>{{high_water_buses}}</strong> facilities has been reclassified as "critically stressed" by the national water authority. Reservoir levels are at 18% capacity — the lowest in recorded history. Government water rationing is imminent, and industrial allocations will be cut by 40% within the next period.',
      '{{water_dependency_detail}}',
      'The equity dimension is critical. {{water_equity_sentence}} Their Social License scores will crater by 25 points, and the ripple effects will follow you into the final rounds.',
      'You must decide: invest $12M in water efficiency {{capital_target}} (equitable but expensive), {{water_option_b_phrase}} (cheap but socially devastating), or commit to a $30M desalination mega-project that eliminates water dependency permanently — but at a cost that could strain your treasury to breaking point.',
    ],
    objectives: [
      'Respond to critical water scarcity across your operations',
      'Balance equitable resource allocation against profit maximisation',
      'Manage Water Dependency scores — they affect long-term resilience',
      '{{water_equity_objective}}',
    ],
    metrics: [
      { icon: '💧', label: 'Water Dependency' },
      { icon: '🤝', label: 'Social License' },
      { icon: '🌿', label: 'NCD' },
    ],
    warning: {
      text: '<strong>🚫 Resilience Penalty:</strong> Choosing "{{water_option_b_label}}" (Option B) causes a <strong>-25 Social License drop</strong> {{water_penalty_scope}}, AND <strong>blocks your R10 resilience bonus</strong> (+0.20 on Regenerative Multiple).',
    },
  },

  9: {
    icon: '✊',
    title: 'Just Transition',
    theme: 'Workforce & Community Justice',
    stamp: 'SOCIAL CRISIS',
    narrative: [
      'Your decarbonisation commitments have reached their most painful consequence: <strong>three legacy factories must close</strong>. These fossil-fuel-dependent manufacturing plants — {{factory_closure_description}} — can no longer operate within your carbon budget. Two thousand workers face redundancy. The communities that grew around these factories over decades — schools funded by local taxes, hospitals serving factory families, small businesses in the supply ecosystem — face economic devastation.',
      'Protests are escalating outside your headquarters. Union leaders representing 1,800 floor workers are in emergency talks with your HR team. Media coverage shows tearful workers holding signs reading "Green jobs, not pink slips." A viral video of a 30-year veteran machinist cleaning out her locker has been viewed 4 million times. Your Social License to Operate hangs in the balance.',
      'This is the <em>Just Transition</em> dilemma — one of the defining moral challenges of the sustainability era. How do you pursue environmental goals without leaving behind the people who built your company?<span class="ped-academic"> The International Labour Organization\'s Just Transition guidelines call for decent work, social dialogue, and community reinvestment.</span> But those principles cost money.',
      'Immediate closure saves $5M but risks a catastrophic <strong>worker strike</strong> if your Social License is already weak. A managed transition with retraining costs $12M. A full community investment fund at $20M is the most expensive path but earns the deepest social trust. Your choice will determine whether your workforce becomes an ally or an adversary in the Grand Finale.',
    ],
    objectives: [
      'Manage the closure of 3 legacy factories and 2,000 workforce layoffs',
      'Balance cost savings against social licence and community impact',
      'Consider strike risk — low social licence can trigger a devastating work stoppage',
      'Evaluate the long-term value of community investment vs short-term savings',
    ],
    metrics: [
      { icon: '🤝', label: 'Social License' },
      { icon: '⭐', label: 'Reputation' },
      { icon: '⚖️', label: 'Governance Risk' },
    ],
    warning: {
      text: '<strong>⚠️ Strike Risk:</strong> If you choose Immediate Closure AND your average Social License is below 50, there is a <strong>75% chance of a total strike</strong> — zeroing ALL BU revenue for this round. Managed Transition and Community Fund are safer.',
    },
  },

  10: {
    icon: '🏛️',
    title: 'Grand Finale',
    theme: 'Year 5 Activist Ultimatum & Terminal Valuation',
    stamp: 'FINAL ROUND',
    narrative: [
      '<strong>Five years</strong> have passed. An activist investor consortium — the <em>FutureFirst Alliance</em> — has acquired a blocking stake in {{company_name}}. Led by Dr. Amara Osei, a former climate scientist turned institutional investor, the Alliance tables a formal motion to <strong>{{activist_motion}}</strong> at a special Board meeting.',
      'Dr. Osei\'s argument is compelling: "{{activist_case}}"',
      'As {{cso_title}}, you must now present your recommendation to the Board. Your evidence is the performance data from 9 rounds of strategic crisis management. {{synergy_question}} Or did you paper over structural weaknesses?',
      'This is your final decision. Your <strong>Terminal Valuation</strong> will be calculated as: <em>Terminal EBITDA × Exit Multiple (12×) × Regenerative Multiple (M_R)</em>. The Regenerative Multiple captures every strategic choice you\'ve made — synergy investments, climate resilience, ethical AI decisions, social license preservation. It determines whether {{company_name}} is remembered as a <strong>Regenerative Titan</strong>, a <strong>De-risked Safe-Haven</strong>, a <strong>Fragile Giant</strong>, or a <strong>Stranded Relic</strong>.',
    ],
    objectives: [
      'Respond to the activist ultimatum: Resist, Spin-off, or Divest',
      'This round determines your Year 5 Profile Archetype and Terminal Valuation',
      'Draft a Decade Forward Plan justifying your recommendation to the Board',
      'Your Regenerative Multiple (M_R) reflects the cumulative impact of all prior decisions',
    ],
    metrics: [
      { icon: '📈', label: 'Terminal Valuation' },
      { icon: '🔄', label: 'Synergy Score' },
      { icon: '🏅', label: 'Regenerative Multiple' },
    ],
    warning: {
      text: '<strong>🔒 Decision Gates:</strong> "Resist & Integrate" requires Synergy Score > 80 (unlocked by R7-C). Your M_R includes: <strong>CSRD Governance Premium (+0.10 from R2A)</strong>, Synergy Bonus (+0.30), Resilience Bonus (+0.20 if R5/R8 not bailed out), Truth Premium (+0.15 from R6-B), and Instability Discount (-0.40 if avg. Social License < 75).',
    },
  },
};
