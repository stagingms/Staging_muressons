/**
 * ═══════════════════════════════════════════════════════════════
 *  HEALTHCARE BRIEFINGS — 10 Rounds
 *
 *  Healthcare BU names (Hospitals, Clinics, Specialised Care,
 *  Telehealth) are stable within healthcare mode and are NOT
 *  subject to vertical substitution, so these briefings contain
 *  no {{tokens}} — they are returned as-is by resolveBriefing().
 *
 *  Extracted verbatim from the original RoundBriefing.js.
 * ═══════════════════════════════════════════════════════════════
 */

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
      'Your choice directly impacts your final Regenerative Multiple in Year 5. A system that cannot withstand the weather cannot be called sustainable.',
    ],
    objectives: [
      'Prepare clinical infrastructure for a devastating extreme weather event',
      'Choose your posture: Insurance, Evacuation, or Hardened Infrastructure',
      'Understand how resilience mitigating protects your balance sheet',
      '⚖️ Complete the mandatory Shadow Board Audit — your board will review your ESG governance posture before allowing strategy access',
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
      '<strong>Five years</strong> of relentless crisis management culminate today. A dominant, health-focused activist investor consortium—the <em>FutureFirst Alliance</em>—has acquired a controlling stake in Muressons Healthcare.',
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
