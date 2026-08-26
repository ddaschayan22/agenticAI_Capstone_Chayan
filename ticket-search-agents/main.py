"""CLI: PlannerAgent plans, ExecutorAgent executes semantic ticket searches."""

from __future__ import annotations

import json
from pathlib import Path

from executor_agent import ExecutorAgent
from logging_config import AgentLogAdapter, configure_logging
from planner_agent import PlannerAgent
from task_store import TaskStore
from tools import TicketTools
from config import LOG_FILE


ROOT = Path(__file__).resolve().parent


def main() -> None:
    base_logger = configure_logging(LOG_FILE)
    task_store = TaskStore(Path(__file__).resolve().parent / "data")
    planner = PlannerAgent(AgentLogAdapter(base_logger, {"agent_name": "PlannerAgent", "agent_type": "planner"}), task_store)
    executor = ExecutorAgent(TicketTools(), AgentLogAdapter(base_logger, {"agent_name": "ExecutorAgent", "agent_type": "executor"}), task_store)
    print("Semantic Ticket Search — Planner and Executor Agents")
    print("PlannerAgent creates the task plan; ExecutorAgent runs the assigned search tools.")
    print("Type 'exit' to quit.")
    while True:
        request = input("\nCustomer issue: ").strip()
        if request.lower() == "exit":
            return
        if not request:
            print("Enter a customer issue.")
            continue
        plan = planner.create_plan(request)
        outcomes = executor.execute(plan)
        stored_plan = task_store.load_plan()
        print(json.dumps({"plan": plan.__dict__, "task_file": str(task_store.path), "updated_tasks": stored_plan["tasks"], "execution_outcomes": [outcome.__dict__ for outcome in outcomes]}, indent=2, ensure_ascii=False, default=lambda value: value.__dict__))
        print(f"\nLogs: {LOG_FILE}")


if __name__ == "__main__":
    main()
