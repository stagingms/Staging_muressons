#!/usr/bin/env python3
"""
revert.py — Muressons Simulation Refactor-by-Isolation Revert Script
=====================================================================
Run this script from the project root to restore ALL archived files
from /temp_archive back to their original paths.

Usage:
    python revert.py [--dry-run]

Options:
    --dry-run   Show what would be restored without actually moving files.
"""

import os
import sys
import shutil

PROJECT_ROOT  = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_ROOT  = os.path.join(PROJECT_ROOT, "temp_archive")
MANIFEST_FILE = os.path.join(PROJECT_ROOT, "SAFETY_MANIFEST.txt")

DRY_RUN = "--dry-run" in sys.argv

def parse_manifest():
    """Parse SAFETY_MANIFEST.txt and return list of (original_path, archive_path) pairs."""
    if not os.path.exists(MANIFEST_FILE):
        print(f"[ERROR] SAFETY_MANIFEST.txt not found at: {MANIFEST_FILE}")
        sys.exit(1)

    entries = []
    current_original = None
    current_archived = None

    with open(MANIFEST_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            if "ORIGINAL :" in line:
                rel = line.split("ORIGINAL :", 1)[1].strip()
                current_original = os.path.join(PROJECT_ROOT, rel)
            elif "ARCHIVED :" in line:
                rel = line.split("ARCHIVED :", 1)[1].strip()
                current_archived = os.path.join(PROJECT_ROOT, rel)

            if current_original and current_archived:
                entries.append((current_original, current_archived))
                current_original = None
                current_archived = None

    return entries


def main():
    if not os.path.isdir(ARCHIVE_ROOT):
        print(f"[ERROR] Archive directory not found: {ARCHIVE_ROOT}")
        print("        Nothing to revert.")
        sys.exit(1)

    entries = parse_manifest()
    if not entries:
        print("[ERROR] No entries found in SAFETY_MANIFEST.txt. Cannot revert.")
        sys.exit(1)

    prefix = "[DRY RUN] " if DRY_RUN else ""
    print(f"{prefix}Muressons Revert Script")
    print(f"{prefix}Restoring {len(entries)} files from temp_archive/")
    print("=" * 70)

    restored = 0
    skipped  = 0
    errors   = 0

    for original_path, archived_path in entries:
        filename = os.path.basename(original_path)
        orig_dir = os.path.dirname(original_path)

        if not os.path.exists(archived_path):
            print(f"  [SKIP] {filename}")
            print(f"         Archive source not found: {archived_path}")
            skipped += 1
            continue

        if os.path.exists(original_path):
            print(f"  [SKIP] {filename}")
            print(f"         Already exists at original path.")
            skipped += 1
            continue

        if DRY_RUN:
            print(f"  [WOULD RESTORE] {filename}")
            print(f"    from: {archived_path}")
            print(f"      to: {original_path}")
            restored += 1
            continue

        try:
            os.makedirs(orig_dir, exist_ok=True)
        except Exception as e:
            print(f"  [ERROR] {filename} - could not create directory: {e}")
            errors += 1
            continue

        try:
            shutil.move(archived_path, original_path)
            print(f"  [OK] {filename}")
            restored += 1
        except Exception as e:
            print(f"  [ERROR] {filename} - {e}")
            errors += 1

    print("=" * 70)
    if DRY_RUN:
        print(f"DRY RUN complete. {restored} files would be restored, {skipped} skipped.")
    else:
        print(f"Revert complete: {restored} restored | {skipped} skipped | {errors} errors")
        if errors == 0 and restored > 0:
            print("\nAll files restored successfully.")
            print("You may now delete /temp_archive and SAFETY_MANIFEST.txt if desired.")
        elif errors > 0:
            print(f"\n[WARNING] {errors} file(s) could not be restored. See errors above.")


if __name__ == "__main__":
    main()
