"""Config importer, template and hot reload — audit 2026-09-04 CFG-04/05/06/08/09 · WP-25.

CFG-04  The shipped simulation_config.xlsx was stale (191 rows vs 208
        parameters) and the importer REBUILT the JSON from the sheet, so
        uploading the template deleted 17 keys and reverted one value. The
        template is regenerated from the JSON and pinned value-identical; the
        importer merges (keys absent from the sheet keep their value).
CFG-06  Negatives, out-of-range rates, bool typos, fractional ints and unknown
        keys were written silently. They are refused, every row listed,
        nothing written.
CFG-05  router / dry_run bound DEFAULT_IMITATION_DECAY_RATE (and the CSF pool
        constants) at import, so the Excel hot reload left the commit path on
        the old value while the response said "reload: complete".
CFG-08  The overrun tunables were literals in admin_shared; the JSON keys
        reached nothing.
CFG-09  The provenance sidecar named five keys the JSON does not have.
"""
from __future__ import annotations

import copy
import importlib
import inspect
import json
import os
import sys
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ROOT = _BACKEND_DIR.parent
sys.path.insert(0, str(_BACKEND_DIR))
os.environ.setdefault("USE_MEMORY_DB", "true")

openpyxl = pytest.importorskip("openpyxl")

import config_excel as ce  # noqa: E402

JSON = _ROOT / "simulation_config.json"
XLSX = _ROOT / "simulation_config.xlsx"


def _public_leaves(d):
    return {k: v for k, v in ce._leaves(d).items() if not any(p.startswith("_") for p in k.split("."))}


# ── CFG-04: template in sync, round trip identical, merge not replace ───────

def test_committed_template_matches_the_committed_json():
    values, problems = ce.read_excel_values(XLSX)
    assert problems == []
    assert values == _public_leaves(json.loads(JSON.read_text(encoding="utf-8"))), (
        "simulation_config.xlsx has drifted from simulation_config.json — regenerate it: "
        "cd backend && python3 -c \"import config_excel as c; from pathlib import Path; "
        "c.export_to_excel(Path('../simulation_config.json'), Path('../simulation_config.xlsx'))\""
    )


def test_export_import_round_trip_is_value_identical(tmp_path):
    xlsx = tmp_path / "rt.xlsx"
    ce.export_to_excel(JSON, xlsx)
    target = tmp_path / "sim.json"
    target.write_text(JSON.read_text(encoding="utf-8"), encoding="utf-8")
    summary = ce.import_from_excel(xlsx, target)
    assert summary["changed"] == {}
    assert summary["preserved"] == []
    assert json.loads(target.read_text(encoding="utf-8")) == json.loads(JSON.read_text(encoding="utf-8"))


def _sheet_with(tmp_path, edits: dict[str, object], drop: set[str] = frozenset(), extra_rows=()):
    """The committed sheet with some rows edited / dropped / appended."""
    wb = openpyxl.load_workbook(str(XLSX))
    ws = wb.active
    rows_to_delete = []
    for row in ws.iter_rows(min_row=2):
        sec, sub, par, val, typ = (c.value for c in row[:5])
        if par is None:
            continue
        section_key = sec
        for json_key, label in ce._SECTION_LABELS.items():
            clean = label.lstrip("📋📈🚧💰🌿🌡️📊🔗💥⚙️🌪️🧮🏦🦢🔄 ")
            if sec == clean or sec == label:
                section_key = json_key
        dotted = ".".join(p for p in (section_key, sub or "", par) if p)
        if dotted in edits:
            row[3].value = edits[dotted]
        if dotted in drop:
            rows_to_delete.append(row[0].row)
    for r in sorted(rows_to_delete, reverse=True):
        ws.delete_rows(r)
    for cells in extra_rows:
        ws.append(list(cells))
    out = tmp_path / "edited.xlsx"
    wb.save(str(out))
    return out


def test_a_key_missing_from_the_sheet_keeps_its_value(tmp_path):
    """The 17-key deletion, in miniature."""
    xlsx = _sheet_with(tmp_path, {}, drop={"engine_parameters.slo_ramp.min_abs_capex",
                                          "terminal_valuation.exit_multiple_ceiling"})
    target = tmp_path / "sim.json"
    target.write_text(JSON.read_text(encoding="utf-8"), encoding="utf-8")
    summary = ce.import_from_excel(xlsx, target)
    assert set(summary["preserved"]) == {"engine_parameters.slo_ramp.min_abs_capex",
                                         "terminal_valuation.exit_multiple_ceiling"}
    after = json.loads(target.read_text(encoding="utf-8"))
    before = json.loads(JSON.read_text(encoding="utf-8"))
    assert after["engine_parameters"]["slo_ramp"]["min_abs_capex"] == before["engine_parameters"]["slo_ramp"]["min_abs_capex"]
    assert after["terminal_valuation"]["exit_multiple_ceiling"] == before["terminal_valuation"]["exit_multiple_ceiling"]
    assert after == before


def test_an_edited_value_lands_and_is_reported(tmp_path):
    xlsx = _sheet_with(tmp_path, {"financial_parameters.corporate_tax_rate": 0.30})
    target = tmp_path / "sim.json"
    target.write_text(JSON.read_text(encoding="utf-8"), encoding="utf-8")
    summary = ce.import_from_excel(xlsx, target)
    assert summary["changed"] == {"financial_parameters.corporate_tax_rate": (0.25, 0.30)}
    assert json.loads(target.read_text(encoding="utf-8"))["financial_parameters"]["corporate_tax_rate"] == 0.30


# ── CFG-06: refused, listed, nothing written ────────────────────────────────

@pytest.mark.parametrize("edits,extra,fragment", [
    ({"financial_parameters.corporate_tax_rate": -0.25}, (), "negative"),
    ({"financial_parameters.corporate_tax_rate": 5.0}, (), "[0, 1]"),
    ({"engine_parameters.eu_taxonomy.green_threshold_pct": 160}, (), "[0, 100]"),
    ({"simulation_settings.rounds": 1.7}, (), "not an integer"),
    ({"engine_parameters.black_swans.enabled": "Ture"}, (), "not a boolean"),
    ({}, (("Engine Parameters", "black_swans", "made_up_key", 42, "int"),), "not a parameter the engine reads"),
])
def test_malformed_sheets_are_refused_and_nothing_is_written(tmp_path, edits, extra, fragment):
    # a bool row must exist for the typo case — find one
    if edits and list(edits)[0] == "engine_parameters.black_swans.enabled":
        leaves = _public_leaves(json.loads(JSON.read_text(encoding="utf-8")))
        bool_key = next(k for k, v in leaves.items() if isinstance(v, bool))
        edits = {bool_key: "Ture"}
    xlsx = _sheet_with(tmp_path, edits, extra_rows=extra)
    target = tmp_path / "sim.json"
    original = JSON.read_text(encoding="utf-8")
    target.write_text(original, encoding="utf-8")
    with pytest.raises(ce.ConfigImportError) as exc:
        ce.import_from_excel(xlsx, target)
    msg = str(exc.value)
    assert fragment in msg, msg
    assert "nothing was written" in msg
    assert "row " in msg or "refused" in msg
    assert target.read_text(encoding="utf-8") == original


def test_legitimately_negative_keys_are_allowed(tmp_path):
    xlsx = _sheet_with(tmp_path, {"financial_parameters.treasury_floor": -400_000_000})
    target = tmp_path / "sim.json"
    target.write_text(JSON.read_text(encoding="utf-8"), encoding="utf-8")
    summary = ce.import_from_excel(xlsx, target)
    assert summary["changed"] == {"financial_parameters.treasury_floor": (-500_000_000, -400_000_000)}


def test_the_shipped_config_breaks_no_range_rule():
    leaves = _public_leaves(json.loads(JSON.read_text(encoding="utf-8")))
    broken = {k: ce._range_violation(k, v) for k, v in leaves.items() if ce._range_violation(k, v)}
    assert broken == {}, broken


# ── CFG-05: call-time reads survive a reload ────────────────────────────────

def test_router_and_dry_run_read_the_decay_and_csf_constants_at_call_time():
    import router, dry_run
    for mod in (router, dry_run):
        src = inspect.getsource(mod)
        assert "from config import" not in src or not any(
            name in line for line in src.splitlines() if line.startswith("from config import")
            for name in ("DEFAULT_IMITATION_DECAY_RATE", "CSF_POOL_TREASURY_FRACTION", "CSF_POOL_FLOOR")
        ), f"{mod.__name__} binds a hot-reloadable constant at import"
        assert "_cfg.DEFAULT_IMITATION_DECAY_RATE" in src


def test_a_reloaded_decay_rate_reaches_the_commit_path(monkeypatch):
    """The upload's hot reload rebinds config.DEFAULT_IMITATION_DECAY_RATE; the
    router must see the new value on the next commit without a restart."""
    import config, router
    monkeypatch.setattr(config, "DEFAULT_IMITATION_DECAY_RATE", 0.0777)
    assert router._cfg.DEFAULT_IMITATION_DECAY_RATE == 0.0777


# ── CFG-08: overrun tunables come from the JSON ─────────────────────────────

def test_overrun_tunables_are_seeded_from_config():
    import config, admin_shared
    assert admin_shared._god_mode_settings["overrun_probability"] == config.OVERRUN_DEFAULT_PROBABILITY
    assert admin_shared._god_mode_settings["overrun_severity"] == config.OVERRUN_DEFAULT_SEVERITY
    cfg = json.loads(JSON.read_text(encoding="utf-8"))["engine_parameters"]["overrun_risk"]
    assert config.OVERRUN_DEFAULT_PROBABILITY == cfg["default_probability"]
    assert config.OVERRUN_DEFAULT_SEVERITY == cfg["default_severity"]


# ── CFG-09: the provenance sidecar names real keys with the shipped values ──

def test_provenance_sidecar_is_in_sync():
    prov = json.loads((_ROOT / "simulation_config.provenance.json").read_text(encoding="utf-8"))
    leaves = ce._leaves(json.loads(JSON.read_text(encoding="utf-8")))
    for key, entry in prov["parameters"].items():
        assert key in leaves, f"provenance names a key the JSON does not have: {key}"
        if isinstance(entry.get("value"), (int, float)) and not isinstance(entry["value"], bool):
            assert leaves[key] == entry["value"], (key, leaves[key], entry["value"])
    assert "Parameter_Provenance.md" not in prov["_comment"]


# ── the upload endpoint refuses a bad sheet with 422 and keeps the file ─────

def test_upload_endpoint_refuses_a_bad_sheet(tmp_path, monkeypatch):
    import master_credentials
    monkeypatch.setattr(master_credentials, "MASTER_PASSWORD", "test-master-pw", raising=False)
    monkeypatch.setattr(master_credentials, "_load_override_hash", lambda: None, raising=False)
    from fastapi.testclient import TestClient
    from main import app
    import config as _config_mod
    client = TestClient(app)
    assert client.post("/api/admin/facilitators/login", json={"facilitator_id": "god_mode", "password": "test-master-pw"}).status_code == 200
    before = Path(_config_mod.CONFIG_PATH).read_text(encoding="utf-8")
    xlsx = _sheet_with(tmp_path, {"financial_parameters.corporate_tax_rate": -0.25})
    with open(xlsx, "rb") as fh:
        r = client.post("/api/admin/config/upload?reason=WP-25+test", files={"file": ("simulation_config.xlsx", fh,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 422, r.text[:300]
    assert "negative" in r.text
    assert Path(_config_mod.CONFIG_PATH).read_text(encoding="utf-8") == before
    # and the live sheet is downloadable with every key
    dl = client.get("/api/admin/config/excel")
    assert dl.status_code == 200
    out = tmp_path / "live.xlsx"
    out.write_bytes(dl.content)
    values, problems = ce.read_excel_values(out)
    assert problems == [] and len(values) == len(_public_leaves(_config_mod.SIMULATION_CONFIG))
