import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter06_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
SPEC = [
 ("the attribution matters only for what you look for in a stored game",
  "fig06_01_ncd_chain", "6.1",
  "Two chains: the one natural capital debt runs, and the one that reaches the cost of capital.",
  "Causal diagram in two halves. The upper half traces natural capital debt: it sets its own interest "
  "rate at WACC plus NCD times 0.0001 and compounds, 300 points becoming 593 between Rounds 3 and 10; "
  "and it loads operating cost at NCD times one thousand dollars times the market hostility index, which "
  "at the default hostility of 5 is 1.5 million dollars a round on 300 points. Green capex forgives it "
  "at 2.0 times the natural log of one plus the capex in millions. Both routes reach terminal valuation. "
  "The lower half shows the four terms that actually set the cost of capital — weighted carbon intensity "
  "contributing 0.42 per cent, governance risk zero, social licence zero, and water dependency times "
  "transparency contributing 0.76 per cent — summing to an ESG adjustment of 1.18 on a base of 5.00 per "
  "cent, giving a WACC of 6.18 per cent and a capped 18 times exit multiple. Natural capital debt appears "
  "in none of those four terms.", 6.4),

 ("moved by Round 8's options and by the Energy and Human Resources pillars' water options",
  "fig06_02_water_profile", "6.2",
  "The water risk profile of the four units, and the only lever on the premium it creates.",
  "Two panels. Left: water dependency by unit as horizontal bars — Pharma 82, Consumer Goods 65, "
  "Electronics 58, Software 12 — with a dashed line at the group mean of 54.25 that feeds the nature "
  "premium. Right: the nature premium on the WACC plotted against transparency, for Pharma alone at 82, "
  "the group mean at 54.25, and Software alone at 12. All three fall linearly to zero at full "
  "transparency. A marked point shows the opening state: transparency 30 gives a nature premium of 0.76 "
  "per cent.", 6.4),

 ("Adaptation is an asset, and a nature-based one is an asset that appreciates",
  "fig06_03_grey_green", "6.3",
  "Grey, green and hybrid on cost, lead time, protection, co-benefit and residual risk.",
  "Comparison table with three columns — grey hard engineering, green nature-based, and hybrid — against "
  "five rows. Cost: 8 million, 5 million, between. Lead time: two rounds certain; two rounds with a "
  "75 per cent chance of establishing; two rounds with the grey part certain. Protection: 0.85; 0.60, "
  "falling to 0.35 on a failed roll; additive in principle. Co-benefits: none, and NCD plus 10, carbon "
  "intensity plus 3, revenue minus 600 thousand; against NCD minus 8, carbon intensity minus 6, revenue "
  "plus 500 thousand per unit. Residual risk: 15 per cent of damage with the wall failing once "
  "catastrophically; 40 per cent with the mangrove degrading gradually; lowest for hybrid.", 6.4),
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
