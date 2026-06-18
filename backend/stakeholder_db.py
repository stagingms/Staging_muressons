"""
Muressons Global Corporation — Stakeholder DB (Regional Localisation)
Provides region-specific stakeholder configuration loading and management.

Stakeholder configs are stored as JSON files in:
    db/stakeholder_configs/<region_id>.json

Each JSON file contains an array of stakeholder override objects.
A "partial override" only changes the fields specified — missing fields
fall back to the canonical STAKEHOLDERS in stakeholder_map.py.

Supported region_ids:
    asean, south_asia, europe, north_america, africa

If no override file exists for a region, the canonical data is returned
unchanged (graceful degradation).
"""

from __future__ import annotations

import copy
import json
import os
import pathlib
from typing import Any

# Absolute path to the stakeholder config directory
_CONFIG_DIR = pathlib.Path(__file__).resolve().parent.parent / "db" / "stakeholder_configs"

# In-memory cache:  region_id → list[dict]
_region_cache: dict[str, list[dict]] = {}

# Sentinel to avoid re-reading missing directories every request
_dir_exists: bool | None = None


def _ensure_config_dir() -> bool:
    """Create the config directory if it doesn't exist. Returns True on success."""
    global _dir_exists
    if _dir_exists is None:
        _dir_exists = _CONFIG_DIR.exists()
        if not _dir_exists:
            try:
                _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                _dir_exists = True
            except OSError:
                _dir_exists = False
    return bool(_dir_exists)


def _config_path(region_id: str) -> pathlib.Path:
    return _CONFIG_DIR / f"{region_id}.json"


def get_stakeholders_for_region(region_id: str) -> list[dict]:
    """Return the fully-merged stakeholder list for a region.

    Strategy:
      1. Load the canonical STAKEHOLDERS from stakeholder_map.
      2. If a region JSON file exists, apply each override entry on top:
         - Match by stakeholder ``id``.
         - Only the keys present in the override object are updated.
         - Extra entries (new stakeholders) in the JSON are appended.
      3. Return the result.

    The merged list is cached in-process for the lifetime of the server.
    """
    if region_id in _region_cache:
        return _region_cache[region_id]

    # Canonical baseline
    try:
        from stakeholder_map import STAKEHOLDERS as _canonical
        base: list[dict] = copy.deepcopy(_canonical)
    except ImportError:
        base = []

    if not region_id:
        return base

    cfg_path = _config_path(region_id)
    if not cfg_path.exists():
        # No override — canonical data applies for this region
        _region_cache[region_id] = base
        return base

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            overrides: list[dict] = json.load(f)
    except Exception as exc:
        print(f"[stakeholder_db] Failed to load {cfg_path}: {exc}")
        _region_cache[region_id] = base
        return base

    # Apply overrides
    base_index: dict[str, int] = {s["id"]: i for i, s in enumerate(base)}
    for override in overrides:
        s_id = override.get("id")
        if not s_id:
            continue
        if s_id in base_index:
            # Partial merge — only update specified keys
            base[base_index[s_id]].update(override)
        else:
            # New stakeholder unique to this region
            base.append(copy.deepcopy(override))

    _region_cache[region_id] = base
    return base


def invalidate_cache(region_id: str | None = None) -> None:
    """Invalidate the in-process stakeholder cache.

    Call after writing a new/updated region config file so the next
    request picks up the latest data.
    """
    if region_id is None:
        _region_cache.clear()
    else:
        _region_cache.pop(region_id, None)


# ─────────────────────────────────────────────────────────────────
# Admin API helpers
# ─────────────────────────────────────────────────────────────────

def list_region_configs() -> list[str]:
    """Return the region_ids for which a config file exists."""
    if not _ensure_config_dir():
        return []
    return [
        p.stem
        for p in sorted(_CONFIG_DIR.glob("*.json"))
    ]


def get_region_config_raw(region_id: str) -> list[dict] | None:
    """Return the raw override list for a region, or None if not found."""
    cfg_path = _config_path(region_id)
    if not cfg_path.exists():
        return None
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_region_config(region_id: str, overrides: list[dict]) -> bool:
    """Persist a region stakeholder override list to disk.

    Validates that ``region_id`` is a non-empty slug (alphanumeric + underscore).
    Returns True on success, False on failure.
    """
    import re
    if not re.match(r"^[a-z0-9_]{1,50}$", region_id):
        return False
    _ensure_config_dir()
    cfg_path = _config_path(region_id)
    tmp_path = cfg_path.with_suffix(".json.tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(overrides, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, cfg_path)
        invalidate_cache(region_id)
        return True
    except Exception as exc:
        print(f"[stakeholder_db] Failed to save {cfg_path}: {exc}")
        return False


def delete_region_config(region_id: str) -> bool:
    """Delete a region override file. Returns True if deleted, False if not found."""
    cfg_path = _config_path(region_id)
    if not cfg_path.exists():
        return False
    try:
        cfg_path.unlink()
        invalidate_cache(region_id)
        return True
    except Exception:
        return False
