"""
Report node — generates natural language incident report.

This is what gets written to the database and displayed
in the dashboard's agent analysis field.
"""

from langchain_openai import ChatOpenAI

from app.agent.prompts.threat_analysis import get_report_prompt
from app.agent.state import AgentState
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def report_node(state: AgentState) -> dict:
    """
    Generates a professional incident report using the LLM.
    """
    settings = get_settings()

    logger.info("agent_report_start", event_id=state["event_id"])

    prompt = get_report_prompt(
        token_label=state["token_label"],
        token_type=state["token_type"],
        source_ip=state["source_ip"],
        threat_actor_type=state.get("threat_actor_type", "unknown"),
        severity=state.get("severity", "medium"),
        classification_reasoning=state.get("classification_reasoning", ""),
        severity_reasoning=state.get("severity_reasoning", ""),
        triggered_at=state["triggered_at"],
    )

    try:
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3,
            max_tokens=600,
        )
        response = llm.invoke(prompt)
        incident_report = response.content.strip()

        # Extract first sentence as the dashboard summary
        first_sentence = incident_report.split(".")[0] + "."
        summary = first_sentence[:150]

    except Exception as e:
        logger.warning(
            "agent_report_llm_failed",
            error=str(e),
            event_id=state["event_id"],
        )
        severity = state.get("severity", "medium").upper()
        actor = state.get("threat_actor_type", "unknown")
        incident_report = (
            f"{severity} severity incident detected. "
            f"Threat actor classification: {actor}. "
            f"Source IP: {state['source_ip']} accessed "
            f"{state['token_type']} token '{state['token_label']}'. "
            f"Manual review recommended."
        )
        summary = f"{severity} alert: {actor} accessed {state['token_label']}"

    log_entry = f"Incident report generated ({len(incident_report)} chars)"
    logger.info("agent_report_complete", event_id=state["event_id"])

    return {
        "incident_report": incident_report,
        "summary": summary,
        "reasoning_log": [log_entry],
    }
