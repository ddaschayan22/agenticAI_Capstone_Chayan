"""Tools used by the generic capstone-planning agent."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Callable

from models import ToolResult

ToolFunction = Callable[[str], dict[str, Any]]


def extract_terms(text: str) -> dict[str, Any]:
    terms = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", text.lower())
    return {"top_terms": Counter(terms).most_common(20)}


def count_words(text: str) -> dict[str, Any]:
    return {"word_count": len(re.findall(r"\S+", text))}


def detect_sections(text: str) -> dict[str, Any]:
    headings = re.findall(r"(?im)^\s*(?:#|[-*])?\s*([A-Za-z][A-Za-z /&-]{2,50}):?\s*$", text)
    signals = [term for term in ["objective", "workflow", "tools", "success", "requirements", "output"] if term in text.lower()]
    return {"headings": headings[:20], "planning_signals": signals}


def identify_actions(text: str) -> dict[str, Any]:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    verbs = ("build", "create", "implement", "develop", "monitor", "analyze", "generate", "integrate", "test", "deploy", "store", "validate")
    return {"candidate_tasks": [s.strip() for s in sentences if s.strip() and s.lower().startswith(verbs)][:20]}


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolFunction] = {
            "extract_terms": extract_terms,
            "count_words": count_words,
            "detect_sections": detect_sections,
            "identify_actions": identify_actions,
        }

    def descriptions(self) -> list[dict[str, str]]:
        return [
            {"name": "extract_terms", "purpose": "Extract frequent requirement terms.", "parameters": "text: string", "returns": "top_terms: list"},
            {"name": "count_words", "purpose": "Count requirement words.", "parameters": "text: string", "returns": "word_count: integer"},
            {"name": "detect_sections", "purpose": "Detect headings and planning signals.", "parameters": "text: string", "returns": "headings and planning_signals: lists"},
            {"name": "identify_actions", "purpose": "Find action-oriented sentences for task creation.", "parameters": "text: string", "returns": "candidate_tasks: list"},
        ]

    def run(self, name: str, text: str) -> ToolResult:
        function = self._tools.get(name)
        if function is None:
            return ToolResult(name, False, {}, f"Tool is not registered: {name}")
        try:
            return ToolResult(name, True, function(text))
        except Exception as exc:
            return ToolResult(name, False, {}, f"Tool failed: {exc}")
