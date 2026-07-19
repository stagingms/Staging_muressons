"""
stakeholder_bulk_excel.py — multi-scope ("master file") stakeholder import.

The single-scope importer (stakeholder_config_excel) reads one sheet of
stakeholders and the CALLER decides which config they belong to. That means one
upload per region and per vertical — 5 regions x 6 verticals + canonical is up
to 31 separate uploads to seed a platform.

This module accepts ONE workbook covering many scopes at once, in either of the
two shapes an administrator would naturally produce:

  A. Scope columns. A single sheet with the usual stakeholder columns plus
     "Vertical" and/or "Region" columns; each row is routed to the config those
     two fields name.

  B. Sheet-per-scope. One sheet per scope, named for the scope
     ("Region - Europe", "Vertical - Pharma", "Canonical", or a bare config id
     such as "europe" / "vertical_pharma").

     NOTE: Excel rejects ':' in sheet names (also \\ / ? * [ ]), so the
     separator must be a dash, underscore or space — "Region - Europe", not
     "Region: Europe". Guidance text elsewhere must not suggest a colon.

Both forms resolve to the same thing: a mapping of config_id -> stakeholder
list, ready for stakeholder_db.save_region_config.

Design decisions worth knowing:

  * Parsing is TOTAL before anything is written. A bulk import that half-applies
    is worse than one that refuses, because the operator cannot tell which
    scopes are stale. The router therefore validates every scope, then commits.
  * Scope labels are matched leniently (case, spacing, punctuation, emoji and
    common aliases like "India" -> south_asia) because these files are written
    by humans, but the RESULT is always a strict slug that stakeholder_db will
    accept.
  * A row whose scope cannot be resolved is an error, never a silent drop —
    silently discarding a region's worth of stakeholders is exactly the failure
    an operator would not notice until a class was running.
  * A row naming BOTH an industry and a region produces a composite scope
    (``vertical_pharma__south_asia``) rather than an error, so an industry map
    can be localised per market.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from stakeholder_config_excel import (
    COLUMNS,
    SHEET_NAME,
    VALID_QUADRANTS,
    VALID_URGENCY_LEGITIMACY,
    _parse_tactic,
)

# Scope columns recognised in form A (in addition to the standard COLUMNS).
VERTICAL_COL_ALIASES = ("vertical", "industry vertical", "industry", "business", "business unit")
REGION_COL_ALIASES = ("region", "geographic region", "geography", "market")

CANONICAL_ID = "canonical"

# Known scopes. Aliases are matched after normalisation (lowercase, non-alnum
# collapsed to underscore), so "🇮🇳 India", "India", "south asia" all land on
# south_asia.
REGION_IDS = {
    "asean": ("asean", "sea", "south_east_asia", "southeast_asia"),
    "south_asia": ("south_asia", "india", "in", "in_india", "sa"),
    "europe": ("europe", "eu", "emea"),
    "north_america": ("north_america", "na", "usa", "us", "united_states"),
    "africa": ("africa", "af"),
}
VERTICAL_IDS = {
    "agriculture": ("agriculture", "agri", "farming"),
    "banking_financial_services": ("banking_financial_services", "banking", "bfsi",
                                   "banking_finance", "financial_services", "finance"),
    "oil_gas": ("oil_gas", "oil", "gas", "oil_and_gas", "energy_oil_gas"),
    "retail_fmcg": ("retail_fmcg", "retail", "fmcg", "consumer_goods", "retail_consumer"),
    "technology": ("technology", "tech", "software", "it"),
    "chemicals": ("chemicals", "chemical", "specialty_chemicals", "petrochemicals"),
    "electronics": ("electronics", "electronic", "semiconductors", "hardware"),
    "pharma": ("pharma", "pharmaceutical", "pharmaceuticals", "healthcare",
               "pharma_healthcare", "health"),
}


def _norm(v: Any) -> str:
    """Normalise a human-written scope label to a comparable token."""
    s = re.sub(r"[^a-z0-9]+", "_", str(v or "").strip().lower())
    return s.strip("_")


def _match(token: str, table: dict[str, tuple[str, ...]]) -> str | None:
    if not token:
        return None
    for canonical, aliases in table.items():
        if token == canonical or token in aliases:
            return canonical
    return None


def _split_composite(tok: str) -> str | None:
    """Recognise an industry+region token as a composite scope id.

    Cannot rely on the "__" separator: _norm collapses any run of non-alphanumeric
    characters to a SINGLE underscore, so "vertical_pharma__south_asia" arrives
    here as "vertical_pharma_south_asia". Match against known pairs instead —
    unambiguous because vertical and region vocabularies are disjoint.
    """
    if not tok:
        return None
    body = tok[len("vertical_"):] if tok.startswith("vertical_") else tok
    for v_id, v_aliases in VERTICAL_IDS.items():
        for v_alias in (v_id, *v_aliases):
            prefix = f"{v_alias}_"
            if body.startswith(prefix):
                r_id = _match(body[len(prefix):], REGION_IDS)
                if r_id:
                    return f"vertical_{v_id}__{r_id}"
    return None


def resolve_scope(vertical_raw: Any = "", region_raw: Any = "") -> tuple[str | None, str | None]:
    """Map raw vertical/region labels to a (config_id, error) pair.

    Scope ids:
      vertical + region -> ``vertical_<v>__<r>``  (industry localised to a market)
      vertical only     -> ``vertical_<v>``
      region only       -> ``<r>``
      neither           -> ``canonical``

    The composite form exists because an industry's stakeholder map genuinely
    differs by market (pharma in India is not pharma in Europe). It is resolved
    ahead of the plain vertical scope by stakeholder_map.get_stakeholders_for_session.
    """
    v_tok, r_tok = _norm(vertical_raw), _norm(region_raw)

    # Explicit canonical markers in either column.
    if v_tok in ("canonical", "default", "all", "") and r_tok in ("canonical", "default", "all", ""):
        return CANONICAL_ID, None

    v_id = _match(v_tok, VERTICAL_IDS) if v_tok not in ("", "canonical", "default", "all") else None
    r_id = _match(r_tok, REGION_IDS) if r_tok not in ("", "canonical", "default", "all") else None

    if v_tok and v_id is None and v_tok not in ("canonical", "default", "all"):
        return None, f"unknown vertical '{vertical_raw}'"
    if r_tok and r_id is None and r_tok not in ("canonical", "default", "all"):
        return None, f"unknown region '{region_raw}'"

    if v_id and r_id:
        # Composite industry x region scope. Kept within the 50-char slug rule
        # enforced by stakeholder_db.save_region_config; the double underscore
        # is the separator so the two halves stay recoverable.
        return f"vertical_{v_id}__{r_id}", None
    if v_id:
        return f"vertical_{v_id}", None
    if r_id:
        return r_id, None
    return CANONICAL_ID, None


def resolve_sheet_scope(sheet_name: str) -> tuple[str | None, str | None]:
    """Map a sheet name to a config id (form B)."""
    raw = str(sheet_name or "").strip()
    tok = _norm(raw)
    if tok in ("canonical", "default", "stakeholder_matrix", "all", ""):
        return CANONICAL_ID, None
    # Composite industry x region, e.g. "vertical_pharma__south_asia",
    # "Pharma - India". MUST precede the prefix regex below, which would
    # otherwise consume the "vertical_" prefix and lose the region half.
    composite = _split_composite(tok)
    if composite:
        return composite, None
    # "Region - Europe" / "Vertical - Pharma"
    m = re.match(r"^(region|vertical|industry|business)[_\s:-]+(.*)$", tok)
    if m:
        kind, rest = m.group(1), m.group(2)
        if kind == "region":
            rid = _match(rest, REGION_IDS)
            return (rid, None) if rid else (None, f"unknown region in sheet '{raw}'")
        vid = _match(rest, VERTICAL_IDS)
        return (f"vertical_{vid}", None) if vid else (None, f"unknown vertical in sheet '{raw}'")
    if tok.startswith("vertical_"):
        vid = _match(tok[len("vertical_"):], VERTICAL_IDS)
        return (f"vertical_{vid}", None) if vid else (None, f"unknown vertical in sheet '{raw}'")
    rid = _match(tok, REGION_IDS)
    if rid:
        return rid, None
    vid = _match(tok, VERTICAL_IDS)
    if vid:
        return f"vertical_{vid}", None
    return None, f"sheet '{raw}' does not name a known region, vertical or 'Canonical'"


# ── Row parsing (mirrors the single-scope validator) ────────────────────────

def _row_to_stakeholder(get, row_num: int, errors: list[str]) -> dict | None:
    sid = get("ID")
    if not sid:
        return None
    # Hyphens are allowed. A stakeholder id is only ever a dict key (master_map,
    # the client's quadrant mapping) — never a filename, so the strict slug rule
    # that governs config_id does not apply here. Rejecting "in-pharma-cdsco"
    # would force authors to rewrite their own identifiers for no safety gain.
    if not re.match(r"^[a-z0-9_-]{1,50}$", sid):
        errors.append(
            f"Row {row_num}: ID '{sid}' must be lowercase letters, digits, "
            f"underscore or hyphen (max 50 characters)."
        )
        return None

    name = get("Name")
    if not name:
        errors.append(f"Row {row_num}: Name is required for '{sid}'.")

    quadrant = get("Correct Quadrant").lower().replace(" ", "_")
    if quadrant and quadrant not in VALID_QUADRANTS:
        errors.append(
            f"Row {row_num}: Correct Quadrant '{quadrant}' for '{sid}' is invalid "
            f"(expected one of {sorted(VALID_QUADRANTS)})."
        )
    alternate_quadrant = get("Alternate Quadrant").lower().replace(" ", "_")
    if alternate_quadrant and alternate_quadrant not in VALID_QUADRANTS:
        errors.append(
            f"Row {row_num}: Alternate Quadrant '{alternate_quadrant}' for '{sid}' is invalid."
        )

    urgency = get("Urgency").lower()
    legitimacy = get("Legitimacy").lower()
    for label, val in (("Urgency", urgency), ("Legitimacy", legitimacy)):
        if val and val not in VALID_URGENCY_LEGITIMACY:
            errors.append(
                f"Row {row_num}: {label} '{val}' for '{sid}' is invalid "
                f"(expected high/medium/low)."
            )

    intel = [get(f"Intel Dossier {i}") for i in (1, 2, 3)]
    intel = [x for x in intel if x]
    tactics = []
    for i in (1, 2, 3):
        parsed = _parse_tactic(get(f"Engagement Tactic {i}"))
        if parsed:
            tactics.append(parsed)

    sh: dict[str, Any] = {
        "id": sid,
        "name": name,
        "icon": get("Icon") or "👤",
        "correct_quadrant": quadrant or "monitor",
        "urgency": urgency or "low",
        "legitimacy": legitimacy or "low",
        "description": get("Description"),
        "urgency_rationale": get("Urgency Rationale"),
        "intel_dossier": intel,
    }
    if alternate_quadrant:
        sh["alternate_quadrant"] = alternate_quadrant
    if get("Alternate Rationale"):
        sh["alternate_rationale"] = get("Alternate Rationale")
    if tactics:
        sh["engagement_tactics"] = tactics
    return sh


def parse_bulk_workbook(xlsx_path: str | Path) -> dict[str, list[dict]]:
    """Parse a multi-scope workbook into {config_id: [stakeholder, ...]}.

    Raises ValueError listing EVERY problem found (never partial success).
    """
    from openpyxl import load_workbook

    wb = load_workbook(str(xlsx_path), read_only=True, data_only=True)
    scopes: dict[str, list[dict]] = {}
    seen: dict[str, set[str]] = {}
    errors: list[str] = []

    try:
        for ws in wb.worksheets:
            header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
            if header_row is None:
                continue
            col_map = {
                str(v).strip().lower(): i
                for i, v in enumerate(header_row) if v is not None
            }
            if "id" not in col_map:
                continue  # not a stakeholder sheet (notes/instructions tabs are fine)

            v_col = next((col_map[a] for a in VERTICAL_COL_ALIASES if a in col_map), None)
            r_col = next((col_map[a] for a in REGION_COL_ALIASES if a in col_map), None)
            has_scope_cols = v_col is not None or r_col is not None

            # Form B: sheet name carries the scope (only when no scope columns).
            sheet_scope = None
            if not has_scope_cols:
                sheet_scope, err = resolve_sheet_scope(ws.title)
                if err:
                    # A single-sheet workbook with the default name is the
                    # canonical set — that is the legacy shape, accept it.
                    if len(wb.worksheets) == 1 or ws.title.strip() == SHEET_NAME:
                        sheet_scope = CANONICAL_ID
                    else:
                        errors.append(f"Sheet '{ws.title}': {err}")
                        continue

            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
                if row is None or all(c is None for c in row):
                    continue

                def get(col_name: str, _row=row) -> str:
                    idx = col_map.get(col_name.lower())
                    if idx is None or idx >= len(_row):
                        return ""
                    val = _row[idx]
                    return str(val).strip() if val is not None else ""

                if has_scope_cols:
                    v_raw = row[v_col] if v_col is not None and v_col < len(row) else ""
                    r_raw = row[r_col] if r_col is not None and r_col < len(row) else ""
                    scope, err = resolve_scope(v_raw, r_raw)
                    if err:
                        errors.append(f"Sheet '{ws.title}' row {row_num}: {err}.")
                        continue
                else:
                    scope = sheet_scope

                sh = _row_to_stakeholder(get, row_num, errors)
                if sh is None:
                    continue

                ids = seen.setdefault(scope, set())
                if sh["id"] in ids:
                    errors.append(
                        f"Sheet '{ws.title}' row {row_num}: duplicate stakeholder ID "
                        f"'{sh['id']}' within scope '{scope}'."
                    )
                    continue
                ids.add(sh["id"])
                scopes.setdefault(scope, []).append(sh)
    finally:
        wb.close()

    if not scopes and not errors:
        raise ValueError(
            "No stakeholder rows found. Expect a header row containing 'ID' plus the "
            "standard stakeholder columns, and either Vertical/Region columns or one "
            "sheet per scope."
        )
    if errors:
        raise ValueError(
            f"Validation failed with {len(errors)} error(s):\n"
            + "\n".join(f"  • {e}" for e in errors[:60])
            + ("\n  … and more" if len(errors) > 60 else "")
        )
    return scopes


def build_bulk_template(output_path: str | Path,
                        existing: dict[str, list[dict]] | None = None) -> None:
    """Write a master template: one sheet, scope columns first, pre-filled with
    whatever configs already exist so an operator edits rather than retypes."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Stakeholder Master"

    headers = ["Vertical", "Region"] + COLUMNS
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1B4F72", end_color="1B4F72", fill_type="solid")
    scope_fill = PatternFill(start_color="0E6655", end_color="0E6655", fill_type="solid")
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=i, value=h)
        c.font = header_font
        c.fill = scope_fill if i <= 2 else header_fill
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = 22 if i <= 2 else 28
    ws.freeze_panes = "C2"

    def scope_labels(config_id: str) -> tuple[str, str]:
        if config_id == CANONICAL_ID:
            return "Canonical", ""
        if config_id.startswith("vertical_"):
            return config_id[len("vertical_"):], ""
        return "", config_id

    row = 2
    for config_id, items in sorted((existing or {}).items()):
        v_label, r_label = scope_labels(config_id)
        for sh in items:
            ws.cell(row=row, column=1, value=v_label)
            ws.cell(row=row, column=2, value=r_label)
            vals = [
                sh.get("id", ""), sh.get("name", ""), sh.get("icon", ""),
                sh.get("correct_quadrant", ""), sh.get("alternate_quadrant", ""),
                sh.get("urgency", ""), sh.get("legitimacy", ""),
                sh.get("description", ""), sh.get("urgency_rationale", ""),
                sh.get("alternate_rationale", ""),
            ]
            intel = sh.get("intel_dossier") or []
            vals += [intel[i] if i < len(intel) else "" for i in range(3)]
            tactics = sh.get("engagement_tactics") or []
            for i in range(3):
                t = tactics[i] if i < len(tactics) else None
                # Must match _parse_tactic's contract EXACTLY: label|correct|rationale.
                # A previous version wrote "option_text | rationale" — a key that
                # does not exist on stored tactics and only two fields — so every
                # tactic was silently dropped on export→import round-trip.
                if isinstance(t, dict):
                    label = t.get("label") or t.get("option_text") or ""
                    correct = "true" if t.get("correct") else "false"
                    vals.append(f"{label}|{correct}|{t.get('rationale','')}" if label else "")
                else:
                    vals.append("")
            for j, v in enumerate(vals, 3):
                ws.cell(row=row, column=j, value=v)
            row += 1

    # Guidance sheet — no 'ID' column, so the parser ignores it.
    guide = wb.create_sheet("How to use")
    lines = [
        ("Stakeholder master upload", True),
        ("", False),
        ("Fill ONE row per stakeholder. Use the Vertical or Region column to say which", False),
        ("configuration the row belongs to — not both on the same row.", False),
        ("", False),
        ("  Vertical column: agriculture, banking_financial_services, oil_gas,", False),
        ("                   retail_fmcg, technology, pharma", False),
        ("  Region column:   asean, south_asia (India), europe, north_america, africa", False),
        ("  Leave both blank (or write 'Canonical') for the default set.", False),
        ("", False),
        ("Alternatively, delete the scope columns and put each scope on its own sheet", False),
        ("named e.g. 'Region - Europe', 'Vertical - Pharma' or 'Canonical'.", False),
        ("(Excel does not allow ':' in a sheet name — use a dash or underscore.)", False),
        ("", False),
        ("Uploading REPLACES the full stakeholder list for every scope present in the", False),
        ("file. Scopes absent from the file are left untouched. Preview before applying.", False),
    ]
    for i, (text, bold) in enumerate(lines, 1):
        c = guide.cell(row=i, column=1, value=text)
        if bold:
            c.font = Font(bold=True, size=13)
    guide.column_dimensions["A"].width = 100

    wb.save(str(output_path))
