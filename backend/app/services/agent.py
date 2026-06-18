"""
Agent service — orchestrates the LangGraph threat analysis pipeline.

This service is the bridge between:
- The event that fired (trigger event data)
- The LangGraph graph that analyzes it
- The database that stores the results
- The WebSocket that broadcasts the findings

Called automatically by the event service after every trigger.
Runs asynchronously so it never blocks the HTTP response.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import threat_analysis_graph
from app.agent.state import AgentState
from app.core.logging import get_logger
from app.db.models.token import TokenStatus
from app.db.repositories.event import EventRepository
from app.db.repositories.token import TokenRepository
from app.schemas.event import SeverityLevel
from app.websocket.manager import manager

logger = get_logger(__name__)


class AgentService:
    """
    Runs the LangGraph threat analysis graph for a trigger event.

    The analysis runs in a background task — it does not block
    the HTTP response that recorded the trigger event.
    The dashboard receives two WebSocket updates:
    1. Immediate: "token_triggered" (from event service, instant)
    2. Delayed: "agent_analysis_complete" (from here, 5-15 seconds later)
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.event_repo = EventRepository(session)
        self.token_repo = TokenRepository(session)

    async def analyze_trigger(
        self,
        event_id: uuid.UUID,
        token_id: uuid.UUID,
        token_label: str,
        token_type: str,
        source_ip: str,
        user_agent: str | None,
        request_method: str | None,
        request_path: str | None,
    ) -> None:
        """
        Run the full threat analysis graph for a trigger event.

        This method is called as a background task — it runs
        after the HTTP response has already been sent to the client.

        Steps:
        1. Build initial agent state from event data
        2. Run the LangGraph graph (enrich→classify→assess→report→respond)
        3. Persist findings to the database
        4. Broadcast analysis results over WebSocket
        """
        logger.info(
            "agent_analysis_starting",
            event_id=str(event_id),
            token_id=str(token_id),
        )

        # ----------------------------------------------------------------
        # Step 1 — Build initial state
        # ----------------------------------------------------------------
        initial_state: AgentState = {
            "event_id": str(event_id),
            "token_id": str(token_id),
            "token_label": token_label,
            "token_type": token_type,
            "source_ip": source_ip,
            "user_agent": user_agent,
            "request_method": request_method,
            "request_path": request_path,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            # Fields populated by nodes — initialized empty
            "threat_indicators": {},
            "ip_context": "",
            "request_context": "",
            "threat_actor_type": "",
            "classification_reasoning": "",
            "severity": "medium",
            "confidence": 0.5,
            "severity_reasoning": "",
            "incident_report": "",
            "summary": "",
            "recommended_action": "monitor",
            "action_reasoning": "",
            "reasoning_log": [],
            "completed_at": None,
            "error": None,
        }

        # ----------------------------------------------------------------
        # Step 2 — Run the graph
        # LangGraph handles the node execution sequence
        # ----------------------------------------------------------------
        try:
            # Run in executor to avoid blocking the event loop
            # LangGraph's invoke is synchronous internally
            loop = asyncio.get_event_loop()
            final_state = await loop.run_in_executor(
                None,
                lambda: threat_analysis_graph.invoke(initial_state),
            )

            severity_str = final_state.get("severity", "medium")
            incident_report = final_state.get("incident_report", "")
            summary = final_state.get("summary", "")
            recommended_action = final_state.get("recommended_action", "monitor")

            logger.info(
                "agent_analysis_complete",
                event_id=str(event_id),
                severity=severity_str,
                action=recommended_action,
            )

        except Exception as e:
            logger.error(
                "agent_analysis_failed",
                event_id=str(event_id),
                error=str(e),
            )
            severity_str = "medium"
            incident_report = f"Agent analysis failed: {str(e)}"
            summary = "Analysis failed — manual review required"
            recommended_action = "investigate"

        # ----------------------------------------------------------------
        # Step 3 — Persist findings to database
        # ----------------------------------------------------------------
        try:
            severity_level = SeverityLevel(severity_str)
            await self.event_repo.update_agent_analysis(
                event_id=event_id,
                severity=severity_level,
                analysis=incident_report,
            )
            await self.session.commit()
        except Exception as e:
            logger.error(
                "agent_persist_failed",
                event_id=str(event_id),
                error=str(e),
            )

        # ----------------------------------------------------------------
        # Step 4 — Broadcast analysis complete to dashboard
        # ----------------------------------------------------------------
        await manager.broadcast({
            "type": "agent_analysis_complete",
            "payload": {
                "event_id": str(event_id),
                "token_id": str(token_id),
                "token_label": token_label,
                "severity": severity_str,
                "summary": summary,
                "recommended_action": recommended_action,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })

        logger.info(
            "agent_broadcast_complete",
            event_id=str(event_id),
        )


        """
Agent service — orchestrates the LangGraph threat analysis pipeline.

This service is the bridge between:
- The event that fired (trigger event data)
- The LangGraph graph that analyzes it
- The database that stores the results
- The WebSocket that broadcasts the findings

Called automatically by the event service after every trigger.
Runs asynchronously so it never blocks the HTTP response.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import threat_analysis_graph
from app.agent.state import AgentState
from app.core.logging import get_logger
from app.db.models.token import TokenStatus
from app.db.repositories.event import EventRepository
from app.db.repositories.token import TokenRepository
from app.schemas.event import SeverityLevel
from app.websocket.manager import manager

logger = get_logger(__name__)


class AgentService:
    """
    Runs the LangGraph threat analysis graph for a trigger event.

    The analysis runs in a background task — it does not block
    the HTTP response that recorded the trigger event.
    The dashboard receives two WebSocket updates:
    1. Immediate: "token_triggered" (from event service, instant)
    2. Delayed: "agent_analysis_complete" (from here, 5-15 seconds later)
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.event_repo = EventRepository(session)
        self.token_repo = TokenRepository(session)

    async def analyze_trigger(
        self,
        event_id: uuid.UUID,
        token_id: uuid.UUID,
        token_label: str,
        token_type: str,
        source_ip: str,
        user_agent: str | None,
        request_method: str | None,
        request_path: str | None,
    ) -> None:
        """
        Run the full threat analysis graph for a trigger event.

        This method is called as a background task — it runs
        after the HTTP response has already been sent to the client.

        Steps:
        1. Build initial agent state from event data
        2. Run the LangGraph graph (enrich→classify→assess→report→respond)
        3. Persist findings to the database
        4. Broadcast analysis results over WebSocket
        """
        logger.info(
            "agent_analysis_starting",
            event_id=str(event_id),
            token_id=str(token_id),
        )

        # ----------------------------------------------------------------
        # Step 1 — Build initial state
        # ----------------------------------------------------------------
        initial_state: AgentState = {
            "event_id": str(event_id),
            "token_id": str(token_id),
            "token_label": token_label,
            "token_type": token_type,
            "source_ip": source_ip,
            "user_agent": user_agent,
            "request_method": request_method,
            "request_path": request_path,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            # Fields populated by nodes — initialized empty
            "threat_indicators": {},
            "ip_context": "",
            "request_context": "",
            "threat_actor_type": "",
            "classification_reasoning": "",
            "severity": "medium",
            "confidence": 0.5,
            "severity_reasoning": "",
            "incident_report": "",
            "summary": "",
            "recommended_action": "monitor",
            "action_reasoning": "",
            "reasoning_log": [],
            "completed_at": None,
            "error": None,
        }

        # ----------------------------------------------------------------
        # Step 2 — Run the graph
        # LangGraph handles the node execution sequence
        # ----------------------------------------------------------------
        try:
            # Run in executor to avoid blocking the event loop
            # LangGraph's invoke is synchronous internally
            loop = asyncio.get_event_loop()
            final_state = await loop.run_in_executor(
                None,
                lambda: threat_analysis_graph.invoke(initial_state),
            )

            severity_str = final_state.get("severity", "medium")
            incident_report = final_state.get("incident_report", "")
            summary = final_state.get("summary", "")
            recommended_action = final_state.get("recommended_action", "monitor")

            logger.info(
                "agent_analysis_complete",
                event_id=str(event_id),
                severity=severity_str,
                action=recommended_action,
            )

        except Exception as e:
            logger.error(
                "agent_analysis_failed",
                event_id=str(event_id),
                error=str(e),
            )
            severity_str = "medium"
            incident_report = f"Agent analysis failed: {str(e)}"
            summary = "Analysis failed — manual review required"
            recommended_action = "investigate"

        # ----------------------------------------------------------------
        # Step 3 — Persist findings to database
        # ----------------------------------------------------------------
        try:
            severity_level = SeverityLevel(severity_str)
            await self.event_repo.update_agent_analysis(
                event_id=event_id,
                severity=severity_level,
                analysis=incident_report,
            )
            await self.session.commit()
        except Exception as e:
            logger.error(
                "agent_persist_failed",
                event_id=str(event_id),
                error=str(e),
            )

        # ----------------------------------------------------------------
        # Step 4 — Broadcast analysis complete to dashboard
        # ----------------------------------------------------------------
        await manager.broadcast({
            "type": "agent_analysis_complete",
            "payload": {
                "event_id": str(event_id),
                "token_id": str(token_id),
                "token_label": token_label,
                "severity": severity_str,
                "summary": summary,
                "recommended_action": recommended_action,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })

        logger.info(
            "agent_broadcast_complete",
            event_id=str(event_id),
        )
