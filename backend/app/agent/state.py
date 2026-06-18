"""
LangGraph agent state definition.

The AgentState is the single data structure that flows through
every node in the threat analysis graph. Each node receives the
full state, does its work, and returns a dict of fields to update.

LangGraph merges those updates back into the state automatically
before passing it to the next node.

This is the TypedDict pattern — every field is typed, making the
graph's data flow explicit and inspectable.
"""

from typing import TypedDict, Annotated
import operator
from datetime import datetime


class ThreatIndicators(TypedDict, total=False):
    """
    Structured threat indicators extracted during enrichment.
    Built up progressively as the agent reasons through the event.
    """
    is_known_scanner: bool        # Matches known scanner IP ranges
    is_tor_exit_node: bool        # TOR exit node indicator
    is_automated: bool            # Automated tool vs human browser
    access_pattern: str           # "targeted", "scanning", "fuzzing"
    token_sensitivity: str        # "low", "medium", "high", "critical"
    geographic_anomaly: bool      # Access from unexpected region
    time_anomaly: bool            # Access at unusual hour


class AgentState(TypedDict):
    """
    Complete state for one threat analysis run.

    Flows through the graph:
    enrich → classify → assess → report → respond

    Fields are populated progressively — early nodes set context,
    later nodes build on it to produce the final assessment.
    """

    # ----------------------------------------------------------------
    # Input — set before graph starts, never modified
    # ----------------------------------------------------------------
    event_id: str
    token_id: str
    token_label: str
    token_type: str
    source_ip: str
    user_agent: str | None
    request_method: str | None
    request_path: str | None
    triggered_at: str

    # ----------------------------------------------------------------
    # Enrichment — populated by enrich_node
    # ----------------------------------------------------------------
    threat_indicators: ThreatIndicators
    ip_context: str           # Human-readable IP context summary
    request_context: str      # Human-readable request context

    # ----------------------------------------------------------------
    # Classification — populated by classify_node
    # ----------------------------------------------------------------
    threat_actor_type: str    # "automated_scanner" | "targeted_human" | "insider" | "unknown"
    classification_reasoning: str

    # ----------------------------------------------------------------
    # Assessment — populated by assess_node
    # ----------------------------------------------------------------
    severity: str             # "low" | "medium" | "high" | "critical"
    confidence: float         # 0.0 - 1.0
    severity_reasoning: str

    # ----------------------------------------------------------------
    # Report — populated by report_node
    # ----------------------------------------------------------------
    incident_report: str      # Full natural language report
    summary: str              # One-line summary for dashboard

    # ----------------------------------------------------------------
    # Response — populated by respond_node
    # ----------------------------------------------------------------
    recommended_action: str   # "monitor" | "block" | "escalate" | "investigate"
    action_reasoning: str

    # ----------------------------------------------------------------
    # Execution metadata
    # ----------------------------------------------------------------
    # Annotated with operator.add means LangGraph APPENDS to this
    # list rather than replacing it — gives us a full reasoning log
    reasoning_log: Annotated[list[str], operator.add]
    completed_at: str | None
    error: str | None
