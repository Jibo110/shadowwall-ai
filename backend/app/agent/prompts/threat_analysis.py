"""
Versioned prompt templates for the ShadowWall AI threat analysis agent.

Keeping prompts in a dedicated module (not scattered through code) means:
- They can be version-controlled and A/B tested
- They're easy to find and audit
- They can be loaded from a database in production (LLMOps pattern)

Each prompt is a function that takes context and returns a formatted string.
This is cleaner than f-strings scattered throughout the codebase.
"""


def get_classification_prompt(
    source_ip: str,
    user_agent: str | None,
    request_method: str | None,
    request_path: str | None,
    token_type: str,
    token_label: str,
    ip_context: str,
    request_context: str,
) -> str:
    return f"""You are an expert cybersecurity analyst working on a cyber deception system.

A honey token has been triggered. Analyze the access attempt and classify the threat actor.

## Honey Token Details
- Token Label: {token_label}
- Token Type: {token_type}

## Access Attempt Details
- Source IP: {source_ip}
- User Agent: {user_agent or "Not provided"}
- Request Method: {request_method or "Unknown"}
- Request Path: {request_path or "Unknown"}

## Enrichment Context
{ip_context}
{request_context}

## Classification Task
Classify this threat actor into exactly ONE of these categories:

1. **automated_scanner** — Automated tools, vulnerability scanners, crawlers
   Indicators: generic user agents, sequential paths, no session context

2. **targeted_human** — A human deliberately seeking this specific credential
   Indicators: specific path access, credential-aware behavior, targeted token type

3. **insider_threat** — Internal actor with knowledge of system structure
   Indicators: specific internal paths, knowledge of naming conventions

4. **unknown** — Insufficient evidence to classify

Respond in this EXACT JSON format (no other text):
{{
  "threat_actor_type": "automated_scanner|targeted_human|insider_threat|unknown",
  "reasoning": "Your detailed reasoning here",
  "confidence": 0.0
}}"""


def get_severity_prompt(
    threat_actor_type: str,
    token_type: str,
    classification_reasoning: str,
    threat_indicators: dict,
) -> str:
    return f"""You are a senior security analyst assigning severity to a honey token trigger.

## Threat Classification
- Actor Type: {threat_actor_type}
- Token Type: {token_type}
- Classification Reasoning: {classification_reasoning}

## Threat Indicators
{threat_indicators}

## Severity Assignment Task
Assign severity based on these criteria:

- **critical**: Targeted human accessing high-value credentials (AWS keys, database URLs, JWT secrets)
- **high**: Targeted human OR insider threat accessing any token
- **medium**: Automated scanner accessing high-value token, or unclear human intent
- **low**: Automated scanner accessing low-value token

Respond in this EXACT JSON format (no other text):
{{
  "severity": "low|medium|high|critical",
  "confidence": 0.0,
  "reasoning": "Your reasoning here"
}}"""


def get_report_prompt(
    token_label: str,
    token_type: str,
    source_ip: str,
    threat_actor_type: str,
    severity: str,
    classification_reasoning: str,
    severity_reasoning: str,
    triggered_at: str,
) -> str:
    return f"""You are a cybersecurity incident responder writing a concise incident report.

## Incident Data
- Token: {token_label} ({token_type})
- Source IP: {source_ip}
- Threat Actor: {threat_actor_type}
- Severity: {severity.upper()}
- Time: {triggered_at}

## Analysis Summary
Classification: {classification_reasoning}
Severity: {severity_reasoning}

## Report Task
Write a professional incident report with these sections:
1. **Executive Summary** (2 sentences maximum)
2. **Threat Assessment** (what happened and who likely did it)
3. **Recommended Actions** (specific, actionable steps)

Keep it under 200 words. Be direct. No fluff.
Write as plain text, not markdown."""


def get_action_prompt(
    severity: str,
    threat_actor_type: str,
    token_type: str,
    incident_report: str,
) -> str:
    return f"""You are a security operations lead deciding on response actions.

## Incident Summary
- Severity: {severity.upper()}
- Threat Actor: {threat_actor_type}
- Token Type: {token_type}

## Incident Report
{incident_report}

## Response Decision Task
Choose exactly ONE primary action:

- **monitor**: Low-risk, continue observing (automated scanners, low severity)
- **investigate**: Medium-risk, needs human review within 24 hours
- **block**: High-risk, IP should be blocked immediately
- **escalate**: Critical-risk, immediate human intervention required

Respond in this EXACT JSON format (no other text):
{{
  "action": "monitor|investigate|block|escalate",
  "reasoning": "Why this action",
  "urgency": "immediate|within_1h|within_24h|when_convenient"
}}"""
