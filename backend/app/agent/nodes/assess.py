"""
Assessment node — assigns severity level.

Takes the classification output and determines how serious
this incident is. This directly affects dashboard alerting
and response prioritization.
"""

import json

from langchain_openai import ChatOpenAI

from app.agent.prompts.threat_analysis import get_severity_prompt
from app.agent.state import AgentState
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Heuristic severity matrix — used as fallback
SEVERITY_MATRIX = {
    ("targeted_human", "aws_key"): "critical",
    ("targeted_human", "database_url"): "critical",
    ("targeted_human", "jwt_secret"): "high",
    ("targeted_human", "ssh_key"): "high",
    ("targeted_human", "api_key"): "high",
    ("insider_threat", "aws_key"): "critical",
    ("insider_threat", "database_url"): "critical",
    ("automated_scanner", "aws_key"): "medium",
    ("automated_scanner", "database_url"): "medium",
    ("automated_scanner", "api_key"): "low",
}


def assess_node(state: AgentState) -> dict:
    """
    Assigns severity using LLM reasoning with heuristic fallback.
    """
    settings = get_settings()

    logger.info("agent_assess_start", event_id=state["event_id"])

    prompt = get_severity_prompt(
        threat_actor_type=state.get("threat_actor_type", "unknown"),
        token_type=state["token_type"],
        classification_reasoning=state.get("classification_reasoning", ""),
        threat_indicators=state.get("threat_indicators", {}),
    )

    try:
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.1,
            max_tokens=300,
        )
        response = llm.invoke(prompt)
        clean = response.content.strip().strip("```json").strip("```").strip()
        result = json.loads(clean)

        severity = result.get("severity", "medium")
        confidence = float(result.get("confidence", 0.5))
        reasoning = result.get("reasoning", "")

    except Exception as e:
        logger.warning(
            "agent_assess_llm_failed",
            error=str(e),
            event_id=state["event_id"],
        )
        # Heuristic fallback using severity matrix
        actor = state.get("threat_actor_type", "unknown")
        token_type = state.get("token_type", "")
        severity = SEVERITY_MATRIX.get((actor, token_type), "medium")
        confidence = 0.5
        reasoning = f"Heuristic severity from matrix: actor={actor}, token={token_type}"

    log_entry = f"Severity assessed: {severity.upper()} (confidence: {confidence:.0%})"
    logger.info(
        "agent_assess_complete",
        event_id=state["event_id"],
        severity=severity,
    )

    return {
        "severity": severity,
        "confidence": confidence,
        "severity_reasoning": reasoning,
        "reasoning_log": [log_entry],
    }
