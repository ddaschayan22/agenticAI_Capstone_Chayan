from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    allowed_agents: frozenset[str]
    side_effect: bool
    handler: Callable[..., Any]


class ToolRegistry:
    """Central allow-list: agents cannot invoke unregistered functions."""
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str, agent: str) -> ToolDefinition:
        tool = self._tools[name]
        if agent not in tool.allowed_agents:
            raise PermissionError(f"Agent {agent} cannot use tool {name}")
        return tool

    def catalog(self, agent: str) -> list[dict[str, Any]]:
        return [{"name": t.name, "description": t.description, "side_effect": t.side_effect} for t in self._tools.values() if agent in t.allowed_agents]
