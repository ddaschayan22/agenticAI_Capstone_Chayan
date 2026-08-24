"""OpenRouter client for structured capstone-plan generation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


class OpenRouterError(RuntimeError):
    pass


class OpenRouterClient:
    TEMPERATURE = 0.5

    def __init__(self, project_root: Path) -> None:
        load_dotenv(project_root / ".env")
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.model = os.getenv("OPENROUTER_MODEL", "").strip()
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def configured(self) -> bool:
        return bool(self.api_key and self.model and not self.api_key.startswith("your_"))

    def generate_plan(self, requirement: str, tool_catalog: list[dict[str, str]], tool_results: dict[str, Any]) -> dict[str, Any]:
        if not self.configured():
            raise OpenRouterError("OpenRouter is not configured in .env.")
        system = (
            "You are one planning agent. Analyze only the supplied capstone requirement. "
            "Return a JSON object with exactly these top-level fields: goals (list of strings), "
            "success_criteria (list of strings), workflow (list of step objects), tools_required "
            "(list of canonical tool names), tool_details (object keyed by canonical tool name), "
            "goal_task_mapping (list of goal objects), and confidence (number from 0 to 1). "
            "Create detailed content specific to the requirement. For a substantial capstone requirement, "
            "produce 8 goals, with at least 2 and preferably 2 to 4 tasks under every goal, and all tools explicitly required by "
            "the requirement. Do not compress a multi-part requirement into one goal or one task. One goal may have multiple tasks; "
            "one task may have multiple tools; a tool may be used by multiple tasks; and tools may "
            "call other tools. Do not use generic placeholder goals or tools when the requirement "
            "provides enough detail.\n\n"
            "Every workflow step must have this shape: {step, name, details, goals, tasks}. "
            "Every task in tasks must be an object with exactly or more of: task_id, name, details, "
            "goals, tools, tool_parameters, tool_call_order, outcome. The tools field is a list of "
            "canonical tool names. tool_parameters is an object keyed by tool name; each value is "
            "that tool's parameter object for this task. tool_call_order is an ordered list and may "
            "show one tool calling another. outcome must be a JSON object containing result and "
            "task-specific output fields.\n\n"
            "Every tool_details entry must contain purpose, description, parameter_schema, "
            "example_parameters, outputs, and workflow_use. The description and parameter_schema "
            "are canonical properties of the tool and must be identical wherever the tool is reused; "
            "only example parameter values may vary by task. Never put task-specific parameters in "
            "the canonical schema. Make all JSON valid and do not return Markdown fences."
        )
        user = json.dumps({"requirement": requirement, "registered_tools": tool_catalog, "tool_results": tool_results})
        payload = {"model": self.model, "temperature": self.TEMPERATURE, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        try:
            response = requests.post(self.endpoint, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, json=payload, timeout=60)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            result = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
            raise OpenRouterError(f"OpenRouter request failed or returned invalid JSON: {exc}") from exc
        required = {"goals", "success_criteria", "workflow", "tools_required", "tool_details", "goal_task_mapping", "confidence"}
        if not isinstance(result, dict) or not required.issubset(result):
            raise OpenRouterError("Model output is missing required planning sections.")
        return result
