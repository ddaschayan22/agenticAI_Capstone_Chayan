"""OpenRouter Chat Completions client."""

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

    def complete(self, user_input: str, tools: list[dict[str, str]], tool_results: dict[str, Any]) -> dict[str, Any]:
        if not self.configured():
            raise OpenRouterError("OpenRouter is not configured in .env.")
        system_prompt = (
            "You are one single agent creating an implementation plan from the user's capstone "
            "requirement. Analyze only the user input and tool results. Return only JSON with "
            "exactly these fields: goals, success_criteria, workflow, tools_required, tool_details, "
            "confidence. Make all five planning fields detailed and specific to the input. "
            "The workflow must describe one agent, not multiple agents. The tools_required field "
            "must list only tools needed by the requirement. The tool_details field must explain "
            "each required tool's purpose, inputs, outputs, and use in the workflow. Confidence "
            "must be a number from 0.0 to 1.0."
        )
        prompt = json.dumps({"input": user_input, "registered_tools": tools, "tool_results": tool_results})
        payload = {
            "model": self.model,
            "temperature": self.TEMPERATURE,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        try:
            response = requests.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=45,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
            raise OpenRouterError(f"OpenRouter request failed or returned invalid JSON: {exc}") from exc
        required = {"goals", "success_criteria", "workflow", "tools_required", "tool_details", "confidence"}
        if not isinstance(parsed, dict) or not required.issubset(parsed):
            raise OpenRouterError("OpenRouter response is missing required fields.")
        parsed["confidence"] = max(0.0, min(1.0, float(parsed["confidence"])))
        return parsed
