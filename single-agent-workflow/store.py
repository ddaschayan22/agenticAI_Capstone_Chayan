"""State and audit persistence for the single-agent workflow."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from models import AgentResult, AuditEvent


class JsonStore:
    def __init__(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self.results_file = directory / "results.jsonl"
        self.audit_file = directory / "audit.jsonl"

    def save_result(self, result: AgentResult) -> None:
        with self.results_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(result), default=str) + "\n")

    def save_audit(self, event: AuditEvent) -> None:
        with self.audit_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), default=str) + "\n")
