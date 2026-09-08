import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter10_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
SPEC = [
 ("Round 6's Quiet Patch adds exactly that, and its sticker price is",
  "fig10_01_governance_propagation", "10.1",
  "Governance risk, and the four channels it runs down.",
  "Diagram. One unit's governance risk score feeds four channels: every other unit's OPEX, through a "
  "supply-chain contagion surcharge of the unit's opex times the sum of the other units' governance risk "
  "times 0.002; the Round 9 strike probability; the cost of capital, through a premium of 0.0006 for each "
  "point of mean governance risk above 25; and the regulator NPC, whose formal-investigation trigger fires "
  "above 60. Staff burnout above 70 feeds back into governance risk. A bar chart beneath gives the "
  "contagion surcharge each unit pays at the opening state: Pharma 1.32 million a round, Electronics 1.15, "
  "Consumer Goods 0.90, Software 0.49 — none of it caused by the unit paying it.", 6.4),

 ("It makes it impossible to reach the wrong one without noticing",
  "fig10_02_five_lenses", "10.2",
  "Five ethical lenses on the Round 6 decision.",
  "Table. The three Round 6 options are set out with their engine impacts: A monetise the algorithm, plus "
  "10 million Software revenue, minus 20 reputation, minus 15 licence, plus 8 governance risk; B ethical "
  "AI overhaul, minus 8 million, plus 15 licence, plus 5 reputation, minus 5 governance, plus 0.8 million "
  "revenue per unit; C quiet patch, minus 1 million, minus 5 reputation, plus 10 governance risk. Five "
  "lenses are then applied — consequences, duty, rights, virtue and justice — each with its question and "
  "its reading of the three options. Four of the five land on B; the one that does not, consequences, is "
  "the only one the cockpit shows a number for.", 6.4),

 ("The core game's auditor is the regulator agent",
  "fig10_04_greenwashing", "10.3",
  "The greenwashing detector, and the five forms it does and does not catch.",
  "Two panels. Left: the social licence penalty against the team's share of the Corporate Strategic Fund "
  "pool. A full green claim backed by less than 15 per cent of the pool costs 15 licence points; a "
  "moderate claim backed by less than 10.05 per cent costs 7.5. Right: five forms of greenwashing — "
  "selective disclosure, empty claim, symbolic action, misleading baseline and concealed remediation — "
  "each with a mechanic or dictionary entry in the build that instantiates it. The detector catches only "
  "the second.", 6.4),

 ("In their official wording",
  "fig10_03_ngrbc_map", "10.4",
  "The nine NGRBC principles against the rounds of the BRSR side track.",
  "Grid with the nine NGRBC principles as rows and the ten BRSR side-track rounds as columns. Principle 1, "
  "integrity and transparency, is marked at Round 1; Principle 2, sustainable and safe goods, at Round 3; "
  "Principle 3, employee well-being, at Round 2; Principle 4, stakeholder responsiveness, at Round 9; "
  "Principle 5, human rights, at Rounds 2 and 6; Principle 6, the environment, at Round 3; Principle 7, "
  "responsible policy influence, at Rounds 1 and 7; Principle 8, inclusive growth, at Round 8; Principle "
  "9, responsible consumer engagement, at Round 9. Rounds 4, 5 and 10 carry no single principle: they are "
  "the integrative rounds.", 6.4),
]
d = Document(DOC)
print("stripped", figdoc.strip_figures(d))
ps = list(iter_paras(d))
placed = []
for needle, fname, num, cap, alt, w in SPEC:
    hits = [p for p in ps if needle in ptext(p)]
    assert len(hits) == 1, f"{needle!r}: {len(hits)}"
    figdoc.insert_after_para(d, hits[0], os.path.join(FIG, fname + ".png"), num, cap, alt, width_in=w)
    placed.append(num)
tmp = os.path.expanduser("~/audit_scratch/tmp_out.docx")
d.save(tmp)
try:
    shutil.copyfile(tmp, DOC); print("WROTE", os.path.basename(DOC), placed)
except PermissionError:
    dest = os.path.expanduser("~/mnt/muressons-sim/docs/_pending_close_word/" + os.path.basename(DOC))
    os.makedirs(os.path.dirname(dest), exist_ok=True); shutil.copyfile(tmp, dest); print("LOCKED -> pending")
