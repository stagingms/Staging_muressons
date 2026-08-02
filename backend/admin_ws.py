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

from fastapi import WebSocket

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

    async def connect_player(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.setdefault(session_id, []).append(websocket)

    async def connect_admin(self, websocket: WebSocket):
        await websocket.accept()
        self.admin_connections.append(websocket)

    def disconnect_player(self, websocket: WebSocket, session_id: str):
        conns = self.active_connections.get(session_id, [])
        if websocket in conns:
            conns.remove(websocket)

    def disconnect_admin(self, websocket: WebSocket):
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)

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
        dead = []
        for ws in self.admin_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.admin_connections.remove(ws)

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
