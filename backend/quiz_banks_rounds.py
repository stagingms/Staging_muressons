"""quiz_banks_rounds.py — per-round knowledge-check notebooks (rounds 2,4,6-10).

Companion to quiz_banks.py (which supplies NLM_001/002/003 for rounds 1/3/5).
These fill the remaining rounds so a facilitator who turns on the MANDATORY quiz
gate has a topically-aligned quiz on every round. Each entry mirrors the
NotebookLMItem shape consumed by admin_resources._notebooklm_notebooks:
    {id, title, description, content_types, target_round, category,
     review_content, quiz_questions:[{question, options, correct, explanation, difficulty}]}

Question banks carry ≥10 items spanning easy/medium/hard so
GET /api/simulations/quiz/{id} can serve a full 10-question quiz at any
facilitator difficulty setting (it supplements across levels when short).
"""

# ═══════════════════════════════════════════════════════════════════════════
#  ROUND 2 — Double Materiality Gate
# ═══════════════════════════════════════════════════════════════════════════
R2_REVIEW = """## Double Materiality — CSRD & ESRS Deep Dive

The EU **Corporate Sustainability Reporting Directive (CSRD)** and its
**European Sustainability Reporting Standards (ESRS)** require *double
materiality*: a topic is material if it is financially material (affects
enterprise value) **or** impact material (the company affects people/planet) —
or both. Passing **either** test triggers a disclosure obligation.

Key mechanics you use in Round 2:
- **Severity × Likelihood** scoring on each axis. ESRS 1 frames impact severity
  as *scale × scope × irremediability*.
- **Quadrant 1 (doubly material)** issues drive capital allocation.
- **Quadrant 2 (high impact / low financial)** issues are NOT capex-intensive
  but still demand *disclosure investment* (data, assurance, engagement).
- A **stakeholder panel** improves classification accuracy but costs budget.
- **Limited vs reasonable assurance** (ISAE 3000 / ISSA 5000) depends on process
  quality — board oversight, recall, and disclosure, not just the answer.
"""
R2_QUESTIONS = [
    {"question": "Under CSRD, a topic is 'material' if it passes which test(s)?", "options": ["Financial materiality only", "Impact materiality only", "Financial OR impact materiality", "Financial AND impact materiality"], "correct": 2, "explanation": "Double materiality means EITHER financial OR impact materiality triggers a disclosure obligation.", "difficulty": "easy"},
    {"question": "What does the 'impact' dimension of double materiality assess?", "options": ["How ESG issues affect company value", "How the company affects people and the environment", "How competitors are performing", "How share price moves"], "correct": 1, "explanation": "Impact materiality is outward-facing: the company's effect on society and the environment.", "difficulty": "easy"},
    {"question": "Which EU standard set operationalises CSRD reporting?", "options": ["GRI", "ESRS", "SASB", "IFRS 9"], "correct": 1, "explanation": "The European Sustainability Reporting Standards (ESRS) are the detailed rules under CSRD.", "difficulty": "easy"},
    {"question": "A 'doubly material' issue is one that is…", "options": ["Only financially material", "Only impact material", "Both financially and impact material", "Neither, but reported anyway"], "correct": 2, "explanation": "Doubly material = high on BOTH the financial and impact axes (Quadrant 1).", "difficulty": "easy"},
    {"question": "Under ESRS 1, impact severity is assessed by which combination?", "options": ["Scale × Scope × Irremediability", "Probability × Cost", "Revenue × Margin", "Frequency × Duration"], "correct": 0, "explanation": "ESRS 1 defines severity as scale × scope × irremediability of the impact.", "difficulty": "medium"},
    {"question": "A high-impact but low-financial issue (Quadrant 2) primarily requires…", "options": ["Large capital expenditure", "Disclosure investment (data, assurance, engagement)", "Immediate divestment", "No action at all"], "correct": 1, "explanation": "Q2 issues aren't capex-heavy but still demand mandatory disclosure and the investment to support it.", "difficulty": "medium"},
    {"question": "Why might a company commission a stakeholder panel during a materiality assessment?", "options": ["To reduce reporting scope", "To improve classification accuracy of material issues", "To avoid assurance", "To lower its carbon footprint"], "correct": 1, "explanation": "Stakeholder input sharpens which issues are genuinely material — at a survey cost.", "difficulty": "medium"},
    {"question": "Which is a valid reason NOT to place every issue in Quadrant 1?", "options": ["Q1 has a capacity limit", "Placing non-material issues in Q1 misallocates capital and fails the CFO gate", "Q1 issues are ignored", "There is no difference between quadrants"], "correct": 1, "explanation": "Over-stuffing Q1 with non-material issues wastes capital and is rejected under the double-materiality framework.", "difficulty": "medium"},
    {"question": "Limited vs reasonable assurance under CSRD depends most on…", "options": ["The auditor's mood", "Process quality: governance, recall, and disclosure", "The size of the logo", "Share price"], "correct": 1, "explanation": "Assurance readiness reflects process quality — board oversight, issue recall, and disclosure completeness.", "difficulty": "hard"},
    {"question": "A company reports a supplier human-rights risk that barely affects its P&L but severely harms workers. Under double materiality it is…", "options": ["Not material — no financial effect", "Material via the impact axis", "Only material if a lawsuit is filed", "Material only for competitors"], "correct": 1, "explanation": "Severe outward impact makes it material even with negligible financial effect — the essence of double materiality.", "difficulty": "hard"},
    {"question": "Which standard is the ISSB's global-baseline counterpart that CSRD interoperates with?", "options": ["IFRS S1/S2", "Basel III", "COSO", "ISO 9001"], "correct": 0, "explanation": "The ISSB's IFRS S1/S2 form the global baseline; ESRS is designed to interoperate with it.", "difficulty": "hard"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  ROUND 4 — ESG Contagion Crisis
# ═══════════════════════════════════════════════════════════════════════════
R4_REVIEW = """## ESG Contagion & Systemic Reputational Risk

A single ESG failure rarely stays contained. **Contagion** is the cascade of a
localised failure into cross-BU reputational, financial, and regulatory damage.
Watch for:
- **Social licence to operate** erosion — informal community/stakeholder consent
  that, once lost, raises every future cost.
- **Greenwashing risk** — overstated claims that convert a marketing win into a
  regulatory and reputational liability (e.g. under the EU Green Claims regime).
- **Stakeholder cascades** — NGOs, investors, employees, and regulators reacting
  in sequence, each amplifying the last.
- **Systemic / tipping-point risk** — non-linear escalation once a reputational
  threshold is crossed. Early, credible remediation is far cheaper than late
  crisis control.
"""
R4_QUESTIONS = [
    {"question": "What is 'social licence to operate'?", "options": ["A government mining permit", "Informal, ongoing community/stakeholder acceptance of a company", "An ESG rating", "A stock-exchange listing"], "correct": 1, "explanation": "It's the informal, ongoing acceptance by communities and stakeholders — not a legal permit.", "difficulty": "easy"},
    {"question": "'Greenwashing' refers to…", "options": ["Cleaning industrial equipment", "Overstating or misrepresenting environmental credentials", "Painting factories green", "A carbon-offset method"], "correct": 1, "explanation": "Greenwashing is misleading or exaggerated environmental claims.", "difficulty": "easy"},
    {"question": "Contagion risk means a problem in one business unit can…", "options": ["Stay perfectly contained", "Spread reputational and financial damage across the group", "Only affect that unit's manager", "Improve group reputation"], "correct": 1, "explanation": "Contagion is the cross-BU cascade of a localised failure.", "difficulty": "easy"},
    {"question": "Which stakeholder group can most directly divest and move a share price?", "options": ["Local schools", "Institutional investors", "Trade press", "Product users"], "correct": 1, "explanation": "Institutional investors hold the capital to divest and move valuation directly.", "difficulty": "easy"},
    {"question": "Why is early remediation of a reputational issue usually cheaper than late crisis control?", "options": ["Regulators offer discounts", "It avoids the non-linear escalation once a tipping point is crossed", "It is legally mandatory", "It raises the share price automatically"], "correct": 1, "explanation": "Reputational damage escalates non-linearly; acting before the tipping point avoids compounding costs.", "difficulty": "medium"},
    {"question": "The EU Green Claims Directive primarily targets…", "options": ["Carbon taxes", "Substantiation of environmental marketing claims", "Board diversity", "Water pricing"], "correct": 1, "explanation": "It requires companies to substantiate green marketing claims, curbing greenwashing.", "difficulty": "medium"},
    {"question": "A 'stakeholder cascade' describes…", "options": ["A waterfall diagram", "Sequential, amplifying reactions across NGOs, investors, employees, regulators", "A dividend schedule", "A supply-chain map"], "correct": 1, "explanation": "Each stakeholder's reaction amplifies the next, escalating the crisis.", "difficulty": "medium"},
    {"question": "Which action best protects social licence during an ESG controversy?", "options": ["Silence and denial", "Transparent disclosure and credible remediation", "Increasing marketing spend", "Blaming a supplier publicly"], "correct": 1, "explanation": "Transparency and credible remediation rebuild trust; denial deepens erosion.", "difficulty": "medium"},
    {"question": "Why does greenwashing convert a short-term marketing gain into a long-term liability?", "options": ["It has no downside", "Discovery triggers regulatory penalties and trust collapse that outweigh the gain", "It always boosts sales", "It reduces Scope 3 emissions"], "correct": 1, "explanation": "When exposed, penalties and lost trust far exceed the initial marketing benefit.", "difficulty": "hard"},
    {"question": "Systemic reputational risk is characterised by…", "options": ["Linear, predictable losses", "Non-linear escalation past a threshold", "Zero correlation between units", "Guaranteed recovery"], "correct": 1, "explanation": "It escalates non-linearly once a reputational threshold is breached.", "difficulty": "hard"},
    {"question": "An investor-confidence index at 'historic lows' most directly threatens…", "options": ["Employee lunch menus", "Cost of capital and access to financing", "Office decor", "Patent filings"], "correct": 1, "explanation": "Collapsing investor confidence raises the cost of capital and can choke off financing.", "difficulty": "hard"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  ROUND 6 — AI Ethics & Bias
# ═══════════════════════════════════════════════════════════════════════════
R6_REVIEW = """## AI Ethics, Bias & Governance

As Muressons deploys AI across Software and Electronics, **algorithmic
accountability** becomes an ESG issue in its own right — spanning the Social
(bias, rights) and Governance (oversight, transparency) pillars.
- **Algorithmic bias** — models trained on skewed data reproduce and amplify
  discrimination.
- **The EU AI Act** — a risk-tiered regime (unacceptable / high / limited /
  minimal) with strict obligations for high-risk systems.
- **Explainability & transparency** — the ability to justify a model's outputs;
  central to accountability and redress.
- **Data privacy** — GDPR principles (lawful basis, minimisation, purpose
  limitation) govern the data AI is built on.
- **Human oversight** — meaningful human-in-the-loop control over consequential
  decisions.
"""
R6_QUESTIONS = [
    {"question": "'Algorithmic bias' most often originates from…", "options": ["Faster processors", "Skewed or unrepresentative training data", "Open-source licences", "Cloud outages"], "correct": 1, "explanation": "Biased or unrepresentative training data leads models to reproduce discrimination.", "difficulty": "easy"},
    {"question": "The EU AI Act classifies systems primarily by…", "options": ["Colour", "Risk tier (unacceptable/high/limited/minimal)", "Vendor size", "Programming language"], "correct": 1, "explanation": "It is a risk-tiered regime with the strictest rules for high-risk systems.", "difficulty": "easy"},
    {"question": "Which regulation governs personal data used to train models in the EU?", "options": ["MiFID II", "GDPR", "Basel III", "REACH"], "correct": 1, "explanation": "GDPR governs personal data — lawful basis, minimisation, purpose limitation.", "difficulty": "easy"},
    {"question": "AI ethics spans which ESG pillars most directly?", "options": ["Only Environmental", "Social and Governance", "Only Governance", "None"], "correct": 1, "explanation": "Bias/rights are Social; oversight/transparency are Governance.", "difficulty": "easy"},
    {"question": "'Explainability' in AI governance refers to…", "options": ["How fast a model runs", "The ability to justify and interpret a model's outputs", "The model's file size", "The marketing story"], "correct": 1, "explanation": "Explainability is being able to justify outputs — key to accountability and redress.", "difficulty": "medium"},
    {"question": "Under the EU AI Act, high-risk systems must have…", "options": ["No documentation", "Risk management, data governance, and human oversight", "Only a privacy policy", "A social-media account"], "correct": 1, "explanation": "High-risk systems carry strict obligations including human oversight and data governance.", "difficulty": "medium"},
    {"question": "'Human-in-the-loop' means…", "options": ["Humans watch ads", "Meaningful human control over consequential automated decisions", "Employees test hardware", "A recruitment process"], "correct": 1, "explanation": "It is meaningful human oversight of consequential AI decisions.", "difficulty": "medium"},
    {"question": "A hiring model rejects qualified candidates from one demographic. The core ESG failure is…", "options": ["Slow inference", "Discriminatory bias harming a protected group", "High cloud cost", "Poor UI design"], "correct": 1, "explanation": "The harm is discriminatory bias — a Social-pillar failure with legal exposure.", "difficulty": "medium"},
    {"question": "Why is data minimisation an AI-governance principle, not just privacy hygiene?", "options": ["It speeds up marketing", "Less unnecessary data reduces bias, breach, and misuse risk", "It increases model size", "It is optional"], "correct": 1, "explanation": "Collecting only what's needed shrinks bias, breach, and misuse surface area.", "difficulty": "hard"},
    {"question": "Deploying an unexplainable 'black-box' model for credit decisions primarily risks…", "options": ["Nothing", "Regulatory non-compliance and inability to provide redress", "Faster approvals only", "Lower storage cost"], "correct": 1, "explanation": "Without explainability, the firm can't justify decisions or offer redress — a compliance and rights failure.", "difficulty": "hard"},
    {"question": "The strongest governance response to AI bias is…", "options": ["Hiding the model", "Independent audit, bias testing, and human oversight before deployment", "Marketing the model as 'ethical'", "Disabling logging"], "correct": 1, "explanation": "Independent audit, bias testing, and oversight address the risk at source.", "difficulty": "hard"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  ROUND 7 — Circular Economy Pivot
# ═══════════════════════════════════════════════════════════════════════════
R7_REVIEW = """## Circular Economy — Designing Out Waste

A circular economy decouples growth from virgin-resource use by keeping
materials in productive use. Core ideas for Round 7:
- **Waste hierarchy** — Reduce > Reuse > Recycle > Recover > Dispose.
- **The R-strategies** — Refuse, Rethink, Reduce, Reuse, Repair, Refurbish,
  Remanufacture, Repurpose, Recycle, Recover.
- **Extended Producer Responsibility (EPR)** — producers bear end-of-life cost/
  responsibility for their products.
- **Cradle-to-cradle** — designing products so materials become nutrients for
  new cycles, not landfill.
- **Product-as-a-service** — selling function (light, mobility) rather than the
  physical good, aligning incentives with durability and recovery.
"""
R7_QUESTIONS = [
    {"question": "The waste hierarchy ranks which option highest?", "options": ["Recycle", "Dispose", "Reduce", "Recover"], "correct": 2, "explanation": "Reduce sits at the top: preventing waste beats recycling or disposal.", "difficulty": "easy"},
    {"question": "A circular economy aims to…", "options": ["Maximise virgin-material use", "Keep materials in productive use and design out waste", "Increase landfill", "Speed up disposal"], "correct": 1, "explanation": "It keeps materials circulating and designs out waste and pollution.", "difficulty": "easy"},
    {"question": "'Extended Producer Responsibility' makes whom responsible for end-of-life?", "options": ["Only consumers", "The producer of the product", "Local government only", "Retailers only"], "correct": 1, "explanation": "EPR shifts end-of-life cost/responsibility onto the producer.", "difficulty": "easy"},
    {"question": "'Cradle-to-cradle' design means…", "options": ["Products end in landfill", "Materials are designed to feed new cycles", "Products last one use", "Only recycling metal"], "correct": 1, "explanation": "Materials become nutrients for new production cycles rather than waste.", "difficulty": "easy"},
    {"question": "Which is an example of 'product-as-a-service'?", "options": ["Selling lightbulbs", "Selling lighting-as-a-service and retaining the fixtures", "Landfilling fixtures", "Exporting waste"], "correct": 1, "explanation": "Selling the function (light) keeps the producer responsible for durability and recovery.", "difficulty": "medium"},
    {"question": "Why does product-as-a-service align incentives with durability?", "options": ["It doesn't", "The producer retains ownership, so longer-lasting products cost it less", "It raises disposal fees for users", "It bans repair"], "correct": 1, "explanation": "Retaining ownership means durability and recovery directly benefit the producer.", "difficulty": "medium"},
    {"question": "Which R-strategy is generally higher-value than recycling?", "options": ["Recover", "Remanufacture", "Dispose", "Incinerate"], "correct": 1, "explanation": "Remanufacture retains more embedded value than breaking material down to recycle.", "difficulty": "medium"},
    {"question": "A key barrier to circularity in electronics is…", "options": ["Too much repairability", "Design that prevents disassembly, repair, and material recovery", "Excess recycling capacity", "Low product demand"], "correct": 1, "explanation": "Non-repairable, hard-to-disassemble design blocks reuse and recovery.", "difficulty": "medium"},
    {"question": "How can circular design reduce a firm's Scope 3 emissions?", "options": ["It can't", "Reuse/remanufacture avoids virgin-material and manufacturing emissions upstream", "By increasing shipping", "By adding packaging"], "correct": 1, "explanation": "Avoiding virgin extraction and re-manufacture cuts embodied (Scope 3) emissions.", "difficulty": "hard"},
    {"question": "EPR schemes primarily internalise which externality?", "options": ["Advertising cost", "End-of-life waste-management cost", "Executive pay", "Currency risk"], "correct": 1, "explanation": "EPR forces producers to bear the disposal/recovery cost society otherwise absorbs.", "difficulty": "hard"},
    {"question": "The biggest strategic risk of ignoring circularity is…", "options": ["Nothing", "Exposure to resource-price volatility and tightening EPR/right-to-repair regulation", "Lower marketing spend", "Faster obsolescence being rewarded"], "correct": 1, "explanation": "Linear models face resource-price shocks and rising circular-economy regulation.", "difficulty": "hard"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  ROUND 8 — Blue Water Stress
# ═══════════════════════════════════════════════════════════════════════════
R8_REVIEW = """## Water Stewardship & Blue-Water Stress

Water is a shared, local, and increasingly scarce resource — a material risk for
industrial operations. Round 8 concepts:
- **Water stress** — demand approaching or exceeding available supply in a basin.
- **Water footprint** — blue (surface/ground), green (rainwater), and grey
  (pollution-dilution) water embedded in operations and products.
- **Watershed / basin risk** — water risk is inherently *local*; a global average
  hides acute basin-level exposure.
- **CDP Water & the CEO Water Mandate** — disclosure and stewardship frameworks.
- **TNFD** — nature-related disclosures now explicitly cover freshwater
  dependencies and impacts.
- **Context-based water targets** — targets set against local basin conditions,
  not a flat corporate percentage.
"""
R8_QUESTIONS = [
    {"question": "'Water stress' occurs when…", "options": ["Water is always abundant", "Demand approaches or exceeds available supply in an area", "Rainfall is high", "A pipe leaks"], "correct": 1, "explanation": "Water stress is demand meeting or exceeding local available supply.", "difficulty": "easy"},
    {"question": "Water risk is best understood at which scale?", "options": ["Global average", "Local watershed / basin", "National only", "Continental"], "correct": 1, "explanation": "Water is inherently local — basin-level exposure matters, not global averages.", "difficulty": "easy"},
    {"question": "'Blue water' in a water footprint refers to…", "options": ["Rainwater", "Surface and groundwater consumed", "Polluted water only", "Ocean water"], "correct": 1, "explanation": "Blue water is surface/ground water consumed; green is rainwater; grey is dilution water.", "difficulty": "easy"},
    {"question": "Which framework focuses on corporate water disclosure?", "options": ["CDP Water", "Basel III", "MiFID II", "ISO 27001"], "correct": 0, "explanation": "CDP Water is a leading corporate water-disclosure framework.", "difficulty": "easy"},
    {"question": "Why can a company with low global water use still face acute water risk?", "options": ["It can't", "A key facility may sit in a severely water-stressed basin", "Water is never scarce", "Averages capture everything"], "correct": 1, "explanation": "A single facility in a stressed basin creates acute local exposure a global average hides.", "difficulty": "medium"},
    {"question": "'Grey water' in the water-footprint sense is…", "options": ["Recycled sink water", "Water needed to dilute pollution to safe levels", "Rainwater", "Seawater"], "correct": 1, "explanation": "Grey water is the volume required to assimilate pollutants to acceptable standards.", "difficulty": "medium"},
    {"question": "TNFD extends nature disclosure to explicitly include…", "options": ["Only carbon", "Freshwater dependencies and impacts", "Only biodiversity of forests", "Executive pay"], "correct": 1, "explanation": "TNFD covers nature broadly, including freshwater dependencies and impacts.", "difficulty": "medium"},
    {"question": "'Context-based water targets' are set relative to…", "options": ["A flat corporate %", "Local basin conditions and shared limits", "Competitor averages", "Share price"], "correct": 1, "explanation": "They reflect what a specific basin can sustain, not a uniform corporate percentage.", "difficulty": "medium"},
    {"question": "Why is water stewardship a shared-resource governance problem, not just efficiency?", "options": ["It isn't", "Basins are shared with communities/ecosystems, so unilateral use creates conflict and licence risk", "Water has no other users", "Efficiency solves scarcity fully"], "correct": 1, "explanation": "Shared basins mean over-extraction harms others and erodes social licence — beyond internal efficiency.", "difficulty": "hard"},
    {"question": "The most credible response to high blue-water stress at a plant is…", "options": ["Ignore it", "Reduce withdrawal, recycle on-site, and engage the watershed's stakeholders", "Buy carbon offsets", "Relocate emissions"], "correct": 1, "explanation": "Reducing withdrawal, closed-loop recycling, and watershed engagement address the actual risk.", "difficulty": "hard"},
    {"question": "Water scarcity most directly threatens which financial exposure for a manufacturer?", "options": ["Marketing budget", "Operational continuity and licence to operate", "Brand colour", "Patent count"], "correct": 1, "explanation": "No water can halt production and revoke the local licence to operate.", "difficulty": "hard"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  ROUND 9 — Just Transition & Labor
# ═══════════════════════════════════════════════════════════════════════════
R9_REVIEW = """## Just Transition & Labour Rights

Decarbonisation and restructuring must be *just* — distributing costs and
benefits fairly so no worker or community is left behind. Round 9 concepts:
- **Just Transition** — the ILO/Paris-anchored principle that the shift to a
  low-carbon economy protects workers and communities through reskilling, social
  dialogue, and investment.
- **Stranded workers/communities** — those dependent on declining activities
  (e.g. legacy mining) who bear transition costs.
- **Social dialogue** — meaningful engagement with workers and unions on change.
- **Reskilling & redeployment** — active labour-market support versus abrupt
  layoffs.
- **Responsible disengagement** — improving or exiting supplier relationships
  without abandoning workers to worse conditions.
"""
R9_QUESTIONS = [
    {"question": "A 'Just Transition' primarily protects…", "options": ["Only shareholders", "Workers and communities during the shift to a low-carbon economy", "Only executives", "Only regulators"], "correct": 1, "explanation": "It ensures the low-carbon shift is fair to workers and affected communities.", "difficulty": "easy"},
    {"question": "Which body anchors the Just Transition concept in labour standards?", "options": ["ILO", "OPEC", "NATO", "FIFA"], "correct": 0, "explanation": "The International Labour Organization (ILO) is central to Just Transition guidelines.", "difficulty": "easy"},
    {"question": "'Reskilling' in a transition context means…", "options": ["Firing workers", "Training workers for new roles in the changing economy", "Cutting wages", "Outsourcing offshore"], "correct": 1, "explanation": "Reskilling equips workers for viable new roles rather than discarding them.", "difficulty": "easy"},
    {"question": "'Social dialogue' refers to…", "options": ["Company social media", "Meaningful engagement with workers and unions on change", "Marketing campaigns", "Customer surveys"], "correct": 1, "explanation": "It is structured engagement with workers/unions over transition decisions.", "difficulty": "easy"},
    {"question": "'Stranded workers' are those…", "options": ["On vacation", "Dependent on declining activities who bear transition costs", "Recently promoted", "Working remotely"], "correct": 1, "explanation": "They depend on shrinking industries and carry the human cost of transition.", "difficulty": "medium"},
    {"question": "'Responsible disengagement' from a problematic supplier means…", "options": ["Cutting ties instantly with no notice", "Working to improve conditions or exiting without abandoning workers to worse harm", "Ignoring the issue", "Publicly blaming the supplier"], "correct": 1, "explanation": "Abrupt exit can worsen worker conditions; responsible disengagement mitigates that harm.", "difficulty": "medium"},
    {"question": "Why can abrupt plant closures create ESG risk even when carbon falls?", "options": ["They don't", "They inflict social harm, community backlash, and reputational/regulatory cost", "They always raise share price", "They reduce Scope 3 only"], "correct": 1, "explanation": "Ignoring the social dimension of transition creates backlash and reputational damage.", "difficulty": "medium"},
    {"question": "Community investment during transition primarily aims to…", "options": ["Increase executive pay", "Cushion affected communities and sustain social licence", "Avoid all disclosure", "Boost quarterly EPS"], "correct": 1, "explanation": "It offsets local harm and preserves the licence to operate.", "difficulty": "medium"},
    {"question": "A firm decarbonises rapidly but lays off a whole town's workforce with no support. The failure is…", "options": ["Environmental only", "A Just Transition / Social failure despite the carbon win", "No failure", "A governance win"], "correct": 1, "explanation": "Environmental progress at the cost of workers violates Just Transition principles.", "difficulty": "hard"},
    {"question": "Why is social dialogue considered risk mitigation, not just goodwill?", "options": ["It isn't", "Early worker engagement reduces strikes, litigation, and reputational shocks", "It slows everything with no benefit", "It raises wages arbitrarily"], "correct": 1, "explanation": "Engaging workers early pre-empts disputes, litigation, and reputational damage.", "difficulty": "hard"},
    {"question": "Which best demonstrates a credible Just Transition plan?", "options": ["A press release only", "Funded reskilling, redeployment, community investment, and union engagement", "Silent layoffs", "Offsets purchased abroad"], "correct": 1, "explanation": "Credibility comes from funded, concrete measures — not announcements.", "difficulty": "hard"},
]

# ═══════════════════════════════════════════════════════════════════════════
#  ROUND 10 — Grand Finale: Activist Ultimatum & Terminal Value
# ═══════════════════════════════════════════════════════════════════════════
R10_REVIEW = """## Shareholder Activism, Governance & Terminal Value

The finale tests whether five years of ESG posture translate into durable
enterprise value under activist pressure. Round 10 concepts:
- **Shareholder activism** — investors using ownership rights (proxy votes,
  resolutions, board nominations) to force change.
- **Say-on-Climate / Say-on-Pay** — advisory votes on climate strategy and
  executive pay.
- **ESG alpha & cost of capital** — credible ESG performance lowers WACC and can
  add a valuation premium; greenwashing does the reverse when exposed.
- **Terminal / enterprise value** — the discounted value of the enduring
  business; equity value = enterprise value − net debt.
- **Board accountability** — governance quality (independence, oversight,
  transparency) is what makes E and S credible to the market.
"""
R10_QUESTIONS = [
    {"question": "Shareholder activism uses which primary lever?", "options": ["Advertising", "Ownership rights — proxy votes, resolutions, board nominations", "Product design", "Payroll"], "correct": 1, "explanation": "Activists deploy ownership rights: votes, resolutions, and board seats.", "difficulty": "easy"},
    {"question": "A 'Say-on-Climate' vote is…", "options": ["A binding tax", "An advisory shareholder vote on climate strategy", "A carbon offset", "A supplier contract"], "correct": 1, "explanation": "It is an advisory vote letting shareholders weigh in on climate plans.", "difficulty": "easy"},
    {"question": "Equity value equals…", "options": ["Enterprise value + net debt", "Enterprise value − net debt", "Revenue − opex", "Assets + liabilities"], "correct": 1, "explanation": "Equity value = enterprise (terminal) value minus net debt.", "difficulty": "easy"},
    {"question": "Strong, credible ESG performance tends to…", "options": ["Raise the cost of capital", "Lower the cost of capital / WACC", "Have no financial effect", "Guarantee bankruptcy"], "correct": 1, "explanation": "Credible ESG lowers WACC and can add a valuation premium.", "difficulty": "easy"},
    {"question": "Why does governance quality make Environmental and Social claims 'credible'?", "options": ["It doesn't", "Board oversight, independence, and transparency are what markets trust to verify E and S", "It replaces E and S", "It only affects pay"], "correct": 1, "explanation": "Governance is the foundation that makes E and S believable to investors.", "difficulty": "medium"},
    {"question": "An activist consortium demands an emergency shareholder vote citing low reputation. The core threat is…", "options": ["A marketing tweak", "Loss of board control / forced strategic change", "A new product line", "A dividend increase"], "correct": 1, "explanation": "Activist votes can reshape the board and force strategy — a control threat.", "difficulty": "medium"},
    {"question": "How does exposed greenwashing affect terminal value?", "options": ["Raises it", "Erodes it via penalties, lost trust, and higher cost of capital", "No effect", "Only affects marketing"], "correct": 1, "explanation": "Discovery triggers penalties and trust loss that raise WACC and cut valuation.", "difficulty": "medium"},
    {"question": "'ESG alpha' refers to…", "options": ["A carbon unit", "Excess risk-adjusted return attributable to ESG quality", "An audit standard", "A board committee"], "correct": 1, "explanation": "It's the outperformance linked to superior ESG management.", "difficulty": "medium"},
    {"question": "Why can a company post a positive enterprise value yet a negative equity value?", "options": ["Impossible", "Net debt exceeds enterprise value, wiping out shareholders", "Revenue is negative", "It paid too little tax"], "correct": 1, "explanation": "When net debt > enterprise value, equity is wiped out even with positive EV.", "difficulty": "hard"},
    {"question": "The most durable defence against activist intervention is…", "options": ["A bigger ad budget", "A credible, well-governed ESG and financial track record", "Ignoring investors", "Share buybacks alone"], "correct": 1, "explanation": "Consistent, well-governed performance removes the activist's thesis.", "difficulty": "hard"},
    {"question": "Say-on-Pay votes primarily hold the board accountable for…", "options": ["Carbon targets", "Executive compensation alignment with performance", "Water use", "Supplier audits"], "correct": 1, "explanation": "Say-on-Pay is an advisory vote on executive-pay alignment with performance.", "difficulty": "hard"},
]


# ── Notebook records (NotebookLMItem shape) ─────────────────────────────────
ROUND_QUIZ_NOTEBOOKS = [
    {
        "id": "NLM_R2", "title": "Double Materiality & CSRD",
        "description": "Knowledge check on double materiality, ESRS, and the CSRD assessment you run in Round 2.",
        "content_types": ["quiz", "review"], "target_round": 2, "category": "General",
        "podcast_transcript": [], "review_content": R2_REVIEW, "quiz_questions": R2_QUESTIONS,
    },
    {
        "id": "NLM_R4", "title": "ESG Contagion & Reputational Risk",
        "description": "Knowledge check on social licence, greenwashing, and stakeholder-cascade risk (Round 4).",
        "content_types": ["quiz", "review"], "target_round": 4, "category": "Social",
        "podcast_transcript": [], "review_content": R4_REVIEW, "quiz_questions": R4_QUESTIONS,
    },
    {
        "id": "NLM_R6", "title": "AI Ethics, Bias & Governance",
        "description": "Knowledge check on algorithmic bias, the EU AI Act, explainability, and data privacy (Round 6).",
        "content_types": ["quiz", "review"], "target_round": 6, "category": "Social",
        "podcast_transcript": [], "review_content": R6_REVIEW, "quiz_questions": R6_QUESTIONS,
    },
    {
        "id": "NLM_R7", "title": "Circular Economy & Waste",
        "description": "Knowledge check on the waste hierarchy, EPR, cradle-to-cradle, and product-as-a-service (Round 7).",
        "content_types": ["quiz", "review"], "target_round": 7, "category": "Ecological",
        "podcast_transcript": [], "review_content": R7_REVIEW, "quiz_questions": R7_QUESTIONS,
    },
    {
        "id": "NLM_R8", "title": "Water Stewardship & Scarcity",
        "description": "Knowledge check on water stress, basin risk, water footprint, and stewardship frameworks (Round 8).",
        "content_types": ["quiz", "review"], "target_round": 8, "category": "Ecological",
        "podcast_transcript": [], "review_content": R8_REVIEW, "quiz_questions": R8_QUESTIONS,
    },
    {
        "id": "NLM_R9", "title": "Just Transition & Labour Rights",
        "description": "Knowledge check on Just Transition, reskilling, social dialogue, and responsible disengagement (Round 9).",
        "content_types": ["quiz", "review"], "target_round": 9, "category": "Social",
        "podcast_transcript": [], "review_content": R9_REVIEW, "quiz_questions": R9_QUESTIONS,
    },
    {
        "id": "NLM_R10", "title": "Activism, Governance & Terminal Value",
        "description": "Knowledge check on shareholder activism, say-on-climate, ESG alpha, and the equity bridge (Round 10).",
        "content_types": ["quiz", "review"], "target_round": 10, "category": "General",
        "podcast_transcript": [], "review_content": R10_REVIEW, "quiz_questions": R10_QUESTIONS,
    },
]
