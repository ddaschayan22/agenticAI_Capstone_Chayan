"""Load and parse plain-text support tickets."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from .models import Ticket

LOGGER = logging.getLogger(__name__)


class TicketLoader:
    def __init__(self, tickets_dir: Path) -> None:
        self.tickets_dir = tickets_dir

    def load(self, limit: int | None = None) -> list[Ticket]:
        if not self.tickets_dir.exists():
            LOGGER.warning("Ticket directory does not exist: %s", self.tickets_dir)
            return []
        tickets = []
        paths = sorted(self.tickets_dir.glob("*.txt"))
        if limit is not None:
            if limit <= 0:
                raise ValueError("Ticket limit must be greater than zero.")
            paths = paths[:limit]
        for path in paths:
            try:
                text = path.read_text(encoding="utf-8").strip()
            except (OSError, UnicodeError) as exc:
                LOGGER.warning("Skipping %s: %s", path.name, exc)
                continue
            if not text:
                LOGGER.warning("Skipping empty ticket: %s", path.name)
                continue
            tickets.append(self._parse(path, text))
        return tickets

    @staticmethod
    def _parse(path: Path, text: str) -> Ticket:
        id_match = re.search(r"(?im)^\s*ticket\s*id\s*:\s*(.+?)\s*$", text)
        status_match = re.search(r"(?im)^\s*status\s*:\s*(.+?)\s*$", text)
        ticket_id = id_match.group(1).strip() if id_match else path.stem
        status = status_match.group(1).strip().lower() if status_match else "unknown"
        return Ticket(ticket_id=ticket_id, text=text, resolution_status=status, source_file=path.name)
