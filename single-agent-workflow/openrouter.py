"""Optional OpenRouter Chat Completions client."""

from __future__ import annotations

import json
import os
from typing import Any

import requests
from dotenv import load_dotenv


class OpenRouterError(RuntimeError):
    pass


class OpenRouterClient:
    def __init__(self, env_path: str) -> None:
        load_dotenv(env_path)
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.model = os.getenv("OPENROUTER_MODEL", "").strip()
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def configured(self) -> bool:
        return bool(self.api_key and self.model and not self.api_key.startswith("your_"))

    def ask(self, input_text: str, tool_data: dict[str, Any]) -> dict[str, Any]:
        if not self.configured():
            raise OpenRouterError("OpenRouter is not configured.")
        system = (
            "You are one careful general-purpose agent. Analyze only the user input "
            "and supplied tool data. Do not invent facts. Return only JSON with string "
            "fields summary, analysis, recommendation and numeric confidence from 0 to 1."
        )
        payload = {
            "model": self.model,
            "temperature": 0.0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Input:\n{input_text}\nTool data:\n{json.dumps(tool_data)}"},
            ],
        }
        try:
            response = requests.post(
                self.url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=45,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            result = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
            raise OpenRouterError(f"OpenRouter request failed: {exc}") from exc
        required = {"summary", "analysis", "recommendation", "confidence"}
        if not isinstance(result, dict) or not required.issubset(result):
            raise OpenRouterError("The model response did not match the required structure.")
        return result
