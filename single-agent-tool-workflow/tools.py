"""Registered tools available to the single agent."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Callable

from models import ToolResult


ToolFunction = Callable[[str], dict[str, Any]]


def extract_terms(text: str) -> dict[str, Any]:
    words = re.findall(r"[A-Za-z0-9]+", text.lower())
    return {"top_terms": Counter(words).most_common(10)}


def count_words(text: str) -> dict[str, Any]:
    return {"word_count": len(text.split())}


def detect_question(text: str) -> dict[str, Any]:
    return {"is_question": text.strip().endswith("?")}


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolFunction] = {
            "extract_terms": extract_terms,
            "count_words": count_words,
            "detect_question": detect_question,
        }

    def descriptions(self) -> list[dict[str, str]]:
        return [
            {
                "name": "extract_terms",
                "purpose": "Extract the ten most frequent normalized terms.",
                "input": "text: string",
                "output": "top_terms: list of [term, count] pairs",
            },
            {
                "name": "count_words",
                "purpose": "Count whitespace-separated words in the input.",
                "input": "text: string",
                "output": "word_count: integer",
            },
            {
                "name": "detect_question",
                "purpose": "Determine whether the input ends with a question mark.",
                "input": "text: string",
                "output": "is_question: boolean",
            },
        ]

    def run(self, name: str, text: str) -> ToolResult:
        function = self._tools.get(name)
        if function is None:
            return ToolResult(name=name, success=False, data={}, error=f"Tool is not registered: {name}")
        try:
            return ToolResult(name=name, success=True, data=function(text))
        except Exception as exc:
            return ToolResult(name=name, success=False, data={}, error=f"Tool failed: {exc}")
