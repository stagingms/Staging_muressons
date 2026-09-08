import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter12_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
SPEC = [
 ("one that hides it is a decoration",
  "fig12_01_waterfall", "12.1",
  "The Round 1 treasury bridge on the opening state, with its zero rows kept.",
  "Waterfall chart. Opening treasury 50.00 million; gross profit of 17.00 million, being group revenue of "
  "53.5 million less group OPEX of 36.5 million; a supply-chain contagion surcharge of 3.87 million; a "
  "brain-drain premium of 0.83 million on Software; capex of 10.00 million if the whole Round 1 fund is "
  "spent; carbon, climate and regulatory ratchet lines all nil at Round 1 and drawn as flat markers rather "
  "than omitted; closing treasury 52.30 million. Increases and decreases are distinguished by hatch as "
  "well as colour.", 6.4),

 ("do not wait for the standard-setter to tell you it is a liability",
  "fig12_02_three_statements", "12.2",
  "The three statements, and the articulation points that make them one document.",
  "Three columns — income statement, cash flow, balance sheet — with their opening figures. Arrows mark "
  "the articulation points: EBITDA of 17.0 million opens the cash statement; depreciation is added back; "
  "the net movement lands in cash; and net income is the only route into equity. A note records that "
  "retained earnings is derived as a plug rather than accumulated, which is the one place the model "
  "departs from a real set of statements.", 6.4),

 ("becomes a number an accountant would recognise",
  "fig12_03_metric_to_line", "12.3",
  "Where each non-financial metric lands on the financial statements.",
  "Grid with ten non-financial metrics as rows and eight financial lines as columns — revenue, operating "
  "expense, interest expense, intangible assets, provisions, cost of capital, terminal EBITDA and terminal "
  "multiplier. Marks show where each metric lands. Operating expense receives seven of the ten metrics, "
  "more than any other line; revenue receives two. The second ledger reaches the first mostly through "
  "cost, not through revenue.", 6.4),
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
