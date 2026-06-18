"""
Response node — decides the recommended action.

The final node in the graph. Takes the full analysis and
produces a concrete recommended action for the security team.
"""

import json

from langchain_openai import ChatOpenAI

from app.agent.prompts.threat_analysis import get_action_prompt
from app.agent.state import AgentState
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Deterministic fallback — severity directly maps to action
SEVERITY_TO_ACTION = {
    "critical": ("escalate", "immediate"),
    "high": ("block", "within_1h"),
    "medium": ("investigate", "within_24h"),
    "low": ("monitor", "when_convenient"),
}


def respond_node(state: AgentState) -> dict:
    """
    Determines recommended response action.
    """
    settings = get_settings()

    logger.info("agent_respond_start", event_id=state["event_id"])

    prompt = get_action_prompt(
        severity=state.get("severity", "medium"),
        threat_actor_type=state.get("threat_actor_type", "unknown"),
        token_type=state["token_type"],
        incident_report=state.get("incident_report", ""),
    )

    try:
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.1,
            max_tokens=200,
        )
        response = llm.invoke(prompt)
        clean = response.content.strip().strip("```json").strip("```").strip()
        result = json.loads(clean)

        action = result.get("action", "monitor")
        reasoning = result.get("reasoning", "")
        urgency = result.get("urgency", "when_convenient")

    except Exception as e:
        logger.warning(
            "agent_respond_llm_failed",
            error=str(e),
            event_id=state["event_id"],
        )
        severity = state.get("severity", "medium")
        action, urgency = SEVERITY_TO_ACTION.get(
            severity, ("monitor", "when_convenient")
        )
        reasoning = f"Deterministic fallback: severity={severity}"

    from datetime import datetime, timezone
    completed_at = datetime.now(timezone.utc).isoformat()

    log_entry = f"Response decided: {action.upper()} (urgency: {urgency})"
    logger.warning(
        "agent_respond_complete",
        event_id=state["event_id"],
        action=action,
        severity=state.get("severity"),
    )

    return {
        "recommended_action": action,
        "action_reasoning": reasoning,
        "completed_at": completed_at,
        "reasoning_log": [log_entry],
    }
