"""Persistent JSON task queue shared by PlannerAgent and ExecutorAgent."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from models import AgentPlan


class TaskStore:
    def __init__(self, data_dir: Path) -> None:
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "tasks.json"
        self.detail_log_path = data_dir / "task_execution_details.jsonl"

    def save_plan(self, plan: AgentPlan) -> None:
        payload = asdict(plan)
        for task in payload["tasks"]:
            task["status"] = "pending"
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_plan(self) -> dict[str, Any]:
        if not self.path.exists():
            raise FileNotFoundError(f"Task file does not exist: {self.path}")
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Task file is not valid JSON: {exc}") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("tasks"), list):
            raise ValueError("Task file must contain a tasks list.")
        return payload

    def update_task(self, task_id: str, status: str, outcome: dict[str, Any]) -> None:
        payload = self.load_plan()
        for task in payload["tasks"]:
            if task.get("task_id") == task_id:
                task["status"] = status
                task["outcome"] = outcome
                break
        else:
            raise KeyError(f"Task not found: {task_id}")
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def append_execution_detail(self, detail: dict[str, Any]) -> None:
        """Append a complete task/tool audit event as one JSONL record."""
        required_fields = {"event", "input_parameters", "outcome", "reason", "status", "timestamp"}
        missing_fields = required_fields.difference(detail)
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Execution detail is missing required fields: {missing}")
        with self.detail_log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(detail, ensure_ascii=False, default=str) + "\n")
