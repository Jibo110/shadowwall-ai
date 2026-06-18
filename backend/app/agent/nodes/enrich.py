"""
Enrichment node — gathers context about the trigger event.

This node runs FIRST in the graph. It analyzes the raw event data
and builds human-readable context summaries that subsequent nodes
use for their reasoning.

In production this node would:
- Query IP reputation APIs (AbuseIPDB, VirusTotal)
- Check against threat intel feeds
- Perform reverse DNS lookups
- Query GeoIP databases

For now we use heuristic analysis — enough to demonstrate the
pattern and produce meaningful results without API keys.
"""

from app.agent.state import AgentState, ThreatIndicators
from app.core.logging import get_logger

logger = get_logger(__name__)

# Known scanner/bot user agent fragments
SCANNER_UA_PATTERNS = [
    "python-requests", "curl", "wget", "nikto", "nmap",
    "masscan", "zgrab", "gobuster", "dirbuster", "sqlmap",
    "burpsuite", "metasploit", "nuclei", "httpx", "ffuf",
]

# Known high-value token types
HIGH_VALUE_TOKENS = {"aws_key", "database_url", "jwt_secret", "ssh_key"}

# Suspicious path patterns
SUSPICIOUS_PATHS = [
    ".env", "config", "secret", "credential", "password",
    "passwd", "shadow", "key", "token", "auth", "backup",
    "dump", "admin", "wp-config", ".git",
]


def enrich_node(state: AgentState) -> dict:
    """
    Enriches raw event data with contextual threat indicators.

    Takes the raw IP, user agent, and request data and produces
    structured threat indicators plus human-readable context
    summaries for the classifier node.
    """
    logger.info(
        "agent_enrich_start",
        event_id=state["event_id"],
        source_ip=state["source_ip"],
    )

    indicators: ThreatIndicators = {}
    ip_context_parts = []
    request_context_parts = []

    # ----------------------------------------------------------------
    # Analyze User Agent
    # ----------------------------------------------------------------
    ua = (state.get("user_agent") or "").lower()

    is_automated = any(pattern in ua for pattern in SCANNER_UA_PATTERNS)
    indicators["is_automated"] = is_automated

    if is_automated:
        matched = [p for p in SCANNER_UA_PATTERNS if p in ua]
        ip_context_parts.append(
            f"User agent matches known tool pattern: {matched[0]}"
        )
    elif not ua:
        ip_context_parts.append("No user agent provided — unusual for legitimate access")
        indicators["is_automated"] = True
    else:
        ip_context_parts.append(f"Browser-like user agent detected: {ua[:80]}")

    # ----------------------------------------------------------------
    # Analyze Request Path
    # ----------------------------------------------------------------
    path = (state.get("request_path") or "").lower()

    if path:
        suspicious_matches = [p for p in SUSPICIOUS_PATHS if p in path]
        if suspicious_matches:
            request_context_parts.append(
                f"Request path contains sensitive indicators: {suspicious_matches}"
            )
            indicators["access_pattern"] = "targeted"
        else:
            indicators["access_pattern"] = "scanning"

    # ----------------------------------------------------------------
    # Analyze Token Type Sensitivity
    # ----------------------------------------------------------------
    token_type = state.get("token_type", "")
    if token_type in HIGH_VALUE_TOKENS:
        indicators["token_sensitivity"] = "critical"
        request_context_parts.append(
            f"High-value token type accessed: {token_type}"
        )
    else:
        indicators["token_sensitivity"] = "medium"

    # ----------------------------------------------------------------
    # Analyze IP (heuristic — no external API)
    # ----------------------------------------------------------------
    ip = state.get("source_ip", "")

    # Private IP ranges suggest internal/insider access
    if ip.startswith(("10.", "192.168.", "172.16.", "172.17.")):
        ip_context_parts.append(
            "Source IP is from private network range — potential insider threat"
        )
        indicators["geographic_anomaly"] = True
    elif ip.startswith("127."):
        ip_context_parts.append("Source IP is localhost — likely internal testing")
    else:
        ip_context_parts.append(f"External IP address: {ip}")

    # ----------------------------------------------------------------
    # Build context summaries
    # ----------------------------------------------------------------
    ip_context = " | ".join(ip_context_parts) if ip_context_parts else "No IP context"
    request_context = (
        " | ".join(request_context_parts)
        if request_context_parts
        else "No suspicious request patterns detected"
    )

    log_entry = f"Enrichment complete: automated={indicators.get('is_automated')}, sensitivity={indicators.get('token_sensitivity')}"

    logger.info("agent_enrich_complete", event_id=state["event_id"])

    return {
        "threat_indicators": indicators,
        "ip_context": ip_context,
        "request_context": request_context,
        "reasoning_log": [log_entry],
    }
