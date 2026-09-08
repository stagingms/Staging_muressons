import sys, os, shutil
sys.path.insert(0, os.path.expanduser("~/audit_scratch/docs_edit"))
from docxtools import *
import figdoc
DOC = os.path.expanduser("~/mnt/muressons-sim/docs/Muressons_Chapter08_Complete.docx")
FIG = os.path.expanduser("~/mnt/muressons-sim/docs/figures")
SPEC = [
 ("Salience is a diagnostic: it explains why the sort changes",
  "fig08_01_power_interest_grid", "8.1",
  "The power–interest grid with the Round 1 roster placed, and the seven that will not stay there.",
  "Two-by-two grid of power against interest with the ten Round 1 stakeholders placed. Manage closely "
  "holds the Activist Fund and EU Regulators. Keep satisfied holds the National Government and the "
  "Syndicate Banks. Keep informed holds Factory Employees, Local Communities and Tier-3 Miners. Monitor "
  "holds Cafeteria Vendors, the General Public and the Regional Journalist. Seven of the ten are marked "
  "with a square because they migrate later: the General Public, Regional Journalist and Cafeteria Vendors "
  "in Round 4, Local Communities and Syndicate Banks in Round 6, Factory Employees and Tier-3 Miners in "
  "Round 9. The Regional Journalist is marked as accepting two answers.", 6.4),

 ("any model that made trust symmetrical would be modelling an irrational stakeholder",
  "fig08_02_contagion_sigmoid", "8.2",
  "The contagion sigmoid, with severity 40 and 80 marked.",
  "S-curve of reputation points erased against crisis severity. The curve saturates at 50 points; its "
  "midpoint is at severity 30, where half the maximum drop applies. At severity 40 the drop is 33.0 points, "
  "taking group reputation from 55 to 22.0. At severity 80 the drop is 48.3 points, taking it to 6.7. "
  "Doubling severity from 40 to 80 buys only 15 more points of damage, because the curve is already past "
  "its inflection at 40.", 6.4),

 ("They are different instruments and only one of them is a risk register",
  "fig08_03_fatigue_curve", "8.3",
  "The fatigue curve: what the same recovery action buys after each crisis.",
  "Two panels. Left: recovery efficiency against lifetime crises survived, falling from 100 per cent at "
  "zero crises to 77, 63, 53, 45, 40, 36, 32, 29, 27 and 25 per cent after one to ten. Right: the points a "
  "ten-point recovery action actually delivers at each of those counts, from 10.0 down to 2.5. Bars "
  "alternate hatch as well as colour.", 6.4),

 ("you will get a third number, which is correct",
  "fig08_04_round4_today_year5", "8.4",
  "Round 4's three options, costed today and at Year 5.",
  "Two panels. Left: the cash cost today — 6.0 million for Option A full transparency and remediation, "
  "2.0 million for Option B damage control PR, nothing for Option C deny and deflect. Right: what each is "
  "still worth at Year 5 across three channels. Option A permanently cuts group revenue by 2 million a "
  "round, 14 million cumulatively over Rounds 4 to 10, and 36 million of terminal value at the 18 times "
  "ceiling. Option B changes none of them. Option C permanently cuts group revenue by 4 million a round, "
  "28 million cumulatively, and 72 million of terminal value. A note records that the reputation, licence "
  "and governance deltas all evaluate to zero from the opening state, because mean licence of 50 stays "
  "below the 70-point floor of the Instability Discount ramp under every option.", 6.4),
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
