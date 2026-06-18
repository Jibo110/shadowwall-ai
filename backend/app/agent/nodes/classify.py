"""
Classification node — identifies the threat actor type.

Uses the LLM to reason about the enriched context and classify
the threat actor into one of four categories.
"""

import json

from langchain_openai import ChatOpenAI

from app.agent.prompts.threat_analysis import get_classification_prompt
from app.agent.state import AgentState
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def classify_node(state: AgentState) -> dict:
    """
    Classifies the threat actor using the LLM.

    Falls back to heuristic classification if the LLM call fails
    or if no API key is configured. This ensures the agent always
    produces a result — degraded gracefully, never crashes.
    """
    settings = get_settings()

    logger.info("agent_classify_start", event_id=state["event_id"])

    # ----------------------------------------------------------------
    # Build the classification prompt
    # ----------------------------------------------------------------
    prompt = get_classification_prompt(
        source_ip=state["source_ip"],
        user_agent=state.get("user_agent"),
        request_method=state.get("request_method"),
        request_path=state.get("request_path"),
        token_type=state["token_type"],
        token_label=state["token_label"],
        ip_context=state.get("ip_context", ""),
        request_context=state.get("request_context", ""),
    )

    # ----------------------------------------------------------------
    # Call LLM — with graceful fallback
    # ----------------------------------------------------------------
    try:
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=500,
        )
        response = llm.invoke(prompt)
        content = response.content

        # Parse JSON response
        # Strip any markdown code blocks if the LLM added them
        clean = content.strip().strip("```json").strip("```").strip()
        result = json.loads(clean)

        threat_actor_type = result.get("threat_actor_type", "unknown")
        reasoning = result.get("reasoning", "No reasoning provided")
        confidence = float(result.get("confidence", 0.5))

    except Exception as e:
        logger.warning(
            "agent_classify_llm_failed",
            error=str(e),
            event_id=state["event_id"],
        )
        # Heuristic fallback — still produces meaningful output
        indicators = state.get("threat_indicators", {})
        threat_actor_type = (
            "automated_scanner"
            if indicators.get("is_automated")
            else "unknown"
        )
        reasoning = f"LLM unavailable, heuristic classification applied: {str(e)[:100]}"
        confidence = 0.4

    log_entry = f"Classification: {threat_actor_type} (confidence: {confidence:.0%})"
    logger.info(
        "agent_classify_complete",
        event_id=state["event_id"],
        threat_actor_type=threat_actor_type,
    )

    return {
        "threat_actor_type": threat_actor_type,
        "classification_reasoning": reasoning,
        "confidence": confidence,
        "reasoning_log": [log_entry],
    }
