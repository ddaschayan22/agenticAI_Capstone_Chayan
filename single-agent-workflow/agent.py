"""Single autonomous agent workflow."""

from __future__ import annotations

import uuid
from pathlib import Path

from models import AgentRequest, AgentResult, AuditEvent, ToolResult
from openrouter import OpenRouterClient, OpenRouterError
from store import JsonStore
from tools import ToolRegistry


class SingleAgent:
    def __init__(self, root: Path) -> None:
        self.tools = ToolRegistry()
        self.llm = OpenRouterClient(str(root / ".env"))
        self.store = JsonStore(root / "data")

    def run(self, input_text: str) -> AgentResult:
        if not input_text.strip():
            raise ValueError("Input cannot be empty.")
        request = AgentRequest(request_id=f"REQ-{uuid.uuid4().hex[:10]}", input_text=input_text.strip())
        self.store.save_audit(AuditEvent(request.request_id, "input_received", {"length": len(request.input_text)}))

        tool_results: list[ToolResult] = []
        if len(request.input_text.split()) > 8:
            tool_results.append(self.tools.run("extract_terms", request.input_text))
        tool_data = {item.tool_name: item.data for item in tool_results if item.success}

        warnings: list[str] = []
        try:
            response = self.llm.ask(request.input_text, tool_data)
            confidence = max(0.0, min(1.0, float(response["confidence"])))
            summary = str(response["summary"])
            analysis = str(response["analysis"])
            recommendation = str(response["recommendation"])
            action_status = "completed"
        except (OpenRouterError, ValueError, TypeError) as exc:
            warnings.append(str(exc))
            confidence = 0.35
            summary = "The input was received but the configured LLM could not complete analysis."
            analysis = "No validated model analysis is available."
            recommendation = "Review the configuration or retry the request."
            action_status = "fallback"

        result = AgentResult(
            request_id=request.request_id,
            summary=summary,
            analysis=analysis,
            recommendation=recommendation,
            confidence=confidence,
            action_status=action_status,
            tool_results=tool_results,
            warnings=warnings,
        )
        self.store.save_result(result)
        self.store.save_audit(AuditEvent(request.request_id, "workflow_completed", {"status": action_status, "confidence": confidence}))
        return result
