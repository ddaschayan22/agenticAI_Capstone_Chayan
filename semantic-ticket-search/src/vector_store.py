"""Persistent ChromaDB vector store."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

from .models import TicketChunk


class TicketVectorStore:
    def __init__(self, db_dir: Path, collection_name: str, embedding_service: Any) -> None:
        self.client = chromadb.PersistentClient(path=str(db_dir))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedding_service = embedding_service

    def upsert(self, chunks: list[TicketChunk]) -> int:
        if not chunks:
            return 0
        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=self.embedding_service.embed_documents([chunk.text for chunk in chunks]),
            metadatas=[{
                "ticket_id": chunk.ticket_id,
                "chunk_index": chunk.chunk_index,
                "resolution_status": chunk.resolution_status,
                "source_file": chunk.source_file,
            } for chunk in chunks],
        )
        return len(chunks)

    def query(self, query: str, top_k: int) -> dict[str, Any]:
        if self.collection.count() == 0:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        return self.collection.query(
            query_embeddings=[self.embedding_service.embed_query(query)],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

    def get_ticket_chunks(self, ticket_id: str) -> dict[str, Any]:
        """Return every indexed chunk for one ticket in chunk order."""
        return self.collection.get(
            where={"ticket_id": ticket_id},
            include=["documents", "metadatas"],
        )

    def count(self) -> int:
        return self.collection.count()
