"""quiz_gate.py — mandatory round-quiz gate + per-player quiz score log.

The facilitator can mark quizzes MANDATORY for a cohort (quiz_mandatory cohort
setting). When on, a round that carries a quiz notebook blocks the player's
decision/commit until they have taken that round's quiz. "Taken" = at least one
recorded attempt (the existing /learning-bonus flow writes
learning_bonuses_awarded["quiz_complete_<notebook_id>"]); passing is NOT
required, so a struggling student is never permanently trapped. Rounds with no
quiz notebook are unaffected, and the gate is inert unless quizzes are actually
enabled for the cohort.

Everything here is read-only and defensive: any resolution hiccup fails OPEN
(blocked=False) so the gate can never wedge a cohort.
"""

from __future__ import annotations


def _round_quiz_notebook(current_round: int):
    """The notebook that is THIS round's required quiz, or None.

    A notebook qualifies when its target_round equals the current round AND it
    offers a quiz. (Notebooks are cumulative for browsing — target_round <=
    round — but the MANDATORY gate keys only on the round's own notebook.)"""
    try:
        from admin_resources import _notebooklm_notebooks
    except Exception:
        return None
    for nb in _notebooklm_notebooks:
        if nb.get("target_round", 1) == current_round and "quiz" in (nb.get("content_types") or []):
            return nb
    return None


def _quizzes_enabled(session_id: str, parent_id: str | None) -> bool:
    """Whether quizzes are visible for this cohort (the same resolution the
    player-resources endpoint uses). Gate is inert when quizzes are off."""
    try:
        from admin_resources import _quiz_enabled
    except Exception:
        return True
    enabled = _quiz_enabled.get(session_id, True)
    if parent_id:
        enabled = _quiz_enabled.get(parent_id, enabled)
    return bool(enabled)


def quiz_gate_status(session_id: str, current_round: int, global_state: dict,
                     parent_id: str | None = None) -> dict:
    """Mandatory-quiz gate for a player's current round.

    Returns a JSON-safe dict the dashboard surfaces on global_state so the
    cockpit can block committing (mirrors cohort_round_locked):
        mandatory            — the cohort setting is on
        quiz_enabled         — quizzes are visible for this cohort
        required_notebook_id — the round's quiz notebook id (None if none)
        required_title       — its title (for the player-facing prompt)
        completed            — the player has ≥1 recorded attempt on it
        best_score_percent   — best recorded score (None if not taken)
        blocked              — mandatory AND enabled AND a quiz is due AND not taken
    """
    try:
        from admin_shared import get_effective_settings
        eff = get_effective_settings(parent_id or session_id)
        mandatory = bool(eff.get("quiz_mandatory", False))
    except Exception:
        mandatory = False

    q_enabled = _quizzes_enabled(session_id, parent_id)
    nb = _round_quiz_notebook(current_round)
    required_id = nb.get("id") if nb else None
    required_title = nb.get("title") if nb else None

    awarded = (global_state or {}).get("learning_bonuses_awarded", {}) or {}
    rec = awarded.get(f"quiz_complete_{required_id}") if required_id else None
    completed = rec is not None
    best = None
    if rec:
        best = rec.get("best_score_percent", rec.get("score_percent"))

    blocked = bool(mandatory and q_enabled and required_id is not None and not completed)

    return {
        "mandatory": mandatory,
        "quiz_enabled": q_enabled,
        "required_notebook_id": required_id,
        "required_title": required_title,
        "completed": completed,
        "best_score_percent": best,
        "blocked": blocked,
    }


def build_quiz_score_log(global_state: dict) -> dict:
    """Per-player quiz score log for the final results / archetype card.

    Reads the already-persisted learning_bonuses_awarded (the /learning-bonus
    flow records best score + attempts per quiz notebook) and enriches each
    entry with the notebook's title/round + pass/fail against the cohort
    threshold. Returns {entries: [...], quizzes_taken, average_best_score,
    passed_count, pass_threshold} — safe to embed in the final-report payload."""
    awarded = (global_state or {}).get("learning_bonuses_awarded", {}) or {}
    try:
        from admin_resources import _notebooklm_notebooks
        nb_by_id = {nb.get("id"): nb for nb in _notebooklm_notebooks}
    except Exception:
        nb_by_id = {}

    # Pass threshold is a cohort setting; fall back to the legacy 70.
    pass_threshold = 70
    try:
        from admin_shared import _god_mode_settings
        pass_threshold = int(_god_mode_settings.get("quiz_pass_threshold", 70) or 70)
    except Exception:
        pass_threshold = 70

    entries = []
    for key, rec in awarded.items():
        if not key.startswith("quiz_complete_") or not isinstance(rec, dict):
            continue
        nb_id = key[len("quiz_complete_"):]
        nb = nb_by_id.get(nb_id, {})
        best = int(rec.get("best_score_percent", rec.get("score_percent", 0)) or 0)
        entries.append({
            "notebook_id": nb_id,
            "title": nb.get("title", nb_id),
            "round": nb.get("target_round"),
            "best_score_percent": best,
            "attempts": int(rec.get("attempt", 1) or 1),
            "points": int(rec.get("points", 0) or 0),
            "passed": best >= pass_threshold,
        })

    entries.sort(key=lambda e: (e["round"] if e["round"] is not None else 99, e["title"]))
    taken = len(entries)
    avg = round(sum(e["best_score_percent"] for e in entries) / taken, 1) if taken else 0.0
    passed = sum(1 for e in entries if e["passed"])
    return {
        "entries": entries,
        "quizzes_taken": taken,
        "average_best_score": avg,
        "passed_count": passed,
        "pass_threshold": pass_threshold,
    }
