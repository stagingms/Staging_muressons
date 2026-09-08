import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter09_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
# NOTE: 9.4 is inserted on the same anchor as 9.3, and first, so that the
# document order comes out 9.3 then 9.4.
SPEC = [
 ("Readiness bundles three things practitioners usually keep apart",
  "fig09_01_hr_loop", "9.1",
  "The burnout–readiness loop, and everything downstream of it.",
  "System diagram. The HR pillar choice feeds two stocks: staff burnout index per unit, moved by minus 10 "
  "for a high-tier choice, minus 4 for medium, plus 12 for active neglect, with a plus 3 drift when HR is "
  "skipped; and workforce readiness for the group, moved by plus 16, plus 8 or minus 10. Burnout feeds an "
  "OPEX penalty above 20 and the Round 9 strike probability. Readiness feeds the Round 7 synergy modifier, "
  "which is 0.70 below 40, 1.00 from 40 to 60 and 1.10 at 60 or above. Both reach terminal valuation, "
  "through the Just Transition scaling and the readiness bonus above 75. A dashed return path marks the "
  "loop: last round's neglect is this round's operating cost.", 6.4),

 ("The two HR penalties are booked on different principles",
  "fig09_02_burnout_penalty", "9.2",
  "The quadratic OPEX penalty, and three HR strategies against it.",
  "Two panels. Left: the OPEX penalty rate against the staff burnout index — zero below 20, then a "
  "quadratic curve reaching 1.1 per cent at 40, 4.5 at 60, 10.1 at 80 and 18.0 at 100, with the critical "
  "threshold of 70 marked. Right: burnout paths from the opening index of 10 for three strategies — "
  "neglect every round rises steadily past 20 and towards 40; the cheapest medium option every round falls "
  "to zero; high-quality every round falls to zero faster.", 6.4),

 ("Nothing in Rounds 1 to 9 tells you it is coming except this chapter",
  "fig09_04_hr_strategies", "9.4",
  "Three HR strategies across the ten rounds: spend, burnout, readiness and the multiplier earned.",
  "Four small line charts across rounds 1 to 10 for three strategies. Cumulative HR spend reaches 30.0 "
  "million for high quality every round, 10.0 million for the cheapest option that still counts, and "
  "nothing for never investing. Staff burnout falls to zero on both investing routes and rises to 40 on "
  "the third. Workforce readiness rises to the 100 ceiling on both investing routes and falls to zero on "
  "the third by Round 6. Just Transition scaling reaches its 1.5 cap by Round 5 on both investing routes "
  "and stays at 1.0 on the third. Lines are distinguished by style and marker as well as colour.", 6.4),

 ("Nothing in Rounds 1 to 9 tells you it is coming except this chapter",
  "fig09_03_jt_scaling", "9.3",
  "Just Transition scaling counts rounds, not quality.",
  "Two panels. Left: Just Transition scaling against the number of rounds carrying any HR investment, "
  "rising by 0.10 a round from 1.0 and capping at 1.5 at five rounds. Right: the cost of five qualifying "
  "rounds by route — 3.0 million for the five cheapest medium options against 10.0 million for the five "
  "cheapest high options, with each route's five options listed. Both routes buy the identical multiplier.", 6.4),
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
