"""
Muressons Simulation — Materiality Config Excel Converter
Bidirectional converter between materiality_config JSON ↔ .xlsx

Two sheets:
  1. "Issues"              — all MaterialityIssue fields
  2. "Interdependencies"   — all InterdependenceLink fields

The consultant_fee_usd is stored as a metadata row in the Issues sheet
(row 2, merged, clearly labelled).

openpyxl is lazily imported inside each public function so the
simulation runtime never depends on it.
"""

from __future__ import annotations

import json
import pathlib
from pathlib import Path
from typing import Any


# ── Column definitions ───────────────────────────────────────────
_ISSUE_COLUMNS = [
    ("id",                   "ID"),
    ("title",                "Title"),
    ("category",             "Category"),
    ("financial_impact",     "Financial Impact"),
    ("societal_impact",      "Societal Impact"),
    ("severity_score",       "Severity Score"),
    ("likelihood_score",     "Likelihood Score"),
    ("mitigation_cost_usd",  "Mitigation Cost USD"),
    ("disclosure_required",  "Disclosure Required"),
    ("is_ambiguous",         "Is Ambiguous"),
    ("esrs_topic",           "ESRS Topic"),
    ("value_chain_scope",    "Value Chain Scope"),
    ("time_horizon",         "Time Horizon"),
    ("hover_description",    "Hover Description"),
    ("blindspot_description","Blindspot Description"),
    ("electronics_sensitive","Electronics Sensitive"),
]

_LINK_COLUMNS = [
    ("source_issue_id",  "Source Issue ID"),
    ("target_issue_id",  "Target Issue ID"),
    ("severity",         "Severity"),
    ("description",      "Description"),
]

# Also accept legacy key names used in some configs
_LINK_KEY_ALIASES = {
    "source": "source_issue_id",
    "target": "target_issue_id",
}

# ── Validation constants ─────────────────────────────────────────
_VALID_CATEGORIES = {"economic", "environmental", "ecological", "social", "governance"}
_VALID_IMPACTS    = {"high", "medium", "low"}


# ═══════════════════════════════════════════════════════════════
#  EXPORT: dict → Excel
# ═══════════════════════════════════════════════════════════════

def export_materiality_to_excel(config: dict, output_path) -> None:
    """
    Write a richly-formatted .xlsx file from a materiality config dict.

    Parameters
    ----------
    config : dict
        Must contain keys ``issues``, ``interdependencies``, and optionally
        ``consultant_fee_usd``.
    output_path : str or Path
        Destination file path.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    output_path = Path(output_path)
    wb = Workbook()

    # ── Shared styles ─────────────────────────────────────────
    thin_border = Border(bottom=Side(style="thin", color="D5D8DC"))
    data_font   = Font(name="Calibri", size=10)
    bold_font   = Font(name="Calibri", size=10, bold=True)
    meta_font   = Font(name="Calibri", size=10, italic=True, color="2E86C1")
    row_even    = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
    row_odd     = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    # ──────────────────────────────────────────────────────────
    # SHEET 1: Issues
    # ──────────────────────────────────────────────────────────
    ws_issues = wb.active
    ws_issues.title = "Issues"
    ws_issues.sheet_properties.tabColor = "1B4F72"

    issue_header_fill = PatternFill(start_color="1B4F72", end_color="1B4F72", fill_type="solid")
    issue_header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_align      = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Row 1: Consultant fee metadata
    fee = config.get("consultant_fee_usd", 1_500_000)
    fee_cell = ws_issues.cell(row=1, column=1, value=f"Consultant Fee (USD): {fee:,}")
    fee_cell.font = meta_font
    fee_cell.alignment = Alignment(vertical="center")
    ws_issues.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(_ISSUE_COLUMNS))

    # Row 2: Headers
    col_widths = [20, 32, 16, 18, 18, 14, 14, 20, 18, 14, 14, 18, 14, 55, 45, 20]
    for col_idx, ((_, header), width) in enumerate(zip(_ISSUE_COLUMNS, col_widths), 1):
        cell = ws_issues.cell(row=2, column=col_idx, value=header)
        cell.font      = issue_header_font
        cell.fill      = issue_header_fill
        cell.alignment = header_align
        cell.border    = thin_border
        ws_issues.column_dimensions[get_column_letter(col_idx)].width = width

    ws_issues.freeze_panes = "A3"

    # Data rows
    for r_idx, issue in enumerate(config.get("issues", []), start=3):
        fill = row_even if (r_idx % 2 == 0) else row_odd
        for col_idx, (key, _) in enumerate(_ISSUE_COLUMNS, 1):
            value = issue.get(key, "")
            if isinstance(value, bool):
                value = str(value).upper()
            cell = ws_issues.cell(row=r_idx, column=col_idx, value=value)
            cell.font   = bold_font if col_idx <= 2 else data_font
            cell.fill   = fill
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center", wrap_text=(col_idx >= 14))

    # ──────────────────────────────────────────────────────────
    # SHEET 2: Interdependencies
    # ──────────────────────────────────────────────────────────
    ws_links = wb.create_sheet("Interdependencies")
    ws_links.sheet_properties.tabColor = "6C3483"

    link_header_fill = PatternFill(start_color="6C3483", end_color="6C3483", fill_type="solid")
    link_header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

    link_widths = [24, 24, 12, 60]
    for col_idx, ((_, header), width) in enumerate(zip(_LINK_COLUMNS, link_widths), 1):
        cell = ws_links.cell(row=1, column=col_idx, value=header)
        cell.font      = link_header_font
        cell.fill      = link_header_fill
        cell.alignment = header_align
        cell.border    = thin_border
        ws_links.column_dimensions[get_column_letter(col_idx)].width = width

    ws_links.freeze_panes = "A2"

    for r_idx, link in enumerate(config.get("interdependencies", []), start=2):
        fill = row_even if (r_idx % 2 == 0) else row_odd
        for col_idx, (key, _) in enumerate(_LINK_COLUMNS, 1):
            # Support legacy key names (source/target vs source_issue_id/target_issue_id)
            value = link.get(key, link.get({v: k for k, v in _LINK_KEY_ALIASES.items()}.get(key, ""), ""))
            cell = ws_links.cell(row=r_idx, column=col_idx, value=value)
            cell.font   = data_font
            cell.fill   = fill
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center", wrap_text=(col_idx == 4))

    wb.save(str(output_path))


# ═══════════════════════════════════════════════════════════════
#  IMPORT: Excel → dict
# ═══════════════════════════════════════════════════════════════

def import_materiality_from_excel(xlsx_path) -> dict:
    """
    Read a materiality Excel file and return a validated config dict.

    Parameters
    ----------
    xlsx_path : str or Path
        Path to the .xlsx file.

    Returns
    -------
    dict
        ``{"issues": [...], "interdependencies": [...], "consultant_fee_usd": int}``

    Raises
    ------
    ValueError
        On validation failure with a descriptive message.
    """
    from openpyxl import load_workbook

    xlsx_path = Path(xlsx_path)
    wb = load_workbook(str(xlsx_path), read_only=True, data_only=True)

    # ── Parse consultant fee from Issues sheet row 1 ──────────
    consultant_fee = 1_500_000  # default
    if "Issues" not in wb.sheetnames:
        raise ValueError("Excel file must contain a sheet named 'Issues'.")

    ws_issues = wb["Issues"]
    rows_iter = ws_issues.iter_rows(values_only=True)

    # Row 1: metadata row with consultant fee
    first_row = next(rows_iter, None)
    if first_row:
        cell_val = str(first_row[0] or "")
        if "Consultant Fee" in cell_val:
            # Extract number from "Consultant Fee (USD): 1,500,000"
            import re
            match = re.search(r"[\d,]+", cell_val.split(":")[-1])
            if match:
                consultant_fee = int(match.group().replace(",", ""))

    # Row 2: headers
    header_row = next(rows_iter, None)
    if header_row is None:
        raise ValueError("Issues sheet is missing the header row.")

    # Build column name → index mapping (normalised)
    header_map: dict[str, int] = {}
    for idx, val in enumerate(header_row):
        if val is None:
            continue
        normalised = str(val).strip().lower().replace(" ", "_")
        header_map[normalised] = idx

    # Build reverse lookup from our canonical keys
    _HEADER_ALIASES = {
        "id": ["id"],
        "title": ["title"],
        "category": ["category"],
        "financial_impact": ["financial_impact"],
        "societal_impact": ["societal_impact"],
        "severity_score": ["severity_score"],
        "likelihood_score": ["likelihood_score"],
        "mitigation_cost_usd": ["mitigation_cost_usd"],
        "disclosure_required": ["disclosure_required"],
        "is_ambiguous": ["is_ambiguous"],
        "esrs_topic": ["esrs_topic"],
        "value_chain_scope": ["value_chain_scope"],
        "time_horizon": ["time_horizon"],
        "hover_description": ["hover_description"],
        "blindspot_description": ["blindspot_description"],
        "electronics_sensitive": ["electronics_sensitive"],
    }

    def _resolve_col(canonical_key: str) -> int | None:
        for alias in _HEADER_ALIASES.get(canonical_key, [canonical_key]):
            if alias in header_map:
                return header_map[alias]
        return None

    # ── Read issues ───────────────────────────────────────────
    issues: list[dict] = []
    seen_ids: set[str] = set()
    errors: list[str]  = []

    for row_num, row in enumerate(rows_iter, start=3):
        if row is None or all(c is None for c in row):
            continue

        issue: dict[str, Any] = {}
        for key, _ in _ISSUE_COLUMNS:
            col_idx = _resolve_col(key)
            if col_idx is None or col_idx >= len(row):
                continue
            value = row[col_idx]
            if value is None:
                continue
            # Type coercion
            if key in ("severity_score", "likelihood_score"):
                try:
                    value = int(float(value))
                except (ValueError, TypeError):
                    value = 3
            elif key == "mitigation_cost_usd":
                try:
                    value = int(float(str(value).replace(",", "")))
                except (ValueError, TypeError):
                    value = 0
            elif key in ("disclosure_required", "is_ambiguous", "electronics_sensitive"):
                if isinstance(value, str):
                    value = value.strip().upper() in ("TRUE", "YES", "1")
                else:
                    value = bool(value)
            else:
                value = str(value).strip()
            issue[key] = value

        # Skip completely empty rows
        if not issue.get("id") and not issue.get("title"):
            continue

        # Auto-generate ID from title if missing
        if not issue.get("id") and issue.get("title"):
            import re
            issue["id"] = re.sub(r"[^a-z0-9]+", "_", issue["title"].lower()).strip("_")

        # ── Validate ──
        issue_id = issue.get("id", f"row_{row_num}")

        if not issue.get("id"):
            errors.append(f"Row {row_num}: Missing issue ID.")
            continue

        if issue_id in seen_ids:
            errors.append(f"Row {row_num}: Duplicate issue ID '{issue_id}'.")
            continue
        seen_ids.add(issue_id)

        cat = issue.get("category", "").lower()
        if cat and cat not in _VALID_CATEGORIES:
            errors.append(
                f"Row {row_num} ('{issue_id}'): Invalid category '{cat}'. "
                f"Must be one of {sorted(_VALID_CATEGORIES)}."
            )
        if cat:
            issue["category"] = cat

        for impact_key in ("financial_impact", "societal_impact"):
            val = str(issue.get(impact_key, "")).lower()
            if val and val not in _VALID_IMPACTS:
                errors.append(
                    f"Row {row_num} ('{issue_id}'): Invalid {impact_key} '{val}'. "
                    f"Must be high/medium/low."
                )
            if val:
                issue[impact_key] = val

        for score_key in ("severity_score", "likelihood_score"):
            val = issue.get(score_key)
            if val is not None and (not isinstance(val, int) or val < 1 or val > 5):
                errors.append(
                    f"Row {row_num} ('{issue_id}'): {score_key} must be 1-5, got '{val}'."
                )

        issues.append(issue)


    # ── Read interdependencies ────────────────────────────────
    interdependencies: list[dict] = []
    if "Interdependencies" in wb.sheetnames:
        ws_links = wb["Interdependencies"]
        link_rows = ws_links.iter_rows(values_only=True)

        link_header_row = next(link_rows, None)
        if link_header_row:
            link_header_map: dict[str, int] = {}
            for idx, val in enumerate(link_header_row):
                if val is None:
                    continue
                normalised = str(val).strip().lower().replace(" ", "_")
                link_header_map[normalised] = idx

            for row_num, row in enumerate(link_rows, start=2):
                if row is None or all(c is None for c in row):
                    continue

                link: dict[str, Any] = {}
                for key, _ in _LINK_COLUMNS:
                    col_idx = link_header_map.get(key)
                    if col_idx is None or col_idx >= len(row):
                        continue
                    value = row[col_idx]
                    if value is None:
                        continue
                    if key == "severity":
                        try:
                            value = int(float(value))
                        except (ValueError, TypeError):
                            value = 3
                    else:
                        value = str(value).strip()
                    link[key] = value

                src = link.get("source_issue_id", "")
                tgt = link.get("target_issue_id", "")
                if not src or not tgt:
                    continue

                # Validate references
                if src not in seen_ids:
                    errors.append(
                        f"Interdependencies row {row_num}: source_issue_id '{src}' "
                        f"does not match any issue ID."
                    )
                if tgt not in seen_ids:
                    errors.append(
                        f"Interdependencies row {row_num}: target_issue_id '{tgt}' "
                        f"does not match any issue ID."
                    )

                interdependencies.append(link)

    wb.close()

    if errors:
        raise ValueError(
            f"Validation failed with {len(errors)} error(s):\n"
            + "\n".join(f"  • {e}" for e in errors[:25])
        )

    return {
        "issues": issues,
        "interdependencies": interdependencies,
        "consultant_fee_usd": consultant_fee,
    }


# ═══════════════════════════════════════════════════════════════
#  CLI (optional dev helper)
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python materiality_config_excel.py [export|import] [json_path] [excel_path]")
        sys.exit(1)

    command = sys.argv[1].lower()
    json_path  = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "db" / "materiality_config.json"
    excel_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).parent.parent / "materiality_config.xlsx"

    if command == "export":
        with open(json_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        export_materiality_to_excel(cfg, excel_path)
        print(f"[OK] Exported {len(cfg.get('issues', []))} issues to {excel_path}")
    elif command == "import":
        result = import_materiality_from_excel(excel_path)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"[OK] Imported {len(result['issues'])} issues to {json_path}")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
#  REGION WORKBOOK — one file per region, one sheet per SBU
#
#  The single-config format above uses fixed sheets "Issues" and
#  "Interdependencies". A region workbook instead names one sheet per SBU
#  (pharma, electronics, consumer_goods, software), optionally paired with
#  "<slot> Interdependencies".
#
#  Rather than reimplement the row parsing — and inevitably drift from its
#  validation — each SBU sheet is lifted into a throwaway single-config
#  workbook with the names the existing parser expects, and
#  import_materiality_from_excel does the real work. Every validation rule,
#  present and future, is inherited for free.
# ═══════════════════════════════════════════════════════════════════════════

def import_region_workbook(xlsx_path, slots=None) -> dict:
    """Parse a region workbook into {slot: materiality config dict}.

    Sheets are matched to slots case-insensitively. Anything unmatched is
    simply absent from the result; the caller reports it, because a silently
    skipped sheet is how a cohort reaches a classroom half-configured.
    """
    import tempfile
    from openpyxl import load_workbook, Workbook

    if slots is None:
        try:
            from bu_profiles import DEFAULT_SLOTS
            slots = list(DEFAULT_SLOTS)
        except Exception:
            slots = ["pharma", "electronics", "consumer_goods", "software"]

    src = load_workbook(str(xlsx_path), read_only=True, data_only=True)
    names = {n.strip().lower(): n for n in src.sheetnames}

    out: dict = {}
    for slot in slots:
        sheet = names.get(slot.lower())
        if not sheet:
            continue
        interdep = names.get(f"{slot.lower()} interdependencies") or names.get(f"{slot.lower()}_interdependencies")

        tmp_wb = Workbook()
        tmp_wb.remove(tmp_wb.active)
        for src_name, dest_name in ((sheet, "Issues"), (interdep, "Interdependencies")):
            if not src_name:
                continue
            dest = tmp_wb.create_sheet(title=dest_name)
            for row in src[src_name].iter_rows(values_only=True):
                dest.append(list(row))

        tmp_path = pathlib.Path(tempfile.mkdtemp()) / f"{slot}.xlsx"
        tmp_wb.save(tmp_path)
        try:
            out[slot] = import_materiality_from_excel(tmp_path)
        except ValueError:
            # Malformed sheet for this slot: leave it out so the caller can
            # report it, rather than aborting the other three.
            continue
    return out
