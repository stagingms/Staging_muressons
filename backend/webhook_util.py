"""webhook_util.py — fire-and-forget lifecycle webhooks (LOW-tier / LMS sync).

A cohort may configure `webhook_url` (https-only, validated in
admin_shared.normalize_advanced_cohort_settings). When set, the platform POSTs
a small JSON envelope on lifecycle events — currently `round_committed` and
`game_over` — so an LMS / gradebook / Slack bridge can sync without polling.

Design constraints:
  • NEVER blocks or fails the player-facing request: delivery is scheduled as
    a background task with a hard timeout; every failure path is swallowed
    (and logged) after bounded retries.
  • Scoped like every other cohort setting: the player session's parent cohort
    carries the config.
  • No secrets: the envelope contains ids + headline numbers only.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

log = logging.getLogger("muressons.webhook")

_TIMEOUT_SECONDS = 5.0
_MAX_ATTEMPTS = 2  # one retry — webhooks are best-effort, not a delivery queue


def resolve_webhook_url(session_id: str, parent_cohort_id: str | None = None) -> str:
    """Effective webhook_url for a session (parent cohort's settings win)."""
    try:
        from admin_shared import get_effective_settings
        url = str(get_effective_settings(parent_cohort_id or session_id).get("webhook_url", "") or "").strip()
        return url if url.startswith("https://") else ""
    except Exception:
        return ""


async def _deliver(url: str, envelope: dict) -> None:
    try:
        import httpx
    except ImportError:  # pragma: no cover - httpx ships with fastapi's stack
        log.warning("[webhook] httpx unavailable — delivery skipped")
        return
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                resp = await client.post(url, json=envelope,
                                         headers={"User-Agent": "Muressons-Webhook/1.0"})
            if resp.status_code < 400:
                return
            log.warning("[webhook] %s returned %s (attempt %s/%s)",
                        url, resp.status_code, attempt, _MAX_ATTEMPTS)
        except Exception as e:
            log.warning("[webhook] delivery to %s failed (attempt %s/%s): %s",
                        url, attempt, _MAX_ATTEMPTS, e)
        await asyncio.sleep(0.5)


def fire_webhook(event: str, session_id: str, parent_cohort_id: str | None = None,
                 payload: dict | None = None) -> bool:
    """Schedule a webhook delivery for `event`. Returns True if one was
    scheduled (config present + running loop), False otherwise. Never raises."""
    try:
        url = resolve_webhook_url(session_id, parent_cohort_id)
        if not url:
            return False
        envelope = {
            "event": event,
            "session_id": session_id,
            "cohort_session_id": parent_cohort_id or session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload or {},
        }
        # Guard: the envelope must be JSON-serialisable before we schedule.
        json.dumps(envelope)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return False  # sync context (tests / scripts) — nothing to schedule on
        loop.create_task(_deliver(url, envelope))
        return True
    except Exception as e:  # absolute backstop — a webhook must never break a commit
        log.warning("[webhook] scheduling failed for %s: %s", session_id, e)
        return False
