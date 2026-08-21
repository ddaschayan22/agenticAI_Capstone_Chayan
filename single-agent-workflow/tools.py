"""Small, safe tools available to the single agent."""

from __future__ import annotations

import re
from collections import Counter

from models import ToolResult


class ToolRegistry:
    def run(self, tool_name: str, input_text: str) -> ToolResult:
        if tool_name == "extract_terms":
            words = re.findall(r"[A-Za-z0-9]+", input_text.lower())
            return ToolResult(tool_name, True, {"keywords": Counter(words).most_common(10)})
        if tool_name == "count_words":
            return ToolResult(tool_name, True, {"word_count": len(input_text.split())})
        return ToolResult(tool_name, False, {}, f"Unknown tool: {tool_name}")
