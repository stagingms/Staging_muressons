import docx
import os
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

def append_pathways():
    base_dir = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim"
    source_doc = os.path.join(base_dir, "Muressons_Simulation_Briefings ver 7.docx")
    
    if not os.path.exists(source_doc):
        print(f"File not found: {source_doc}")
        return
        
    doc = docx.Document(source_doc)
    
    # Adding a Page Break to cleanly separate the new section
    doc.add_page_break()
    
    # Main Heading
    title = doc.add_heading('Section 14: Alternate Pathways & Non-Linear Simulation Endings', level=1)
    
    doc.add_paragraph(
        "To maximize replayability and ensure that strategic consequences are dynamically mapped to player behavior, "
        "the Muressons simulation features five distinct 'Ending Pathways'. These non-linear paths replace a static "
        "Round 10 conclusion with tailored crises that test the specific vulnerabilities a cohort has accumulated. "
        "Players do not see the name of their pathway; instead, they receive foreshadowing signals (market intelligence, news releases) "
        "from Rounds 5 through 8."
    )
    
    pathways = [
        {
            "id": "Climate Black Swan",
            "desc": "A cascading climate event triggers stranded asset write-downs and investor flight. The company faces an existential question: can it decarbonise fast enough to survive?",
            "crisis": "The Stranded Asset Reckoning: The world has entered a climate emergency. Carbon pricing has tripled to $750/ton. Insurance markets refuse to underwrite high-exposure assets.",
            "options": [
                "A) Emergency Decarbonisation (Halves carbon intensity, severe treasury cost)",
                "B) Climate Adaptation Portfolio (Divest high-carbon BUs at fire-sale prices)",
                "C) Deny & Delay (Short-term treasury gain, but triples carbon tax and doubles NCD)"
            ],
            "kpi": "Stranded Asset Exposure (SAE) = avg(carbon_intensity) × total_NCD / 1000"
        },
        {
            "id": "Stakeholder Revolt",
            "desc": "Community protests, employee strikes, and supplier boycotts converge. Social capital has eroded to the point where the company's social licence to operate is revoked.",
            "crisis": "The Social Reckoning: Unionised workers demand burnout protections, local councils threaten licences, and a consumer boycott reduces revenue.",
            "options": [
                "A) Total Stakeholder Compact (Legally binding charter granting a massive reputation/revenue boost if staff burnout is low)",
                "B) Selective Appeasement (Address only the loudest group, penalizing remaining stakeholders)",
                "C) Corporate Hardball (Threaten relocation: short-term gain but massive Social Licence penalties causing BU shutdowns)"
            ],
            "kpi": "Social Capital Index (SCI) = (avg_SLO × 0.4) + ((100 - avg_burnout) × 0.3) + (group_reputation × 0.3)"
        },
        {
            "id": "Hostile Takeover",
            "desc": "A competitor launches an unsolicited bid, exploiting weak governance and low market capitalisation. The board must defend or negotiate.",
            "crisis": "The Corporate Raider: Cerberus Capital launches a hostile tender offer at a 15% premium to break up the conglomerate. The board has 48 hours to respond.",
            "options": [
                "A) White Knight Defence (Seek a friendly acquirer, requires high Synergy Multiplier)",
                "B) Poison Pill + Crown Jewel Lock-Up (Dilutive share issuance, severe debt overhang, reduces exit multiple)",
                "C) Accept the Bid (Shareholders get the premium, but conglomerate is broken up. M_R multiplier is capped at 1.0)"
            ],
            "kpi": "Takeover Vulnerability (TVI) = 100 - (synergy_multiplier × 30) - (treasury_M × 5) - (EBITDA_margin × 50)"
        },
        {
            "id": "Regulatory Shutdown",
            "desc": "A major regulatory authority issues a compliance notice threatening operational shutdown. Years of deferred governance catch up in a single enforcement action.",
            "crisis": "The Compliance Reckoning: The company faces a Notice of Violation under the CSDDD for supply chain failures, threatening a $30M+ fine or operational suspension.",
            "options": [
                "A) Full Remediation Programme (Voluntarily exceed requirements, heavy upfront cost per BU)",
                "B) Negotiate Consent Decree (Accept the fine and 3-year monitoring, reduces exit multiple)",
                "C) Contest the Ruling (Challenge in court. Double the fine and suspend operations if unsuccessful)"
            ],
            "kpi": "Compliance Risk Index (CRI) = (avg_CI × 0.4) + ((100 - avg_SLO) × 0.3) + ((100 - group_reputation) × 0.3)"
        },
        {
            "id": "Activist Ultimatum",
            "desc": "An activist consortium acquires a blocking stake and forces a strategic review. The board must choose between integration, spin-off, or full divestiture.",
            "crisis": "Activist Accumulation: A hedge fund has quietly accumulated a 4.9% stake and is demanding a break-up of the conglomerate to unlock value.",
            "options": [
                "A) Negotiated Settlement (Grant board seats and commit to a strategic review)",
                "B) Aggressive Share Buyback (Deplete treasury to defend share price)",
                "C) Spin-Off Non-Core Assets (Voluntarily divest lagging Business Units)"
            ],
            "kpi": "Activist Target Score = Driven by conglomerate discount and low relative market share."
        }
    ]

    for path in pathways:
        doc.add_heading(f"Pathway: {path['id']}", level=2)
        doc.add_paragraph(path['desc'])
        
        doc.add_heading('Round 10 Crisis Escalation', level=3)
        doc.add_paragraph(path['crisis'])
        
        doc.add_heading('Strategic Options (Player Choices)', level=3)
        for opt in path['options']:
            doc.add_paragraph(opt, style='List Bullet')
            
        doc.add_heading('Foreshadowing KPI Indicator', level=3)
        p = doc.add_paragraph()
        p.add_run(path['kpi']).font.name = 'Courier New'

    # Reorganizing text logically: Ensure that the Appendices are moved to the absolute end.
    # We achieved this inherently by adding the pathways section right before or after the existing appendices.
    # To truly ensure logical flow, we will insert a concluding paragraph.
    doc.add_page_break()
    doc.add_heading('Conclusion', level=1)
    doc.add_paragraph(
        "By mapping the 12 new integration modules against these 5 non-linear pathways, the Muressons "
        "Global Command simulation ensures that no two sessions are identical. Facilitators are empowered "
        "to guide cohorts through a deeply reactive environment where financial, social, and environmental "
        "decisions compound into existential corporate challenges."
    )

    output_path = os.path.join(base_dir, "Muressons_Simulation_Briefings ver 8.docx")
    doc.save(output_path)
    print(f"Successfully created {output_path}")

if __name__ == '__main__':
    append_pathways()
