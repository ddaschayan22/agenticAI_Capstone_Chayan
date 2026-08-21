"""Single agent that selects registered tools and processes their results."""

from __future__ import annotations

import uuid
from pathlib import Path

from models import AgentResult
from openrouter import OpenRouterClient, OpenRouterError
from store import JsonlStore
from tools import ToolRegistry


class SingleAgent:
    def __init__(self, project_root: Path) -> None:
        self.tools = ToolRegistry()
        self.llm = OpenRouterClient(project_root)
        self.store = JsonlStore(project_root / "data")

    def run(self, user_input: str) -> AgentResult:
        text = user_input.strip()
        if not text:
            raise ValueError("Input cannot be empty.")
        request_id = f"REQ-{uuid.uuid4().hex[:10]}"
        self.store.save_audit({"request_id": request_id, "event": "input_received", "input_length": len(text)})

        selected_tools = ["extract_terms"] if len(text.split()) > 8 else ["count_words"]
        tool_results = [self.tools.run(name, text) for name in selected_tools]
        result_map = {result.name: result.data for result in tool_results if result.success}
        warnings = [result.error for result in tool_results if result.error]

        try:
            response = self.llm.complete(text, self.tools.descriptions(), result_map)
            result = AgentResult(
                request_id=request_id,
                goals=str(response["goals"]),
                success_criteria=str(response["success_criteria"]),
                workflow=str(response["workflow"]),
                tools_required=str(response["tools_required"]),
                tool_details=str(response["tool_details"]),
                confidence=float(response["confidence"]),
                tool_results=tool_results,
                warnings=warnings,
            )
        except (OpenRouterError, ValueError, TypeError) as exc:
            warnings.append(str(exc))
            result = AgentResult(
                request_id=request_id,
                goals="OpenRouter analysis was unavailable; no requirement-specific goals were generated.",
                success_criteria="OpenRouter analysis was unavailable; no requirement-specific success criteria were generated.",
                workflow="OpenRouter analysis was unavailable; no requirement-specific workflow was generated.",
                tools_required="OpenRouter analysis was unavailable; no requirement-specific tools were identified.",
                tool_details="Configure OpenRouter and retry to generate tool details from the supplied requirement.",
                confidence=0.0,
                tool_results=tool_results,
                warnings=warnings,
            )

        self.store.save_result(result)
        self.store.save_audit({"request_id": request_id, "event": "workflow_completed", "confidence": result.confidence})
        return result
