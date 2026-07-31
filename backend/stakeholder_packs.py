"""stakeholder_packs — named, reusable per-SBU stakeholder matrices.

WHAT A PACK IS
--------------
A pack binds ONE stakeholder matrix to EACH of the four SBU slots for a single
region, under a name a facilitator can recognise:

    {"pack_id": "emea_2026",
     "label":   "EMEA 2026",
     "region":  "europe",
     "bus": {"pharma":         "vertical_pharma__europe",
             "electronics":    "vertical_electronics__europe",
             "consumer_goods": "vertical_consumer_goods__europe",
             "software":       "vertical_software__europe"}}

The values are ordinary stakeholder-config ids, so a pack owns no stakeholder
data of its own — it is an INDEX over configs that stakeholder_db already
stores. That is deliberate: packs can be added, renamed or deleted without ever
touching a matrix, and a config edited through the existing single-scope Excel
flow is immediately live in every pack that references it.

WHY IT EXISTS
-------------
get_stakeholders_for_session() resolves ONE set for the whole cohort, because
_resolve_active_vertical() returns a single vertical. In the 4-SBU conglomerate
format that means all four business units share one stakeholder map, so a
pharma BU and a software BU face identical stakeholders. Packs make the
resolution per-BU without disturbing that chain: when a cohort has no pack, or
a pack omits a slot, resolution falls through to exactly what happens today.

WHERE IT LIVES
--------------
On the durable volume via runtime_paths.data_subdir. The sibling
stakeholder_configs directory used to sit inside the image, so uploads were
discarded on every Railway redeploy; packs must not repeat that.
"""

from __future__ import annotations

import json
import pathlib
import re
import tempfile
from typing import Any

# The four conglomerate slots. Imported lazily in _slots() so this module never
# fails to import if bu_profiles moves.
_FALLBACK_SLOTS = ["pharma", "electronics", "consumer_goods", "software"]

_PACK_ID_RE = re.compile(r"^[a-z0-9_]{1,50}$")

_cache: dict[str, dict] | None = None


def _slots() -> list[str]:
    try:
        from bu_profiles import DEFAULT_SLOTS
        return list(DEFAULT_SLOTS)
    except Exception:
        return list(_FALLBACK_SLOTS)


def _pack_dir() -> pathlib.Path:
    from runtime_paths import data_subdir
    return data_subdir("stakeholder_packs")


def invalidate_cache() -> None:
    global _cache
    _cache = None


def _load_all() -> dict[str, dict]:
    global _cache
    if _cache is not None:
        return _cache
    packs: dict[str, dict] = {}
    try:
        for path in sorted(_pack_dir().glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue  # a corrupt pack must not take the whole list down
            pid = data.get("pack_id") or path.stem
            data["pack_id"] = pid
            packs[pid] = data
    except OSError:
        pass
    _cache = packs
    return packs


def list_packs() -> list[dict]:
    """Every pack, newest-labelled first. Safe for an unauthenticated-ish
    listing: contains no stakeholder content, only ids and labels."""
    return sorted(_load_all().values(), key=lambda p: (p.get("label") or p["pack_id"]).lower())


def _norm(pack_id: str) -> str:
    """Ids are case-insensitive. save_pack lowercases before writing, so every
    READ must lowercase too — otherwise saving "EMEA_2026" and asking for
    "EMEA_2026" returns nothing, and the cohort silently falls back to the
    default map. Caught by test_invalid_pack_ids_are_refused_not_raised."""
    return (pack_id or "").strip().lower()


def get_pack(pack_id: str) -> dict | None:
    pid = _norm(pack_id)
    if not pid:
        return None
    return _load_all().get(pid)


def save_pack(pack_id: str, label: str, region: str, bus: dict) -> bool:
    """Persist a pack. Returns False for an invalid id rather than raising, to
    match save_region_config's contract in stakeholder_db."""
    pid = _norm(pack_id)
    if not _PACK_ID_RE.match(pid):
        return False

    known = set(_slots())
    clean_bus = {
        str(slot): str(cfg).strip()
        for slot, cfg in (bus or {}).items()
        if str(slot) in known and str(cfg or "").strip()
    }

    payload = {
        "pack_id": pid,
        "label": (label or pid).strip(),
        "region": (region or "").strip(),
        "bus": clean_bus,
    }

    target = _pack_dir() / f"{pid}.json"
    try:
        # Atomic write: a half-written pack read by another worker mid-save
        # would look like a corrupt file and silently drop out of the list.
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
        with open(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1)
        pathlib.Path(tmp).replace(target)
    except OSError:
        return False

    invalidate_cache()
    return True


def delete_pack(pack_id: str) -> bool:
    pid = _norm(pack_id)
    if not _PACK_ID_RE.match(pid):
        return False
    try:
        (_pack_dir() / f"{pid}.json").unlink()
    except FileNotFoundError:
        return False
    except OSError:
        return False
    invalidate_cache()
    return True


def config_id_for_bu(pack_id: str, bu_id: str) -> str | None:
    """The stakeholder-config id this pack assigns to `bu_id`, or None.

    None is the signal to fall through to the pre-existing resolution chain —
    never a reason to show a player an empty stakeholder map.
    """
    pack = get_pack(pack_id)   # normalises the id
    if not pack:
        return None
    return (pack.get("bus") or {}).get(str(bu_id)) or None


def pack_coverage(pack_id: str) -> dict:
    """Which slots a pack covers and which fall back. Surfaced in the admin UI
    so a half-configured pack is visible BEFORE a class, not during one."""
    pack = get_pack(pack_id)
    slots = _slots()
    if not pack:
        return {"pack_id": pack_id, "exists": False, "covered": [], "missing": slots}
    bus = pack.get("bus") or {}
    covered = [s for s in slots if bus.get(s)]
    return {
        "pack_id": pack.get("pack_id"),
        "label": pack.get("label"),
        "region": pack.get("region"),
        "exists": True,
        "covered": covered,
        "missing": [s for s in slots if not bus.get(s)],
        "complete": len(covered) == len(slots),
    }


def build_pack_from_region_workbook(
    pack_id: str,
    label: str,
    region: str,
    sheet_scopes: dict,
) -> dict:
    """Turn a parsed 4-sheet region workbook into configs + a pack.

    `sheet_scopes` maps sheet name -> list of stakeholder dicts, as returned by
    stakeholder_config_excel.import_master_workbook. A sheet is matched to a
    slot by name, case-insensitively, so "Pharma", "pharma" and
    "vertical_pharma__europe" all bind to the pharma slot.

    Returns a report: which slots bound, which config ids were written, and
    which sheets could not be matched — the operator needs to see an unmatched
    sheet, not have it silently ignored.
    """
    from stakeholder_db import save_region_config

    slots = _slots()
    region_slug = (region or "").strip().lower().replace(" ", "_")
    bus: dict = {}
    written: list[str] = []
    unmatched: list[str] = []

    for sheet_name, rows in (sheet_scopes or {}).items():
        key = str(sheet_name).strip().lower().replace(" ", "_")
        slot = next((s for s in slots if s == key or key.startswith(f"vertical_{s}") or s in key), None)
        if not slot or not rows:
            unmatched.append(str(sheet_name))
            continue
        config_id = f"vertical_{slot}__{region_slug}" if region_slug else f"vertical_{slot}"
        if save_region_config(config_id, rows):
            bus[slot] = config_id
            written.append(config_id)
        else:
            unmatched.append(str(sheet_name))

    ok = save_pack(pack_id, label, region_slug, bus)
    return {
        "saved": ok,
        "pack_id": _norm(pack_id),
        "region": region_slug,
        "bus": bus,
        "configs_written": written,
        "unmatched_sheets": unmatched,
        "missing_slots": [s for s in slots if s not in bus],
    }
