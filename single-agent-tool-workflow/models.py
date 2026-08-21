"""Data models for the single-agent tool workflow."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ToolResult:
    name: str
    success: bool
    data: dict[str, Any]
    error: str | None = None


@dataclass
class AgentResult:
    request_id: str
    goals: str
    success_criteria: str
    workflow: str
    tools_required: str
    tool_details: str
    confidence: float
    tool_results: list[ToolResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=timestamp)
