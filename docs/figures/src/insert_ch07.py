import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter07_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
SPEC = [
 ("which is the regulation Round 7 opens with",
  "fig07_01_linear_circular", "7.1",
  "The linear flow and its three leaks; the circular alternative and the loops that close it.",
  "Two panels. The upper shows the linear model as four boxes — take virgin material, make the product, "
  "use for three years, waste lost to the firm — with three downward arrows marking where value leaks: "
  "residual value, embodied energy and disposal liability. The lower shows Make and Use with four return "
  "loops of decreasing tightness: reuse, repair and refurbish keeps the whole product; remanufacture and "
  "repurpose keeps the component; recycle keeps only the material; recover keeps only the energy. Loops "
  "are distinguished by line style as well as position. A separate note marks the biological cycle as "
  "Chapter 6's engine rather than this one.", 6.4),

 ("Design out the drawer and the landfill takes care of itself",
  "fig07_02_r_hierarchy", "7.2",
  "The R-hierarchy, with the Muressons option that sits on each rung.",
  "Six rungs descending from most to least value retained: refuse and rethink; reduce; reuse, repair and "
  "refurbish; remanufacture and repurpose; recycle; recover. Against each is its meaning and where it "
  "appears in the game — Round 2's Energy Efficiency Upgrades, Round 7's Material Passports, Round 3's "
  "Closed-Loop Manufacturing, Round 7's Extended Producer Responsibility and Round 7's Waste-to-Energy "
  "Partnership. The top rung, refuse and rethink, has no round option: it is discussed in the text only.", 6.4),

 ("its operating-cost sacrifice is the price of that route",
  "fig07_03_r7_options", "7.3",
  "Round 7's three options on six dimensions.",
  "Six small bar charts comparing options A, B and C. Cash cost: 10.0, 5.0 and 7.0 million dollars. "
  "Carbon intensity points removed: 8, 5 and 6. Natural capital debt points removed: 12, 6 and 4. "
  "Reputation and licence points gained: 14, 7 and 0. OPEX cut this round from the 15 per cent circular "
  "bonus: 5.475 million for A and B, nothing for C. Synergy multiplier added: nothing for A and B, 0.30 "
  "for C. Bars are distinguished by hatch as well as colour.", 6.4),
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
