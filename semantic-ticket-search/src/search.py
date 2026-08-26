"""Semantic ticket search with optional ticket-level diversification."""

from __future__ import annotations

from typing import Any

from .vector_store import TicketVectorStore


class TicketSearch:
    def __init__(self, store: TicketVectorStore) -> None:
        self.store = store

    def search_tickets(self, query: str, top_k: int = 4, diversify_by_ticket: bool = True) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError("Search query cannot be empty.")
        raw = self.store.query(query, max(top_k * 3, top_k) if diversify_by_ticket else top_k)
        results = []
        seen_tickets: set[str] = set()
        for document, metadata, distance in zip(raw["documents"][0], raw["metadatas"][0], raw["distances"][0]):
            ticket_id = str(metadata["ticket_id"])
            if diversify_by_ticket and ticket_id in seen_tickets:
                continue
            seen_tickets.add(ticket_id)
            all_chunks = self.store.get_ticket_chunks(ticket_id)
            complete_text = "\n\n".join(
                text for _, text in sorted(
                    zip(all_chunks["metadatas"], all_chunks["documents"]),
                    key=lambda item: int(item[0]["chunk_index"]),
                )
                if text
            )
            results.append({
                "ticket_id": ticket_id,
                "chunk_index": int(metadata["chunk_index"]),
                "matched_chunk_text": document,
                "text": complete_text or document,
                "resolution_status": metadata["resolution_status"],
                "source_file": metadata["source_file"],
                "distance": float(distance),
                "similarity_score": round(1.0 - float(distance), 4),
            })
            if len(results) >= top_k:
                break
        return results
