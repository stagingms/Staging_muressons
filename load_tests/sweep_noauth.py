"""No-credential route sweep (audit G04; Wave 0's acc/sweep_noauth.py rebuilt
inside the repo so it can be re-run at every gate).

Walks every route the FastAPI app registers, calls each with NO credential
(path parameters filled with a syntactically valid dummy id — a random UUID,
a round number, a plausible slug), and reports which answered 200. The
number is compared with a baseline listing when one is given, so the gate
question is "did this wave open anything that was closed?"

Usage (memory store, no server needed):
  cd backend && python ../load_tests/sweep_noauth.py --out ../SWEEP_after.json
  python ../load_tests/sweep_noauth.py --baseline ../SWEEP_before.json --out ../SWEEP_after.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))
os.chdir(_BACKEND)
os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("JWT_SECRET", "sweep-secret-not-for-production-0123456789")
os.environ.setdefault("MURESSONS_DATA_DIR", str(Path(os.environ.get("TMPDIR", "/tmp")) / f"sweep_{uuid.uuid4().hex[:8]}"))
os.environ.setdefault("MURESSONS_NO_LEGACY_MIGRATION", "1")
os.environ.pop("MASTER_PASSWORD", None)

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402

_DUMMY = {
    "session_id": str(uuid.uuid4()), "cohort_id": str(uuid.uuid4()), "player_id": "MUR-0000",
    "facilitator_id": "FAC-000", "round_number": "3", "round": "3", "notebook_id": "nb-1",
    "bu_id": "pharma", "vertical": "pharma", "event_id": "cyber_attack", "template_id": "t1",
    "resource_id": "r1", "message_id": "m1", "room_id": "room1", "track_id": "brsr_ngrbc",
    "scenario_id": "orderly_1_5", "file_name": "x.json", "filename": "x.json", "key": "k",
    "industry": "pharma", "paradigm": "legacy_abc", "tier": "advanced", "path": "x",
}


def _fill(path: str) -> str:
    def rep(m):
        name = m.group(1).split(":")[0]
        return _DUMMY.get(name, "x")
    return re.sub(r"\{([^}]+)\}", rep, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default=None)
    ap.add_argument("--out", default="SWEEP_result.json")
    a = ap.parse_args()
    rows = []

    def _flatten(routes, prefix=""):
        """FastAPI ≥ 0.120 keeps included routers as _IncludedRouter entries
        whose routes live on .original_router; older versions flatten them."""
        for r in routes:
            orig = getattr(r, "original_router", None)
            if orig is not None:
                yield from _flatten(orig.routes, prefix + (getattr(r, "include_context", None) and getattr(r.include_context, "prefix", "") or ""))
                continue
            sub = getattr(r, "routes", None)
            if sub is not None and getattr(r, "path", None) is not None and not getattr(r, "methods", None):
                yield from _flatten(sub, prefix + r.path)
                continue
            yield r, prefix

    with TestClient(app) as c:
        for r, prefix in _flatten(app.routes):
            methods = sorted(getattr(r, "methods", None) or [])
            path = getattr(r, "path", None)
            if path is not None and prefix and not path.startswith(prefix):
                path = prefix + path
            if not path or not methods:
                continue
            for m in methods:
                if m in ("HEAD", "OPTIONS"):
                    continue
                url = _fill(path)
                try:
                    if m == "GET":
                        res = c.get(url)
                    elif m == "POST":
                        res = c.post(url, json={})
                    elif m == "PUT":
                        res = c.put(url, json={})
                    elif m == "PATCH":
                        res = c.patch(url, json={})
                    elif m == "DELETE":
                        res = c.delete(url)
                    else:
                        continue
                    rows.append({"method": m, "path": path, "status": res.status_code, "bytes": len(res.content)})
                except Exception as exc:  # noqa: BLE001
                    rows.append({"method": m, "path": path, "status": -1, "error": str(exc)[:120]})
    open_200 = sorted(f"{r['method']} {r['path']}" for r in rows if r["status"] == 200)
    result = {"routes": len(rows), "open_200": open_200, "open_200_count": len(open_200),
              "by_status": {}, "rows": rows}
    for r in rows:
        result["by_status"][str(r["status"])] = result["by_status"].get(str(r["status"]), 0) + 1
    if a.baseline:
        base = json.load(open(a.baseline, encoding="utf-8"))
        before = set(base.get("open_200", []))
        result["newly_open"] = sorted(set(open_200) - before)
        result["newly_closed"] = sorted(before - set(open_200))
    json.dump(result, open(a.out, "w", encoding="utf-8"), indent=2)
    print(json.dumps({k: v for k, v in result.items() if k not in ("rows", "open_200")}, indent=2))
    if a.baseline:
        print("newly open:", result["newly_open"])
        print("newly closed:", result["newly_closed"])
        sys.exit(1 if result["newly_open"] else 0)


if __name__ == "__main__":
    main()
