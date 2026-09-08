import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc

DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter03_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")

SPEC = [
 ("better spent elsewhere",
  "fig03_01_synergy_curve", "3.1",
  "The synergy curve, and the allocation it rewards.",
  "Two panels. Left: OPEX reduction per round against investment ratio, four curves for synergy "
  "multipliers 0.80, 1.00, 1.30 and 1.60, each with its own line style. The 6 per cent per-round "
  "ceiling is drawn as a dotted horizontal line; only the 1.60 curve reaches it. Points on the "
  "S equals 1.00 curve are marked at ratios 0.05, 0.10, 0.25, 0.50 and 1.00, giving reductions of "
  "0.94, 1.33, 2.10, 2.97 and 4.20 per cent. Right: the same 10 million dollars concentrated in "
  "Pharma yields 504 thousand dollars of reduction; split four ways it yields 766 thousand, "
  "52 per cent more, shown as a stacked bar by unit.", 6.4),

 ("needs a project boost or Round 7",
  "fig03_02_vrio_decay", "3.2",
  "Nine decays from Round 1 to Round 10, at four average investment ratios.",
  "Line chart of the group synergy multiplier over rounds 1 to 10, starting at 1.00. Four paths, "
  "distinguished by line style and marker: zero reinvestment ends at 0.630, a 25 per cent average "
  "ratio at 0.709, 50 per cent at 0.796 and 80 per cent at 0.914. A dashed horizontal line marks the "
  "Round 10 synergy gate of 0.80. The 50 per cent path ends just below the gate.", 6.4),

 ("Three things to read off the table",
  "fig03_03_slot_fit", "3.3",
  "The slot-fit matrix: seventeen profiles, four slots, one eligible slot each.",
  "Matrix with the four unit slots as columns and the seventeen business-unit profiles as rows. Each "
  "row is marked in exactly one column, either as the slot's default occupant or as an eligible "
  "substitution; a dash marks every combination the registry refuses. Pharma's slot takes Oil and Gas, "
  "Chemical, Cosmetics, Food and Beverage and Power and Utilities; Electronics takes Semiconductor, "
  "Medical Devices, Automotive and Telecom; Consumer Goods takes Retail FMCG and Agriculture; Software "
  "takes Banking and Financial Services and Technology. Each row also carries its opening revenue, "
  "carbon intensity, governance risk and water dependency.", 6.4),
]

d = Document(DOC)
print("stripped", figdoc.strip_figures(d), "old figure paragraphs")
ps = list(iter_paras(d))
placed = []
for needle, fname, num, cap, alt, w in SPEC:
    hits = [p for p in ps if needle in ptext(p)]
    assert len(hits) == 1, f"{needle!r}: {len(hits)} matches"
    path = os.path.join(FIG, fname + ".png")
    assert os.path.exists(path), path
    figdoc.insert_after_para(d, hits[0], path, num, cap, alt, width_in=w)
    placed.append(num)

tmp = os.path.expanduser("~/audit_scratch/tmp_out.docx")
d.save(tmp)
try:
    shutil.copyfile(tmp, DOC); print("WROTE", os.path.basename(DOC), placed)
except PermissionError:
    dest = os.path.expanduser("~/mnt/muressons-sim/docs/_pending_close_word/" + os.path.basename(DOC))
    os.makedirs(os.path.dirname(dest), exist_ok=True); shutil.copyfile(tmp, dest)
    print("LOCKED -> pending", dest)
