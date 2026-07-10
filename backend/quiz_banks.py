"""
Quiz question banks for NotebookLM notebooks.
Each notebook has 20 difficulty-tagged MCQ questions derived from review content.
Difficulty levels: easy, medium, hard
"""

# ═══════════════════════════════════════════════════════════════
#  NLM_001 — ESG Fundamentals Deep Dive (Round 1, General)
# ═══════════════════════════════════════════════════════════════

NLM_001_REVIEW = """## ESG Fundamentals — Comprehensive Review

### What is ESG?
**ESG** stands for **Environmental, Social, and Governance** — three pillars that measure a company's sustainability and ethical impact. Originally a niche concern for socially responsible investors, ESG has become a mainstream framework used by regulators, institutional investors, credit agencies, and consumers to evaluate corporate performance beyond financial returns.

### The Three Pillars in Detail

**🌍 Environmental (E)**
- **Carbon emissions & climate targets**: Scope 1 (direct), Scope 2 (purchased energy), Scope 3 (value chain). Companies must set Science-Based Targets (SBTi) aligned to 1.5°C pathways.
- **Water stewardship & waste reduction**: Water-intensive industries (mining, pharma) face acute physical risks. Zero-waste-to-landfill targets are increasingly standard.
- **Biodiversity protection**: The Taskforce on Nature-related Financial Disclosures (TNFD) mirrors TCFD for nature. Companies must assess dependencies on ecosystem services.
- **Resource efficiency & circular economy**: Product lifecycle design, materials recovery, and industrial symbiosis reduce environmental footprint and input costs.
- **Pollution prevention**: Air, water, and soil contamination from manufacturing, chemicals, and extractive operations carry both regulatory and reputational risk.

**👥 Social (S)**
- **Labour rights & fair wages**: ILO core conventions, living wage commitments, freedom of association. Non-compliance triggers supply chain exclusion.
- **Community engagement**: Free, Prior, and Informed Consent (FPIC) for operations near indigenous communities. Social licence to operate is earned, not given.
- **Diversity, equity & inclusion (DEI)**: Board diversity quotas, gender pay gap reporting, inclusive hiring. Linked to innovation performance and talent retention.
- **Supply chain responsibility**: Multi-tier supplier audits, conflict minerals due diligence (Dodd-Frank Section 1502, EU Conflict Minerals Regulation).
- **Health & safety**: Occupational health programs, process safety management. Fatality-free operations are the benchmark.
- **Data privacy & digital rights**: GDPR, CCPA, and emerging AI governance frameworks. Software and tech divisions face heightened scrutiny.

**⚖️ Governance (G)**
- **Board independence & diversity**: Minimum 40% independent directors (EU standard). Separation of Chair and CEO roles reduces conflicts of interest.
- **Executive compensation alignment**: Long-term incentive plans (LTIPs) tied to ESG KPIs. Say-on-pay votes give shareholders a voice.
- **Anti-corruption & ethics**: FCPA, UK Bribery Act compliance. Whistleblower protection programs are essential.
- **Stakeholder transparency**: Integrated reporting (IIRC framework), ESG data assurance by third parties.
- **Risk management**: Enterprise risk frameworks must incorporate climate, social, and governance risks alongside financial ones.
- **Tax transparency**: Country-by-country reporting, fair tax principles. Aggressive tax planning damages reputation.

### Double Materiality (CSRD)
The EU **Corporate Sustainability Reporting Directive (CSRD)** requires companies to report on two dimensions simultaneously:
1. **Financial materiality** — How ESG risks affect the company's financial value (outside-in perspective)
2. **Impact materiality** — How the company impacts society and the environment (inside-out perspective)

An issue is "double material" when it is significant from both perspectives. For example, carbon emissions are financially material (carbon tax costs) AND impact material (climate change contribution).

The CSRD applies to all large EU companies and non-EU companies with significant EU revenue. Reports must follow **European Sustainability Reporting Standards (ESRS)** and be assured by auditors.

### Key Frameworks & Standards
- **GRI (Global Reporting Initiative)**: Impact-focused, widely used for sustainability reports
- **SASB (now ISSB)**: Industry-specific, investor-focused financial materiality standards
- **TCFD**: Climate-related financial disclosures — scenario analysis, governance, strategy, risk management, metrics
- **TNFD**: Nature-related financial disclosures — dependencies and impacts on biodiversity
- **UN SDGs**: 17 Sustainable Development Goals — used as a universal language for impact alignment
- **Science-Based Targets (SBTi)**: Validates corporate emissions reduction targets against climate science

### Key Concepts for Round 1
- **ESG Audit Depth**: Surface scan vs. deep forensic audit affects what risks you uncover. A surface scan is cheap but misses hidden liabilities. A forensic audit is expensive but reveals the full picture.
- **Stakeholder Mapping (Mendelow's Matrix)**: Classifying stakeholders by Power (ability to influence) and Interest (level of concern). Quadrants: Keep Satisfied (high power, low interest), Manage Closely (high power, high interest), Monitor (low power, low interest), Keep Informed (low power, high interest).
- **Capital Allocation via CSF Pool**: The Corporate Sustainability Fund is the primary mechanism for investing in ESG improvements across business units.
- **Materiality Assessment**: Identifying which ESG issues are most important (material) for a specific company based on industry, geography, and stakeholder expectations.

### Why ESG Matters — The Business Case
Companies with strong ESG performance see:
- Lower cost of capital (avg. 1.2% reduction according to MSCI research)
- Higher employee retention (+25% in high-ESG companies)
- Better risk management and fewer "black swan" events
- Stronger brand loyalty and customer willingness to pay premiums (up to 10%)
- Regulatory preparedness (avoiding fines, sanctions, and licence revocations)
- Improved access to green finance instruments (green bonds, sustainability-linked loans)

### ESG Rating Agencies
- **MSCI ESG Ratings**: AAA to CCC scale, used by institutional investors
- **Sustainalytics**: Risk-based approach (Negligible → Severe)
- **CDP**: Climate, water, and forests disclosure scoring (A to D-)
- **ISS ESG**: Corporate and country-level ratings
- Ratings divergence is common — different agencies, different methodologies, different conclusions
"""

NLM_001_QUESTIONS = [
    # ── EASY ──
    {"question": "What does the 'E' in ESG stand for?", "options": ["Economics", "Environmental", "Efficiency", "Equity"], "correct": 1, "explanation": "ESG stands for Environmental, Social, and Governance. The 'E' covers carbon emissions, biodiversity, water, waste, and resource management.", "difficulty": "easy"},
    {"question": "What does the 'S' in ESG stand for?", "options": ["Sustainability", "Social", "Strategy", "Standards"], "correct": 1, "explanation": "The 'S' in ESG covers Social factors including labour rights, community engagement, diversity, and supply chain responsibility.", "difficulty": "easy"},
    {"question": "What does the 'G' in ESG stand for?", "options": ["Growth", "Global", "Governance", "Green"], "correct": 2, "explanation": "Governance covers board composition, executive pay, transparency, anti-corruption, and risk management.", "difficulty": "easy"},
    {"question": "How many pillars make up the ESG framework?", "options": ["Two", "Three", "Four", "Five"], "correct": 1, "explanation": "ESG has three pillars: Environmental, Social, and Governance.", "difficulty": "easy"},
    {"question": "Which ESG pillar covers carbon emissions and climate targets?", "options": ["Social", "Governance", "Environmental", "Economic"], "correct": 2, "explanation": "Carbon emissions, climate targets, biodiversity, and resource efficiency all fall under the Environmental pillar.", "difficulty": "easy"},
    {"question": "What does CSRD stand for?", "options": ["Corporate Social Responsibility Directive", "Corporate Sustainability Reporting Directive", "Climate Strategy and Risk Disclosure", "Community Sustainability Reporting Duty"], "correct": 1, "explanation": "CSRD is the EU Corporate Sustainability Reporting Directive, requiring companies to report on sustainability impacts.", "difficulty": "easy"},
    {"question": "What is the average cost of capital reduction for companies with strong ESG?", "options": ["0.5%", "1.2%", "3.0%", "5.0%"], "correct": 1, "explanation": "According to MSCI research, companies with strong ESG performance see an average 1.2% reduction in cost of capital.", "difficulty": "easy"},
    # ── MEDIUM ──
    {"question": "What are the two dimensions of 'Double Materiality' under CSRD?", "options": ["Past materiality and future materiality", "Financial materiality and impact materiality", "Internal materiality and external materiality", "Quantitative materiality and qualitative materiality"], "correct": 1, "explanation": "Double Materiality requires reporting on financial materiality (how ESG affects company value) AND impact materiality (how the company affects society and environment).", "difficulty": "medium"},
    {"question": "In Mendelow's Stakeholder Matrix, which quadrant requires the strategy 'Manage Closely'?", "options": ["Low power, low interest", "Low power, high interest", "High power, low interest", "High power, high interest"], "correct": 3, "explanation": "Stakeholders with both high power and high interest must be managed closely — they can influence outcomes and care deeply about them.", "difficulty": "medium"},
    {"question": "Which framework specifically addresses nature-related financial disclosures?", "options": ["TCFD", "TNFD", "GRI", "SASB"], "correct": 1, "explanation": "The Taskforce on Nature-related Financial Disclosures (TNFD) mirrors TCFD but focuses on biodiversity and ecosystem dependencies.", "difficulty": "medium"},
    {"question": "What does Scope 3 emissions cover?", "options": ["Direct emissions from company operations", "Emissions from purchased electricity", "All indirect emissions in the value chain", "Emissions avoided through offsets"], "correct": 2, "explanation": "Scope 3 covers all indirect emissions in a company's value chain — suppliers, logistics, product use, and end-of-life. It typically represents 70-90% of total emissions.", "difficulty": "medium"},
    {"question": "What is the purpose of Science-Based Targets (SBTi)?", "options": ["Rate companies on ESG performance", "Set industry-specific reporting standards", "Validate corporate emissions targets against climate science", "Provide green bond certification"], "correct": 2, "explanation": "SBTi validates that corporate emissions reduction targets are aligned with what climate science says is necessary to meet the Paris Agreement goals.", "difficulty": "medium"},
    {"question": "What employee benefit is associated with high ESG performance?", "options": ["+10% salary increase", "+25% employee retention", "+50% productivity", "+15% promotion rate"], "correct": 1, "explanation": "Companies with strong ESG performance see approximately 25% higher employee retention rates.", "difficulty": "medium"},
    {"question": "What does FPIC stand for in community engagement?", "options": ["Federal Policy on Industrial Compliance", "Free, Prior, and Informed Consent", "Financial Planning for Impact Capital", "Framework for Public Interest Consultation"], "correct": 1, "explanation": "FPIC — Free, Prior, and Informed Consent — is a principle requiring that indigenous communities give consent before projects affecting their lands.", "difficulty": "medium"},
    # ── HARD ──
    {"question": "Why do ESG rating agencies often give divergent scores to the same company?", "options": ["They use identical methodologies but different data", "They use different methodologies, weighting, and data sources", "They only disagree on Governance scores", "There is a regulatory requirement for divergence"], "correct": 1, "explanation": "ESG rating divergence occurs because agencies use different methodologies, weights, metrics, and data sources. MSCI, Sustainalytics, and CDP may reach different conclusions about the same company.", "difficulty": "hard"},
    {"question": "Under the CSRD, which reporting standards must companies follow?", "options": ["GRI Standards only", "SASB Standards only", "European Sustainability Reporting Standards (ESRS)", "TCFD Recommendations only"], "correct": 2, "explanation": "The CSRD requires companies to follow ESRS (European Sustainability Reporting Standards), which are developed by EFRAG and cover all ESG topics.", "difficulty": "hard"},
    {"question": "Which type of ESG audit carries the risk of missing hidden liabilities but is cheaper?", "options": ["Forensic audit", "Surface-level scan", "Third-party assured audit", "Integrated assurance audit"], "correct": 1, "explanation": "A surface-level scan is fast and cheap but risks missing hidden environmental or social liabilities that a deeper forensic audit would uncover.", "difficulty": "hard"},
    {"question": "What concept describes the idea that a company's right to operate is earned from the community, not granted by regulation?", "options": ["Regulatory licence", "Social licence to operate", "Free market mandate", "Corporate charter"], "correct": 1, "explanation": "Social licence to operate is the ongoing acceptance of a company's practices by the local community and broader society. It is earned through trust, transparency, and genuine engagement.", "difficulty": "hard"},
    {"question": "What is the maximum customer willingness-to-pay premium associated with strong ESG performance?", "options": ["Up to 5%", "Up to 10%", "Up to 20%", "Up to 30%"], "correct": 1, "explanation": "Research shows customers are willing to pay premiums of up to 10% for products from companies with strong ESG credentials.", "difficulty": "hard"},
    {"question": "Which legislation requires multi-tier conflict minerals due diligence for supply chains?", "options": ["UK Modern Slavery Act", "Paris Agreement Article 6", "Dodd-Frank Section 1502 and EU Conflict Minerals Regulation", "Basel Convention"], "correct": 2, "explanation": "Dodd-Frank Section 1502 (US) and the EU Conflict Minerals Regulation require companies to conduct due diligence on tin, tantalum, tungsten, and gold supply chains.", "difficulty": "hard"},
]

# ═══════════════════════════════════════════════════════════════
#  NLM_002 — Carbon Markets & Climate Risk (Round 3, Ecological)
# ═══════════════════════════════════════════════════════════════

NLM_002_REVIEW = """## Carbon Markets & Climate Risk — Comprehensive Review

### Carbon Pricing Mechanisms

Carbon pricing puts a monetary cost on greenhouse gas emissions to incentivize reduction. There are two main mechanisms:

**Emissions Trading System (ETS) — Cap and Trade**
A cap-and-trade system where governments set a total emissions cap. Allowances equal to the cap are distributed or auctioned. Companies that emit less can sell surplus allowances; those that exceed their allocation must buy more. The price is set by supply and demand in the market. The EU ETS is the world's largest, covering approximately 40% of EU greenhouse gas emissions across power generation, heavy industry, and aviation.

**Carbon Tax**
A direct fee levied on each tonne of CO₂ emitted. Provides price certainty (companies know the exact cost) but less environmental certainty than cap-and-trade (no guaranteed cap). Countries like Sweden ($130+/tCO₂), Canada, and South Africa use carbon taxes. Some jurisdictions combine both approaches.

### EU ETS Deep Dive

**Phase 4 (2021-2030)**: The current phase features significantly tighter caps, declining free allowances, and expanded sectoral coverage.
- **Annual cap reduction**: Linear Reduction Factor increased to 4.3% per year (from 2.2%)
- **Free allowance phase-out**: Declining annually, to be fully replaced by auctioning for most sectors by 2034
- **Market Stability Reserve (MSR)**: Absorbs surplus allowances to prevent price crashes
- **Innovation Fund**: Funded from ETS auction revenues, supports breakthrough clean tech

**CBAM — Carbon Border Adjustment Mechanism**
- Import tariff on carbon-intensive goods entering the EU (cement, iron/steel, aluminium, fertilisers, electricity, hydrogen)
- Prevents **carbon leakage** — when companies relocate production to countries without carbon pricing
- Transitional phase (2023-2025): Reporting only. Full implementation from 2026 with financial adjustment
- Importers must purchase CBAM certificates matching the carbon price difference between the EU and origin country

**Price trajectory**: EU ETS prices have risen from ~€5/tCO₂ in 2017 to ~€45 in 2021, with projections exceeding **€100/tCO₂ by 2030** and potentially €150+ by 2040. This makes decarbonization investments increasingly cost-effective compared to paying for allowances.

### Greenhouse Gas Protocol — Emission Scopes

**Scope 1 — Direct Emissions**
Emissions from sources owned or controlled by the company: on-site fuel combustion, fleet vehicles, process emissions, fugitive emissions (refrigerant leaks).

**Scope 2 — Indirect Energy Emissions**
Emissions from purchased electricity, steam, heating, and cooling. Can be reported using location-based (grid average) or market-based (supplier-specific) methods.

**Scope 3 — Value Chain Emissions**
All other indirect emissions: upstream (purchased goods, transportation, business travel, employee commuting) and downstream (product use, end-of-life treatment, investments). Typically represents **70-90%** of a company's total carbon footprint. The most challenging to measure but increasingly required for SBTi validation.

### Corporate Climate Strategy Framework

1. **Measure**: Establish a comprehensive GHG inventory across Scopes 1, 2, and 3. Use the GHG Protocol Corporate Standard. Engage suppliers for Scope 3 data.
2. **Set Targets**: Near-term (5-10 year) and long-term (Year 5) targets validated by SBTi. Net-zero commitments must include residual emissions plans.
3. **Reduce**: Energy efficiency improvements, renewable energy procurement (PPAs, RECs), process electrification, fuel switching, supply chain decarbonization programs.
4. **Report**: TCFD-aligned climate disclosure covering Governance, Strategy, Risk Management, and Metrics/Targets. Scenario analysis (1.5°C, 2°C, 4°C) is essential.
5. **Offset (last resort)**: Verified carbon credits (Gold Standard, Verra VCS) only for residual emissions. Not a substitute for reduction. Nature-based and technology-based removal credits.

### Climate Risk Categories

**Physical Risks**
- *Acute*: Extreme weather events (floods, hurricanes, wildfires) — supply chain disruption, asset damage
- *Chronic*: Sea-level rise, temperature increase, precipitation changes — resource availability, insurance costs

**Transition Risks**
- *Policy/Legal*: Carbon pricing, emissions regulations, litigation
- *Technology*: Stranded assets (fossil fuel infrastructure), disruption by clean tech
- *Market*: Shifting consumer preferences, commodity price changes
- *Reputation*: Stakeholder activism, greenwashing allegations

### Impact on Muressons Business Units
- **Electronics BU**: High-energy manufacturing = high Scope 1 & 2 emissions. Vulnerable to EU ETS costs and CBAM if sourcing from non-EU suppliers. Transition to renewable energy critical.
- **Pharma BU**: Cold chain logistics = significant Scope 3 emissions. Temperature-controlled transport and storage are energy-intensive. Active pharmaceutical ingredient (API) manufacturing chemical processes.
- **Software BU**: Low carbon intensity = competitive advantage. Data centre energy the main concern. Already well-positioned for green credentials.
- **Consumer Goods BU**: Packaging materials, distribution networks, and product lifecycle impacts. Circular economy strategies reduce both emissions and costs.

### Key Numbers to Remember
- EU ETS covers ~40% of EU GHG emissions
- Scope 3 = 70-90% of typical corporate footprint
- EU carbon price target: €100+/tCO₂ by 2030
- SBTi requires 42% reduction by 2030 for 1.5°C alignment
- CBAM full implementation: 2026
"""

NLM_002_QUESTIONS = [
    # ── EASY ──
    {"question": "What does the EU ETS stand for?", "options": ["European Union Energy Trading System", "European Union Emissions Trading System", "European Union Environmental Tax Scheme", "European Union Ecological Transition Strategy"], "correct": 1, "explanation": "The EU ETS is the European Union Emissions Trading System — the world's first and largest carbon market, established in 2005.", "difficulty": "easy"},
    {"question": "What are the two main carbon pricing mechanisms?", "options": ["Carbon tax and carbon credits", "Emissions Trading System and carbon tax", "Carbon offsets and green bonds", "Subsidies and penalties"], "correct": 1, "explanation": "The two main mechanisms are Emissions Trading Systems (cap-and-trade) and carbon taxes. Each has different strengths regarding price and environmental certainty.", "difficulty": "easy"},
    {"question": "What percentage of EU emissions does the EU ETS cover?", "options": ["About 20%", "About 40%", "About 60%", "About 80%"], "correct": 1, "explanation": "The EU ETS covers approximately 40% of EU greenhouse gas emissions across power generation, heavy industry, and aviation.", "difficulty": "easy"},
    {"question": "Which emission scope covers direct emissions from company operations?", "options": ["Scope 1", "Scope 2", "Scope 3", "Scope 4"], "correct": 0, "explanation": "Scope 1 covers direct emissions from sources owned or controlled by the company, such as on-site fuel combustion and fleet vehicles.", "difficulty": "easy"},
    {"question": "What type of emissions are covered by Scope 2?", "options": ["Direct operational emissions", "Purchased electricity and energy", "Supply chain emissions", "Product end-of-life emissions"], "correct": 1, "explanation": "Scope 2 covers indirect energy emissions from purchased electricity, steam, heating, and cooling.", "difficulty": "easy"},
    {"question": "Which Muressons BU has the lowest carbon intensity?", "options": ["Pharma", "Electronics", "Consumer Goods", "Software"], "correct": 3, "explanation": "Software has inherently low carbon intensity as digital services require minimal physical manufacturing.", "difficulty": "easy"},
    {"question": "What is the projected EU carbon price by 2030?", "options": ["€25-30 per tonne", "€45-60 per tonne", "€100+ per tonne", "€200+ per tonne"], "correct": 2, "explanation": "EU carbon prices are projected to exceed €100 per tonne by 2030, up from ~€45 in 2021.", "difficulty": "easy"},
    # ── MEDIUM ──
    {"question": "What is CBAM designed to prevent?", "options": ["Tax evasion by multinationals", "Carbon leakage through imports from countries without carbon pricing", "Environmental protests at EU borders", "Currency manipulation in green bond markets"], "correct": 1, "explanation": "CBAM prevents 'carbon leakage' — when companies relocate production to countries with weaker climate policies to avoid carbon costs.", "difficulty": "medium"},
    {"question": "Which Scope of emissions typically represents 70-90% of a company's total footprint?", "options": ["Scope 1", "Scope 2", "Scope 3", "Scopes 1 and 2 combined"], "correct": 2, "explanation": "Scope 3 (value chain emissions) typically represents 70-90% of a company's total footprint, though it's the most challenging to measure.", "difficulty": "medium"},
    {"question": "When does CBAM full implementation with financial adjustment begin?", "options": ["2024", "2025", "2026", "2030"], "correct": 2, "explanation": "CBAM's transitional phase (reporting only) runs 2023-2025. Full implementation with financial adjustments begins in 2026.", "difficulty": "medium"},
    {"question": "What is the Market Stability Reserve (MSR) in the EU ETS?", "options": ["A government fund for climate disasters", "A mechanism that absorbs surplus allowances to prevent price crashes", "A reserve of carbon credits for offsetting", "An insurance pool for carbon-intensive industries"], "correct": 1, "explanation": "The MSR absorbs surplus allowances when there are too many in circulation, helping stabilize the carbon price.", "difficulty": "medium"},
    {"question": "What reduction target does SBTi require by 2030 for 1.5°C alignment?", "options": ["25% reduction", "42% reduction", "55% reduction", "75% reduction"], "correct": 1, "explanation": "For 1.5°C alignment, SBTi requires companies to reduce emissions by at least 42% by 2030 from a base year.", "difficulty": "medium"},
    {"question": "What is the difference between 'acute' and 'chronic' physical climate risks?", "options": ["Acute are financial, chronic are reputational", "Acute are extreme weather events, chronic are long-term shifts", "Acute affect supply chain, chronic affect demand", "There is no difference"], "correct": 1, "explanation": "Acute physical risks are sudden extreme events (floods, fires). Chronic risks are gradual changes (sea-level rise, temperature increase).", "difficulty": "medium"},
    # ── HARD ──
    {"question": "What is the Linear Reduction Factor in the EU ETS Phase 4?", "options": ["1.5% per year", "2.2% per year", "4.3% per year", "6.0% per year"], "correct": 2, "explanation": "In Phase 4, the Linear Reduction Factor was increased to 4.3% per year (from 2.2%), meaning the emissions cap tightens more rapidly.", "difficulty": "hard"},
    {"question": "Which products are covered by the EU CBAM?", "options": ["All manufactured goods", "Only fossil fuels", "Cement, iron/steel, aluminium, fertilisers, electricity, hydrogen", "Only goods over €10,000 in value"], "correct": 2, "explanation": "CBAM covers six carbon-intensive product categories: cement, iron and steel, aluminium, fertilisers, electricity, and hydrogen.", "difficulty": "hard"},
    {"question": "What is the difference between location-based and market-based methods for Scope 2 reporting?", "options": ["Location-based uses grid average emissions factors; market-based uses supplier-specific factors", "Location-based is for domestic companies; market-based for multinationals", "They are identical but used in different jurisdictions", "Market-based is always lower"], "correct": 0, "explanation": "Location-based uses average grid emission factors for the region. Market-based reflects specific purchasing decisions (e.g., renewable PPAs). A company buying 100% renewable energy has zero market-based Scope 2.", "difficulty": "hard"},
    {"question": "Why are carbon offsets considered a 'last resort' in corporate climate strategy?", "options": ["They are very expensive", "They are illegal in the EU", "They don't substitute for actual emissions reduction and have quality concerns", "They require government approval"], "correct": 2, "explanation": "Offsets should only cover residual emissions after all reduction efforts. Quality varies widely, and using offsets instead of reducing emissions is considered greenwashing.", "difficulty": "hard"},
    {"question": "Which Muressons BU faces the most significant Scope 3 challenges and why?", "options": ["Software — data centre supply chain", "Electronics — component sourcing from global suppliers", "Pharma — cold chain logistics and API manufacturing", "Consumer Goods — retail distribution only"], "correct": 2, "explanation": "Pharma faces major Scope 3 challenges due to temperature-controlled logistics (cold chain), energy-intensive API manufacturing processes, and global distribution requirements.", "difficulty": "hard"},
    {"question": "What Swedish carbon tax rate makes it one of the world's highest?", "options": ["$50+ per tCO₂", "$80+ per tCO₂", "$130+ per tCO₂", "€100+ per tCO₂"], "correct": 2, "explanation": "Sweden has one of the world's highest carbon tax rates at over $130 per tonne of CO₂, driving rapid decarbonization.", "difficulty": "hard"},
]

# ═══════════════════════════════════════════════════════════════
#  NLM_003 — Supply Chain Ethics & Labour Rights (Round 5, Social)
# ═══════════════════════════════════════════════════════════════

NLM_003_REVIEW = """## Supply Chain Ethics & Labour Rights — Comprehensive Review

### The Global Challenge
- **50 million** people affected by modern slavery worldwide (ILO 2022 estimate)
- **$150 billion** in illegal profits from forced labour annually
- **160 million** children in child labour globally, with 79 million in hazardous work
- Mining, agriculture, garment manufacturing, and electronics assembly are highest-risk sectors
- Supply chain complexity (5-10 tiers deep) makes visibility and accountability extremely difficult

### Forms of Modern Slavery
- **Forced labour**: Work under threat of penalty — debt bondage, retention of identity documents, physical violence
- **Human trafficking**: Recruitment, transport, and exploitation through force, fraud, or coercion
- **Child labour**: Work that deprives children of education, health, and childhood. Hazardous child labour is worst-form
- **Bonded/debt labour**: Workers trapped by debts to employers or recruiters, often spanning generations
- **Domestic servitude**: Hidden exploitation in private households, extremely difficult to detect

### Key Legislation

**UK Modern Slavery Act (2015)**
- Companies with £36M+ annual turnover must publish an annual **Modern Slavery Statement**
- Must describe steps taken to prevent slavery in operations and supply chains
- Board-level sign-off required — personal accountability for directors
- Penalty: unlimited fines and reputational damage from non-compliance

**French Duty of Vigilance Law (2017)**
- Companies with 5,000+ employees in France (or 10,000+ globally) must establish a **vigilance plan**
- Covers human rights, health/safety, and environmental risks
- Civil liability for failure — companies can be sued for damages by victims
- First law to create a **legal duty of care** for corporate human rights impacts

**EU Corporate Sustainability Due Diligence Directive (CSDDD)**
- Mandatory human rights and environmental due diligence across the **full value chain**
- Covers subsidiaries, direct suppliers, and indirect business partners
- **Civil liability**: Companies can be held liable for failing to prevent adverse impacts
- Requires integration into corporate governance (board oversight, risk management)
- Applies to large EU companies (500+ employees, €150M+ turnover) and non-EU companies with €150M+ EU revenue
- Climate transition plans aligned with Paris Agreement are mandatory

**US Uyghur Forced Labor Prevention Act (UFLPA, 2022)**
- Presumes all goods from Xinjiang region are made with forced labour (rebuttable presumption)
- Importers must prove forced-labour-free supply chain or goods are seized at US customs
- Affects cotton, polysilicon (solar panels), tomatoes, and other commodities

### The Gobi Region Dilemma
Muressons' mining operations in the Gobi region present a complex ethical challenge:
- **Tier-3 mine workers** in artisanal and small-scale mining (ASM) operations with inadequate safety equipment
- **Community displacement**: Local communities relocated without adequate compensation or consent (FPIC violations)
- **Conflict mineral risks**: Revenue from minerals may fund armed groups or corrupt officials
- **Water scarcity**: Mining operations consume water resources that local populations depend on for survival
- **Child labour**: Children as young as 10 found working in unregulated artisanal mines
- **Environmental contamination**: Mercury and cyanide use in gold extraction poisons water tables

### Due Diligence Framework (OECD Six-Step)
1. **Embed**: Integrate responsible business conduct into policies and management systems
2. **Identify**: Map all suppliers across tiers — you can't address risks you haven't found
3. **Cease, prevent, mitigate**: Stop causing harm, prevent potential harm, mitigate actual harm
4. **Track**: Monitor implementation with measurable KPIs (audit scores, incident rates, worker surveys)
5. **Communicate**: Report publicly on findings, actions taken, and outcomes achieved
6. **Remediate**: Provide access to remedy for affected stakeholders — operational grievance mechanisms

### Responsible Disengagement vs. Cut-and-Run
- **Cut-and-run**: Immediately terminating contracts with non-compliant suppliers. This can worsen worker conditions as suppliers lose income and workers face unemployment.
- **Responsible disengagement**: A phased approach — set clear improvement expectations with timelines, provide capacity-building support, monitor progress, disengage only as a last resort after remediation fails.
- **Engagement and improvement** is the preferred approach recommended by the UN Guiding Principles on Business and Human Rights.

### Strategic Implications for Muressons
- Cutting ties with problematic suppliers may harm workers further — the "paradox of withdrawal"
- Engagement and capacity building create long-term, resilient supply chains
- Stakeholder trust is directly linked to supply chain transparency
- **Regulatory risk**: Non-compliance with CSDDD carries civil liability and unlimited fines
- **Reputational risk**: NGO campaigns and media exposés can destroy brand value overnight
- **Financial risk**: Supply chain disruptions from labour strikes, sanctions, or legal actions
- **Opportunity**: Companies with ethical supply chains command premium pricing and attract ESG-focused investors

### Worker Voice & Grievance Mechanisms
- **Hotlines and digital platforms**: Anonymous reporting channels for workers to raise concerns
- **Worker committees**: Elected representatives who negotiate with management on working conditions
- **Third-party audits**: Independent social audits (SA8000, SMETA) to verify compliance
- **Technology solutions**: Blockchain-based traceability, worker voice apps (e.g., Ulula, Laborlink)

### Metrics for Measuring Supply Chain Ethics
- % of suppliers audited in last 12 months
- Number of critical non-conformities identified and remediated
- Worker satisfaction scores from anonymous surveys
- Grievance mechanism utilization and resolution rates
- Tier-1, Tier-2, and Tier-3 supplier mapping coverage percentage
"""

NLM_003_QUESTIONS = [
    # ── EASY ──
    {"question": "How many people are estimated to be affected by modern slavery globally?", "options": ["10 million", "25 million", "50 million", "100 million"], "correct": 2, "explanation": "According to the ILO, an estimated 50 million people are in situations of modern slavery, including 28 million in forced labour.", "difficulty": "easy"},
    {"question": "Which UK law requires companies to publish Modern Slavery Statements?", "options": ["Companies Act", "UK Modern Slavery Act 2015", "Equality Act", "Human Rights Act"], "correct": 1, "explanation": "The UK Modern Slavery Act 2015 requires companies with £36M+ turnover to publish annual Modern Slavery Statements.", "difficulty": "easy"},
    {"question": "What annual revenue does forced labour generate in illegal profits?", "options": ["$50 billion", "$100 billion", "$150 billion", "$200 billion"], "correct": 2, "explanation": "Forced labour generates an estimated $150 billion in illegal profits annually.", "difficulty": "easy"},
    {"question": "Which sectors are highest risk for modern slavery?", "options": ["Technology and finance", "Mining, agriculture, garment, and electronics", "Healthcare and education", "Real estate and hospitality"], "correct": 1, "explanation": "Mining, agriculture, garment manufacturing, and electronics assembly are the highest-risk sectors for modern slavery.", "difficulty": "easy"},
    {"question": "What does the recommended approach say about suppliers with labour rights issues?", "options": ["Immediately terminate all contracts", "Ignore it if production continues", "Engage with the supplier to improve conditions", "Report only if legally required"], "correct": 2, "explanation": "The preferred approach is responsible engagement — working with suppliers to improve conditions rather than cutting ties.", "difficulty": "easy"},
    {"question": "How many children are estimated to be in child labour globally?", "options": ["50 million", "100 million", "160 million", "200 million"], "correct": 2, "explanation": "160 million children are in child labour globally, with 79 million in hazardous work.", "difficulty": "easy"},
    # ── MEDIUM ──
    {"question": "What does the EU CSDDD require companies to do?", "options": ["Only report on direct operations", "Conduct due diligence across their full value chain", "Exit all developing country markets", "Achieve zero human rights violations immediately"], "correct": 1, "explanation": "The CSDDD requires companies to conduct mandatory human rights and environmental due diligence across their full value chain, including subsidiaries and business partners.", "difficulty": "medium"},
    {"question": "What is 'responsible disengagement'?", "options": ["Immediately cutting ties with problematic suppliers", "A phased approach with improvement expectations before disengaging as last resort", "Ignoring supply chain problems", "Outsourcing due diligence to third parties"], "correct": 1, "explanation": "Responsible disengagement involves setting improvement expectations, providing support, monitoring progress, and disengaging only as a last resort after remediation fails.", "difficulty": "medium"},
    {"question": "What is the first step in the OECD due diligence framework?", "options": ["Identify risks", "Communicate findings", "Embed responsible conduct into policies", "Track progress with KPIs"], "correct": 2, "explanation": "Step 1 is to embed responsible business conduct into policies and management systems before starting to identify and address specific risks.", "difficulty": "medium"},
    {"question": "Which Muressons stakeholder group is most directly affected by Gobi region issues?", "options": ["Shareholders", "Tier-3 Mine Workers", "Software developers", "Retail customers"], "correct": 1, "explanation": "Tier-3 Mine Workers face the most acute risks including poor safety conditions, potential forced labour, and community displacement.", "difficulty": "medium"},
    {"question": "What turnover threshold triggers the UK Modern Slavery Act reporting requirement?", "options": ["£10M+", "£36M+", "£50M+", "£100M+"], "correct": 1, "explanation": "Companies with £36M+ annual turnover must publish a Modern Slavery Statement describing steps to prevent slavery.", "difficulty": "medium"},
    {"question": "What does the French Duty of Vigilance Law uniquely introduce?", "options": ["Criminal penalties for CEOs", "A legal duty of care for corporate human rights impacts", "Mandatory supply chain exit", "Carbon reporting requirements"], "correct": 1, "explanation": "The French law was the first to create a legal duty of care for companies regarding human rights impacts, allowing victims to sue for damages.", "difficulty": "medium"},
    {"question": "What is the 'paradox of withdrawal' in supply chain ethics?", "options": ["Companies profit more after leaving unethical suppliers", "Withdrawing from problematic suppliers can worsen worker conditions", "Withdrawal reduces regulatory risk but increases costs", "All companies eventually return to cheap suppliers"], "correct": 1, "explanation": "The paradox is that cutting ties can actually harm the workers you're trying to protect, as they lose income and may face worse conditions.", "difficulty": "medium"},
    {"question": "What does FPIC stand for?", "options": ["Federal Protection for Industrial Compliance", "Free, Prior, and Informed Consent", "Financial Protocol for Investment Clearing", "Framework for Public Interest Communication"], "correct": 1, "explanation": "FPIC ensures indigenous communities give free, informed consent before any operations on their lands.", "difficulty": "medium"},
    # ── HARD ──
    {"question": "What unique legal mechanism does the US Uyghur Forced Labor Prevention Act use?", "options": ["Criminal prosecution of importers", "Rebuttable presumption that all goods from Xinjiang use forced labour", "Sanctions against foreign governments", "Mandatory DNA testing of cotton products"], "correct": 1, "explanation": "The UFLPA presumes all goods from the Xinjiang region are made with forced labour. Importers must prove otherwise, shifting the burden of proof.", "difficulty": "hard"},
    {"question": "Under the CSDDD, what company size thresholds trigger the directive's requirements?", "options": ["Any EU company", "250+ employees and €50M+ turnover", "500+ employees and €150M+ turnover", "1000+ employees and €500M+ turnover"], "correct": 2, "explanation": "The CSDDD applies to EU companies with 500+ employees and €150M+ net turnover, and non-EU companies with €150M+ EU revenue.", "difficulty": "hard"},
    {"question": "Which social audit standards are mentioned for verifying supply chain compliance?", "options": ["ISO 9001 and ISO 14001", "SA8000 and SMETA", "B Corp and Fair Trade", "GRI and SASB"], "correct": 1, "explanation": "SA8000 (Social Accountability) and SMETA (Sedex Members Ethical Trade Audit) are independent social audit standards used to verify workplace conditions.", "difficulty": "hard"},
    {"question": "What specific environmental hazards affect Gobi region artisanal mining?", "options": ["Noise pollution only", "Deforestation and soil erosion", "Mercury and cyanide contamination of water tables", "Air pollution from diesel generators"], "correct": 2, "explanation": "Artisanal gold mining in the Gobi region uses mercury and cyanide for extraction, poisoning water tables and endangering local populations.", "difficulty": "hard"},
    {"question": "How deep can typical supply chain tiers extend, making visibility challenging?", "options": ["2-3 tiers", "5-10 tiers", "15-20 tiers", "50+ tiers"], "correct": 1, "explanation": "Complex global supply chains can extend 5-10 tiers deep, with visibility and accountability decreasing dramatically at each level.", "difficulty": "hard"},
    {"question": "What technology solution is mentioned for supply chain traceability?", "options": ["AI-powered cameras", "Blockchain-based traceability and worker voice apps", "Satellite monitoring", "RFID tags only"], "correct": 1, "explanation": "Blockchain-based traceability systems and worker voice apps (Ulula, Laborlink) are technology solutions for verifying ethical supply chains.", "difficulty": "hard"},
]
