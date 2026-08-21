"""Simple local output and audit persistence."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from models import AgentResult


class JsonlStore:
    def __init__(self, data_dir: Path) -> None:
        data_dir.mkdir(parents=True, exist_ok=True)
        self.results_path = data_dir / "results.jsonl"
        self.audit_path = data_dir / "audit.jsonl"

    def save_result(self, result: AgentResult) -> None:
        self._append(self.results_path, asdict(result))

    def save_audit(self, event: dict) -> None:
        self._append(self.audit_path, event)

    @staticmethod
    def _append(path: Path, value: dict) -> None:
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, default=str) + "\n")
