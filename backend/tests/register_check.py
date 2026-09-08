"""Re-execute the claims register mechanically — the triage instrument for
docs/verification/register_reexec.md.

Not a test. The register is a verification document whose 99 rows each cite
`backend/file.py:LINE` and quote the code they were traced against; Phases 0-5
moved a great deal of that code. This decides, per citation, whether the quoted
fragment is still where the register says it is, has merely moved, or is gone and
the row needs a human. Phase 5 used it to scope what the cut-over left open
(register_reexec.md, "PHASE 5 RE-EXECUTION").

    python3 tests/register_check.py             # summary + every non-EXACT row
    python3 tests/register_check.py --human     # only the rows needing a re-read
    python3 tests/register_check.py --moves     # unambiguous line moves, for review
    python3 tests/register_check.py --versioned # rows whose cited code is rule-gated

It over-reports by design: the register sometimes quotes a config path, a bare
number or a shell command inside backticks, none of which is Python source, and
those land in --human. A false positive costs a re-read; a false negative would
leave a stale claim in a document people print from.

For every `backend/file.py:LINE` citation the register makes, and every code
fragment it quotes against that citation, decide one of:

    EXACT   the fragment is still at the cited line(s)
    MOVED   the fragment is still in the file, at a different line
    HUMAN   the fragment is no longer findable — the row needs re-reading

Matching is against a whitespace-normalised view of the whole file, so a
statement the register joined onto one line still matches when the source spans
several. `...` in a quote is treated as an elision and matched as a gap.
"""
import re, sys, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
REG = ROOT / "docs" / "verification" / "register_reexec.md"
CITE = re.compile(r"backend/([A-Za-z0-9_/]+\.py):(\d+)(?:-(\d+))?")
FRAG = re.compile(r"`([^`]+)`")
_cache: dict[str, tuple[str, list[int]]] = {}


def normalised(f):
    """(one whitespace-collapsed string for the file, char-offset -> line no)."""
    if f not in _cache:
        p = ROOT / "backend" / f
        if not p.exists():
            _cache[f] = ("", [])
        else:
            buf, idx = [], []
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                t = " ".join(line.split())
                if not t:
                    continue
                buf.append(t)
                idx.extend([n] * (len(t) + 1))
            _cache[f] = (" ".join(buf) + " ", idx)
    return _cache[f]


def locate(f, frag):
    """Every line number where the (possibly elided) fragment starts."""
    src, idx = normalised(f)
    if not src:
        return None
    frag = " ".join(frag.split())
    parts = [p for p in (x.strip() for x in frag.split("...")) if p]
    if not parts:
        return []
    hits, start = [], 0
    while True:
        i = src.find(parts[0], start)
        if i < 0:
            break
        j, ok = i + len(parts[0]), True
        for p in parts[1:]:
            k = src.find(p, j)
            # an elision may not jump more than ~400 normalised chars
            if k < 0 or k - j > 400:
                ok = False
                break
            j = k + len(p)
        if ok:
            hits.append(idx[i])
        start = i + 1
    return sorted(set(hits))


# The register grows re-execution appendices below this marker. They cite code
# too, but they are not rows of the register being triaged — checking them would
# double-count and would report this instrument's own output back to itself.
_APPENDIX_MARKER = "\n# PHASE 5 RE-EXECUTION"

# A quoted fragment has to be distinctive enough to locate. A bare number or a
# two-character operator matches somewhere in every file, so it would report a
# spurious MOVED; the register's real code quotes are all far longer.
_MIN_FRAGMENT = 8


# ── which rows describe a mechanic that is now version-dependent ──────────
#
# Phase 5 first found these by searching the register's CLAIM TEXT for the names
# of the switched mechanics, and the register says in as many words that such a
# sweep will miss any row describing an affected mechanic without naming it.
# This closes that gap: it searches on CODE LOCATION, which wording cannot evade.
#
# The subtlety is that a register citation's LINE NUMBER is stamped against
# 0ad1246 and much of it has drifted, so the number in the document cannot be
# tested against today's function spans. Each quoted fragment is resolved to its
# CURRENT line first — the same `locate` the rest of this tool uses — and that
# resolved line is what gets tested.
#
# Two tiers, because two of the fifteen rule-gated reads sit inside very large
# functions (engine._run_reporting_layer is ~680 lines) and "cited somewhere in
# that function" is not evidence of anything.
_NARROW_FUNCTION = 140          # lines; above this, fall back to proximity
_PROXIMITY = 40                 # lines either side of the gated read itself


def versioned_reads():
    """Every rule_on / rule_value call in the backend, with its enclosing
    function's span: (file, line, kind, switch, func, start, end)."""
    import ast as _ast
    out, skip = [], ("tests", "__pycache__", "manual_tests", "archive")
    for path in sorted((ROOT / "backend").rglob("*.py")):
        if any(part in path.parts for part in skip):
            continue
        try:
            tree = _ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        rel = str(path.relative_to(ROOT / "backend"))
        funcs = [(n.lineno, getattr(n, "end_lineno", n.lineno), n.name)
                 for n in _ast.walk(tree)
                 if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef))]
        for n in _ast.walk(tree):
            if (isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name)
                    and n.func.id in ("rule_on", "rule_value") and len(n.args) > 1):
                try:
                    name = _ast.literal_eval(n.args[1])
                except Exception:
                    name = _ast.unparse(n.args[1])
                a, b, fn = min(((x, y, z) for x, y, z in funcs if x <= n.lineno <= y),
                               key=lambda t: t[1] - t[0],
                               default=(n.lineno, n.lineno, "<module>"))
                out.append((rel, n.lineno, n.func.id, name, fn, a, b))
    return out


def cmd_versioned():
    reads = versioned_reads()
    text = REG.read_text(encoding="utf-8")
    if _APPENDIX_MARKER in text:
        text = text.split(_APPENDIX_MARKER, 1)[0]
    rows = re.split(r"\n(?=## )", text)[1:]

    flagged = {}
    for row in rows:
        name = row.split("\n", 1)[0][3:].strip()
        ev = next((l for l in row.splitlines() if l.startswith("EVIDENCE:")), "")
        if not ev:
            continue
        cites = list(CITE.finditer(ev))
        for i, m in enumerate(cites):
            f = m.group(1)
            seg = ev[m.end(): cites[i + 1].start() if i + 1 < len(cites) else len(ev)]
            for frag in FRAG.findall(seg):
                if len(frag.strip()) < _MIN_FRAGMENT or not any(c.isalpha() for c in frag):
                    continue
                for line in (locate(f, frag) or []):
                    for rf, rl, _kind, sw, fn, a, b in reads:
                        if rf != f:
                            continue
                        narrow = (b - a) <= _NARROW_FUNCTION
                        if (a <= line <= b) if narrow else (abs(line - rl) <= _PROXIMITY):
                            flagged.setdefault(name, set()).add(
                                (sw, f"{f}:{fn}()", "in-function" if narrow else "proximity"))
    print(f"{len(reads)} rule-gated reads; {len(flagged)} of {len(rows)} register rows "
          f"cite code inside one\n")
    for name in sorted(flagged):
        print(name)
        for sw, where, how in sorted(flagged[name]):
            print(f"    {sw:38s} {where:50s} [{how}]")


def main():
    text = REG.read_text(encoding="utf-8")
    if _APPENDIX_MARKER in text:
        text = text.split(_APPENDIX_MARKER, 1)[0]
    rows = re.split(r"\n(?=## )", text)[1:]
    tally = collections.Counter()
    detail = []
    moves = []                      # (file, cited_line, new_line) for re-stamping
    for row in rows:
        name = row.split("\n", 1)[0][3:].strip()
        ev = next((l for l in row.splitlines() if l.startswith("EVIDENCE:")), "")
        if not ev:
            tally["no EVIDENCE line"] += 1
            detail.append((name, "NO-EVIDENCE", []))
            continue
        cites = list(CITE.finditer(ev))
        problems, worst = [], "EXACT"
        for i, m in enumerate(cites):
            f, lo = m.group(1), int(m.group(2))
            hi = int(m.group(3)) if m.group(3) else lo
            seg = ev[m.end(): cites[i + 1].start() if i + 1 < len(cites) else len(ev)]
            for frag in FRAG.findall(seg):
                if len(frag.strip()) < _MIN_FRAGMENT or not any(c.isalpha() for c in frag):
                    continue
                hits = locate(f, frag)
                if hits is None:
                    problems.append(("FILE-GONE", f, lo, frag[:50], []))
                    worst = "HUMAN"
                elif not hits:
                    problems.append(("HUMAN", f, lo, frag[:50], []))
                    worst = "HUMAN"
                elif not any(lo <= h <= hi for h in hits):
                    problems.append(("MOVED", f, lo, frag[:40], hits))
                    if worst == "EXACT":
                        worst = "MOVED"
                    if len(hits) == 1:
                        moves.append((f, lo, hits[0]))
        tally[worst] += 1
        if worst != "EXACT":
            detail.append((name, worst, problems))

    print("rows:", len(rows), dict(tally))
    if "--moves" in sys.argv:
        agg = collections.Counter(moves)
        print("\nunambiguous line moves (file, cited, actual) x count:")
        for (f, lo, hi), n in sorted(agg.items()):
            print(f"   {f}:{lo} -> {hi}   x{n}")
        return
    for name, kind, problems in detail:
        if "--human" in sys.argv and kind != "HUMAN":
            continue
        print(f"\n{name}  [{kind}]")
        for k, f, lo, frag, hits in problems:
            if "--human" in sys.argv and k not in ("HUMAN", "FILE-GONE"):
                continue
            print(f"    {k:9s} {f}:{lo}  {frag}" + (f"  -> {hits}" if hits else ""))


if "--versioned" in sys.argv:
    cmd_versioned()
else:
    main()
