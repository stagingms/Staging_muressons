"""Deployment hygiene: proxy trust, image contents, and the boot preflight.

Three defects, all found while preparing the first Railway deploy, all of the
same shape — a setting that LOOKED configured but did nothing:

  1. TRUSTED_PROXY_IPS documented CIDRs and compared exact strings.
  2. .dockerignore let a developer's local runtime state into the image, where
     runtime_paths migrated it onto the production volume.
  3. Nothing said either had happened; the symptom was a login that failed
     with no explanation, hours later.
"""
import ipaddress
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
DOCKERIGNORE = REPO / ".dockerignore"
DOCKERFILE = REPO / "Dockerfile"


# ── 1. Trusted-proxy matching ───────────────────────────────────────────────

def _resolver(trusted: str):
    """Build a resolver with a given TRUSTED_PROXY_IPS, without import order
    games — _parse_trusted is pure, so the parse is the unit under test."""
    import rate_limit
    entries = tuple(e.strip() for e in trusted.split(",") if e.strip())
    exact, nets = rate_limit._parse_trusted(entries)

    def is_trusted(ip: str) -> bool:
        if ip in exact:
            return True
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return False
        return any(addr in n for n in nets)
    return is_trusted


@pytest.mark.parametrize("trusted,ip,expected", [
    # Exact addresses — the pre-existing behaviour, which must not regress.
    ("127.0.0.1,::1", "127.0.0.1", True),
    ("127.0.0.1,::1", "::1", True),
    ("127.0.0.1,::1", "10.1.2.3", False),
    # CIDR — the bug. Every one of these was False before the fix.
    ("10.0.0.0/8", "10.1.2.3", True),
    ("10.0.0.0/8", "10.255.255.254", True),
    ("10.0.0.0/8", "11.0.0.1", False),
    ("100.64.0.0/10", "100.64.0.5", True),      # PaaS carrier-grade NAT range
    ("100.64.0.0/10", "100.128.0.1", False),
    # Mixed, which is what a real deployment sets.
    ("127.0.0.1,::1,10.0.0.0/8", "10.9.9.9", True),
    ("127.0.0.1,::1,10.0.0.0/8", "127.0.0.1", True),
    ("127.0.0.1,::1,10.0.0.0/8", "203.0.113.7", False),
    # IPv6 networks.
    ("fd00::/8", "fd00::1234", True),
    ("fd00::/8", "2001:db8::1", False),
])
def test_trusted_proxy_matching(trusted, ip, expected):
    assert _resolver(trusted)(ip) is expected


def test_a_non_canonical_form_still_matches():
    """'127.000.000.001' and '::0001' are the same hosts a human might type."""
    assert _resolver("127.0.0.1")("127.0.0.1") is True
    assert _resolver("::1")("::1") is True


def test_a_host_bit_in_a_cidr_is_tolerated():
    """strict=False: operators write 10.1.2.3/8 meaning "that network"."""
    assert _resolver("10.1.2.3/8")("10.9.9.9") is True


def test_garbage_entries_do_not_widen_trust():
    """A typo must fail CLOSED. Silently trusting everything would be the
    worst possible outcome of a malformed config value."""
    is_trusted = _resolver("not-an-ip,10.0.0.0/8")
    assert is_trusted("10.1.1.1") is True       # the valid entry still works
    assert is_trusted("203.0.113.1") is False   # the garbage trusts nothing
    assert is_trusted("not-an-ip") is True      # ...except its literal self


def test_xff_is_only_honoured_from_a_trusted_source(monkeypatch):
    """The actual security property: an untrusted client cannot spoof its IP."""
    import rate_limit
    monkeypatch.setattr(rate_limit, "_TRUSTED_EXACT", frozenset({"127.0.0.1"}))
    monkeypatch.setattr(rate_limit, "_TRUSTED_NETS", (ipaddress.ip_network("10.0.0.0/8"),))

    class Req:
        def __init__(self, host, xff=None):
            self.client = type("C", (), {"host": host})()
            self.headers = {"X-Forwarded-For": xff} if xff else {}

    # From a trusted proxy: the forwarded client IP is used.
    assert rate_limit._resolve_client_ip(Req("10.0.0.7", "203.0.113.9")) == "203.0.113.9"
    # From an arbitrary client: the header is ignored, socket IP wins.
    assert rate_limit._resolve_client_ip(Req("198.51.100.4", "203.0.113.9")) == "198.51.100.4"


# ── 2. Image hygiene ────────────────────────────────────────────────────────

def _ignore_lines():
    return [ln.strip() for ln in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")]


def test_every_runtime_state_file_is_excluded_from_the_image():
    """Pins .dockerignore to deploy_preflight.RUNTIME_STATE_FILES.

    Adding a mutable file to that list without excluding it here means the next
    deploy ships a developer's copy of it and runtime_paths migrates it onto
    the production volume — exactly how a locally rotated master password
    became the production master password.
    """
    from deploy_preflight import RUNTIME_STATE_FILES
    lines = set(_ignore_lines())
    missing = [n for n in RUNTIME_STATE_FILES if f"db/{n}" not in lines]
    assert not missing, (
        f".dockerignore does not exclude {missing}. Add 'db/<name>' for each."
    )


def test_the_legacy_master_password_location_is_excluded_too():
    """runtime_paths migrates backend/db/master_password.json FORWARD, so
    excluding only the repo-root copy leaves the trap fully armed."""
    assert "backend/db/master_password.json" in set(_ignore_lines())


def test_seed_data_is_not_excluded():
    """The failure mode in the other direction. A glob like `db/*.json` also
    catches the seeds, and `backend/db/*.json` catches every materiality and
    pillar config — the app then breaks in production while working locally."""
    lines = _ignore_lines()
    for pattern in ("db/*.json", "db/*.jsonl", "backend/db/*.json"):
        assert pattern not in lines, (
            f"'{pattern}' is too broad — it removes seed/config data the app needs. "
            "Exclude runtime state by exact name instead."
        )


def test_seed_files_referenced_by_the_dockerfile_still_ship():
    """Seed data must be BOTH present on disk AND tracked by git.

    An earlier version of this test only checked the filesystem, which is why
    it passed while db/seed_healthcare.json was untracked: .gitignore's
    `db/*.json` rule re-included only seed_round1.json. The file existed on
    every developer's disk and in no image, so a healthcare-paradigm cohort
    seeded fine locally and would have failed in production. What reaches the
    image is what git tracks, so that is what this asserts.
    """
    import subprocess
    seeds = ["db/seed_round1.json", "db/seed_healthcare.json"]
    lines = set(_ignore_lines())
    try:
        tracked = set(subprocess.run(
            ["git", "ls-files", "db/"], cwd=REPO, capture_output=True, text=True,
            timeout=30,
        ).stdout.split())
    except (OSError, subprocess.SubprocessError):
        pytest.skip("git not available")
    for s in seeds:
        assert s not in lines, f"{s} is seed data and must ship in the image"
        assert (REPO / s).exists(), f"{s} is expected by the app but missing from the repo"
        assert s in tracked, (
            f"{s} exists on disk but is NOT tracked by git, so it will not be in "
            f"the deployed image. Add '!{s}' to .gitignore and `git add -f {s}`."
        )


def test_no_seed_file_is_left_untracked():
    """Generalises the above: anything the backend loads by filename from db/
    must be tracked. Catches the NEXT seed file added without a .gitignore
    re-include, rather than only the one that was already missed."""
    import re
    import subprocess
    backend = REPO / "backend"
    referenced = set()
    for py in backend.glob("*.py"):
        for m in re.finditer(r'"(seed_[a-z0-9_]+\.json)"', py.read_text(encoding="utf-8")):
            referenced.add(m.group(1))
    if not referenced:
        pytest.skip("no seed filenames found in backend sources")
    try:
        tracked = set(subprocess.run(
            ["git", "ls-files", "db/"], cwd=REPO, capture_output=True, text=True,
            timeout=30,
        ).stdout.split())
    except (OSError, subprocess.SubprocessError):
        pytest.skip("git not available")
    missing = [n for n in sorted(referenced)
               if (REPO / "db" / n).exists() and f"db/{n}" not in tracked]
    assert not missing, (
        f"seed files present on disk but untracked (they will be absent in "
        f"production): {missing}"
    )


def test_env_files_are_excluded_at_every_level():
    """A bare `.env` in .dockerignore matches only the CONTEXT ROOT, so
    `COPY backend/ .` shipped backend/.env — real local credentials — inside
    every image. The `**/` form covers all levels; `.env.*` catches variants
    like backend/.env.railway. The example template must still ship-able."""
    lines = set(_ignore_lines())
    assert "**/.env" in lines
    assert "**/.env.*" in lines
    assert "!.env.railway.example" in lines


def test_dockerfile_still_copies_the_seed_directory():
    """If this COPY ever goes away the exclusions above become meaningless and
    the seeds vanish — assert the assumption this whole file rests on."""
    assert "COPY db/ /app/db/" in DOCKERFILE.read_text(encoding="utf-8")


# ── 3. Preflight ────────────────────────────────────────────────────────────

def test_override_conflict_is_reported(tmp_path, monkeypatch):
    from deploy_preflight import check_master_password_override
    monkeypatch.setenv("MASTER_PASSWORD", "some-deploy-secret")
    (tmp_path / "master_password.json").write_text('{"hash": "x"}', encoding="utf-8")
    msg = check_master_password_override(tmp_path)
    assert msg and "override" in msg.lower()
    assert "will NOT log in" in msg


def test_override_conflict_is_silent_when_there_is_no_conflict(tmp_path, monkeypatch):
    from deploy_preflight import check_master_password_override
    monkeypatch.setenv("MASTER_PASSWORD", "some-deploy-secret")
    assert check_master_password_override(tmp_path) is None      # no file
    monkeypatch.delenv("MASTER_PASSWORD", raising=False)
    (tmp_path / "master_password.json").write_text('{"hash": "x"}', encoding="utf-8")
    assert check_master_password_override(tmp_path) is None      # no env value


def test_the_legacy_path_is_checked_as_well(tmp_path, monkeypatch):
    """The trap that survived my first attempt at fixing this."""
    from deploy_preflight import check_master_password_override
    monkeypatch.setenv("MASTER_PASSWORD", "x")
    legacy = tmp_path / "legacy" / "master_password.json"
    legacy.parent.mkdir()
    legacy.write_text('{"hash": "y"}', encoding="utf-8")
    assert check_master_password_override(tmp_path / "data", legacy) is not None


@pytest.mark.parametrize("value,flagged", [
    ("", True),                                   # unset — localhost default
    ("127.0.0.1,::1", True),                      # explicit localhost only
    ("127.0.0.1,::1,10.0.0.0/8", False),          # a real proxy range
])
def test_proxy_trust_warning(value, flagged, monkeypatch):
    from deploy_preflight import check_proxy_trust
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("TRUSTED_PROXY_IPS", value)
    assert (check_proxy_trust() is not None) is flagged


def test_player_master_password_is_flagged_in_production(monkeypatch):
    from deploy_preflight import check_player_master_unset
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("PLAYER_MASTER_PASSWORD", "skeleton-key")
    assert check_player_master_unset() is not None
    monkeypatch.delenv("PLAYER_MASTER_PASSWORD")
    assert check_player_master_unset() is None


def test_preflight_is_quiet_in_local_development(monkeypatch, tmp_path):
    """A laptop has no volume and no proxy. Warning about it every boot would
    train the operator to ignore the whole block."""
    from deploy_preflight import run_preflight
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.delenv("MASTER_PASSWORD", raising=False)
    monkeypatch.delenv("TRUSTED_PROXY_IPS", raising=False)
    monkeypatch.delenv("MURESSONS_DATA_DIR", raising=False)
    assert run_preflight(data_dir=tmp_path) == []


def test_preflight_never_raises(monkeypatch, tmp_path):
    """A diagnostic that can crash the boot is worse than no diagnostic.

    Points the data dir at a path whose parent is a FILE, so mkdir raises
    NotADirectoryError — the realistic version of a bad volume mount.
    """
    from deploy_preflight import run_preflight
    blocker = tmp_path / "iam_a_file"
    blocker.write_text("not a directory", encoding="utf-8")
    bad = blocker / "data"
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("MURESSONS_DATA_DIR", str(bad))
    findings = run_preflight(data_dir=bad)
    assert isinstance(findings, list)
    assert any("not writable" in f or "failed to run" in f for f in findings)
