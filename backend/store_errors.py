"""store_errors — exceptions shared by the two state stores.

N2 (EVAL_AuditResponse 2026-09-10, action 9). Both database.py (PostgreSQL)
and database_memory.py raise the same class, so router code and the FastAPI
exception handler (main.py) can name one type whichever store is active.
"""
from __future__ import annotations


class StaleStateError(Exception):
    """A round-bound write found that the session is no longer on the round
    the caller read (F01 / N2, audit 2026-09-09). The write was NOT applied.

    Callers must not retry it against the newer round: whatever was being
    written was computed from the old one. main.py answers 409 stale_state.
    """

    def __init__(self, session_id: str, expected_round, actual_round=None):
        self.session_id = session_id
        self.expected_round = expected_round
        self.actual_round = actual_round
        super().__init__(
            f"session {session_id}: write bound to round {expected_round} but the session "
            f"is on round {actual_round if actual_round is not None else '?'}"
        )


__all__ = ["StaleStateError"]
