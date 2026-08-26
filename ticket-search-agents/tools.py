"""Tools used by the executor agent."""

from __future__ import annotations

from typing import Any

from semantic_ticket_adapter import SemanticTicketAdapter


class TicketTools:
    def __init__(self) -> None:
        self.search = SemanticTicketAdapter()

    def search_tickets(self, query: str, top_k: int = 4) -> dict[str, Any]:
        results = self.search.search(query, top_k=top_k)
        return {"query": query, "top_k": top_k, "results": results}

    def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        return self.search.get_ticket(ticket_id)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "search_tickets",
                "description": "Search historical support tickets using ChromaDB vector similarity.",
                "parameters": {"query": "string", "top_k": "integer, default 4"},
            },
            {
                "name": "get_ticket",
                "description": "Retrieve the complete indexed ticket, including issue and resolution text.",
                "parameters": {"ticket_id": "string"},
            },
        ]

    def run(self, name: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if name == "search_tickets":
            return self.search_tickets(str(parameters["query"]), int(parameters.get("top_k", 4)))
        if name == "get_ticket":
            return self.get_ticket(str(parameters["ticket_id"]))
        raise ValueError(f"Executor tool is not registered: {name}")
