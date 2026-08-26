"""Meaningful, overlapping ticket chunking."""

from __future__ import annotations

import re

from .models import Ticket, TicketChunk


class TicketChunker:
    def __init__(self, chunk_size: int = 700, overlap: int = 100) -> None:
        if chunk_size <= overlap:
            raise ValueError("chunk_size must be greater than overlap")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, ticket: Ticket) -> list[TicketChunk]:
        sections = re.split(r"(?im)(?=^(?:customer|agent|resolution|issue|notes)\s*:)", ticket.text)
        sections = [section.strip() for section in sections if section.strip()]
        chunks: list[TicketChunk] = []
        for section in sections or [ticket.text]:
            words = section.split()
            step = self.chunk_size - self.overlap
            for start in range(0, len(words), step):
                part = " ".join(words[start:start + self.chunk_size]).strip()
                if part:
                    index = len(chunks)
                    chunks.append(TicketChunk(
                        chunk_id=f"{ticket.ticket_id}_chunk_{index}",
                        ticket_id=ticket.ticket_id,
                        chunk_index=index,
                        text=part,
                        resolution_status=ticket.resolution_status,
                        source_file=ticket.source_file,
                    ))
                if start + self.chunk_size >= len(words):
                    break
        return chunks
