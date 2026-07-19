"""Bulk player provisioning from Excel — single-cohort and master workbook.

Two shapes, one parser core:

  * FACILITATOR shape — a flat sheet of players for ONE cohort the facilitator
    already owns. Columns: name, email, programme (optional), assigned_bu,
    region_id. The cohort is named by the URL, not the sheet.

  * PROJECT-ADMIN master workbook — three sheets, `Facilitators`, `Cohorts`
    and `Players`, that provision an entire programme in one upload. Rows are
    linked by a `ref` the author invents (e.g. "f1", "c1"), NOT by an ID the
    server has not assigned yet: the whole point is that none of these entities
    exist before the upload, so the author cannot cite a FAC-003 that does not
    exist. A cohort may alternatively cite an EXISTING facilitator id, which is
    how a second intake gets added to a facilitator provisioned last term.

Contract (owner decision, July 2026): **all-or-nothing**. The workbook is
parsed and validated in full before anything is created; one bad row aborts
the entire import. This differs deliberately from the older facilitator-only
bulk upload, which creates good rows and reports bad ones. That is defensible
for one flat entity; it is not defensible across three linked ones, because a
partial import can leave a cohort pointing at a facilitator that was never
created, and no operator can tell from the resulting state which half applied.

Every error carries sheet + row so the author can fix the file in one pass
rather than re-uploading to discover the next problem.
"""
from __future__ import annotations

import re
from io import BytesIO

from player_capacity import MAX_PLAYERS_CEILING, clamp_max_players

MAX_UPLOAD_BYTES = 2 * 1024 * 1024

# ── Column vocabulary ───────────────────────────────────────────────────────
PLAYER_COLUMNS = ("name", "email", "programme", "assigned_bu", "region_id")
PLAYER_REQUIRED = ("name",)

# Authors write human headers; we normalise. Unknown columns are ignored rather
# than rejected so an institution can keep its own bookkeeping columns in the
# same sheet.
_ALIASES = {
    "full_name": "name",
    "student_name": "name",
    "player_name": "name",
    "participant": "name",
    "participant_name": "name",
    "e_mail": "email",
    "email_address": "email",
    "email_id": "email",
    "course": "programme",
    "program": "programme",
    "program_name": "programme",
    "programme_name": "programme",
    "batch": "programme",
    "business_unit": "assigned_bu",
    "bu": "assigned_bu",
    "assigned_business_unit": "assigned_bu",
    "region": "region_id",
    "market": "region_id",
    "cohort": "cohort_ref",
    "cohort_id": "cohort_ref",
    "cohort_key": "cohort_ref",
    "facilitator": "facilitator_ref",
    "facilitator_id": "facilitator_ref",
    "facilitator_key": "facilitator_ref",
    "cohort_title": "cohort_name",
    "session_name": "cohort_name",
    "max_players": "max_players",
    "seats": "max_players",
}

COHORT_COLUMNS = (
    "ref", "cohort_name", "facilitator_ref", "max_players",
    "simulation_mode", "industry_vertical", "region_id", "decision_paradigm",
)
FACILITATOR_COLUMNS = (
    "ref", "name", "email", "contact_number", "programme", "role", "max_cohorts",
)

MASTER_SHEETS = ("Facilitators", "Cohorts", "Players")

# An email is validated only loosely: this is a classroom roster, and rejecting
# an unusual-but-valid institutional address would be worse than accepting a
# typo the facilitator can see in the preview.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class BulkPlayerError(ValueError):
    """Carries the full error list so the caller can render all of them."""

    def __init__(self, errors: list[dict]):
        self.errors = errors
        n = len(errors)
        head = "; ".join(
            f"{e.get('sheet', 'Sheet')} row {e.get('row', '?')}: {e['error']}"
            for e in errors[:8]
        )
        more = f" (+{n - 8} more)" if n > 8 else ""
        super().__init__(f"{n} error(s) — nothing was created. {head}{more}")


def _norm_header(cell) -> str:
    h = str(cell or "").strip().lower()
    h = re.sub(r"[^a-z0-9]+", "_", h).strip("_")
    return _ALIASES.get(h, h)


def _load(raw: bytes):
    from openpyxl import load_workbook
    if len(raw) > MAX_UPLOAD_BYTES:
        raise BulkPlayerError([{"sheet": "-", "row": 0, "error": "File too large (max 2 MB)"}])
    try:
        return load_workbook(BytesIO(raw), read_only=True, data_only=True)
    except Exception:
        raise BulkPlayerError([{
            "sheet": "-", "row": 0,
            "error": "Not a readable .xlsx file. Download the template and try again.",
        }])


def _rows_of(ws, columns: tuple[str, ...], sheet_label: str):
    """Yield (rownum, cell_accessor) for each non-blank data row.

    Returns ([], [error]) when the header row lacks a usable column so the
    caller reports a bad sheet rather than silently importing zero rows — a
    silent zero-row import is the failure mode that makes an operator think the
    upload worked.
    """
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], [{"sheet": sheet_label, "row": 1, "error": "Sheet is empty"}]
    header = [_norm_header(c) for c in rows[0]]
    idx = {name: header.index(name) for name in columns if name in header}
    if "name" not in idx and "ref" not in idx:
        return [], [{
            "sheet": sheet_label, "row": 1,
            "error": f"Header row must contain a 'name' column. Found: {[h for h in header if h]}",
        }]

    out = []
    for rownum, row in enumerate(rows[1:], start=2):
        if not any(str(c or "").strip() for c in row):
            continue  # fully blank rows are skipped silently

        def cell(key, default="", _row=row):
            i = idx.get(key)
            v = _row[i] if i is not None and i < len(_row) else None
            if v is None:
                return default
            s = str(v).strip()
            return s if s else default

        out.append((rownum, cell))
    return out, []


def _validate_player(cell, rownum, sheet_label, errors) -> dict | None:
    name = cell("name")
    if not name:
        errors.append({"sheet": sheet_label, "row": rownum, "error": "Missing required 'name'"})
        return None
    email = cell("email")
    if email and not _EMAIL_RE.match(email):
        errors.append({"sheet": sheet_label, "row": rownum, "error": f"'{email}' is not a valid email"})
        return None
    return {
        "row": rownum,
        "name": name[:100],
        "email": email[:200],
        # Programme is OPTIONAL by design — an open-enrolment cohort has no
        # programme, and forcing a placeholder would pollute the roster export.
        "programme": cell("programme")[:200],
        "assigned_bu": cell("assigned_bu")[:100],
        "region_id": cell("region_id")[:50],
        "cohort_ref": cell("cohort_ref"),
    }


# ── Form 1: one cohort, one flat sheet ──────────────────────────────────────

def parse_player_sheet(raw: bytes, limit: int = MAX_PLAYERS_CEILING) -> list[dict]:
    """Players for a single cohort. All-or-nothing.

    `limit` is the REMAINING capacity of the target cohort, not its total: a
    cohort of 20 that already holds 15 accepts 5 more. The check lives here so
    the operator is told the file is too big BEFORE any player is created,
    instead of watching the import die partway at row 16.
    """
    wb = _load(raw)
    ws = wb.active
    rows, errors = _rows_of(ws, PLAYER_COLUMNS + ("cohort_ref",), ws.title or "Sheet1")
    players = []
    seen_emails: dict[str, int] = {}
    seen_names: dict[str, int] = {}
    label = ws.title or "Sheet1"
    for rownum, cell in rows:
        rec = _validate_player(cell, rownum, label, errors)
        if rec is None:
            continue
        key = rec["name"].lower()
        if key in seen_names:
            errors.append({"sheet": label, "row": rownum,
                           "error": f"Duplicate player name '{rec['name']}' (also row {seen_names[key]})"})
            continue
        seen_names[key] = rownum
        if rec["email"]:
            ekey = rec["email"].lower()
            if ekey in seen_emails:
                errors.append({"sheet": label, "row": rownum,
                               "error": f"Duplicate email '{rec['email']}' (also row {seen_emails[ekey]})"})
                continue
            seen_emails[ekey] = rownum
        players.append(rec)

    if len(players) > limit:
        errors.append({
            "sheet": label, "row": 0,
            "error": (f"Sheet has {len(players)} players but the cohort has room for "
                      f"{limit}. Remove {len(players) - limit} row(s) or raise the "
                      f"cohort's player limit (max {MAX_PLAYERS_CEILING})."),
        })
    if errors:
        raise BulkPlayerError(errors)
    return players


# ── Form 2: master workbook ─────────────────────────────────────────────────

def parse_master_workbook(raw: bytes) -> dict:
    """Facilitators + Cohorts + Players in one file. All-or-nothing.

    Returns {"facilitators": [...], "cohorts": [...], "players": [...]} with
    every cross-reference already resolved, so the caller creates in order and
    never has to re-check linkage.
    """
    wb = _load(raw)
    present = {name.strip().lower(): name for name in wb.sheetnames}
    errors: list[dict] = []

    missing = [s for s in MASTER_SHEETS if s.lower() not in present]
    if missing:
        raise BulkPlayerError([{
            "sheet": "-", "row": 0,
            "error": (f"Master workbook must contain sheets named {', '.join(MASTER_SHEETS)}. "
                      f"Missing: {', '.join(missing)}. Found: {', '.join(wb.sheetnames)}"),
        }])

    # ── Facilitators ────────────────────────────────────────────────────────
    fac_rows, errs = _rows_of(wb[present["facilitators"]], FACILITATOR_COLUMNS, "Facilitators")
    errors.extend(errs)
    facilitators, fac_refs = [], {}
    for rownum, cell in fac_rows:
        name = cell("name")
        if not name:
            errors.append({"sheet": "Facilitators", "row": rownum, "error": "Missing required 'name'"})
            continue
        ref = cell("ref") or name
        rkey = ref.strip().lower()
        if rkey in fac_refs:
            errors.append({"sheet": "Facilitators", "row": rownum,
                           "error": f"Duplicate ref '{ref}' (also row {fac_refs[rkey]['row']})"})
            continue
        email = cell("email")
        if email and not _EMAIL_RE.match(email):
            errors.append({"sheet": "Facilitators", "row": rownum, "error": f"'{email}' is not a valid email"})
            continue
        try:
            max_cohorts = max(1, int(float(cell("max_cohorts", "3") or 3)))
        except (TypeError, ValueError):
            max_cohorts = 3
        rec = {
            "row": rownum, "ref": ref, "name": name[:200], "email": email[:200],
            "contact_number": cell("contact_number")[:50],
            "programme": cell("programme")[:200],
            # Role is caller-scoped at the endpoint (assignable_roles_for); a
            # spreadsheet must never be a route to a role above the uploader's.
            "role": (cell("role", "facilitator") or "facilitator").lower(),
            "max_cohorts": max_cohorts,
        }
        fac_refs[rkey] = rec
        facilitators.append(rec)

    # ── Cohorts ─────────────────────────────────────────────────────────────
    coh_rows, errs = _rows_of(wb[present["cohorts"]], COHORT_COLUMNS, "Cohorts")
    errors.extend(errs)
    cohorts, coh_refs = [], {}
    for rownum, cell in coh_rows:
        cname = cell("cohort_name") or cell("name")
        if not cname:
            errors.append({"sheet": "Cohorts", "row": rownum, "error": "Missing required 'cohort_name'"})
            continue
        ref = cell("ref") or cname
        rkey = ref.strip().lower()
        if rkey in coh_refs:
            errors.append({"sheet": "Cohorts", "row": rownum,
                           "error": f"Duplicate ref '{ref}' (also row {coh_refs[rkey]['row']})"})
            continue
        fref = cell("facilitator_ref")
        if not fref:
            errors.append({"sheet": "Cohorts", "row": rownum,
                           "error": "Missing 'facilitator_ref' — name the ref of a row on the "
                                    "Facilitators sheet, or an existing facilitator id"})
            continue
        rec = {
            "row": rownum, "ref": ref, "cohort_name": cname[:200],
            "facilitator_ref": fref,
            # Resolved below: either a new facilitator from this workbook, or an
            # existing id the endpoint must verify.
            "facilitator_is_new": fref.strip().lower() in fac_refs,
            "max_players": clamp_max_players(cell("max_players") or None),
            "simulation_mode": cell("simulation_mode", "conglomerate") or "conglomerate",
            "industry_vertical": cell("industry_vertical"),
            "region_id": cell("region_id"),
            "decision_paradigm": cell("decision_paradigm", "legacy_abc") or "legacy_abc",
        }
        coh_refs[rkey] = rec
        cohorts.append(rec)

    # ── Players ─────────────────────────────────────────────────────────────
    ply_rows, errs = _rows_of(wb[present["players"]], PLAYER_COLUMNS + ("cohort_ref",), "Players")
    errors.extend(errs)
    players = []
    per_cohort: dict[str, list[dict]] = {}
    seen: dict[tuple[str, str], int] = {}
    for rownum, cell in ply_rows:
        rec = _validate_player(cell, rownum, "Players", errors)
        if rec is None:
            continue
        cref = rec["cohort_ref"]
        if not cref:
            errors.append({"sheet": "Players", "row": rownum,
                           "error": "Missing 'cohort_ref' — name the ref of a row on the Cohorts sheet"})
            continue
        ckey = cref.strip().lower()
        if ckey not in coh_refs:
            errors.append({"sheet": "Players", "row": rownum,
                           "error": f"cohort_ref '{cref}' does not match any row on the Cohorts sheet"})
            continue
        # Names and emails must be unique WITHIN a cohort, not globally: the
        # same student legitimately appears in two cohorts of a programme.
        nkey = (ckey, rec["name"].lower())
        if nkey in seen:
            errors.append({"sheet": "Players", "row": rownum,
                           "error": f"Duplicate player '{rec['name']}' in cohort '{cref}' (also row {seen[nkey]})"})
            continue
        seen[nkey] = rownum
        if rec["email"]:
            ekey = (ckey, rec["email"].lower())
            if ekey in seen:
                errors.append({"sheet": "Players", "row": rownum,
                               "error": f"Duplicate email '{rec['email']}' in cohort '{cref}' (also row {seen[ekey]})"})
                continue
            seen[ekey] = rownum
        rec["cohort_ref"] = cref
        per_cohort.setdefault(ckey, []).append(rec)
        players.append(rec)

    # Capacity is checked per cohort against that cohort's own configured cap.
    for ckey, group in per_cohort.items():
        cap = coh_refs[ckey]["max_players"]
        if len(group) > cap:
            errors.append({
                "sheet": "Players", "row": group[cap]["row"],
                "error": (f"Cohort '{coh_refs[ckey]['ref']}' has {len(group)} players but its "
                          f"max_players is {cap} (ceiling {MAX_PLAYERS_CEILING})"),
            })

    # An orphan cohort is a warning-shaped bug: the author almost certainly
    # meant to add players and mistyped a ref, which the ref check above would
    # have flagged only on the Players side.
    for rec in cohorts:
        if not per_cohort.get(rec["ref"].strip().lower()):
            rec["player_count"] = 0
        else:
            rec["player_count"] = len(per_cohort[rec["ref"].strip().lower()])

    if errors:
        raise BulkPlayerError(errors)
    return {"facilitators": facilitators, "cohorts": cohorts, "players": players}


# ── Templates ───────────────────────────────────────────────────────────────

def _style_header(ws, headers, width=22):
    from openpyxl.styles import Font, PatternFill
    ws.append(list(headers))
    fill = PatternFill("solid", fgColor="1E293B")
    for i, _h in enumerate(headers, start=1):
        c = ws.cell(row=1, column=i)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = fill
        ws.column_dimensions[c.column_letter].width = width


def build_player_template(out_path) -> str:
    """Single-cohort player roster template."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Players"
    _style_header(ws, ["name", "email", "programme", "assigned_bu", "region_id"])
    ws.append(["Priya Raman", "priya@example.edu", "MBA 2026", "pharma", "south_asia"])
    ws.append(["Sam Okoye", "sam@example.edu", "", "chemicals", "europe"])

    notes = wb.create_sheet("How to use")
    for line in (
        ["Fill one row per player on the 'Players' sheet."],
        ["'name' is required. 'programme' is optional."],
        ["'email' is optional but must look like an email if present."],
        ["assigned_bu / region_id are optional and may be set later in the dashboard."],
        [f"Maximum {MAX_PLAYERS_CEILING} players per cohort."],
        ["A single bad row aborts the whole upload — nothing is created."],
        ["Each player gets a random temporary password, shown in the Player Registry."],
    ):
        notes.append(line)
    notes.column_dimensions["A"].width = 90
    wb.save(str(out_path))
    return str(out_path)


def build_master_template(out_path) -> str:
    """Three-sheet provisioning template for project admins."""
    from openpyxl import Workbook
    wb = Workbook()

    fac = wb.active
    fac.title = "Facilitators"
    _style_header(fac, list(FACILITATOR_COLUMNS))
    fac.append(["f1", "Dr Anita Rao", "anita@example.edu", "+91-99999-00000", "MBA", "facilitator", 3])
    fac.append(["f2", "Prof Liam Byrne", "liam@example.edu", "", "EMBA", "lead_facilitator", 5])

    coh = wb.create_sheet("Cohorts")
    _style_header(coh, list(COHORT_COLUMNS))
    coh.append(["c1", "MBA 2026 — Section A", "f1", 20, "conglomerate", "", "", "legacy_abc"])
    coh.append(["c2", "EMBA Pharma Intensive", "f2", 12, "single_bu", "pharma", "south_asia", "multi_toggles"])

    ply = wb.create_sheet("Players")
    _style_header(ply, ["cohort_ref", "name", "email", "programme", "assigned_bu", "region_id"])
    ply.append(["c1", "Priya Raman", "priya@example.edu", "MBA 2026", "pharma", "south_asia"])
    ply.append(["c1", "Sam Okoye", "sam@example.edu", "MBA 2026", "chemicals", "europe"])
    ply.append(["c2", "Maria Silva", "maria@example.edu", "", "pharma", "south_asia"])

    notes = wb.create_sheet("How to use")
    for line in (
        ["This ONE workbook provisions facilitators, cohorts and players together."],
        [""],
        ["Linking: invent your own 'ref' values (f1, c1, ...) and cite them."],
        ["  Cohorts.facilitator_ref  -> a Facilitators.ref, OR an existing facilitator id (FAC-003)."],
        ["  Players.cohort_ref       -> a Cohorts.ref."],
        ["Refs are yours to choose because none of these records exist yet."],
        [""],
        [f"max_players is per cohort, default {MAX_PLAYERS_CEILING}, ceiling {MAX_PLAYERS_CEILING}."],
        ["'programme' is optional everywhere. 'name' is always required."],
        [""],
        ["ALL-OR-NOTHING: the whole workbook is validated first. One bad row and"],
        ["nothing at all is created, so a failed upload never leaves half a programme."],
        ["Use Preview to see every error at once before committing."],
        [""],
        ["A role you are not permitted to grant is downgraded to 'facilitator'."],
    ):
        notes.append(line)
    notes.column_dimensions["A"].width = 95
    wb.save(str(out_path))
    return str(out_path)
