import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc

DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter01_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")

SPEC = [
 ("Read the right-hand column again",
  "fig01_01_capitals_chain", "1.1",
  "The capital-to-money chain. Every capital terminates in a number on the first ledger.",
  "Three-column flow diagram. Six capitals — financial, manufactured, human, social and relationship, "
  "intellectual, natural — each connect by arrows to their Muressons state variables and then to the "
  "financial line those variables reach. Manufactured is drawn with a dashed border because it is the "
  "one capital with no dedicated stock variable: it is carried by revenue_base and opex_base.", 6.4),

 ("Static maps are the reason crises feel sudden",
  "fig01_02_salience", "1.2",
  "The eight salience classes, with the Muressons roster placed by its own stored attributes.",
  "A three-circle Venn of power, legitimacy and urgency, giving the eight Mitchell, Agle and Wood "
  "salience classes, numbered 1 to 7 inside the circles with non-stakeholder outside. A key beneath "
  "names each class and lists who occupies it. Definitive holds Elise Thornton, Sofia Petrova and Jaya "
  "Mehta; Dependent holds Rajesh Patil; the other five classes are empty. The Dangerous cell — power and "
  "urgency without legitimacy — is empty and marked in rust as the class the text calls systematically "
  "under-managed.", 6.4),

 ("It is a cost that has not yet been assigned to anybody",
  "fig01_03_pillar_cost", "1.3",
  "Round 1: fifteen options across five pillars, against one budget. The gap is opportunity cost, priced.",
  "Horizontal bar chart of the fifteen Round 1 pillar options grouped by pillar — Energy Strategy, "
  "Operational Efficiency, Supply Chain, Carbon Offsetting, Talent and Culture — with each bar's cash "
  "cost in millions of dollars and its non-cash impacts labelled alongside. Bars are distinguished by "
  "hatch as well as colour. The most expensive single option is Solar CapEx at 4.0 million. Taking the "
  "most expensive option in every pillar costs 13.5 million against a Round 1 Corporate Strategic Fund "
  "of 10.0 million.", 6.4),
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
    shutil.copyfile(tmp, DOC); print("WROTE", os.path.basename(DOC), "figures", placed)
except PermissionError:
    dest = os.path.expanduser("~/mnt/muressons-sim/docs/_pending_close_word/" + os.path.basename(DOC))
    os.makedirs(os.path.dirname(dest), exist_ok=True); shutil.copyfile(tmp, dest)
    print("LOCKED -> pending", dest)
