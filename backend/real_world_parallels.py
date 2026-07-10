from __future__ import annotations
"""
Muressons Global Corporation — Real World Parallel Cards
Case briefs linking each round to a real corporate event.
Bridges simulation-reality transfer gap (Baldwin & Ford, 1988).

Visibility: Always in teleprompter. Player-visible only if facilitator enables.
"""

REAL_WORLD_PARALLELS = {
    1: {
        "round": 1,
        "title": "Volkswagen Dieselgate (2015)",
        "icon": "🚗",
        "company": "Volkswagen AG",
        "dilemma": "ESG Audit Depth",
        "brief": (
            "In 2015, the US Environmental Protection Agency discovered that Volkswagen had "
            "installed 'defeat device' software in 11 million diesel vehicles worldwide, "
            "enabling them to cheat emissions tests. The scandal revealed systematic governance "
            "failures — internal audits had flagged anomalies but were overridden by management. "
            "A deeper, forensic audit culture could have surfaced the fraud years earlier."
        ),
        "simulation_parallel": (
            "Like Muressons' R1 choice, VW faced a diagnostic decision: invest in thorough "
            "compliance checks or accept surface-level assurances. The 'electronics_blindspot' "
            "flag in the simulation mirrors VW's willful blindness to defeat devices."
        ),
        "outcome": (
            "VW paid over €30 billion in fines, settlements, and recalls. CEO Martin Winterkorn "
            "resigned and was later charged with fraud. The company's share price dropped 37% "
            "in two days. A $3M audit would have been the best investment in VW's history."
        ),
        "key_lesson": "The cost of not knowing always exceeds the cost of finding out.",
        "theory_link": "Argyris (1977) Double-Loop Learning: VW's culture suppressed the 'governing variables' that should have triggered alarm.",
        "reference": "United States Environmental Protection Agency. (2015). Notice of Violation to Volkswagen AG. https://www.epa.gov/enforcement/volkswagen-clean-air-act-civil-settlement",
    },
    2: {
        "round": 2,
        "title": "Danone's Double Materiality Journey (2020-2023)",
        "icon": "🥛",
        "company": "Danone SA",
        "dilemma": "Double Materiality Alignment",
        "brief": (
            "Danone became the first listed French company to adopt 'Entreprise à Mission' "
            "status in 2020, embedding social and environmental objectives into its corporate "
            "charter. CEO Emmanuel Faber championed full materiality alignment — but activist "
            "investors argued this came at the expense of shareholder returns."
        ),
        "simulation_parallel": (
            "Danone's dilemma mirrors R2's Option A (Full Alignment) vs Option C (Business as "
            "Usual). Faber chose full alignment but was ousted in 2021 by activists who felt "
            "the company was under-performing on financial materiality."
        ),
        "outcome": (
            "Faber was removed as CEO in March 2021. His successor Antoine de Saint-Affrique "
            "took a more balanced approach. The case shows that materiality alignment requires "
            "both conviction AND financial performance — purpose without profit is unsustainable."
        ),
        "key_lesson": "Double materiality is a lens, not a religion. Align ESG with financial performance or lose your mandate.",
        "theory_link": "Freeman (1984) Stakeholder Theory: Balancing purpose and profit requires managing competing stakeholder expectations simultaneously.",
        "reference": "Danone SA. (2020). Danone Becomes the First Listed Company to Adopt the Entreprise à Mission Model. https://www.danone.com/media/news-list/danone-becomes-first-listed-company-to-adopt-entreprise-a-mission.html",
    },
    3: {
        "round": 3,
        "title": "Ørsted's Green Transformation (2017-2023)",
        "icon": "🌊",
        "company": "Ørsted A/S (formerly DONG Energy)",
        "dilemma": "Scope 3 Decarbonisation",
        "brief": (
            "In 2017, Danish Oil and Natural Gas (DONG) Energy rebranded as Ørsted and "
            "committed to divesting all fossil fuel assets. The company sold its upstream "
            "oil and gas business, issued green bonds to fund offshore wind expansion, "
            "and reduced carbon intensity by 87% in six years."
        ),
        "simulation_parallel": (
            "Ørsted's transformation mirrors R3's Option A (supply chain transformation) "
            "combined with Option B (green bond issuance). The company accepted massive "
            "short-term disruption for long-term strategic positioning."
        ),
        "outcome": (
            "Ørsted's market capitalisation increased from €10B to €60B+ between 2017-2021. "
            "The company became the world's largest offshore wind developer. Their green bonds "
            "were oversubscribed 3×, demonstrating investor appetite for credible transition stories."
        ),
        "key_lesson": "Genuine decarbonisation creates shareholder value. Carbon offsets (Option C) are not a substitute for structural change.",
        "theory_link": "Teece (2007) Dynamic Capabilities: Ørsted's sensing, seizing, and transforming of its business model exemplifies strategic agility.",
        "reference": "Ørsted A/S. (2023). Our Green Transformation. https://orsted.com/en/who-we-are/our-purpose/our-green-transformation",
    },
    4: {
        "round": 4,
        "title": "Nike's Supply Chain Scandal (1990s)",
        "icon": "👟",
        "company": "Nike, Inc.",
        "dilemma": "Crisis Contagion & Reputation",
        "brief": (
            "In the 1990s, Nike faced devastating revelations about child labour and sweatshop "
            "conditions in its Southeast Asian supplier factories. The crisis began with a single "
            "factory exposé but rapidly spread to become a symbol of corporate exploitation. "
            "Nike's initial response — denial and deflection — amplified the contagion."
        ),
        "simulation_parallel": (
            "Nike's experience mirrors R4's contagion engine. Their initial 'Option C' (deny) "
            "approach doubled the crisis severity. When they eventually chose transparency "
            "(Option A), publishing factory audits and supplier lists, reputation recovery began."
        ),
        "outcome": (
            "Nike lost an estimated $1.5B in market value during the peak crisis. Recovery took "
            "nearly a decade. Today, Nike is considered a leader in supply chain transparency — "
            "but only because the crisis forced transformation. The company now publishes its "
            "complete supplier list and requires third-party audits."
        ),
        "key_lesson": "Reputation contagion follows a sigmoid curve: slow start, rapid middle, saturating end. Early transparency flattens the curve.",
        "theory_link": "Kahneman (2011) System 1/2: Nike's initial denial was a System 1 (fast, defensive) response. Effective crisis management requires System 2 (slow, analytical) thinking.",
        "reference": "Locke, R.M. (2003). The Promise and Perils of Globalization: The Case of Nike. MIT Working Paper. https://doi.org/10.2139/ssrn.427500",
    },
    5: {
        "round": 5,
        "title": "Unilever's Climate Adaptation (2010-2020)",
        "icon": "🌿",
        "company": "Unilever PLC",
        "dilemma": "Physical Climate Risk",
        "brief": (
            "Unilever's Sustainable Living Plan (2010) included commitments to halve "
            "environmental footprint while doubling business size. In Indonesia, the company "
            "invested in smallholder farmer resilience programs — nature-based solutions that "
            "reduced supply chain disruption from floods and droughts by 30%."
        ),
        "simulation_parallel": (
            "Unilever's approach mirrors R5's Option B (nature-based resilience). Rather than "
            "hard engineering (Option A) or insurance only (Option C), they invested in "
            "ecosystem restoration that provided both climate adaptation and natural capital benefits."
        ),
        "outcome": (
            "Unilever's sustainable brands grew 69% faster than the rest of the business. "
            "The nature-based approach reduced NCD while building community resilience. "
            "Paul Polman's tenure demonstrated that adaptation and growth are compatible."
        ),
        "key_lesson": "Nature-based solutions provide resilience AND reduce natural capital debt. Hard engineering protects assets; ecosystems protect systems.",
        "theory_link": "Taleb (2012) Antifragility: Unilever's ecosystem approach gets stronger from stress, unlike hard infrastructure which degrades.",
        "reference": "Unilever PLC. (2020). Unilever Sustainable Living Plan 2010-2020: Summary of 10 Years' Progress. https://www.unilever.com/planet-and-society/sustainability-reporting-centre/",
    },
    6: {
        "round": 6,
        "title": "Amazon's AI Recruitment Tool Bias (2018)",
        "icon": "🤖",
        "company": "Amazon.com, Inc.",
        "dilemma": "Algorithmic Ethics",
        "brief": (
            "In 2018, Amazon scrapped an AI recruitment tool after discovering it systematically "
            "discriminated against women. The algorithm, trained on 10 years of predominantly "
            "male resumes, learned to penalise CVs containing the word 'women's' and downgrade "
            "graduates of all-women's colleges."
        ),
        "simulation_parallel": (
            "Amazon ultimately chose the equivalent of R6's Option B (ethical overhaul) — "
            "scrapping the tool entirely. However, they initially attempted Option C (quiet patch) "
            "before the bias was too systemic to fix incrementally."
        ),
        "outcome": (
            "Amazon disbanded the team and never deployed the tool. The case became a landmark "
            "in AI ethics education. The EU AI Act (2024) now classifies recruitment AI as "
            "'high-risk', requiring conformity assessments and human oversight."
        ),
        "key_lesson": "Algorithmic bias is a leadership problem, not a technical one. The training data reflects the culture that created it.",
        "theory_link": "Argyris (1977): Amazon's bias was embedded in 'governing variables' — the historical hiring patterns that the AI internalised as 'normal'.",
        "reference": "Dastin, J. (2018). Amazon Scraps Secret AI Recruiting Tool That Showed Bias Against Women. Reuters. https://www.reuters.com/article/us-amazon-com-jobs-automation-insight-idUSKCN1MK08G",
    },
    7: {
        "round": 7,
        "title": "Interface Carpets' Circular Transformation (1994-2020)",
        "icon": "♻️",
        "company": "Interface, Inc.",
        "dilemma": "Circular Economy",
        "brief": (
            "In 1994, Interface founder Ray Anderson had an 'epiphany' after reading Paul "
            "Hawken's 'The Ecology of Commerce'. He committed to 'Mission Zero' — zero "
            "environmental footprint by 2020. The company redesigned products for disassembly, "
            "pioneered carpet tile take-back programs, and achieved 96% waste diversion."
        ),
        "simulation_parallel": (
            "Interface chose the equivalent of R7's Option A (full circular redesign). "
            "The $10M+ investment seemed radical in 1994 but created lasting competitive "
            "advantage through material cost reduction and brand differentiation."
        ),
        "outcome": (
            "Interface achieved Mission Zero in 2020. GHG emissions fell 96%, renewable energy "
            "reached 89%, and water use dropped 89%. The company's market position strengthened "
            "as governments mandated extended producer responsibility."
        ),
        "key_lesson": "Circular economy is not a cost — it's a competitive moat. First-movers set the standards that followers must meet.",
        "theory_link": "Barney (1991) VRIO: Interface's circular capabilities are Valuable, Rare, Inimitable, and Organisation-embedded — a textbook sustainable competitive advantage.",
        "reference": "Anderson, R.C. (2009). Confessions of a Radical Industrialist. St. Martin's Press. https://www.interface.com/us/en/about/mission-zero",
    },
    8: {
        "round": 8,
        "title": "Coca-Cola's Water Crisis in India (2003-2007)",
        "icon": "💧",
        "company": "The Coca-Cola Company",
        "dilemma": "Water Stewardship & Social License",
        "brief": (
            "Coca-Cola's bottling plant in Plachimada, Kerala, was shut down in 2004 after "
            "local communities accused the company of depleting groundwater and contaminating "
            "wells. The Kerala High Court ruled that the company had violated the public trust "
            "doctrine — groundwater belongs to the community, not the corporation."
        ),
        "simulation_parallel": (
            "Coca-Cola initially chose the equivalent of R8's Option B (prioritise high-value "
            "operations). The social license collapse in 'left behind' communities mirrors "
            "the SLO penalty in the simulation."
        ),
        "outcome": (
            "The Plachimada plant remains closed. Coca-Cola subsequently invested $2B+ globally "
            "in water stewardship programs, achieving 'water positive' status in 2021. "
            "The crisis transformed the company's approach to community water rights."
        ),
        "key_lesson": "Water is a human right before it is a production input. Social license is revoked faster than it is earned.",
        "theory_link": "Freeman (1984): The Plachimada community shifted from 'Monitor' to 'Manage Closely' overnight — stakeholder salience migration in action.",
        "reference": "Hills, J. & Welford, R. (2005). Coca-Cola and Water in India. Corporate Social Responsibility and Environmental Management, 12(3), 168-177. https://doi.org/10.1002/csr.97",
    },
    9: {
        "round": 9,
        "title": "Enel's Just Transition (2019-2025)",
        "icon": "⚡",
        "company": "Enel SpA",
        "dilemma": "Just Transition",
        "brief": (
            "Italian utility Enel committed to closing all coal plants by 2027, affecting "
            "thousands of workers. Rather than mass layoffs, Enel invested €10B in reskilling "
            "programs, renewable energy job creation, and community transition funds in coal "
            "regions across Italy, Spain, and Chile."
        ),
        "simulation_parallel": (
            "Enel's approach combines R9's Option B (managed transition) and Option C "
            "(community investment fund). The company explicitly rejected Option A (immediate "
            "closure) on ethical grounds, arguing that decarbonisation without justice is 'just "
            "another form of extraction'."
        ),
        "outcome": (
            "Enel retrained 3,000+ workers and created 5× more jobs in renewables than were "
            "lost in coal. Community satisfaction scores in transition regions exceeded pre-closure "
            "levels. The ILO cited Enel as a global best practice for just transition."
        ),
        "key_lesson": "Just Transition is not charity — it's risk management. Companies that abandon communities create future regulatory and social liabilities.",
        "theory_link": "Rawls (1971) Veil of Ignorance + Sen (1999) Capabilities: Would you choose mass layoffs if you didn't know whether you were the CEO or the coal worker?",
        "reference": "Enel SpA. (2022). Just Transition Report 2022. https://www.enel.com/company/stories/articles/2022/09/just-transition",
    },
    10: {
        "round": 10,
        "title": "Danone's Activist Investor Battle (2021)",
        "icon": "🦈",
        "company": "Danone SA",
        "dilemma": "Activist Pressure & Terminal Valuation",
        "brief": (
            "In early 2021, activist investors Bluebell Capital and Artisan Partners forced "
            "the ouster of Danone CEO Emmanuel Faber, arguing that his ESG-focused strategy "
            "had underperformed peers on financial returns. The campaign culminated in a proxy "
            "fight that split the board."
        ),
        "simulation_parallel": (
            "Danone's crisis mirrors R10's Activist Ultimatum pathway. The board faced the "
            "same three options: defend integration (Option A), spin off underperformers "
            "(Option B), or accept the activist's agenda (Option C)."
        ),
        "outcome": (
            "Faber was removed. New CEO de Saint-Affrique maintained ESG commitments but "
            "refocused on operational efficiency. The case demonstrates that sustainability "
            "strategy must deliver financial returns to survive activist pressure — M_R "
            "without EBITDA is a target, not a fortress."
        ),
        "key_lesson": "Terminal value = EBITDA × Exit Multiple × M_R. All three matter. Purpose without profit is unsustainable; profit without purpose is vulnerable.",
        "theory_link": "Barney (1991) VRIO + Porter (1985) Value Chain: Synergy is a defensive weapon — conglomerate premium makes break-up less attractive.",
        "reference": "Bluebell Capital Partners. (2021). Open Letter to the Board of Directors of Danone SA. https://www.ft.com/content/cf31353f-19b1-4c89-8a66-d4c36ccd0ed6",
    },
}


def get_parallel(round_number: int) -> dict | None:
    """Return the real-world parallel card for a round."""
    return REAL_WORLD_PARALLELS.get(round_number)


def get_all_parallels() -> dict[int, dict]:
    """Return all parallel cards."""
    return dict(REAL_WORLD_PARALLELS)
