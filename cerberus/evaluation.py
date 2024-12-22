"""Classification and information-retrieval evaluation utilities."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from os.path import basename
from typing import Any

Record = dict[str, Any]


def _filename(record: Mapping[str, Any]) -> str:
    pathname = record.get("pathname")
    if not isinstance(pathname, str) or not pathname:
        raise ValueError("every record must contain a non-empty pathname")
    return basename(pathname)


def _index_unique(records: Iterable[Record], label: str) -> dict[str, Record]:
    indexed: dict[str, Record] = {}
    for record in records:
        key = _filename(record)
        if key in indexed:
            raise ValueError(f"duplicate {label} filename: {key}")
        indexed[key] = record
    return indexed


def _classification_map(record: Mapping[str, Any]) -> dict[str, bool]:
    values = record.get("classifications")
    if not isinstance(values, list):
        raise ValueError(f"{_filename(record)} has no classifications list")
    mapped: dict[str, bool] = {}
    for pair in values:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(f"{_filename(record)} has a malformed classification")
        class_name, value = pair
        if not isinstance(class_name, str) or not class_name:
            raise ValueError(f"{_filename(record)} has an invalid class name")
        if class_name in mapped:
            raise ValueError(
                f"{_filename(record)} contains duplicate class {class_name!r}"
            )
        if not isinstance(value, bool):
            raise ValueError(
                f"{_filename(record)} class {class_name!r} must be boolean"
            )
        mapped[class_name] = value
    return mapped


def classification_confusions(
    actual_records: Iterable[Record],
    predicted_records: Iterable[Record],
) -> list[tuple[str, dict[str, int]]]:
    """Compute per-class confusion counts after validated name-based joins."""
    actual = _index_unique(actual_records, "actual")
    predicted = _index_unique(predicted_records, "predicted")
    missing = sorted(actual.keys() - predicted.keys())
    extra = sorted(predicted.keys() - actual.keys())
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing predictions: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected predictions: {', '.join(extra)}")
        raise ValueError("; ".join(details))

    if not actual:
        return []

    actual_labels = {key: _classification_map(value) for key, value in actual.items()}
    predicted_labels = {
        key: _classification_map(value) for key, value in predicted.items()
    }
    first_filename = next(iter(actual_labels))
    class_names = list(actual_labels[first_filename])
    expected_classes = set(class_names)
    for filename in actual:
        if set(actual_labels[filename]) != expected_classes:
            raise ValueError(f"actual class set differs for {filename}")
        if set(predicted_labels[filename]) != expected_classes:
            raise ValueError(f"predicted class set differs for {filename}")

    results: list[tuple[str, dict[str, int]]] = []
    for class_name in class_names:
        counts = {
            "total": 0,
            "actual_positive": 0,
            "actual_negative": 0,
            "predicted_positive": 0,
            "predicted_negative": 0,
            "true_positive": 0,
            "false_positive": 0,
            "true_negative": 0,
            "false_negative": 0,
        }
        for filename in actual:
            actual_value = actual_labels[filename][class_name]
            predicted_value = predicted_labels[filename][class_name]
            counts["total"] += 1
            counts["actual_positive" if actual_value else "actual_negative"] += 1
            counts[
                "predicted_positive" if predicted_value else "predicted_negative"
            ] += 1
            if actual_value and predicted_value:
                counts["true_positive"] += 1
            elif not actual_value and predicted_value:
                counts["false_positive"] += 1
            elif actual_value and not predicted_value:
                counts["false_negative"] += 1
            else:
                counts["true_negative"] += 1
        results.append((class_name, counts))
    return results


def average_precision(ranked_ids: Sequence[str], relevant_ids: Iterable[str]) -> float:
    """Compute average precision over the supplied (possibly truncated) ranking."""
    relevant = set(relevant_ids)
    if not relevant:
        return 0.0
    hits = 0
    precision_sum = 0.0
    seen: set[str] = set()
    for rank, document_id in enumerate(ranked_ids, start=1):
        if document_id in seen:
            raise ValueError(f"ranking contains duplicate document: {document_id}")
        seen.add(document_id)
        if document_id in relevant:
            hits += 1
            precision_sum += hits / rank
    return precision_sum / len(relevant)


def evaluate_retrieval(
    queries: Sequence[str],
    search: Callable[[str, int], Sequence[Mapping[str, Any]]],
    ground_truth: Mapping[str, Sequence[str]],
    *,
    return_k: int,
    top_k: int,
) -> dict[str, Any]:
    """Evaluate a search function with precision/recall/F1@k and AP@return_k."""
    if return_k < 1 or top_k < 1:
        raise ValueError("return_k and top_k must be at least 1")
    if top_k > return_k:
        raise ValueError("top_k cannot exceed return_k")
    if len(set(queries)) != len(queries):
        raise ValueError("queries must be unique")

    per_query: dict[str, dict[str, Any]] = {}
    for query in queries:
        if query not in ground_truth:
            raise ValueError(f"ground truth has no entry for query: {query}")
        relevant = set(ground_truth[query])
        results = search(query, return_k)[:return_k]
        ranked_ids = [_filename(result) for result in results]
        top_ids = ranked_ids[:top_k]
        hits = sum(document_id in relevant for document_id in top_ids)
        precision = hits / top_k
        recall = hits / len(relevant) if relevant else 0.0
        f1 = (
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
        )
        per_query[query] = {
            "retrieved": ranked_ids,
            "relevant_retrieved": [value for value in ranked_ids if value in relevant],
            "precision_at_k": precision,
            "recall_at_k": recall,
            "f1_at_k": f1,
            "average_precision_at_return_k": average_precision(ranked_ids, relevant),
        }

    metric_names = (
        "precision_at_k",
        "recall_at_k",
        "f1_at_k",
        "average_precision_at_return_k",
    )
    count = len(per_query)
    overall = {
        metric: (
            sum(result[metric] for result in per_query.values()) / count
            if count
            else 0.0
        )
        for metric in metric_names
    }
    return {
        "return_k": return_k,
        "top_k": top_k,
        "queries": per_query,
        "overall": overall,
    }
