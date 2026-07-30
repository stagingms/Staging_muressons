"""Stakeholder Configurator — master file (all verticals & regions).

BUG-2026-07-30. The "Master file" tab showed "Template download failed". The
whole mode was frontend-only: it called three endpoints that did not exist —
/stakeholder-config/bulk-template, /bulk-preview and /bulk-upload. Single-scope
worked because /download/{config_id} is real, which is why only half the panel
appeared broken.

A second, quieter defect was found while testing these: the first cut of
_collect_all_scopes() exported stakeholder_map.STAKEHOLDERS for "canonical"
unconditionally. On a real install whose canonical set had been customised
(an India-pharma roster), downloading the master file and re-applying it would
have silently replaced that customisation with the shipped defaults. A template
must round-trip as identity, so saved overrides now win over built-ins.

ISOLATION NOTE — the reason this file monkeypatches _CONFIG_DIR:
stakeholder_db writes to <repo>/db/stakeholder_configs, a GIT-TRACKED
directory, and it does NOT honour MURESSONS_DATA_DIR. An ad-hoc script run
against the live app during this investigation overwrote all 13 real config
files (restored from git afterwards). Any test touching this module must
redirect the config dir first, or it edits the developer's actual data.
"""
import io
import json
import os
import pathlib
import tempfile

import pytest


@pytest.fixture
def isolated_configs(monkeypatch):
    """Point stakeholder_db at a throwaway dir and seed a CUSTOM canonical set,
    so 'saved overrides win' is actually exercised rather than assumed."""
    import stakeholder_db

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="skcfg_"))
    monkeypatch.setattr(stakeholder_db, "_CONFIG_DIR", tmp, raising=False)
    stakeholder_db.invalidate_cache()

    custom = [{
        "id": "custom_regulator",
        "name": "Custom Regulator",
        "correct_quadrant": "manage_closely",
        "urgency": 90,
        "legitimacy": 85,
        "description": "Seeded by the test — must survive a template round trip.",
        "intel_dossier": ["dossier one"],
        "engagement_tactics": [],
    }]
    (tmp / "canonical.json").write_text(json.dumps(custom), encoding="utf-8")
    stakeholder_db.invalidate_cache()
    yield tmp
    stakeholder_db.invalidate_cache()


@pytest.fixture
def client():
    d = tempfile.mkdtemp(prefix="skmaster_")
    os.environ["MURESSONS_DATA_DIR"] = d
    pathlib.Path(d, "memory_snapshot.json").write_text("{}", encoding="utf-8")
    pathlib.Path(d, "facilitators.json").write_text("[]", encoding="utf-8")
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        r = c.post("/api/admin/facilitators/login",
                   json={"facilitator_id": "god_mode", "password": "sim2026@iim"})
        assert r.status_code == 200, r.text
        yield c


def _xlsx(content: bytes):
    return {"file": ("master.xlsx", io.BytesIO(content),
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}


# ── the reported bug ────────────────────────────────────────────────────────

def test_master_template_downloads(client, isolated_configs):
    """The exact failure: this 404'd, and the UI showed 'Template download
    failed'."""
    r = client.get("/api/admin/stakeholder-config/bulk-template")
    assert r.status_code == 200, r.text
    assert r.content[:2] == b"PK", "not a real .xlsx (zip) payload"
    assert len(r.content) > 5000
    assert "stakeholder_master_all_scopes.xlsx" in r.headers.get("content-disposition", "")


def test_master_template_requires_authentication(client, isolated_configs):
    from fastapi.testclient import TestClient
    from main import app
    anon = TestClient(app, raise_server_exceptions=False)
    assert anon.get("/api/admin/stakeholder-config/bulk-template").status_code == 401


def test_single_scope_download_still_works(client, isolated_configs):
    """The half that was never broken must stay unbroken."""
    r = client.get("/api/admin/stakeholder-config/download/canonical")
    assert r.status_code == 200
    assert r.content[:2] == b"PK"


# ── the quiet data-loss defect ──────────────────────────────────────────────

def test_template_exports_the_saved_canonical_not_the_builtin(client, isolated_configs):
    """A customised canonical set must appear in the master file. Exporting the
    Python defaults here is what would overwrite the customisation on re-apply."""
    from stakeholder_config_excel import import_master_workbook

    r = client.get("/api/admin/stakeholder-config/bulk-template")
    tmp = pathlib.Path(tempfile.mkdtemp()) / "m.xlsx"
    tmp.write_bytes(r.content)
    parsed = import_master_workbook(tmp)

    assert "canonical" in parsed
    ids = [s["id"] for s in parsed["canonical"]]
    assert ids == ["custom_regulator"], (
        f"canonical exported as {ids} — the built-in defaults, not the saved "
        "override. Re-applying this template would destroy the customisation."
    )


def test_download_then_apply_is_identity(client, isolated_configs):
    """The round trip must not change anything — the property that makes a
    template safe to hand to a facilitator."""
    tpl = client.get("/api/admin/stakeholder-config/bulk-template")
    pv = client.post("/api/admin/stakeholder-config/bulk-preview", files=_xlsx(tpl.content))
    assert pv.status_code == 200, pv.text
    canonical = next(s for s in pv.json()["scopes"] if s["config_id"] == "canonical")
    assert canonical["new_overrides"] == [], "re-applying its own template invented rows"
    assert canonical["reverting_to_canonical"] == [], "re-applying its own template dropped rows"
    assert canonical["replaced_overrides"] == ["custom_regulator"]


# ── preview / apply contract the UI renders ─────────────────────────────────

def test_preview_returns_the_shape_the_ui_renders(client, isolated_configs):
    tpl = client.get("/api/admin/stakeholder-config/bulk-template")
    r = client.post("/api/admin/stakeholder-config/bulk-preview", files=_xlsx(tpl.content))
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body.get("scope_count"), int) and body["scope_count"] > 0
    for sc in body["scopes"]:
        for key in ("config_id", "scope_kind", "is_new_config", "existing_overrides",
                    "incoming_overrides", "new_overrides", "replaced_overrides",
                    "reverting_to_canonical"):
            assert key in sc, f"preview row missing {key} — the UI reads it"


def test_preview_writes_nothing(client, isolated_configs):
    """It is called on file-drop, before the operator has agreed to anything."""
    before = sorted(p.name for p in isolated_configs.glob("*.json"))
    tpl = client.get("/api/admin/stakeholder-config/bulk-template")
    client.post("/api/admin/stakeholder-config/bulk-preview", files=_xlsx(tpl.content))
    after = sorted(p.name for p in isolated_configs.glob("*.json"))
    assert before == after, "preview mutated the config directory"


def test_apply_writes_every_scope(client, isolated_configs):
    tpl = client.get("/api/admin/stakeholder-config/bulk-template")
    r = client.post("/api/admin/stakeholder-config/bulk-upload", files=_xlsx(tpl.content))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["scope_count"] >= 1
    assert body["total_stakeholders"] >= 1
    assert "canonical" in body["scopes"]


def test_apply_requires_super_admin(client, isolated_configs):
    from fastapi.testclient import TestClient
    from main import app
    anon = TestClient(app, raise_server_exceptions=False)
    tpl = client.get("/api/admin/stakeholder-config/bulk-template")
    r = anon.post("/api/admin/stakeholder-config/bulk-upload", files=_xlsx(tpl.content))
    assert r.status_code in (401, 403)


def test_garbage_upload_is_a_clean_400(client, isolated_configs):
    r = client.post("/api/admin/stakeholder-config/bulk-preview",
                    files={"file": ("x.xlsx", io.BytesIO(b"not a workbook"), "application/octet-stream")})
    assert r.status_code in (400, 422), f"expected a handled rejection, got {r.status_code}"


# ── the single-sheet layout the UI also promises ────────────────────────────

def test_single_sheet_with_vertical_and_region_columns(client, isolated_configs):
    """'Either add Vertical and Region columns to a single sheet, or give each
    scope its own sheet' — the UI says both work, so both must."""
    from openpyxl import Workbook
    from stakeholder_config_excel import COLUMNS

    wb = Workbook()
    ws = wb.active
    ws.title = "All"
    ws.append(list(COLUMNS) + ["Vertical", "Region"])
    row = ["reg1", "Regulator", "", "manage_closely", "", 90, 80, "d", "u", "a",
           "dossier", "", "", "", "", ""]
    ws.append(row + ["pharma", "europe"])
    ws.append(["ngo1", "NGO", "", "keep_informed", "", 60, 70, "d", "u", "a",
               "", "", "", "", "", ""] + ["", "south_asia"])
    tmp = pathlib.Path(tempfile.mkdtemp()) / "single.xlsx"
    wb.save(tmp)

    r = client.post("/api/admin/stakeholder-config/bulk-preview",
                    files=_xlsx(tmp.read_bytes()))
    assert r.status_code == 200, r.text
    ids = {s["config_id"] for s in r.json()["scopes"]}
    assert "vertical_pharma__europe" in ids
    assert "south_asia" in ids


def test_long_config_ids_survive_the_31_char_sheet_limit(isolated_configs):
    """Excel caps sheet names at 31 chars; several real ids are longer
    (vertical_banking_financial_services__north_america is 49). The Scopes
    index carries the true id so nothing is truncated on the way back."""
    from stakeholder_config_excel import export_master_workbook, import_master_workbook

    long_a = "vertical_banking_financial_services__north_america"
    long_b = "vertical_banking_financial_services__south_asia"
    scopes = {
        long_a: [{"id": "a1", "name": "A", "intel_dossier": [], "engagement_tactics": []}],
        long_b: [{"id": "b1", "name": "B", "intel_dossier": [], "engagement_tactics": []}],
    }
    tmp = pathlib.Path(tempfile.mkdtemp()) / "long.xlsx"
    written = export_master_workbook(scopes, tmp)
    assert all(len(sheet) <= 31 for sheet in written.values())

    back = import_master_workbook(tmp)
    assert set(back) == {long_a, long_b}, f"ids mangled by the sheet-name limit: {set(back)}"
    assert [s["id"] for s in back[long_a]] == ["a1"]
