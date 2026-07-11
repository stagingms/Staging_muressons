import re

with open('frontend/app/components/CreateCohortModal.js', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('<div className={styles.formGrid}>\n                            <div className={styles.formColumn}>', '')
content = content.replace('                            </div>\n\n                            <div className={styles.formColumn}>', '')
content = content.replace('                            </div>\n                        </div>\n\n                        <div className={styles.footer}>', '<div className={styles.footer}>')

def extract_section(start_marker, end_marker=None):
    if end_marker:
        pattern = re.compile(rf'({re.escape(start_marker)}.*?){re.escape(end_marker)}', re.DOTALL)
        match = pattern.search(content)
        if match:
            return match.group(1)
    else:
        pattern = re.compile(rf'({re.escape(start_marker)}.*?)(?=\n\s*{{/\*\s*──\s*Section)', re.DOTALL)
        match = pattern.search(content)
        if match:
            return match.group(1)
    return ''

sec1 = extract_section('{/* ── Section 1: Core Details ── */}')
sec2 = extract_section('{/* ── Section 2: Decision Paradigm ── */}')
sec3 = extract_section('{/* ── Section 3: Scenario & Display Currency ── */}')
sec35 = extract_section('{/* ── Section 3.5: Ending Pathway ── */}')
sec37 = extract_section('{/* ── Section 3.7: CEO Interview ── */}')
sec39 = extract_section('{/* ── Section 3.9: Side Tracks ── */}')
sec4 = extract_section('{/* ── Section 4: Team Interventions', end_marker='{/* ── Section 5:')
if sec4.endswith('{/* ── Section 5:'):
    sec4 = sec4[:-17].rstrip()

sec5 = extract_section('{/* ── Section 5: Pedagogical Scaffolding ── */}')
sec6 = extract_section('{/* ── Section 6: Analytics Visibility ── */}', '<div className={styles.footer}>')

if not all([sec1, sec2, sec3, sec35, sec37, sec39, sec4, sec5, sec6]):
    print('Failed to extract some sections')
    print(bool(sec1), bool(sec2), bool(sec3), bool(sec35), bool(sec37), bool(sec39), bool(sec4), bool(sec5), bool(sec6))
    exit(1)

for sec in [sec1, sec2, sec3, sec35, sec37, sec39, sec4, sec5, sec6]:
    content = content.replace(sec, '')

new_body = f"""
                        <AccordionItem id="core" title="1. Core Configuration" summary="Cohort Name, Facilitator, Scenario, & Currency">
{sec1}
{sec3}
                        </AccordionItem>

                        <AccordionItem id="engine" title="2. Simulation Engine" summary="Decision Paradigm & Ending Pathway">
{sec2}
{sec35}
                        </AccordionItem>

                        <AccordionItem id="modules" title="3. Optional Modules" summary="Side Tracks & CEO Interview">
{sec39}
{sec37}
                        </AccordionItem>

                        <AccordionItem id="interventions" title="4. Team Interventions" summary="Manual Overrides & Swipe Files">
{sec4}
                        </AccordionItem>

                        <AccordionItem id="pedagogy" title="5. Pedagogy & Analytics" summary="Difficulty, Toggles, and Visibility">
{sec5}
{sec6}
                        </AccordionItem>

                        <div className={{styles.footer}}>
"""

content = content.replace('<div className={styles.footer}>', new_body)

with open('frontend/app/components/CreateCohortModal.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('Success')
