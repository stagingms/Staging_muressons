"""
Muressons Simulation — Stakeholder Matrix Excel Converter
Bidirectional converter between stakeholder config dicts ↔ stakeholder_matrix.xlsx

Usage (standalone):
    python stakeholder_config_excel.py export [output_path]   # dict → Excel
    python stakeholder_config_excel.py import [input_path]    # Excel → dict

Dev/admin dependency only — openpyxl is lazily imported inside functions so it
is NOT required at simulation runtime.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# ── Constants ────────────────────────────────────────────────
SHEET_NAME = "Stakeholder Matrix"

COLUMNS = [
    "ID",
    "Name",
    "Icon",
    "Correct Quadrant",
    "Alternate Quadrant",
    "Urgency",
    "Legitimacy",
    "Description",
    "Urgency Rationale",
    "Alternate Rationale",
    "Intel Dossier 1",
    "Intel Dossier 2",
    "Intel Dossier 3",
    "Engagement Tactic 1",
    "Engagement Tactic 2",
    "Engagement Tactic 3",
]

VALID_QUADRANTS = {"manage_closely", "keep_informed", "keep_satisfied", "monitor"}
VALID_URGENCY_LEGITIMACY = {"high", "medium", "low"}

_COL_WIDTHS = [
    20,   # ID
    32,   # Name
    6,    # Icon
    18,   # Correct Quadrant
    18,   # Alternate Quadrant
    10,   # Urgency
    10,   # Legitimacy
    60,   # Description
    50,   # Urgency Rationale
    50,   # Alternate Rationale
    60,   # Intel Dossier 1
    60,   # Intel Dossier 2
    60,   # Intel Dossier 3
    60,   # Engagement Tactic 1
    60,   # Engagement Tactic 2
    60,   # Engagement Tactic 3
]


# ═══════════════════════════════════════════════════════════════
#  EXPORT: list[dict] → Excel
# ═══════════════════════════════════════════════════════════════

def _encode_tactic(tactic: dict) -> str:
    """Encode a single engagement tactic dict to pipe-delimited string.

    Format: ``Label|true/false|Rationale``
    """
    label = tactic.get("label", "")
    correct = "true" if tactic.get("correct") else "false"
    rationale = tactic.get("rationale", "")
    return f"{label}|{correct}|{rationale}"


def export_stakeholders_to_excel(
    stakeholders: list[dict],
    output_path: str | Path,
) -> None:
    """Write a list of stakeholder dicts to a richly formatted Excel file.

    openpyxl is imported lazily so this module can be imported at runtime
    without triggering an ImportError when openpyxl is absent.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME

    # ── Styles ────────────────────────────────────────────
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1B4F72", end_color="1B4F72", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    data_font = Font(name="Calibri", size=10)
    id_font = Font(name="Consolas", size=10)
    thin_border = Border(bottom=Side(style="thin", color="D5D8DC"))
    row_fill_even = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
    row_fill_odd = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    # ── Header row ────────────────────────────────────────
    for col_idx, (header, width) in enumerate(zip(COLUMNS, _COL_WIDTHS), 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{len(stakeholders) + 1}"

    # ── Data rows ─────────────────────────────────────────
    for row_idx, sh in enumerate(stakeholders, 2):
        intel = sh.get("intel_dossier", [])
        tactics = sh.get("engagement_tactics", [])

        values = [
            sh.get("id", ""),
            sh.get("name", ""),
            sh.get("icon", ""),
            sh.get("correct_quadrant", ""),
            sh.get("alternate_quadrant", ""),
            sh.get("urgency", ""),
            sh.get("legitimacy", ""),
            sh.get("description", ""),
            sh.get("urgency_rationale", ""),
            sh.get("alternate_rationale", ""),
            intel[0] if len(intel) > 0 else "",
            intel[1] if len(intel) > 1 else "",
            intel[2] if len(intel) > 2 else "",
            _encode_tactic(tactics[0]) if len(tactics) > 0 else "",
            _encode_tactic(tactics[1]) if len(tactics) > 1 else "",
            _encode_tactic(tactics[2]) if len(tactics) > 2 else "",
        ]

        fill = row_fill_even if (row_idx % 2 == 0) else row_fill_odd

        for col_idx, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = id_font if col_idx == 1 else data_font
            cell.fill = fill
            cell.alignment = Alignment(vertical="center", wrap_text=(col_idx >= 8))
            cell.border = thin_border

    # ── Save ──────────────────────────────────────────────
    ws.sheet_properties.tabColor = "1B4F72"
    wb.save(str(output_path))


# ═══════════════════════════════════════════════════════════════
#  IMPORT: Excel → list[dict]
# ═══════════════════════════════════════════════════════════════

def _parse_tactic(raw: str) -> dict | None:
    """Parse a pipe-delimited engagement tactic string back to a dict.

    Expected format: ``Label|true/false|Rationale``
    Returns None if the string is empty or unparseable.
    """
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    if not raw:
        return None
    parts = raw.split("|", 2)
    if len(parts) < 3:
        return None
    label = parts[0].strip()
    correct = parts[1].strip().lower() in ("true", "1", "yes")
    rationale = parts[2].strip()
    if not label:
        return None
    # Generate a stable tactic id from label
    tactic_id = label.lower().replace(" ", "_")[:40]
    return {
        "id": tactic_id,
        "label": label,
        "correct": correct,
        "rationale": rationale,
    }


def import_stakeholders_from_excel(xlsx_path: str | Path) -> list[dict]:
    """Read a Stakeholder Matrix Excel file and return a validated list of stakeholder dicts.

    openpyxl is imported lazily.

    Raises ``ValueError`` on validation failures with a descriptive message.
    """
    from openpyxl import load_workbook

    wb = load_workbook(str(xlsx_path), read_only=True, data_only=True)

    # Try to find the correct sheet
    if SHEET_NAME in wb.sheetnames:
        ws = wb[SHEET_NAME]
    else:
        ws = wb.active

    stakeholders: list[dict] = []
    seen_ids: set[str] = set()
    errors: list[str] = []

    # Read header row to build column map
    header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
    if header_row is None:
        raise ValueError("Excel file has no header row.")

    # Build col_name → index mapping (case-insensitive, strip whitespace)
    col_map: dict[str, int] = {}
    for idx, val in enumerate(header_row):
        if val is not None:
            col_map[str(val).strip().lower()] = idx

    def _get(row_values: tuple, col_name: str) -> str:
        """Safely retrieve a cell value by column header name."""
        idx = col_map.get(col_name.lower())
        if idx is None or idx >= len(row_values):
            return ""
        val = row_values[idx]
        return str(val).strip() if val is not None else ""

    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
        if row is None or all(cell is None for cell in row):
            continue

        sid = _get(row, "ID")
        if not sid:
            continue  # skip empty rows

        # ── Validate ID uniqueness ────────────────────────
        if sid in seen_ids:
            errors.append(f"Row {row_num}: Duplicate stakeholder ID '{sid}'.")
        seen_ids.add(sid)

        # ── Parse fields ──────────────────────────────────
        name = _get(row, "Name")
        icon = _get(row, "Icon") or "👤"
        correct_quadrant = _get(row, "Correct Quadrant").lower().replace(" ", "_")
        alternate_quadrant = _get(row, "Alternate Quadrant").lower().replace(" ", "_")
        urgency = _get(row, "Urgency").lower()
        legitimacy = _get(row, "Legitimacy").lower()
        description = _get(row, "Description")
        urgency_rationale = _get(row, "Urgency Rationale")
        alternate_rationale = _get(row, "Alternate Rationale")

        # ── Validate quadrants ────────────────────────────
        if correct_quadrant not in VALID_QUADRANTS:
            errors.append(
                f"Row {row_num} ('{sid}'): Invalid correct_quadrant '{correct_quadrant}'. "
                f"Must be one of: {', '.join(sorted(VALID_QUADRANTS))}"
            )
        if alternate_quadrant and alternate_quadrant not in VALID_QUADRANTS:
            errors.append(
                f"Row {row_num} ('{sid}'): Invalid alternate_quadrant '{alternate_quadrant}'. "
                f"Must be one of: {', '.join(sorted(VALID_QUADRANTS))}"
            )

        # ── Validate urgency / legitimacy ─────────────────
        if urgency and urgency not in VALID_URGENCY_LEGITIMACY:
            errors.append(
                f"Row {row_num} ('{sid}'): Invalid urgency '{urgency}'. "
                f"Must be one of: {', '.join(sorted(VALID_URGENCY_LEGITIMACY))}"
            )
        if legitimacy and legitimacy not in VALID_URGENCY_LEGITIMACY:
            errors.append(
                f"Row {row_num} ('{sid}'): Invalid legitimacy '{legitimacy}'. "
                f"Must be one of: {', '.join(sorted(VALID_URGENCY_LEGITIMACY))}"
            )

        # ── Intel dossier ─────────────────────────────────
        intel_dossier: list[str] = []
        for n in range(1, 4):
            val = _get(row, f"Intel Dossier {n}")
            if val:
                intel_dossier.append(val)

        # ── Engagement tactics ────────────────────────────
        engagement_tactics: list[dict] = []
        for n in range(1, 4):
            val = _get(row, f"Engagement Tactic {n}")
            parsed = _parse_tactic(val)
            if parsed:
                engagement_tactics.append(parsed)

        # ── Build stakeholder dict ────────────────────────
        sh: dict[str, Any] = {
            "id": sid,
            "name": name,
            "icon": icon,
            "correct_quadrant": correct_quadrant,
            "urgency": urgency or "low",
            "legitimacy": legitimacy or "low",
            "description": description,
            "urgency_rationale": urgency_rationale,
            "intel_dossier": intel_dossier,
        }
        if alternate_quadrant:
            sh["alternate_quadrant"] = alternate_quadrant
        if alternate_rationale:
            sh["alternate_rationale"] = alternate_rationale
        if engagement_tactics:
            sh["engagement_tactics"] = engagement_tactics

        stakeholders.append(sh)

    wb.close()

    # ── Final validation ──────────────────────────────────
    if not stakeholders:
        raise ValueError("No stakeholders found in the Excel file.")

    if errors:
        raise ValueError(
            f"Validation failed with {len(errors)} error(s):\n"
            + "\n".join(f"  • {e}" for e in errors)
        )

    return stakeholders


# ═══════════════════════════════════════════════════════════════
#  CLI (standalone usage)
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Usage: python stakeholder_config_excel.py [export|import] [path]")
        print("  export  — Generate Excel from canonical STAKEHOLDERS")
        print("  import  — Parse Excel back to stakeholder dicts (JSON to stdout)")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "export":
        from stakeholder_map import STAKEHOLDERS
        output_path = sys.argv[2] if len(sys.argv) > 2 else "stakeholder_matrix.xlsx"
        export_stakeholders_to_excel(STAKEHOLDERS, output_path)
        print(f"[OK] Exported {len(STAKEHOLDERS)} stakeholders to: {output_path}")

    elif command == "import":
        input_path = sys.argv[2] if len(sys.argv) > 2 else "stakeholder_matrix.xlsx"
        try:
            stakeholders = import_stakeholders_from_excel(input_path)
            print(json.dumps(stakeholders, indent=2, ensure_ascii=False))
            print(f"\n[OK] Imported {len(stakeholders)} stakeholders from: {input_path}")
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        print("Use 'export' or 'import'")
        sys.exit(1)


if __name__ == "__main__":
    main()
