"""Executor agent for running planner-assigned semantic search tools."""

from __future__ import annotations

from datetime import datetime, timezone
from logging_config import AgentLogAdapter
from models import AgentPlan, ExecutionOutcome
from task_store import TaskStore
from tools import TicketTools


class ExecutorAgent:
    name = "ExecutorAgent"
    agent_type = "executor"

    def __init__(self, tools: TicketTools, logger: AgentLogAdapter, task_store: TaskStore) -> None:
        self.tools = tools
        self.logger = logger
        self.task_store = task_store

    def execute(self, plan: AgentPlan) -> list[ExecutionOutcome]:
        outcomes: list[ExecutionOutcome] = []
        context: dict = {}
        stored_plan = self.task_store.load_plan()
        for task_data in stored_plan["tasks"]:
            task = next((item for item in plan.tasks if item.task_id == task_data.get("task_id")), None)
            if task is None:
                self.logger.error("Task %s in task file is not present in the plan", task_data.get("task_id"))
                continue
            if task_data.get("status") != "pending":
                self.logger.info("Skipping task %s because status=%s", task.task_id, task_data.get("status"))
                continue
            self.logger.info("Starting task %s: %s", task.task_id, task.name)
            start_reason = "Task was read from tasks.json with status=pending."
            start_outcome = {"result": "started", "task_id": task.task_id, "reason": start_reason}
            self.task_store.update_task(task.task_id, "in_progress", start_outcome)
            self.task_store.append_execution_detail({
                "event": "task_status_changed",
                "task_id": task.task_id,
                "status": "in_progress",
                "input_parameters": {"previous_status": task_data.get("status")},
                "outcome": start_outcome,
                "reason": start_reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            self.logger.info("Updated task %s status pending -> in_progress; reason=%s", task.task_id, start_reason)
            task_output: dict = {"result": "success", "task_id": task.task_id, "tool_results": []}
            for call in task.tools:
                parameters = dict(call.parameters)
                if parameters.get("ticket_id") == "<best_matching_ticket_id>":
                    results = context.get("search_tickets", {}).get("results", [])
                    parameters["ticket_id"] = results[0]["ticket_id"] if results else ""
                try:
                    output = self.tools.run(call.tool_name, parameters)
                    context[call.tool_name] = output
                    task_output["tool_results"].append({"tool": call.tool_name, "parameters": parameters, "output": output})
                    reason = f"Tool {call.tool_name} returned success data for task {task.task_id}."
                    self.logger.info("Tool %s completed for task %s; parameters=%s; reason=%s", call.tool_name, task.task_id, parameters, reason)
                    self.task_store.append_execution_detail({
                        "event": "tool_execution",
                        "task_id": task.task_id,
                        "tool": call.tool_name,
                        "input_parameters": parameters,
                        "outcome": output,
                        "status": "success",
                        "reason": reason,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                except (KeyError, TypeError, ValueError) as exc:
                    task_output["result"] = "failure"
                    task_output["tool_results"].append({"tool": call.tool_name, "parameters": parameters, "error": str(exc)})
                    reason = f"Tool execution failed because: {exc}"
                    self.logger.error("Tool %s failed for task %s; parameters=%s; reason=%s", call.tool_name, task.task_id, parameters, reason)
                    self.task_store.append_execution_detail({
                        "event": "tool_execution",
                        "task_id": task.task_id,
                        "tool": call.tool_name,
                        "input_parameters": parameters,
                        "outcome": {"error": str(exc)},
                        "status": "failure",
                        "reason": reason,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
            outcomes.append(ExecutionOutcome(task_id=task.task_id, status=task_output["result"], output=task_output))
            final_status = "resolved" if task_output["result"] == "success" else "failed"
            final_reason = "All assigned tools completed successfully." if final_status == "resolved" else "One or more assigned tools failed."
            task_output["reason"] = final_reason
            self.task_store.update_task(task.task_id, final_status, task_output)
            self.task_store.append_execution_detail({
                "event": "task_completed",
                "task_id": task.task_id,
                "status": final_status,
                "input_parameters": {
                    "tools": [
                        {"tool": call.tool_name, "parameters": dict(call.parameters)}
                        for call in task.tools
                    ]
                },
                "outcome": task_output,
                "reason": final_reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            self.logger.info("Updated task %s status in_progress -> %s; reason=%s", task.task_id, final_status, final_reason)
            self.logger.info("Finished task %s with status=%s; outcome=%s; reason=%s", task.task_id, task_output["result"], task_output, final_reason)
        return outcomes
