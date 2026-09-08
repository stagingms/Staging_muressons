import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter15_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
SPEC = [
 ("the compression is the point of the exercise",
  "fig15_01_strategic_loop", "15.1",
  "The strategic loop over one round, and the state that carries into the next.",
  "A six-stage cycle — look outward, look inward, synthesise, choose, commit, read the result — with the "
  "rounds in which the build asks for each. Alongside, the three things that carry over: flags, which "
  "cannot be unset; stocks, which are path-dependent; and the strategic thesis, which the loop cannot "
  "rewrite for the team.", 6.4),

 ("whose leverage over both is contractual rather than operational",
  "fig15_02_value_chain", "15.2",
  "The value chain redrawn for Electronics, with the three rows that run its whole width.",
  "The five primary activities across the top and four support activities beneath, with three added rows "
  "running the full width: emissions at each stage, water at each stage, and labour conditions at each "
  "stage. Electronics' own figures populate the cells — 75 per cent of its tonnes upstream in purchased "
  "components, carbon intensity 72, water dependency 58, and the Tier-3 labour conditions and e-waste "
  "entries from the Round 2 dictionary. The two rows that matter most sit upstream of anything the unit "
  "controls directly.", 6.4),

 ("That report is the most under-used artefact in the debrief",
  "fig15_03_leverage_points", "15.3",
  "The twelve leverage points, with the simulation decision that sits at each.",
  "The twelve leverage points from twelve, the weakest, to one, the strongest, each with the build's own "
  "name and the first simulation example it lists. Twelve is adjusting the investment sliders; eight is "
  "the burnout-to-OPEX balancing loop; seven is the contagion sigmoid; six is the fog of complexity; five "
  "is the Round 2 materiality gate; four is stakeholder salience migration; three is the terminal "
  "valuation formula, which defines what winning means; two is the mental model tracker; one is the "
  "post-game question about the simulation's own paradigm. A power column shows the registry's "
  "effectiveness rating as a count of blocks.", 6.4),

 ("A strategy is a sequence, not a list, and this is why",
  "fig15_04_five_endings", "15.4",
  "The five endings, the capability each audits, and the rounds where that capability is built.",
  "Grid with the five ending pathways as rows and the ten rounds as columns. Activist Ultimatum audits "
  "portfolio logic, built in Rounds 1 to 7. Climate Black Swan audits decarbonisation conviction, built in "
  "Rounds 3, 5 and 7. Stakeholder Revolt audits social investment, built in Rounds 1, 4, 8 and 9. Hostile "
  "Takeover audits financial strength and governance, built across Rounds 1 to 9. Regulatory Shutdown "
  "audits compliance integrity, built in Rounds 2, 4 and 6. Round 10 is empty in every row: by the time "
  "the ending is revealed, the capability has already been built or it has not.", 6.4),
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
