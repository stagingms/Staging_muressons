import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter11_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
SPEC = [
 ("does it end the game",
  "fig11_01_fat_tails", "11.1",
  "The loss distribution the registry actually carries, against a normal fitted to it.",
  "Two panels. Left: the per-round outcome distribution of the eight global black swan events at the "
  "opening state. Nothing happens 83.3 per cent of the time; the eight events sit between minus 11.3 and "
  "plus 1.7 million dollars with probabilities between 1.7 and 3.3 per cent each. A dashed normal curve "
  "fitted to the same mean of minus 1.04 million and standard deviation of 2.92 million is overlaid. "
  "Right: for each loss, the registry's probability against the normal's, on a logarithmic axis. At minus "
  "11.3 million the normal understates by a factor of 131.", 6.4),

 ("The register is a matrix, not a list",
  "fig11_03_probability_tree", "11.2",
  "A conditional probability tree, taken from the registry's own modifiers.",
  "Tree for the whistleblower scandal. The base probability is 2.00 per cent a round over Rounds 3 to 9. "
  "Two conditional modifiers add to it: plus 12 per cent when mean governance risk exceeds 50, and plus 15 "
  "per cent when the greenwashing flag is set. The four leaves are: neither condition, 2 per cent; "
  "governance risk alone, 14 per cent; greenwashing alone, 17 per cent; both, 29 per cent. The modifiers "
  "add rather than multiply.", 6.4),

 ("three of them can be computed by hand from numbers the cockpit already shows",
  "fig11_02_four_indices", "11.3",
  "The four foreshadowing indices across Rounds 5 to 10, for two contrasting decision sets.",
  "Four small line charts, one per index — Stranded Asset Exposure, Social Capital Index, Takeover "
  "Vulnerability and Compliance Risk Index — plotted from Round 5 to Round 10 for two teams: one taking "
  "the dearest option in Energy, Offsetting and Human Resources every round, the other taking the free "
  "option every round. The two paths diverge on every index. A note under each records that the engine "
  "shows it only to teams on the matching ending, and only from Round 7.", 6.4),

 ("Muressons is the rare case where the register can be written from the source",
  "fig11_04_risk_register", "11.4",
  "The risk register, pre-filled from the registry, in the four columns §11.7 prescribes.",
  "Table of all thirteen registry events ordered by base probability, with four columns: likelihood as a "
  "per-round probability over a stated round range; impact as the actual treasury, revenue, OPEX, "
  "reputation, licence, governance and burnout deltas; velocity as the registry's duration in rounds; and "
  "correlation as the conditional modifiers that name the state each risk shares with the others. Five of "
  "the thirteen are region-gated and are marked as such.", 6.4),
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
