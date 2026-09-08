import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter14_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
SPEC = [
 ("That is the whole argument of Chapter 5, arriving as arithmetic",
  "fig14_01_valuation_bridge", "14.1",
  "Every modifier the Regenerative Multiple can add, on one path.",
  "Waterfall from a base of 1.00 through Materiality Governance plus 0.10, the Synergy Strategic Premium "
  "plus 0.15, Resilience Champion plus 0.20, Truth Premium plus 0.15, Community Champion plus 0.27 after "
  "Just Transition scaling of 1.5, Workforce Excellence plus 0.10 and Wellbeing Champion plus 0.05, to a "
  "Regenerative Multiple of 2.02. Reference lines mark the published ceiling of 2.02 with Just Transition "
  "scaling and 1.93 without it.", 6.4),

 ("this is the same instrument pointed at a ceiling",
  "fig14_03_multiple_vs_wacc", "14.2",
  "The exit multiple against the cost of capital, and what the two levers are worth together.",
  "Two panels. Left: the Gordon-growth exit multiple against the cost of capital, capped at 18 times and "
  "floored at 6, with the cap breaking at 7.67 per cent and the floor binding above about 20 per cent. "
  "Right: terminal value against the cost of capital for four values of the Regenerative Multiple — 2.02, "
  "1.44, 1.00 and 0.40. Across the whole plausible range of the cost of capital the multiple stays pinned "
  "at 18 times, while the Regenerative Multiple moves terminal value by a factor of five.", 6.4),

 ("a figure of 2.33 that circulated in earlier material is gone",
  "fig14_04_component_table", "14.3",
  "The twelve components, what sets each, and whether it is a cliff or a ramp.",
  "Reference table of the twelve Regenerative Multiple components in the order the function applies them, "
  "with the value each carries, the flag or state that sets it, how it is earned, and whether it is applied "
  "as a hard cliff or ramped over a band. Four are ramped: the Synergy Strategic Premium over a 0.10 band "
  "of the synergy multiplier, and Workforce Excellence, Wellbeing Champion and the Instability Discount "
  "over ten-point bands. Resilience Champion is the only component granted by default.", 6.4),

 ("it is a restructuring",
  "fig14_02_mr_waterfalls", "14.4",
  "Three teams, one structure: the Regenerative Multiple and the terminal value it produces.",
  "Three waterfalls side by side. A regenerative team earning every flag reaches a Regenerative Multiple "
  "of 2.02 and a terminal value of 596 million dollars. A competent team taking partial materiality "
  "credit, Resilience Champion, a Just Transition bonus and part of the workforce ramp reaches 1.44 and "
  "426 million. An extractive team taking the Planet Expendable penalty and the full Instability Discount "
  "reaches 0.40 and 118 million. All three are computed at the 18 times ceiling on the same 16.39 million "
  "of terminal EBITDA.", 6.4),
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
