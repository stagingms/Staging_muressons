"""materiality_packs — named, reusable per-SBU double-materiality matrices.

WHAT A PACK IS
--------------
The same shape as stakeholder_packs, deliberately: a named index binding one
materiality matrix to each SBU slot for a single region.

    {"pack_id": "emea_2026",
     "label":   "EMEA 2026 (CSRD)",
     "region":  "europe",
     "bus": {"pharma": "pharma__europe", "electronics": "electronics__europe", ...}}

The values name a materiality config that materiality_db already stores, so a
pack owns NO matrix data. Packs can be created, renamed or deleted without
touching a matrix, and a matrix edited through the existing Excel flow is
instantly live in every pack referencing it.

HOW IT DIFFERS FROM STAKEHOLDER PACKS
-------------------------------------
Stakeholder packs point at stakeholder_db config ids and resolution returns a
LIST. Materiality configs are dicts (issues, interdependencies, consultant fee)
addressed as <bu> or <bu>__<region>, so config_for_bu returns the DICT itself.
Callers therefore never need to know whether a pack was involved.

WHY IT EXISTS
-------------
Before this, the only way to give a cohort a bespoke matrix was
PUT /{session_id}/materiality-dictionary, which writes a full dictionary INTO
that cohort's state. Every cohort needing the same setup got its own copy:
no reuse, no single place to correct an error, and no way to tell that two
cohorts were running the same configuration.

WHERE IT LIVES
--------------
On the durable volume via runtime_paths.data_subdir. materiality_db's own
configs used to sit in backend/db — inside the image — so an admin's edit
silently reverted to the shipped file on every redeploy. Packs must not repeat
that, and Phase 1 fixed the underlying store.
"""

from __future__ import annotations

import json
import pathlib
import re
import tempfile

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
    return data_subdir("materiality_packs")


def invalidate_cache() -> None:
    global _cache
    _cache = None


def _norm(pack_id: str) -> str:
    """Ids are case-insensitive. save_pack lowercases before writing, so every
    READ must lowercase too. The stakeholder version shipped with this
    asymmetry: "EMEA_2026" saved fine and then resolved to nothing, silently
    falling back to the default matrix with no error anywhere."""
    return (pack_id or "").strip().lower()


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
                continue  # one corrupt pack must not hide the rest
            pid = data.get("pack_id") or path.stem
            data["pack_id"] = pid
            packs[pid] = data
    except OSError:
        pass
    _cache = packs
    return packs


def list_packs() -> list[dict]:
    return sorted(_load_all().values(), key=lambda p: (p.get("label") or p["pack_id"]).lower())


def get_pack(pack_id: str) -> dict | None:
    pid = _norm(pack_id)
    return _load_all().get(pid) if pid else None


def save_pack(pack_id: str, label: str, region: str, bus: dict) -> bool:
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
        "region": (region or "").strip().lower(),
        "bus": clean_bus,
    }

    target = _pack_dir() / f"{pid}.json"
    try:
        # Atomic: a half-written pack read by another worker mid-save would
        # parse as corrupt and silently drop out of the list.
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
    except (FileNotFoundError, OSError):
        return False
    invalidate_cache()
    return True


def config_for_bu(pack_id: str, bu_id: str) -> dict | None:
    """The materiality DICT this pack assigns to `bu_id`, or None.

    None always means "fall through to the pre-existing chain" — never a
    reason to hand a class an empty matrix. That includes a pack naming a
    config that has since been deleted, which is why the loaded dict is
    checked for issues before being returned.
    """
    pack = get_pack(pack_id)
    if not pack:
        return None
    ref = (pack.get("bus") or {}).get(str(bu_id))
    if not ref:
        return None

    import materiality_db as mat_db

    # A reference is either "<bu>__<region>" or a plain "<bu>".
    if "__" in ref:
        bu_part, _, region_part = ref.partition("__")
        cfg = mat_db.get_regional_bu_config(bu_part, region_part)
        if cfg is not None:
            return cfg
        ref = bu_part  # regional file gone — try the plain BU matrix

    try:
        cfg = mat_db.get_bu_config(ref)
    except ValueError:
        return None  # unknown BU id in the pack
    return cfg if isinstance(cfg, dict) and cfg.get("issues") else None


def resolve_session_bu_config(global_state: dict, bu_id: str) -> dict:
    """The ONE materiality resolution chain for a session + BU.

    Order (highest wins):
      1. explicit per-BU cohort override (a sandbox edit made for one class
         must never be silently replaced by anything chosen later),
      2. the cohort's Materiality Pack entry for this BU,
      3. a region-specific matrix (materiality_config_<bu>__<region>),
      4. the plain BU/vertical matrix (resolve_bu_config).

    Extracted from router.submit_materiality_matrix (2026-07-31) so the
    DISPLAY endpoint can resolve identically: previously the player's matrix
    fetched the raw BU config while scoring resolved pack→region→BU, so a
    cohort with a pack or regional matrix could be SHOWN one dictionary and
    SCORED against another.
    """
    import materiality_db as mat_db

    override_key = f"materiality_dictionary_override_{bu_id}"
    if override_key in (global_state or {}):
        return global_state[override_key]

    flags = (global_state or {}).get("active_event_flags") or {}
    region = (global_state or {}).get("region_id") or flags.get("region_id") or ""
    pack_id = ((global_state or {}).get("materiality_pack_id")
               or flags.get("materiality_pack_id") or "")

    cfg = None
    if pack_id:
        try:
            cfg = config_for_bu(pack_id, bu_id)
        except Exception:
            cfg = None  # a broken pack never blocks a class
    if cfg is None:
        cfg = mat_db.resolve_bu_config(bu_id, region)
    return cfg


def pack_coverage(pack_id: str) -> dict:
    """Which slots a pack covers and which fall back — surfaced in the admin UI
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


def build_pack_from_region_workbook(pack_id: str, label: str, region: str,
                                    sheet_configs: dict) -> dict:
    """Turn a parsed 4-sheet region workbook into matrices + a pack.

    `sheet_configs` maps sheet name -> materiality config dict. Sheets bind to
    slots by name, case-insensitively. An unmatched sheet is REPORTED, not
    ignored: a silently skipped sheet is how a cohort reaches a classroom
    half-configured.
    """
    import materiality_db as mat_db

    slots = _slots()
    region_slug = (region or "").strip().lower().replace(" ", "_")
    bus: dict = {}
    written: list[str] = []
    unmatched: list[str] = []

    for sheet_name, cfg in (sheet_configs or {}).items():
        key = str(sheet_name).strip().lower().replace(" ", "_")
        slot = next((s for s in slots if s == key or key.startswith(s) or s in key), None)
        if not slot or not isinstance(cfg, dict) or not cfg.get("issues"):
            unmatched.append(str(sheet_name))
            continue
        if region_slug and mat_db.save_regional_bu_config(slot, region_slug, cfg):
            ref = f"{slot}__{region_slug}"
        else:
            try:
                mat_db.save_bu_config(slot, cfg)
                ref = slot
            except ValueError:
                unmatched.append(str(sheet_name))
                continue
        bus[slot] = ref
        written.append(ref)

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
