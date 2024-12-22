from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from cerberus.evaluation import (
    average_precision,
    classification_confusions,
    evaluate_retrieval,
)


def classification_record(
    pathname: str, classifications: list[list[Any]]
) -> dict[str, Any]:
    return {"pathname": pathname, "classifications": classifications}


def test_classification_confusions_join_by_filename_and_class_name() -> None:
    actual = [
        classification_record("gold/a.mp4", [["A", True], ["B", False]]),
        classification_record("gold/b.mp4", [["A", False], ["B", True]]),
    ]
    predicted = [
        classification_record("pred/b.mp4", [["B", True], ["A", True]]),
        classification_record("pred/a.mp4", [["B", False], ["A", False]]),
    ]

    results = dict(classification_confusions(actual, predicted))

    assert results["A"] == {
        "total": 2,
        "actual_positive": 1,
        "actual_negative": 1,
        "predicted_positive": 1,
        "predicted_negative": 1,
        "true_positive": 0,
        "false_positive": 1,
        "true_negative": 0,
        "false_negative": 1,
    }
    assert results["B"]["true_positive"] == 1
    assert results["B"]["true_negative"] == 1
    assert results["B"]["false_positive"] == 0
    assert results["B"]["false_negative"] == 0


def test_classification_confusions_accepts_an_empty_evaluation() -> None:
    assert classification_confusions([], []) == []


@pytest.mark.parametrize(
    ("actual", "predicted", "message"),
    [
        (
            [classification_record("a.mp4", [["A", True]])],
            [],
            "missing predictions: a.mp4",
        ),
        (
            [],
            [classification_record("extra.mp4", [["A", True]])],
            "unexpected predictions: extra.mp4",
        ),
        (
            [
                classification_record("one/a.mp4", [["A", True]]),
                classification_record("two/a.mp4", [["A", False]]),
            ],
            [],
            "duplicate actual filename: a.mp4",
        ),
        (
            [classification_record("a.mp4", [["A", True]])],
            [classification_record("a.mp4", [["A", None]])],
            "class 'A' must be boolean",
        ),
        (
            [classification_record("a.mp4", [["A", True], ["A", False]])],
            [classification_record("a.mp4", [["A", True]])],
            "contains duplicate class 'A'",
        ),
        (
            [classification_record("a.mp4", [["A", True]])],
            [classification_record("a.mp4", [["B", True]])],
            "predicted class set differs for a.mp4",
        ),
    ],
)
def test_classification_confusions_rejects_misaligned_or_invalid_data(
    actual: list[dict[str, Any]], predicted: list[dict[str, Any]], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        classification_confusions(actual, predicted)


def test_average_precision_matches_a_hand_calculated_ranking() -> None:
    # Relevant hits are at ranks 1 and 3: (1/1 + 2/3) / 2.
    assert average_precision(["a", "b", "c"], {"a", "c"}) == pytest.approx(5 / 6)
    assert average_precision(["a"], set()) == 0.0


def test_average_precision_rejects_duplicate_documents() -> None:
    with pytest.raises(ValueError, match="duplicate document: a"):
        average_precision(["a", "a"], {"a"})


def test_evaluate_retrieval_computes_per_query_and_overall_metrics() -> None:
    rankings = {
        "packages": ["a.mp4", "b.mp4", "c.mp4"],
        "nothing": [],
    }

    def search(query: str, k: int) -> Sequence[dict[str, str]]:
        assert k == 3
        return [{"pathname": f"results/{name}"} for name in rankings[query]]

    report = evaluate_retrieval(
        ["packages", "nothing"],
        search,
        {"packages": ["a.mp4", "c.mp4"], "nothing": []},
        return_k=3,
        top_k=2,
    )

    packages = report["queries"]["packages"]
    assert packages["retrieved"] == ["a.mp4", "b.mp4", "c.mp4"]
    assert packages["relevant_retrieved"] == ["a.mp4", "c.mp4"]
    assert packages["precision_at_k"] == pytest.approx(0.5)
    assert packages["recall_at_k"] == pytest.approx(0.5)
    assert packages["f1_at_k"] == pytest.approx(0.5)
    assert packages["average_precision_at_return_k"] == pytest.approx(5 / 6)
    assert report["overall"]["precision_at_k"] == pytest.approx(0.25)
    assert report["overall"]["average_precision_at_return_k"] == pytest.approx(5 / 12)


@pytest.mark.parametrize(
    ("return_k", "top_k", "message"),
    [
        (0, 1, "return_k and top_k must be at least 1"),
        (2, 0, "return_k and top_k must be at least 1"),
        (1, 2, "top_k cannot exceed return_k"),
    ],
)
def test_evaluate_retrieval_validates_cutoffs(
    return_k: int, top_k: int, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        evaluate_retrieval(
            [], lambda _query, _k: [], {}, return_k=return_k, top_k=top_k
        )


def test_evaluate_retrieval_requires_ground_truth_for_every_query() -> None:
    message = "ground truth has no entry for query: missing"
    with pytest.raises(ValueError, match=message):
        evaluate_retrieval(["missing"], lambda _query, _k: [], {}, return_k=1, top_k=1)


def test_evaluate_retrieval_rejects_duplicate_queries() -> None:
    with pytest.raises(ValueError, match="queries must be unique"):
        evaluate_retrieval(
            ["same", "same"],
            lambda _query, _k: [],
            {"same": []},
            return_k=1,
            top_k=1,
        )


def test_evaluate_retrieval_enforces_return_k_on_search_results() -> None:
    report = evaluate_retrieval(
        ["query"],
        lambda _query, _k: [
            {"pathname": "first.mp4"},
            {"pathname": "second.mp4"},
        ],
        {"query": ["second.mp4"]},
        return_k=1,
        top_k=1,
    )

    result = report["queries"]["query"]
    assert result["retrieved"] == ["first.mp4"]
    assert result["average_precision_at_return_k"] == 0.0


def test_evaluate_retrieval_handles_no_queries() -> None:
    report = evaluate_retrieval([], lambda _query, _k: [], {}, return_k=1, top_k=1)

    assert report["queries"] == {}
    assert set(report["overall"].values()) == {0.0}
