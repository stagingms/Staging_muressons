import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter05_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
SPEC = [
 ("why the same policy lands so differently on each unit",
  "fig05_01_scopes", "5.1",
  "The scope split each unit carries, as shares and as tonnes.",
  "Two panels of stacked horizontal bars. Left: each unit's emissions split by scope as a percentage — "
  "Pharma 35 / 25 / 40, Electronics 10 / 15 / 75, Consumer Goods 15 / 10 / 75, Software 5 / 60 / 35. "
  "Right: the same split in tonnes at the opening state — Electronics 1,188 t, Pharma 630 t, Consumer "
  "Goods 504 t, Software 102 t, group total 2,424 t. Scopes are distinguished by hatch as well as colour.", 6.4),

 ("read the method note before the number",
  "fig05_02_scope3_categories", "5.2",
  "The fifteen Scope 3 categories, and the unit most exposed to each.",
  "Table of the fifteen GHG Protocol Scope 3 categories, split into upstream categories 1 to 8 and "
  "downstream categories 9 to 15. Against each is the most-exposed Muressons unit and the attribute or "
  "mechanic that puts it there. Five categories — employee commuting, upstream leased assets, downstream "
  "leased assets, franchises and investments — have no mechanic in the build and are marked with a dashed "
  "empty box rather than assigned a unit.", 6.4),

 ("Chapter 14 §14.1.4 works through why",
  "fig05_03_terminal_carbon", "5.3",
  "The terminal carbon line at the three prices the engine can charge, before and after decarbonising.",
  "Grouped bar chart. At the standard 250 dollar shadow price the opening state pays 606 thousand dollars, "
  "3.6 per cent of gross profit; under the Regulatory Shutdown ending at 350 dollars, 848 thousand or 5.0 "
  "per cent; under the Climate Black Swan ending at 750 dollars, 1,818 thousand or 10.7 per cent. A second, "
  "hatched series shows the same three prices for a group decarbonised to intensity 31 and 1,659 tonnes: "
  "415, 581 and 1,244 thousand dollars.", 6.4),

 ("a team that reads the last column will do both",
  "fig05_04_macc", "5.4",
  "A marginal abatement cost curve built from the Energy pillar's own options.",
  "Marginal abatement cost curve. Thirteen carbon-reducing Energy pillar options are ordered by cost per "
  "tonne, each bar's width being the tonnes it abates at the opening state and its height the cost per "
  "tonne. The cheapest are the Renewable PPA and Green Energy Tariff at 4,294 dollars a tonne; the dearest "
  "is the Round 7 Waste-to-Energy Plant at 12,881. A horizontal line marks the 250 dollars a tonne the "
  "terminal valuation actually charges — every option on the curve sits far above it. A table inside the "
  "plot lists each option with its round, cost, intensity points, tonnes and cost per tonne.", 6.4),
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
