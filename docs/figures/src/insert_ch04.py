import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc

DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter04_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")

SPEC = [
 ("the greenwashing detector in Chapter 10 exists because that pattern is common enough to model",
  "fig04_01_quadrant", "4.1",
  "The quadrant, with §4.5.1's default eight issues placed by the engine's own classifier.",
  "Scatter plot with financial materiality on the horizontal axis and impact materiality on the vertical, "
  "divided into four quadrants by dashed lines at the boundary between medium and high. Five issues sit in "
  "Q1, double materiality: plastic waste, e-waste, drug safety, API leakage and data privacy. Two sit in "
  "Q2, impact only: biodiversity and supply-chain labour. One sits in Q3, financial only: energy cost "
  "exposure. Q4 is empty — the default dictionary contains no low-low distractor. Quadrants are "
  "distinguished by marker shape as well as colour.", 6.4),

 ("what did this cost us, and what did we stop doing",
  "fig04_02_six_steps", "4.2",
  "The six steps, what each decides, and the evidence each must leave behind.",
  "Six numbered steps flowing downward: context and value chain; identify impacts, risks and opportunities; "
  "score and threshold; stakeholder engagement; validation and audit trail; link to strategy, targets and "
  "capital. Each row states what the step decides and the evidence it must leave. A fourth column is left "
  "blank for the reader to name the owner of each step.", 6.4),

 ("where the regimes genuinely conflict",
  "fig04_03_esrs_map", "4.3",
  "The ten ESRS topical standards against the ten rounds and the five pillars.",
  "Grid with the ten ESRS topical standards as rows and the ten simulation rounds as columns. A marked cell "
  "means the build carries a mechanic for that standard in that round; a dash means it does not. E1 climate "
  "change is marked at rounds 3, 5 and 10; E2 pollution at round 7; E3 water at round 8; E4 biodiversity at "
  "rounds 2 and 8; E5 circular economy at round 7; S1 own workforce at round 9; S2 workers in the value "
  "chain at rounds 2 and 4; S3 affected communities at rounds 4 and 8; S4 consumers and end-users at rounds "
  "2 and 6; G1 business conduct at rounds 6 and 10. A right-hand column names the pillars that act on each "
  "standard; S4 alone has none. A key beneath states the state variable, dictionary entry or round option "
  "that grounds every row.", 6.4),
]

d = Document(DOC)
print("stripped", figdoc.strip_figures(d))
ps = list(iter_paras(d))
placed = []
for needle, fname, num, cap, alt, w in SPEC:
    hits = [p for p in ps if needle in ptext(p)]
    assert len(hits) == 1, f"{needle!r}: {len(hits)} matches"
    figdoc.insert_after_para(d, hits[0], os.path.join(FIG, fname + ".png"), num, cap, alt, width_in=w)
    placed.append(num)
tmp = os.path.expanduser("~/audit_scratch/tmp_out.docx")
d.save(tmp)
try:
    shutil.copyfile(tmp, DOC); print("WROTE", os.path.basename(DOC), placed)
except PermissionError:
    dest = os.path.expanduser("~/mnt/muressons-sim/docs/_pending_close_word/" + os.path.basename(DOC))
    os.makedirs(os.path.dirname(dest), exist_ok=True); shutil.copyfile(tmp, dest); print("LOCKED -> pending")
