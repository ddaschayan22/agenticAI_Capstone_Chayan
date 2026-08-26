"""Data models used by the ticket search pipeline."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Ticket:
    ticket_id: str
    text: str
    resolution_status: str
    source_file: str


@dataclass
class TicketChunk:
    chunk_id: str
    ticket_id: str
    chunk_index: int
    text: str
    resolution_status: str
    source_file: str
    metadata: dict[str, Any] = field(default_factory=dict)
