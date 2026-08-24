"""Models for generic capstone planning."""

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
class PlanResult:
    request_id: str
    goals: list[str]
    success_criteria: list[str]
    workflow: list[dict[str, Any]]
    tools_required: list[str]
    tool_details: dict[str, dict[str, Any]]
    goal_task_mapping: list[dict[str, Any]]
    confidence: float
    tool_results: list[ToolResult] = field(default_factory=list)
    created_at: str = field(default_factory=timestamp)
