"""
admin_ws.py — WebSocket connection manager (audit #17, extracted from admin_router).

Behaviour-preserving extraction of the ConnectionManager class and the shared
`manager` singleton that fans real-time pushes out to player/admin WebSocket
connections. Moved here verbatim to shrink admin_router.py's ~10k-line god-file.
admin_router re-exports `manager` (and the class) so every existing reference —
the websocket endpoints in admin_router and `from admin_router import manager` in
admin_resources.py / router.py — keeps working unchanged.
"""

from __future__ import annotations

import json
import logging
from typing import Awaitable, Callable, Optional

from fastapi import WebSocket

_log = logging.getLogger("muressons.ws")

# QA-2026-07-16 #10: cross-worker fan-out. Imported lazily-safe: in single-worker
# / memory mode every publish() is a no-op, so behaviour is unchanged.
try:
    import ws_fanout as _fanout
except Exception:  # pragma: no cover
    _fanout = None


class ConnectionManager:
    """Manages WebSocket connections for real-time push to players."""

    def __init__(self):
        # session_id → list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}
        # Admin connections for dashboard updates
        self.admin_connections: list[WebSocket] = []
        # F08 residual (2026-09-10): the facilitator behind each admin socket,
        # and the predicate that says whether a facilitator may observe a
        # session (admin_router sets it: owner / co-facilitator / admin). A
        # push that names a session is delivered only to sockets whose
        # facilitator may observe it; a push that names none (platform
        # settings, players cleared) goes to every admin socket, as before.
        self.admin_identity: dict[WebSocket, Optional[str]] = {}
        self.admin_scope: Optional[Callable[[str, str], Awaitable[bool]]] = None

    async def connect_player(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.setdefault(session_id, []).append(websocket)

    async def connect_admin(self, websocket: WebSocket, facilitator_id: Optional[str] = None):
        await websocket.accept()
        self.admin_connections.append(websocket)
        self.admin_identity[websocket] = facilitator_id

    def disconnect_player(self, websocket: WebSocket, session_id: str):
        conns = self.active_connections.get(session_id, [])
        if websocket in conns:
            conns.remove(websocket)

    def disconnect_admin(self, websocket: WebSocket):
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)
        self.admin_identity.pop(websocket, None)

    @staticmethod
    def _message_session(message: dict) -> Optional[str]:
        """The session a push is about, if it names one."""
        sid = message.get("session_id") or message.get("cohort_id")
        if not sid:
            player = message.get("player")
            if isinstance(player, dict):
                sid = player.get("session_id")
        return str(sid) if sid else None

    async def _admin_may_receive(self, websocket: WebSocket, session_id: Optional[str]) -> bool:
        if session_id is None or self.admin_scope is None:
            return True
        fac_id = self.admin_identity.get(websocket)
        if fac_id is None:
            return False          # a socket without an identity sees nothing session-bound
        if fac_id == "god_mode":
            return True
        try:
            return bool(await self.admin_scope(fac_id, session_id))
        except Exception as exc:  # fail closed for everyone but the break-glass identity
            _log.warning("admin push scope check failed for %s on %s: %s", fac_id, session_id, exc)
            return False

    async def push_to_session(self, session_id: str, message: dict):
        """Push a message to all player connections in a session (this worker),
        then fan out to other workers so their local sockets get it too (#10)."""
        await self._deliver_session_local(session_id, message)
        if _fanout is not None:
            await _fanout.publish("session", session_id, message)

    async def _deliver_session_local(self, session_id: str, message: dict):
        """Local-only delivery to this worker's sockets (no fan-out) — also the
        sink the fan-out listener calls for a REMOTE push."""
        payload = json.dumps(message)
        conns = self.active_connections.get(session_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            conns.remove(ws)

    async def broadcast_admin(self, message: dict):
        """Broadcast to all admin dashboard connections, then fan out (#10)."""
        await self._deliver_admin_local(message)
        if _fanout is not None:
            await _fanout.publish("admin", None, message)

    async def _deliver_admin_local(self, message: dict):
        payload = json.dumps(message)
        session_id = self._message_session(message)
        dead = []
        for ws in list(self.admin_connections):
            if not await self._admin_may_receive(ws, session_id):
                continue
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.admin_connections:
                self.admin_connections.remove(ws)
            self.admin_identity.pop(ws, None)

    async def broadcast_students(self, message: dict):
        """Broadcast to all player connections, then fan out (#10)."""
        await self._deliver_students_local(message)
        if _fanout is not None:
            await _fanout.publish("students", None, message)

    async def _deliver_students_local(self, message: dict):
        payload = json.dumps(message)
        for session_id, conns in list(self.active_connections.items()):
            dead = []
            for ws in conns:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                conns.remove(ws)

    async def broadcast(self, message: dict):
        """Broadcast to ALL connected clients (players + admins), then fan out (#10)."""
        await self._deliver_students_local(message)
        await self._deliver_admin_local(message)
        if _fanout is not None:
            await _fanout.publish("all", None, message)

    async def deliver_local(self, kind: str, session_id, message: dict):
        """QA-2026-07-16 #10: sink for a REMOTE push received via ws_fanout —
        delivers to THIS worker's sockets only (never re-publishes)."""
        if kind == "session":
            await self._deliver_session_local(session_id, message)
        elif kind == "admin":
            await self._deliver_admin_local(message)
        elif kind == "students":
            await self._deliver_students_local(message)
        elif kind == "all":
            await self._deliver_students_local(message)
            await self._deliver_admin_local(message)


manager = ConnectionManager()
