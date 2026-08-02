"""
C5 drift tripwire -- backend and frontend ROLE_HIERARCHY must stay identical.

ROLE_HIERARCHY is declared twice: backend admin_shared.py (authoritative,
enforcement) and frontend app/config/sidebarConfig.js (tab filtering). A silent
drift breaks role-based tab visibility and, worse, hides the fact that a level
change on one side didn't reach the other. This test parses the frontend source
and asserts an exact match, the same pattern the repo uses for the shockwave
catalog tripwire.
"""

import re
import pathlib

from admin_shared import ROLE_HIERARCHY as BACKEND_ROLE_HIERARCHY

_SIDEBAR = (
    pathlib.Path(__file__).resolve().parents[2]
    / "frontend" / "app" / "config" / "sidebarConfig.js"
)


def _parse_frontend_role_hierarchy() -> dict:
    text = _SIDEBAR.read_text(encoding="utf-8")
    m = re.search(r"const ROLE_HIERARCHY\s*=\s*\{(.*?)\}\s*;", text, re.S)
    assert m, f"ROLE_HIERARCHY object not found in {_SIDEBAR}"
    pairs = {}
    for line in m.group(1).splitlines():
        line = line.split("//", 1)[0]  # strip JS line comments
        mm = re.search(r"(\w+)\s*:\s*(\d+)", line)
        if mm:
            pairs[mm.group(1)] = int(mm.group(2))
    return pairs


def test_frontend_role_hierarchy_matches_backend():
    frontend = _parse_frontend_role_hierarchy()
    backend = dict(BACKEND_ROLE_HIERARCHY)
    assert frontend == backend, (
        "ROLE_HIERARCHY drift between backend and frontend!\n"
        f"  backend  (admin_shared.py):   {backend}\n"
        f"  frontend (sidebarConfig.js):  {frontend}\n"
        "Update BOTH in the same commit."
    )


def test_role_hierarchy_ordering_invariants():
    """The guarantees the guards rely on, expressed as ordering invariants."""
    h = dict(BACKEND_ROLE_HIERARCHY)
    assert h["god_mode"] > h["super_admin"], "god_mode must outrank super_admin (C6)"
    assert h["super_admin"] == h["admin"], "admin is an alias of super_admin"
    assert h["super_admin"] > h["lead_facilitator"] > h["facilitator"], "run ladder order"
    assert h["project_admin"] < h["facilitator"], "project_admin is off the run ladder (C4)"
    assert h["project_admin"] < h["lead_facilitator"], (
        "project_admin must never satisfy require_lead_facilitator"
    )
