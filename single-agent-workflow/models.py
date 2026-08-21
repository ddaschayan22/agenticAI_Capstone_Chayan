"""Domain-neutral models for the single-agent workflow."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentRequest:
    request_id: str
    input_text: str
    created_at: str = field(default_factory=now)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    data: dict[str, Any]
    error: str | None = None


@dataclass
class AgentResult:
    request_id: str
    summary: str
    analysis: str
    recommendation: str
    confidence: float
    action_status: str
    tool_results: list[ToolResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=now)


@dataclass
class AuditEvent:
    request_id: str
    event_type: str
    details: dict[str, Any]
    timestamp: str = field(default_factory=now)
