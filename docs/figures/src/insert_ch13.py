import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter13_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
SPEC = [
 ("both start on the flat part of their curve",
  "fig13_01_wacc_bridge", "13.1",
  "The WACC bridge at the opening state, and the multiple it does not move.",
  "Two panels. Left: a bridge from the 5.00 per cent base rate through a carbon premium of 0.42 points, a "
  "governance premium of nothing because mean governance risk of 17.5 is below the 25 floor, a licence "
  "discount of nothing because mean licence of 50 is at its floor, and a nature premium of 0.76 points, to "
  "a cost of capital of 6.18 per cent. Right: the exit multiple against the cost of capital, a "
  "Gordon-growth curve capped at 18 times and floored at 6. The cap binds until 7.67 per cent, so the "
  "whole 1.18-point ESG adjustment changes the multiple by nothing at the opening state. At 9 per cent the "
  "multiple is 14.60, at 12 per cent 10.20 and at 15 per cent 7.85.", 6.4),

 ("nothing happens, nothing happens, and then everything happens at once",
  "fig13_02_macro_regimes", "13.2",
  "The four macro regimes across the ten rounds, and what they do to the multiple.",
  "Two stacked charts across rounds 1 to 10, with the four rate regimes shaded: easing at minus 1 per cent "
  "in Rounds 1 and 2, neutral in Rounds 3 to 5, tightening at plus 1 per cent in Rounds 6 to 8, and a "
  "crisis premium of plus 1.5 and plus 2 per cent in Rounds 9 and 10. The cost of capital runs 5.18, 5.18, "
  "6.18, 6.18, 6.18, 7.18, 7.18, 7.18, 7.68, 8.18. The exit multiple holds at 18.00 times through Round 8, "
  "falls to 17.96 at Round 9 and 16.50 at Round 10.", 6.4),

 ("Each instrument has its own failure mode, and the table names them",
  "fig13_04_instruments", "13.3",
  "Five instruments on what they price, their flexibility, their credibility test and their exposure.",
  "Comparison table of five financing instruments: use-of-proceeds green bond, European green bond label, "
  "sustainability-linked bond, transition finance and blended finance. Each row gives what the instrument "
  "prices, its flexibility, its credibility test and its greenwashing exposure, rated high, moderate or "
  "low in words with a matching count of markers. Only the European green bond label and blended finance "
  "carry a control the issuer does not write itself.", 6.4),

 ("the debrief has something to read",
  "fig13_03_allocation", "13.4",
  "Four allocation heuristics against the two constraints the engine actually enforces.",
  "Grouped bar chart of a 10 million dollar Round 1 pool allocated four ways across the four units: "
  "proportional by revenue, worst-first, flag-hunting, and concentrated in one unit. Two horizontal lines "
  "mark the constraints — a 15 per cent floor per unit below which neglect is penalised, and 3 million "
  "above which an allocation carries a 25 per cent chance of a 15 per cent overrun, an expected tax of "
  "3.75 per cent. The concentrated allocation trips both at once.", 6.4),
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
