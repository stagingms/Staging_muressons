#!/usr/bin/env python3
"""Patch exactly the launch-blocker keys in the data-volume simulation_config.json.

Surgical: every other key in the file is left byte-for-byte alone.
Usage:  python3 patch_volume_config.py [--dry-run] [/path/to/simulation_config.json]
Default path: $MURESSONS_DATA_DIR/simulation_config.json  (falls back to /data).

Lives under backend/ (audit 2026-09-04 F-07) because the Docker image copies
backend/, db/ and simulation_config.json only — a script under scripts/ cannot
be run inside the Railway container. From the Railway CLI:

    railway ssh -- python3 /app/backend/patch_volume_config.py --dry-run
    railway ssh -- python3 /app/backend/patch_volume_config.py
    (then Restart the service and confirm the deploy log has no "[CONFIG] WARNING")

The eleven keys are the ones a volume seeded before 2026-09-03 may still carry
at their legacy values: the original seven, plus the four slo_ramp tiers that the
2026-09-03 calibration commits (b1e7345 / cfc07fe / 278365d) moved and moved
back — config.py accepts any ordered set of tiers silently, so a volume written
by one of the intermediate builds would otherwise govern forever.
"""
import json, os, shutil, sys, datetime

args = [a for a in sys.argv[1:] if a != "--dry-run"]
DRY = "--dry-run" in sys.argv
PATH = args[0] if args else os.path.join(
    os.environ.get("MURESSONS_DATA_DIR", "/data"), "simulation_config.json")

PATCH = [
    (["engine_parameters", "cbam", "surcharge_rate"],              100),
    (["engine_parameters", "imitation_decay", "default_rate"],     0.05),
    (["engine_parameters", "regulatory_ratchet", "baseline"],      20.0),
    (["engine_parameters", "synergy", "max_reduction_per_round"],  0.06),
    (["ncd_parameters", "hard_cap"],                               5000),
    (["ncd_parameters", "warn_threshold"],                         1000),
    (["ncd_parameters", "opex_penalty_per_unit"],                  1000),
    # slo_ramp: the shipped natural-decay tiers (278365d) — see config.py NATURAL_DECAY_*
    (["engine_parameters", "slo_ramp", "no_decay_ratio"],          0.15),
    (["engine_parameters", "slo_ramp", "mid_ratio"],               0.2),
    (["engine_parameters", "slo_ramp", "growth_ratio"],            0.3),
    (["engine_parameters", "slo_ramp", "min_abs_capex"],           100000),
]

print(f"file: {PATH}")
with open(PATH, encoding="utf-8") as f:
    cfg = json.load(f)            # malformed JSON fails here, before any write

changed = False
for path, value in PATCH:
    node = cfg
    for seg in path[:-1]:
        node = node.setdefault(seg, {})
    before = node.get(path[-1], "<absent>")
    if before != value:
        changed = True
    node[path[-1]] = value
    flag = "  " if before == value else "->"
    print(f"  {'.'.join(path):<48} {before!r:>12}  {flag}  {value!r}")

if DRY:
    print("dry run - nothing written")
    sys.exit(0)
if not changed:
    print("already correct - nothing written")
    sys.exit(0)

backup = f"{PATH}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
shutil.copy2(PATH, backup)
print(f"backup: {backup}")

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("written")
