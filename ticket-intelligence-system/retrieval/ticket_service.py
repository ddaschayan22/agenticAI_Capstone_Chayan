from __future__ import annotations

import re
from pathlib import Path
from typing import Any


FIELD_NAMES = ["ticket_id", "customer_id", "customer_name", "category", "issue_type", "summary", "description", "priority", "status", "created_date", "resolved_date", "assigned_team", "resolution", "customer_impact", "churn_risk", "churned", "tags", "related_tickets"]


class TicketService:
    def __init__(self, path: Path):
        self.path = path
        self.tickets = self._load(path)

    @staticmethod
    def _load(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        records: list[dict[str, Any]] = []
        blocks = re.split(r"\n(?=TICKET ID:)", text)
        for block in blocks:
            if not block.lstrip().startswith("TICKET ID:"):
                continue
            record: dict[str, Any] = {}
            for line in block.splitlines():
                if ": " in line:
                    key, value = line.split(": ", 1)
                    normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
                    if normalized in FIELD_NAMES:
                        record[normalized] = value.strip()
            if "ticket_id" in record:
                record["tags"] = [x.strip() for x in record.get("tags", "").split(",") if x.strip()]
                record["related_tickets"] = [x.strip() for x in record.get("related_tickets", "").split(",") if x.strip() and x.strip().lower() != "none"]
                records.append(record)
        return records

    def get_ticket(self, ticket_id: str) -> dict[str, Any] | None:
        return next((t for t in self.tickets if t["ticket_id"].upper() == ticket_id.upper()), None)

    def search_tickets(self, query: str, category: str | None = None, limit: int = 3) -> list[dict[str, Any]]:
        """Search ticket text deterministically when the user has no ticket ID."""
        words = set(re.findall(r"[a-z0-9]+", query.lower()))
        results: list[tuple[float, dict[str, Any]]] = []
        for ticket in self.tickets:
            if category and ticket.get("category", "").lower() != category.lower():
                continue
            text = " ".join(str(ticket.get(key, "")) for key in ("category", "issue_type", "summary", "description", "resolution", "tags")).lower()
            ticket_words = set(re.findall(r"[a-z0-9]+", text))
            overlap = words & ticket_words
            if overlap:
                results.append((len(overlap) / max(len(words), 1), ticket))
        return [{**ticket, "relevance": round(score, 3)} for score, ticket in sorted(results, key=lambda item: item[0], reverse=True)[:limit]]

    def search_similar_tickets(self, issue_description: str, exclude: str | None = None) -> list[dict[str, Any]]:
        words = set(re.findall(r"[a-z0-9]+", issue_description.lower()))
        scored = []
        for ticket in self.tickets:
            if exclude and ticket["ticket_id"].upper() == exclude.upper():
                continue
            haystack = " ".join(str(ticket.get(k, "")) for k in ("issue_type", "summary", "description", "tags")).lower()
            overlap = len(words & set(re.findall(r"[a-z0-9]+", haystack)))
            if overlap:
                scored.append((overlap / max(len(words), 1), ticket))
        return [
            {**ticket, "similarity": round(score, 3), "relevance": round(score, 3)}
            for score, ticket in sorted(scored, reverse=True, key=lambda x: x[0])[:10]
        ]

    def get_customer_tickets(self, customer_id: str) -> list[dict[str, Any]]:
        return [t for t in self.tickets if t.get("customer_id", "").upper() == customer_id.upper()]

    def get_customer_status(self, customer_id: str) -> dict[str, Any]:
        tickets = self.get_customer_tickets(customer_id)
        if not tickets:
            return {}
        return {"customer_id": customer_id, "customer_name": tickets[0].get("customer_name"), "churned": any(t.get("churned") == "Yes" for t in tickets), "tickets": [t["ticket_id"] for t in tickets]}
