"""
Add regulatory_tooltip to every option in BRSR_PILLAR_OPTIONS.
Each area (energy, operations, supply_chain, offsetting, human_resources) has 3 options.
The FIRST option in each area is "Option A", SECOND is "Option B", THIRD is "Option C".
Tooltip text is the same for all rounds for a given pillar/option combination.
"""
import re, sys

TOOLTIPS = {
    "energy": {
        "a": (
            "Satisfies P6 Leadership Indicator; aligns with BRSR Core Attribute 5 "
            "(Energy intensity per rupee of turnover) and MoEFCC National Clean Air "
            "Programme reporting mandates."
        ),
        "b": (
            "Meets P6 Essential Indicator baseline; partial compliance with BRSR Core "
            "Attribute 5 but may trigger SEBI clarification query on energy intensity "
            "methodology."
        ),
        "c": (
            "Heightens vulnerability to SEBI Show-Cause interventions; compounds P6 "
            "non-compliance risks under Rule 34(2)(f) of the Companies Act, 2013."
        ),
    },
    "operations": {
        "a": (
            "Fulfills Extended Producer Responsibility (EPR) statutory filing requirements "
            "under CPCB hazardous waste amendments; satisfies P2 Leadership Indicator on "
            "product lifecycle stewardship."
        ),
        "b": (
            "Meets P2 Essential Indicator on responsible sourcing; partial compliance with "
            "EPR registration requirements under Plastic Waste Management Rules, 2016."
        ),
        "c": (
            "Heightens vulnerability to SPCB closure orders; compounds Section 135 CSR "
            "shortfall penalties and CPCB consent-to-operate revocation risk."
        ),
    },
    "supply_chain": {
        "a": (
            "Ensures BRSR Core readiness; initiates preliminary Top-250 glide path "
            "reasonable assurance mapping under SEBI Circular "
            "SEBI/HO/CFD/CMD-2/P/CIR/2023/18."
        ),
        "b": (
            "Meets P4 Essential Indicator on supply chain disclosure; partial compliance "
            "with BRSR Core but defers reasonable assurance engagement to subsequent "
            "filing period."
        ),
        "c": (
            "Heightens greenwash exposure; creates material discrepancy between "
            "self-assessed and third-party validated BRSR Core attributes for value "
            "chain KPIs."
        ),
    },
    "offsetting": {
        "a": (
            "Mitigates P1 Principle friction; satisfies Clause 4(b) of the updated "
            "NGRBC mandate regarding independent oversight of lobbying and political "
            "contribution disclosures."
        ),
        "b": (
            "Meets P1 Essential Indicator on anti-corruption policies; partial compliance "
            "with NGRBC governance standards but may not satisfy institutional investor "
            "ESG screening criteria."
        ),
        "c": (
            "Heightens governance fragility; compounds vulnerability to SEBI adjudication "
            "proceedings under Regulation 4(2)(f) of the LODR Regulations, 2015."
        ),
    },
    "human_resources": {
        "a": (
            "Aligns with P3 Leadership Indicators; rectifies statutory EPFO and ESIC "
            "non-compliance risks among third-party contractual dependencies. Satisfies "
            "POSH Act, 2013 reporting mandates."
        ),
        "b": (
            "Meets P3 Essential Indicator on employee well-being metrics; addresses basic "
            "OHS compliance under Factories Act but defers living wage gap analysis."
        ),
        "c": (
            "Heightens vulnerability to P3/P5 non-compliance citations; compounds exposure "
            "to Section 25FF Industrial Disputes Act consequences and ESI Act penalty "
            "proceedings."
        ),
    },
}


def main():
    filepath = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim\backend\side_tracks\brsr_ngrbc\configs.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # We need to find the start of BRSR_PILLAR_OPTIONS and work only within it
    pillar_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("BRSR_PILLAR_OPTIONS"):
            pillar_start = i
            break

    if pillar_start is None:
        print("ERROR: Could not find BRSR_PILLAR_OPTIONS")
        sys.exit(1)

    # Find the end of BRSR_PILLAR_OPTIONS (the closing `}` at column 0)
    # It's the `}` line that closes the top-level dict.
    brace_depth = 0
    pillar_end = None
    started = False
    for i in range(pillar_start, len(lines)):
        line = lines[i]
        for ch in line:
            if ch == '{':
                brace_depth += 1
                started = True
            elif ch == '}':
                brace_depth -= 1
        if started and brace_depth == 0:
            pillar_end = i
            break

    if pillar_end is None:
        print("ERROR: Could not find end of BRSR_PILLAR_OPTIONS")
        sys.exit(1)

    print(f"BRSR_PILLAR_OPTIONS spans lines {pillar_start+1} to {pillar_end+1}")

    # Now process only within that range.
    # Strategy: track which area we're in, and count option blocks within each area.
    # When we see `"flags_set":` within an option block, insert `"regulatory_tooltip":`
    # right after the `"flags_set": [...]` line (or after the closing `],` if multiline).

    current_area = None
    option_index = 0  # 0=A, 1=B, 2=C within current area
    in_options_block = False  # True when inside an area's "options" dict
    area_options_depth = 0

    new_lines = lines[:pillar_start]  # everything before BRSR_PILLAR_OPTIONS

    # We'll track brace depth relative to the area "options" dict
    i = pillar_start
    while i <= pillar_end:
        line = lines[i]
        stripped = line.strip()

        # Detect area key transitions
        area_match = re.match(r'^\s+"(energy|operations|supply_chain|offsetting|human_resources)"\s*:\s*\{', stripped)
        if area_match:
            current_area = area_match.group(1)
            option_index = 0
            in_options_block = False
            new_lines.append(line)
            i += 1
            continue

        # Detect "options": { within an area
        if current_area and not in_options_block and stripped.startswith('"options"') and '{' in stripped:
            in_options_block = True
            area_options_depth = 0
            for ch in line:
                if ch == '{':
                    area_options_depth += 1
                elif ch == '}':
                    area_options_depth -= 1
            new_lines.append(line)
            i += 1
            continue

        # Track depth within options block
        if in_options_block:
            # Check if this line has "flags_set": [...],
            if '"flags_set"' in stripped and current_area:
                # Determine option letter
                option_letter = ["a", "b", "c"][min(option_index, 2)]
                tooltip_text = TOOLTIPS[current_area][option_letter]

                new_lines.append(line)

                # If flags_set ends on this line (contains `],`)
                if '],\n' in line + '\n' or line.rstrip().endswith('],'):
                    # Insert regulatory_tooltip after this line
                    # Determine indentation from flags_set line
                    indent = len(line) - len(line.lstrip())
                    indent_str = " " * indent
                    tooltip_line = f'{indent_str}"regulatory_tooltip": (\n{indent_str}    "{tooltip_text}"\n{indent_str}),'
                    new_lines.append(tooltip_line)
                    option_index += 1
                elif line.rstrip().endswith('],'):
                    indent = len(line) - len(line.lstrip())
                    indent_str = " " * indent
                    tooltip_line = f'{indent_str}"regulatory_tooltip": (\n{indent_str}    "{tooltip_text}"\n{indent_str}),'
                    new_lines.append(tooltip_line)
                    option_index += 1
                else:
                    # flags_set might be multiline - look ahead for closing `],`
                    i += 1
                    while i <= pillar_end:
                        fline = lines[i]
                        new_lines.append(fline)
                        if fline.strip().startswith('],') or fline.strip() == '],':
                            indent = len(line) - len(line.lstrip())
                            indent_str = " " * indent
                            tooltip_line = f'{indent_str}"regulatory_tooltip": (\n{indent_str}    "{tooltip_text}"\n{indent_str}),'
                            new_lines.append(tooltip_line)
                            option_index += 1
                            break
                        i += 1

                i += 1
                continue

            # Track brace depth to detect end of options block
            for ch in stripped:
                if ch == '{':
                    area_options_depth += 1
                elif ch == '}':
                    area_options_depth -= 1

            if area_options_depth <= 0:
                in_options_block = False
                current_area = None

        new_lines.append(line)
        i += 1

    # Add everything after pillar_end
    new_lines.extend(lines[pillar_end + 1:])

    result = "\n".join(new_lines)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(result)

    print("Done! Tooltips added.")


if __name__ == "__main__":
    main()
