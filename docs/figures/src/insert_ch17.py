import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter17_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
SPEC = [
 ("with the last two appearing in no financial statement",
  "fig17_01_value_creation", "17.1",
  "The value-creation model, populated with Muressons' opening state.",
  "The integrated-reporting value-creation model. Six capitals as inputs on the left, each with its "
  "opening figures: financial, treasury 50.0 million and cost of capital 6.18 per cent; manufactured, "
  "revenue base 53.5 million and opex base 36.5 million; intellectual, synergy 1.00 and VRIO advantage "
  "0.80; human, readiness 50 and burnout 10; social and relationship, licence 50, reputation 55 and four "
  "named NPCs; natural, 2,424 tonnes of CO2e, natural capital debt 500 and water dependency 54.25. These "
  "feed a business model of four units, five pillars and ten rounds, which produces outputs and two "
  "ledgers of outcomes. The whole sits inside an external environment and a governance structure, and a "
  "return arrow marks outcomes becoming the next period's inputs.", 6.4),

 ("it is a choice, and Chapter 2's assurance question applies to it",
  "fig17_02_three_ways", "17.2",
  "The same emissions data, charted three ways: two misleading, one honest.",
  "Three line charts of the same constructed team over ten rounds — revenue growing 8 per cent a round, "
  "carbon intensity falling 6 per cent a round. The first shows intensity alone, falling 43 per cent, "
  "which is true. The second shows absolute tonnes on an axis starting at 2,000, drawing an 8 per cent "
  "rise as a surge. The third shows both series on zero-based axes: intensity falls 43 per cent while "
  "absolute emissions rise 8 per cent, and both are true. Only the third lets a reader see the growth "
  "trap.", 6.4),

 ("the position of the bad news in the deck is itself a disclosure",
  "fig17_03_section_checklist", "17.3",
  "The eight sections of the reporting job, against the two disclosure regimes.",
  "Checklist of eight sections — governance; strategy and business model; impacts, risks and "
  "opportunities; policies and actions; targets and metrics; value chain; assurance; and connectivity — "
  "with what each has to answer and where it is required under the European standards and under India's "
  "BRSR against the NGRBC principles. Each row carries a check-box for the team. The last row, "
  "connectivity, is not a section and has no reference: it is the test the other seven have to pass "
  "together.", 6.4),
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
