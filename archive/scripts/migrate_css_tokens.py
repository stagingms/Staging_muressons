"""
scripts/migrate_css_tokens.py  (C1 — CSS token consolidation)
=============================================================
Replaces exact-value hardcoded hex colours in the frontend CSS modules with the
matching design token from globals.css. Only maps colours whose hex value is
IDENTICAL to a token, so the rendered output is unchanged — this is a safe,
mechanical consolidation, not a restyle.

WHY RUN THIS LOCALLY (not in the cowork sandbox):
The migration touches ~80 files. Run it on your own machine where the
filesystem is reliable, and review every change with `git diff` before
committing. `git` is your undo button.

USAGE (from project root):
    python scripts/migrate_css_tokens.py            # dry run — shows counts only
    python scripts/migrate_css_tokens.py --apply    # writes changes
    git diff                                        # review
    # happy?  git add -A && git commit -m "C1: tokenize exact-match CSS colours"
    # not happy?  git checkout -- frontend/app       # revert everything

Then tighten .stylelintrc.json rules from "warning" to "error" so raw hex
can't come back.
"""

from __future__ import annotations

import argparse
import glob
import os
import re

# Exact hex -> token. Only 1:1 value matches (verified against globals.css :root).
# Deliberately conservative: colours without an identical token are left alone.
MAPPING = {
    "#3b82f6": "var(--accent-blue)",
    "#06b6d4": "var(--accent-cyan)",
    "#8b5cf6": "var(--accent-purple)",
    "#f59e0b": "var(--accent-gold)",
    "#10b981": "var(--kpi-good)",
    "#ef4444": "var(--kpi-danger)",
    "#1e293b": "var(--bg-elevated)",
    "#f1f5f9": "var(--text-primary)",
}

# Directory holding the CSS modules (relative to project root).
CSS_GLOB = "frontend/app/components/*.module.css"
# Never touch the token definitions themselves.
SKIP = {"globals.css"}


def migrate(text: str) -> tuple[str, int]:
    """Return (new_text, replacements). Matches hex case-insensitively but only
    as a whole colour token (not inside a longer hex like #10b9813)."""
    count = 0
    for hex_val, token in MAPPING.items():
        # (?i) case-insensitive; (?![0-9a-fA-F]) so #10b981 doesn't match #10b9812
        pattern = re.compile(re.escape(hex_val) + r"(?![0-9a-fA-F])", re.IGNORECASE)
        text, n = pattern.subn(token, text)
        count += n
    return text, count


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry run).")
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = sorted(glob.glob(os.path.join(root, CSS_GLOB)))

    total_files, total_repl = 0, 0
    for path in files:
        if os.path.basename(path) in SKIP:
            continue
        with open(path, "r", encoding="utf-8") as fh:
            original = fh.read()
        migrated, n = migrate(original)
        if n == 0:
            continue
        total_files += 1
        total_repl += n
        rel = os.path.relpath(path, root)
        print(f"{'WROTE ' if args.apply else 'would change'} {rel}: {n} replacement(s)")
        if args.apply:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(migrated)

    verb = "Applied" if args.apply else "Dry run —"
    print(f"\n{verb} {total_repl} replacement(s) across {total_files} file(s).")
    if not args.apply and total_repl:
        print("Re-run with --apply to write, then review with: git diff")


if __name__ == "__main__":
    main()
