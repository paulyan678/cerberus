"""Deterministic in-memory sparse and dense retrieval."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Sequence
from typing import Any

Record = dict[str, Any]
_TOKEN_PATTERN = re.compile(r"[\w']+", re.UNICODE)


def _validate_k(k: int) -> None:
    if k < 1:
        raise ValueError("k must be at least 1")


def tokenize(text: str) -> list[str]:
    """Tokenize text for the lightweight BM25 implementation."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return [token.casefold() for token in _TOKEN_PATTERN.findall(text)]


def rank_sparse(
    records: Sequence[Record],
    query: str,
    k: int,
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[Record]:
    """Rank records by BM25 score over their ``description`` field."""
    _validate_k(k)
    if k1 <= 0:
        raise ValueError("k1 must be positive")
    if not 0 <= b <= 1:
        raise ValueError("b must be between 0 and 1")
    if not query.strip() or not records:
        return []

    documents: list[list[str]] = []
    for index, record in enumerate(records):
        description = record.get("description")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"record {index} has no non-empty description")
        documents.append(tokenize(description))

    query_terms = set(tokenize(query))
    if not query_terms:
        return []

    document_frequency = {
        term: sum(term in document for document in documents) for term in query_terms
    }
    average_length = sum(map(len, documents)) / len(documents)
    scored: list[tuple[float, int]] = []

    for index, document in enumerate(documents):
        frequencies = Counter(document)
        score = 0.0
        for term in query_terms:
            frequency = frequencies[term]
            if frequency == 0:
                continue
            frequency_in_corpus = document_frequency[term]
            inverse_document_frequency = math.log(
                1
                + (len(documents) - frequency_in_corpus + 0.5)
                / (frequency_in_corpus + 0.5)
            )
            length_normalization = k1 * (1 - b + b * len(document) / average_length)
            score += inverse_document_frequency * (
                frequency * (k1 + 1) / (frequency + length_normalization)
            )
        if score > 0:
            scored.append((score, index))

    scored.sort(key=lambda item: (-item[0], item[1]))
    results: list[Record] = []
    for rank, (score, index) in enumerate(scored[:k], start=1):
        results.append(
            {
                **records[index],
                "query": query,
                "rank": rank,
                "score": score,
                "retrieval_method": "sparse",
            }
        )
    return results


def _unit_vector(values: Sequence[float]) -> list[float]:
    if not values:
        raise ValueError("vectors cannot be empty")
    try:
        vector = [float(value) for value in values]
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("vector components must be finite numbers") from error
    if not all(math.isfinite(value) for value in vector):
        raise ValueError("vector components must be finite numbers")
    scale = max(abs(value) for value in vector)
    if scale == 0:
        raise ValueError("cosine distance is undefined for zero vectors")
    # Scale before squaring: valid finite values can overflow or underflow
    # naive dot products and norms (for example 1e308 and 1e-308).
    scaled = [value / scale for value in vector]
    norm = math.sqrt(math.fsum(value * value for value in scaled))
    return [value / norm for value in scaled]


def _unit_distance(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError(f"vector dimensions differ: {len(left)} != {len(right)}")
    similarity = math.fsum(a * b for a, b in zip(left, right, strict=True))
    return 1.0 - max(-1.0, min(1.0, similarity))


def cosine_distance(left: Sequence[float], right: Sequence[float]) -> float:
    """Return cosine distance for finite non-zero vectors, safely rescaled."""
    return _unit_distance(_unit_vector(left), _unit_vector(right))


def rank_dense(
    records: Sequence[Record],
    query: str,
    query_embedding: Sequence[float],
    k: int,
) -> list[Record]:
    """Rank records by cosine distance from a precomputed query embedding."""
    _validate_k(k)
    if not query.strip():
        raise ValueError("query cannot be empty")

    query_unit = _unit_vector(query_embedding)
    scored: list[tuple[float, int]] = []
    for index, record in enumerate(records):
        embedding = record.get("embedding")
        if not isinstance(embedding, list):
            raise ValueError(f"record {index} has no embedding list")
        try:
            distance = _unit_distance(query_unit, _unit_vector(embedding))
        except ValueError as error:
            raise ValueError(f"record {index}: {error}") from error
        scored.append((distance, index))

    scored.sort(key=lambda item: (item[0], item[1]))
    results: list[Record] = []
    for rank, (distance, index) in enumerate(scored[:k], start=1):
        results.append(
            {
                **records[index],
                "query": query,
                "rank": rank,
                "distance": distance,
                "retrieval_method": "dense",
            }
        )
    return results
