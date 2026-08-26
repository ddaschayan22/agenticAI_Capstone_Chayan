"""Paraphrased semantic-search evaluation."""

from __future__ import annotations

from .search import TicketSearch


QUERY = "app keeps logging me out"
EXPECTED_TICKET = "TICKET-042"


def evaluate(search: TicketSearch, top_k: int = 3) -> dict[str, object]:
    results = search.search_tickets(QUERY, top_k=top_k, diversify_by_ticket=True)
    rank = next((index for index, result in enumerate(results, 1) if result["ticket_id"] == EXPECTED_TICKET), None)
    return {
        "query": QUERY,
        "expected_ticket": EXPECTED_TICKET,
        "expected_ticket_rank": rank,
        "top_k_pass": rank is not None and rank <= top_k,
        "results": results,
    }
