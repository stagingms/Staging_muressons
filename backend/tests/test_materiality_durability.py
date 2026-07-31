"""Materiality matrix edits must survive a redeploy.

DURABILITY-2026-07-31. materiality_db kept its JSON in backend/db — a SECOND
in-image location, separate from <repo>/db, and never routed through
runtime_paths. On Railway the container filesystem is ephemeral, so every edit
an admin made to a materiality matrix was lost on the next deploy.

It failed in two different ways depending on the file, and the first is the
nastier one:

  * materiality_config.json and materiality_config_<bu>.json SHIP in git (31
    files). An edit therefore did not vanish — it silently REVERTED to the
    shipped version. It saves, it reads back correctly, and days later a
    deploy quietly restores the original with nothing in any log. From the
    admin's chair that reads as "the edit didn't stick", with no way to tell
    whether they mis-clicked.
  * bu_registry.json is NOT tracked, so a newly registered BU disappeared
    outright.

Reproduced before the fix: writing "ADMIN EDITED THIS" into the pharma matrix
read back correctly in-process and was gone after a fresh checkout.

WHY LOCAL BEHAVIOUR IS DELIBERATELY UNCHANGED
An earlier cut migrated unconditionally, which on a developer machine created
<repo>/db/materiality_configs and left the 31 tracked files in backend/db
stale and shadowed by untracked copies. Off Railway there is no bug to fix —
backend/db is as durable as the host disk — so migration happens only when a
volume is actually configured. test_local_path_is_unchanged pins that, because
the "fix" quietly splitting a developer's config set would be its own defect.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

import pytest

BACKEND = pathlib.Path(__file__).resolve().parents[1]


def test_local_path_is_unchanged_when_no_volume_is_configured(monkeypatch):
    """No MURESSONS_DATA_DIR → backend/db, exactly as before. No migration, no
    second directory, no shadowing of the tracked seed files."""
    monkeypatch.delenv("MURESSONS_DATA_DIR", raising=False)
    import materiality_db
    assert materiality_db._resolve_config_dir() == materiality_db._SEED_DIR


def test_volume_path_is_used_when_one_is_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("MURESSONS_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("MURESSONS_NO_LEGACY_MIGRATION", raising=False)
    import materiality_db
    resolved = materiality_db._resolve_config_dir()
    assert resolved == tmp_path / "materiality_configs"
    assert resolved != materiality_db._SEED_DIR


def test_existing_configs_migrate_onto_the_volume(monkeypatch, tmp_path):
    """The migration must find backend/db explicitly. Without the `legacy`
    argument it would look under <repo>/db, find nothing, and the volume would
    start EMPTY — resetting every matrix to defaults, which is the very
    failure this change exists to prevent."""
    monkeypatch.setenv("MURESSONS_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("MURESSONS_NO_LEGACY_MIGRATION", raising=False)
    import materiality_db
    resolved = materiality_db._resolve_config_dir()
    migrated = list(resolved.glob("*.json"))
    assert migrated, "volume started empty — every matrix would reset to defaults"
    names = {p.name for p in migrated}
    assert "materiality_config.json" in names
    assert any(n.startswith("materiality_config_") for n in names)


def test_an_edit_survives_a_redeploy(tmp_path):
    """The headline. Two independent processes against one volume: the second
    stands in for a fresh container after a deploy.

    Before the fix the second process read the git-shipped file and the edit
    was silently gone.
    """
    env = dict(os.environ)
    env["MURESSONS_DATA_DIR"] = str(tmp_path)
    env.pop("MURESSONS_NO_LEGACY_MIGRATION", None)

    write = (
        "import sys; sys.path.insert(0, %r)\n"
        "import materiality_db as m\n"
        "cfg = m.get_bu_config('pharma')\n"
        "issues = cfg.get('issues') or cfg.get('material_issues') or []\n"
        "assert issues, 'pharma config has no issues to edit'\n"
        "issues[0]['name'] = 'ADMIN EDITED THIS'\n"
        "m.save_bu_config('pharma', cfg)\n"
        "print('WROTE')\n"
    ) % str(BACKEND)
    out = subprocess.run([sys.executable, "-c", write], capture_output=True,
                         text=True, env=env, timeout=90)
    assert "WROTE" in out.stdout, f"could not write the edit: {out.stderr[-500:]}"

    read = (
        "import sys; sys.path.insert(0, %r)\n"
        "import materiality_db as m\n"
        "cfg = m.get_bu_config('pharma')\n"
        "issues = cfg.get('issues') or cfg.get('material_issues') or []\n"
        "print(issues[0].get('name') if issues else 'NONE')\n"
    ) % str(BACKEND)
    out2 = subprocess.run([sys.executable, "-c", read], capture_output=True,
                          text=True, env=env, timeout=90)
    assert "ADMIN EDITED THIS" in out2.stdout, (
        "the edit did not survive a fresh process — a redeploy would silently "
        f"revert the matrix to the shipped version. Got: {out2.stdout!r}"
    )


def test_bu_registry_also_lands_on_the_volume(monkeypatch, tmp_path):
    """bu_registry.json is untracked, so it did not revert — it vanished, and
    with it every BU an admin had registered."""
    monkeypatch.setenv("MURESSONS_DATA_DIR", str(tmp_path))
    import importlib
    import materiality_db
    importlib.reload(materiality_db)
    assert str(materiality_db.BU_REGISTRY_FILE).startswith(str(tmp_path)), \
        f"registry still points into the image: {materiality_db.BU_REGISTRY_FILE}"


def test_seed_templates_stay_in_the_image(monkeypatch, tmp_path):
    """industry_configs/ and the master xlsx are read-only build artefacts
    referenced by no Python code. They must NOT be dragged onto the volume —
    runtime_paths' own doctrine is that seeds ship with the image."""
    monkeypatch.setenv("MURESSONS_DATA_DIR", str(tmp_path))
    import materiality_db
    resolved = materiality_db._resolve_config_dir()
    assert not (resolved / "industry_configs").exists()
    assert not list(resolved.glob("*.xlsx"))


def test_config_still_loads_after_the_change():
    """Whatever the path, the module must still serve a usable config — the
    change is a relocation, not a behaviour change."""
    import materiality_db
    cfg = materiality_db.get_bu_config("pharma")
    assert isinstance(cfg, dict) and cfg
    assert materiality_db.get_bu_ids(), "BU registry came back empty"
