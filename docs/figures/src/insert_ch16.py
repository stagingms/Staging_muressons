import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter16_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
SPEC = [
 ("what did we decide today that we would decide differently with one more piece of information",
  "fig16_01_decision_rights", "16.1",
  "The decision-rights matrix, left blank because it is the team's to write.",
  "Matrix with seven decisions as rows — the five pillar areas of Energy, Operations, Supply Chain, "
  "Offsetting and Human Resources, plus the crisis decision and the Round 9 closure — against three seats "
  "as columns: CEO, CFO and CSO. Every cell is an empty dashed box for the team to fill with one of four "
  "verbs: propose, decide, consult, inform. A further column asks who holds the tie-break on each row. A "
  "note records that the build implements none of this: the role-asymmetry specification's seats and "
  "private information are unbuilt, and the decision log's consensus column is written by nothing.", 6.4),

 ("it would have shown four cards saying no",
  "fig16_03_pathologies", "16.2",
  "The six pathologies, and the round in which each most often appears.",
  "Six pathologies with their definitions, marked against the rounds where the chapter says each shows up. "
  "Groupthink at Round 6; escalation of commitment at Rounds 4, 5 and 7; anchoring and ordering at Round "
  "1; overconfidence after a good round at Round 4; loss aversion after a bad one at Rounds 5 and 9; "
  "diffusion of responsibility across all ten. A note records that the outline promised eight pathologies "
  "and the chapter names six.", 6.4),

 ("the journal is the record and the diary is the press release",
  "fig16_02_meeting", "16.3",
  "The twenty-five-minute meeting, minute by minute, and what each segment protects against.",
  "Timeline of a twenty-five-minute round meeting in six segments: Brief 3 minutes, Analyse 5, Argue 8, "
  "Decide 4, Allocate 3, Record 2. Against each, what happens and what goes wrong without the clock. Argue "
  "is the longest segment and the one teams shorten first. A note records that the platform's own decision "
  "timer ships off and is set to 300 seconds when enabled — the Analyse segment alone.", 6.4),
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
