"""Adapter that reuses the semantic-ticket-search package components."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from config import CHROMA_DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL, TICKETS_DIR

SEMANTIC_PROJECT = Path(__file__).resolve().parent.parent / "semantic-ticket-search"
if str(SEMANTIC_PROJECT) not in sys.path:
    sys.path.insert(0, str(SEMANTIC_PROJECT))

from src.chunker import TicketChunker  # noqa: E402
from src.config import CHUNK_OVERLAP, CHUNK_SIZE  # noqa: E402
from src.embeddings import EmbeddingService  # noqa: E402
from src.search import TicketSearch  # noqa: E402
from src.ticket_loader import TicketLoader  # noqa: E402
from src.vector_store import TicketVectorStore  # noqa: E402


class SemanticTicketAdapter:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService(EMBEDDING_MODEL)
        self.store = TicketVectorStore(CHROMA_DB_DIR, COLLECTION_NAME, self.embedding_service)
        self.searcher = TicketSearch(self.store)

    def ensure_indexed(self) -> int:
        if self.store.count() > 0:
            return self.store.count()
        tickets = TicketLoader(TICKETS_DIR).load()
        chunks = [chunk for ticket in tickets for chunk in TicketChunker(CHUNK_SIZE, CHUNK_OVERLAP).chunk(ticket)]
        return self.store.upsert(chunks)

    def search(self, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        self.ensure_indexed()
        return self.searcher.search_tickets(query, top_k=top_k, diversify_by_ticket=True)

    def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        self.ensure_indexed()
        ticket_chunks = self.store.get_ticket_chunks(ticket_id)
        if not ticket_chunks["documents"]:
            return {"ticket_id": ticket_id, "found": False, "text": ""}
        ordered = sorted(zip(ticket_chunks["metadatas"], ticket_chunks["documents"]), key=lambda row: int(row[0]["chunk_index"]))
        return {"ticket_id": ticket_id, "found": True, "text": "\n\n".join(text for _, text in ordered)}
