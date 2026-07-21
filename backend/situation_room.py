"""
situation_room.py — W-D (W4): Situation-Room bulletin assembly.

Builds a ~15-second market-news broadcast script from a cohort's REAL
state: the biggest EBITDA mover, live crisis flags, and the Nordhaven
NPC competitor print. Pure function of its inputs — no randomness, no
I/O, no state writes — so the same cohort state always produces the
same script (shared-dice determinism doctrine).
"""

from __future__ import annotations

CRISIS_PATTERNS = (
    "crisis", "black_swan", "strike", "scandal", "breach",
    "recall", "shockwave", "cyclone", "greenwashing",
)


def _m(v: float | None) -> str:
    return f"${(v or 0) / 1_000_000:.1f} million"


def _pretty_flag(flag: str) -> str:
    return str(flag).replace("_", " ")


def assemble_bulletin_text(teams: list[dict], round_number: int) -> str:
    """Assemble the broadcast script.

    teams: [{ "name": str, "ebitda": float, "prev_ebitda": float | None,
              "flags": [str], "competitor_ebitda": float }]
    Returns roughly 50-80 words of anchor copy.
    """
    lines = [f"This is Muressons Global News at the close of round {round_number}."]

    movers = [t for t in teams if t.get("prev_ebitda") not in (None, 0)]
    if movers:
        best = max(movers, key=lambda t: (t.get("ebitda") or 0) - (t.get("prev_ebitda") or 0))
        delta = (best.get("ebitda") or 0) - (best.get("prev_ebitda") or 0)
        verb = "climbing" if delta >= 0 else "sliding"
        lines.append(
            f"{best.get('name', 'A team')} leads the tape, EBITDA {verb} {_m(abs(delta))} to {_m(best.get('ebitda'))}."
        )
    elif teams:
        top = max(teams, key=lambda t: t.get("ebitda") or 0)
        lines.append(f"{top.get('name', 'A team')} tops the board at {_m(top.get('ebitda'))} EBITDA.")

    crisis_hits: list[tuple[str, str]] = []
    for t in teams:
        for f in t.get("flags") or []:
            if any(p in str(f).lower() for p in CRISIS_PATTERNS):
                crisis_hits.append((t.get("name", "A team"), _pretty_flag(f)))
    if crisis_hits:
        name, flag = crisis_hits[0]
        extra = f", one of {len(crisis_hits)} live alerts on the board" if len(crisis_hits) > 1 else ""
        lines.append(f"On the risk desk: {name} is managing a {flag}{extra}.")
    else:
        lines.append("The risk desk is quiet. No live crises on the board.")

    comp = [t for t in teams if (t.get("competitor_ebitda") or 0) > 0]
    if comp:
        avg = sum(t["competitor_ebitda"] for t in comp) / len(comp)
        lines.append(f"Rival Nordhaven Group keeps grinding forward, printing {_m(avg)} EBITDA this period.")

    lines.append("Back to the boardroom. Decisions close soon.")
    return " ".join(lines)
