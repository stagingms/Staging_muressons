import re
import json

file_path = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim\frontend\app\components\RoundBriefing.js"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

def parse_section(section_name):
    match = re.search(f"export const {section_name} = \{{(.*?)\n\}};", content, re.DOTALL)
    if not match: return {}
    
    body = match.group(1)
    rounds = {}
    
    round_matches = list(re.finditer(r"^\s+(\d+):\s+\{", body, re.MULTILINE))
    
    for i, rm in enumerate(round_matches):
        end = round_matches[i+1].start() if i + 1 < len(round_matches) else len(body)
        round_str = body[rm.start():end]
        
        title_m = re.search(r"title:\s*'([^']+)'", round_str)
        title = title_m.group(1) if title_m else ""
        
        theme_m = re.search(r"theme:\s*'([^']+)'", round_str)
        theme = theme_m.group(1) if theme_m else ""
        
        narrative_m = re.search(r"narrative:\s*\[(.*?)\]", round_str, re.DOTALL)
        narrative_texts = []
        if narrative_m:
            narrative_arr_str = narrative_m.group(1)
            strs = re.findall(r"'((?:\\'|[^'])*)'", narrative_arr_str)
            narrative_texts = [s.replace("\\'", "'") for s in strs]
            
        rounds[int(rm.group(1))] = {
            "title": title,
            "theme": theme,
            "narratives": narrative_texts
        }
    return rounds

briefings = parse_section("BRIEFINGS")
healthcare = parse_section("HEALTHCARE_BRIEFINGS")
sdg = parse_section("SDG_BRIEFINGS")

out_md = []

out_md.append("# Muressons Global Corporation — Briefing Screens & Game Logic")
out_md.append("\nThis document compiles the core narrative information, decision paradigms, side tracks, and alternate pathways available in the Muressons Global Corporation simulation.\n")

out_md.append("## Simulation Flow Map\n")
out_md.append("```mermaid")
out_md.append("flowchart TD")
out_md.append("    %% Main Rounds")
out_md.append("    R1[\"Round 1: Foundations\"] --> R2[\"Round 2: Double Materiality\"]")
out_md.append("    R2 --> R3[\"Round 3: Scope 3 Emissions\"]")
out_md.append("    R3 --> R4[\"Round 4: Contagion\"]")
out_md.append("    R4 --> R5[\"Round 5: Climate Event\"]")
out_md.append("    R5 --> R6[\"Round 6: AI Bias\"]")
out_md.append("    R6 --> R7[\"Round 7: Circularity\"]")
out_md.append("    R7 --> R8[\"Round 8: Blue Stress\"]")
out_md.append("    R8 --> R9[\"Round 9: Just Transition\"]")
out_md.append("    ")
out_md.append("    %% Alternate Ending Pathways")
out_md.append("    R9 --> R10A[\"R10: Activist Ultimatum\"]")
out_md.append("    R9 --> R10B[\"R10: Climate Black Swan\"]")
out_md.append("    R9 --> R10C[\"R10: Stakeholder Revolt\"]")
out_md.append("    R9 --> R10D[\"R10: Hostile Takeover\"]")
out_md.append("    R9 --> R10E[\"R10: Regulatory Shutdown\"]")
out_md.append("    ")
out_md.append("    %% Side Tracks (Run parallel)")
out_md.append("    subgraph \"Parallel Curricula (Side Tracks)\"")
out_md.append("        ST1[\"Supply Chain (7 Rounds)\"]")
out_md.append("        ST2[\"Ethics & Sustainability (5 Rounds)\"]")
out_md.append("        ST3[\"Stakeholder Mgmt (4 Rounds)\"]")
out_md.append("        ST4[\"Sustainability Reporting (5 Rounds)\"]")
out_md.append("    end")
out_md.append("    ")
out_md.append("    R1 -.->|Facilitator Assigned| ST1")
out_md.append("    R1 -.->|Facilitator Assigned| ST2")
out_md.append("    R1 -.->|Facilitator Assigned| ST3")
out_md.append("    R1 -.->|Facilitator Assigned| ST4")
out_md.append("```\n")
out_md.append("---\n")

out_md.append("## 1. Decision Paradigms")
out_md.append("Decision Paradigms govern how choices are presented and evaluated during the simulation:")
out_md.append("- **`legacy_abc`**: The classic paradigm featuring standard 3-option (A/B/C) multiple-choice decision gates per round.")
out_md.append("- **`multi_toggles`**: Advanced decision gating where players configure multiple sliders/toggles across different pillars instead of a single A/B/C choice.")
out_md.append("- **`advanced_climate`**: A paradigm focused heavily on decarbonization, carbon pricing, and physical/transition climate risks.")
out_md.append("- **`healthcare`**: A specialized paradigm reshaping the simulation into a healthcare network (Hospitals, Clinics, Specialised Care, Telehealth) managing patient outcomes and clinical compliance.")
out_md.append("\n---\n")

out_md.append("## 2. Standard Briefing Screens (Rounds 1–10)\n")
for r in range(1, 11):
    b = briefings.get(r, {})
    out_md.append(f"### Round {r}: {b.get('title')} ({b.get('theme')})")
    for n in b.get('narratives', []):
        out_md.append(f"{n}\n")

out_md.append("\n---\n")

out_md.append("## 3. Specialized Briefing Screens \n")

out_md.append("### Healthcare Edition Briefings\n")
for r in range(1, 11):
    b = healthcare.get(r, {})
    out_md.append(f"#### Round {r}: {b.get('title')} ({b.get('theme')})")
    for n in b.get('narratives', []):
        out_md.append(f"{n}\n")

out_md.append("### UN SDG Edition Briefings\n")
for r in range(1, 11):
    b = sdg.get(r, {})
    out_md.append(f"#### Round {r}: {b.get('title')} ({b.get('theme')})")
    for n in b.get('narratives', []):
        out_md.append(f"{n}\n")

out_md.append("\n---\n")

out_md.append("## 4. Alternate Ending Pathways\n")
out_md.append("The simulation contains 5 dynamic ending scenarios (R10 crises) governed by the `ending_pathways.py` engine. These are selected by the facilitator and foreshadowed during Rounds 5–8 via market news.\n")
out_md.append("1. **Activist Ultimatum (Default)**\n   - **Trigger**: Activist hedge fund accumulates a blocking stake.\n   - **Options**: Resist & Integrate, Spin-off, Divest.\n   - **Key Metric**: Synergy Score (> 80 required to successfully resist).\n")
out_md.append("2. **Climate Black Swan**\n   - **Trigger**: 1.5°C threshold breached; carbon markets in turmoil. Carbon tax triples to $750/ton.\n   - **Options**: Emergency Decarbonisation (halve CI/NCD), Climate Adaptation Portfolio (divest high CI BUs), or Deny & Delay.\n   - **Key Metric**: Carbon Intensity (high CI leads to stranded asset penalties and exit multiple haircuts).\n")
out_md.append("3. **Stakeholder Revolt**\n   - **Trigger**: Employees, communities, and consumers issue coordinated demands.\n   - **Options**: Total Stakeholder Compact, Selective Appeasement, or Corporate Hardball (threaten relocation).\n   - **Key Metric**: Social License and Burnout Index (determines Social Collapse vs Regeneration bonuses).\n")
out_md.append("4. **Hostile Takeover**\n   - **Trigger**: Cerberus Capital launches a hostile tender offer to break up the company.\n   - **Options**: White Knight Defence (requires Synergy ≥ 1.3), Poison Pill + Lock-Up, or Accept the Bid.\n   - **Key Metric**: Fortress Premium (EBITDA margin > 20%) and Synergy Multiplier.\n")
out_md.append("5. **Regulatory Shutdown**\n   - **Trigger**: Whistleblower triggers environmental agency investigation under the CSDDD.\n   - **Options**: Full Remediation Programme, Negotiate Consent Decree (accept $30M fine), or Contest the Ruling (high risk).\n   - **Key Metric**: Compliance Risk Index & Ethical Score (gates the \"Regulatory Exemplar\" bonus).\n")

out_md.append("\n---\n")

out_md.append("## 5. Side Tracks\nSide tracks are 4–7 round deep-dive curricula that run parallel to the main game or can be assigned by facilitators.\n")
out_md.append("- **Supply Chain Track (7 Rounds)**\n  - Maps tier vulnerabilities, modern slavery, circular procurement, nearshoring, and supply chain resilience stress testing.")
out_md.append("- **Ethics & Sustainability Track (5 Rounds)**\n  - Explores ethical AI, human rights due diligence, greenwashing substantiation, natural capital accounting, and community impact.")
out_md.append("- **Stakeholder Management Track (4 Rounds)**\n  - Focuses on salience mapping, investor ESG disclosure, social license, and crisis communication.")
out_md.append("- **Sustainability Reporting Track (5 Rounds)**\n  - Simulates CSRD/ESRS readiness, TCFD/ISSB climate disclosures, metrics assurance, and integrated value creation reporting.")

with open(r"C:\Users\Home\.gemini\antigravity\brain\b7053311-d6a3-42c6-b94e-f2f59aaaf5a5\artifacts\briefings_and_pathways.md", "w", encoding="utf-8") as f:
    f.write("\n".join(out_md))

print("Markdown generated successfully!")
