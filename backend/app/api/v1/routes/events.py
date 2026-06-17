"""
Event routes — REST endpoints and WebSocket connection.

This module provides:
1. WebSocket /ws — real-time event stream for the dashboard
2. POST /events/trigger — record a new token trigger
3. GET /events/recent — fetch recent events (dashboard init)
4. GET /events/token/{token_id} — events for a specific token
"""

import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.engine import get_db_session
from app.schemas.event import TriggerEventCreate, TriggerEventResponse
from app.services.event import EventService
from app.websocket.manager import manager

logger = get_logger(__name__)

router = APIRouter(tags=["Events"])


# ----------------------------------------------------------------
# Dependency
# ----------------------------------------------------------------
async def get_event_service(
    session: AsyncSession = Depends(get_db_session),
) -> EventService:
    return EventService(session)


# ----------------------------------------------------------------
# WebSocket endpoint
# The dashboard connects here for real-time event streaming.
# Path: ws://localhost:8000/api/v1/ws
# ----------------------------------------------------------------
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Real-time WebSocket connection for the dashboard.

    Connection lifecycle:
    1. Client connects → manager registers the connection
    2. Client receives a welcome message immediately
    3. Connection stays open — client receives broadcasts
    4. If client disconnects → manager removes the connection

    The while True loop keeps the connection alive and
    handles any messages the client sends (ping/pong, etc.)
    """
    await manager.connect(websocket)
    try:
        while True:
            # Wait for any message from the client
            # This keeps the connection alive
            data = await websocket.receive_text()

            # Handle client ping — respond with pong
            if data == "ping":
                await manager.send_to_client(websocket, {
                    "type": "pong",
                    "connections": manager.connection_count,
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("websocket_client_disconnected_cleanly")

    except Exception as e:
        logger.error("websocket_error", error=str(e))
        manager.disconnect(websocket)


# ----------------------------------------------------------------
# POST /events/trigger
# Called when a honey token is accessed — records the event
# and broadcasts to all connected dashboards instantly.
# ----------------------------------------------------------------
@router.post(
    "/events/trigger",
    response_model=TriggerEventResponse,
    status_code=201,
    summary="Record a honey token trigger event",
    description=(
        "Called when unauthorized access to a honey token is detected. "
        "Records the event, marks the token as triggered, and broadcasts "
        "a real-time alert to all connected dashboard clients."
    ),
)
async def trigger_event(
    payload: TriggerEventCreate,
    service: EventService = Depends(get_event_service),
) -> TriggerEventResponse:
    return await service.record_trigger(payload)


# ----------------------------------------------------------------
# GET /events/recent
# Dashboard calls this on load to get historical events
# ----------------------------------------------------------------
@router.get(
    "/events/recent",
    response_model=list[TriggerEventResponse],
    summary="Get recent trigger events",
)
async def get_recent_events(
    limit: int = 100,
    service: EventService = Depends(get_event_service),
) -> list[TriggerEventResponse]:
    return await service.get_recent_events(limit=limit)


# ----------------------------------------------------------------
# GET /events/token/{token_id}
# All events for a specific token
# ----------------------------------------------------------------
@router.get(
    "/events/token/{token_id}",
    response_model=list[TriggerEventResponse],
    summary="Get all events for a specific token",
)
async def get_token_events(
    token_id: uuid.UUID,
    service: EventService = Depends(get_event_service),
) -> list[TriggerEventResponse]:
    return await service.get_events_for_token(token_id)
