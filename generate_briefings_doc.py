"""
Generate comprehensive Word document with all Muressons simulation briefings,
teleprompter scripts, side tracks, and alternate ending pathways.
"""
import re, html, sys, os
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

# ── Helpers ──────────────────────────────────────────────────────
def strip_html(text):
    """Remove HTML tags from briefing text."""
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text).replace("\\n", "\n")

def add_styled_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)
    return h

def add_body(doc, text, bold=False, italic=False):
    p = doc.add_paragraph()
    run = p.add_run(strip_html(text))
    run.font.size = Pt(11)
    run.bold = bold
    run.italic = italic
    return p

def add_bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        run = p.add_run(bold_prefix)
        run.bold = True
        run.font.size = Pt(11)
        run = p.add_run(strip_html(text))
        run.font.size = Pt(11)
    else:
        run = p.add_run(strip_html(text))
        run.font.size = Pt(11)
    return p

def add_option_table(doc, options):
    """Add a formatted table for decision options."""
    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Light Grid Accent 1'
    hdr = table.rows[0].cells
    for i, label in enumerate(['Option', 'Title', 'Description', 'Key Impacts']):
        hdr[i].text = label
        for p in hdr[i].paragraphs:
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(10)

    for key in sorted(options.keys()):
        opt = options[key]
        row = table.add_row().cells
        row[0].text = opt.get('label', key[-1].upper())
        row[1].text = opt.get('title', '')
        row[2].text = strip_html(opt.get('description', ''))
        impacts = opt.get('impacts', {})
        impact_lines = []
        for k, v in impacts.items():
            if isinstance(v, bool):
                impact_lines.append(f"{k}: {'Yes' if v else 'No'}")
            elif isinstance(v, (int, float)):
                prefix = '+' if v > 0 else ''
                if abs(v) >= 1_000_000:
                    impact_lines.append(f"{k}: {prefix}${v/1_000_000:.0f}M")
                else:
                    impact_lines.append(f"{k}: {prefix}{v}")
        row[3].text = '\n'.join(impact_lines) if impact_lines else 'See description'
        for cell in row:
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9)
    return table

# ── Parse RoundBriefing.js ───────────────────────────────────────
JS_PATH = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim\frontend\app\components\RoundBriefing.js"
with open(JS_PATH, 'r', encoding='utf-8') as f:
    js_content = f.read()

def parse_js_briefings(section_name):
    match = re.search(f"export const {section_name} = \\{{(.*?)\n\\}};", js_content, re.DOTALL)
    if not match:
        return {}
    body = match.group(1)
    rounds = {}
    round_matches = list(re.finditer(r"^\s+(\d+):\s+\{", body, re.MULTILINE))
    for i, rm in enumerate(round_matches):
        end = round_matches[i+1].start() if i+1 < len(round_matches) else len(body)
        rs = body[rm.start():end]
        title_m = re.search(r"title:\s*'([^']+)'", rs)
        theme_m = re.search(r"theme:\s*'([^']+)'", rs)
        icon_m = re.search(r"icon:\s*'([^']+)'", rs)
        stamp_m = re.search(r"stamp:\s*'([^']+)'", rs)
        narr_m = re.search(r"narrative:\s*\[(.*?)\]", rs, re.DOTALL)
        obj_m = re.search(r"objectives:\s*\[(.*?)\]", rs, re.DOTALL)
        warn_m = re.search(r"warning:\s*\{[^}]*text:\s*'((?:\\'|[^'])*)'", rs, re.DOTALL)
        narratives = []
        if narr_m:
            narratives = [s.replace("\\'", "'") for s in re.findall(r"'((?:\\'|[^'])*)'", narr_m.group(1))]
        objectives = []
        if obj_m:
            objectives = [s.replace("\\'", "'") for s in re.findall(r"'((?:\\'|[^'])*)'", obj_m.group(1))]
        warning = None
        if warn_m:
            warning = warn_m.group(1).replace("\\'", "'")
        rounds[int(rm.group(1))] = {
            "title": title_m.group(1) if title_m else "",
            "theme": theme_m.group(1) if theme_m else "",
            "icon": icon_m.group(1) if icon_m else "",
            "stamp": stamp_m.group(1) if stamp_m else "",
            "narratives": narratives,
            "objectives": objectives,
            "warning": warning,
        }
    return rounds

BRIEFINGS = parse_js_briefings("BRIEFINGS")
HC_BRIEFINGS = parse_js_briefings("HEALTHCARE_BRIEFINGS")
SDG_BRIEFINGS = parse_js_briefings("SDG_BRIEFINGS")

# ── Import backend data ─────────────────────────────────────────
sys.path.insert(0, r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim\backend")
from admin_teleprompter import _TELEPROMPTER_SCRIPTS
from ending_pathways import PATHWAY_DESCRIPTIONS, PATHWAY_R10_CONFIGS, FORESHADOWING
from side_tracks.supply_chain.configs import SUPPLY_CHAIN_ROUND_CONFIGS
from side_tracks.ethics_sustainability.configs import ETHICS_ROUND_CONFIGS
from side_tracks.stakeholder_management.configs import STAKEHOLDER_ROUND_CONFIGS
from side_tracks.sustainability_reporting.configs import REPORTING_ROUND_CONFIGS
from round_configs import ROUND_CONFIGS, TURNAROUND_OPTION_T
from healthcare_configs import HEALTHCARE_ROUND_CONFIGS

# ═══════════════════════════════════════════════════════════════
#  BUILD THE DOCUMENT
# ═══════════════════════════════════════════════════════════════
doc = Document()

# Page setup
for section in doc.sections:
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

# ── TITLE PAGE ───────────────────────────────────────────────────
doc.add_paragraph()
doc.add_paragraph()
title = doc.add_heading('Muressons Global Corporation', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
subtitle = doc.add_heading('Simulation Briefings, Decision Paradigms,\nAlternate Pathways & Side Tracks', level=1)
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('Comprehensive Facilitator Reference Document')
run.font.size = Pt(14)
run.italic = True
doc.add_page_break()

# ── TABLE OF CONTENTS ────────────────────────────────────────────
add_styled_heading(doc, 'Table of Contents', level=1)
toc_items = [
    '1. Decision Paradigms',
    '2. Standard Briefing Screens (Rounds 1–10)',
    '3. Facilitator Teleprompter Scripts (Rounds 1–10)',
    '4. Healthcare Edition Briefings',
    '5. UN SDG Edition Briefings',
    '6. Alternate Ending Pathways',
    '7. Side Track: Supply Chain (7 Rounds)',
    '8. Side Track: Ethics & Sustainability (5 Rounds)',
    '9. Side Track: Stakeholder Management (4 Rounds)',
    '10. Side Track: Sustainability Reporting (5 Rounds)',
    '11. Mathematical Engine: Formulae & Sample Calculations',
    '12. Investment Matrix: How Capital Allocation Impacts Round Outcomes',
    '13. Investment-to-Score Rationale: Why Investment Improves Player Scores',
    '14. Full Game Walkthrough: Climate Black Swan (Rounds 1-10)',
]
for item in toc_items:
    doc.add_paragraph(item, style='List Number')
doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 1: DECISION PARADIGMS
# ═══════════════════════════════════════════════════════════════
add_styled_heading(doc, '1. Decision Paradigms', level=1)
add_body(doc, 'Decision Paradigms govern how choices are presented and evaluated during the simulation:')
paradigms = [
    ('legacy_abc', 'The classic paradigm featuring standard 3-option (A/B/C) multiple-choice decision gates per round.'),
    ('multi_toggles', 'Advanced decision gating where players configure multiple sliders/toggles across different pillars instead of a single A/B/C choice.'),
    ('advanced_climate', 'A paradigm focused heavily on decarbonization, carbon pricing, and physical/transition climate risks.'),
    ('healthcare', 'A specialized paradigm reshaping the simulation into a healthcare network (Hospitals, Clinics, Specialised Care, Telehealth) managing patient outcomes and clinical compliance.'),
]
for name, desc in paradigms:
    add_bullet(doc, desc, bold_prefix=f'{name}: ')

add_body(doc, '')
add_body(doc, 'Emergency Turnaround Option (Option T):', bold=True)
add_body(doc, 'When a team enters Survival Mode (crisis or stabilisation phase), an additional Option T is dynamically injected alongside A/B/C:')
add_bullet(doc, f"Title: {TURNAROUND_OPTION_T['title']}")
add_bullet(doc, f"Description: {TURNAROUND_OPTION_T['description']}")
add_bullet(doc, f"Flags Set: {', '.join(TURNAROUND_OPTION_T['flags_set'])}")
imp = TURNAROUND_OPTION_T['impacts']
for k, v in imp.items():
    add_bullet(doc, f"{k}: {v}")
doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 2: STANDARD BRIEFING SCREENS
# ═══════════════════════════════════════════════════════════════
add_styled_heading(doc, '2. Standard Briefing Screens (Rounds 1–10)', level=1)
add_body(doc, 'The following are the complete round introduction screens shown to students at the start of each decision round in the standard (Corporate ESG) edition of the simulation.')

for r in range(1, 11):
    b = BRIEFINGS.get(r, {})
    add_styled_heading(doc, f"Round {r}: {b.get('icon','')} {b.get('title','')} — {b.get('theme','')}", level=2)
    p = doc.add_paragraph()
    run = p.add_run(f"[{b.get('stamp', '')}]")
    run.bold = True
    run.font.color.rgb = RGBColor(0xc0, 0x39, 0x2b)
    run.font.size = Pt(11)

    for narr in b.get('narratives', []):
        add_body(doc, narr)

    if b.get('objectives'):
        add_body(doc, 'Objectives:', bold=True)
        for obj in b['objectives']:
            add_bullet(doc, obj)

    if b.get('warning'):
        p = doc.add_paragraph()
        run = p.add_run('[WARNING] ')
        run.bold = True
        run.font.color.rgb = RGBColor(0xe7, 0x4c, 0x3c)
        run = p.add_run(strip_html(b['warning']))
        run.font.size = Pt(11)

    # ── Decision Alternatives (from round_configs.py) ────────
    rc = ROUND_CONFIGS.get(r, {})
    crisis = rc.get('crisis', {})
    if crisis.get('description'):
        add_body(doc, f"Crisis Scenario: {crisis.get('icon','')} {crisis.get('title','')}", bold=True)
        add_body(doc, crisis['description'])

    options = rc.get('options', {})
    if options:
        add_body(doc, 'Decision Alternatives:', bold=True)
        add_option_table(doc, options)
        # Flags set per option
        for okey in sorted(options.keys()):
            opt = options[okey]
            flags = opt.get('flags_set', [])
            if flags:
                add_bullet(doc, f"Flags: {', '.join(flags)}", bold_prefix=f"Option {opt.get('label', okey[-1].upper())}: ")

    # Special rules
    sr = rc.get('special_rules', {})
    if sr:
        add_body(doc, 'Special Rules:', bold=True)
        for k, v in sr.items():
            if isinstance(v, dict):
                for sk, sv in v.items():
                    add_bullet(doc, f"{sk}: {sv}")
            else:
                add_bullet(doc, f"{k}: {v}")

    doc.add_paragraph()  # spacer

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 3: TELEPROMPTER SCRIPTS
# ═══════════════════════════════════════════════════════════════
add_styled_heading(doc, '3. Facilitator Teleprompter Scripts (Rounds 1–10)', level=1)
add_body(doc, 'The following scripts are designed for facilitator use during the live simulation. They contain talking points, key teaching moments, discussion prompts, and pedagogical connections for each round.')

for r in range(1, 11):
    script = _TELEPROMPTER_SCRIPTS.get(r, {})
    add_styled_heading(doc, script.get('title', f'Round {r}'), level=2)

    # Crisis theme
    if script.get('crisis_theme'):
        add_body(doc, script['crisis_theme'], italic=True)

    # Opening question
    if script.get('opening_question'):
        add_body(doc, 'Opening Question:', bold=True)
        add_body(doc, script['opening_question'])

    # Talking points
    if script.get('talking_points'):
        add_body(doc, 'Talking Points:', bold=True)
        for tp in script['talking_points']:
            add_bullet(doc, tp)

    # Key teaching moment
    if script.get('key_teaching_moment'):
        add_body(doc, 'Key Teaching Moment:', bold=True)
        add_body(doc, script['key_teaching_moment'])

    # HR tracking
    if script.get('hr_tracking'):
        add_body(doc, script['hr_tracking'], italic=True)

    # Connection to theory
    ctt = script.get('connection_to_theory', {})
    if ctt:
        add_body(doc, 'Connection to Theory:', bold=True)
        if isinstance(ctt, dict):
            insights = ctt.get('insights', [])
            if insights:
                for insight in insights:
                    add_bullet(doc, f"{insight.get('theory','')}: {insight.get('insight','')}")
                    if insight.get('reference'):
                        p = doc.add_paragraph()
                        run = p.add_run(f"    Reference: {insight['reference']}")
                        run.font.size = Pt(9)
                        run.italic = True
            # Handle string-valued theory entries
            for k, v in ctt.items():
                if isinstance(v, str):
                    add_bullet(doc, v)

    # Debrief the cascade (R4 special)
    if script.get('debrief_the_cascade'):
        add_body(doc, 'Debrief the R1→R4 Cascade:', bold=True)
        dtc = script['debrief_the_cascade']
        for k, v in dtc.items():
            add_bullet(doc, v, bold_prefix=f'{k}: ')

    # M_R breakdown guide (R10 special)
    if script.get('mr_breakdown_guide'):
        add_body(doc, 'Regenerative Multiple (M_R) Breakdown:', bold=True)
        table = doc.add_table(rows=1, cols=3)
        table.style = 'Light Grid Accent 1'
        hdr = table.rows[0].cells
        hdr[0].text = 'Component'
        hdr[1].text = 'Value'
        hdr[2].text = 'Source'
        for comp_key, comp in script['mr_breakdown_guide'].items():
            row = table.add_row().cells
            row[0].text = comp_key.replace('_', ' ').title()
            row[1].text = str(comp.get('value', ''))
            row[2].text = comp.get('source', '')

    # Discussion prompts
    if script.get('discussion_prompts'):
        add_body(doc, 'Discussion Prompts:', bold=True)
        for dp in script['discussion_prompts']:
            add_bullet(doc, dp)

    # Reflection
    if script.get('reflection_sensitisation'):
        add_body(doc, 'Reflection Protocol:', bold=True)
        add_body(doc, script['reflection_sensitisation'])

    # Stakeholder debrief / migration
    if script.get('stakeholder_debrief'):
        add_body(doc, 'Stakeholder Debrief:', bold=True)
        for k, v in script['stakeholder_debrief'].items():
            add_bullet(doc, v, bold_prefix=f'{k.replace("_"," ").title()}: ')

    if script.get('stakeholder_migration'):
        sm = script['stakeholder_migration']
        if sm.get('migrations_this_round'):
            add_body(doc, 'Stakeholder Migrations This Round:', bold=True)
            for mig in sm['migrations_this_round']:
                add_bullet(doc, mig)
        if sm.get('discussion_prompt'):
            add_body(doc, sm['discussion_prompt'], italic=True)

    # Student UX coaching
    if script.get('student_ux_coaching'):
        uxc = script['student_ux_coaching']
        add_body(doc, 'Student UX Coaching:', bold=True)
        if uxc.get('facilitator_prompt'):
            add_bullet(doc, uxc['facilitator_prompt'], bold_prefix='Facilitator Prompt: ')
        if uxc.get('what_to_watch'):
            add_bullet(doc, uxc['what_to_watch'], bold_prefix='What to Watch: ')
        if uxc.get('ui_tip'):
            add_bullet(doc, uxc['ui_tip'], bold_prefix='UI Tip: ')

    # Journey improvements
    if script.get('journey_improvement'):
        add_body(doc, 'Journey Improvement Notes:', bold=True)
        ji = script['journey_improvement']
        for ji_key, ji_val in ji.items():
            if isinstance(ji_val, dict) and 'facilitator_guidance' in ji_val:
                for fg in ji_val['facilitator_guidance']:
                    add_bullet(doc, fg)

    doc.add_paragraph()

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 4: HEALTHCARE BRIEFINGS
# ═══════════════════════════════════════════════════════════════
add_styled_heading(doc, '4. Healthcare Edition Briefings', level=1)
add_body(doc, 'The Healthcare Edition replaces the standard corporate conglomerate scenario with a healthcare network (Hospitals, Clinics, Specialised Care, Telehealth). The following are the complete round introduction screens.')

for r in range(1, 11):
    b = HC_BRIEFINGS.get(r, {})
    add_styled_heading(doc, f"Round {r}: {b.get('icon','')} {b.get('title','')} — {b.get('theme','')}", level=2)
    p = doc.add_paragraph()
    run = p.add_run(f"[{b.get('stamp', '')}]")
    run.bold = True
    run.font.color.rgb = RGBColor(0xc0, 0x39, 0x2b)
    for narr in b.get('narratives', []):
        add_body(doc, narr)
    if b.get('objectives'):
        add_body(doc, 'Objectives:', bold=True)
        for obj in b['objectives']:
            add_bullet(doc, obj)
    if b.get('warning'):
        p = doc.add_paragraph()
        run = p.add_run('[WARNING] ')
        run.bold = True
        run.font.color.rgb = RGBColor(0xe7, 0x4c, 0x3c)
        run = p.add_run(strip_html(b['warning']))

    # ── Healthcare Decision Alternatives ────────────────────
    hc_cfg = HEALTHCARE_ROUND_CONFIGS.get(r, {})
    hc_crisis = hc_cfg.get('crisis', {})
    if hc_crisis.get('description'):
        add_body(doc, f"Crisis Scenario: {hc_crisis.get('icon','')} {hc_crisis.get('title','')}", bold=True)
        add_body(doc, hc_crisis['description'])

    hc_options = hc_cfg.get('options', {})
    if hc_options:
        add_body(doc, 'Decision Alternatives:', bold=True)
        add_option_table(doc, hc_options)
        for okey in sorted(hc_options.keys()):
            opt = hc_options[okey]
            flags = opt.get('flags_set', [])
            if flags:
                add_bullet(doc, f"Flags: {', '.join(flags)}", bold_prefix=f"Option {opt.get('label', okey[-1].upper())}: ")

    hc_sr = hc_cfg.get('special_rules', {})
    if hc_sr:
        add_body(doc, 'Special Rules:', bold=True)
        for k, v in hc_sr.items():
            if isinstance(v, dict):
                for sk, sv in v.items():
                    add_bullet(doc, f"{sk}: {sv}")
            else:
                add_bullet(doc, f"{k}: {v}")

    doc.add_paragraph()

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 5: SDG BRIEFINGS
# ═══════════════════════════════════════════════════════════════
add_styled_heading(doc, '5. UN SDG Edition Briefings', level=1)
add_body(doc, 'The UN SDG Edition replaces the corporate scenario with a global development mandate. Players act as UN Special Envoy for Sustainable Development across 4 global regions.')

for r in range(1, 11):
    b = SDG_BRIEFINGS.get(r, {})
    add_styled_heading(doc, f"Round {r}: {b.get('icon','')} {b.get('title','')} — {b.get('theme','')}", level=2)
    p = doc.add_paragraph()
    run = p.add_run(f"[{b.get('stamp', '')}]")
    run.bold = True
    run.font.color.rgb = RGBColor(0xc0, 0x39, 0x2b)
    for narr in b.get('narratives', []):
        add_body(doc, narr)
    if b.get('objectives'):
        add_body(doc, 'Objectives:', bold=True)
        for obj in b['objectives']:
            add_bullet(doc, obj)
    if b.get('warning'):
        p = doc.add_paragraph()
        run = p.add_run('⚠️ WARNING: ')
        run.bold = True
        run.font.color.rgb = RGBColor(0xe7, 0x4c, 0x3c)
        run = p.add_run(strip_html(b['warning']))
    doc.add_paragraph()

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 6: ALTERNATE ENDING PATHWAYS
# ═══════════════════════════════════════════════════════════════
add_styled_heading(doc, '6. Alternate Ending Pathways', level=1)
add_body(doc, 'The simulation features 5 dynamic R10 crisis scenarios. Facilitators select a pathway at cohort creation. Foreshadowing events are injected during Rounds 5–8 via market intelligence news items.')

for pw_id, pw_desc in PATHWAY_DESCRIPTIONS.items():
    add_styled_heading(doc, f"{pw_desc['name']}", level=2)
    add_body(doc, pw_desc['description'])

    # Foreshadowing
    fw = FORESHADOWING.get(pw_id, {})
    if fw:
        add_body(doc, 'Foreshadowing Events:', bold=True)
        for rnd, events in sorted(fw.items()):
            for evt in events:
                add_bullet(doc, f"Round {rnd} — {evt.get('headline','')}: {evt.get('body','')}")

    # R10 config
    cfg = PATHWAY_R10_CONFIGS.get(pw_id, {})
    if cfg:
        crisis = cfg.get('crisis', {})
        add_body(doc, f"R10 Crisis: {crisis.get('icon','')} {crisis.get('title','')}", bold=True)
        add_body(doc, crisis.get('description', ''))

        # Options
        options = cfg.get('options', {})
        if options:
            add_body(doc, 'Decision Options:', bold=True)
            add_option_table(doc, options)

        # Special rules
        rules = cfg.get('special_rules', {})
        if rules:
            add_body(doc, 'Special Rules:', bold=True)
            for k, v in rules.items():
                if isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        add_bullet(doc, f"{sub_k}: {sub_v}")
                else:
                    add_bullet(doc, f"{k}: {v}")

        # Archetype overrides
        archetypes = cfg.get('archetype_overrides', {})
        if archetypes:
            add_body(doc, 'Profile Archetype Overrides:', bold=True)
            for arch_key, arch_val in archetypes.items():
                add_bullet(doc, f"{arch_val.get('icon','')} {arch_val.get('title','')} ({arch_key})")

    doc.add_paragraph()

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 7: SUPPLY CHAIN SIDE TRACK
# ═══════════════════════════════════════════════════════════════
def write_side_track(doc, section_num, track_name, configs, num_rounds):
    add_styled_heading(doc, f'{section_num}. Side Track: {track_name}', level=1)
    for r in range(1, num_rounds + 1):
        cfg = configs.get(r, {})
        add_styled_heading(doc, f"Round {r}: {cfg.get('title', '')}", level=2)

        # Crisis narrative
        crisis = cfg.get('crisis', {})
        if crisis:
            add_body(doc, f"{crisis.get('icon','')} {crisis.get('title','')}", bold=True)
            add_body(doc, crisis.get('description', ''))
            if crisis.get('facilitator_note'):
                p = doc.add_paragraph()
                run = p.add_run('Facilitator Note: ')
                run.bold = True
                run.font.size = Pt(10)
                run = p.add_run(crisis['facilitator_note'])
                run.font.size = Pt(10)
                run.italic = True
        else:
            # Ethics/Stakeholder/Reporting tracks use different keys
            if cfg.get('crisis_title'):
                add_body(doc, cfg['crisis_title'], bold=True)
            if cfg.get('crisis_narrative'):
                add_body(doc, cfg['crisis_narrative'])

        # Options
        options = cfg.get('options', {})
        if options:
            add_body(doc, 'Decision Options:', bold=True)
            add_option_table(doc, options)

        # Special rules
        if cfg.get('special_rules'):
            add_body(doc, 'Special Rules:', bold=True)
            for k, v in cfg['special_rules'].items():
                if isinstance(v, dict):
                    desc = v.get('description', v.get('effect', str(v)))
                    add_bullet(doc, desc, bold_prefix=f'{k}: ')
                elif isinstance(v, bool):
                    add_bullet(doc, f"{k}: {'Active' if v else 'Inactive'}")
                else:
                    add_bullet(doc, f"{k}: {v}")

        doc.add_paragraph()
    doc.add_page_break()

write_side_track(doc, 7, 'Supply Chain (7 Rounds)', SUPPLY_CHAIN_ROUND_CONFIGS, 7)
write_side_track(doc, 8, 'Ethics & Sustainability (5 Rounds)', ETHICS_ROUND_CONFIGS, 5)
write_side_track(doc, 9, 'Stakeholder Management (4 Rounds)', STAKEHOLDER_ROUND_CONFIGS, 4)
write_side_track(doc, 10, 'Sustainability Reporting (5 Rounds)', REPORTING_ROUND_CONFIGS, 5)

# ═══════════════════════════════════════════════════════════════
#  SECTION 11: MATHEMATICAL ENGINE
# ═══════════════════════════════════════════════════════════════
add_styled_heading(doc, '11. Mathematical Engine: Formulae & Sample Calculations', level=1)
add_body(doc, 'This section documents every formula used by the simulation engine (engine.py, round_logic.py, impact_engine.py). Each formula includes a worked example using representative game data.')

# Helper to add a formula block
def add_formula_block(doc, name, formula, description, example_lines):
    add_styled_heading(doc, name, level=2)
    p = doc.add_paragraph()
    run = p.add_run('Formula: ')
    run.bold = True
    run.font.size = Pt(11)
    run = p.add_run(formula)
    run.font.name = 'Consolas'
    run.font.size = Pt(10)
    add_body(doc, description)
    add_body(doc, 'Worked Example:', bold=True)
    for line in example_lines:
        add_bullet(doc, line)
    doc.add_paragraph()

add_formula_block(doc,
    '11.1 Corporate Strategic Fund (CSF)',
    'CSF = Sum(Revenue_i - OPEX_i) - Dividends_Paid',
    'Calculates net cash added to the corporate treasury each round. If total CAPEX exceeds 20% of treasury, a loan is triggered at 12% interest.',
    [
        'Given: Pharma Rev=$18M, OPEX=$11M; Electronics Rev=$22M, OPEX=$14M; Consumer Goods Rev=$15M, OPEX=$9M; Software Rev=$20M, OPEX=$8M',
        'Gross Profit = (18-11) + (22-14) + (15-9) + (20-8) = 7 + 8 + 6 + 12 = $33M',
        'Dividends = $2M',
        'CSF = $33M - $2M = $31M added to treasury',
        'Loan Check: If CAPEX=$8M and 20% of Treasury=$7.6M => Loan=$0.4M at 12% => Penalty=$48K',
    ]
)

add_formula_block(doc,
    '11.2 Contagion Engine (Sigmoid Model)',
    'Group_Rep = AVG(BU_Rep) - 50 * sigmoid((severity - 30) / 15)',
    'Uses S-curve centered at severity=30. Low severity (<15): minimal impact. Medium (20-40): rapid erosion. High (>50): saturating damage. Result clamped to [0, 100].',
    [
        'Given: BU Reps = [70, 58, 74, 82], Crisis Severity = 40',
        'AVG Rep = (70+58+74+82)/4 = 71.0',
        'sigmoid((40-30)/15) = sigmoid(0.667) = 1/(1+e^-0.667) = 0.661',
        'Group_Rep = 71.0 - 50 * 0.661 = 71.0 - 33.05 = 37.95',
        'If electronics_blindspot flag active: severity doubles to 80 => sigmoid=0.967 => Group_Rep = 71 - 48.4 = 22.6',
    ]
)

add_formula_block(doc,
    '11.3 Synergy Engine (Diminishing Returns)',
    'effective_ratio = sqrt(ratio) * 0.7; New_OPEX = Old_OPEX * (1 - effective_ratio * Synergy_Mult)',
    'Uses sqrt scaling so first dollars invested yield outsized returns while later dollars hit diminishing marginal efficiency. Investment_Ratio clamped to [0.0, 1.0].',
    [
        'Given: OPEX = $11M, Investment_Ratio = 0.25, Synergy_Mult = 1.08',
        'effective_ratio = sqrt(0.25) * 0.7 = 0.5 * 0.7 = 0.35',
        'factor = 1 - (0.35 * 1.08) = 1 - 0.378 = 0.622',
        'New_OPEX = $11M * 0.622 = $6.84M (savings of $4.16M)',
    ]
)

add_formula_block(doc,
    '11.4 Natural Capital Cost of Debt',
    'Interest_Rate = Base_Rate + (NCD * 0.0001)',
    'Debt compounds each round: Debt_Next = Debt + (Debt * Interest_Rate). NCD floored at 0, capped at 1,000,000. At NCD=100: rate~6%. At NCD=500: rate~10%. At NCD=1000: rate~15%.',
    [
        'Given: NCD = 5,200, Base_Rate = 0.05',
        'Rate = 0.05 + (5200 * 0.0001) = 0.05 + 0.52 = 0.57 (57%)',
        'Debt_Next = 5200 + (5200 * 0.57) = 5200 + 2964 = 8,164',
        'Note: High NCD compounds aggressively -- early R3 choices have massive downstream impact',
    ]
)

add_formula_block(doc,
    '11.5 VRIO Decay Function',
    'Advantage_Next = Advantage_Current * (1 - Imitation_Decay_Rate)',
    'Prevents synergy from staying permanently high. Default decay rate is 5% per round.',
    [
        'Given: Synergy_Mult = 1.38, Decay_Rate = 0.05',
        'Next = 1.38 * (1 - 0.05) = 1.38 * 0.95 = 1.311',
        'After 3 rounds without R7 boost: 1.38 -> 1.311 -> 1.245 -> 1.183',
    ]
)

add_formula_block(doc,
    '11.6 Talent Brain-Drain (Software/Telehealth BUs)',
    'Penalty = 1 + MAX(0, (65 - Group_Rep)/100) * 1.5 + burnout_adj',
    'When Group Reputation < 65, Software BU OPEX inflates. If burnout > 50, additional agency/locum overhead applies: +((burnout-50)/100)*2.0.',
    [
        'Given: Group_Rep = 55, Software OPEX = $8M, Burnout = 60',
        'Rep Penalty = 1 + ((65-55)/100) * 1.5 = 1 + 0.15 = 1.15',
        'Burnout adj = ((60-50)/100) * 2.0 = 0.20',
        'Total Penalty = 1.15 + 0.20 = 1.35',
        'New OPEX = $8M * 1.35 = $10.8M (+35% overhead)',
    ]
)

add_formula_block(doc,
    '11.7 Strike Probability Engine (R9)',
    'P_Strike = Base_Risk + ((1 - SLO/100) * 0.4)',
    'Triggered when Immediate Closure chosen and Social License < 50. Burnout > 50 adds up to +20% probability. Result clamped to [0.0, 1.0].',
    [
        'Given: Base_Risk = 0.25 (from config), SLO = 35, Burnout = 65',
        'P_Strike = 0.25 + ((1 - 35/100) * 0.4) = 0.25 + 0.26 = 0.51',
        'Burnout boost = min(0.20, (65-50)/100 * 0.40) = 0.06',
        'Final P_Strike = 0.51 + 0.06 = 0.57 (57% chance)',
        'If strike fires: revenue for ALL BUs zeroed for the round',
    ]
)

add_formula_block(doc,
    '11.8 Natural Decay (Entropy)',
    'If CAPEX = 0: Rep_Next = Rep * 0.98, SLO_Next = SLO * 0.98',
    'BUs receiving zero investment decay 2% per round in reputation and social license. Simulates organizational entropy.',
    [
        'Given: Rep = 70, SLO = 65, No investment this round',
        'Rep_Next = 70 * 0.98 = 68.6',
        'SLO_Next = 65 * 0.98 = 63.7',
        'After 5 rounds of neglect: Rep = 70 * 0.98^5 = 63.3',
    ]
)

add_formula_block(doc,
    '11.9 Macroeconomic Inflation',
    'New_OPEX = OPEX * (1 + inflation_index)',
    'Every round, baseline OPEX increases by 2.5%. Players must invest just to tread water.',
    [
        'Given: OPEX = $11M, inflation_index = 0.025',
        'New_OPEX = $11M * 1.025 = $11.275M',
        'Over 10 rounds at 2.5%: OPEX grows by factor of 1.025^10 = 1.28 (+28%)',
    ]
)

add_formula_block(doc,
    '11.10 Execution Overrun Risk',
    'If CAPEX > $3M: 25% chance of +15% cost overrun',
    'Stochastic penalty for large capital projects. Simulates real-world execution risk.',
    [
        'Given: CAPEX = $8M, threshold = $3M',
        'Roll = 0.18 (< 0.25 threshold) => Overrun triggered',
        'Overrun = $8M * 0.15 = $1.2M silently drained from treasury',
    ]
)

add_formula_block(doc,
    '11.11 Technical Debt',
    'If consecutive_zero_rounds >= 2: OPEX_Next = OPEX * 1.04',
    '4% OPEX penalty for BUs receiving zero investment for 2+ consecutive rounds.',
    [
        'Given: OPEX = $14M, zero investment for 3 consecutive rounds',
        'New_OPEX = $14M * 1.04 = $14.56M',
        'Cumulative after 3 rounds of neglect: $14M * 1.04^2 = $15.13M (applied from round 2 onward)',
    ]
)

add_formula_block(doc,
    '11.12 Revenue Cannibalization',
    'If BU_Rev > 1.15 * AVG_Rev: penalty = victim_rev * 0.03 * overlap_score',
    'Market overlap matrix determines cannibalization intensity. Software-Electronics overlap: 0.65. Telehealth-Clinics: 0.70.',
    [
        'Given: Software Rev=$25M, Group Avg=$18.75M (25M > 18.75*1.15=$21.6M => aggressor)',
        'Electronics overlap with Software = 0.65',
        'Electronics penalty = $22M * 0.03 * 0.65 = $429K revenue loss',
    ]
)

add_formula_block(doc,
    '11.13 Stakeholder Fatigue',
    'recovery_efficiency = 1.0 / (1 + 0.3 * crisis_count)',
    'Trust recovery diminishes after each crisis. Third crisis reduces recovery to 53% effectiveness.',
    [
        'Given: Recovery amount = +10 SLO, crisis_count = 3',
        'Efficiency = 1 / (1 + 0.3*3) = 1/1.9 = 0.526',
        'Effective recovery = 10 * 0.526 = 5.26 SLO (instead of 10)',
    ]
)

add_formula_block(doc,
    '11.14 Burnout Accumulation',
    'New_Burnout = Current + burnout_delta + natural_drift; OPEX_penalty = ((burnout-20)^2) * 0.000028125',
    'HR investment reduces burnout (-10 high, -4 medium). No investment adds +3 drift. OPEX penalty activates above 20. Critical threshold at 70 adds governance risk.',
    [
        'Given: Current burnout = 45, No HR investment (delta=0, drift=+3)',
        'New_Burnout = 45 + 0 + 3 = 48',
        'OPEX penalty rate = ((48-20)^2) * 0.000028125 = 784 * 0.000028125 = 2.2%',
        'If OPEX = $11M: penalty = $11M * 0.022 = $242K extra OPEX',
    ]
)

add_formula_block(doc,
    '11.15 Workforce Readiness',
    'Readiness_Next = Readiness + delta; High HR: +8, Medium: +4, None: -5',
    'Global workforce competence score (0-100, starts 50). Below 40: strategic pillar effectiveness -20%. Above 75: +0.05 synergy at R10.',
    [
        'Given: Readiness = 50, High HR investment for 3 consecutive rounds',
        'After R1: 50 + 8 = 58',
        'After R2: 58 + 8 = 66',
        'After R3: 66 + 8 = 74 (approaching +0.10 M_R bonus threshold of 75)',
    ]
)

add_formula_block(doc,
    '11.16 Cash Conversion / Working Capital',
    'cash_efficiency = 1.0 - (governance_risk / 500); Realized_Rev = Revenue * efficiency',
    'BUs with high governance risk have slower cash conversion. Efficiency clamped to [0.5, 1.0].',
    [
        'Given: Revenue = $22M, Governance Risk = 40',
        'Efficiency = 1.0 - (40/500) = 1.0 - 0.08 = 0.92',
        'Realized Revenue = $22M * 0.92 = $20.24M',
    ]
)

add_formula_block(doc,
    '11.17 Dividend Ratchet',
    'If Dividends < 80% of last round: Reputation penalty = -5',
    'Simulates board pressure. Cutting dividends by more than 20% triggers a reputation hit.',
    [
        'Given: Last round dividends = $3M, This round = $2M',
        'Threshold = $3M * 0.80 = $2.4M',
        '$2M < $2.4M => Penalty triggered: Reputation -5',
    ]
)

add_formula_block(doc,
    '11.18 FX Risk Engine',
    'FX_delta = Revenue * fx_movement * BU_exposure; fx_movement in [-5%, +5%]',
    'Stochastic currency movement. Exposure varies by BU: Software 80%, Electronics 75%, Pharma 60%, Consumer Goods 40%.',
    [
        'Given: Electronics Rev=$22M, fx_movement = -3%, exposure = 75%',
        'Delta = $22M * (-0.03) * 0.75 = -$495K revenue impact',
        'Software Rev=$20M, exposure=80%: Delta = $20M * (-0.03) * 0.80 = -$480K',
    ]
)

add_formula_block(doc,
    '11.19 Macro Interest Rate Cycles',
    'R1-R3: CoC -0.5% (easing); R4-R6: 0% (neutral); R7-R9: +0.5% (tightening); R10: +1.0% (crisis)',
    'Models central bank policy cycles affecting cost of capital.',
    [
        'Given: Base CoC = 5%, Round 8 (tightening)',
        'Modifier = +0.5%',
        'Effective CoC = 5% + 0.5% = 5.5%',
        'R10 crisis premium pushes CoC to 6.0%',
    ]
)

# ── R5 Stochastic Climate ──
add_formula_block(doc,
    '11.20 R5 Stochastic Climate Event',
    'If random_roll < threshold (0.75): Damage = Base_Damage * (1 - Resilience_Factor)',
    'Base damage: $12M (corporate) / $18M (healthcare). Resilience from Option A=0.85 (hard engineering), B=0.60 (nature-based), C=0.0 (insurance only). Deferred 2 rounds.',
    [
        'Given: Roll = 0.62 (< 0.75 threshold) => Cyclone strikes',
        'Option B chosen: Resilience = 0.60 BUT deferred 2 rounds => effective = 0.0 this round',
        'Actual Damage = $12M * (1 - 0.0) = $12M (full damage this round)',
        'From R7 onward: effective resilience = 0.60, damage = $12M * 0.40 = $4.8M',
        'Climate tipping: If avg CI > 70, threshold increases +5-15% making cyclone more likely',
    ]
)

# ── R9 Regulatory Friction ──
add_formula_block(doc,
    '11.21 R9 Regulatory Friction',
    'Regulatory_Friction = 1 / max(1, avg_SLO); OPEX_surcharge = friction * 0.08',
    'Low social license generates regulatory friction as an OPEX surcharge across all BUs.',
    [
        'Given: Avg SLO = 35 (< 50 threshold)',
        'Friction = 1 / 35 = 0.0286',
        'OPEX surcharge rate = 0.0286 * 0.08 = 0.23%',
        'If BU OPEX = $11M: surcharge = $11M * 0.0023 = $25.3K per BU',
    ]
)

# ── R10 Terminal Valuation ──
add_styled_heading(doc, '11.22 R10 Terminal Valuation (Grand Finale)', level=2)
add_body(doc, 'The terminal valuation combines EBITDA, carbon costs, exit multiple, and the Regenerative Multiple (M_R).', bold=False)

p = doc.add_paragraph()
run = p.add_run('Step 1 -- Terminal EBITDA:')
run.bold = True
run.font.size = Pt(11)
add_body(doc, 'Terminal_EBITDA = Sum(Revenue_i - OPEX_i) - (Carbon_Tonnage * Carbon_Tax_Per_Ton)')
add_body(doc, 'Carbon_Tonnage = Sum(BU_Carbon_Intensity * BU_Revenue / 1,000,000)')
add_bullet(doc, 'Given: Gross Profit = $33M, Carbon Tonnage = 2,850 tons, Tax = $250/ton')
add_bullet(doc, 'Carbon Cost = 2,850 * $250 = $712,500')
add_bullet(doc, 'Terminal EBITDA = $33M - $0.7125M = $32.29M')

p = doc.add_paragraph()
run = p.add_run('Step 2 -- Regenerative Multiple (M_R):')
run.bold = True
run.font.size = Pt(11)
add_body(doc, 'M_R = 1.0 (base) + bonuses - penalties')

# M_R components table
table = doc.add_table(rows=1, cols=4)
table.style = 'Light Grid Accent 1'
hdr = table.rows[0].cells
for i, label in enumerate(['Component', 'Value', 'Trigger', 'Round Source']):
    hdr[i].text = label
    for p2 in hdr[i].paragraphs:
        for run2 in p2.runs:
            run2.bold = True
            run2.font.size = Pt(9)

mr_components = [
    ('Base', '+1.00', 'Always', '--'),
    ('CSRD Governance', '+0.10', 'R2A: materiality_aligned', 'R2'),
    ('Synergy Bonus', '+0.30', 'R7C: synergy_unlock or waste_to_energy', 'R7'),
    ('Resilience Bonus', '+0.20', 'NOT insurance_only AND NOT electronics_water_priority', 'R5/R8'),
    ('Truth Premium', '+0.15', 'R6B: ethical_ai_overhaul', 'R6'),
    ('Community Champion', '+0.18', 'R9C: community_fund', 'R9'),
    ('Just Transition', '+0.12', 'R9B: managed_transition (alt to Community)', 'R9'),
    ('Workforce Excellence', '+0.10', 'workforce_readiness >= 75 at R10', 'Cumulative HR'),
    ('Wellbeing Champion', '+0.05', 'avg burnout < 20 at R10', 'Cumulative HR'),
    ('Instability Discount', '-0.40', 'avg Social License < 75', 'Cumulative'),
]
for comp in mr_components:
    row = table.add_row().cells
    for i2, val in enumerate(comp):
        row[i2].text = val
        for p2 in row[i2].paragraphs:
            for run2 in p2.runs:
                run2.font.size = Pt(9)

add_body(doc, '')
add_bullet(doc, 'Example: R2A + R6B + R7C + R9C + Resilience + Readiness=80 + Burnout=15 + SLO=78')
add_bullet(doc, 'M_R = 1.0 + 0.10 + 0.15 + 0.30 + 0.18 + 0.20 + 0.10 + 0.05 = 2.08 (Regenerative Titan)')
add_bullet(doc, 'Example: R2C + R6C + R7B + R9A + insurance_only + SLO=40')
add_bullet(doc, 'M_R = 1.0 + 0 + 0 + 0 + 0 - 0.40 = 0.60 (Stranded Relic)')

p = doc.add_paragraph()
run = p.add_run('Step 3 -- Terminal Value:')
run.bold = True
run.font.size = Pt(11)
add_body(doc, 'Terminal_Value = (Terminal_EBITDA + Green_Fund_Balance) * Exit_Multiple * M_R')
add_bullet(doc, 'Given: EBITDA=$32.29M, Green Fund=$2M, Exit Multiple=12x, M_R=1.65')
add_bullet(doc, 'TV = ($32.29M + $2M) * 12 * 1.65 = $34.29M * 19.8 = $678.9M')

p = doc.add_paragraph()
run = p.add_run('Step 4 -- Profile Archetype:')
run.bold = True
run.font.size = Pt(11)

profile_table = doc.add_table(rows=1, cols=3)
profile_table.style = 'Light Grid Accent 1'
hdr = profile_table.rows[0].cells
hdr[0].text = 'Profile'
hdr[1].text = 'M_R Threshold'
hdr[2].text = 'Description'
for ph in [('Regenerative Titan', '>= 1.80', 'Gold standard -- rebuilt natural capital + superior returns'),
           ('De-risked Safe Haven', '>= 1.20', 'Avoided tail risks but innovation stalling'),
           ('Fragile Giant', '>= 0.80', 'Financial but brittle -- vulnerable to future shocks'),
           ('Stranded Relic', '< 0.80', 'Structural decline -- chronic underinvestment')]:
    row = profile_table.add_row().cells
    for i2, val in enumerate(ph):
        row[i2].text = val

doc.add_paragraph()

# ── Strategic What-If Table ──
add_styled_heading(doc, '11.23 Strategic What-If Comparison', level=2)
add_body(doc, 'Small choices in earlier rounds compound into massive terminal value deltas:')
whatif_table = doc.add_table(rows=1, cols=4)
whatif_table.style = 'Light Grid Accent 1'
hdr = whatif_table.rows[0].cells
for i, label in enumerate(['Scenario', 'M_R', 'Terminal Value', 'Delta vs Baseline']):
    hdr[i].text = label
for sc in [('Baseline (Fragile Giant)', '1.05', '~$478M', '--'),
           ('Resilient Choices (R5B + R8A)', '1.25', '~$570M', '+$91M'),
           ('Titan Strategy (all bonuses)', '1.65', '~$752M', '+$273M'),
           ('Maximum Achievable', '2.08', '~$948M', '+$469M')]:
    row = whatif_table.add_row().cells
    for i2, val in enumerate(sc):
        row[i2].text = val

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 12: INVESTMENT MATRIX IMPACT
# ═══════════════════════════════════════════════════════════════
add_styled_heading(doc, '12. Investment Matrix: How Capital Allocation Impacts Round Outcomes', level=1)
add_body(doc, (
    'The Investment Matrix is the primary capital allocation interface. Each round, players distribute '
    'their Corporate Strategic Fund (CSF) across Business Units using sliders. This section explains '
    'how those slider positions cascade through every engine calculation, with round-by-round examples.'
))

# 12.1 How the Slider Works
add_styled_heading(doc, '12.1 Investment Matrix Mechanics', level=2)
add_body(doc, 'Slider Inputs per BU:', bold=True)
add_bullet(doc, 'Investment Ratio (0.0 to 1.0): The fraction of a BU\'s revenue base allocated as CAPEX. Slider position = percentage.')
add_bullet(doc, 'CAPEX Allocated ($): The dollar amount = Investment Ratio * BU Revenue. This is deducted from the CSF pool.')
add_bullet(doc, 'Total Allocation Cap: Total CAPEX across all BUs cannot exceed 120% of CSF pool. Above 100% triggers a loan at 12% interest.')
add_bullet(doc, 'Emergency Credit: If the 120% cap is still insufficient, an additional $1M emergency line is available at prevailing rate + 2%.')

add_body(doc, 'Processing Pipeline:', bold=True)
add_bullet(doc, '1. Revenue Cannibalization -- dominant BUs lose sibling revenue before allocation')
add_bullet(doc, '2. FX Risk -- stochastic currency movement adjusts revenue (exposure-weighted)')
add_bullet(doc, '3. DSO / Working Capital -- high governance risk defers a fraction of revenue')
add_bullet(doc, '4. Cash Conversion -- governance risk reduces realized revenue')
add_bullet(doc, '5. Inflation -- all OPEX increases by ~2.5% before synergy is applied')
add_bullet(doc, '6. Synergy Engine -- investment ratio reduces OPEX (diminishing returns via sqrt)')
add_bullet(doc, '7. Implementation Lag -- investments > 10% ratio are DEFERRED 1 round')
add_bullet(doc, '8. CSF Calculation -- gross profit = revenue - OPEX - dividends')
add_bullet(doc, '9. Loan Interest -- CAPEX exceeding 20% of treasury triggers 12% loan')
add_bullet(doc, '10. Overrun Risk -- CAPEX > $3M has 25% chance of +15% cost overrun')
add_bullet(doc, '11. Natural Decay -- BUs with zero CAPEX lose 2% reputation + SLO per round')
add_bullet(doc, '12. Technical Debt -- 2+ rounds of zero investment triggers 4% OPEX penalty')
add_bullet(doc, '13. Brain-Drain -- low group reputation inflates Software/Healthcare OPEX')
add_bullet(doc, '14. Talent Neglect -- BUs receiving < 15% share of total CAPEX get 2% OPEX surcharge')
add_bullet(doc, '15. Technology Lock-In -- same BU getting highest CAPEX for 3+ rounds penalizes others')
doc.add_paragraph()

# 12.2 Round-by-Round Impact Examples
add_styled_heading(doc, '12.2 Worked Example: Three Investment Strategies Compared', level=2)
add_body(doc, (
    'Starting State (Round 1): Treasury $50M. Four BUs: Pharma (Rev $18M, OPEX $11M), '
    'Electronics ($22M/$14M), Consumer Goods ($15M/$9M), Software ($20M/$8M). '
    'Synergy Multiplier 1.00. We compare three strategies over 3 rounds.'
))

# Strategy table
strat_table = doc.add_table(rows=1, cols=4)
strat_table.style = 'Light Grid Accent 1'
hdr = strat_table.rows[0].cells
for i, label in enumerate(['', 'Strategy A: Balanced', 'Strategy B: Concentrated', 'Strategy C: Neglect']):
    hdr[i].text = label
    for p2 in hdr[i].paragraphs:
        for run2 in p2.runs:
            run2.bold = True
            run2.font.size = Pt(9)

strat_rows = [
    ('Pharma Ratio', '0.25', '0.50', '0.00'),
    ('Electronics Ratio', '0.20', '0.50', '0.00'),
    ('Consumer Goods Ratio', '0.20', '0.00', '0.00'),
    ('Software Ratio', '0.15', '0.00', '0.00'),
    ('Total CAPEX', '~$15.5M', '~$20M', '$0'),
    ('Loan Triggered?', 'Yes ($5.5M)', 'Yes ($10M)', 'No'),
    ('Interest Cost', '$660K', '$1.2M', '$0'),
    ('Overrun Risk', '25% chance of +$2.3M', '25% chance of +$3M', 'None'),
]
for sr in strat_rows:
    row = strat_table.add_row().cells
    for i2, val in enumerate(sr):
        row[i2].text = val
        for p2 in row[i2].paragraphs:
            for run2 in p2.runs:
                run2.font.size = Pt(9)

doc.add_paragraph()

# 12.3 OPEX Impact
add_styled_heading(doc, '12.3 OPEX Reduction: How Investment Ratio Drives Synergy', level=2)
add_body(doc, 'The Synergy Engine uses sqrt(ratio) * 0.7 * synergy_multiplier to reduce OPEX. Here is the effect per ratio level:')

opex_table = doc.add_table(rows=1, cols=5)
opex_table.style = 'Light Grid Accent 1'
hdr = opex_table.rows[0].cells
for i, label in enumerate(['Inv. Ratio', 'Effective Ratio', 'OPEX Reduction', 'Example ($11M OPEX)', 'Lag?']):
    hdr[i].text = label
    for p2 in hdr[i].paragraphs:
        for run2 in p2.runs:
            run2.bold = True
            run2.font.size = Pt(9)

opex_rows = [
    ('0.00', '0.00', '0%', '$11.00M (no change)', 'N/A'),
    ('0.05', '0.157', '15.7%', '$9.27M (-$1.73M)', 'Immediate'),
    ('0.10', '0.221', '22.1%', '$8.57M (-$2.43M)', 'Immediate'),
    ('0.15', '0.271', '27.1%', '$8.02M (-$2.98M)', 'Deferred 1 round'),
    ('0.25', '0.350', '35.0%', '$7.15M (-$3.85M)', 'Deferred 1 round'),
    ('0.50', '0.495', '49.5%', '$5.56M (-$5.44M)', 'Deferred 1 round'),
    ('1.00', '0.700', '70.0%', '$3.30M (-$7.70M)', 'Deferred 1 round'),
]
for sr in opex_rows:
    row = opex_table.add_row().cells
    for i2, val in enumerate(sr):
        row[i2].text = val
        for p2 in row[i2].paragraphs:
            for run2 in p2.runs:
                run2.font.size = Pt(9)

add_body(doc, '')
add_body(doc, 'Key Insight:', bold=True)
add_bullet(doc, 'Investments <= 10% apply IMMEDIATELY (minor operational tweaks)')
add_bullet(doc, 'Investments > 10% are DEFERRED 1 round (implementation lag) -- you pay NOW but benefit NEXT round')
add_bullet(doc, 'This creates a critical tension: heavy R1 investment yields zero OPEX savings until R2')
doc.add_paragraph()

# 12.4 Neglect Penalties
add_styled_heading(doc, '12.4 Neglect Cascade: The Cost of Zero Investment', level=2)
add_body(doc, 'When a BU receives zero CAPEX, multiple penalty engines activate simultaneously:')

penalty_table = doc.add_table(rows=1, cols=4)
penalty_table.style = 'Light Grid Accent 1'
hdr = penalty_table.rows[0].cells
for i, label in enumerate(['Penalty Engine', 'Trigger', 'Effect', 'Cumulative Example (3 rounds)']):
    hdr[i].text = label
    for p2 in hdr[i].paragraphs:
        for run2 in p2.runs:
            run2.bold = True
            run2.font.size = Pt(9)

penalty_rows = [
    ('Natural Decay', 'Zero CAPEX this round', 'Rep -2%, SLO -2% per round', 'Rep: 70 -> 68.6 -> 67.2 -> 65.9 (-5.9%)'),
    ('Technical Debt', '2+ consecutive zero rounds', 'OPEX +4% per round (from R2)', 'OPEX: $11M -> $11M -> $11.44M -> $11.9M'),
    ('Talent Neglect', '< 15% share of total CAPEX', 'OPEX +2% surcharge', 'OPEX: +$220K/round extra'),
    ('Inflation (no offset)', 'Always active', 'OPEX +2.5%/round (not offset by synergy)', 'OPEX: $11M -> $11.28M -> $11.56M -> $11.85M'),
    ('Brain-Drain', 'Group Rep < 65 (Software only)', 'OPEX * (1 + (65-rep)/100 * 1.5)', 'If rep=55: OPEX * 1.15 = +$1.27M'),
]
for sr in penalty_rows:
    row = penalty_table.add_row().cells
    for i2, val in enumerate(sr):
        row[i2].text = val
        for p2 in row[i2].paragraphs:
            for run2 in p2.runs:
                run2.font.size = Pt(9)

add_body(doc, '')
add_body(doc, 'Compound Example -- Consumer Goods with zero investment for 4 rounds:', bold=True)
add_bullet(doc, 'Round 1: OPEX=$9M (no change -- penalties have not yet triggered)')
add_bullet(doc, 'Round 2: OPEX=$9M * 1.025 (inflation) = $9.225M. Rep: 70*0.98=68.6, SLO: 78*0.98=76.4')
add_bullet(doc, 'Round 3: OPEX=$9.225M * 1.025 * 1.04 (inflation+tech debt) = $9.83M. Rep=67.2, SLO=74.9')
add_bullet(doc, 'Round 4: OPEX=$9.83M * 1.025 * 1.04 = $10.48M. Rep=65.9, SLO=73.4')
add_bullet(doc, 'Net OPEX increase: $9M -> $10.48M (+16.4%) WITHOUT any crisis or external shock')
doc.add_paragraph()

# 12.5 Round-Specific Investment Effects
add_styled_heading(doc, '12.5 Round-Specific Investment Effects', level=2)
add_body(doc, 'Beyond the general engines, specific rounds amplify or modify how investments work:')

round_fx_table = doc.add_table(rows=1, cols=3)
round_fx_table.style = 'Light Grid Accent 1'
hdr = round_fx_table.rows[0].cells
for i, label in enumerate(['Round', 'Investment-Specific Effect', 'Example']):
    hdr[i].text = label
    for p2 in hdr[i].paragraphs:
        for run2 in p2.runs:
            run2.bold = True
            run2.font.size = Pt(9)

round_fx_rows = [
    ('R1', 'Investments > 10% deferred; no synergy benefit until R2. Foundation flags set by A/B/C choice.', 'Pharma @ 0.25 ratio -> OPEX savings queued for R2. Immediate cost: $4.5M CAPEX.'),
    ('R2', 'Materiality alignment (Option A) earns +0.10 M_R at terminal valuation. Investment builds governance baseline.', 'CSRD investment: $3M cost now -> $67M terminal value increase.'),
    ('R3', 'Green Bond (Option B) cost modulated by R2 flags. NCD delta from option applied to all BUs.', 'R2A discount: Green Bond costs $2.5M instead of $3M. R2C premium: costs $4M.'),
    ('R4', 'Contagion halved if reputation > 60. Social media velocity amplifies low reputation. Investment in SLO-linked BUs critical.', 'Electronics at 0% -> SLO decays -> contagion amplifier = 1.1x. Investing 0.15 prevents decay.'),
    ('R5', 'Resilience infrastructure DEFERRED 2 rounds. Zero protection this round regardless of investment.', '$8M coastal defence: pays in R7. Cyclone hits R5 at full $12M. Net cost if hit: $20M.'),
    ('R6', 'AI monetization (Option A) triggers EU AI Act compliance from R7: $3M/round + gov risk +5.', 'R6A generates +$5M software revenue but commits $3M/round indefinitely. Break-even: 2 rounds.'),
    ('R7', 'Synergy multiplier boost scaled by workforce readiness. Early Decarboniser (R3A) adds +0.10 synergy.', 'R7C synergy boost 0.35 * readiness 0.70 (low) = 0.245 effective. With high readiness: 0.35 * 1.10 = 0.385.'),
    ('R8', 'Water infrastructure DEFERRED 2 rounds. Desalination payback generates revenue over subsequent rounds.', 'Desalination: $15M now -> $2M/round revenue from R10. NCD reduction arrives R10.'),
    ('R9', 'Strike probability increases with low SLO + high burnout. Investment in community fund costs $20M but earns +0.18 M_R.', 'SLO=35, burnout=65: P_strike=0.57. If strike fires: entire round revenue lost (~$75M).'),
    ('R10', 'Investments flow directly into terminal EBITDA via final revenue-OPEX calculation. Green Fund balance adds to EBITDA.', 'Final CAPEX of $5M -> OPEX savings deferred (too late). Better to have invested in R8-R9.'),
]
for sr in round_fx_rows:
    row = round_fx_table.add_row().cells
    for i2, val in enumerate(sr):
        row[i2].text = val
        for p2 in row[i2].paragraphs:
            for run2 in p2.runs:
                run2.font.size = Pt(9)

doc.add_paragraph()

# 12.6 Terminal Value Impact
add_styled_heading(doc, '12.6 Investment Strategy vs Terminal Value: Full Lifecycle Comparison', level=2)
add_body(doc, 'Three players start identically. Their investment patterns over 10 rounds produce vastly different terminal outcomes:')

tv_table = doc.add_table(rows=1, cols=5)
tv_table.style = 'Light Grid Accent 1'
hdr = tv_table.rows[0].cells
for i, label in enumerate(['Metric', 'Balanced Investor', 'Concentrated Investor', 'Zero Investor']):
    hdr[i].text = label
    for p2 in hdr[i].paragraphs:
        for run2 in p2.runs:
            run2.bold = True
            run2.font.size = Pt(9)

tv_rows = [
    ('Avg Inv Ratio', '0.20 across all BUs', '0.50 on 2 BUs, 0.0 on 2', '0.0 on all BUs'),
    ('Total CAPEX (10 rounds)', '~$150M', '~$200M', '$0'),
    ('Loan Interest Paid', '~$6M', '~$18M', '$0'),
    ('Final OPEX (sum)', '~$28M (synergy reduced)', '~$22M (2 BUs) + $26M (2 neglected)', '~$56M (inflation+debt)'),
    ('Final Revenue (sum)', '~$76M (stable)', '~$60M (2 cannibalized)', '~$68M (decay + cannibal)'),
    ('Terminal EBITDA', '~$47M', '~$34M', '~$12M'),
    ('M_R Achievable', '1.65 (all bonuses possible)', '1.25 (missing SLO, lock-in)', '0.60 (instability + no flags)'),
    ('Terminal Value', '~$930M', '~$510M', '~$86M'),
    ('Profile', 'De-risked Safe Haven', 'Fragile Giant', 'Stranded Relic'),
]
for sr in tv_rows:
    row = tv_table.add_row().cells
    for i2, val in enumerate(sr):
        row[i2].text = val
        for p2 in row[i2].paragraphs:
            for run2 in p2.runs:
                run2.font.size = Pt(9)

add_body(doc, '')
add_body(doc, 'Key Takeaways for Facilitators:', bold=True)
add_bullet(doc, 'Balanced investment (0.15-0.25 across all BUs) outperforms concentrated investment by ~80% in terminal value')
add_bullet(doc, 'Zero investment is catastrophic: compound penalties (decay + tech debt + inflation + brain-drain) create a ~$850M terminal value gap')
add_bullet(doc, 'Implementation lag means R1-R2 investments only show OPEX benefit from R2-R3; early players may feel "nothing is happening"')
add_bullet(doc, 'Over-concentration triggers Technology Lock-In (3+ rounds) which penalizes OTHER BUs\' synergy by 15%')
add_bullet(doc, 'The loan mechanism (12% interest) is intentionally expensive -- it teaches capital constraint management')
add_bullet(doc, 'Emergency credit ($1M at rate+2%) is a pedagogical trap: it feels helpful but compounds aggressively')

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 13: INVESTMENT-TO-SCORE RATIONALE
# ═══════════════════════════════════════════════════════════════
add_styled_heading(doc, '13. Investment-to-Score Rationale: Why Investment Improves Player Scores', level=1)
add_body(doc, (
    'Player competency is assessed across 6 dimensions on a 1-10 scale. Each dimension score is a 50/50 blend '
    'of data-derived metrics (from simulation performance) and LLM-assessed interview responses. This section '
    'traces the mathematical causal chain from investment slider decisions through engine calculations to final '
    'scores, proving that thoughtful investment is the primary lever for improving assessment outcomes.'
))

# 13.1 Scoring Framework
add_styled_heading(doc, '13.1 The Six Competency Dimensions & Their Formulas', level=2)
add_body(doc, 'Each dimension draws from specific simulation metrics. The data-derived score (50% weight) is calculated as follows:')

dim_table = doc.add_table(rows=1, cols=4)
dim_table.style = 'Light Grid Accent 1'
hdr = dim_table.rows[0].cells
for i, label in enumerate(['Dimension', 'Formula (Data Score)', 'Metric Range -> Score', 'Investment Lever']):
    hdr[i].text = label
    for p2 in hdr[i].paragraphs:
        for run2 in p2.runs:
            run2.bold = True
            run2.font.size = Pt(9)

dim_rows = [
    ('Strategic Thinking',
     'min(10, max(1, (M_R - 0.5) / 0.15))',
     'M_R 0.5->1, M_R 2.0->10',
     'Every M_R bonus (R2A, R6B, R7C, R9C) + avoiding SLO<75 instability'),
    ('Stakeholder Empathy',
     'min(10, avg_SLO/10 + burnout_bonus)',
     'SLO 0->0, SLO 100->10; Burnout<30: +2, <60: +1',
     'Balanced BU investment prevents SLO decay; HR investment reduces burnout'),
    ('Financial Acumen',
     'min(10, Treasury/$5M + EBITDA/$10M)',
     'Treasury $25M->5; EBITDA $50M->5; max 10',
     'Synergy-driven OPEX reduction -> higher EBITDA; avoiding loans -> higher treasury'),
    ('Ethical Reasoning',
     '4.0 + 2.5*(ethical_ai) + 2.0*(community_fund) + 1.0*(deep_audit)',
     'Base=4; max flags->9.5',
     'R6B (ethical AI +2.5), R9C (community fund +2.0), deep audit +1.0'),
    ('Systems Thinking',
     'min(10, (synergy-0.7)*10 + VRIO_avg/20)',
     'Synergy 0.7->0, 1.2->5; VRIO 0->0, 100->5',
     'R7C synergy boost + balanced investment for VRIO development'),
    ('Adaptive Leadership',
     'min(10, readiness/15 + HR_rounds*1.0)',
     'Readiness 75->5; HR rounds 5->5',
     'Consistent HR pillar investment every round'),
]
for sr in dim_rows:
    row = dim_table.add_row().cells
    for i2, val in enumerate(sr):
        row[i2].text = val
        for p2 in row[i2].paragraphs:
            for run2 in p2.runs:
                run2.font.size = Pt(8)

doc.add_paragraph()

# 13.2 Causal Chains
add_styled_heading(doc, '13.2 Causal Chains: Slider -> Engine -> Metric -> Score', level=2)
add_body(doc, 'Each investment decision triggers a chain of engine calculations that ultimately determines a competency score. Here are the 6 primary chains:')

add_body(doc, '(1) Strategic Thinking: Investment -> M_R -> Score', bold=True)
add_bullet(doc, 'Slider: Balanced investment (0.15-0.25 per BU) reduces OPEX via Synergy Engine')
add_bullet(doc, 'Engine: Lower OPEX -> higher Terminal EBITDA -> higher Terminal Value')
add_bullet(doc, 'Engine: Investment enables flag collection: R2A (+0.10), R6B (+0.15), R7C (+0.30), R9C (+0.18)')
add_bullet(doc, 'Engine: SLO >= 75 avoids -0.40 Instability Discount')
add_bullet(doc, 'Metric: M_R = 1.0 + sum(bonuses) - penalties')
add_bullet(doc, 'Score: (M_R - 0.5) / 0.15, clamped to [1, 10]')
add_bullet(doc, 'Example: M_R=1.65 -> (1.65-0.5)/0.15 = 7.67 -> Strategic Thinking data score = 7.7/10')

add_body(doc, '(2) Stakeholder Empathy: Investment -> SLO & Burnout -> Score', bold=True)
add_bullet(doc, 'Slider: Non-zero investment prevents Natural Decay (SLO -2%/round per neglected BU)')
add_bullet(doc, 'Engine: HR pillar investment reduces burnout (-10 high, -4 medium vs +3 drift/round)')
add_bullet(doc, 'Metric: avg_SLO and avg_burnout at game end')
add_bullet(doc, 'Score: SLO/10 + burnout_bonus (2 if <30, 1 if <60, 0 otherwise)')
add_bullet(doc, 'Example: SLO=72, burnout=25 -> 72/10 + 2.0 = 7.2 + 2.0 = 9.2/10')
add_bullet(doc, 'Counter: SLO=40 (neglect), burnout=65 (no HR) -> 4.0 + 0 = 4.0/10')

add_body(doc, '(3) Financial Acumen: Investment -> OPEX/EBITDA/Treasury -> Score', bold=True)
add_bullet(doc, 'Slider: Investment ratio drives Synergy Engine: OPEX_new = OPEX * (1 - sqrt(ratio)*0.7*synergy)')
add_bullet(doc, 'Engine: Lower OPEX -> higher gross profit -> higher treasury')
add_bullet(doc, 'Engine: Over-investment triggers 12% loan interest -> treasury drain')
add_bullet(doc, 'Metric: Treasury ($ absolute) + EBITDA ($ absolute) at game end')
add_bullet(doc, 'Score: Treasury/$5M + EBITDA/$10M, capped at 10')
add_bullet(doc, 'Example: Treasury=$35M, EBITDA=$45M -> 35/5 + 45/10 = 7.0 + 4.5 = 10.0 (capped)')
add_bullet(doc, 'Counter: Treasury=-$5M (over-borrowed), EBITDA=$15M -> 0 + 1.5 = 1.5/10')

add_body(doc, '(4) Ethical Reasoning: Decision Node -> Flags -> Score', bold=True)
add_bullet(doc, 'Slider: Not directly driven by investment ratio but by A/B/C choice')
add_bullet(doc, 'Engine: R6 Option B sets ethical_ai_overhaul flag (+2.5 to score)')
add_bullet(doc, 'Engine: R9 Option C sets community_fund flag (+2.0 to score)')
add_bullet(doc, 'Engine: Deep audit flag from governance choices (+1.0 to score)')
add_bullet(doc, 'Score: 4.0 (baseline) + flag bonuses, capped at 10')
add_bullet(doc, 'Example: R6B + R9C + deep_audit -> 4.0 + 2.5 + 2.0 + 1.0 = 9.5/10')
add_bullet(doc, 'Counter: R6A (monetise AI) + R9A (immediate closure) -> 4.0 + 0 = 4.0/10')
add_bullet(doc, 'Investment link: Ethical choices often cost more CAPEX (R6B costs $5M vs R6A gains $5M) -- investment budget enables ethical decisions')

add_body(doc, '(5) Systems Thinking: Investment -> Synergy & VRIO -> Score', bold=True)
add_bullet(doc, 'Slider: Balanced cross-BU investment builds VRIO capability scores')
add_bullet(doc, 'Engine: R7C circularity option unlocks synergy_multiplier boost (+0.35)')
add_bullet(doc, 'Engine: Workforce readiness modulates synergy effectiveness (low readiness = -30%)')
add_bullet(doc, 'Metric: synergy_multiplier + VRIO capability average')
add_bullet(doc, 'Score: (synergy-0.7)*10 + VRIO_avg/20, capped at 10')
add_bullet(doc, 'Example: synergy=1.38, VRIO_avg=65 -> (1.38-0.7)*10 + 65/20 = 6.8 + 3.25 = 10.0 (capped)')

add_body(doc, '(6) Adaptive Leadership: HR Investment -> Readiness -> Score', bold=True)
add_bullet(doc, 'Slider: HR pillar investment counts as a "HR invested" flag each round')
add_bullet(doc, 'Engine: High HR investment adds +8 readiness/round; no investment subtracts -5/round')
add_bullet(doc, 'Metric: workforce_readiness (0-100) + HR_rounds_invested (count)')
add_bullet(doc, 'Score: readiness/15 + HR_rounds * 1.0, capped at 10')
add_bullet(doc, 'Example: readiness=80, HR invested 7/10 rounds -> 80/15 + 7.0 = 5.3 + 7.0 = 10.0 (capped)')
add_bullet(doc, 'Counter: readiness=25 (atrophied), HR invested 1/10 -> 25/15 + 1.0 = 1.7 + 1.0 = 2.7/10')

doc.add_paragraph()

# 13.3 Optimal Investment Roadmap
add_styled_heading(doc, '13.3 Optimal Investment Roadmap for Maximum Scores', level=2)
add_body(doc, 'The following round-by-round investment plan maximizes all 6 dimension scores simultaneously:')

roadmap_table = doc.add_table(rows=1, cols=5)
roadmap_table.style = 'Light Grid Accent 1'
hdr = roadmap_table.rows[0].cells
for i, label in enumerate(['Round', 'Investment Strategy', 'Decision Choice', 'Key Flags Earned', 'Dimensions Impacted']):
    hdr[i].text = label
    for p2 in hdr[i].paragraphs:
        for run2 in p2.runs:
            run2.bold = True
            run2.font.size = Pt(8)

roadmap_rows = [
    ('R1', '0.20 balanced across all BUs + HR pillar', 'A or B (foundation)', 'HR flag', 'Financial, Adaptive'),
    ('R2', '0.20 balanced + HR pillar', 'A (Full Materiality)', 'materiality_aligned', 'Strategic (+0.10 M_R), Adaptive'),
    ('R3', '0.15 balanced + HR pillar', 'A (Scope 3 Audit)', 'early_decarboniser', 'Systems (+0.10 synergy at R7), Adaptive'),
    ('R4', '0.20 balanced + HR pillar', 'A or B (Contagion)', 'HR flag', 'Stakeholder (SLO preserved), Adaptive'),
    ('R5', '0.15 balanced + HR pillar', 'B (Nature-Based)', 'nature_resilience', 'Strategic (avoids bailout -> +0.20 M_R), Adaptive'),
    ('R6', '0.15 balanced + HR pillar', 'B (Ethical AI)', 'ethical_ai_overhaul', 'Ethical (+2.5), Strategic (+0.15 M_R), Adaptive'),
    ('R7', '0.25 balanced + HR pillar', 'C (Circularity)', 'synergy_unlock', 'Systems (+0.35 synergy), Strategic (+0.30 M_R), Adaptive'),
    ('R8', '0.20 balanced + HR pillar', 'A (Water Stewardship)', 'water_stewards', 'Strategic (avoids bailout), Stakeholder, Adaptive'),
    ('R9', '0.15 balanced + HR pillar', 'C (Community Fund)', 'community_fund', 'Ethical (+2.0), Strategic (+0.18 M_R), Adaptive'),
    ('R10', '0.10 balanced', 'A (Resist & Integrate)', '--', 'All dimensions (terminal)'),
]
for sr in roadmap_rows:
    row = roadmap_table.add_row().cells
    for i2, val in enumerate(sr):
        row[i2].text = val
        for p2 in row[i2].paragraphs:
            for run2 in p2.runs:
                run2.font.size = Pt(8)

doc.add_paragraph()

# 13.4 Expected Scores
add_styled_heading(doc, '13.4 Expected Scores: Optimal vs Neglect Comparison', level=2)
add_body(doc, 'Given the optimal roadmap above vs a player who invests zero and takes the cheapest option each round:')

score_table = doc.add_table(rows=1, cols=5)
score_table.style = 'Light Grid Accent 1'
hdr = score_table.rows[0].cells
for i, label in enumerate(['Dimension', 'Optimal Data Score', 'Neglect Data Score', 'Optimal Final (50/50)', 'Neglect Final (50/50)']):
    hdr[i].text = label
    for p2 in hdr[i].paragraphs:
        for run2 in p2.runs:
            run2.bold = True
            run2.font.size = Pt(8)

score_rows = [
    ('Strategic Thinking', '10.0 (M_R=2.08)', '1.0 (M_R=0.60)', '~8.5*', '~3.0*'),
    ('Stakeholder Empathy', '9.2 (SLO=72, BO=25)', '4.0 (SLO=40, BO=65)', '~8.0', '~4.5'),
    ('Financial Acumen', '10.0 (T=$35M, E=$45M)', '1.5 (T=-$5M, E=$15M)', '~8.5', '~3.5'),
    ('Ethical Reasoning', '9.5 (3 flags)', '4.0 (0 flags)', '~8.0', '~4.5'),
    ('Systems Thinking', '10.0 (syn=1.38, VRIO=65)', '1.0 (syn=1.0, VRIO=10)', '~8.0', '~3.0'),
    ('Adaptive Leadership', '10.0 (rd=80, HR=7)', '2.7 (rd=25, HR=1)', '~8.5', '~3.5'),
]
for sr in score_rows:
    row = score_table.add_row().cells
    for i2, val in enumerate(sr):
        row[i2].text = val
        for p2 in row[i2].paragraphs:
            for run2 in p2.runs:
                run2.font.size = Pt(8)

add_body(doc, '* Final scores assume a median LLM interview score of 5.0 for the response component (50% weight).')
doc.add_paragraph()

add_body(doc, 'Key Mathematical Insight:', bold=True)
add_body(doc, (
    'The scoring system is designed so that investment decisions are the DOMINANT driver of competency scores. '
    'Even a perfect interview (10/10 on all responses) cannot compensate for poor simulation performance: '
    'a neglect player with flawless interview answers would score (1.0*0.5 + 10*0.5) = 5.5 on Strategic Thinking, '
    'while an optimal investor with average interview answers (5/10) scores (10.0*0.5 + 5.0*0.5) = 7.5. '
    'The simulation performance floor creates a ~2-point advantage that cannot be talked away.'
))

add_body(doc, 'Pedagogical Design Rationale:', bold=True)
add_bullet(doc, 'The 50/50 blend prevents "gaming" -- students cannot simply memorize answers to score well')
add_bullet(doc, 'Data scores reward CONSISTENT strategic behaviour (flags must be earned across multiple rounds)')
add_bullet(doc, 'The M_R -> Strategic Thinking formula has the steepest slope (0.15 per point), making it the hardest to maximize -- this is intentional since it captures the simulation\'s core learning objective')
add_bullet(doc, 'Ethical Reasoning has the most granular flag system (3 separate flags) to reward holistic ethical decision-making, not a single lucky choice')
add_bullet(doc, 'Adaptive Leadership is the only dimension that rewards FREQUENCY of investment (HR rounds count), not just magnitude -- teaching that consistency matters more than grand gestures')
add_bullet(doc, 'The Instability Discount (-0.40 M_R when SLO<75) creates a mathematical cliff: it simultaneously punishes Strategic Thinking AND Stakeholder Empathy, making neglect doubly costly')

doc.add_page_break()

# 13.5 Regulatory Sandbox
add_styled_heading(doc, '13.5 Regulatory Sandbox & Polycentric Governance Outcomes', level=2)
add_body(doc, (
    "The Regulatory Sandbox enables facilitators to dynamically inject regulatory instruments (e.g., Carbon Tax, Due Diligence, Nature Restoration) "
    "to test cohort resilience under Ostrom's polycentric governance model. These instruments mathematically interact with the core engine and influence competency scores."
))

reg_table = doc.add_table(rows=1, cols=4)
reg_table.style = 'Light Grid Accent 1'
hdr = reg_table.rows[0].cells
for i, label in enumerate(['Instrument', 'Core Mechanism', 'Polycentric Governance Outcome', 'Score Impact (M_R / Competency)']):
    hdr[i].text = label
    for p2 in hdr[i].paragraphs:
        for run2 in p2.runs:
            run2.bold = True
            run2.font.size = Pt(8)

reg_rows = [
    ('Carbon Tax (Pigovian)', 'Deducts $X per ton from treasury based on CI', 'Internalizes environmental externalities, forcing rapid transition strategies.', 'M_R (-0.15 if high emission), Financial Acumen down if unprepared'),
    ('Mandatory Due Diligence', 'Flags Scope 3 vulnerabilities, increases compliance OPEX', 'Promotes transparency and accountability across global supply chains.', 'Ethical Reasoning (+1.5 if proactive), Stakeholder Empathy (+1.0)'),
    ('Nature Restoration', 'Increases Natural Capital Debt penalty slope', 'Enforces systemic ecological regeneration beyond mere risk mitigation.', 'Strategic Thinking (penalizes stranded assets), Systems Thinking (+2.0 if restored)'),
    ('Just Transition Fund', 'Grants +$Y M per round to low-carbon BUs', 'Redistributes capital to ensure equitable socio-economic shifts.', 'Stakeholder Empathy (+2.0), Financial Acumen (+1.0 for capturing subsidies)'),
]
for sr in reg_rows:
    row = reg_table.add_row().cells
    for i2, val in enumerate(sr):
        row[i2].text = val
        for p2 in row[i2].paragraphs:
            for run2 in p2.runs:
                run2.font.size = Pt(8)

add_body(doc, '')
add_body(doc, 'Facilitator Guidance:', bold=True)
add_bullet(doc, 'Use instruments progressively. E.g., introduce Due Diligence in R4, followed by Carbon Tax in R6.')
add_bullet(doc, "Highlight Stigler's Theory of Economic Regulation when discussing compliance costs versus strategic opportunities.")

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SECTION 14: FULL GAME WALKTHROUGH
# ═══════════════════════════════════════════════════════════════
from section14_walkthrough import write_section_14
write_section_14(doc, add_styled_heading, add_body, add_bullet)
doc.add_page_break()

# ═══════════════════════════════════════════════════════════════
#  SAVE
# ═══════════════════════════════════════════════════════════════
output_path = r"c:\Users\Home\.gemini\antigravity\scratch\muressons-sim\Muressons_Simulation_Briefings.docx"
doc.save(output_path)
print(f"[OK] Document saved to: {output_path}")
print(f"   Size: {os.path.getsize(output_path) / 1024:.0f} KB")
