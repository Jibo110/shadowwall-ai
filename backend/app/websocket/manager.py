"""
WebSocket Connection Manager.

Manages all active WebSocket connections and provides
broadcast capabilities for real-time event streaming.

Architecture:
    When a browser opens the dashboard, it establishes a
    WebSocket connection. This manager registers that connection.
    When a honey token is triggered anywhere in the system,
    the event service calls manager.broadcast() and every
    connected dashboard receives the alert instantly.

This is a single-process in-memory manager suitable for
development and single-instance deployments. For multi-instance
production deployments (multiple server pods), you would replace
the in-memory set with Redis pub/sub — which we have already
set up for exactly this purpose in Day 3.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ConnectionManager:
    """
    Tracks active WebSocket connections and handles messaging.

    Uses a set for O(1) add/remove operations.
    Each connected client is identified by their WebSocket object.
    """

    # Active connections — all currently connected dashboards
    _active_connections: set[WebSocket] = field(default_factory=set)

    @property
    def connection_count(self) -> int:
        """Number of currently connected clients."""
        return len(self._active_connections)

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.

        Called when a browser dashboard connects.
        We accept the connection first, then register it.
        """
        await websocket.accept()
        self._active_connections.add(websocket)

        logger.info(
            "websocket_client_connected",
            total_connections=self.connection_count,
            client=websocket.client.host if websocket.client else "unknown",
        )

        # Send a welcome message so client knows connection is live
        await self._send_to(websocket, {
            "type": "connection_established",
            "message": "Connected to ShadowWall AI real-time stream",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_connections": self.connection_count,
        })

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a disconnected client from the active set.

        Called when a browser closes the tab or loses connection.
        Using discard() instead of remove() prevents KeyError
        if the connection was never properly registered.
        """
        self._active_connections.discard(websocket)

        logger.info(
            "websocket_client_disconnected",
            total_connections=self.connection_count,
        )

    async def broadcast(self, event: dict) -> None:
        """
        Send an event to ALL connected dashboard clients.

        This is the core method — called whenever a honey token
        is triggered, an agent decision is made, or any system
        event needs to be surfaced in real time.

        Handles dead connections gracefully — if a send fails,
        we remove that connection and continue broadcasting
        to the remaining clients. Never let one bad connection
        block others from receiving events.
        """
        if not self._active_connections:
            logger.debug("websocket_broadcast_no_clients", event_type=event.get("type"))
            return

        # Snapshot the set — we may modify it during iteration
        connections = list(self._active_connections)
        dead_connections: list[WebSocket] = []

        for websocket in connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await self._send_to(websocket, event)
                else:
                    dead_connections.append(websocket)
            except Exception as e:
                logger.warning(
                    "websocket_send_failed",
                    error=str(e),
                    client=websocket.client.host if websocket.client else "unknown",
                )
                dead_connections.append(websocket)

        # Clean up dead connections
        for dead in dead_connections:
            self.disconnect(dead)

        logger.debug(
            "websocket_broadcast_complete",
            recipients=len(connections) - len(dead_connections),
            dead_connections=len(dead_connections),
            event_type=event.get("type"),
        )

    async def send_to_client(self, websocket: WebSocket, event: dict) -> None:
        """
        Send an event to a single specific client.
        Used for client-specific messages (e.g. acknowledgements).
        """
        await self._send_to(websocket, event)

    async def _send_to(self, websocket: WebSocket, data: dict) -> None:
        """
        Internal: serialize and send data to one WebSocket.
        All outgoing messages are JSON — consistent contract.
        """
        await websocket.send_text(json.dumps(data, default=str))


# ----------------------------------------------------------------
# Global singleton instance.
# Imported and used throughout the application.
# There is exactly ONE manager for the entire process.
# ----------------------------------------------------------------
manager = ConnectionManager()
