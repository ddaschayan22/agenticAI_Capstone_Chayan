"""Replaceable lightweight embedding service."""

from __future__ import annotations

from typing import Sequence

from sklearn.feature_extraction.text import HashingVectorizer


class EmbeddingService:
    """Use fixed-size local vectors without importing PyTorch or transformers."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.vectorizer = HashingVectorizer(
            n_features=512,
            alternate_sign=False,
            norm="l2",
            lowercase=True,
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b\w+\b",
        )

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self.vectorizer.transform(list(texts)).toarray().tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.vectorizer.transform([text]).toarray()[0].tolist()
