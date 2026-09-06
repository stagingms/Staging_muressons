"""Boot-time migration of KNOWN superseded values on the data-volume
simulation_config.json (CFG-10, 2026-09-06).

WHY THIS EXISTS
    runtime_paths.config_file() seeds the volume copy once from the image and
    the volume wins from then on — the right contract for a tunable file. Its
    failure mode is a volume seeded by an INTERMEDIATE build: it carries that
    build's transient values forever, and config.py accepts them silently.
    Production's volume was seeded on 2026-09-03 while the JSON briefly said
    slo_ramp 0.10 / 0.25 / 0.50 + $500k (reverted the same day, 278365d) and
    shares_outstanding 100,000,000 (rescaled by WP-15). WP-20 made /health
    and /config/live name the drift; the remedy was a shell step in the
    runbook (patch_volume_config.py) — skipped after the Wave 1 deploy and
    found still live after the Wave 2 deploy.

WHAT IT DOES
    Before config.py reads the file, each row below is checked: if the volume
    holds EXACTLY one of the row's superseded values, it is rewritten to the
    row's current value — atomically, announced on stdout as
    `[config] MIGRATED <key>: <old> -> <new>` and recorded in CONFIG_MIGRATIONS
    for /health. A value that is neither superseded nor current is a
    deliberate tuning and is left alone: config_introspect keeps reporting it
    as image_vs_volume, which is the owner's signal, not ours to override.

WHAT IT NEVER DOES
    Touch a key that is absent (config.py's default applies), touch the
    in-image copy, raise (a failure is announced and the boot continues on
    the file as it is), or run twice on the same value — a migrated value
    equals the current value, so the row is a no-op afterwards.

The table is the single source patch_volume_config.py also applies, so the
manual and the automatic paths cannot disagree.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

# (dotted key, superseded values the shipped JSON once carried, current value)
MIGRATIONS: list[tuple[tuple[str, ...], tuple, object]] = [
    # launch audit 2026-09-02 (ad8ccf6): the pre-launch economy
    (("engine_parameters", "cbam", "surcharge_rate"),              (100000, 100000.0),          100),
    (("engine_parameters", "imitation_decay", "default_rate"),     (0.1,),                      0.05),
    (("engine_parameters", "regulatory_ratchet", "baseline"),      (10, 10.0),                  20.0),
    (("ncd_parameters", "hard_cap"),                               (1000000, 1000000.0),        5000),
    (("ncd_parameters", "warn_threshold"),                         (500000, 500000.0),          1000),
    # natural-decay tiers: the 2026-09-03 move (b1e7345 / cfc07fe) and its
    # same-day revert (278365d) — see config.py NATURAL_DECAY_*
    (("engine_parameters", "slo_ramp", "no_decay_ratio"),          (0.1,),                      0.15),
    (("engine_parameters", "slo_ramp", "mid_ratio"),               (0.25,),                     0.2),
    (("engine_parameters", "slo_ramp", "growth_ratio"),            (0.5, 0.4),                  0.3),
    (("engine_parameters", "slo_ramp", "min_abs_capex"),           (500000, 500000.0),          100000),
    # F-20 / WP-15 (c2e1059): the reveal's share-price scale
    (("terminal_valuation", "shares_outstanding"),                 (100000000, 100000000.0),    6500000),
]


def _walk(cfg: dict, path: tuple[str, ...]):
    node = cfg
    for seg in path[:-1]:
        if not isinstance(node, dict) or seg not in node:
            return None, None
        node = node[seg]
    if not isinstance(node, dict) or path[-1] not in node:
        return None, None
    return node, node[path[-1]]


def _superseded(value, olds: tuple) -> bool:
    if isinstance(value, bool):
        return False
    for old in olds:
        if isinstance(old, bool):
            continue
        if type(value) is type(old) and value == old:
            return True
        if isinstance(value, (int, float)) and isinstance(old, (int, float)) and float(value) == float(old):
            return True
    return False


def plan_migrations(cfg: dict) -> list[dict]:
    """Rows whose value on `cfg` is a known superseded value. Pure."""
    plan = []
    for path, olds, new in MIGRATIONS:
        node, value = _walk(cfg, path)
        if node is None:
            continue                      # absent → config.py default; not ours
        if _superseded(value, olds) and value != new:
            plan.append({"key": ".".join(path), "old": value, "new": new, "_path": path})
    return plan


def apply_known_migrations(config_path: "Path | str | None") -> list[dict]:
    """Rewrite known superseded values on the volume file in place.

    Returns the list of migrations applied ([{key, old, new}]); an empty list
    when nothing was superseded, the file is absent, unreadable, or not
    writable. Never raises."""
    applied: list[dict] = []
    if not config_path:
        return applied
    path = Path(config_path)
    try:
        if not path.exists():
            return applied
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if not isinstance(cfg, dict):
            return applied
        plan = plan_migrations(cfg)
        if not plan:
            return applied
        for row in plan:
            node, _ = _walk(cfg, row["_path"])
            node[row["_path"][-1]] = row["new"]
        tmp = path.with_name(path.name + ".migrating")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
        for row in plan:
            applied.append({"key": row["key"], "old": row["old"], "new": row["new"]})
            print(f"[config] MIGRATED {row['key']}: {row['old']!r} -> {row['new']!r} "
                  "(a superseded value the volume was seeded with; config_migrations.py)")
    except Exception as exc:  # the boot continues on the file as it is
        print(f"[config] migration skipped for {config_path}: {type(exc).__name__}: {exc}")
    return applied
