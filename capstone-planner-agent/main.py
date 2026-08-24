"""Capstone planner with the required list/dictionary output format."""

from __future__ import annotations

import pprint
from pathlib import Path
from typing import Any

from agent import CapstonePlannerAgent


ROOT = Path(__file__).resolve().parent


def display_plan(result: Any) -> None:
    """Print only the requested plan sections in Python list/dict notation."""
    print("\ntool output for capstone:\n")
    print("GOALS")
    pprint.pprint(result.goals, width=240, sort_dicts=False)
    print("\nSUCCESS CRITERIA")
    pprint.pprint(result.success_criteria, width=240, sort_dicts=False)
    print("\nWORKFLOW")
    pprint.pprint(result.workflow, width=240, sort_dicts=False)
    print("\nTOOLS REQUIRED")
    pprint.pprint(result.tools_required, width=240, sort_dicts=False)
    print("\nTOOL DETAILS")
    pprint.pprint(result.tool_details, width=240, sort_dicts=False)
    print("\nTASK DETAILS")
    for step in result.workflow:
        for task in step.get("tasks", []):
            if isinstance(task, dict):
                pprint.pprint(task, width=240, sort_dicts=False)
            else:
                pprint.pprint({"task": task, "goals": step.get("goals", []), "tools": step.get("tools", []), "details": step.get("details", ""), "outcome": step.get("outcome", {"result": "success"})}, width=240, sort_dicts=False)
    print("\nGOAL CONNECTIONS")
    pprint.pprint(result.goal_task_mapping, width=240, sort_dicts=False)


def main() -> None:
    agent = CapstonePlannerAgent(ROOT)
    print("Generic Capstone Planner — Single Agent")
    print("Paste a capstone requirement. Type 'exit' to quit.")
    while True:
        requirement = input("\nRequirement: ").strip()
        if requirement.lower() == "exit":
            return
        try:
            result = agent.run(requirement)
            display_plan(result)
        except ValueError as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
