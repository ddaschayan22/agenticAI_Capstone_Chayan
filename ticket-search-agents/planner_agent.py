"""Planner agent for semantic ticket-search requests."""

from __future__ import annotations

import uuid

from logging_config import AgentLogAdapter
from models import AgentPlan, Task, ToolCall
from task_store import TaskStore


class PlannerAgent:
    name = "PlannerAgent"
    agent_type = "planner"

    def __init__(self, logger: AgentLogAdapter, task_store: TaskStore) -> None:
        self.logger = logger
        self.task_store = task_store

    def create_plan(self, user_request: str) -> AgentPlan:
        request_id = f"REQ-{uuid.uuid4().hex[:10]}"
        self.logger.info("Creating plan for request %s", request_id)
        text = user_request.strip()
        lowered = text.lower()
        tasks = [
            Task(
                task_id="1.1",
                name="Search historical tickets",
                description="Retrieve the most semantically similar historical support tickets.",
                tools=[ToolCall("search_tickets", {"query": text, "top_k": 4})],
            )
        ]
        if "ticket" in lowered or "resolution" in lowered or "complete" in lowered:
            tasks.append(
                Task(
                    task_id="1.2",
                    name="Retrieve complete ticket details",
                    description="Use a returned ticket ID to retrieve the full issue and resolution text.",
                    tools=[ToolCall("get_ticket", {"ticket_id": "<best_matching_ticket_id>"})],
                )
            )
        plan = AgentPlan(request_id=request_id, goal="Find and explain relevant historical support-ticket resolutions.", tasks=tasks)
        self.task_store.save_plan(plan)
        self.logger.info("Saved task plan to %s with all tasks status=pending", self.task_store.path)
        self.logger.info("Plan created with %d task(s)", len(tasks))
        return plan
