"""
llm_negotiator.py — Negotiation Rooms Phase 3: the dialogue layer.

SPEC_Stakeholder_Negotiation_Rooms §6. The LLM is an ACTOR, never an
authority:

  • Its entire influence is one JSON object: {dialogue, offer?, mood}.
  • `offer` may reference ONLY a concession id from the menu THIS agent
    actually has — and even then it is a *suggestion chip* rendered to the
    player, never an applied effect. Applying a concession still requires an
    explicit player POST to /negotiation/accept, which re-validates against
    the whitelist in negotiation.py. So the worst a prompt-injected or
    hallucinating model can do is say strange things and highlight a menu
    item the player could already click.
  • Any failure — no key, timeout, HTTP error, malformed JSON, unknown
    concession id, oversized payload — degrades to the Phase-1 scripted
    line. The room never breaks and never blocks.

Everything the model is told comes from engine truth assembled here
(persona, computed grievances, trust/scar history, the priced menu), so the
character cannot invent red lines, prices, or leverage it does not have.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

_log = logging.getLogger("muressons.negotiation")

# Hard bounds (SPEC §3 rule 5)
MAX_TOKENS = 500
TIMEOUT_S = 15
MAX_DIALOGUE_CHARS = 700
VALID_MOODS = ("softening", "neutral", "hardening")


def llm_available() -> bool:
    """True when a key is configured. Callers use scripted mode otherwise."""
    try:
        from config import LLM_API_KEY
        return bool(LLM_API_KEY)
    except Exception:
        return False


def build_prompt(room: dict, grievances: list[dict], menu: list[dict],
                 agent_state: dict, player_text: str, round_number: int) -> str:
    """Assemble the turn prompt from ENGINE TRUTH only."""
    p = room.get("persona", {})
    g_lines = []
    for g in grievances[:4]:
        want = "at or below" if g["direction"] == "above" else "at or above"
        status = "BREACHED" if g["breached"] else "within tolerance"
        g_lines.append(
            f"- {g['metric'].replace('_', ' ')}: currently {g['current']}, "
            f"your red line is {want} {g['red_line']} ({status})"
        )
    m_lines = [
        f"- id `{m['id']}` — {m['label']}: costs them ${m['cost']:,.0f}"
        + (f" (their {int(round((m['multiplier'] - 1) * 100))}% repeat/broken-trust surcharge applied)" if m["multiplier"] > 1 else "")
        + (f"; commits them to improving {str(m['promise_metric']).replace('_', ' ')} within 2 rounds" if m.get("creates_promise") else "; no binding commitment")
        for m in menu
    ]
    prior_deals = len(room.get("deals", []))
    scarred = any(m["multiplier"] > 1 for m in menu)
    transcript = "\n".join(
        f"{'THEM' if t['who'] == 'player' else 'YOU'}: {t['text']}"
        for t in room.get("turns", [])[-6:]
    )

    return (
        f"You are {p.get('name')}, {p.get('title')}. Personality: {p.get('personality')}.\n"
        f"You are in a private meeting with the executive team of Muressons Global, "
        f"a conglomerate you currently regard as {p.get('stage', 'hostile').upper()}. "
        f"It is simulation round {round_number}.\n\n"
        f"YOUR GRIEVANCES (measured facts — do not invent others):\n" + "\n".join(g_lines) + "\n\n"
        f"CONCESSIONS YOU WOULD ACCEPT (the ONLY things you may propose):\n" + "\n".join(m_lines) + "\n\n"
        f"CONTEXT: they have already agreed to {prior_deals} concession(s) in this meeting."
        + (" They have broken a promise to you before — you are harder to move and you should say so.\n\n" if scarred else "\n\n")
        + (f"CONVERSATION SO FAR:\n{transcript}\n\n" if transcript else "")
        + f"THEY JUST SAID: {player_text}\n\n"
        f"Reply IN CHARACTER, in 2-3 sentences. Be specific about your grievance and hard to please: "
        f"words are not a concession. You may name at most one concession id from the list above if their "
        f"argument warrants it — never invent one, never change a price, never promise anything on your own side "
        f"beyond de-escalating your posture.\n"
        f"Respond ONLY with a JSON object, no markdown fences:\n"
        f'{{"dialogue": "...", "offer": {{"concession_id": "..."}} or null, "mood": "softening|neutral|hardening"}}'
    )


def _parse(text: str, menu_ids: set[str]) -> Optional[dict]:
    """Strict parse + validation. Returns None on ANY irregularity."""
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        # tolerate a fenced block, nothing more exotic
        parts = t.split("\n", 1)
        t = parts[1] if len(parts) > 1 else t
        t = t.rsplit("```", 1)[0]
    try:
        data = json.loads(t.strip())
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    dialogue = data.get("dialogue")
    if not isinstance(dialogue, str) or not dialogue.strip():
        return None
    mood = data.get("mood") if data.get("mood") in VALID_MOODS else "neutral"

    suggested = None
    offer = data.get("offer")
    if isinstance(offer, dict):
        cid = offer.get("concession_id")
        # ONLY an id that is on THIS agent's live menu survives.
        if isinstance(cid, str) and cid in menu_ids:
            suggested = cid
    return {
        "dialogue": dialogue.strip()[:MAX_DIALOGUE_CHARS],
        "suggested_concession": suggested,
        "mood": mood,
    }


async def negotiate_turn(room: dict, grievances: list[dict], menu: list[dict],
                         agent_state: dict, player_text: str,
                         round_number: int) -> Optional[dict]:
    """One in-character reply, or None → caller uses the scripted line.

    Never raises: every failure path returns None.
    """
    try:
        from config import LLM_API_KEY, LLM_PROVIDER, LLM_MODEL
    except Exception:
        return None
    if not LLM_API_KEY:
        return None

    prompt = build_prompt(room, grievances, menu, agent_state, player_text, round_number)
    menu_ids = {m["id"] for m in menu}

    try:
        import httpx
        if LLM_PROVIDER == "anthropic":
            async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
                res = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": LLM_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": LLM_MODEL or "claude-sonnet-4-20250514",
                        "max_tokens": MAX_TOKENS,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                text = (res.json().get("content") or [{}])[0].get("text", "")
        else:
            async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {LLM_API_KEY}",
                             "Content-Type": "application/json"},
                    json={
                        "model": LLM_MODEL or "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.8,
                        "max_tokens": MAX_TOKENS,
                        "response_format": {"type": "json_object"},
                    },
                )
                text = res.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        _log.warning("[negotiation] LLM turn failed (%s) — using scripted line.", exc)
        return None

    parsed = _parse(text, menu_ids)
    if parsed is None:
        _log.warning("[negotiation] LLM returned unusable payload — using scripted line.")
    return parsed
