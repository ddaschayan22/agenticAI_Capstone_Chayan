"""Command-line interface for semantic ticket search."""

from __future__ import annotations

import logging

from .chunker import TicketChunker
from .config import (
    CHROMA_DB_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    DEFAULT_TOP_K,
    EMBEDDING_MODEL,
    EVALUATION_TOP_K,
    TICKETS_DIR,
)
from .embeddings import EmbeddingService
from .evaluation import evaluate
from .search import TicketSearch
from .ticket_loader import TicketLoader
from .vector_store import TicketVectorStore

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def create_search() -> tuple[TicketSearch, TicketLoader, TicketChunker]:
    embeddings = EmbeddingService(EMBEDDING_MODEL)
    store = TicketVectorStore(CHROMA_DB_DIR, COLLECTION_NAME, embeddings)
    return TicketSearch(store), TicketLoader(TICKETS_DIR), TicketChunker(CHUNK_SIZE, CHUNK_OVERLAP)


def index_tickets() -> None:
    search, loader, chunker = create_search()
    limit = get_ticket_limit()
    tickets = loader.load(limit=limit)
    chunks = [chunk for ticket in tickets for chunk in chunker.chunk(ticket)]
    indexed = search.store.upsert(chunks)
    print(f"Loading tickets...\nTickets found: {len(list(TICKETS_DIR.glob('*.txt')))}\nTicket limit: {'all' if limit is None else limit}\nTickets loaded: {len(tickets)}\nChunks created: {len(chunks)}\nChunks indexed/upserted: {indexed}\n\nIndexing completed successfully.")


def get_ticket_limit() -> int | None:
    """Read an optional positive ticket count from the index command."""
    import sys
    if "--limit" not in sys.argv:
        return None
    position = sys.argv.index("--limit")
    if position + 1 >= len(sys.argv):
        raise SystemExit("Usage: python run.py index [--limit N]")
    try:
        limit = int(sys.argv[position + 1])
    except ValueError as exc:
        raise SystemExit("Ticket limit must be an integer.") from exc
    if limit <= 0:
        raise SystemExit("Ticket limit must be greater than zero.")
    return limit


def print_results(query: str, results: list[dict]) -> None:
    print(f"\nQuery:\n{query}\n\nTop semantic matches:")
    for index, result in enumerate(results, 1):
        print(f"\n{index}. {result['ticket_id']}\n   Similarity: {result['similarity_score']:.4f}\n   Distance: {result['distance']:.4f}\n   Status: {result['resolution_status']}\n   Source: {result['source_file']}\n\n   Complete ticket:\n   {result['text'].replace(chr(10), chr(10) + '   ')}")


def main() -> None:
    import sys
    command = sys.argv[1] if len(sys.argv) > 1 else "search"
    if command == "index":
        index_tickets()
        return
    search, _, _ = create_search()
    if command == "search":
        query = " ".join(sys.argv[2:]).strip()
        if not query:
            raise SystemExit("Usage: python run.py search \"your issue\"")
        if search.store.count() == 0:
            raise SystemExit("No indexed chunks. Run: python run.py index")
        print_results(query, search.search_tickets(query, DEFAULT_TOP_K))
    elif command == "evaluate":
        if search.store.count() == 0:
            raise SystemExit("No indexed chunks. Run: python run.py index")
        result = evaluate(search, EVALUATION_TOP_K)
        print("\nSemantic Search Evaluation")
        print(f"Query: {result['query']}\nExpected Ticket: {result['expected_ticket']}\nExpected ticket rank: {result['expected_ticket_rank']}\nTop-3 result: {'PASS' if result['top_k_pass'] else 'FAIL'}")
        print_results(str(result["query"]), result["results"])
    else:
        raise SystemExit("Commands: index | search <query> | evaluate")
