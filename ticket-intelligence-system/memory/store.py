from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class MemoryStore:
    """Persistent three-layer memory with a Chroma-compatible JSON fallback."""
    def __init__(self, directory: Path):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.long_term_file = directory / "long_term_memory.json"
        self.long_term: list[dict[str, Any]] = self._read()
        self.short_term: dict[str, Any] = {}
        self.working: dict[str, Any] = {}

    def _read(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.long_term_file.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def finding_hash(self, finding: dict[str, Any]) -> str:
        identity = "|".join(str(finding.get(k, "")).strip().lower() for k in ("customer_id", "payment_id", "category", "finding_type", "business_event"))
        return hashlib.sha256(identity.encode()).hexdigest()

    def find(self, finding: dict[str, Any]) -> dict[str, Any] | None:
        digest = self.finding_hash(finding)
        return next((x for x in self.long_term if x.get("finding_hash") == digest), None)

    def persist_finding(self, finding: dict[str, Any]) -> dict[str, Any]:
        item = {**finding, "finding_hash": self.finding_hash(finding), "action_status": finding.get("action_status", "ACTIONED")}
        existing = self.find(item)
        if existing:
            existing.update(item)
        else:
            self.long_term.append(item)
        self.long_term_file.write_text(json.dumps(self.long_term, indent=2), encoding="utf-8")
        return item

    def clear_working(self) -> None:
        self.working = {}
