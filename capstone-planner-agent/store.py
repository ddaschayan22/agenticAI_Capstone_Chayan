"""Persist generated plans as JSON Lines."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from models import PlanResult


class JsonStore:
    def __init__(self, data_dir: Path) -> None:
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "plans.jsonl"

    def save(self, result: PlanResult) -> None:
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(result), ensure_ascii=False, default=str) + "\n")
