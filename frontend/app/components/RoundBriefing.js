'use client';

import styles from './RoundBriefing.module.css';

/**
 * ═══════════════════════════════════════════════════════════════
 *  ROUND BRIEFING DATA — All 10 Rounds
 *  Each entry contains narrative text, objectives, key metrics,
 *  and optional warnings that carry forward from prior decisions.
 * ═══════════════════════════════════════════════════════════════
 */
export const BRIEFINGS = {
  1: {
    icon: '📋',
    title: 'Foundations',
    theme: 'ESG Baseline Assessment',
    stamp: 'PRIORITY: HIGH',
    narrative: [
      'The Board of Directors has convened an emergency session. Global regulators are tightening ESG disclosure requirements, and <strong>Muressons Global</strong> — a diversified conglomerate spanning Pharmaceuticals, Electronics, Consumer Goods, and Software — has never conducted a comprehensive ESG materiality assessment.',
      'As the newly appointed <em>Chief Sustainability Officer</em>, your first mandate is clear: determine the depth and scope of an initial ESG audit across all four business units. The audit results will shape every strategic decision you make for the next decade.',
      'Your conglomerate is a complex beast. <strong>Muressons Pharma</strong> generates $18M in revenue with high water dependency. <strong>Electronics</strong> pulls in $16.5M but carries the highest carbon intensity at 72 units. <strong>Consumer Goods</strong> is the steady middle child at $10.5M, and <strong>Software</strong> — the leanest unit at $8.5M — has the lowest environmental footprint but the highest governance sensitivity.',
      'Before making your audit decision, you must also complete the <strong>Stakeholder Power/Interest Grid</strong> (Mendelow\'s Matrix) to map the political landscape. Understanding who holds power over your ESG agenda — regulators, investors, employees, communities — is essential groundwork for every crisis ahead.',
      'Choose carefully. A superficial scan may save money now, but <strong>blind spots in the Electronics supply chain</strong> could come back to haunt you when scrutiny intensifies in later rounds. The consequences of this first decision cascade forward through all ten rounds.',
    ],
    objectives: [
      'Decide audit depth: Surface scan, deep forensic audit, or phased rollout',
      'Balance upfront cost against long-term risk visibility',
      'Complete the Stakeholder Power/Interest Grid (Mendelow\'s Matrix)',
      'Set your initial capital allocation strategy across all 4 BUs',
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
      'The CFO has imposed a new investment governance framework: the <strong>Double Materiality Matrix</strong>. Every capital allocation must now demonstrate alignment with both <em>high financial impact</em> and <em>high ESG impact</em> criteria. This aligns with the EU\'s Corporate Sustainability Reporting Directive (CSRD), which requires companies to assess and report on both how sustainability issues affect the business (financial materiality) and how the business affects society and the environment (impact materiality).',
      'This is not optional. Proposals that fall outside the top-right quadrant of the materiality matrix will be <strong>rejected by the CFO</strong> unless you invoke an executive override — at the cost of your reputation. The CFO has made clear: "Every dollar we invest must serve both our shareholders and our stakeholders. If it doesn\'t pass the double materiality test, it doesn\'t get funded."',
      'You must complete the CSRD Materiality Assessment before making any strategic decisions this round. You will map each business unit\'s initiatives onto a 2×2 matrix of Financial Impact vs ESG Impact. Only initiatives landing in <strong>Quadrant 1 (High/High)</strong> will receive automatic approval. Everything else requires justification or override.',
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
    warning: null,
  },

  3: {
    icon: '🏭',
    title: 'Scope 3 Emissions',
    theme: 'Supply Chain Decarbonisation',
    stamp: 'REGULATORY SIGNAL',
    narrative: [
      'Breaking news from Brussels: <strong>mandatory Scope 3 disclosure</strong> is now on the regulatory horizon. The International Sustainability Standards Board (ISSB) has finalised standards requiring full value-chain emissions reporting. Preliminary analysis shows that your supply chain carbon footprint is <em>four times</em> your direct emissions — and investors are watching.',
      'Your supply chain spans raw material extraction in Southeast Asia, chip fabrication in Taiwan, pharmaceutical ingredients from India, and consumer goods manufacturing across three continents. Each link in this chain carries embedded carbon that will soon appear on your balance sheet. The Electronics division alone accounts for 40% of your total Scope 3 footprint, driven by energy-intensive semiconductor fabrication and rare earth mineral extraction.',
      'The financial stakes are real. Scope 3 emissions will eventually feed into your <strong>Natural Capital Debt (NCD)</strong> — a running tally of your environmental liability that compounds over rounds and directly affects your Year 3 Terminal Valuation. Ignoring it now means paying more later.',
      'The clock is ticking. You can switch suppliers immediately (fast but disruptive, with risk of operational downtime in Electronics and Pharma), issue a green bond for gradual transition (moderate cost, lower NCD), or buy carbon offsets and defer the hard decisions. Each path has very different consequences for your carbon intensity trajectory and treasury.',
    ],
    objectives: [
      'Address Scope 3 emissions exposure across the supply chain',
      'Choose between rapid disruption, structured transition, or deferral',
      'Manage Natural Capital Debt — it accumulates across rounds',
      'Consider how supply chain disruption might affect Electronics and Pharma',
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
      'A whistleblower exposé has gone viral: <strong>child labour allegations</strong> in your Electronics supply chain. An investigative journalist has published footage from a tier-2 supplier facility in Southeast Asia showing underage workers assembling circuit boards. The story was broken by a major news outlet and is trending globally within hours. Hashtags calling for a Muressons boycott are dominating social media.',
      'The <em>Contagion Engine</em> is now active. This is not just an Electronics problem — reputational damage will propagate across <strong>all your business units</strong>. Pharma customers are questioning whether your drug manufacturing follows the same ethical shortcuts. Software enterprise clients are reviewing their vendor ethics clauses. Consumer Goods is facing organised boycott campaigns at major retailers.',
      'The base crisis severity is <strong>40 points</strong>, but if you failed to conduct a deep audit in Round 1, the Electronics blind spot means this crisis hits at <strong>80 points</strong> — double the impact. The forensic audit you could have done would have caught these supplier issues before they became front-page news.',
      'Your response will define whether this crisis becomes a defining moment of transparency — earning long-term stakeholder trust — or the beginning of a death spiral. Full remediation costs $6M but repairs reputation. PR containment is cheaper but does not fix the root cause. Denial risks catastrophic long-term consequences. The board is watching. The market is watching. The world is watching.',
    ],
    objectives: [
      'Respond to the Electronics supply chain scandal',
      'Manage cross-BU reputational contagion',
      'Choose between transparency, PR containment, or denial',
      'Protect Social License to Operate across all business units',
    ],
    metrics: [
      { icon: '⭐', label: 'Reputation' },
      { icon: '🤝', label: 'Social License' },
      { icon: '📊', label: 'Contagion Spread' },
    ],
    warning: {
      text: '<strong>⚡ Blindspot Check:</strong> If you chose a Surface-Level Scan or Phased Audit in Round 1, the Electronics blind spot is active — <strong>crisis severity is DOUBLED</strong> (40 → 80). A Deep Forensic Audit would have protected you.',
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
      'The implications extend beyond this round. Your resilience strategy here feeds into your <strong>Year 3 Regenerative Multiple</strong>. Choosing the insurance-only path signals to investors that you are not building genuine climate resilience — and it will block a critical +0.20 bonus in your final valuation.',
    ],
    objectives: [
      'Prepare for a physical climate event with real financial consequences',
      'Choose your resilience strategy: Hard engineering, nature-based, or insurance',
      'Understand the trade-off between upfront cost and damage mitigation',
      'Consider the Natural Capital Debt implications of each approach',
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
      'An internal audit of your Software BU\'s AI-powered recruitment tool has revealed <strong>systematic discrimination</strong> against minority applicants. The algorithm, trained on a decade of historical hiring data, has been rejecting qualified minority candidates at 3× the rate of non-minority applicants. The bias is embedded in the training data itself — reflecting decades of structural inequality that the AI has learned to perpetuate.',
      'The story has reached mainstream media. Civil rights organisations are mobilising class-action lawsuits. Your Software BU\'s lucrative government contracts — worth $3M annually — are now under formal review. The EU AI Act compliance team is demanding an immediate impact assessment, and the European Data Protection Board has opened a preliminary investigation.',
      'Ironically, the biased algorithm is also commercially valuable. Several Fortune 500 companies have expressed interest in licensing it as a "workforce optimisation tool." Monetising it would generate $5M in immediate revenue for the Software division but could trigger a contagion spike across all BUs if the story gains further traction.',
      'You face a profound ethical crossroads. A full <strong>Ethical AI Overhaul</strong> costs $8M but builds genuine social capital and unlocks the coveted <em>Truth Premium</em> at Round 10 — a +0.15 bonus to your Regenerative Multiple. A quiet patch costs only $1M but increases governance risk by 10 points. Your choice here will echo through your Year 3 Terminal Valuation and define what kind of company Muressons truly is.',
    ],
    objectives: [
      'Respond to the AI bias scandal in Software BU',
      'Weigh the financial temptation of monetisation against reputational risk',
      'Consider the "Truth Premium" — ethical choices unlock R10 bonuses',
      'Manage Social License and Governance Risk across all BUs',
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
      'The European Commission has published its <strong>Circular Economy Action Plan</strong> with binding targets: all companies operating in the EU must achieve <em>60% waste diversion</em> by next fiscal year. Non-compliance fines: <strong>$15 million</strong>. This regulation applies across all four of your business units, and the deadline is non-negotiable.',
      'Your four business units generate waste streams of varying complexity. Pharma faces hazardous pharmaceutical waste requiring specialised treatment. Electronics confronts the growing mountain of e-waste and rare earth recovery challenges. Consumer Goods must tackle single-use packaging across its product lines. And Software\'s expanding data centre operations generate significant electronic waste and thermal output.',
      'This round introduces the concept of <strong>industrial symbiosis</strong> — the potential for cross-BU waste-to-resource exchanges. Electronics\' thermal waste could power Pharma\'s cold chain logistics. Consumer Goods\' organic waste could feed bio-energy systems. Software\'s decommissioned servers contain recoverable rare metals for Electronics. The question is whether you invest in making these connections real.',
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
      'A multi-year drought has reached critical levels. The primary watershed serving your <strong>Pharma and Electronics</strong> facilities has been reclassified as "critically stressed" by the national water authority. Reservoir levels are at 18% capacity — the lowest in recorded history. Government water rationing is imminent, and industrial allocations will be cut by 40% within the next quarter.',
      'Water is the invisible dependency of modern industry, and your exposure is severe. <strong>Pharma</strong> has the highest water dependency score (82) — ultra-pure water is essential for drug formulation and sterile manufacturing. <strong>Electronics</strong> (58) requires massive volumes for semiconductor wafer fabrication and cooling systems. <strong>Consumer Goods</strong> (65) depends on water for food and beverage processing lines. Only <strong>Software</strong> (12) has minimal direct water exposure.',
      'The equity dimension is critical. If you prioritise water allocation to your highest-margin division (Electronics), you are essentially sacrificing Pharma and Consumer Goods — communities and workers who depend on those facilities will face devastating layoffs. Their Social License scores will crater by 25 points, and the ripple effects will follow you into the final rounds.',
      'You must decide: invest $12M in water efficiency across all BUs (equitable but expensive), divert resources to Electronics at $4M (cheap but socially devastating), or commit to a $30M desalination mega-project that eliminates water dependency permanently — but at a cost that could strain your treasury to breaking point.',
    ],
    objectives: [
      'Respond to critical water scarcity across your operations',
      'Balance equitable resource allocation against profit maximisation',
      'Manage Water Dependency scores — they affect long-term resilience',
      'Be aware that prioritising one BU devastates others\' Social License',
    ],
    metrics: [
      { icon: '💧', label: 'Water Dependency' },
      { icon: '🤝', label: 'Social License' },
      { icon: '🌿', label: 'NCD' },
    ],
    warning: {
      text: '<strong>🚫 Resilience Penalty:</strong> Choosing "Prioritise Electronics" (Option B) causes a <strong>-25 Social License drop</strong> on Pharma and Consumer Goods, AND <strong>blocks your R10 resilience bonus</strong> (+0.20 on Regenerative Multiple).',
    },
  },

  9: {
    icon: '✊',
    title: 'Just Transition',
    theme: 'Workforce & Community Justice',
    stamp: 'SOCIAL CRISIS',
    narrative: [
      'Your decarbonisation commitments have reached their most painful consequence: <strong>three legacy factories must close</strong>. These coal-dependent manufacturing plants — two in the Consumer Goods division and one in Electronics — can no longer operate within your carbon budget. Two thousand workers face redundancy. The communities that grew around these factories over decades — schools funded by local taxes, hospitals serving factory families, small businesses in the supply ecosystem — face economic devastation.',
      'Protests are escalating outside your headquarters. Union leaders representing 1,800 floor workers are in emergency talks with your HR team. Media coverage shows tearful workers holding signs reading "Green jobs, not pink slips." A viral video of a 30-year veteran machinist cleaning out her locker has been viewed 4 million times. Your Social License to Operate hangs in the balance.',
      'This is the <em>Just Transition</em> dilemma — one of the defining moral challenges of the sustainability era. How do you pursue environmental goals without leaving behind the people who built your company? The International Labour Organization\'s Just Transition guidelines call for decent work, social dialogue, and community reinvestment. But those principles cost money.',
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
    theme: 'Year 3 Activist Ultimatum & Terminal Valuation',
    stamp: 'FINAL ROUND',
    narrative: [
      '<strong>Three years</strong> have passed. An activist investor consortium — the <em>FutureFirst Alliance</em> — has acquired a blocking stake in Muressons Global. Led by Dr. Amara Osei, a former climate scientist turned institutional investor, the Alliance tables a formal motion to <strong>dissolve the conglomerate structure</strong> at a special Board meeting.',
      'Dr. Osei\'s argument is compelling: "Your four business units — Pharmaceuticals, Electronics, Software, and Consumer Goods — are too fundamentally different to be managed sustainably under one roof. Cross-subsidisation of high-carbon assets by green divisions is a form of corporate greenwashing. Each unit deserves its own sustainability mandate, its own carbon budget, and its own accountability structure."',
      'As Chief Sustainability Officer, you must now present your recommendation to the Board. Your evidence is the performance data from 9 rounds of strategic crisis management. Did you build genuine cross-BU synergies that justify the conglomerate? Or did you paper over structural weaknesses?',
      'This is your final decision. Your <strong>Terminal Valuation</strong> will be calculated as: <em>Terminal EBITDA × Exit Multiple (12×) × Regenerative Multiple (M_R)</em>. The Regenerative Multiple captures every strategic choice you\'ve made — synergy investments, climate resilience, ethical AI decisions, social license preservation. It determines whether Muressons is remembered as a <strong>Regenerative Titan</strong>, a <strong>De-risked Safe-Haven</strong>, a <strong>Fragile Giant</strong>, or a <strong>Stranded Relic</strong>.',
    ],
    objectives: [
      'Respond to the activist ultimatum: Resist, Spin-off, or Divest',
      'This round determines your Year 3 Profile Archetype and Terminal Valuation',
      'Draft a Decade Forward Plan justifying your recommendation to the Board',
      'Your Regenerative Multiple (M_R) reflects the cumulative impact of all prior decisions',
    ],
    metrics: [
      { icon: '📈', label: 'Terminal Valuation' },
      { icon: '🔄', label: 'Synergy Score' },
      { icon: '🏅', label: 'Regenerative Multiple' },
    ],
    warning: {
      text: '<strong>🔒 Decision Gates:</strong> "Resist & Integrate" requires Synergy Score > 80 (unlocked by R7-C). Your M_R includes: Synergy Bonus (+0.30), Resilience Bonus (+0.20 if R5/R8 not bailed out), Truth Premium (+0.15 from R6-B), and Instability Discount (-0.40 if avg. Social License < 75).',
    },
  },
};

export const HEALTHCARE_BRIEFINGS = {
  1: {
    icon: '📋',
    title: 'Foundations',
    theme: 'Compliance Baseline',
    stamp: 'PRIORITY: HIGH',
    narrative: [
      'The Board of Directors has convened an emergency session. Global health regulators have highlighted severe disparities in our compliance and operations protocols across the <strong>Muressons Healthcare Network</strong>, a sprawling system encompassing tertiary Hospitals, Primary Care Clinics, Specialised Oncology Care, and an emerging Digital Health (Telehealth) matrix.',
      'As the newly appointed <em>Chief Sustainability Officer</em> for the Healthcare group, your first mandate is to secure the foundation of our clinical expansion. The audit results surrounding our medical waste protocols and infrastructure expansion will set the trajectory of our care outcomes and risk exposure for the next decade.',
      'Your network balances immense pressure. <strong>Hospitals</strong> represent your core revenue engine at $22M but have massive water dependencies and energy loads. <strong>Clinics</strong> and <strong>Specialised Care</strong> run tight margins, while <strong>Telehealth</strong> is an asset-light but high-risk software entity with deep governance exposure.',
      'Choose your strategic posture carefully. A rapid expansion to meet patient demand may boost short-term revenue, but <strong>blind spots in clinical waste compliance</strong> could come back to haunt you when scrutiny intensifies in later rounds. Every decision cascades forward through all ten rounds.',
    ],
    objectives: [
      'Decide your expansion versus compliance posture',
      'Balance immediate patient access (revenue) against long-term risk visibility',
      'Complete the Stakeholder Power/Interest Grid to map the political landscape',
      'Set your initial capital allocation strategy across all 4 Healthcare BUs',
    ],
    metrics: [
      { icon: '💰', label: 'Treasury' },
      { icon: '⭐', label: 'Reputation' },
      { icon: '🏥', label: 'Patient Outcomes' },
    ],
    warning: null,
  },

  2: {
    icon: '📊',
    title: 'Double Materiality',
    theme: 'Capital Allocation',
    stamp: 'CFO GATE ACTIVE',
    narrative: [
      'Patient inflow across Europe and the Americas is surging. The CFO has imposed a strict capital governance framework: the <strong>Double Materiality Matrix</strong>. Every allocation must now strictly demonstrate alignment with both <em>high financial resilience</em> and <em>high community impact</em> criteria to navigate incoming ESG reporting directives.',
      'You sit at a strategic crossroads. Do you pour massive Capex into heavy ICU infrastructure (bed capacity) to meet peak demand? Or do you shift your investments toward digital health triage to structurally lower the cost-of-care, running the risk of misdiagnosis on untested platforms?',
      'You must complete the Materiality Assessment before proceeding. Only initiatives landing in <strong>Quadrant 1 (High/High)</strong> will receive automatic approval. Everything else requires justification or a reputation-damaging executive override.',
      'Your choices this round determine your structural capacity to absorb patient surges and your baseline natural capital footprint.',
    ],
    objectives: [
      'Complete and submit the Double Materiality Assessment from a healthcare perspective',
      'Allocate budget to balance physical infrastructure vs. digital transformation',
      'Manage Governance Risk when requesting non-standard budget overrides',
    ],
    metrics: [
      { icon: '⭐', label: 'Reputation' },
      { icon: '🛏️', label: 'Bed Capacity' },
      { icon: '⚖️', label: 'Governance Risk' },
    ],
    warning: null,
  },

  3: {
    icon: '📦',
    title: 'Supply Chain Fragility',
    theme: 'Scope 3 Crisis & Shortages',
    stamp: 'CRISIS ALERT',
    narrative: [
      'A catastrophic logistical disruption in Southeast Asia has entirely severed our supply of single-use surgical plastics, sterile gowns, and essential disposable PPE. Your operating theatres in the Hospitals and Specialised Care units are now facing an existential operating constraint within 48 hours.',
      'The healthcare sector is heavily reliant on a brittle, globalised Scope 3 supply chain. Air-freighting emergency supplies will generate a massive carbon spike and drain the treasury. Rationing care by cancelling elective surgeries will protect your balance sheet but severely damage your reputation as a reliable care provider.',
      'Alternatively, you could fund local sterile manufacturing hubs. This is an extremely expensive venture, but building regional autonomy will permanently reduce your natural capital debt and immunize your system against future shocks.',
      'You must act immediately. Care is on the line.',
    ],
    objectives: [
      'Address the critical shortage of surgical plastics and PPE',
      'Choose between air-freight, rationing care, or building local resilience',
      'Consider the immediate impact on revenue and long-term carbon intensity',
    ],
    metrics: [
      { icon: '🌡️', label: 'Carbon Intensity' },
      { icon: '🧫', label: 'Patient Outcomes' },
      { icon: '💰', label: 'Treasury' },
    ],
    warning: null,
  },

  4: {
    icon: '⚠️',
    title: 'The Blindspot',
    theme: 'Algorithmic Triage Failure',
    stamp: 'CONTAGION ALERT',
    narrative: [
      'An investigative health journal has just published a scathing exposé: your <strong>Telehealth triage algorithm</strong> systematically deprioritized high-risk, lower-income patients, leading directly to a spike in severe clinical adverse events across your primary care network.',
      'The <em>Contagion Engine</em> is accelerating. Public trust in your digital front door has collapsed, and the panic is spilling into the physical hospitals. Patients are demanding manual clinician overrides, creating severe bottlenecks.',
      'If you chose a relaxed compliance posture in Round 1, your lack of deep audit data leaves you exposed to maximum liability, doubling the reputational and financial damage. Do you deny and litigate, pull the algorithm offline for an expensive overhaul, or revert entirely to human clinicians (triggering massive staff burnout)?',
    ],
    objectives: [
      'Contain the digital health malpractice scandal',
      'Manage cross-BU reputational contagion and restore patient trust',
      'Monitor staff burnout indices—reverting to manual triage will overwhelm your clinicians',
    ],
    metrics: [
      { icon: '⭐', label: 'Reputation' },
      { icon: '🩺', label: 'Burnout Index' },
      { icon: '📊', label: 'Contagion Spread' },
    ],
    warning: {
      text: '<strong>⚡ Blindspot Check:</strong> If you prioritized rapid expansion over compliance in Round 1, the crisis severity is DOUBLED.',
    },
  },

  5: {
    icon: '🌪️',
    title: 'Climate Stress Test',
    theme: 'Infrastructure Resilience',
    stamp: 'STOCHASTIC EVENT',
    narrative: [
      'A Category 4 cyclone is currently on a trajectory to strike the coastal corridor housing your densest network of Hospitals and Specialised Care centers. Base projected damage to infrastructure is estimated at $18 million.',
      'This is a <strong>stochastic dice roll</strong>. You cannot prevent the storm, but your choice of resilience posture will dictate the outcome if it makes landfall. You can rely purely on insurance, execute pre-emptive patient evacuations (saving lives but incurring operational chaos), or invest heavily in hardened microgrids to keep the power on through the worst of the disaster.',
      'Your choice directly impacts your final Regenerative Multiple in Year 3. A system that cannot withstand the weather cannot be called sustainable.',
    ],
    objectives: [
      'Prepare clinical infrastructure for a devastating extreme weather event',
      'Choose your posture: Insurance, Evacuation, or Hardened Infrastructure',
      'Understand how resilience mitigating protects your balance sheet',
    ],
    metrics: [
      { icon: '🛡️', label: 'Resilience Factor' },
      { icon: '🏥', label: 'Damage Exposure ($18M)' },
      { icon: '⭐', label: 'Reputation' },
    ],
    warning: {
      text: '<strong>🎲 Stochastic Event:</strong> A random dice roll (75%) determines if the cyclone strikes. Pure reliance on insurance provides 0% physical mitigation.',
    },
  },

  6: {
    icon: '🤖',
    title: 'Digital Transformation',
    theme: 'AI Ethics in Oncology',
    stamp: 'ETHICS REVIEW',
    narrative: [
      'Specialised Care has flagged a disturbing pattern: your premier predictive diagnostic AI in Oncology is generating a 22% false-negative rate for minority patients. The structural bias embedded in historical clinical trial data has been codified into the machine.',
      'You are faced with a profound ethical dilemma. You can quietly patch the weights over 6 months to avoid a market panic and protect the stock price. You can fire the software vendor and start over. Or, you can pursue a Transparent AI Overhaul—halting the system, risking short term governance spikes, but publicly collaborating with ethical boards to fix it properly.',
      'A transparent response builds genuine social capital and unlocks the coveted <em>Truth Premium</em> at Round 10. Can you convince the board to take the short-term financial hit for long-term trust?',
    ],
    objectives: [
      'Resolve the oncology diagnostic bias before it causes mass clinical failure',
      'Choose between a quiet patch, vendor replacement, or transparent overhaul',
      'Consider the Truth Premium — ethical transparency unlocks R10 valuation bonuses',
    ],
    metrics: [
      { icon: '⭐', label: 'Reputation' },
      { icon: '🤝', label: 'Social License' },
      { icon: '⚖️', label: 'Governance Risk' },
    ],
    warning: {
      text: '<strong>🏆 Truth Premium:</strong> Choosing the Transparent AI Overhaul unlocks a <strong>+0.15 bonus</strong> to your Regenerative Multiple at Round 10.',
    },
  },

  7: {
    icon: '♻️',
    title: 'Resource Circularity',
    theme: 'Waste Innovation',
    stamp: 'EU REGULATION',
    narrative: [
      'The "Sterile Waste Mountain" has reached a tipping point. Environmental regulators are proposing a punitive, recurring tax on clinical incinerators. Your Hospitals and Clinics represent the largest non-industrial polluters in three states.',
      'You could fund a lobbying campaign to fight the tax—a tactic that protects cash flow but generates immense Natural Capital Debt and destroys community trust. You could simply absorb the tax as an OPEX penalty and carry on.',
      'Or, you can fund <strong>Circular Instrument Hubs</strong>—a radical operational redesign to autoclave and remanufacture complex surgical tools at scale. This initiative will unlock massive cross-BU synergies, allowing regional Clinics to share resources with core Hospitals, drastically reducing your NCD long-term.',
    ],
    objectives: [
      'Navigate the impending punitive tax on clinical waste incineration',
      'Decide between lobbying, absorbing the tax, or innovating a circular solution',
      'Investigate the Synergy Multiplier—it gates your options in the final year',
    ],
    metrics: [
      { icon: '🌿', label: 'NCD Reduction' },
      { icon: '🔄', label: 'Synergy Multiplier' },
      { icon: '💰', label: 'OPEX Load' },
    ],
    warning: {
      text: '<strong>🔗 Synergy Gate:</strong> Circular Hubs will unlock a Synergy Bonus (+0.15), keeping you on track to access the best finale options.',
    },
  },

  8: {
    icon: '💧',
    title: 'Blue Stress',
    theme: 'Water Security',
    stamp: 'EMERGENCY',
    narrative: [
      'A multi-year drought has broken the municipal water system. The city has decreed mandatory shut-offs. Hospitals require staggering amounts of water—not just for sanitation, but to run central HVAC cooling, sterilizers, and diagnostic imaging machinery. Without water, modern healthcare collapses in hours.',
      'You are out of time. You can pay exorbitant surge pricing to tanker in private water from out of state just to keep the Operating Rooms open. You can invoke your legal standing as "critical infrastructure" to force the city to cut residential water in your favor—sacrificing community goodwill to save lives.',
      'Or, if your treasury allows, you can expedite retrofitting the hospitals with closed-loop greywater reclamation. It is devastatingly expensive, but permanently shields your physical assets from future droughts.',
    ],
    objectives: [
      'Avert total clinical collapse due to municipal water shortages',
      'Balance extreme operational costs against devastating social and reputational fallout',
      'Mitigate your long term Natural Capital Debt through bold infrastructural retrofits',
    ],
    metrics: [
      { icon: '💧', label: 'System Uptime' },
      { icon: '🤝', label: 'Social License' },
      { icon: '💰', label: 'Treasury Burn' },
    ],
    warning: null,
  },

  9: {
    icon: '✊',
    title: 'Just Transition',
    theme: 'Workforce Automation',
    stamp: 'SOCIAL CRISIS',
    narrative: [
      'Your aggressive push towards cost-efficiency and Telehealth has consequences. Following a massive robotic-pharmacy deployment and algorithmic triage rollout, the nursing and clinician unions have announced an impending total strike across the primary care network to protest structural job insecurity.',
      'Clinical burnout is at an all-time high. Staff are exhausted. You can attempt to bust the strike by hiring incredibly expensive, low-loyalty agency locums. You can halt the automation entirely, capitulating to the union and wasting millions in R&D.',
      'Or, you can fund a comprehensive Clinician Retraining Hub—elevating nurses into high-tech triage oversight and advanced practitioner roles. It is the most expensive path forward, but it is the only way to heal the deep burnout festering in your workforce before the finale.',
    ],
    objectives: [
      'Prevent a catastrophic nursing strike that would cripple patient outcomes',
      'Address the systemic Staff Burnout Index affecting your OPEX efficiency',
      'Negotiate the delicate transition between human-led care and digital amplification',
    ],
    metrics: [
      { icon: '🩺', label: 'Burnout Index' },
      { icon: '🤝', label: 'Social License' },
      { icon: '⭐', label: 'Reputation' },
    ],
    warning: null,
  },

  10: {
    icon: '🏛️',
    title: 'Grand Finale',
    theme: 'Terminal Valuation & Outcome Legacy',
    stamp: 'FINAL ROUND',
    narrative: [
      '<strong>Three years</strong> of relentless crisis management culminate today. A dominant, health-focused activist investor consortium—the <em>FutureFirst Alliance</em>—has acquired a controlling stake in Muressons Healthcare.',
      'The board requires a definitive choice on our final market posture before going public with a sweeping reorganization. The activists argue that a pure-profit driven consolidation destroys patient outcomes. Your track record of ESG alignment, resilience, and clinical burnout management will be tested.',
      'As Chief Sustainability Officer, you must recommend the terminal trajectory. Do you execute aggressive financial consolidation to pad EBITDA? Do you divest the weakest primary-care clinics to artificially boost group margins? Or do you encode a Universal Care Mandate into the corporate charter, protecting your long-term valuation multiples?',
      'Your <strong>Terminal Valuation</strong> will be judged by your Regenerative Multiple (M_R), tracking synergy, reputation, and clinical excellence. What kind of health system have you built? A <strong>Regenerative Titan</strong> or a <strong>Fragile Giant</strong>?',
    ],
    objectives: [
      'Make the final strategic boardroom decision: Consolidate, Divest, or Charter',
      'Finalize your Terminal Valuation and ESG Archetype',
      'Reflect on the compounding effects of 9 rounds of systemic healthcare management',
    ],
    metrics: [
      { icon: '📈', label: 'Terminal Valuation' },
      { icon: '🏥', label: 'Systemic Health Score' },
      { icon: '🏅', label: 'Regenerative Multiple' },
    ],
    warning: {
      text: '<strong>🔒 Last Stand:</strong> Your final Regenerative Multiple factors in your Synergies, Truth Premium, and punishes deep cuts to community and staff social licenses. The Universal Care Mandate protects long-term value over short-term cash.',
    },
  },
};

/**
 * ═══════════════════════════════════════════════════════════════
 *  SDG EDITION BRIEFINGS — All 10 Rounds
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

/**
 * RoundBriefing — Pre-round briefing document overlay.
 *
 * Props:
 *  - roundNumber: 1–10
 *  - isHealthcare: boolean - Flag indicating whether to use Healthcare narratives
 *  - isSDG: boolean - Flag indicating whether to use UN SDG narratives
 *  - onProceed: () => void — dismisses briefing, enters cockpit
 */
export default function RoundBriefing({ roundNumber, isHealthcare, isSDG, onProceed }) {
  const dictionary = isSDG ? SDG_BRIEFINGS : isHealthcare ? HEALTHCARE_BRIEFINGS : BRIEFINGS;
  const b = dictionary[roundNumber];
  if (!b) return null;

  return (
    <div className={styles.overlay}>
      <div className={styles.container}>
        {/* ── Header ── */}
        <header className={styles.header}>
          <div className={styles.roundBadge}>ROUND {roundNumber} OF 10</div>
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
            <span className={styles.stamp}>{b.stamp}</span>
          </div>

          {/* Narrative */}
          <div className={styles.narrative}>
            {b.narrative.map((para, i) => (
              <p key={i} dangerouslySetInnerHTML={{ __html: para }} />
            ))}
          </div>

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
                dangerouslySetInnerHTML={{ __html: b.warning.text }}
              />
            </div>
          )}
        </div>

        {/* ── Proceed Button ── */}
        <div className={styles.footer}>
          <button className={styles.proceedBtn} onClick={onProceed}>
            Begin Simulation →
          </button>
        </div>
      </div>
    </div>
  );
}
