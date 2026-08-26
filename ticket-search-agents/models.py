"""Data models for agent plans, tool calls, and search results."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ToolCall:
    tool_name: str
    parameters: dict[str, Any]


@dataclass
class Task:
    task_id: str
    name: str
    description: str
    tools: list[ToolCall]
    status: str = "pending"


@dataclass
class ExecutionOutcome:
    task_id: str
    status: str
    output: dict[str, Any]
    completed_at: str = field(default_factory=utc_now)


@dataclass
class AgentPlan:
    request_id: str
    goal: str
    tasks: list[Task]
    created_at: str = field(default_factory=utc_now)
