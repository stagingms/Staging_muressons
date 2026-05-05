import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

def create_document():
    doc = docx.Document()
    
    # Title
    title = doc.add_heading('Muressons Simulation: New Modules Integration & Pedagogical Framework', 0)
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    
    doc.add_paragraph(
        "This comprehensive technical guide outlines the architecture, operationalization mechanics, "
        "theoretical foundations, and applied sample calculations for the 12 newly integrated simulation modules. "
        "These modules have been engineered to transform the core gameplay loop from a linear financial simulation "
        "into a highly reactive, non-linear, and pedagogically robust ESG (Environmental, Social, and Governance) learning environment."
    )
    
    modules = [
        {
            "name": "1. Biodiversity Engine (biodiversity_engine.py)",
            "purpose": "Decouples nature-related financial risks from generic carbon metrics to track real-world ecosystem dependencies.",
            "operationalisation": "Operates as a pure-function module (no side-effect I/O during execution). It consumes the current Business Unit (BU) states, carbon intensity, and player decisions to output an updated biodiversity state dictionary. Metrics tracked include Ecosystem Health Index (EHI), Species Risk Score, and Ecosystem Services Value (ESV). Degradation in EHI cascades into operational costs (nature's invoice) representing the commercial replacement cost of free ecosystem services.",
            "theory": "Based on the Dasgupta Review (2021) which treats nature as an asset with a depreciating stock, the TNFD (Taskforce on Nature-related Financial Disclosures) LEAP approach, and SBTN (Science Based Targets for Nature) classifications for freshwater and land impact.",
            "math": "Ecosystem Health Index (EHI) composite score (0-100):\nEHI_new = EHI_old - (NCD_delta * 0.5) - (deforestation * 2.0) + (habitat_integrity * 5.0) + restoration_bonus - (carbon_intensity * 0.1)\n\nExample Walkthrough:\nIf the current EHI is 65, and a recent expansion causes a Natural Capital Debt (NCD) increase of 10, deforestation of 2.5 hectares, while maintaining a 55% habitat integrity, with a carbon intensity of 50 and an active restoration bonus of +2.0:\nEHI_new = 65 - (10 * 0.5) - (2.5 * 2.0) + (0.55 * 5.0) + 2.0 - (50 * 0.1)\nEHI_new = 65 - 5.0 - 5.0 + 2.75 + 2.0 - 5.0 = 54.75"
        },
        {
            "name": "2. Balance Sheet Engine (balance_sheet.py)",
            "purpose": "Transforms the standard cash-flow treasury system into a holistic corporate balance sheet view.",
            "operationalisation": "Maintains a parallel state dictionary that is strictly updated at the end of each round. It maps tangible assets, debt provisions, and ESG-adjusted intangible assets (like brand reputation and social license). This module introduces debt covenants that trigger lender interventions if equity drops too low due to stranded asset write-downs.",
            "theory": "Anchored in IFRS/IAS 1 (Statement of Financial Position), the Integrated Reporting <IR> Framework's 6 capitals model, and the Modigliani-Miller theorem regarding capital structure relevance in an ESG-constrained market.",
            "math": "Stranded Asset Risk Write-down and Adjusted Equity:\nAdjusted_Equity = Total_Assets - (Standard_Liabilities + (Brown_Assets * Transition_Risk_Factor))\n\nExample Walkthrough:\nFor a company with $100M in total assets, $40M in standard liabilities, and $20M in highly carbon-intensive 'brown' assets facing a 50% transition risk probability factor (e.g., due to incoming carbon taxes):\nAdjusted_Equity = $100M - ($40M + ($20M * 0.5))\nAdjusted_Equity = $100M - ($40M + $10M) = $50M"
        },
        {
            "name": "3. Meadows Leverage Points Framework (meadows_leverage.py)",
            "purpose": "A pedagogical tracking system that measures the systemic depth of a student's interventions.",
            "operationalisation": "Functions as an analytical overlay rather than a direct game state mutator. It analyzes the event log and decision nodes chosen by the player, scoring them against the 12 leverage points. These scores are piped into the post-game debrief dashboards and facilitator teleprompter to visually show if students are treating symptoms (Level 12) or changing system goals (Level 3).",
            "theory": "Directly implements Donella Meadows' (2008) 'Thinking in Systems' 12 Leverage Points framework. It also categorizes feedback loops using Sterman (2000) and detects Senge (1990) system archetypes (e.g., 'Tragedy of the Commons').",
            "math": "Intervention Impact Score Calculation:\nImpact = Base_Decision_Value * (13 - Leverage_Point_Level)\n\nExample Walkthrough:\nIf a student chooses to optimize a constant parameter like adjusting an ad budget (Leverage Point Level 12), with a base value of 10:\nImpact = 10 * (13 - 12) = 10.\nConversely, if a student alters the fundamental rules of the system or its information flows (Leverage Point Level 3) with the same base effort:\nImpact = 10 * (13 - 3) = 100."
        },
        {
            "name": "4. Board Governance Minigame (board_governance.py)",
            "purpose": "Simulates internal corporate governance friction and the agency problem.",
            "operationalisation": "A dynamic minigame triggered during specific strategic gates (e.g., Round 3 and Round 6). The board composition is stored in `global_state['board_governance']`. To execute extreme pivots (like aggressive decarbonization), players must secure enough weighted votes from Independent, Executive, and Shareholder representative directors.",
            "theory": "Built on the Cadbury Report (1992) standards for board independence, the UK Corporate Governance Code (2018), and Bebchuk's (2005) agency theory regarding pay without performance.",
            "math": "Board Resolution Approval Confidence:\nApproval_Confidence = (Independent_Votes * 1.5 + Exec_Votes * 1.0) / Total_Weighted_Votes\n\nExample Walkthrough:\nA board consists of 4 Independents (weight 1.5) and 2 Executives (weight 1.0). If all members vote favorably:\nNumerator = (4 * 1.5) + (2 * 1.0) = 8.0\nTotal Possible = 8.0. Approval is 100%. If threshold > 50%, the resolution passes. If Executives vote No, Confidence drops to (6.0 / 8.0) = 75%, passing with friction."
        },
        {
            "name": "5. Organisational Politics Layer (org_politics.py)",
            "purpose": "Injects internal stakeholder friction, ensuring that decisions are not executed in a vacuum.",
            "operationalisation": "Tracks the satisfaction, alignment score, and political influence budget of 5 C-suite members. Players must expend 'capital' to build coalitions. Initiatives require support from at least 3 out of 5 members. Launching an initiative without a coalition triggers massive implementation delays and OPEX cost overruns.",
            "theory": "Informed by Pfeffer (1992) on managing with power, Cyert & March's (1963) behavioral theory of the firm, and Mintzberg (1983).",
            "math": "Coalition Support Score:\nSupport = Σ (C_Suite_Member_Influence * Alignment_Score)\n\nExample Walkthrough:\nA player pushes a costly ESG initiative. The CFO has high influence (0.4) but low alignment (0.2). The COO has medium influence (0.3) but high alignment (0.9).\nSupport = (0.4 * 0.2) + (0.3 * 0.9) = 0.08 + 0.27 = 0.35.\nIf the threshold to prevent implementation delays is 0.5, the initiative will launch but suffer severe friction penalties."
        },
        {
            "name": "6. TCFD Scenarios Engine (tcfd_scenarios.py)",
            "purpose": "Provides a rigorous transition risk and physical risk forecasting tool.",
            "operationalisation": "Functions strictly as an analytical tool that projects forward-looking stress tests without mutating the immediate game state. Players invoke it to visualize how their current asset portfolio holds up against 1.5°C, 2°C, and 4°C global warming pathways over a simulated 10-year horizon.",
            "theory": "Directly compliant with the Task Force on Climate-related Financial Disclosures (TCFD) 2017 recommendations, Network for Greening the Financial System (NGFS) scenarios, and IEA WEO baselines.",
            "math": "Value at Risk (VaR) under a 2°C Scenario:\nVaR_2C = Current_Portfolio_Value - (Carbon_Tax_Projections + Physical_Damage_Estimates)\n\nExample Walkthrough:\nA $500M portfolio is stress-tested. The 2°C pathway models a $90/ton carbon tax resulting in $45M in tax liabilities, and increased severe weather events mapping to $15M in physical asset damage.\nVaR_2C = $500M - ($45M + $15M) = $440M Projected Value (a 12% impairment)."
        },
        {
            "name": "7. Regulatory Sandbox Mode (regulatory_sandbox.py)",
            "purpose": "An expert-tier capability allowing facilitators and students to design and inject custom regulations.",
            "operationalisation": "Intercepts the main simulation loop by applying custom modifier functions. Users can impose custom carbon taxes, extended producer responsibility (EPR) laws, or strict property rights. The module calculates the immediate shock and cascading secondary effects on market share and profitability.",
            "theory": "Based on Pigouvian taxation (Pigou, 1920), Coasian property rights and externalities (Coase, 1960), and polycentric governance models (Ostrom, 2009).",
            "math": "Pigouvian Tax Penalty Injection:\nPenalty = BU_Carbon_Emissions * Custom_Tax_Rate_Per_Ton\n\nExample Walkthrough:\nA facilitator introduces an aggressive $85/ton carbon tax to a session. A Business Unit emitting 50,000 tons of CO2e annually:\nPenalty = 50,000 * 85 = $4,250,000.\nThis is immediately deducted from the corporate treasury and hits the BU's net margin, forcing an immediate pivot in player strategy."
        },
        {
            "name": "8. Cross-Player Market Dynamics (market_dynamics.py)",
            "purpose": "Replaces absolute scoring with a relative competitive environment for multiplayer cohorts.",
            "operationalisation": "Maintains a shared 'market_state' across all active players in a session. At the end of every round, it calculates relative performance. Players competing for the same talent pool or market share see their costs increase if a competitor heavily out-invests them in reputation or salaries.",
            "theory": "Rooted in Porter’s Five Forces (1980), Schelling’s strategy of conflict (1960), and Akerlof’s (1970) market for lemons (information asymmetry).",
            "math": "Market Share Reallocation:\nNew_Share = Base_Share + (Relative_Reputation_Advantage * 0.1) - Information_Asymmetry_Penalty\n\nExample Walkthrough:\nPlayer A has a base share of 20%. Their reputation score is 80, while the cohort average is 60. They have transparent reporting, so asymmetry penalty is 0.\nNew_Share = 20% + ( (80 - 60) / 100 * 0.1 ) - 0\nNew_Share = 0.20 + (0.2 * 0.1) = 0.22 (22% Market Share)."
        },
        {
            "name": "9. AI-Driven NPC Stakeholders (npc_stakeholders.py)",
            "purpose": "Provides highly reactive, lifelike pressure from activists, regulators, and media.",
            "operationalisation": "A hybrid engine. It uses deterministic math to calculate 'Salience'. If salience breaches a critical threshold, it triggers an LLM generation pipeline to formulate custom-tailored dialogue, press releases, or regulatory warnings based on the player's specific missteps.",
            "theory": "Based on Mitchell et al. (1997) Stakeholder Salience framework (Power, Legitimacy, Urgency) and Fassin's (2009) theories on stakeholder management.",
            "math": "Stakeholder Salience Index:\nSalience = Power_Score + Legitimacy_Score + Urgency_Score\n\nExample Walkthrough:\nAn Activist Investor coalition forms. Power is high (3), their cause is legitimate due to a recent pollution leak (2), and the deadline for the AGM is near, making it urgent (5).\nSalience = 3 + 2 + 5 = 10.\nA score over 8 triggers an active 'Crisis Event' in the UI with LLM-generated demands."
        },
        {
            "name": "10. Dynamic Case Injection (dynamic_cases.py)",
            "purpose": "Contextualizes learning by surfacing the most relevant real-world case studies at the exact moment of failure.",
            "operationalisation": "Replaces the static case-bank. Using vector matching and LLM generation, it analyzes the player's current industry, size, and specific crisis (e.g., greenwashing accusation) and generates a brief mimicking real historical events (like the DWS greenwashing raid or BP Deepwater Horizon) formatted for immediate consumption.",
            "theory": "Supported by the Transfer of Training framework (Baldwin & Ford, 1988), Kolb’s (1984) experiential learning cycle, and Schön’s reflective practice.",
            "math": "Transfer Relevance Score Calculation:\nRelevance = (Industry_Vector_Match * 0.6) + (Crisis_Type_Match * 0.4)\n\nExample Walkthrough:\nA pharmaceutical player faces a supply chain disruption. A historical case study on a tech company supply chain is evaluated.\nIndustry Match (Pharma vs Tech) = 0.2. Crisis Match (Supply Chain vs Supply Chain) = 0.9.\nRelevance = (0.2 * 0.6) + (0.9 * 0.4) = 0.12 + 0.36 = 0.48. (Score is too low; engine searches for a better fit or generates a generic pharma-specific one)."
        },
        {
            "name": "11. Non-Linear Branching Engine (branching_engine.py)",
            "purpose": "Creates replayability and personalized difficulty curves by analyzing early-game behavior.",
            "operationalisation": "At the conclusion of Round 5, this pure-function engine analyzes all previous choices to assign a 'strategic archetype' (e.g., Pioneer, Compliant, Laggard). This classification fundamentally alters the narrative events, crises, and difficulty parameters for Rounds 6 through 10.",
            "theory": "Follows Mintzberg’s (1987) Strategy as Pattern and Snowden’s (2007) Cynefin Framework to transition players from complicated (predictable) environments to complex (unpredictable) ones based on their appetite for risk.",
            "math": "Archetype Classification Ratio:\nExploration_Ratio = Innovative_Decisions_Count / Total_Decisions\n\nExample Walkthrough:\nA player makes 15 decisions in the first half of the game. 12 of them are high-risk, innovative ESG pivots.\nExploration_Ratio = 12 / 15 = 0.8.\nBecause the ratio > 0.7, the engine locks them into the 'Pioneer' branch. Late-game events will feature cutting-edge tech failures rather than basic compliance fines."
        },
        {
            "name": "12. Supply Chain Network Model (supply_chain_network.py)",
            "purpose": "Models cascading risks deep within the value chain, rather than treating suppliers as a generic toggle.",
            "operationalisation": "Maintains a multi-tier directed graph (Tier 1, 2, and 3 suppliers). It tracks visibility and dependency across the network. A failure at Tier 3 (e.g., a localized flood or labor strike) cascades upward, penalized by the lack of visibility the player has invested in.",
            "theory": "Integrates Christopher & Peck’s (2004) Supply Chain Resilience framework, Chopra & Sodhi (2004) risk matrices, and compliance with the EU Corporate Sustainability Due Diligence Directive (CS3D).",
            "math": "Cascading Risk Exposure Calculation:\nTier_1_Risk = Direct_Risk + (Tier_2_Risk * Visibility_Discount) + (Tier_3_Risk * (Visibility_Discount^2))\n\nExample Walkthrough:\nA company faces 10% direct operational risk. Tier 2 suppliers face 40% risk, and Tier 3 faces 80% risk. The company has poor visibility (0.5 discount factor meaning 50% of risk bleeds through).\nTier_1_Risk = 10% + (40% * 0.5) + (80% * (0.5^2))\nTier_1_Risk = 10% + 20% + (80% * 0.25)\nTier_1_Risk = 10% + 20% + 20% = 50% Total Cascaded Risk Exposure."
        }
    ]

    for idx, mod in enumerate(modules):
        doc.add_heading(mod["name"], level=1)
        
        doc.add_heading('Purpose', level=2)
        doc.add_paragraph(mod["purpose"])
        
        doc.add_heading('Integration & Operationalisation', level=2)
        doc.add_paragraph(mod["operationalisation"])
        
        doc.add_heading('Theoretical Foundation', level=2)
        doc.add_paragraph(mod["theory"])
        
        doc.add_heading('Sample Calculations & Walkthrough', level=2)
        p = doc.add_paragraph()
        p.add_run(mod["math"]).font.name = 'Courier New'
        
        if idx < len(modules) - 1:
            doc.add_page_break()

    doc.save(r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim\Muressons_Modules_Technical_Guide.docx")
    print("Document successfully generated at c:\\Users\\Home\\.gemini\\antigravity\\scratch\\muressons-sim\\Muressons_Modules_Technical_Guide.docx")

if __name__ == '__main__':
    create_document()
