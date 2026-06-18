"""
ShadowWall AI — LangGraph threat analysis graph.

Defines the directed graph of reasoning nodes that runs
autonomously when a honey token is triggered.

Graph flow:
    START → enrich → classify → assess → report → respond → END

Each edge is a directed connection. The graph is compiled once
at module load time and reused for every analysis run.

Architecture note:
    LangGraph's StateGraph takes our AgentState TypedDict and
    ensures every node receives and returns the correct fields.
    This gives us type safety across the entire agent pipeline.
"""

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes.enrich import enrich_node
from app.agent.nodes.classify import classify_node
from app.agent.nodes.assess import assess_node
from app.agent.nodes.report import report_node
from app.agent.nodes.respond import respond_node
from app.core.logging import get_logger

logger = get_logger(__name__)


def build_threat_analysis_graph() -> StateGraph:
    """
    Constructs and compiles the threat analysis graph.

    Called once at startup. The compiled graph is a runnable
    that accepts an initial AgentState and returns a final
    AgentState with all fields populated.
    """
    graph = StateGraph(AgentState)

    # ----------------------------------------------------------------
    # Register nodes
    # Each node is a Python function: AgentState -> dict
    # ----------------------------------------------------------------
    graph.add_node("enrich", enrich_node)
    graph.add_node("classify", classify_node)
    graph.add_node("assess", assess_node)
    graph.add_node("report", report_node)
    graph.add_node("respond", respond_node)

    # ----------------------------------------------------------------
    # Define edges — the execution flow
    # ----------------------------------------------------------------
    graph.set_entry_point("enrich")
    graph.add_edge("enrich", "classify")
    graph.add_edge("classify", "assess")
    graph.add_edge("assess", "report")
    graph.add_edge("report", "respond")
    graph.add_edge("respond", END)

    # ----------------------------------------------------------------
    # Compile — validates graph structure and returns a runnable
    # ----------------------------------------------------------------
    compiled = graph.compile()

    logger.info("threat_analysis_graph_compiled")
    return compiled


# ----------------------------------------------------------------
# Module-level compiled graph instance.
# Imported by the agent service. Built once, reused forever.
# ----------------------------------------------------------------
threat_analysis_graph = build_threat_analysis_graph()
