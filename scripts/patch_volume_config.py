#!/usr/bin/env python3
"""Patch exactly the seven launch-blocker keys in simulation_config.json.

Surgical: every other key in the file is left byte-for-byte alone.
Usage:  python3 patch_volume_config.py [--dry-run] [/path/to/simulation_config.json]
Default path: $MURESSONS_DATA_DIR/simulation_config.json  (falls back to /data).
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
